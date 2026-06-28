import os

from dotenv import load_dotenv

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_AGENT_DIR)

# Load explicitly from backend/.env regardless of the process's current
# working directory (load_dotenv() with no args only searches upward from
# CWD, which is fragile once this is launched via uvicorn/streamlit from
# different locations).
load_dotenv(os.path.join(BASE_DIR, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_SELF_HEAL_ATTEMPTS = int(os.getenv("MAX_SELF_HEAL_ATTEMPTS", "4"))
SANDBOX_TIMEOUT_SECONDS = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30"))

OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
RAG_INDEX_DIR = os.path.join(BASE_DIR, "rag_index")
DOCS_CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag", "docs_corpus")
SANDBOX_RUNNER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox_runner.py")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
