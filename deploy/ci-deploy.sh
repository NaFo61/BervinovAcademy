#!/usr/bin/env bash
# CI deploy on the server. Expects DOCKERHUB_USER in the environment.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "${APP_DIR}/lib.sh"
cd "$APP_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found" >&2
  exit 1
fi

: "${DOCKERHUB_USER:?DOCKERHUB_USER is required}"
FRONTEND_URL="${FRONTEND_URL:-https://academy.bervinov-miron.ru}"

echo "[ci-deploy] syncing .env"
upsert_env .env DOCKERHUB_USER "$DOCKERHUB_USER"
upsert_env .env SUB_PATH ""
upsert_env .env FRONTEND_URL "$FRONTEND_URL"

echo "[ci-deploy] pulling images (with retries)"
compose_pull

echo "[ci-deploy] warming code-check-sandbox"
warmup_sandbox

echo "[ci-deploy] starting stack"
docker compose up -d --remove-orphans

echo "[ci-deploy] pruning unused images"
docker image prune -f || true

echo "[ci-deploy] health check"
if ! wait_for_health "http://127.0.0.1:18080/health/" 15; then
  docker compose ps || true
  docker compose logs --tail=80 backend nginx || true
  exit 1
fi

echo "[ci-deploy] done"
docker compose ps
