"""Dataset upload + sample-dataset loading endpoints."""

from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from agent import config as agent_config
from agent.data_loader import UnsupportedFileTypeError, load_dataset, profile_dataset

from .. import schemas
from ..sessions import store

router = APIRouter()

SAMPLE_DATASETS: dict[str, dict[str, str]] = {
    "sales_csv": {
        "label": "Sales",
        "description": "Monthly sales with missing values, duplicates, and outliers",
        "format": "CSV",
        "path": os.path.join(agent_config.BASE_DIR, "data", "sample_sales.csv"),
    },
    "traffic_csv": {
        "label": "Website traffic",
        "description": "Daily sessions over a year, by acquisition source",
        "format": "CSV",
        "path": os.path.join(agent_config.BASE_DIR, "data", "sample_traffic.csv"),
    },
    "customers_json": {
        "label": "Customers",
        "description": "Signup date, spend, and order history for cohort analysis",
        "format": "JSON",
        "path": os.path.join(agent_config.BASE_DIR, "data", "sample_customers.json"),
    },
    "sales_xlsx": {
        "label": "Sales (Excel)",
        "description": "The same sales dataset in Excel format",
        "format": "XLSX",
        "path": os.path.join(agent_config.BASE_DIR, "data", "sample_sales.xlsx"),
    },
}


def _build_response(df, name: str, profile: dict, session_id: str) -> schemas.DatasetLoadResponse:
    preview = df.head(20).astype(str).to_dict(orient="records")
    return schemas.DatasetLoadResponse(
        session_id=session_id,
        dataset_name=name,
        profile=profile,
        preview=preview,
        columns=[str(c) for c in df.columns],
    )


@router.get("/samples", response_model=list[schemas.SampleDatasetInfo])
def list_samples() -> list[schemas.SampleDatasetInfo]:
    return [
        schemas.SampleDatasetInfo(
            key=k, label=v["label"], description=v["description"], format=v["format"]
        )
        for k, v in SAMPLE_DATASETS.items()
    ]


@router.post("/samples/{key}/load", response_model=schemas.DatasetLoadResponse)
def load_sample(key: str) -> schemas.DatasetLoadResponse:
    sample = SAMPLE_DATASETS.get(key)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Unknown sample dataset '{key}'.")

    df = load_dataset(sample["path"])
    name = os.path.basename(sample["path"])
    profile = profile_dataset(df)
    session_id = store.create(df, name, profile)
    return _build_response(df, name, profile, session_id)


@router.post("/upload", response_model=schemas.DatasetLoadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> schemas.DatasetLoadResponse:
    suffix = os.path.splitext(file.filename or "")[1]
    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        df = load_dataset(tmp_path, original_name=file.filename)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read that file: {exc}") from exc
    finally:
        os.unlink(tmp_path)

    name = file.filename or "uploaded_dataset"
    profile = profile_dataset(df)
    session_id = store.create(df, name, profile)
    return _build_response(df, name, profile, session_id)
