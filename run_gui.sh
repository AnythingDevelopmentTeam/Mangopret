#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_FULL="$SCRIPT_DIR/$(basename "$0")"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo -E "$SCRIPT_FULL" "$@"
fi

cd "$SCRIPT_DIR/gui"

PYTHON=""
for p in python3 python; do
    command -v "$p" &>/dev/null && { PYTHON="$p"; break; }
done

if [ -z "$PYTHON" ]; then
    echo "Python3 not found."
    echo ""
    echo "Install it:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Arch:          sudo pacman -S python"
    echo "  Fedora:        sudo dnf install python3"
    echo "  openSUSE:      sudo zypper install python3"
    exit 1
fi

install_pyqt6() {
    echo "PyQt6 not found. Installing..."

    if command -v apt &>/dev/null; then
        sudo apt update -qq && sudo apt install -y python3-pyqt6 2>/dev/null && return 0
    fi
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-pyqt6 2>/dev/null && return 0
    fi
    if command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pyqt6 2>/dev/null && return 0
    fi
    if command -v zypper &>/dev/null; then
        sudo zypper install -y python3-qt6 2>/dev/null && return 0
    fi
    if command -v apk &>/dev/null; then
        sudo apk add py3-pyqt6 2>/dev/null && return 0
    fi

    if command -v pip3 &>/dev/null; then
        pip3 install --user PyQt6 2>/dev/null && return 0
    fi
    if command -v pip &>/dev/null; then
        pip install --user PyQt6 2>/dev/null && return 0
    fi

    return 1
}

install_terminal() {
    if command -v x-terminal-emulator &>/dev/null || command -v xdg-terminal-exec &>/dev/null; then
        return 0
    fi
    echo "No terminal emulator found. Installing..."

    if command -v apt &>/dev/null; then
        sudo apt install -y xdg-utils xterm 2>/dev/null && return 0
    fi
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm xdg-utils xterm 2>/dev/null && return 0
    fi
    if command -v dnf &>/dev/null; then
        sudo dnf install -y xdg-utils xterm 2>/dev/null && return 0
    fi
    if command -v zypper &>/dev/null; then
        sudo zypper install -y xdg-utils xterm 2>/dev/null && return 0
    fi
    if command -v apk &>/dev/null; then
        sudo apk add xdg-utils xterm 2>/dev/null && return 0
    fi

    return 1
}

if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
    install_pyqt6
    if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
        echo ""
        echo "Could not install PyQt6. Falling back to CLI mode."
        echo "Run:  ./run.sh <command>"
        echo ""
        "$PYTHON" main.py "$@"
        exit $?
    fi
fi

install_terminal

exec "$PYTHON" main_gui.py "$@"
