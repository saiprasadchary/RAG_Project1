from __future__ import annotations

from typing import List, Dict, Optional
import requests

from knowledge_assistant.api.config import Settings
from knowledge_assistant.services.retrieval import Retriever


def _google_cse_search(q: str, num: int, settings: Settings) -> List[Dict]:
    key = (settings.google_api_key or "").strip()
    cx = (settings.google_cse_id or "").strip()
    params = {"q": q, "key": key, "cx": cx, "num": max(1, min(10, int(num or 5)))}
    r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", []) or []
    out = []
    for it in items:
        out.append(
            {
                "title": it.get("title"),
                "url": it.get("link"),
                "snippet": it.get("snippet"),
                "type": "web",
            }
        )
    return out


def _local_semantic_search(q: str, num: int, settings: Settings) -> List[Dict]:
    retriever = Retriever(settings)
    results = retriever.query(q, top_k=max(1, int(num or 5)), collection_name=None, oversample_factor=4)
    out: List[Dict] = []
    for ch in results:
        snippet = (ch.text or "").strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "…"
        out.append({"title": None, "url": ch.url, "snippet": snippet, "type": "local"})
    return out


def search(q: str, num: int = 5, settings: Optional[Settings] = None) -> List[Dict]:
    settings = settings or Settings()
    # If Google CSE is configured, try it first; otherwise fallback to local search.
    if (settings.google_api_key or "") and (settings.google_cse_id or ""):
        try:
            return _google_cse_search(q, num, settings)
        except Exception:
            pass
    return _local_semantic_search(q, num, settings)