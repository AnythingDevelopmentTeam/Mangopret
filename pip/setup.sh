#!/bin/bash
# Mangopret pip bootstrap for Linux
# Installs pip + PyQt6 when system pip is unavailable
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
GET_PIP="$SCRIPT_DIR/get-pip.py"

PYTHON=""
for p in python3 python; do
    command -v "$p" &>/dev/null && { PYTHON="$p"; break; }
done

if [ -z "$PYTHON" ]; then
    echo "Python not found. Install python3 first."
    exit 1
fi

echo "Using: $PYTHON ($("$PYTHON" --version 2>&1))"

# Check if pip is available
if "$PYTHON" -m pip --version &>/dev/null; then
    echo "pip is already available: $("$PYTHON" -m pip --version)"
else
    echo "pip not found, bootstrapping from bundled get-pip.py..."
    if [ ! -f "$GET_PIP" ]; then
        echo "Error: $GET_PIP not found"
        echo "Download from https://bootstrap.pypa.io/get-pip.py"
        exit 1
    fi
    "$PYTHON" "$GET_PIP" --no-warn-script-location
    if ! "$PYTHON" -m pip --version &>/dev/null; then
        echo "Failed to install pip."
        exit 1
    fi
    echo "pip installed: $("$PYTHON" -m pip --version)"
fi

# Install PyQt6 if missing
if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
    echo "Installing PyQt6..."
    "$PYTHON" -m pip install --user PyQt6
    echo "PyQt6 installed."
else
    echo "PyQt6 already installed."
fi

echo ""
echo "Setup complete. Run: ./run_gui.sh"
