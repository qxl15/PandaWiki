#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker is required" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[ERROR] docker compose plugin is required" >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  rand() { openssl rand -hex 16; }

  sed -i "s/change_me_postgres/$(rand)/" .env
  sed -i "s/change_me_redis/$(rand)/" .env
  sed -i "s/change_me_nats/$(rand)/" .env
  sed -i "s/change_me_minio/$(rand)/" .env
  sed -i "s/change_me_jwt/$(rand)/" .env
  sed -i "s/change_me_admin/$(rand)/" .env

  echo "[INFO] generated deploy/custom/.env"
  echo "[INFO] Please edit RAG_CT_RAG_BASE_URL and RAG_CT_RAG_API_KEY in .env before production use."
fi

if ! grep -q '^RAG_CT_RAG_BASE_URL=' .env; then
  echo "[ERROR] missing RAG_CT_RAG_BASE_URL in .env" >&2
  exit 1
fi

if ! grep -q '^RAG_CT_RAG_API_KEY=' .env; then
  echo "[ERROR] missing RAG_CT_RAG_API_KEY in .env" >&2
  exit 1
fi

echo "[INFO] Building and starting PandaWiki custom stack..."
docker compose up -d --build

echo "[DONE] PandaWiki custom deployment started"
echo "- API: http://<server-ip>:8000"
echo "- Frontend App: http://<server-ip>:3010"
echo "- Caddy: http://<server-ip>:80"
