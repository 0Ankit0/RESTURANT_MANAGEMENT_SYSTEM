#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

export PGPASSWORD="$POSTGRES_PASSWORD"

gunzip -c "$BACKUP_FILE" | psql \
  --host "$POSTGRES_HOST" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB"

echo "Restore completed from: $BACKUP_FILE"
