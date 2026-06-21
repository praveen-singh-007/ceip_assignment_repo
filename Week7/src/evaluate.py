"""
evaluate.py
------------------------------------------------------------------
End-to-end validation script for the evaluator's checklist:

    1. Builds the index from data/atomic_habits.pdf
    2. Runs a fixed set of dynamic sample questions through the full
       RAG pipeline (retrieve -> augment -> generate)
    3. Prints grounded answers to the console
    4. Writes a timestamped, structured log to docs/validation_log.md

Run with (from the project root, with GROQ_API_KEY set in your
environment or in a .env file):

    python src/evaluate.py
------------------------------------------------------------------
"""

import os
import sys
import time
import datetime

from dotenv import load_dotenv
from vectorstore import VectorStore
from chatbot import Chatbot

load_dotenv()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "atomic_habits.pdf")
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "validation_log.md")

SAMPLE_QUESTIONS = [
    "What is the main idea of the book?",
    "What are the four laws of behavior change?",
    "What is habit stacking and how does it work?",
    "How does the author explain identity-based habits?",
    "What role does the two-minute rule play in building habits?",
    "What does the book say about breaking bad habits?",
    "What is the cure for the photosynthesis problem?",  # off-topic control question
]


def run_evaluation(chunk_size=800, chunk_overlap=150, top_k=4, search_mode="hybrid"):
    print(f"Loading source document: {DATA_PATH}")
    vs = VectorStore(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    t0 = time.time()
    vs.build_all(DATA_PATH)
    build_time = time.time() - t0
    print(f"Indexed {len(vs.chunks)} chunks ({vs.embedding_dim}-dim) in {build_time:.1f}s\n")

    bot = Chatbot(
        vectorstore=vs,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        top_k=top_k,
        search_mode=search_mode,
    )

    log_lines = [
        f"# Validation Log",
        f"",
        f"Run timestamp: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"",
        f"## Index build stats",
        f"- Source document: `{os.path.basename(DATA_PATH)}`",
        f"- Chunks created: {len(vs.chunks)}",
        f"- Embedding dimension: {vs.embedding_dim}",
        f"- Chunk size / overlap: {chunk_size} / {chunk_overlap} chars",
        f"- Search mode: {search_mode}",
        f"- Index build time: {build_time:.2f}s",
        f"",
        f"## Sample Question Results",
        f"",
    ]

    for i, question in enumerate(SAMPLE_QUESTIONS, 1):
        print(f"[{i}/{len(SAMPLE_QUESTIONS)}] Q: {question}")
        t0 = time.time()
        answer, sources = bot.respond(question)
        latency = time.time() - t0
        print(f"A: {answer}\n   (retrieved {len(sources)} chunks in {latency:.2f}s)\n")

        log_lines.append(f"### Q{i}: {question}")
        log_lines.append(f"**Answer:** {answer}")
        log_lines.append(f"")
        log_lines.append(f"**Latency:** {latency:.2f}s &nbsp;|&nbsp; **Chunks retrieved:** {len(sources)}")
        log_lines.append(f"")
        log_lines.append(f"**Top retrieved context:**")
        for s in sources:
            preview = s["text"][:220].replace("\n", " ")
            log_lines.append(f"- (p.{s['page']}, score={s['score']:.3f}) {preview}...")
        log_lines.append(f"")
        log_lines.append(f"---")
        log_lines.append(f"")

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"Validation log written to {LOG_PATH}")


if __name__ == "__main__":
    run_evaluation()
