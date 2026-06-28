"""Load (or lazily build) the FAISS index and expose a simple retrieve() API."""

from __future__ import annotations

import os
import threading

from langchain_community.vectorstores import FAISS

from .. import config
from .build_index import build_and_save_index, get_embeddings

_store: FAISS | None = None
_lock = threading.Lock()


def _load_store() -> FAISS:
    global _store
    if _store is not None:
        return _store

    with _lock:
        if _store is not None:
            return _store

        index_file = os.path.join(config.RAG_INDEX_DIR, "index.faiss")
        if os.path.exists(index_file):
            _store = FAISS.load_local(
                config.RAG_INDEX_DIR,
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )
        else:
            _store = build_and_save_index()
        return _store


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return up to k {"source", "text", "score"} dicts most relevant to query."""
    store = _load_store()
    results = store.similarity_search_with_score(query, k=k)
    docs = []
    for doc, score in results:
        docs.append(
            {
                "source": doc.metadata.get("source", "unknown"),
                "text": doc.page_content,
                "score": float(score),
            }
        )
    return docs
