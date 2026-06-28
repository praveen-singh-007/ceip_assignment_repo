"""Streamlit UI for the Autonomous Data Science Co-Pilot.

Upload a CSV / Excel / JSON file, ask a question in plain English, and the
agent writes, executes, and self-corrects Python/Pandas code until it
delivers a chart and a plain-English insight.
"""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import streamlit as st

from agent import config
from agent.data_loader import UnsupportedFileTypeError, load_dataset, profile_dataset
from agent.report import save_report
from agent.self_heal_agent import AnalysisOutcome, analyze

SAMPLE_DATASETS = {
    "-- choose a sample --": None,
    "🛒 Sales (CSV, has data-quality issues)": os.path.join(config.BASE_DIR, "data", "sample_sales.csv"),
    "📈 Website Traffic (CSV, time series)": os.path.join(config.BASE_DIR, "data", "sample_traffic.csv"),
    "👥 Customers (JSON, for cohorts)": os.path.join(config.BASE_DIR, "data", "sample_customers.json"),
    "🛒 Sales (Excel version)": os.path.join(config.BASE_DIR, "data", "sample_sales.xlsx"),
}

QUICK_ACTIONS = [
    ("📊 Sales dashboard", "Pick the most relevant numeric metric (e.g. revenue/sales) and the most "
                            "relevant categorical column (e.g. region/category/product) from this "
                            "dataset's actual columns, show the metric broken down by that category "
                            "as a bar chart, and tell me which one leads."),
    ("🧹 Data quality audit", "Run a full data quality audit: missing values, duplicate rows, and "
                               "outliers in the numeric columns, and summarize the findings."),
    ("📈 Trend analysis", "Is the main numeric metric in this dataset trending up or down over time? "
                           "Plot the trend and explain what you see."),
    ("🧩 Cohort analysis", "Segment the records into cohorts based on the most relevant spend or "
                            "activity column and show a grouped chart comparing the cohorts."),
]

st.set_page_config(page_title="Autonomous Data Science Co-Pilot", page_icon="🧠", layout="wide")


def _init_state() -> None:
    defaults = {"df": None, "dataset_name": None, "profile": None, "history": [], "question_input": ""}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _load_uploaded_file(uploaded) -> pd.DataFrame:
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name
    try:
        return load_dataset(tmp_path, original_name=uploaded.name)
    finally:
        os.unlink(tmp_path)


