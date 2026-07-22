#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/gui"

if ! command -v python3 &>/dev/null; then
    echo "Python3 not found. Install it:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Arch: sudo pacman -S python python-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "PyQt6 not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

python3 main.py "$@"
