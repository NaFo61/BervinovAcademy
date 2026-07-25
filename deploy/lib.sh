#!/usr/bin/env bash
# Shared helpers for server deploy scripts.
# shellcheck shell=bash

upsert_env() {
  local file="$1"
  local key="$2"
  local value="$3"
  touch "$file"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
    rm -f "${file}.bak"
  else
    printf '%s=%s\n' "$key" "$value" >>"$file"
  fi
}

retry_cmd() {
  local attempts="${1:-5}"
  local delay="${2:-8}"
  shift 2
  local n=1
  local wait="$delay"
  until "$@"; do
    if ((n >= attempts)); then
      echo "FAILED after ${attempts} attempts: $*" >&2
      return 1
    fi
    echo "Retry ${n}/${attempts} in ${wait}s: $*" >&2
    sleep "$wait"
    wait=$((wait * 2))
    if ((wait > 60)); then
      wait=60
    fi
    n=$((n + 1))
  done
}

compose_pull() {
  retry_cmd 5 8 docker compose pull "$@"
}

wait_for_health() {
  local url="${1:-http://127.0.0.1:18080/health/}"
  local attempts="${2:-15}"
  local i
  for i in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null; then
      echo "Health check OK ($url)"
      return 0
    fi
    echo "Waiting for health... ($i/$attempts)"
    sleep 10
  done
  echo "Health check failed: $url" >&2
  return 1
}

warmup_sandbox() {
  # entrypoint is already /bin/true; --no-deps avoids pulling up Kafka/DB for a no-op.
  retry_cmd 3 5 docker compose run --rm --no-deps code-check-sandbox
}
