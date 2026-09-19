#!/usr/bin/env bash
# Instala, dentro de un entorno MSYS2 MINGW64, todo lo necesario para
# compilar el .exe de Windows de MyTag con PyInstaller.
set -euo pipefail

pacman -S --needed --noconfirm \
  mingw-w64-x86_64-gtk4 \
  mingw-w64-x86_64-libadwaita \
  mingw-w64-x86_64-python-gobject \
  mingw-w64-x86_64-python-pillow \
  mingw-w64-x86_64-python-mutagen \
  mingw-w64-x86_64-pyinstaller \
  mingw-w64-x86_64-pyinstaller-hooks-contrib \
  mingw-w64-x86_64-flac \
  unzip \
  curl

# Descargar binario oficial de fpcalc (Chromaprint / AcoustID)
if [ ! -f /mingw64/bin/fpcalc.exe ]; then
  echo "==> Descargando fpcalc para Windows..."
  curl -sSL "https://github.com/acoustid/chromaprint/releases/download/v1.6.1/chromaprint-fpcalc-1.6.1-windows-x86_64.zip" -o /tmp/fpcalc.zip
  unzip -q -j /tmp/fpcalc.zip "*/fpcalc.exe" -d /mingw64/bin/
  rm -f /tmp/fpcalc.zip
  chmod +x /mingw64/bin/fpcalc.exe
fi
