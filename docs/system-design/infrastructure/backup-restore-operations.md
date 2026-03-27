# Backup and Restore Operations

## PostgreSQL backup

Use `scripts/ops/backup_postgres.sh` with environment variables:

- `POSTGRES_HOST`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- optional `BACKUP_DIR`

Example:

```bash
POSTGRES_HOST=127.0.0.1 POSTGRES_DB=restaurant POSTGRES_USER=restaurant POSTGRES_PASSWORD=secret \
  scripts/ops/backup_postgres.sh
```

## PostgreSQL restore

Use `scripts/ops/restore_postgres.sh` with:

- `POSTGRES_HOST`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `BACKUP_FILE`

Example:

```bash
POSTGRES_HOST=127.0.0.1 POSTGRES_DB=restaurant_restore POSTGRES_USER=restaurant POSTGRES_PASSWORD=secret \
  BACKUP_FILE=./backups/restaurant_20260326T120000Z.sql.gz \
  scripts/ops/restore_postgres.sh
```

## Verification checklist

1. Run database migrations on the restored DB.
2. Run `/api/v1/system/ready/` check against restored environment.
3. Validate branch operational report endpoint for a known branch.
4. Validate a day-close list endpoint for latest business date.
