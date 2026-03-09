"""
vector_store.py — ChromaDB wrapper with hybrid search (vector + BM25)

Architecture:
  - Vector search  : ChromaDB cosine similarity with sentence-transformers
  - Keyword search : BM25 (rank_bm25) over all stored documents
  - Fusion         : Reciprocal Rank Fusion (RRF) to merge both ranked lists

RRF formula: score(d) = Σ  1 / (k + rank_i(d))
  k = 60 (standard constant that prevents top-rank dominance)
"""

import logging
from functools import lru_cache

import chromadb
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger("verite.vector_store")


# ── Singleton helpers ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
    return SentenceTransformer(config.EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_chroma_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = client.get_collection(config.COLLECTION_NAME)
    logger.info(f"ChromaDB collection loaded — {collection.count()} chunks")
    return collection


# ── Vector Store Class ────────────────────────────────────────────────────────

class VectorStore:
    """
    Handles all retrieval operations.
    Lazily loads models so startup is fast.
    """

    def __init__(self):
        self._model      = None
        self._collection = None
        self._bm25       = None
        self._all_docs   = None   # cached list of all documents for BM25

    # ── Lazy loaders ──────────────────────────────────────────────────────────

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = _get_embedding_model()
        return self._model

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = _get_chroma_collection()
        return self._collection

    def _ensure_bm25(self) -> None:
        """Build BM25 index lazily from all stored documents."""
        if self._bm25 is not None:
            return

        logger.info("Building BM25 index from stored documents…")
        result = self.collection.get(include=["documents", "metadatas"])

        self._all_docs = [
            {
                "text":        doc,
                "source":      meta.get("source", "unknown"),
                "page":        meta.get("page", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "id":          doc_id,
            }
            for doc, meta, doc_id in zip(
                result["documents"],
                result["metadatas"],
                result["ids"],
            )
        ]

        tokenised    = [doc["text"].lower().split() for doc in self._all_docs]
        self._bm25   = BM25Okapi(tokenised)
        logger.info(f"BM25 index built over {len(self._all_docs)} chunks")

    # ── Individual search methods ──────────────────────────────────────────────

    def vector_search(self, query: str, top_k: int = config.TOP_K_VECTOR) -> list[dict]:
        """
        Semantic vector search via ChromaDB.
        Returns list of result dicts with rank positions.
        """
        embedding = self.model.encode([query])[0].tolist()

        results = self.collection.query(
            query_embeddings = [embedding],
            n_results        = top_k,
            include          = ["documents", "metadatas", "distances"],
        )

        hits = []
        for i, (doc, meta, dist) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ):
            hits.append({
                "rank":   i + 1,
                "text":   doc,
                "source": meta.get("source", "unknown"),
                "page":   meta.get("page", 0),
                "score":  1 - dist,       # cosine similarity (0–1, higher = better)
            })

        return hits

    def bm25_search(self, query: str, top_k: int = config.TOP_K_BM25) -> list[dict]:
        """
        Keyword-based BM25 search.
        Returns list of result dicts with rank positions.
        """
        self._ensure_bm25()

        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        hits = []
        for rank, idx in enumerate(top_indices, start=1):
            doc = self._all_docs[idx]
            if scores[idx] > 0:          # skip zero-score results
                hits.append({
                    "rank":   rank,
                    "text":   doc["text"],
                    "source": doc["source"],
                    "page":   doc["page"],
                    "score":  float(scores[idx]),
                })

        return hits

    # ── Hybrid Search with RRF ─────────────────────────────────────────────────

    def hybrid_search(
        self,
        query:       str,
        top_k_final: int = config.TOP_K_FINAL,
        rrf_k:       int = config.RRF_K,
    ) -> list[dict]:
        """
        Hybrid search: combine vector + BM25 results via Reciprocal Rank Fusion.

        RRF ensures that a chunk appearing high in BOTH rankings scores best,
        even if it isn't the absolute top result in either list alone.

        Returns top_k_final de-duplicated, fused result dicts for the agent.
        """
        vector_hits = self.vector_search(query)
        bm25_hits   = self.bm25_search(query)

        # Build RRF score map keyed by (source, page, text[:80]) for dedup
        def _key(hit: dict) -> str:
            return f"{hit['source']}__p{hit['page']}__{hit['text'][:80]}"

        rrf_scores: dict[str, float] = {}
        hit_store:  dict[str, dict]  = {}

        for hit in vector_hits:
            k = _key(hit)
            rrf_scores[k]  = rrf_scores.get(k, 0.0) + 1.0 / (rrf_k + hit["rank"])
            hit_store[k]   = hit

        for hit in bm25_hits:
            k = _key(hit)
            rrf_scores[k]  = rrf_scores.get(k, 0.0) + 1.0 / (rrf_k + hit["rank"])
            if k not in hit_store:
                hit_store[k] = hit

        # Sort by RRF score descending
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for key, rrf_score in ranked[:top_k_final]:
            hit = hit_store[key].copy()
            hit["rrf_score"] = round(rrf_score, 6)
            results.append(hit)

        logger.info(
            f"Hybrid search for '{query[:60]}' → "
            f"{len(vector_hits)} vector + {len(bm25_hits)} BM25 → "
            f"{len(results)} fused results"
        )
        return results

    # ── Utility ───────────────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        """Check if the vector store has documents."""
        try:
            return self.collection.count() > 0
        except Exception:
            return False
