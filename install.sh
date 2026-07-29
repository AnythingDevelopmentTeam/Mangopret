#!/bin/bash
set -e

REPO="https://github.com/AnythingDevelopmentTeam/Mangopret.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/mangopret}"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo -E "$0" "$@"
fi

TMPDIR=$(mktemp -d)

echo "==> Cloning latest version from $REPO ..."
git clone --depth 1 "$REPO" "$TMPDIR"

VERSION=$(cd "$TMPDIR" && git describe --tags --always 2>/dev/null || echo "git")
echo "    Version: $VERSION"

echo "==> Installing to $INSTALL_DIR ..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$INSTALL_DIR"
cp -a "$TMPDIR"/. "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/.git" "$TMPDIR"

cd "$INSTALL_DIR"

echo "==> Installing dependencies ..."
PYTHON=""
for p in python3 python; do
    command -v "$p" &>/dev/null && { PYTHON="$p"; break; }
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Install python3 first."
    exit 1
fi

if ! "$PYTHON" -c "import PyQt6" 2>/dev/null; then
    bash pip/setup.sh
fi

echo "==> Creating symlink ..."
ln -sf "$INSTALL_DIR/run.sh" /bin/mangopret
ln -sf "$INSTALL_DIR/run_gui.sh" /bin/mangopret-gui

echo "==> Installing desktop entry ..."
cp mangopret.desktop /usr/share/applications/
cp gui/ui/icon.svg /usr/share/icons/hicolor/scalable/apps/mangopret.svg

echo ""
echo "=== Installation complete ==="
echo "  Version: $VERSION"
echo "  Path:    $INSTALL_DIR"
echo ""
echo "  GUI:     mangopret-gui"
echo "  CLI:     sudo mangopret <command>"
echo "  Or:      cd $INSTALL_DIR && ./run_gui.sh"
echo "           cd $INSTALL_DIR && sudo ./run.sh start <strategy>"
echo ""
echo "  Install systemd service:  sudo mangopret service install"
