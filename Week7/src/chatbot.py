"""
chatbot.py
------------------------------------------------------------------
Handles the "augmentation + generation" half of the RAG pipeline:

    1. Takes a user query
    2. Retrieves grounding context from a VectorStore (hybrid search)
    3. Builds a single grounded prompt (context + query)
    4. Calls a free Groq-hosted LLM to generate the final answer
------------------------------------------------------------------
"""

import os
from typing import List, Dict, Tuple

from groq import Groq


SYSTEM_PROMPT = (
    "You are a precise document question-answering assistant. "
    "Answer the user's question using ONLY the information in the provided "
    "context. If the answer is not contained in the context, say "
    "\"I don't have enough information in the document to answer that.\" "
    "Do not use outside knowledge. Keep answers concise and cite the page "
    "number(s) you used in the form (p. X) where relevant."
)


class Chatbot:
    """Thin wrapper around the Groq chat-completions API, grounded by a VectorStore."""

    def __init__(
        self,
        vectorstore,
        groq_api_key: str = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 512,
        top_k: int = 4,
        search_mode: str = "hybrid",   # "vector" | "keyword" | "hybrid"
        use_reranker: bool = False,
    ):
        api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "No Groq API key provided. Pass groq_api_key= or set the "
                "GROQ_API_KEY environment variable (see .env.example)."
            )
        self.client = Groq(api_key=api_key)
        self.vectorstore = vectorstore
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_k = top_k
        self.search_mode = search_mode
        self.use_reranker = use_reranker
        self.history: List[Dict] = []  # [{"role": "user"/"assistant", "content": ...}]

    # ------------------------------------------------------------------ #
    # RETRIEVAL
    # ------------------------------------------------------------------ #
    def retrieve(self, query: str) -> List[Dict]:
        if self.search_mode == "vector":
            results = self.vectorstore.similarity_search(query, top_k=self.top_k)
        elif self.search_mode == "keyword":
            results = self.vectorstore.keyword_search(query, top_k=self.top_k)
        else:
            # over-fetch a slightly larger candidate pool, optionally rerank down to top_k
            fetch_k = self.top_k * 3 if self.use_reranker else self.top_k
            results = self.vectorstore.hybrid_search(query, top_k=fetch_k)
            if self.use_reranker:
                results = self.vectorstore.rerank(query, results, top_n=self.top_k)
        return results

    # ------------------------------------------------------------------ #
    # PROMPT CONSTRUCTION
    # ------------------------------------------------------------------ #
    @staticmethod
    def build_prompt(query: str, context_chunks: List[Dict]) -> str:
        context_block = "\n\n".join(
            f"[Source: {c['source']}, page {c['page']}]\n{c['text']}"
            for c in context_chunks
        )
        return (
            f"Context:\n{context_block}\n\n"
            f"Question: {query}\n\n"
            f"Answer the question using only the context above."
        )

    # ------------------------------------------------------------------ #
    # GENERATION
    # ------------------------------------------------------------------ #
    def respond(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Runs one full RAG turn: retrieve -> augment -> generate.
        Returns (answer_text, retrieved_chunks).
        """
        retrieved = self.retrieve(query)
        user_prompt = self.build_prompt(query, retrieved)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_prompt})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        answer = completion.choices[0].message.content

        # keep conversational memory lightweight (raw query, not the bulky context block)
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer})

        return answer, retrieved
