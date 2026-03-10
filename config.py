"""
config.py — Central configuration for Verité Research Chatbot
All settings are loaded from environment variables with sensible defaults.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
MEMORY_DB_PATH  = BASE_DIR / "memory.db"
LOG_DIR         = BASE_DIR / "logs"

# ChromaDB needs a writable directory — /mount/src/ is read-only on HuggingFace
# So we copy it to /tmp at startup if running on HF
_SOURCE_CHROMA  = BASE_DIR / "chroma_db"
_TMP_CHROMA     = Path("/tmp/chroma_db")

def get_chroma_dir() -> Path:
    """
    Return a writable path for ChromaDB.
    On HuggingFace Spaces, /mount/src is read-only so we copy to /tmp first.
    """
    import shutil
    if not _TMP_CHROMA.exists() or not any(_TMP_CHROMA.iterdir()):
        if _SOURCE_CHROMA.exists():
            shutil.copytree(str(_SOURCE_CHROMA), str(_TMP_CHROMA), dirs_exist_ok=True)
    return _TMP_CHROMA

CHROMA_DIR = get_chroma_dir()

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # current production
MAX_TOKENS   = 2048

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"   # fast, local, no API cost

# ── Vector Store ──────────────────────────────────────────────────────────────
COLLECTION_NAME   = "verite_research"
TOP_K_VECTOR      = 10    # candidates from vector search before RRF fusion
TOP_K_BM25        = 10    # candidates from keyword search before RRF fusion
TOP_K_FINAL       = 5     # final results returned to agent after fusion
RRF_K             = 60    # RRF constant (standard value)

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE        = 800   # characters per chunk
CHUNK_OVERLAP     = 150   # overlap between consecutive chunks

# ── Memory ────────────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS    = 20   # in-session turns kept in context window
LONG_TERM_LOAD_TURNS = 6    # past turns loaded from SQLite at session start

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)

import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(stream=open(
            sys.stdout.fileno(),
            mode="w", encoding="utf-8", closefd=False, buffering=1
        )),
    ],
)

logger = logging.getLogger("verite")
