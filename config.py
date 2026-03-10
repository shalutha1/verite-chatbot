"""
config.py — Central configuration for Verité Research Chatbot
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "data"
LOG_DIR        = BASE_DIR / "logs"

# ── Memory DB — use /tmp on HuggingFace (read-only mount) ─────────────────────
_IS_HF = Path("/mount/src").exists()

if _IS_HF:
    MEMORY_DB_PATH = Path("/tmp/memory.db")
    # Copy existing memory.db to /tmp if exists
    _src_memory = BASE_DIR / "memory.db"
    if _src_memory.exists() and not MEMORY_DB_PATH.exists():
        shutil.copy2(str(_src_memory), str(MEMORY_DB_PATH))
else:
    MEMORY_DB_PATH = BASE_DIR / "memory.db"

# ── ChromaDB — copy to /tmp on HuggingFace ────────────────────────────────────
_SOURCE_CHROMA = BASE_DIR / "chroma_db"
_TMP_CHROMA    = Path("/tmp/chroma_db")

def _setup_chroma_dir() -> Path:
    if _IS_HF:
        # Always copy fresh on HuggingFace to ensure writable copy
        if _TMP_CHROMA.exists():
            shutil.rmtree(str(_TMP_CHROMA))
        if _SOURCE_CHROMA.exists():
            shutil.copytree(str(_SOURCE_CHROMA), str(_TMP_CHROMA))
            print(f"[config] Copied chroma_db to /tmp — files: {list(_TMP_CHROMA.iterdir())}")
        else:
            _TMP_CHROMA.mkdir(parents=True, exist_ok=True)
            print(f"[config] WARNING: source chroma_db not found at {_SOURCE_CHROMA}")
        return _TMP_CHROMA
    else:
        return _SOURCE_CHROMA

CHROMA_DIR = _setup_chroma_dir()

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS   = 2048

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Vector Store ──────────────────────────────────────────────────────────────
COLLECTION_NAME = "verite_research"
TOP_K_VECTOR    = 10
TOP_K_BM25      = 10
TOP_K_FINAL     = 5
RRF_K           = 60

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150

# ── Memory ────────────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS    = 20
LONG_TERM_LOAD_TURNS = 6

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers= [
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("verite")
logger.info(f"CHROMA_DIR = {CHROMA_DIR}")
logger.info(f"MEMORY_DB  = {MEMORY_DB_PATH}")
logger.info(f"IS_HF      = {_IS_HF}")
