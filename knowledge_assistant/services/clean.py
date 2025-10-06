from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", text or "").strip()

def _chunk_by_tokens(text: str, max_tokens: int = 250, overlap: int = 50) -> List[str]:
    try:
        import tiktoken
    except ImportError:
        logger.warning("tiktoken not available; falling back to character-based splitting")
        raise
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    if not tokens:
        return []
    chunks: List[str] = []
    start = 0
    step = max_tokens - overlap
    while start < len(tokens):
        end = min(len(tokens), start + max_tokens)
        chunk_tokens = tokens[start:end]
        chunk_str = encoding.decode(chunk_tokens)
        chunk_cleaned = clean_text(chunk_str)
        if chunk_cleaned:
            chunks.append(chunk_cleaned)
        start += step
    return chunks

def _chunk_by_chars(text: str, max_chars: int = 1000, overlap_chars: int = 200) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    step = max_chars - overlap_chars
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(clean_text(chunk))
        start += step
    return chunks

def chunk_text(text: str, max_tokens: int = 250, overlap: int = 50) -> List[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    try:
        return _chunk_by_tokens(cleaned, max_tokens=max_tokens, overlap=overlap)
    except Exception:
        approx_chars = max_tokens * 4
        approx_overlap = overlap * 4
        return _chunk_by_chars(cleaned, max_chars=approx_chars, overlap_chars=approx_overlap)
