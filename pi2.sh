#!/usr/bin/env bash
# Runs Lobotomized (pi/2 in Python) from this checkout, the way pi-test.sh runs the TypeScript pi/2.
# Works from any directory:  ~/pi-2/pi2.sh --model ollama/gemma4-workshop:12b -e path/to/extension.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
  echo "pi2 needs Python 3.10 or newer; $PYTHON is $("$PYTHON" --version 2>&1). Set PYTHON=/path/to/python3." >&2
  exit 1
fi

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m pi2 "$@"
