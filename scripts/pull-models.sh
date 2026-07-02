#!/usr/bin/env bash
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-180}"

models=(
  "qwen2.5:7b-instruct"
  "qwen2.5:14b-instruct"
  "llama3.2"
  "gemma3"
  "qwen2.5-vl"
  "bge-m3"
  "nomic-embed-text"
  "bge-reranker-large"
)

echo "Waiting for Ollama at ${OLLAMA_HOST}..."
elapsed=0
until curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
  if (( elapsed >= MAX_WAIT_SECONDS )); then
    echo "Ollama did not become ready within ${MAX_WAIT_SECONDS}s."
    echo "Start the stack first: docker compose up -d --build"
    exit 1
  fi
  sleep 3
  elapsed=$((elapsed + 3))
  echo "  still waiting (${elapsed}s)..."
done

echo "Pulling Ollama models from ${OLLAMA_HOST}..."
for model in "${models[@]}"; do
  echo "-> ${model}"
  curl -fsS "${OLLAMA_HOST}/api/pull" -d "{\"name\":\"${model}\"}" || echo "  warning: failed to pull ${model}"
done

echo "Done."
