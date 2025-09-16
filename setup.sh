#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
NNG_DIR="$REPO_ROOT/NNG4"

if [[ ! -d "$NNG_DIR/.git" ]]; then
  echo "Cloning Natural Number Game into $NNG_DIR"
  git submodule add https://github.com/leanprover-community/NNG4.git "$NNG_DIR"
else
  echo "NNG4 submodule already present"
fi

echo "Updating submodule"
git submodule update --init --recursive

ENV_FILE="$REPO_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^NNG_PATH=' "$ENV_FILE"; then
    echo "Updating NNG_PATH in .env"
    sed -i "" "s|^NNG_PATH=.*|NNG_PATH=$NNG_DIR|" "$ENV_FILE" 2>/dev/null || \
      sed -i "s|^NNG_PATH=.*|NNG_PATH=$NNG_DIR|" "$ENV_FILE"
  else
    echo "Appending NNG_PATH to .env"
    printf '\nNNG_PATH=%s\n' "$NNG_DIR" >> "$ENV_FILE"
  fi
else
  echo "Creating .env with NNG_PATH"
  printf 'NNG_PATH=%s\n' "$NNG_DIR" > "$ENV_FILE"
fi

echo "Setup complete."
