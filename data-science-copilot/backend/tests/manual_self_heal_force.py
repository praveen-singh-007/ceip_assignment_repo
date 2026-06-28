"""Force a real execution failure (wrong column name, no defensive guard) and
verify the live self-correction path: sandbox error -> RAG retrieval -> Groq
fixes the code -> sandbox succeeds. This proves the loop end-to-end against
the real model rather than relying on the LLM happening to fail on its own.

Run with: .venv\\Scripts\\python.exe tests\\manual_self_heal_force.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.data_loader import load_dataset, schema_summary_text
from agent.llm import get_completion, get_llm
from agent.code_extractor import extract_code
from agent.prompts import build_self_heal_prompt
from agent.rag.retriever import retrieve
from agent.sandbox import run_code

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BROKEN_CODE = (
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "revenue_by_region = df.groupby('Region')['Revenue'].sum()\n"
    "fig, ax = plt.subplots()\n"
    "revenue_by_region.plot(kind='bar', ax=ax)\n"
    "plt.savefig('chart.png')\n"
    "insights = f'Top region: {revenue_by_region.idxmax()}'\n"
)

if __name__ == "__main__":
    df = load_dataset(os.path.join(BASE_DIR, "data", "sample_sales.csv"))
    schema = schema_summary_text(df)
    question = "Show total revenue by region as a bar chart."

    print("--- Attempt 1 (deliberately broken: wrong column case) ---")
    result1 = run_code(df, BROKEN_CODE)
    print(f"success={result1.success}")
    print((result1.error or "")[-500:])
    assert not result1.success, "expected attempt 1 to fail"

    print("\n--- Retrieving RAG docs for this error ---")
    docs = retrieve(f"{result1.error}\n\n{question}", k=3)
    for d in docs:
        print(f"  source={d['source']} score={d['score']:.3f}")
    assert docs, "expected at least one retrieved doc"

    print("\n--- Asking Groq to self-correct using the retrieved docs ---")
    llm = get_llm()
    prompt = build_self_heal_prompt(
        question=question, schema=schema, previous_code=BROKEN_CODE,
        error_message=result1.error, retrieved_docs=docs,
    )
    response = get_completion(llm, prompt, "Provide the corrected code.")
    fixed_code = extract_code(response)
    print(fixed_code)

    print("\n--- Attempt 2 (corrected code) ---")
    result2 = run_code(df, fixed_code)
    print(f"success={result2.success}")
    print(f"insights={result2.insights}")
    print(f"charts={result2.chart_paths}")
    assert result2.success, "expected the self-healed code to succeed"

    print("\nSELF-HEAL LOOP VERIFIED END-TO-END.")
