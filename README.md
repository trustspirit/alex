# Alex

A personal knowledge assistant desktop app. Upload PDFs, Markdown files, text documents, or YouTube videos — Alex extracts, indexes, and lets you ask questions with source citations.

Named after the [Library of Alexandria](https://en.wikipedia.org/wiki/Library_of_Alexandria), the ancient world's greatest knowledge repository.

## Features

- **Multi-source ingestion** — PDF, Markdown, plain text, YouTube videos
- **Smart PDF parsing** — 3-tier fallback: LlamaParse v2 (cloud AI) → OpenDataLoader (local) → LiteParse (local)
- **YouTube transcription** — Subtitle extraction with GPT-4o audio transcription fallback
- **Hybrid RAG** — Full-context for small collections, vector-based retrieval for large ones
- **Multiple index types** — Vector, Document Summary, and Router-based composite search
- **Multi-LLM support** — Claude, GPT, Gemini — switch providers in settings
- **Source citations** — Every answer includes traceable references with page numbers, timestamps, and relevance scores
- **Persistent knowledge** — ChromaDB vectors + SQLite metadata survive app restarts
- **Collections & tags** — Organize documents by topic
- **Chat history** — All conversations are saved and resumable
- **Fallback warnings** — Clear indicators when lower-quality parsing was used

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop | [PyWebView](https://pywebview.flowrl.com/) |
| Frontend | React + Vite + Styled-components |
| RAG Framework | [LlamaIndex](https://www.llamaindex.ai/) 0.14+ |
| PDF Parsing | [LlamaParse v2](https://cloud.llamaindex.ai) (llama-cloud SDK) / OpenDataLoader / LiteParse |
| Vector DB | [ChromaDB](https://www.trychroma.com/) |
| Metadata DB | SQLite (via SQLAlchemy) |
| LLM Providers | OpenAI, Anthropic, Google Gemini |
| Embeddings | OpenAI text-embedding-3-small |

## Project Structure

```
alex/
├── run.py                  # App entry point
├── backend/
│   ├── app.py              # PyWebView setup and dependency wiring
│   ├── bridge.py           # JS ↔ Python bridge API
│   ├── storage/            # SQLite models and repositories
│   ├── ingestion/          # Document processing pipeline
│   │   ├── loaders/        # PDF, YouTube, Markdown, Text loaders
│   │   ├── chunker.py      # Hierarchical / Semantic chunking
│   │   ├── summarizer.py   # LLM-based summaries and Q&A pairs
│   │   └── pipeline.py     # Orchestrator with background processing
│   ├── indexing/            # ChromaDB store and index management
│   ├── query/              # Hybrid router, query engine, source tracker
│   └── llm/                # Multi-LLM provider abstraction
├── frontend/
│   └── src/
│       ├── hooks/          # Business logic (useBridge, useChat, useLearn, etc.)
│       ├── components/     # Shared UI components
│       └── pages/          # Chat, Learn, Settings pages
└── tests/                  # 168+ unit tests
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- API keys for at least one LLM provider (OpenAI, Anthropic, or Google)

### Installation

```bash
# Clone and enter the project
cd alex

# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm run build
cd ..
```

### Running

```bash
# Production (uses built frontend)
python run.py

# Development (with hot reload)
# Terminal 1: React dev server
cd frontend && npm run dev

# Terminal 2: PyWebView pointing to dev server
python run.py
```

### First Launch

1. Go to **Settings** and enter your API key(s):
   - **OpenAI** (required) — for embeddings and optionally chat
   - **Anthropic** or **Gemini** — for chat (at least one LLM provider needed)
   - **LlamaParse** (recommended) — for high-quality PDF parsing. Free key at [cloud.llamaindex.ai](https://cloud.llamaindex.ai) (1,000 pages/day)
2. Select a default LLM model
3. Go to **Learn** and upload a document or paste a YouTube URL
4. Go to **Chat** and start asking questions

## Architecture

```
React (PyWebView)  ←→  Python Backend
     │                      │
     │  pywebview.api       ├── Ingestion Pipeline
     │  evaluate_js()       │   ├── Loaders (PDF/YT/MD/TXT)
     │                      │   ├── Chunker (Hierarchical/Semantic)
     │                      │   └── Summarizer + Metadata
     │                      │
     │                      ├── Index Manager
     │                      │   ├── VectorStoreIndex
     │                      │   └── DocumentSummaryIndex
     │                      │
     │                      ├── Query Engine
     │                      │   ├── Hybrid Router (full vs RAG)
     │                      │   └── Source Tracker
     │                      │
     │                      └── Storage
     │                          ├── ChromaDB (vectors)
     │                          └── SQLite (metadata)
```

## Data Storage

All data is stored locally at `~/.alex/`:
- `app.db` — SQLite database (documents, collections, chat history, settings)
- `chroma/` — ChromaDB vector embeddings
- `logs/` — Application logs

API keys are stored securely via the OS keychain (macOS Keychain).

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT
