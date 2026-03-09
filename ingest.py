"""
ingest.py — PDF ingestion pipeline for Verité Research Chatbot

Run this script once (locally) to:
  1. Load all PDFs from data/
  2. Extract text with page numbers
  3. Chunk with overlap
  4. Generate sentence-transformer embeddings
  5. Store in ChromaDB with metadata

Usage:
    python ingest.py
    python ingest.py --reset   # wipe existing DB before ingesting
"""

import argparse
import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import Generator

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger("verite.ingest")


# ── Text Extraction ────────────────────────────────────────────────────────────

def extract_pages(pdf_path: Path) -> list[dict]:
    """
    Extract text from every page of a PDF.
    Returns list of {"page": int, "text": str, "source": str}
    """
    reader   = PdfReader(str(pdf_path))
    pages    = []
    source   = pdf_path.stem          # filename without extension

    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        # Collapse excessive whitespace while preserving paragraph breaks
        text = re.sub(r"\n{3,}", "\n\n", raw)
        text = re.sub(r"[ \t]+", " ", text).strip()

        if len(text) > 50:            # skip near-empty pages (headers/footers)
            pages.append({"page": i, "text": text, "source": source})

    logger.info(f"  Extracted {len(pages)} pages from '{pdf_path.name}'")
    return pages


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_page(
    page_data: dict,
    chunk_size: int  = config.CHUNK_SIZE,
    overlap: int     = config.CHUNK_OVERLAP,
) -> Generator[dict, None, None]:
    """
    Split a single page into overlapping chunks.
    Yields dicts with keys: text, source, page, chunk_index, chunk_id
    """
    text        = page_data["text"]
    source      = page_data["source"]
    page_num    = page_data["page"]
    start       = 0
    chunk_index = 0

    while start < len(text):
        end   = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if len(chunk) > 50:          # skip trivially small chunks
            # Deterministic ID — same PDF always gets same IDs
            chunk_id = hashlib.md5(
                f"{source}_{page_num}_{chunk_index}".encode()
            ).hexdigest()

            yield {
                "text":        chunk,
                "source":      source,
                "page":        page_num,
                "chunk_index": chunk_index,
                "chunk_id":    chunk_id,
            }
            chunk_index += 1

        if end == len(text):
            break
        start = end - overlap          # move back by overlap for continuity


# ── ChromaDB Setup ─────────────────────────────────────────────────────────────

def get_or_create_collection(reset: bool = False) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
            logger.info("Existing collection deleted (--reset flag).")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name     = config.COLLECTION_NAME,
        metadata = {"hnsw:space": "cosine"},   # cosine similarity for embeddings
    )
    return collection


# ── Embedding ─────────────────────────────────────────────────────────────────

def load_embedding_model() -> SentenceTransformer:
    logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    return model


def embed_chunks(chunks: list[dict], model: SentenceTransformer) -> list[list[float]]:
    texts      = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.tolist()


# ── Main Ingestion ─────────────────────────────────────────────────────────────

def ingest_pdf(
    pdf_path:   Path,
    collection: chromadb.Collection,
    model:      SentenceTransformer,
) -> int:
    """
    Full pipeline for a single PDF.
    Returns number of chunks ingested.
    """
    logger.info(f"Processing: {pdf_path.name}")

    # 1. Extract pages
    pages = extract_pages(pdf_path)
    if not pages:
        logger.warning(f"  No text extracted from {pdf_path.name}. Skipping.")
        return 0

    # 2. Chunk all pages
    all_chunks = []
    for page_data in pages:
        all_chunks.extend(chunk_page(page_data))

    logger.info(f"  Generated {len(all_chunks)} chunks")

    # 3. Check for already-ingested chunks (idempotent)
    existing_ids = set(collection.get(ids=[c["chunk_id"] for c in all_chunks])["ids"])
    new_chunks   = [c for c in all_chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        logger.info(f"  All chunks already in DB. Skipping.")
        return 0

    # 4. Embed new chunks
    logger.info(f"  Embedding {len(new_chunks)} new chunks…")
    embeddings = embed_chunks(new_chunks, model)

    # 5. Upsert into ChromaDB
    collection.upsert(
        ids        = [c["chunk_id"]    for c in new_chunks],
        embeddings = embeddings,
        documents  = [c["text"]        for c in new_chunks],
        metadatas  = [
            {
                "source":      c["source"],
                "page":        c["page"],
                "chunk_index": c["chunk_index"],
            }
            for c in new_chunks
        ],
    )

    logger.info(f"  ✓ Stored {len(new_chunks)} chunks for '{pdf_path.name}'")
    return len(new_chunks)


def run_ingestion(reset: bool = False) -> None:
    pdf_files = sorted(config.DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        logger.error(
            f"No PDFs found in {config.DATA_DIR}. "
            "Place your Verité PDFs in the data/ folder and re-run."
        )
        sys.exit(1)

    logger.info(f"Found {len(pdf_files)} PDF(s): {[f.name for f in pdf_files]}")

    collection = get_or_create_collection(reset=reset)
    model      = load_embedding_model()

    total_chunks = 0
    for pdf_path in pdf_files:
        total_chunks += ingest_pdf(pdf_path, collection, model)

    total_in_db = collection.count()
    logger.info(
        f"\n{'─'*50}\n"
        f"Ingestion complete.\n"
        f"  New chunks added : {total_chunks}\n"
        f"  Total in DB      : {total_in_db}\n"
        f"{'─'*50}"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Verité PDFs into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing ChromaDB collection before ingesting",
    )
    args = parser.parse_args()
    run_ingestion(reset=args.reset)
