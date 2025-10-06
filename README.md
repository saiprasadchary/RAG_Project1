# Modular Knowledge Assistant (Backend Core)

FastAPI backend for a modular knowledge assistant. Ingests HTML/PDF URLs, cleans and chunks text, embeds with MiniLM (SentenceTransformers), and stores vectors in a local ChromaDB instance with deterministic IDs.

## Quick Start

```bash
# 1) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment (optional)
cp .env.example .env

# 4) Run the API
uvicorn knowledge_assistant.api.main:app --port ${PORT:-8000} --reload
```

## API

### Health
```bash
curl http://127.0.0.1:8000/health
```

### Ingest
```bash
curl -X POST http://127.0.0.1:8000/ingest   -H "Content-Type: application/json"   -d '{
    "urls": [
      "https://en.wikipedia.org/wiki/Transformer_(machine_learning)",
      "https://arxiv.org/pdf/1706.03762.pdf"
    ]
  }'
```

## Project Structure

```
Knowledge_assistant/
├─ knowledge_assistant/
│  ├─ __init__.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  ├─ main.py
│  │  └─ models.py
│  └─ services/
│     ├─ __init__.py
│     ├─ clean.py
│     ├─ embed_store.py
│     └─ ingest.py
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Notes
- Requires Python 3.11+.
- PDF ingestion needs `pdfplumber` (already included).
- ChromaDB persists to `CHROMA_DIRECTORY` (default `./chroma_db`). Make sure the process can write to that path.
- This is the backend core; retrieval/ask endpoints and UI can be added next.
