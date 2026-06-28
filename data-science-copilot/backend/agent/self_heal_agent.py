"""Orchestrates the core loop: generate code -> execute in the sandbox ->
on failure, retrieve relevant docs via RAG and ask the LLM to self-correct ->
retry until it succeeds or the attempt budget runs out."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import config
from .code_extractor import extract_code
from .data_loader import schema_summary_text
from .llm import get_completion, get_llm
from .prompts import build_code_gen_prompt, build_self_heal_prompt
from .rag.retriever import retrieve
from .sandbox import ExecutionResult, run_code


@dataclass
class Attempt:
    attempt_number: int
    code: str
    success: bool
    error: str | None = None
    retrieved_docs: list[dict] = field(default_factory=list)


@dataclass
class AnalysisOutcome:
    success: bool
    question: str
    insights: str | None
    result: dict | None
    chart_paths: list[str]
    attempts: list[Attempt]
    final_code: str | None
    # Populated by the UI layer (app.py) after the outcome is produced --
    # path to the saved Markdown report bundling chart + insights + trace.
    report_path: str | None = None


def analyze(df: pd.DataFrame, question: str, max_attempts: int | None = None) -> AnalysisOutcome:
    max_attempts = max_attempts or config.MAX_SELF_HEAL_ATTEMPTS
    llm = get_llm()
    schema = schema_summary_text(df)

    attempts: list[Attempt] = []
    code: str | None = None
    exec_result: ExecutionResult | None = None

    for attempt_number in range(1, max_attempts + 1):
        if attempt_number == 1:
            system_prompt = build_code_gen_prompt(schema)
            response_text = get_completion(llm, system_prompt, question)
        else:
            prev_attempt = attempts[-1]
            retrieved = retrieve(f"{prev_attempt.error}\n\n{question}", k=3)
            prev_attempt.retrieved_docs = retrieved
            self_heal_prompt = build_self_heal_prompt(
                question=question,
                schema=schema,
                previous_code=code or "",
                error_message=prev_attempt.error or "Unknown error",
                retrieved_docs=retrieved,
            )
            response_text = get_completion(llm, self_heal_prompt, "Provide the corrected code.")

        code = extract_code(response_text)
        exec_result = run_code(df, code)

        attempts.append(
            Attempt(
                attempt_number=attempt_number,
                code=code,
                success=exec_result.success,
                error=exec_result.error,
            )
        )

        if exec_result.success:
            break

    final_success = bool(exec_result and exec_result.success)
    return AnalysisOutcome(
        success=final_success,
        question=question,
        insights=exec_result.insights if exec_result else None,
        result=exec_result.result if exec_result else None,
        chart_paths=exec_result.chart_paths if exec_result else [],
        attempts=attempts,
        final_code=code,
    )
