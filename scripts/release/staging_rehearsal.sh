#!/usr/bin/env bash
set -euo pipefail

: "${STAGING_API_URL:?STAGING_API_URL is required}"
: "${BACKUP_DIR:=./backups}"

echo "[1/5] Validating docs and template health"
python scripts/validate_documentation.py
python scripts/check_template_health.py

echo "[2/5] Running backup"
./scripts/ops/backup_postgres.sh

LATEST_BACKUP="$(ls -1t "$BACKUP_DIR"/*.sql.gz | head -n1)"
if [[ -z "${LATEST_BACKUP:-}" ]]; then
  echo "No backup generated" >&2
  exit 1
fi

echo "[3/5] Verifying backup restore in rehearsal database"
BACKUP_FILE="$LATEST_BACKUP" ./scripts/ops/verify_backup_restore.sh

echo "[4/5] Smoke-checking staging health"
curl -fsS "$STAGING_API_URL/health" >/dev/null

echo "[5/5] Rehearsal complete"
echo "Backup: $LATEST_BACKUP"
