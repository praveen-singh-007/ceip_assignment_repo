"""Pydantic request/response models for the FastAPI layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DatasetProfileColumn(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: list[str]


class DatasetProfile(BaseModel):
    shape: dict[str, int]
    columns: list[DatasetProfileColumn]
    duplicate_rows: int
    numeric_columns: list[str]
    datetime_columns: list[str]


class SampleDatasetInfo(BaseModel):
    key: str
    label: str
    description: str
    format: str


class DatasetLoadResponse(BaseModel):
    session_id: str
    dataset_name: str
    profile: DatasetProfile
    preview: list[dict[str, Any]]
    columns: list[str]


class AskRequest(BaseModel):
    session_id: str
    question: str


class AttemptOut(BaseModel):
    attempt_number: int
    success: bool
    code: str
    error: str | None = None
    retrieved_doc_sources: list[str] = []


class ResultTable(BaseModel):
    type: str
    columns: list[str] | None = None
    data: Any = None


class AskResponse(BaseModel):
    success: bool
    question: str
    insights: str | None = None
    result: ResultTable | None = None
    chart_urls: list[str] = []
    attempts: list[AttemptOut] = []
    final_code: str | None = None
    report_url: str | None = None


class HealthResponse(BaseModel):
    status: str
    model: str
    max_self_heal_attempts: int
