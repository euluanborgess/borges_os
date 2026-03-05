#!/usr/bin/env bash
set -euo pipefail

# Run migrations (best-effort; fail fast if DB is misconfigured)
echo "[entrypoint] Running migrations..."
python -m alembic upgrade head

echo "[entrypoint] Starting API..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
