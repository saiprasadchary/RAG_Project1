from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .embed_store import EmbedStore
from ..api.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    url: str
    distance: float
    meta: Dict


def _mmr_lite_diversity(
    candidates: List[RetrievedChunk], top_k: int
) -> List[RetrievedChunk]:
    """
    Simple diversity filter by URL: prefer closest distances but avoid
    returning many chunks from the same source_url.
    """
    seen_urls = set()
    result: List[RetrievedChunk] = []
    # Sort by distance ascending (closer = better)
    for c in sorted(candidates, key=lambda x: x.distance):
        if len(result) >= top_k:
            break
        u = c.url
        if u not in seen_urls:
            seen_urls.add(u)
            result.append(c)
    # If we still don't have enough, fill with next best regardless of URL
    if len(result) < top_k:
        pool = [c for c in sorted(candidates, key=lambda x: x.distance) if c not in result]
        result.extend(pool[: max(0, top_k - len(result))])
    return result


class Retriever:
    """
    Wraps Chroma queries over one or more collections.

    If `collection_name` is provided, we query only that. Otherwise we
    query *all* collections and merge results.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self.store = EmbedStore(self.settings)

    def _query_one(
        self, collection_name: str, query: str, n_results: int
    ) -> List[RetrievedChunk]:
        col = self.store._get_collection(collection_name)
        # Compute query embedding using our SentenceTransformer and query by embedding
        q_emb = self.store.model.encode([query])  # shape (1, d)
        res = col.query(
            query_embeddings=q_emb,  # type: ignore[arg-type]
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        chunks: List[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            url = (meta or {}).get("source_url", "")
            chunks.append(RetrievedChunk(text=doc or "", url=url, distance=float(dist), meta=meta or {}))
        return chunks

    def query(
        self,
        question: str,
        top_k: int = 4,
        collection_name: Optional[str] = None,
        oversample_factor: int = 6,
    ) -> List[RetrievedChunk]:
        n_results = max(top_k * oversample_factor, top_k)
        candidates: List[RetrievedChunk] = []

        if collection_name:
            try:
                candidates.extend(self._query_one(collection_name, question, n_results))
            except Exception as e:
                logger.warning(f"Query failed on collection '{collection_name}': {e}")
        else:
            # Query across all collections and merge
            try:
                cols = self.store.client.list_collections()
            except Exception as e:
                logger.error(f"Failed to list collections: {e}")
                cols = []
            for c in cols:
                try:
                    candidates.extend(self._query_one(c.name, question, n_results))
                except Exception as e:
                    logger.debug(f"Skipping collection {c.name}: {e}")

        if not candidates:
            return []

        # Keep the global top (by distance) then apply URL diversity
        # Use a heap to pick top-N quickly if very large
        best = heapq.nsmallest(min(len(candidates), n_results), candidates, key=lambda x: x.distance)
        diverse = _mmr_lite_diversity(best, top_k=top_k)
        return diverse