#!/bin/bash
set -e

VERSION="${1:-v2.2.0}"
VERSION_NUM="${VERSION#v}"

echo "=== Building Mangopret ${VERSION} for Linux ==="

if [ ! -f packaging/linux/build-appimage.sh ]; then
    echo "ERROR: packaging/linux/build-appimage.sh not found"
    exit 1
fi

bash packaging/linux/build-appimage.sh "${VERSION_NUM}"

echo "=== Done ==="
echo "Artifacts:"
ls -la mangopret-*.AppImage 2>/dev/null || true

echo ""
echo "To create a GitHub release, run:"
echo "  gh release create ${VERSION} mangopret-${VERSION_NUM}-x86_64.AppImage --generate-notes"
