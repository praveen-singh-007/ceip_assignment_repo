"""Live end-to-end check against the real Groq API. Costs a few API calls.

Run with: .venv\\Scripts\\python.exe tests\\manual_e2e.py
Use this to confirm your GROQ_API_KEY works and the full self-healing loop
(generate -> execute -> RAG-assisted retry) produces a chart + insight.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from agent.data_loader import load_dataset
from agent.self_heal_agent import analyze

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_case(label, df, question):
    print(f"\n=== {label} ===")
    print(f"Q: {question}")
    outcome = analyze(df, question)
    print(f"Success: {outcome.success} after {len(outcome.attempts)} attempt(s)")
    for a in outcome.attempts:
        print(f"  attempt {a.attempt_number}: success={a.success} "
              f"error={(a.error or '').splitlines()[-1] if a.error else None}")
    print(f"Insights: {outcome.insights}")
    print(f"Charts: {outcome.chart_paths}")
    if not outcome.success:
        print("FINAL CODE:\n", outcome.final_code)
    return outcome


if __name__ == "__main__":
    sales = load_dataset(os.path.join(BASE_DIR, "data", "sample_sales.csv"))
    traffic = load_dataset(os.path.join(BASE_DIR, "data", "sample_traffic.csv"))
    customers = load_dataset(os.path.join(BASE_DIR, "data", "sample_customers.json"))

    o1 = run_case("Sales dashboard", sales,
                  "Show me total revenue by region as a bar chart and tell me which region leads.")
    o2 = run_case("Data quality audit", sales,
                  "Run a data quality audit: missing values, duplicate rows, and revenue outliers. "
                  "Summarize what's wrong with this dataset.")
    o3 = run_case("Trend analysis", traffic,
                  "Is my traffic growing? Show a trend line over time and explain.")
    o4 = run_case("Cohort analysis", customers,
                  "Segment customers into cohorts by total_spend and show a grouped chart comparing them.")
    o5 = run_case("Self-heal stress test (deliberately ambiguous column)", sales,
                  "Plot revenue over time using the 'Revenue' and 'Date' columns (note capitalization).")

    results = {"sales_dashboard": o1, "data_quality": o2, "trend": o3, "cohort": o4, "self_heal": o5}
    print("\n\n=== SUMMARY ===")
    for name, o in results.items():
        print(f"{name}: success={o.success}, attempts={len(o.attempts)}")
