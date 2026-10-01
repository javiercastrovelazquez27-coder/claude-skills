#!/usr/bin/env bash
# One-time environment for the report generator (reused across clients).
set -euo pipefail
VENV="$HOME/.cache/reporte-search-console/venv"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade reportlab matplotlib pymupdf fonttools pillow
echo "$VENV/bin/python"
