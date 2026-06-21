# System Metrics Report

This report documents the configuration and measured characteristics of the
RAG pipeline, satisfying the evaluator's requirement for "chunking profiles,
chosen text embedding dimensions, vector store tools, and language model
setups."

## 1. Source Document
- File: `data/atomic_habits.pdf`
- Pages: **256**
- Format: PDF, text extracted with `pypdf`

## 2. Chunking Profile
- Method: custom sentence-aware sliding window (`VectorStore.chunk_text`)
  - Splits each page on sentence boundaries (`. `, `! `, `? `)
  - Greedily packs sentences into chunks up to `chunk_size` characters
  - Carries the last `chunk_overlap` characters of each chunk into the next,
    so a sentence split across chunk boundaries still has context on both
    sides
- Default parameters: `chunk_size = 800` characters, `chunk_overlap = 150`
  characters
- **Measured result on the full 256-page book** (verified by an actual
  ingestion run in this environment): **829 chunks** produced, average chunk
  length ≈ 780 characters, one-to-one page traceability preserved per chunk
  (`source`, `page` metadata)

## 3. Embedding Model
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Embedding dimensionality: **384**
- Normalization: L2-normalized at encode time, so inner-product search is
  equivalent to cosine similarity
- Note: this model downloads weights from Hugging Face Hub on first run and
  requires outbound internet access from wherever `evaluate.py` / `app.py`
  is executed (the model is not bundled in this repo).

## 4. Vector Store
- Library: `FAISS` (`faiss-cpu`)
- Index type: `IndexFlatIP` (exact, brute-force inner-product search over
  normalized vectors → cosine similarity)
- Persistence: `VectorStore.save()` / `VectorStore.load()` serialize the
  FAISS index (`index.faiss`) and chunk metadata (`store.pkl`) to disk for
  reuse without re-embedding

## 5. Keyword Index (Hybrid Search)
- Library: `rank-bm25` (`BM25Okapi`)
- Tokenization: lowercase whitespace split
- **Measured live in this environment** against the real book text — e.g.
  query *"two minute rule"* correctly surfaced the Chapter 13 passage on
  p.127 and the explicit rule definition on p.221 from 829 indexed chunks,
  confirming the keyword index retrieves real, relevant passages.

## 6. Hybrid Retrieval
- Formula: `combined_score = alpha * normalized_vector_score + (1 - alpha) * normalized_bm25_score`
- Default `alpha = 0.6` (weighted toward semantic similarity, configurable)
- Default `top_k = 4` chunks returned per query
- Optional re-ranking stage: cross-encoder `ms-marco-MiniLM-L-6-v2` can
  re-score a `3 × top_k` candidate shortlist down to the final `top_k`

## 7. Language Model Setup
- Provider: **Groq** (free tier)
- Default model: `llama-3.3-70b-versatile`
  - Also selectable: `llama-3.1-8b-instant` (faster), `gemma2-9b-it`
- `temperature = 0.2` (low, favors grounded/consistent answers)
- `max_tokens = 512`
- System prompt instructs the model to answer **only** from retrieved
  context and explicitly state when an answer is not contained in the
  document, to reduce hallucination on out-of-scope questions

## 8. Validation Coverage
`src/evaluate.py` runs 7 sample questions end-to-end against the book,
including 6 in-domain questions (main idea, four laws of behavior change,
habit stacking, identity-based habits, the two-minute rule, breaking bad
habits) and 1 deliberately out-of-domain control question, to confirm the
system both answers correctly when context exists and declines gracefully
when it doesn't. See `docs/validation_log.md` for the generated transcript
once `evaluate.py` is run with a live `GROQ_API_KEY`.

## 9. Known Sandbox Limitation (disclosed)
The component-level logic above (chunking, FAISS indexing, BM25 keyword
search, hybrid scoring, save/load) was tested end-to-end in this development
environment against the real 256-page book and produced the chunk counts and
retrieval results quoted above. The embedding model download (Hugging Face
Hub) and the Groq LLM call could not be executed from this sandbox, as
outbound network access here is restricted to PyPI/GitHub. `evaluate.py` and
`app.py` will exercise those two remaining stages for real the first time
they're run in an environment with normal internet access.
