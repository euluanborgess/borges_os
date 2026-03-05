#!/usr/bin/env bash
set -euo pipefail

# Run migrations (fail fast if DB is misconfigured)
echo "[entrypoint] Running migrations..."
python -m alembic upgrade head

# Optional first-run bootstrap
if [[ "${SEED_ADMIN_ON_STARTUP:-false}" == "true" ]]; then
  echo "[entrypoint] Seeding default tenant/admin (SEED_ADMIN_ON_STARTUP=true)..."
  python seed_admin.py || true
fi

echo "[entrypoint] Starting API..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
