#!/usr/bin/env bash
# Construye el paquete de Arch Linux de MyTag con makepkg, descargando el
# código fuente publicado en el tag de GitHub que referencia el PKGBUILD
# (por eso hay que subir antes la release/tag correspondiente).
# Requiere el grupo base-devel (paquete "base-devel" en Arch).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCH_DIR="$REPO_ROOT/packaging/arch"
OUT_DIR="$REPO_ROOT/packaging/dist"

cd "$ARCH_DIR"
rm -rf src pkg
if [ ! -f "$ARCH_DIR/mytag-0.50.0.tar.gz" ]; then
  git -C "$REPO_ROOT" archive --format=tar.gz --prefix="MyTag-0.50.0/" HEAD -o "$ARCH_DIR/mytag-0.50.0.tar.gz"
fi
makepkg -f -d --clean --skipchecksums

mkdir -p "$OUT_DIR"
cp ./*.pkg.tar.zst "$OUT_DIR/"
rm -rf src pkg ./*.tar.gz
echo "Listo: $(ls "$OUT_DIR"/*.pkg.tar.zst)"
