from __future__ import annotations

import io
import logging
import mimetypes
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup  # type: ignore

from .clean import chunk_text
from .embed_store import EmbedStore, deterministic_id
from ..api.config import Settings

logger = logging.getLogger(__name__)

def _fetch_html_text(url: str) -> str:
    logger.info(f"Fetching HTML document from {url}")
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text

def _fetch_pdf_text(url: str) -> str:
    logger.info(f"Fetching PDF document from {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required for PDF ingestion") from exc
    data = io.BytesIO(response.content)
    texts: List[str] = []
    with pdfplumber.open(data) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                texts.append(page_text)
    return "\n".join(texts)

def _detect_pdf(url: str) -> bool:
    path = url.lower().split("?")[0]
    return path.endswith(".pdf") or mimetypes.guess_type(path)[0] == "application/pdf"

def ingest_and_embed(urls: List[str], settings: Settings | None = None) -> List[str]:
    settings = settings or Settings()
    store = EmbedStore(settings)
    all_ids: List[str] = []
    for url in urls:
        try:
            if _detect_pdf(url):
                raw_text = _fetch_pdf_text(url)
            else:
                raw_text = _fetch_html_text(url)
        except requests.HTTPError as http_err:
            logger.error(f"Failed to fetch {url}: {http_err}")
            continue
        except Exception as err:
            logger.error(f"Error processing {url}: {err}")
            continue

        chunks = chunk_text(raw_text)
        if not chunks:
            logger.warning(f"No text extracted from {url}")
            continue

        ids: List[str] = []
        metadata_list: List[dict] = []
        parsed = urlparse(url)
        domain = parsed.netloc or "default"
        for idx, chunk in enumerate(chunks):
            cid = deterministic_id(url, chunk)
            ids.append(cid)
            metadata_list.append({
                "source_url": url,
                "chunk_index": idx,
                "domain": domain,
            })
        store.upsert_embeddings(domain, chunks, ids, metadata_list)
        all_ids.extend(ids)
    return all_ids
