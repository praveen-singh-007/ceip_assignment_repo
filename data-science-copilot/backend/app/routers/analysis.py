"""The core "ask a question" endpoint: runs the self-healing agent loop
against a session's DataFrame and returns chart/insight/result/trace."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from agent import config as agent_config
from agent.report import save_report
from agent.self_heal_agent import analyze

from .. import schemas
from ..sessions import store

router = APIRouter()


def _to_file_url(path: str | None) -> str | None:
    if not path:
        return None
    rel = os.path.relpath(path, agent_config.OUTPUTS_DIR).replace(os.sep, "/")
    return f"/files/{rel}"


@router.post("/ask", response_model=schemas.AskResponse)
def ask(payload: schemas.AskRequest) -> schemas.AskResponse:
    session = store.get(payload.session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown or expired session. Please reload your dataset.",
        )

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        outcome = analyze(session["df"], question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach the LLM: {exc}") from exc

    try:
        outcome.report_path = save_report(outcome, session["name"], session["profile"])
    except Exception:
        outcome.report_path = None

    attempts_out = [
        schemas.AttemptOut(
            attempt_number=a.attempt_number,
            success=a.success,
            code=a.code,
            error=a.error,
            retrieved_doc_sources=sorted({d["source"] for d in a.retrieved_docs}),
        )
        for a in outcome.attempts
    ]

    result_out = schemas.ResultTable(**outcome.result) if outcome.result else None

    return schemas.AskResponse(
        success=outcome.success,
        question=outcome.question,
        insights=outcome.insights,
        result=result_out,
        chart_urls=[url for p in outcome.chart_paths if (url := _to_file_url(p))],
        attempts=attempts_out,
        final_code=outcome.final_code,
        report_url=_to_file_url(outcome.report_path),
    )
