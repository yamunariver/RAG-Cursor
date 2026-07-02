#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "Starting core services..."
docker compose up -d --build

echo "Waiting for backend..."
until docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')" >/dev/null 2>&1; do
  sleep 2
done

echo "Pulling Ollama models (this can take a while on first run)..."
./scripts/pull-models.sh

echo "Bootstrapping knowledge bases..."
docker compose exec -T backend python /scripts/bootstrap-knowledge-bases.py

echo
echo "Ready: http://localhost"
echo "Login: admin@local / admin123!"
