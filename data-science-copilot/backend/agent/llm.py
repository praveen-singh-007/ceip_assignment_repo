"""Thin wrapper around the Groq-hosted chat model used for code generation."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from . import config


def get_llm(temperature: float = 0.0) -> ChatGroq:
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to a .env file (see .env.example) or "
            "export it before launching the app."
        )
    return ChatGroq(
        model=config.GROQ_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=temperature,
        max_retries=2,
        timeout=60,
    )


def get_completion(llm: ChatGroq, system_prompt: str, user_message: str) -> str:
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
    )
    return response.content
