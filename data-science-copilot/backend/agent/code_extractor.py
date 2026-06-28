"""Pull the Python code block out of an LLM response."""

import re

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(llm_response: str) -> str:
    matches = _CODE_BLOCK_RE.findall(llm_response)
    if matches:
        return max(matches, key=len).strip()
    return llm_response.strip()
