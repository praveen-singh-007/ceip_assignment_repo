"""Builds a structured, self-contained Markdown report for one analysis run:
question, plain-English summary, embedded chart(s), result table, a dataset
quality snapshot, and the self-correction trace -- the "finished artefact"
counterpart to the in-app chart/insight view."""

from __future__ import annotations

import base64
import datetime
import os
import re

import pandas as pd

from . import config


def _slugify(text: str, max_len: int = 50) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "analysis"


def _embed_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _result_to_markdown(result: dict | None) -> str:
    if not result:
        return ""
    if result["type"] == "dataframe":
        df = pd.DataFrame(result["data"], columns=result["columns"])
        try:
            return df.to_markdown(index=False)
        except ImportError:
            return df.to_string(index=False)
    if result["type"] == "dict":
        lines = ["| Key | Value |", "|---|---|"]
        for k, v in result["data"].items():
            lines.append(f"| {k} | {v} |")
        return "\n".join(lines)
    return str(result["data"])


def _quality_section(profile: dict | None) -> str:
    if not profile:
        return ""
    lines = [
        "## Dataset Snapshot",
        "",
        f"- **Rows:** {profile['shape']['rows']}",
        f"- **Columns:** {profile['shape']['columns']}",
        f"- **Duplicate rows:** {profile['duplicate_rows']}",
    ]
    flagged = [c for c in profile["columns"] if c["null_count"] > 0]
    if flagged:
        lines.append("- **Columns with missing values:**")
        for c in flagged:
            lines.append(f"  - `{c['name']}`: {c['null_count']} nulls ({c['null_pct']}%)")
    lines.append("")
    return "\n".join(lines)


def generate_markdown_report(outcome, dataset_name: str, profile: dict | None = None) -> str:
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self_corrections = max(len(outcome.attempts) - 1, 0)

    lines = [
        "# Data Analysis Report",
        "",
        f"- **Dataset:** {dataset_name}",
        f"- **Generated:** {generated_at}",
        f"- **Question:** {outcome.question}",
        f"- **Status:** {'Success' if outcome.success else 'Failed'} "
        f"({len(outcome.attempts)} attempt(s), {self_corrections} self-correction(s))",
        "",
        "## Summary",
        "",
        outcome.insights or "_No insights were produced._",
        "",
    ]

    if outcome.chart_paths:
        lines.append("## Visualization")
        lines.append("")
        for path in outcome.chart_paths:
            if os.path.exists(path):
                lines.append(f"![chart]({_embed_image_base64(path)})")
                lines.append("")

    table_md = _result_to_markdown(outcome.result)
    if table_md:
        lines.append("## Result Table")
        lines.append("")
        lines.append(table_md)
        lines.append("")

    quality_md = _quality_section(profile)
    if quality_md:
        lines.append(quality_md)

    if len(outcome.attempts) > 1:
        lines.append("## Self-Correction Trace")
        lines.append("")
        for attempt in outcome.attempts:
            status = "succeeded" if attempt.success else "failed"
            lines.append(f"- **Attempt {attempt.attempt_number}** -- {status}")
            if attempt.error:
                first_line = attempt.error.strip().splitlines()[-1]
                lines.append(f"  - Error: `{first_line}`")
            if attempt.retrieved_docs:
                sources = ", ".join(sorted({d["source"] for d in attempt.retrieved_docs}))
                lines.append(f"  - RAG docs consulted: {sources}")
        lines.append("")

    if outcome.final_code:
        lines.append("## Appendix: Generated Code")
        lines.append("")
        lines.append("```python")
        lines.append(outcome.final_code)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def save_report(outcome, dataset_name: str, profile: dict | None = None) -> str:
    reports_dir = os.path.join(config.OUTPUTS_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{_slugify(outcome.question)}.md"
    path = os.path.join(reports_dir, filename)

    content = generate_markdown_report(outcome, dataset_name, profile)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
