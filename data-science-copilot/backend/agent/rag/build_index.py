"""Build the FAISS index for the documentation corpus.

Run directly to (re)build the on-disk index:
    python -m agent.rag.build_index
"""

from __future__ import annotations

import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from .. import config
from .chunking import chunk_text

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _load_corpus_documents() -> list[Document]:
    documents = []
    for fname in sorted(os.listdir(config.DOCS_CORPUS_DIR)):
        if not fname.lower().endswith((".md", ".txt")):
            continue
        path = os.path.join(config.DOCS_CORPUS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        source = os.path.splitext(fname)[0]
        for i, chunk in enumerate(chunk_text(text)):
            documents.append(
                Document(page_content=chunk, metadata={"source": source, "chunk": i})
            )
    return documents


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def build_and_save_index() -> FAISS:
    documents = _load_corpus_documents()
    if not documents:
        raise RuntimeError(f"No documentation files found in {config.DOCS_CORPUS_DIR}")

    embeddings = get_embeddings()
    store = FAISS.from_documents(documents, embeddings)
    os.makedirs(config.RAG_INDEX_DIR, exist_ok=True)
    store.save_local(config.RAG_INDEX_DIR)
    return store


if __name__ == "__main__":
    store = build_and_save_index()
    print(f"Indexed into {config.RAG_INDEX_DIR}")
