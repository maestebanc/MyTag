#!/usr/bin/env bash
# Construye y exporta el Flatpak de MyTag como un único archivo .flatpak
# instalable con `flatpak install archivo.flatpak`.
# Requiere flatpak-builder y los runtimes org.gnome.Platform//50 y
# org.gnome.Sdk//50 (`flatpak install flathub org.gnome.Platform//50
# org.gnome.Sdk//50`).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_DIR="$REPO_ROOT/packaging/flatpak"
BUILD_DIR="$REPO_ROOT/packaging/build/flatpak"
REPO_DIR="$REPO_ROOT/packaging/build/flatpak-repo"
OUT_DIR="$REPO_ROOT/packaging/dist"
APP_ID="com.maestebanc.MyTag"
VERSION="0.50.0"

cd "$MANIFEST_DIR"
flatpak-builder --force-clean --user --repo="$REPO_DIR" "$BUILD_DIR" "$APP_ID.yml"

mkdir -p "$OUT_DIR"
flatpak build-bundle "$REPO_DIR" "$OUT_DIR/mytag-${VERSION}.flatpak" "$APP_ID"
echo "Listo: $OUT_DIR/mytag-${VERSION}.flatpak"
