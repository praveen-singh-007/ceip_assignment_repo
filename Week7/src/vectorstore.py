"""
vectorstore.py
------------------------------------------------------------------
Handles the "retrieval" half of the RAG pipeline:

    1. Document ingestion   -> load_pdf() / load_text()
    2. Text chunking        -> chunk_text()
    3. Embedding creation    -> embed_chunks()   (sentence-transformers)
    4. Vector indexing       -> build_index()    (FAISS)
    5. Keyword indexing      -> build keyword index (BM25)
    6. Retrieval              -> similarity_search() / keyword_search()
                                  / hybrid_search()  / rerank()

All artifacts (FAISS index + chunk metadata) can be persisted to disk
with save() and reloaded with load(), so the embedding step does not
need to be repeated every run.
------------------------------------------------------------------
"""

import os
import re
import json
import pickle
from typing import List, Dict, Optional

import numpy as np
import faiss
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

# sentence-transformers is the "pre-trained embedding model" required by the
# brief. It is imported lazily inside VectorStore so that the rest of this
# module (chunking, BM25, FAISS bookkeeping) can still be unit-tested in
# network-restricted environments without forcing a model download.


class VectorStore:
    """
    A lightweight, fully local replacement for the Cohere+Pinecone stack
    used in the reference project. Everything here runs for free:

        * Embeddings : sentence-transformers (all-MiniLM-L6-v2, 384-dim)
        * Vector DB  : FAISS (IndexFlatIP over L2-normalised vectors == cosine similarity)
        * Keyword DB : rank-bm25 (for hybrid search)
    """

    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self.embedding_model_name = embedding_model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.chunks: List[str] = []          # raw chunk text
        self.metadatas: List[Dict] = []      # {"source": ..., "page": ...}
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.Index] = None
        self.bm25: Optional[BM25Okapi] = None
        self._embed_model = None             # lazy-loaded SentenceTransformer
        self.embedding_dim: Optional[int] = None

    # ------------------------------------------------------------------ #
    # 1. DOCUMENT INGESTION
    # ------------------------------------------------------------------ #
    def load_pdf(self, pdf_path: str, skip_front_matter: bool = True) -> List[Dict]:
        """
        Extract text page-by-page from a PDF, keeping page numbers for citations.

        skip_front_matter: drops pages that are clearly navigational (table of
        contents, index) rather than substantive content. These pages tend to
        be dense lists of chapter/section titles, which can dominate keyword
        and even semantic retrieval simply because they echo the same words a
        question about that chapter would use ("the two-minute rule" appearing
        verbatim as a chapter title is a near-perfect keyword match, but the
        ToC entry itself contains none of the actual explanation).

        Tables of contents commonly span more than one page, and only the
        first page carries the literal "Contents" heading. We track a small
        bit of state while walking pages in order: once a "Contents" heading
        is seen, we keep skipping consecutive low-prose-density pages until
        real prose resumes (the introduction / chapter 1).
        """
        reader = PdfReader(pdf_path)
        pages = []
        in_front_matter = False
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = self._clean_text(text)
            if not text.strip():
                continue

            if skip_front_matter:
                if not in_front_matter and self._starts_with_contents_heading(text):
                    in_front_matter = True
                if in_front_matter:
                    if self._is_low_prose_density(text):
                        continue  # still inside the ToC -> skip
                    in_front_matter = False  # real prose resumed -> stop skipping

                # Back-of-book alphabetical index: openes with an A-Z letter
                # rail ("A B C D E ... Z Index") and runs to the end of the
                # book as comma-separated "term, page-number" entries —
                # navigational, not explanatory, so we stop ingestion there.
                if self._is_index_start(text):
                    break

            pages.append({"text": text, "source": os.path.basename(pdf_path), "page": i + 1})
        return pages

    @staticmethod
    def _is_index_start(text: str, lookahead_tokens: int = 40, min_consecutive_letters: int = 8) -> bool:
        tokens = text.split()[:lookahead_tokens]
        single_upper = sum(1 for tok in tokens if len(tok) == 1 and tok.isupper())
        return single_upper >= min_consecutive_letters

    @staticmethod
    def _starts_with_contents_heading(text: str, head_chars: int = 40) -> bool:
        return text[:head_chars].strip().lower().startswith("content")

    @staticmethod
    def _is_low_prose_density(text: str) -> bool:
        """True for pages that read as title/list lines rather than prose
        (very few sentence-ending punctuation marks relative to word count) —
        characteristic of a table of contents or index page."""
        sentence_enders = text.count(".") + text.count("!") + text.count("?")
        words = max(len(text.split()), 1)
        return (sentence_enders / words) < 0.02

    def load_text_file(self, txt_path: str) -> List[Dict]:
        """Load a plain .txt file as a single 'page'."""
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            text = self._clean_text(f.read())
        return [{"text": text, "source": os.path.basename(txt_path), "page": 1}]

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\t", " ")
        text = re.sub(r"[ \u00a0]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------ #
    # 2. TEXT CHUNKING
    # ------------------------------------------------------------------ #
    def chunk_text(self, pages: List[Dict]) -> None:
        """
        Sentence-aware sliding-window chunker.

        Splits each page into sentences, then greedily packs sentences into
        chunks of ~chunk_size characters, carrying `chunk_overlap` characters
        of trailing context into the next chunk so retrieval doesn't lose
        meaning at chunk borders.
        """
        sentence_split_re = re.compile(r"(?<=[.!?])\s+")

        for page in pages:
            sentences = sentence_split_re.split(page["text"])
            current = ""
            for sentence in sentences:
                if not sentence:
                    continue
                if len(current) + len(sentence) + 1 <= self.chunk_size:
                    current = f"{current} {sentence}".strip()
                else:
                    if current:
                        self.chunks.append(current)
                        self.metadatas.append({"source": page["source"], "page": page["page"]})
                    # start new chunk, carrying overlap from the tail of the previous chunk
                    overlap_text = current[-self.chunk_overlap:] if current else ""
                    current = f"{overlap_text} {sentence}".strip()
            if current:
                self.chunks.append(current)
                self.metadatas.append({"source": page["source"], "page": page["page"]})

    def ingest(self, file_path: str) -> None:
        """Convenience method: load + chunk a PDF or .txt file in one call."""
        if file_path.lower().endswith(".pdf"):
            pages = self.load_pdf(file_path)
        elif file_path.lower().endswith(".txt"):
            pages = self.load_text_file(file_path)
        else:
            raise ValueError("Unsupported file type. Use .pdf or .txt")
        self.chunk_text(pages)

    # ------------------------------------------------------------------ #
    # 3. EMBEDDING CREATION
    # ------------------------------------------------------------------ #
    @property
    def embed_model(self):
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer
            self._embed_model = SentenceTransformer(self.embedding_model_name)
        return self._embed_model

    def embed_chunks(self, batch_size: int = 64) -> None:
        if not self.chunks:
            raise ValueError("No chunks to embed. Call ingest() first.")
        vectors = self.embed_model.encode(
            self.chunks,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,  # so inner product == cosine similarity
        )
        self.embeddings = vectors.astype("float32")
        self.embedding_dim = self.embeddings.shape[1]

    # ------------------------------------------------------------------ #
    # 4. VECTOR DATABASE (FAISS) + KEYWORD INDEX (BM25)
    # ------------------------------------------------------------------ #
    def build_index(self) -> None:
        if self.embeddings is None:
            raise ValueError("No embeddings found. Call embed_chunks() first.")
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # cosine similarity via normalised vectors
        self.index.add(self.embeddings)

        tokenized_corpus = [c.lower().split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def build_all(self, file_path: str) -> None:
        """Full ingestion pipeline: ingest -> embed -> index."""
        self.ingest(file_path)
        self.embed_chunks()
        self.build_index()

    # ------------------------------------------------------------------ #
    # 5 & 6. QUERY EMBEDDING + RETRIEVAL
    # ------------------------------------------------------------------ #
    def similarity_search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Pure vector (semantic) search."""
        query_vec = self.embed_model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        scores, idxs = self.index.search(query_vec, top_k)
        return self._format_results(idxs[0], scores[0])

    def keyword_search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Pure BM25 keyword search."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_idxs = np.argsort(scores)[::-1][:top_k]
        return self._format_results(top_idxs, scores[top_idxs])

    def hybrid_search(self, query: str, top_k: int = 4, alpha: float = 0.6) -> List[Dict]:
        """
        Hybrid retrieval: alpha * normalised_vector_score + (1 - alpha) * normalised_bm25_score.
        alpha=1.0 -> pure vector search, alpha=0.0 -> pure keyword search.
        """
        n = len(self.chunks)
        query_vec = self.embed_model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        scores, idxs = self.index.search(query_vec, n)

        # IMPORTANT: FAISS returns (scores, indices) sorted by similarity, NOT in
        # chunk order. We must scatter each score back to its own chunk's
        # position so it lines up with kw_scores (which IS in chunk order)
        # before combining the two. Naively zipping the raw `scores` array
        # with `kw_scores` silently mixes unrelated chunks together.
        vec_scores_aligned = np.full(n, -1.0, dtype="float32")  # cosine sim floor
        for score, idx in zip(scores[0], idxs[0]):
            if idx >= 0:
                vec_scores_aligned[idx] = score

        tokenized_query = query.lower().split()
        kw_scores = np.asarray(self.bm25.get_scores(tokenized_query), dtype="float32")

        vec_norm = self._minmax(vec_scores_aligned)
        kw_norm = self._minmax(kw_scores)

        combined = alpha * vec_norm + (1 - alpha) * kw_norm
        top_idxs = np.argsort(combined)[::-1][:top_k]
        return self._format_results(top_idxs, combined[top_idxs])

    def rerank(self, query: str, candidates: List[Dict], top_n: int = 4,
               cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> List[Dict]:
        """
        Optional re-ranking layer using a cross-encoder model for a more
        accurate (but slower) relevance score over a shortlist of candidates.
        """
        from sentence_transformers import CrossEncoder
        if not hasattr(self, "_cross_encoder") or self._cross_encoder is None:
            self._cross_encoder = CrossEncoder(cross_encoder_name)
        pairs = [(query, c["text"]) for c in candidates]
        scores = self._cross_encoder.predict(pairs)
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)[:top_n]

    @staticmethod
    def _minmax(arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr, dtype="float32")
        lo, hi = arr.min(), arr.max()
        if hi - lo < 1e-9:
            return np.zeros_like(arr)
        return (arr - lo) / (hi - lo)

    def _format_results(self, idxs, scores) -> List[Dict]:
        results = []
        for idx, score in zip(idxs, scores):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append({
                "text": self.chunks[idx],
                "score": float(score),
                "source": self.metadatas[idx]["source"],
                "page": self.metadatas[idx]["page"],
            })
        return results

    # ------------------------------------------------------------------ #
    # PERSISTENCE
    # ------------------------------------------------------------------ #
    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "store.pkl"), "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "metadatas": self.metadatas,
                "embedding_model_name": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "embedding_dim": self.embedding_dim,
            }, f)

    def load(self, directory: str) -> None:
        self.index = faiss.read_index(os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "store.pkl"), "rb") as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.metadatas = data["metadatas"]
        self.embedding_model_name = data["embedding_model_name"]
        self.chunk_size = data["chunk_size"]
        self.chunk_overlap = data["chunk_overlap"]
        self.embedding_dim = data["embedding_dim"]
        tokenized_corpus = [c.lower().split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
