#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/.venv/bin/python" -m pytest "${SCRIPT_DIR}/tests" "$@"
