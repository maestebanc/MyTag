#!/usr/bin/env bash
# Construye el paquete .rpm de MyTag. Requiere rpmbuild (paquete "rpm-tools" en Arch).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOPDIR="$REPO_ROOT/packaging/build/rpmbuild"
OUT_DIR="$REPO_ROOT/packaging/dist"

mkdir -p "$TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS,BUILDROOT}

MYTAG_SRCDIR="$REPO_ROOT" rpmbuild --define "_topdir $TOPDIR" -bb "$REPO_ROOT/packaging/rpm/mytag.spec"

mkdir -p "$OUT_DIR"
cp "$TOPDIR"/RPMS/noarch/mytag-*.rpm "$OUT_DIR/"
echo "Listo: $(ls "$OUT_DIR"/mytag-*.rpm)"
