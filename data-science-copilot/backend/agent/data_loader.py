"""Load CSV / Excel / JSON uploads into a pandas DataFrame and profile them."""

from __future__ import annotations

import json
import os

import pandas as pd


class UnsupportedFileTypeError(Exception):
    pass


def load_dataset(file_path: str, original_name: str | None = None) -> pd.DataFrame:
    """Read a CSV, Excel (.xlsx/.xls) or JSON file into a DataFrame."""
    name = (original_name or file_path).lower()

    if name.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    elif name.endswith(".json"):
        df = _load_json(file_path)
    else:
        ext = os.path.splitext(name)[1] or "unknown"
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Please upload a CSV, Excel (.xlsx), or JSON file."
        )

    df.columns = [str(c).strip() for c in df.columns]
    return df


def _load_json(file_path: str) -> pd.DataFrame:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return pd.DataFrame(data)

    if isinstance(data, dict):
        for key in ("records", "data", "rows", "results", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return pd.DataFrame(value)
        try:
            return pd.DataFrame(data)
        except ValueError:
            return pd.DataFrame([data])

    raise ValueError("JSON file must contain a list of records or a dict of columns.")


def profile_dataset(df: pd.DataFrame) -> dict:
    """Summarize shape, dtypes, nulls, duplicates and samples -- powers both the
    UI's data-quality panel and the schema text fed to the LLM."""
    null_counts = df.isnull().sum()
    n_rows = len(df)

    columns = []
    for col in df.columns:
        series = df[col]
        columns.append(
            {
                "name": str(col),
                "dtype": str(series.dtype),
                "null_count": int(null_counts[col]),
                "null_pct": round(float(null_counts[col]) / max(n_rows, 1) * 100, 2),
                "unique_count": int(series.nunique(dropna=True)),
                "sample_values": [str(v) for v in series.dropna().unique()[:5].tolist()],
            }
        )

    return {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": columns,
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
        "datetime_columns": df.select_dtypes(include="datetime").columns.tolist(),
        "head": df.head(5).astype(str).to_dict(orient="records"),
    }


def schema_summary_text(df: pd.DataFrame, profile: dict | None = None) -> str:
    """Compact natural-language schema description used inside LLM prompts."""
    profile = profile or profile_dataset(df)
    lines = [
        f"DataFrame `df` has {profile['shape']['rows']} rows and "
        f"{profile['shape']['columns']} columns."
    ]
    for col in profile["columns"]:
        lines.append(
            f"- {col['name']} (dtype={col['dtype']}, nulls={col['null_count']}, "
            f"unique={col['unique_count']}, examples={col['sample_values']})"
        )
    if profile["duplicate_rows"]:
        lines.append(f"Duplicate rows detected: {profile['duplicate_rows']}")
    return "\n".join(lines)
