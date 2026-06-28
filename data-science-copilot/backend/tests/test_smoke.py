"""Dependency-light smoke tests for the pieces that don't need a live LLM call.

Run with: .venv\\Scripts\\python.exe tests\\test_smoke.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from agent.code_extractor import extract_code
from agent.code_safety import validate_code
from agent.data_loader import load_dataset, profile_dataset, schema_summary_text
from agent.report import generate_markdown_report, save_report
from agent.sandbox import run_code
from agent.self_heal_agent import Attempt, AnalysisOutcome

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


def test_data_loader_formats():
    csv_df = load_dataset(os.path.join(DATA_DIR, "sample_sales.csv"))
    check("load CSV", len(csv_df) > 0 and "revenue" in csv_df.columns)

    xlsx_df = load_dataset(os.path.join(DATA_DIR, "sample_sales.xlsx"))
    check("load Excel", len(xlsx_df) > 0 and "revenue" in xlsx_df.columns)

    json_df = load_dataset(os.path.join(DATA_DIR, "sample_customers.json"))
    check("load JSON", len(json_df) > 0 and "customer_id" in json_df.columns)

    profile = profile_dataset(csv_df)
    check("profile has duplicate_rows", "duplicate_rows" in profile)
    check("profile detects injected duplicates", profile["duplicate_rows"] >= 1)
    check("profile detects injected nulls", any(c["null_count"] > 0 for c in profile["columns"]))

    schema_text = schema_summary_text(csv_df, profile)
    check("schema text mentions revenue", "revenue" in schema_text)


def test_code_extractor():
    response = "Here you go:\n```python\nx = 1\nprint(x)\n```\nDone."
    code = extract_code(response)
    check("extract_code pulls fenced block", code == "x = 1\nprint(x)")


def test_code_safety_blocks_dangerous_patterns():
    bad_import = "import os\nos.system('echo hi')"
    bad_dunder = "x = (1).__class__.__bases__"
    bad_eval = "eval('1+1')"
    good_code = "import pandas as pd\nresult = df.head()\ninsights = 'ok'"

    check("blocks disallowed import", len(validate_code(bad_import)) > 0)
    check("blocks dunder attribute access", len(validate_code(bad_dunder)) > 0)
    check("blocks eval", len(validate_code(bad_eval)) > 0)
    check("allows normal pandas code", len(validate_code(good_code)) == 0)


def test_sandbox_execution():
    df = pd.DataFrame({"region": ["N", "S", "N"], "revenue": [10, 20, 30]})

    good_code = (
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "totals = df.groupby('region')['revenue'].sum()\n"
        "result = totals.reset_index()\n"
        "insights = f'Top region revenue is {totals.max()}'\n"
    )
    res = run_code(df, good_code)
    check("sandbox runs valid code successfully", res.success)
    check("sandbox captures insights", res.insights is not None and "Top region" in res.insights)
    check("sandbox captures result table", res.result is not None and res.result["type"] == "dataframe")

    bad_code = "totals = df['does_not_exist'].sum()\ninsights = str(totals)\n"
    res_bad = run_code(df, bad_code)
    check("sandbox reports failure for bad column", not res_bad.success)
    check("sandbox surfaces KeyError", "KeyError" in (res_bad.error or ""))

    unsafe_code = "import os\nos.listdir('.')\ninsights = 'x'\n"
    res_unsafe = run_code(df, unsafe_code)
    check("sandbox rejects unsafe import before executing", not res_unsafe.success)
    check("sandbox flags safety violation", len(res_unsafe.safety_violations) > 0)


def test_rag_retrieval():
    from agent.rag.retriever import retrieve

    docs = retrieve("KeyError column not found in DataFrame groupby", k=3)
    check("RAG retrieval returns results", len(docs) > 0)
    sources = {d["source"] for d in docs}
    check("RAG retrieval finds a relevant pandas doc", any("pandas" in s for s in sources))


def test_markdown_report():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_path = os.path.join(BASE_DIR, "outputs", "_test_chart.png")
    fig, ax = plt.subplots()
    ax.bar(["a", "b"], [1, 2])
    fig.savefig(chart_path)
    plt.close(fig)

    df = pd.DataFrame({"region": ["N", "S"], "revenue": [100, 200]})
    profile = profile_dataset(df)

    outcome = AnalysisOutcome(
        success=True,
        question="Show revenue by region",
        insights="South leads with 200 in revenue.",
        result={"type": "dataframe", "columns": ["region", "revenue"], "data": df.to_dict("records")},
        chart_paths=[chart_path],
        attempts=[
            Attempt(attempt_number=1, code="x = 1\ninsights='bad'", success=False, error="KeyError: 'Region'",
                     retrieved_docs=[{"source": "pandas_groupby", "text": "...", "score": 0.5}]),
            Attempt(attempt_number=2, code="insights = 'South leads with 200 in revenue.'", success=True),
        ],
        final_code="insights = 'South leads with 200 in revenue.'",
    )

    report_md = generate_markdown_report(outcome, "sample_sales.csv", profile)
    check("report has title", report_md.startswith("# Data Analysis Report"))
    check("report includes the question", "Show revenue by region" in report_md)
    check("report embeds chart as base64 image", "data:image/png;base64," in report_md)
    check("report includes result table", "| region " in report_md or "region" in report_md)
    check("report includes dataset snapshot", "## Dataset Snapshot" in report_md)
    check("report includes self-correction trace", "## Self-Correction Trace" in report_md)
    check("report references retrieved RAG doc", "pandas_groupby" in report_md)
    check("report includes appendix code", "## Appendix: Generated Code" in report_md)

    saved_path = save_report(outcome, "sample_sales.csv", profile)
    check("save_report writes a file", os.path.exists(saved_path))
    os.remove(saved_path)
    os.remove(chart_path)


if __name__ == "__main__":
    test_data_loader_formats()
    test_code_extractor()
    test_code_safety_blocks_dangerous_patterns()
    test_sandbox_execution()
    test_rag_retrieval()
    test_markdown_report()
    print("\nAll smoke tests passed.")