def _render_data_quality(profile: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", profile["shape"]["rows"])
    c2.metric("Columns", profile["shape"]["columns"])
    c3.metric("Duplicate rows", profile["duplicate_rows"])

    cols_df = pd.DataFrame(
        [
            {
                "Column": c["name"],
                "Dtype": c["dtype"],
                "Nulls": c["null_count"],
                "Null %": c["null_pct"],
                "Unique": c["unique_count"],
                "Examples": ", ".join(c["sample_values"]),
            }
            for c in profile["columns"]
        ]
    )
    st.dataframe(cols_df, use_container_width=True, hide_index=True)


def _render_result_table(result: dict | None) -> None:
    if not result:
        return
    if result["type"] == "dataframe":
        st.dataframe(pd.DataFrame(result["data"], columns=result["columns"]), use_container_width=True)
    elif result["type"] == "dict":
        st.json(result["data"])
    else:
        st.write(result["data"])


def _render_attempt_trace(outcome: AnalysisOutcome) -> None:
    with st.expander(f"🔍 How the agent got here ({len(outcome.attempts)} attempt(s))"):
        for attempt in outcome.attempts:
            status = "✅ succeeded" if attempt.success else "❌ failed"
            st.markdown(f"**Attempt {attempt.attempt_number} — {status}**")
            st.code(attempt.code, language="python")
            if attempt.error:
                st.text(attempt.error[-1500:])
            if attempt.retrieved_docs:
                sources = ", ".join(sorted({d["source"] for d in attempt.retrieved_docs}))
                st.caption(f"📚 RAG self-correction used docs: {sources}")
            st.divider()


def _render_outcome(outcome: AnalysisOutcome) -> None:
    st.markdown(f"**Q: {outcome.question}**")
    if outcome.success:
        st.success("Analysis complete.")
        if outcome.chart_paths:
            cols = st.columns(len(outcome.chart_paths)) if len(outcome.chart_paths) > 1 else [st]
            for col, path in zip(cols, outcome.chart_paths):
                col.image(path, use_container_width=True)
        if outcome.insights:
            st.info(outcome.insights)
        _render_result_table(outcome.result)
    else:
        st.error("The agent could not produce a working result within the attempt budget.")
        last_error = outcome.attempts[-1].error if outcome.attempts else "Unknown error"
        st.text((last_error or "")[-1500:])
    _render_report_section(outcome)
    _render_attempt_trace(outcome)


def _render_report_section(outcome: AnalysisOutcome) -> None:
    if not outcome.report_path or not os.path.exists(outcome.report_path):
        return
    with open(outcome.report_path, "r", encoding="utf-8") as f:
        report_md = f.read()
    st.download_button(
        "📄 Download structured report (.md)",
        data=report_md,
        file_name=os.path.basename(outcome.report_path),
        mime="text/markdown",
        key=f"dl_{outcome.report_path}",
    )
    with st.expander("📄 Preview structured report"):
        st.markdown(report_md)


def main() -> None:
    _init_state()

    st.title("🧠 Autonomous Data Science Co-Pilot")
    st.caption(
        "Upload a CSV / Excel / JSON file, ask a question in plain English, and the agent writes, "
        "runs, and self-corrects Python/Pandas code until it delivers a chart and an insight."
    )

    with st.sidebar:
        st.header("📁 Dataset")
        sample_choice = st.selectbox("Try a sample dataset", list(SAMPLE_DATASETS.keys()))
        uploaded = st.file_uploader("...or upload your own", type=["csv", "xlsx", "xls", "json"])

        new_df, new_name = None, None
        try:
            if uploaded is not None:
                new_df = _load_uploaded_file(uploaded)
                new_name = uploaded.name
            elif SAMPLE_DATASETS[sample_choice]:
                path = SAMPLE_DATASETS[sample_choice]
                new_df = load_dataset(path)
                new_name = os.path.basename(path)
        except UnsupportedFileTypeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not read that file: {exc}")

        if new_df is not None and new_name != st.session_state.dataset_name:
            st.session_state.df = new_df
            st.session_state.dataset_name = new_name
            st.session_state.profile = profile_dataset(new_df)
            st.session_state.history = []

        st.divider()
        st.caption(f"LLM: Groq · `{config.GROQ_MODEL}`")
        st.caption(f"Self-heal attempts: up to {config.MAX_SELF_HEAL_ATTEMPTS}")
        st.caption("RAG: FAISS over pandas/numpy/matplotlib/python docs")

    if st.session_state.df is None:
        st.info("👈 Pick a sample dataset or upload your own CSV / Excel / JSON file to get started.")
        return

    st.subheader(f"Dataset: {st.session_state.dataset_name}")
    tab_preview, tab_quality, tab_ask = st.tabs(["👀 Preview", "🧹 Data Quality", "💬 Ask a Question"])

    with tab_preview:
        st.dataframe(st.session_state.df.head(20), use_container_width=True)

    with tab_quality:
        _render_data_quality(st.session_state.profile)

    with tab_ask:
        st.write("**Quick actions** (click to draft a question, then edit if you like):")
        cols = st.columns(len(QUICK_ACTIONS))
        for col, (label, prompt) in zip(cols, QUICK_ACTIONS):
            if col.button(label, use_container_width=True):
                st.session_state.question_input = prompt
                st.rerun()

        question = st.text_area(
            "Ask anything about this dataset in plain English",
            key="question_input",
            height=80,
        )
        analyze_clicked = st.button("🚀 Analyze", type="primary")

        if analyze_clicked and question.strip():
            with st.spinner("Agent is writing and running Python code, self-correcting on errors..."):
                try:
                    outcome = analyze(st.session_state.df, question.strip())
                except Exception as exc:
                    st.error(f"Could not reach the LLM: {exc}")
                    outcome = None
            if outcome is not None:
                try:
                    outcome.report_path = save_report(
                        outcome, st.session_state.dataset_name, st.session_state.profile
                    )
                except Exception:
                    outcome.report_path = None
                st.session_state.history.insert(0, outcome)

        st.divider()
        for outcome in st.session_state.history:
            _render_outcome(outcome)


if __name__ == "__main__":
    main()
