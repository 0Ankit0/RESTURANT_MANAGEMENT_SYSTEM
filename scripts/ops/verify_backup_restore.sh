#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_HOST:?POSTGRES_HOST is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
: "${RESTORE_DB_SUFFIX:=_restore_verify}"

export PGPASSWORD="$POSTGRES_PASSWORD"
VERIFY_DB="${POSTGRES_DB}${RESTORE_DB_SUFFIX}"

psql --host "$POSTGRES_HOST" --username "$POSTGRES_USER" --dbname postgres -v ON_ERROR_STOP=1 <<SQL
DROP DATABASE IF EXISTS ${VERIFY_DB};
CREATE DATABASE ${VERIFY_DB};
SQL

gunzip -c "$BACKUP_FILE" | psql --host "$POSTGRES_HOST" --username "$POSTGRES_USER" --dbname "$VERIFY_DB"

TABLE_COUNT="$(psql --host "$POSTGRES_HOST" --username "$POSTGRES_USER" --dbname "$VERIFY_DB" -tAc "select count(*) from information_schema.tables where table_schema='public';")"
if [[ "$TABLE_COUNT" -eq 0 ]]; then
  echo "Restore verification failed: no public tables found" >&2
  exit 1
fi

echo "Restore verification passed for database: $VERIFY_DB (tables=$TABLE_COUNT)"
