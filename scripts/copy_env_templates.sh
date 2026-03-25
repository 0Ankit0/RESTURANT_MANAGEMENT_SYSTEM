#!/usr/bin/env bash
set -euo pipefail

copy_if_missing() {
  local source_file="$1"
  local target_file="$2"

  if [ -f "$target_file" ]; then
    echo "Keeping existing $target_file"
    return
  fi

  cp "$source_file" "$target_file"
  echo "Created $target_file from $source_file"
}

copy_if_missing "backend/.env.example" "backend/.env"
copy_if_missing "frontend/.env.local.example" "frontend/.env.local"
copy_if_missing "mobile/.env.example" "mobile/.env"
