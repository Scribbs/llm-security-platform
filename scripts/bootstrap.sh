#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== LLM Security Assessment Platform – Bootstrap ==="

if [ ! -f .env ]; then
  echo "Creating .env from .env.example …"
  cp .env.example .env
  echo "Please edit .env and set strong passwords before going to production."
fi

echo "Building images (this may take several minutes the first time)…"
docker compose build backend frontend

echo "Starting infrastructure + application…"
docker compose up -d postgres redis keycloak

echo "Waiting for Keycloak to become healthy…"
for i in {1..40}; do
  if docker compose exec -T keycloak bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080' 2>/dev/null; then
    echo "Keycloak is up."
    break
  fi
  sleep 3
done

echo "Starting backend + frontend…"
docker compose up -d backend frontend

echo ""
echo "=== Bootstrap complete ==="
echo "Frontend:        http://localhost:3000"
echo "Backend API:     http://localhost:8000/docs"
echo "Keycloak Admin:  http://localhost:8080  (admin / value of KEYCLOAK_ADMIN_PASSWORD)"
echo ""
echo "Default realm users (from realm import):"
echo "  admin   / admin123"
echo "  analyst / analyst123"
echo ""
echo "Tip: run 'docker compose logs -f backend' to watch job execution."
