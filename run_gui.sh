#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_FULL="$SCRIPT_DIR/$(basename "$0")"

# Skip root escalation when launched with --minimized from autostart.
# Tray-only mode needs X11 access which breaks under root.
if [ "$(id -u)" -ne 0 ] && [[ "$*" != *"--minimized"* ]]; then
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
    echo " Ubuntu/Debian: sudo apt install python3"
    echo " Arch: sudo pacman -S python"
    echo " Fedora: sudo dnf install python3"
    echo " openSUSE: sudo zypper install python3"
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

    # System packages failed — try pip
    if command -v pip3 &>/dev/null; then
        pip3 install --user PyQt6 2>/dev/null && return 0
    fi
    if command -v pip &>/dev/null; then
        pip install --user PyQt6 2>/dev/null && return 0
    fi

    # pip itself missing — bootstrap from bundled get-pip.py
    local GET_PIP="$SCRIPT_DIR/pip/get-pip.py"
    if [ -f "$GET_PIP" ]; then
        echo "Bootstrapping pip from bundled get-pip.py..."
        "$PYTHON" "$GET_PIP" --no-warn-script-location 2>/dev/null
        if "$PYTHON" -m pip --version &>/dev/null; then
            "$PYTHON" -m pip install --user PyQt6 2>/dev/null && return 0
        fi
    fi

    return 1
}

install_terminal() {
    # detect terminal from environment or parent process tree
    for var in TERMINAL_EMULATOR TERM_PROGRAM COLORTERM; do
        val="${!var}"
        if [ -n "$val" ] && command -v "$val" &>/dev/null; then
            return 0
        fi
    done

    pid=$$
    for _ in 1 2 3 4 5 6; do
        pid=$(awk '/^PPid:/ {print $2}' "/proc/$pid/status" 2>/dev/null) || break
        [ "$pid" -le 1 ] 2>/dev/null && break
        comm=$(cat "/proc/$pid/comm" 2>/dev/null) || continue
        if command -v "$comm" &>/dev/null; then
            return 0
        fi
    done

    # fallback
    for cmd in x-terminal-emulator xdg-terminal-exec gnome-terminal konsole xfce4-terminal lxterminal xterm; do
        if command -v "$cmd" &>/dev/null; then
            return 0
        fi
    done

    read -rp "No terminal emulator found. Install xterm? [y/N] " answer
    case "$answer" in
        [yY]|[yY][eE][sS])
            echo "Installing xterm..."
            if command -v apt &>/dev/null; then
                sudo apt install -y xterm 2>/dev/null && return 0
            fi
            if command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm xterm 2>/dev/null && return 0
            fi
            if command -v dnf &>/dev/null; then
                sudo dnf install -y xterm 2>/dev/null && return 0
            fi
            if command -v zypper &>/dev/null; then
                sudo zypper install -y xterm 2>/dev/null && return 0
            fi
            if command -v apk &>/dev/null; then
                sudo apk add xterm 2>/dev/null && return 0
            fi
            echo "Failed to install xterm."
            ;;
        *)
            echo "Install a terminal emulator manually (gnome-terminal, konsole, xterm, etc.)"
            ;;
    esac
    return 1
}

if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
    install_pyqt6
    if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
        echo ""
        echo "Could not install PyQt6. Falling back to CLI mode."
        echo "Run: ./run.sh <command>"
        echo ""
        "$PYTHON" main.py "$@"
        exit $?
    fi
fi

install_terminal

exec "$PYTHON" main_gui.py "$@"
