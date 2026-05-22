#!/usr/bin/env bash
set -o errexit

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

if [ -n "$RENDER_EXTERNAL_HOSTNAME" ]; then
  "$PYTHON_BIN" manage.py load_demo_data --base-url "https://$RENDER_EXTERNAL_HOSTNAME"
else
  "$PYTHON_BIN" manage.py load_demo_data --base-url "http://127.0.0.1:${PORT:-8000}"
fi

"$PYTHON_BIN" -m gunicorn telcomplus_qr_demo.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
