"""Parent-side orchestration: validate, then run LLM-generated code in an
isolated subprocess and collect its results."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

import pandas as pd

from . import config
from .code_safety import validate_code


@dataclass
class ExecutionResult:
    success: bool
    stdout: str = ""
    error: str | None = None
    insights: str | None = None
    result: dict | None = None
    chart_paths: list[str] = field(default_factory=list)
    safety_violations: list[str] = field(default_factory=list)


def run_code(df: pd.DataFrame, code: str) -> ExecutionResult:
    violations = validate_code(code)
    if violations:
        return ExecutionResult(
            success=False,
            safety_violations=violations,
            error="Code safety check failed:\n" + "\n".join(violations),
        )

    workdir = tempfile.mkdtemp(prefix="dsc_run_")
    data_path = os.path.join(workdir, "data.pkl")
    code_path = os.path.join(workdir, "snippet.py")
    result_path = os.path.join(workdir, "result.json")

    try:
        df.to_pickle(data_path)
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        cmd = [sys.executable, config.SANDBOX_RUNNER_PATH, data_path, code_path, result_path]

        try:
            proc = subprocess.run(
                cmd,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=config.SANDBOX_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=(
                    f"Execution timed out after {config.SANDBOX_TIMEOUT_SECONDS}s "
                    "(possible infinite loop or very expensive operation)."
                ),
            )

        if not os.path.exists(result_path):
            stderr_tail = (proc.stderr or "")[-3000:]
            return ExecutionResult(
                success=False,
                error=f"Sandbox process crashed before producing a result.\nstderr:\n{stderr_tail}",
            )

        with open(result_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        chart_paths = []
        for fname in sorted(os.listdir(workdir)):
            if fname.lower().endswith(".png"):
                dest = os.path.join(config.OUTPUTS_DIR, f"{os.path.basename(workdir)}_{fname}")
                shutil.copyfile(os.path.join(workdir, fname), dest)
                chart_paths.append(dest)

        return ExecutionResult(
            success=(payload.get("status") == "success"),
            stdout=payload.get("stdout", ""),
            error=payload.get("error"),
            insights=payload.get("insights"),
            result=payload.get("result"),
            chart_paths=chart_paths,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
