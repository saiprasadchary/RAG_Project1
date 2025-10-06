from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List

import chromadb
from chromadb.api import Collection
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer  # type: ignore

from ..api.config import Settings

logger = logging.getLogger(__name__)

@dataclass
class EmbedStore:
    settings: Settings
    _model: SentenceTransformer | None = field(default=None, init=False, repr=False)
    _client: chromadb.Client | None = field(default=None, init=False, repr=False)
    _collections: Dict[str, Collection] = field(default_factory=dict, init=False, repr=False)

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading embedding model {self.settings.embed_model_name}…")
            self._model = SentenceTransformer(self.settings.embed_model_name)
        return self._model

    @property
    def client(self) -> chromadb.Client:
        if self._client is None:
            logger.info(f"Initialising ChromaDB at {self.settings.chroma_directory}…")
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self, name: str) -> Collection:
        if name not in self._collections:
            try:
                collection = self.client.get_collection(name)
            except Exception:
                collection = self.client.create_collection(name)
            self._collections[name] = collection
        return self._collections[name]

    def upsert_embeddings(
        self,
        collection_name: str,
        texts: List[str],
        ids: List[str],
        metadatas: List[dict],
    ) -> None:
        if not texts:
            return
        collection = self._get_collection(collection_name)
        embeddings = self.model.encode(texts)  # type: ignore
        try:
            collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        except AttributeError:
            logger.info("Collection does not support upsert; falling back to add/delete+add")
            existing = []
            try:
                res = collection.get(ids=ids)
                existing = res.get("ids", [])  # type: ignore
            except Exception:
                pass
            if existing:
                collection.delete(ids=existing)
            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

def deterministic_id(prefix: str, content: str) -> str:
    h = hashlib.sha256()
    h.update(prefix.encode("utf-8"))
    h.update(content.encode("utf-8"))
    return h.hexdigest()
