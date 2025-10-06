from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class IngestRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., description="List of document URLs to ingest")

class IngestResponse(BaseModel):
    message: str = Field(..., description="Status message")
    ids: List[str] = Field(..., description="Chunk identifiers stored in the vector DB")

# UPDATED: include environment + vector collections
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Environment name")
    vector_collections: List[str] = Field(default_factory=list, description="Available vector collections")
    detail: Optional[str] = Field(None, description="Additional detail")

# ---- /ask request/response models ----
class AskRequest(BaseModel):
    question: str = Field(..., description="User question to answer using retrieved context")
    top_k: int = Field(4, ge=1, le=10, description="Number of diverse sources to use")
    domain: Optional[str] = Field(None, description="Collection name to restrict retrieval")

class SourceItem(BaseModel):
    title: Optional[str] = Field(None, description="Optional human title (not always available)")
    url: Optional[HttpUrl] = Field(None, description="Source URL")
    snippet: Optional[str] = Field(None, description="Context snippet used")

class AskResponse(BaseModel):
    answer: str = Field(..., description="Final answer with inline [n] citations")
    sources: List[SourceItem] = Field(..., description="List of sources cited in the answer")

# NEW: /search schemas
class SearchResult(BaseModel):
    title: Optional[str] = Field(None)
    url: Optional[HttpUrl] = Field(None)
    snippet: Optional[str] = Field(None)
    type: str = Field(..., description="Result type: 'web' or 'local'")

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)