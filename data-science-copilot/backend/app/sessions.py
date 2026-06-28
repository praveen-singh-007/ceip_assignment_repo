"""In-memory per-dataset session store.

A "session" pins one uploaded/loaded DataFrame + its quality profile under a
UUID so the frontend can ask multiple follow-up questions against the same
dataset without re-uploading it. This is intentionally simple (a single
process's memory) -- fine for a local/single-instance tool, not for a
multi-worker production deployment.
"""

from __future__ import annotations

import uuid

import pandas as pd


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def create(self, df: pd.DataFrame, name: str, profile: dict) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {"df": df, "name": name, "profile": profile}
        return session_id

    def get(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)


store = SessionStore()
