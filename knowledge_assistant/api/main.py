from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from knowledge_assistant.api.config import Settings
from knowledge_assistant.api.models import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    AskRequest,
    AskResponse,
    SourceItem,
    SearchResponse,
)
from knowledge_assistant.services.ingest import ingest_and_embed
from knowledge_assistant.services.retrieval import Retriever
from knowledge_assistant.services.llm_adapter import LLMAdapter, SourceForPrompt
from knowledge_assistant.services.embed_store import EmbedStore
from knowledge_assistant.services.metrics import METRICS
from knowledge_assistant.services import search as search_service

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Modular Knowledge Assistant", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        store = EmbedStore(settings)
        try:
            cols = [c.name for c in store.client.list_collections()]
        except Exception:
            cols = []
        return HealthResponse(status="ok", environment=settings.environment, vector_collections=cols, detail="service is running")

    @app.post("/ingest", response_model=IngestResponse)
    async def ingest(request: IngestRequest) -> IngestResponse:
        import time as _time
        t0 = _time.time()
        METRICS.inc("/ingest")
        try:
            ids: List[str] = await asyncio.to_thread(
                ingest_and_embed, [str(u) for u in request.urls], settings
            )
        except Exception as exc:
            logger.exception("Ingestion failed")
            raise HTTPException(status_code=500, detail=str(exc))
        duration_ms = int((_time.time() - t0) * 1000)
        METRICS.record_ingest(docs=len(request.urls), chunks=len(ids), duration_ms=duration_ms)
        return IngestResponse(message="Ingestion complete", ids=ids)

    # ---- NEW: /ask ----
    @app.post("/ask", response_model=AskResponse)
    async def ask(req: AskRequest) -> AskResponse:
        t0 = time.time()
        METRICS.inc("/ask")
        t_ret0 = time.time()

        retriever = Retriever(settings)
        llm = LLMAdapter(settings)

        # retrieval
        retrieved = await asyncio.to_thread(
            retriever.query,
            req.question,
            req.top_k,
            req.domain,  # may be None (search across all)
        )
        retrieval_ms = int((time.time() - t_ret0) * 1000)

        if not retrieved:
            answer = "I don't know based on the available sources."
            return AskResponse(answer=answer, sources=[])

        # Prepare sources for prompt + response
        src_for_prompt: List[SourceForPrompt] = []
        sources_payload: List[SourceItem] = []
        for i, ch in enumerate(retrieved, start=1):
            snippet = ch.text.strip()
            if len(snippet) > 300:
                snippet = snippet[:300] + "…"
            url = ch.url or ""
            src_for_prompt.append(SourceForPrompt(url=url, snippet=snippet))
            sources_payload.append(SourceItem(title=None, url=url or None, snippet=snippet))

        # generation (dummy/local)
        answer = await asyncio.to_thread(llm.answer, req.question, src_for_prompt)

        # Telemetry log (console JSON)
        telemetry = {
            "endpoint": "/ask",
            "domain": req.domain or "*",
            "top_k": req.top_k,
            "n_returned": len(retrieved),
            "answer_chars": len(answer),
            "latency_ms": int((time.time() - t0) * 1000),
        }
        logger.info(json.dumps(telemetry))
        total_ms = int((time.time() - t0) * 1000)
        METRICS.record_ask(req.top_k, len(retrieved), total_ms, len(answer), retrieval_ms)

        return AskResponse(answer=answer, sources=sources_payload)

    @app.get("/search", response_model=SearchResponse)
    async def search(q: str = Query(..., min_length=1), num: int = Query(5, ge=1, le=10)) -> SearchResponse:
        from knowledge_assistant.services.metrics import METRICS as _M #import issue here -3
        _M.inc("/search")
        results = await asyncio.to_thread(search_service.search, q, num, settings)
        return SearchResponse(results=results)

    @app.get("/metrics")
    async def metrics() -> dict:
        return METRICS.snapshot()

    return app

app = create_app()