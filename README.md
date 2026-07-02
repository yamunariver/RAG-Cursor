<<<<<<< HEAD
# Enterprise RAG

Production-oriented retrieval-augmented generation platform for 29,000+ documents, designed for air-gapped deployment with Docker Compose and Kubernetes migration in mind.

## Stack

- **LLM**: Ollama (Qwen2.5, Llama 3.2, Gemma 3, vision models)
- **Embeddings / reranker**: bge-m3, nomic-embed-text, bge-reranker-large
- **Vector DB**: Qdrant (HNSW, cosine, payload indexes, snapshots)
- **Metadata**: PostgreSQL
- **Object storage**: MinIO
- **Cache / workers**: Redis + Celery
- **API**: FastAPI
- **UI**: React + TypeScript
- **Proxy**: Nginx
- **OCR / scan**: Tesseract, ClamAV

## Quick start

```bash
cd enterprise-rag
cp .env.example .env   # already copied on first setup
chmod +x scripts/*.sh
./scripts/start-dev.sh
```

Or step by step:

```bash
docker compose up -d --build
./scripts/pull-models.sh
docker compose exec backend python /scripts/bootstrap-knowledge-bases.py
```

Open http://localhost and sign in with:

- Email: `admin@local`
- Password: `admin123!`

## Apple Silicon (M1/M2/M3) / local dev

The official ClamAV image is **amd64-only**, so it is disabled by default on Mac (`ENABLE_VIRUS_SCAN=false`). The core stack runs natively on arm64.

On production Ubuntu/Rocky (amd64), enable virus scanning with:

```bash
# set ENABLE_VIRUS_SCAN=true in .env first
docker compose --profile clamav up -d
```

## GPU profile

For NVIDIA GPU hosts, stop the CPU Ollama service and start the GPU profile:

```bash
docker compose stop ollama
docker compose --profile gpu up -d ollama-gpu
```

## Knowledge layout

Documents are organized under `knowledge/` by department:

```
knowledge/
├── Electrical/
├── Mechanical/
├── Civil/
├── AutoCAD/
├── SOP/
├── Manuals/
├── Policies/
├── HR/
├── Networking/
├── Servers/
├── UPS/
├── Firewalls/
└── Drawings/
```

Run the bootstrap script to create matching Qdrant collections and PostgreSQL knowledge bases.

## Pipelines

**Ingestion**: upload → virus scan → type detection → OCR (if needed) → extraction → chunking → embeddings → Qdrant + PostgreSQL

**Retrieval**: question → embedding → hybrid vector + BM25 search → reranking → context → Ollama → cited answer

## API

Base path: `/api/v1`

- `POST /auth/token` — login
- `GET /knowledge-bases` — list KBs (RBAC-aware)
- `POST /documents/upload` — upload and queue indexing
- `POST /chat` — grounded Q&A with citations
- `POST /chat/stream` — streaming NDJSON responses

## Scale notes

- Tune `CELERY_CONCURRENCY` and `INGESTION_WORKERS` for 40–60 parallel indexing workers on 80-core hosts
- Use dedicated NVMe for Qdrant and document storage
- Enable Qdrant snapshots to NAS/object storage for backup
- One Qdrant collection per knowledge base

## Security

Change `APP_SECRET_KEY`, PostgreSQL credentials, and MinIO credentials before production. Replace the seeded admin account after first login.
=======
# RAG-Cursor
>>>>>>> 886dca3f2acfe64ceb86918851f86ef8cffbb95d
