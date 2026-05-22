#!/usr/bin/env bash
set -o errexit

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

pip install -r requirements.txt
"$PYTHON_BIN" manage.py collectstatic --no-input
"$PYTHON_BIN" manage.py migrate
