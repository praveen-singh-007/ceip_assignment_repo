"""Worker script executed inside an isolated subprocess.

Invoked as:
    python sandbox_runner.py <data_pickle_path> <code_path> <result_json_path>

Reads the DataFrame, execs the analysis code against a restricted namespace, and
writes a JSON summary (stdout, error/traceback, insights, result, status) to
<result_json_path>. Any chart the code saves (e.g. plt.savefig("chart.png")) is
left in the current working directory for the parent process to collect.
"""

from __future__ import annotations

import builtins
import collections
import contextlib
import datetime
import io
import itertools
import json
import math
import re
import statistics
import sys
import traceback

import numpy as np
import pandas as pd

ALLOWED_BUILTIN_NAMES = [
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float", "format",
    "frozenset", "int", "isinstance", "len", "list", "map", "max", "min", "print",
    "range", "repr", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip",
    "type", "Exception", "ValueError", "KeyError", "TypeError", "IndexError",
    "StopIteration", "ZeroDivisionError", "AttributeError", "RuntimeError", "NotImplementedError",
    "getattr", "hasattr", "setattr", "slice", "iter", "next", "True", "False", "None",
    "divmod", "pow", "chr", "ord",
]

# Modules the generated code is allowed to `import`. The parent-process AST
# check (agent/code_safety.py) already enforces this same allowlist on the
# source text before the subprocess is even started; this restricted
# __import__ enforces it again at runtime so plain `import x` / `from x
# import y` statements keep working (Python's IMPORT_NAME opcode needs a
# working __import__ in __builtins__) without opening the door to arbitrary
# imports.
ALLOWED_IMPORT_MODULES = {
    "pandas", "numpy", "matplotlib", "seaborn", "json", "math", "re",
    "statistics", "datetime", "collections", "itertools",
}


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    top_level = name.split(".")[0]
    if top_level not in ALLOWED_IMPORT_MODULES:
        raise ImportError(f"Import of '{name}' is not allowed in this sandbox.")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in ALLOWED_BUILTIN_NAMES if hasattr(builtins, name)}
    safe["__import__"] = _restricted_import
    return safe


def _stringify(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _serialize_result(value):
    if value is None:
        return None
    try:
        if isinstance(value, pd.DataFrame):
            head = value.head(200)
            return {
                "type": "dataframe",
                "columns": [str(c) for c in head.columns],
                "data": head.astype(str).to_dict(orient="records"),
            }
        if isinstance(value, pd.Series):
            head = value.reset_index().head(200)
            return {
                "type": "dataframe",
                "columns": [str(c) for c in head.columns],
                "data": head.astype(str).to_dict(orient="records"),
            }
        if isinstance(value, dict):
            return {"type": "dict", "data": json.loads(json.dumps(value, default=str))}
        return {"type": "text", "data": str(value)}
    except Exception:
        return {"type": "text", "data": str(value)}


def main() -> None:
    data_path, code_path, result_path = sys.argv[1:4]

    df = pd.read_pickle(data_path)
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    # A single namespace is used for both globals and locals. exec() with two
    # *separate* dicts makes top-level comprehensions/generator expressions
    # (e.g. `all(col in df.columns for col in cols)`) raise NameError on `df`,
    # because such nested code objects resolve free variables via LOAD_GLOBAL
    # against the globals dict only, never the locals dict. Using one shared
    # dict for both sidesteps that scoping pitfall entirely.
    safe_namespace = {
        "__builtins__": _safe_builtins(),
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "json": json,
        "math": math,
        "re": re,
        "statistics": statistics,
        "datetime": datetime,
        "collections": collections,
        "itertools": itertools,
        "df": df,
    }

    stdout_buf = io.StringIO()
    output = {
        "status": "error",
        "stdout": "",
        "error": None,
        "insights": None,
        "result": None,
    }

    try:
        with contextlib.redirect_stdout(stdout_buf):
            exec(compile(code, "<analysis_code>", "exec"), safe_namespace)
        output["status"] = "success"
        output["insights"] = _stringify(safe_namespace.get("insights"))
        output["result"] = _serialize_result(safe_namespace.get("result"))
    except Exception:
        output["error"] = traceback.format_exc()
    finally:
        output["stdout"] = stdout_buf.getvalue()
        plt.close("all")

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(output, f)


if __name__ == "__main__":
    main()
