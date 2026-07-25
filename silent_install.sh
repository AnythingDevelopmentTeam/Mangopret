#!/bin/bash
# Mangopret silent installer for zapret
# Copies zapret tree, lets install_bin.sh handle binary detection/linking
# Usage: silent_install.sh <source_dir> <target_dir>

set -e

SRC="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
TARGET="${2:-/opt/zapret}"

echo "[mangopret] Source: $SRC"
echo "[mangopret] Target: $TARGET"

[ "$(id -u)" -eq 0 ] || {
    echo "[mangopret] Error: must be run as root"
    exit 1
}

# Copy everything to target
if [ -d "$TARGET" ] && [ "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    echo "[mangopret] Cleaning existing $TARGET ..."
    rm -rf "$TARGET"
fi

echo "[mangopret] Copying zapret to $TARGET ..."
mkdir -p "$(dirname "$TARGET")"
cp -R "$SRC" "$TARGET"
[ -d "$TARGET/tmp" ] || mkdir "$TARGET/tmp"

# Create default ipset user files
[ -d "$TARGET/ipset" ] || mkdir -p "$TARGET/ipset"
[ -f "$TARGET/ipset/zapret-hosts-user-exclude.txt" ] || {
    [ -f "$TARGET/ipset/zapret-hosts-user-exclude.txt.default" ] && \
        cp "$TARGET/ipset/zapret-hosts-user-exclude.txt.default" "$TARGET/ipset/zapret-hosts-user-exclude.txt" || \
        touch "$TARGET/ipset/zapret-hosts-user-exclude.txt"
}
[ -f "$TARGET/ipset/zapret-hosts-user.txt" ] || echo "nonexistent.domain" >> "$TARGET/ipset/zapret-hosts-user.txt"
[ -f "$TARGET/ipset/zapret-hosts-user-ipban.txt" ] || touch "$TARGET/ipset/zapret-hosts-user-ipban.txt"

# Create config from default if missing
[ -f "$TARGET/config" ] || {
    [ -f "$TARGET/config.default" ] && cp "$TARGET/config.default" "$TARGET/config"
}

# Auto-detect firewall type for prereq installer
if ! grep -q "^FWTYPE=" "$TARGET/config" 2>/dev/null; then
    if command -v nft >/dev/null 2>&1; then
        echo "FWTYPE=nftables" >> "$TARGET/config"
    else
        echo "FWTYPE=iptables" >> "$TARGET/config"
    fi
fi

# Use zapret's own install_bin.sh to detect arch and link binaries
echo "[mangopret] Detecting architecture and linking binaries ..."
cd "$TARGET"
ZAPRET_BASE="$TARGET" sh "$TARGET/install_bin.sh"

# Install system prerequisites using zapret's own script
echo "[mangopret] Installing prerequisites ..."
cd "$TARGET"
FWTYPE=$(grep "^FWTYPE=" "$TARGET/config" 2>/dev/null | cut -d= -f2)
[ -z "$FWTYPE" ] && FWTYPE="nftables"
echo "" | ZAPRET_BASE="$TARGET" FWTYPE="$FWTYPE" sh "$TARGET/install_prereq.sh" || {
    echo "[mangopret] WARNING: some prerequisites may not be installed"
}

# Set permissions
echo "[mangopret] Setting permissions ..."
find "$TARGET" -type d -exec chmod 755 {} \;
find "$TARGET" -type f -exec chmod 644 {} \;
chown -R root:root "$TARGET" 2>/dev/null || true
find "$TARGET/binaries" -type f -name "ip2net" -exec chmod 755 {} \; 2>/dev/null || true
find "$TARGET/binaries" -type f \( -name "nfqws" -o -name "tpws" -o -name "mdig" \) -exec chmod 755 {} \; 2>/dev/null || true

chmod 755 "$TARGET/install_bin.sh" 2>/dev/null || true
chmod 755 "$TARGET/install_easy.sh" 2>/dev/null || true
chmod 755 "$TARGET/install_prereq.sh" 2>/dev/null || true
chmod 755 "$TARGET/blockcheck.sh" 2>/dev/null || true
chmod 755 "$TARGET/uninstall_easy.sh" 2>/dev/null || true

# Install systemd service
if systemctl --version >/dev/null 2>&1; then
    SVC_DIR="/etc/systemd/system"
    if [ -d "$SVC_DIR" ] && [ -f "$TARGET/init.d/systemd/zapret.service" ]; then
        cp -f "$TARGET/init.d/systemd/zapret.service" "$SVC_DIR/mangopret.service"
        systemctl daemon-reload 2>/dev/null || true
        echo "[mangopret] Systemd service installed (mangopret.service)"
    fi
fi

echo "[mangopret] Installation complete!"
echo "[mangopret] Zapret installed to: $TARGET"
