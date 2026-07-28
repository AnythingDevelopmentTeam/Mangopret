#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_FULL="$SCRIPT_DIR/$(basename "$0")"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo -E "$SCRIPT_FULL" "$@"
fi

cd "$SCRIPT_DIR/gui"
python3 main.py "$@"
