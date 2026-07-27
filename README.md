# Production RAG Assistant & Evaluation System

Enterprise-grade Retrieval-Augmented Generation (RAG) backend implementing:
- **Hybrid Retrieval**: Dense Vector Search (pgvector) + BM25 Full-Text Keyword Search merged via Reciprocal Rank Fusion (RRF).
- **LangGraph Orchestration**: Deterministic RAG graph state machine.
- **Guardrails & Confidence Thresholds**: Auto-refusal and context validation.
- **Evaluation Harness**: CLI evaluation runner with LLM-as-a-judge scoring and retrieval hit-rate metrics.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```
