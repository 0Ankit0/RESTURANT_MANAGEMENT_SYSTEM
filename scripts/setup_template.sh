#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

./scripts/copy_env_templates.sh

echo "Installing backend dependencies..."
(cd backend && uv sync --all-groups)

echo "Installing frontend dependencies..."
(cd frontend && npm ci)

if command -v flutter >/dev/null 2>&1; then
  echo "Installing mobile dependencies..."
  (cd mobile && flutter pub get)
else
  echo "Flutter is not installed; skipping mobile dependency setup."
fi

echo "Template setup complete."
