#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/compose.prod.yml"
NGINX_FILE="$ROOT_DIR/deploy/nginx/prod.conf"
FRONTEND_ENV="$ROOT_DIR/frontend/.env.production"
BACKEND_ENV="$ROOT_DIR/backend/.env.production"

required_files=(
  "$COMPOSE_FILE"
  "$NGINX_FILE"
  "$FRONTEND_ENV"
  "$BACKEND_ENV"
)

frontend_required_keys=(
  "NEXT_PUBLIC_APP_NAME"
  "NEXT_PUBLIC_API_URL"
  "NEXT_PUBLIC_WS_URL"
)

backend_required_keys=(
  "APP_ENV"
  "SECRET_KEY"
  "PASSWORD_PEPPER"
  "POSTGRES_SERVER"
  "POSTGRES_USER"
  "POSTGRES_PASSWORD"
  "POSTGRES_DB"
  "DATABASE_URL"
  "SYNC_DATABASE_URL"
  "REDIS_HOST"
  "REDIS_PORT"
  "MINIO_ROOT_USER"
  "MINIO_ROOT_PASSWORD"
  "FRONTEND_URL"
  "SERVER_HOST"
)

errors=0

require_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "[ERROR] Required file is missing: $file" >&2
    errors=1
  fi
}

has_key() {
  local key="$1"
  local file="$2"
  rg -q "^[[:space:]]*${key}=" "$file"
}

key_value() {
  local key="$1"
  local file="$2"
  awk -F= -v k="$key" '$1 ~ "^[[:space:]]*"k"[[:space:]]*$" {v=$2} END {sub(/^[[:space:]]+/, "", v); print v}' "$file"
}

validate_keys() {
  local file="$1"
  shift
  local keys=("$@")

  for key in "${keys[@]}"; do
    if ! has_key "$key" "$file"; then
      echo "[ERROR] Missing required key '$key' in $file" >&2
      errors=1
      continue
    fi

    local value
    value="$(key_value "$key" "$file")"
    value="${value%"\r"}"

    if [[ -z "${value// }" ]]; then
      echo "[ERROR] Key '$key' is empty in $file" >&2
      errors=1
    fi
  done
}

echo "[preflight] Validating required production deployment files"
for file in "${required_files[@]}"; do
  require_file "$file"
done

if [[ $errors -ne 0 ]]; then
  exit 1
fi

echo "[preflight] Validating frontend environment contract"
validate_keys "$FRONTEND_ENV" "${frontend_required_keys[@]}"

echo "[preflight] Validating backend environment contract"
validate_keys "$BACKEND_ENV" "${backend_required_keys[@]}"

if has_key "APP_ENV" "$BACKEND_ENV"; then
  app_env="$(key_value "APP_ENV" "$BACKEND_ENV")"
  if [[ "$app_env" != "production" ]]; then
    echo "[ERROR] APP_ENV must be 'production' in $BACKEND_ENV (found '$app_env')" >&2
    errors=1
  fi
fi

if has_key "SECURE_COOKIES" "$BACKEND_ENV"; then
  secure_cookies="$(key_value "SECURE_COOKIES" "$BACKEND_ENV")"
  if [[ "$secure_cookies" != "True" ]]; then
    echo "[ERROR] SECURE_COOKIES should be 'True' in production (found '$secure_cookies')" >&2
    errors=1
  fi
else
  echo "[ERROR] Missing required key 'SECURE_COOKIES' in $BACKEND_ENV" >&2
  errors=1
fi

if [[ $errors -ne 0 ]]; then
  echo "[preflight] FAILED: resolve errors before running docker compose." >&2
  exit 1
fi

echo "[preflight] OK: ready for docker compose -f deploy/compose.prod.yml up"
