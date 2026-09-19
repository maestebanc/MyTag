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
  mingw-w64-x86_64-pyinstaller-hooks-contrib
