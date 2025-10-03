#!/usr/bin/env bash
set -euo pipefail

cd tests
pytest "$@"
cd - >/dev/null
