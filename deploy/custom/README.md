# PandaWiki Custom One-Click Deployment

This directory provides a **self-hosted one-click installer** for your custom PandaWiki branch.

## Quick Start

```bash
cd deploy/custom
./install.sh
```

The installer will:
1. Generate `.env` from `.env.example` (with random secrets) if not exists.
2. Build custom backend images from this repository (`backend/Dockerfile.api`, `backend/Dockerfile.consumer`).
3. Build custom web app image from this repository (`deploy/custom/Dockerfile.app`).
4. Start full dependency stack with Docker Compose.

## Services

- Postgres
- Redis
- NATS
- MinIO
- Caddy (admin API via unix socket)
- panda-wiki-api
- panda-wiki-consumer
- panda-wiki-app

## Required Manual Config

Before production use, update `deploy/custom/.env`:
- `RAG_CT_RAG_BASE_URL`
- `RAG_CT_RAG_API_KEY`

## Common Operations

```bash
# start/rebuild
cd deploy/custom && docker compose up -d --build

# stop
cd deploy/custom && docker compose down

# view logs
cd deploy/custom && docker compose logs -f panda-wiki-api
```
