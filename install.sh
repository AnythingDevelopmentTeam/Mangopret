#!/bin/bash
set -e

REPO="AnythingDevelopmentTeam/Mangopret"
INSTALL_DIR="${INSTALL_DIR:-/opt/zapret}"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo -E "$0" "$@"
fi

echo "==> Fetching latest release from $REPO ..."
LATEST=$(curl -sSL "https://api.github.com/repos/$REPO/releases/latest")
VERSION=$(echo "$LATEST" | grep -oP '"tag_name":\s*"\K[^"]+')
echo "    Latest version: $VERSION"

ARCHIVE_URL=$(echo "$LATEST" | grep -oP '"browser_download_url":\s*"\K[^"]+linux-[^"]+\.tar\.gz' | head -1)
if [ -z "$ARCHIVE_URL" ]; then
    echo "Error: no Linux tar.gz found in latest release"
    exit 1
fi

ARCHIVE_NAME=$(basename "$ARCHIVE_URL")

echo "==> Downloading $ARCHIVE_NAME ..."
curl -#SL -o "/tmp/$ARCHIVE_NAME" "$ARCHIVE_URL"

echo "==> Installing to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
tar xzf "/tmp/$ARCHIVE_NAME" -C "$INSTALL_DIR" --strip-components=1
rm "/tmp/$ARCHIVE_NAME"

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
ln -sf "$INSTALL_DIR/run.sh" /usr/local/bin/mangopret
ln -sf "$INSTALL_DIR/run_gui.sh" /usr/local/bin/mangopret-gui

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
