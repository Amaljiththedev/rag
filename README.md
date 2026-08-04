# Enterprise Production RAG Assistant & Evaluation Harness

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16--pgvector-blue.svg)](https://github.com/pgvector/pgvector)
[![SentenceTransformers](https://img.shields.io/badge/Embeddings-SentenceTransformer--all--MiniLM--L6--v2-orange.svg)](https://www.sbert.net/)

An enterprise-grade Retrieval-Augmented Generation (RAG) system featuring local offline embeddings, pgvector vector search, BM25 full-text keyword retrieval, Reciprocal Rank Fusion (RRF), LangGraph graph orchestration, and automated evaluation metrics.

---

## 🚀 Key Features

- 🧠 **Local & Offline Embedding Pipeline**: Powered by `SentenceTransformer('all-MiniLM-L6-v2')` (384-dimensional dense vectors), completely cached and usable offline without API key dependencies.
- ⚡ **Hybrid Search Engine**: Combines **Dense Vector Similarity Search** (`pgvector`) with **Lexical Keyword Search** merged via **Reciprocal Rank Fusion (RRF)**.
- 🗄️ **pgvector Integration**: Native PostgreSQL vector storage using `pgvector/pgvector:pg16` for high-performance vector indexing and similarity lookups.
- 📄 **Section-Aware Document Chanking**: Document loading and chunking for SEC filings and unstructured text/PDF documents.
- 🕸️ **LangGraph Orchestration**: Deterministic RAG state machine for query expansion, retrieval, context validation, and guardrails.
- 🐳 **Docker & Docker Compose**: Fully containerized environment orchestrating the FastAPI service (`rag_app`) and PostgreSQL vector database (`rag_postgres`).
- 🧪 **Automated Testing & Evals**: Comprehensive `pytest` test suite and CLI evaluation harness.

---

## 🏗️ System Architecture

```text
┌────────────────┐     ┌─────────────────────┐     ┌───────────────────────┐
│ User / API Client │ ──► │  FastAPI Application │ ──► │ Ingestion / Chunking  │
└────────────────┘     └──────────┬──────────┘     └──────────┬────────────┘
                                  │                           │
                                  ▼                           ▼
                        ┌───────────────────┐     ┌───────────────────────┐
                        │ LangGraph RAG     │ ──► │ SentenceTransformer   │
                        │ Graph Engine      │     │ (all-MiniLM-L6-v2)    │
                        └─────────┬─────────┘     └──────────┬────────────┘
                                  │                           │
                                  ▼                           ▼
                        ┌─────────────────────────────────────────┐
                        │        Hybrid Retriever (RRF)           │
                        │  ┌──────────────────┬────────────────┐  │
                        │  │  pgvector Dense  │  BM25 Keyword  │  │
                        │  └─────────┬────────┴────────┬───────┘  │
                        └────────────┼─────────────────┼──────────┘
                                     ▼                 ▼
                        ┌─────────────────────────────────────────┐
                        │     PostgreSQL 16 Vector DB             │
                        └─────────────────────────────────────────┘
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **Docker Desktop / Docker Engine**

### 2. Clone & Environment Setup
```bash
git clone https://github.com/Amaljiththedev/rag.git
cd rag

# Copy environment template
cp .env.example .env
```

### 3. Run with Docker Compose
To build and launch the containerized application and PostgreSQL database:

```bash
docker compose up --build -d
```

Verify services are running and healthy:
- **FastAPI Web Service**: `http://localhost:8001`
- **Health Check Endpoint**: `http://localhost:8001/health`
- **PostgreSQL Vector DB**: `localhost:5432` (`user: rag_user`, `db: rag_db`)

---

## 💻 Local Development Setup

### 1. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run Test Scripts

#### Test Local SentenceTransformer Embeddings
```bash
python scripts/test_sentence_transformer.py
```

#### Test PostgreSQL Connection & `pgvector` Extension
```bash
python scripts/test_db_connection.py
```

#### Execute Ingestion & Embedding Pipeline
```bash
$env:PYTHONPATH="backend"; python backend/app/retrieval/embeddings.py
```

---

## 🧪 Running Unit Tests

Run pytest with `PYTHONPATH` set to `backend`:

```bash
python -m pytest tests/test_embeddings.py tests/test_hybrid_retrieval.py
```

---

## 📂 Project Structure

```text
.
├── backend/
│   └── app/
│       ├── api/               # FastAPI endpoints & routes
│       ├── db/                # SQLAlchemy async models & pgvector schema
│       ├── ingestion/         # Document loaders & section-aware chunkers
│       ├── retrieval/         # SentenceTransformer embeddings & RRF Hybrid search
│       ├── generation/        # LLM response generation
│       └── config.py          # Pydantic environment configuration
├── data/                      # Sample documents & embedded chunk JSON outputs
├── evals/                     # RAG evaluation harness & LLM-as-a-judge runner
├── scripts/                   # Utility & verification scripts
├── tests/                     # Automated unit and integration tests
├── Dockerfile                 # Container build definition for FastAPI backend
├── docker-compose.yml         # Container orchestration (FastAPI + pgvector)
├── pyproject.toml             # Project dependencies & pytest configuration
└── requirements.txt           # Python package requirements
```

---

## 🛡️ License

MIT License. Designed and built for enterprise RAG pipeline deployment.
