"""Static (AST-based) safety gate for LLM-generated analysis code.

Runs in the parent process *before* anything is handed to the sandbox subprocess.
This is not a substitute for OS-level sandboxing (see README's Security Notes) --
it blocks the common, well-known restricted-exec escape patterns (dunder
attribute chains, dynamic import/eval, direct file/network access) while
letting normal pandas/numpy/matplotlib/seaborn analysis code run unmodified.
"""

from __future__ import annotations

import ast

ALLOWED_TOP_LEVEL_MODULES = {
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "json",
    "math",
    "re",
    "statistics",
    "datetime",
    "collections",
    "itertools",
}

FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "open", "input", "__import__", "globals",
    "locals", "vars", "breakpoint", "exit", "quit", "help", "memoryview",
    "object", "staticmethod", "classmethod", "super",
}


def validate_code(code: str) -> list[str]:
    """Return a list of human-readable violation messages (empty == safe)."""
    violations: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Code does not parse as valid Python: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in ALLOWED_TOP_LEVEL_MODULES:
                    violations.append(f"Disallowed import: '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top not in ALLOWED_TOP_LEVEL_MODULES:
                violations.append(f"Disallowed import: 'from {node.module} import ...'")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                violations.append(f"Disallowed dunder attribute access: '.{node.attr}'")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                violations.append(f"Disallowed name used: '{node.id}'")

    seen: set[str] = set()
    unique_violations = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            unique_violations.append(v)
    return unique_violations
