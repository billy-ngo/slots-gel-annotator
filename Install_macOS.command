#!/usr/bin/env bash
# ===============================================================
#   Slots Gel Annotator — macOS / Linux installer
#   Installs the package from this source tree (editable mode)
#   and launches the annotator. Re-run any time to update.
# ===============================================================
set -e

# Move into this script's directory so `pip install -e .` resolves
# correctly regardless of where the user double-clicked from.
cd "$(dirname "$0")"

echo
echo "  =============================================="
echo "    Slots Gel Annotator -- installing"
echo "  =============================================="
echo

# Resolve a Python interpreter. macOS ships /usr/bin/python3 (Catalina+);
# Linux distros use python3 by convention. Refuse to use Python 2.
PY=""
for candidate in python3 python3.13 python3.12 python3.11 python3.10 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        ver="$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo 0)"
        if [ "$ver" = "3" ]; then
            PY="$candidate"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "  ERROR: Python 3.10+ not found."
    echo "  macOS:  brew install python  (or download from https://www.python.org)"
    echo "  Linux:  sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

echo "  Using $PY ($("$PY" --version 2>&1))"
echo

echo "  Running: $PY -m pip install -U pip"
"$PY" -m pip install -U pip || echo "  Pip self-upgrade failed. Continuing anyway."

echo
echo "  Running: $PY -m pip install -e ."
if ! "$PY" -m pip install -e . ; then
    echo
    echo "  System-wide install failed. Retrying with --user ..."
    "$PY" -m pip install -e . --user
fi

echo
echo "  Install OK. Launching Slots Gel Annotator..."
echo
exec "$PY" -m gel_annotator
