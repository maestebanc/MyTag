#!/usr/bin/env bash
# Construye el paquete de Arch Linux (.pkg.tar.zst) de MyTag.
# Usa makepkg si está disponible en Arch; si no (ej. Fedora o Ubuntu),
# empaqueta directamente usando python3, tar y zstd.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCH_DIR="$REPO_ROOT/packaging/arch"
OUT_DIR="$REPO_ROOT/packaging/dist"
VERSION="$(python3 -c "import tomllib; print(tomllib.load(open('$REPO_ROOT/pyproject.toml', 'rb'))['project']['version'])")-1"

mkdir -p "$OUT_DIR"

if command -v makepkg >/dev/null 2>&1; then
    echo "==> Construyendo con makepkg oficial..."
    cd "$ARCH_DIR"
    rm -rf src pkg ./*.tar.gz
    makepkg -f -d --clean
    cp ./*.pkg.tar.zst "$OUT_DIR/"
    rm -rf src pkg ./*.tar.gz
else
    echo "==> makepkg no disponible; empaquetando con tar + zstd..."
    WORK="$REPO_ROOT/packaging/build/arch_pkg"
    rm -rf "$WORK"
    mkdir -p "$WORK/usr/bin"

    PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    SITE_PKG="$WORK/usr/lib/python${PY_VER}/site-packages"
    mkdir -p "$SITE_PKG"

    cp -r "$REPO_ROOT/mytag" "$SITE_PKG/"
    find "$SITE_PKG/mytag" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    cat > "$WORK/usr/bin/mytag" <<'LAUNCHER'
#!/usr/bin/python3
import sys
from mytag.app import main
if __name__ == "__main__":
    sys.exit(main())
LAUNCHER
    chmod 755 "$WORK/usr/bin/mytag"

    mkdir -p "$WORK/usr/share/applications" "$WORK/usr/share/metainfo"
    cp "$REPO_ROOT/data/com.maestebanc.MyTag.desktop" "$WORK/usr/share/applications/"
    cp "$REPO_ROOT/data/com.maestebanc.MyTag.metainfo.xml" "$WORK/usr/share/metainfo/"

    for size in 16 22 24 32 48 64 128 256 512; do
        mkdir -p "$WORK/usr/share/icons/hicolor/${size}x${size}/apps"
        cp "$REPO_ROOT/data/icons/hicolor/${size}x${size}/apps/com.maestebanc.MyTag.png" \
           "$WORK/usr/share/icons/hicolor/${size}x${size}/apps/"
    done
    mkdir -p "$WORK/usr/share/icons/hicolor/scalable/apps"
    cp "$REPO_ROOT/data/icons/hicolor/scalable/apps/com.maestebanc.MyTag.svg" \
       "$WORK/usr/share/icons/hicolor/scalable/apps/"

    # Tamaño total instalado en bytes
    INSTALLED_SIZE=$(find "$WORK/usr" -type f -exec stat -c %s {} + | awk '{s+=$1} END {print s}')
    BUILD_DATE=$(date +%s)

    cat > "$WORK/.PKGINFO" <<EOF
# Generated for MyTag
pkgname = mytag
pkgbase = mytag
xdata = pkgtype=pkg
pkgver = ${VERSION}
pkgdesc = Edit tags and cover art on your music files
url = https://maestebanc.github.io/MyTag/
builddate = ${BUILD_DATE}
packager = Miguel Angel Esteban <maestebanc@gmail.com>
size = ${INSTALLED_SIZE}
arch = any
license = GPL-3.0-or-later
depend = python
depend = python-mutagen
depend = python-pillow
depend = python-gobject
depend = gtk4
depend = libadwaita
optdepend = flac: audio stream integrity verification
optdepend = chromaprint: audio fingerprint identification (AcoustID)
EOF

    RAW_VER="${VERSION%-1}"
    tar --numeric-owner --owner=0 --group=0 --zstd -cf "$OUT_DIR/mytag-${RAW_VER}-1-any.pkg.tar.zst" -C "$WORK" .PKGINFO usr
    rm -rf "$WORK"
fi

echo "Listo: $(ls "$OUT_DIR"/mytag-*-any.pkg.tar.zst | tail -n 1)"
