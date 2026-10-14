#!/usr/bin/env sh
set -eu

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

printf '\n== Docker service status ==\n'
if command -v docker >/dev/null 2>&1; then
  docker compose ps || true
else
  echo "Docker CLI not found; skipping docker compose ps."
fi

printf '\n== Cloud API health ==\n'
curl -sS -i --max-time 5 "${API_BASE_URL}/health" || true

printf '\n== Database health ==\n'
curl -sS -i --max-time 5 "${API_BASE_URL}/health/db" || true

printf '\n== Camera configuration in database ==\n'
curl -sS -i --max-time 5 "${API_BASE_URL}/api/v1/cameras" || true

printf '\n== Recent Cloud API logs ==\n'
if command -v docker >/dev/null 2>&1; then
  docker compose logs --tail=100 cloud-api || true
fi

printf '\nDiagnostic requests completed. Review HTTP status codes and logs above.\n'
