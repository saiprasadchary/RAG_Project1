from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "local")
    port: int = int(os.getenv("PORT", "8000"))
    llm_backend: str = os.getenv("LLM_BACKEND", "openai")
    embed_model_name: str = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
    chroma_directory: str = os.getenv("CHROMA_DIRECTORY", "./chroma_db")

    def __post_init__(self) -> None:
        self.chroma_directory = os.path.abspath(self.chroma_directory)
        try:
            self.port = int(self.port)
        except ValueError as exc:
            raise ValueError(f"Invalid PORT value: {self.port}") from exc
            
google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")