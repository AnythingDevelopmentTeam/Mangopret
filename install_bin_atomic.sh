#!/bin/sh
# Simplified install_bin.sh for atomic systems (rpm-ostree, read-only /usr).
# Creates symlinks within /opt/zapret/ — only basic POSIX commands, no hexdump/dd.
# Called from mangopret's platform.py when _is_atomic_system() is true.

EXEDIR="$(dirname "$0")"
EXEDIR="$(cd "$EXEDIR"; pwd)"
ZAPRET_BASE="${ZAPRET_BASE:-"$EXEDIR"}"
BINDIR="$ZAPRET_BASE/binaries"

ARCHLIST="linux-x86_64 linux-x86 linux-arm64 linux-arm linux-mips64 linux-mipsel linux-mips linux-lexra linux-ppc"

ccp() {
    local F="$1"
    local TARGET="$2"
    local DST_DIR="$ZAPRET_BASE/$TARGET"
    [ -d "$DST_DIR" ] || mkdir -p "$DST_DIR"
    [ -f "$DST_DIR/$F" ] && rm -f "$DST_DIR/$F"
    ln -fs "../binaries/$arch/$F" "$DST_DIR/"
    echo "linked : ../binaries/$arch/$F => $DST_DIR/"
}

for arch in $ARCHLIST; do
    [ -d "$BINDIR/$arch" ] || continue
    if [ -x "$BINDIR/$arch/ip2net" ]; then
        echo "$arch found, installing binaries..."
        ccp ip2net ip2net
        ccp mdig mdig
        ccp nfqws nfq
        ccp tpws tpws
        exit 0
    fi
done

echo "no compatible binaries found in $BINDIR"
exit 1
