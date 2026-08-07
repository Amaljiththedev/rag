#!/usr/bin/env bash
# Apply every migration in order. Idempotent - safe to re-run.
# Usage: PGURL="postgresql://user:pass@host:5432/db" ./scripts/migrate.sh
set -euo pipefail

: "${PGURL:?PGURL must be set, e.g. postgresql://rag_user:pass@localhost:5432/rag_db}"

for f in "$(dirname "$0")"/migrations/*.sql; do
  echo "[migrate] applying $(basename "$f")"
  psql "$PGURL" -v ON_ERROR_STOP=1 -f "$f"
done

echo "[migrate] all migrations applied"
