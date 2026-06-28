"""FastAPI entry point for the Autonomous Data Science Co-Pilot API.

Run from inside backend/ with:
    .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000

(`-m` puts backend/ on sys.path so the sibling `agent` package resolves.)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import config as agent_config

from .routers import analysis, datasets
from . import schemas

app = FastAPI(title="Autonomous Data Science Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=agent_config.OUTPUTS_DIR), name="files")

app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


@app.get("/api/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    return schemas.HealthResponse(
        status="ok",
        model=agent_config.GROQ_MODEL,
        max_self_heal_attempts=agent_config.MAX_SELF_HEAL_ATTEMPTS,
    )
