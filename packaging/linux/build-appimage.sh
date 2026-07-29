#!/bin/bash
# Build Mangopret AppImage
set -e

VERSION="${1:-2.2.0}"
APP=mangopret
ARCH=x86_64
APP_DIR="${PWD}/${APP}.AppDir"

# Clean
rm -rf "${APP_DIR}" "${APP}-${VERSION}-${ARCH}.AppImage"

# Create AppDir structure
mkdir -p "${APP_DIR}/python"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/scalable/apps"

# Download portable Python
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260718/cpython-3.10.20+20260718-${ARCH}-unknown-linux-gnu-install_only.tar.gz"
wget -q -O python.tar.gz "${PYTHON_URL}"
tar -xzf python.tar.gz -C "${APP_DIR}/python" --strip-components=1
rm python.tar.gz

# Install PyQt6 into portable Python
"${APP_DIR}/python/bin/pip3" install "PyQt6>=6.5"

# Copy app files
cp -r gui "${APP_DIR}/gui"
cp -r lists "${APP_DIR}/lists"
cp -r bin "${APP_DIR}/bin"
cp -r strategies "${APP_DIR}/strategies"
cp -r .service "${APP_DIR}/.service" 2>/dev/null || true
cp run.sh run_gui.sh README.md README.en.md LICENSE.txt "${APP_DIR}/"
cp packaging/linux/AppRun "${APP_DIR}/AppRun"
cp packaging/linux/mangopret.desktop "${APP_DIR}/"

# Copy icon (name must match Icon= in desktop file)
cp gui/ui/icon.svg "${APP_DIR}/mangopret.svg"
cp gui/ui/icon.svg "${APP_DIR}/usr/share/icons/hicolor/scalable/apps/mangopret.svg"
ln -sf "${APP_DIR}/mangopret.svg" "${APP_DIR}/.DirIcon"

chmod +x "${APP_DIR}/AppRun"

# Download appimagetool
wget -q -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
chmod +x appimagetool

# Build AppImage (APPIMAGE_EXTRACT_AND_RUN=1 avoids FUSE in CI)
ARCH="${ARCH}" APPIMAGE_EXTRACT_AND_RUN=1 ./appimagetool --no-appstream "${APP_DIR}" "${APP}-${VERSION}-${ARCH}.AppImage"

echo "Done: ${APP}-${VERSION}-${ARCH}.AppImage"
