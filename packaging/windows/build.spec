# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para generar el ejecutable de Windows de MyTag.
# Se ejecuta con: pyinstaller packaging/windows/build.spec
# desde la raíz del repositorio, dentro de un entorno MSYS2 MINGW64 con
# gtk4, libadwaita, python-gobject, python-pillow y python-mutagen
# instalados vía pacman (ver packaging/windows/bootstrap.sh).

import os
import shutil
from pathlib import Path

ROOT = Path.cwd().resolve()
ICON = ROOT / "packaging" / "windows" / "com.maestebanc.MyTag.ico"
ENTRYPOINT = ROOT / "packaging" / "windows" / "run_mytag.py"

extra_binaries = []
for bin_name in ("flac", "fpcalc"):
    found = shutil.which(f"{bin_name}.exe") or shutil.which(bin_name)
    if not found:
        p = Path(os.environ.get("MINGW_PREFIX", "C:/msys64/mingw64")) / "bin" / f"{bin_name}.exe"
        if p.is_file():
            found = str(p)
    if found:
        extra_binaries.append((found, "."))

extra_datas = [
    (str(ROOT / "mytag" / "resources" / "icons"), "mytag/resources/icons"),
    (str(ROOT / "data" / "icons"), "data/icons"),
    (str(ROOT / "LICENSE"), "."),
]

mingw_prefix = Path(os.environ.get("MINGW_PREFIX", "C:/msys64/mingw64"))
etc_fonts = mingw_prefix / "etc" / "fonts"
if etc_fonts.is_dir():
    extra_datas.append((str(etc_fonts), "etc/fonts"))

a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(ROOT)],
    binaries=extra_binaries,
    datas=extra_datas,
    hiddenimports=[
        "mytag",
        "mytag.app",
        "mytag.config",
        "mytag.audio_track",
        "mytag.i18n",
        "mytag.integrity",
        "mytag.acoustid",
        "mytag.cover_search",
        "mytag.cover_types",
        "mytag.cover_utils",
        "mytag.itunes",
        "mytag.musicbrainz",
        "mytag.rename_pattern",
        "mytag.natural_sort",
        "mytag.ui.main_window",
        "mytag.ui.style",
        "mytag.ui.tag_editor",
        "mytag.ui.cover_panel",
        "mytag.ui.track_item",
        "mytag.ui.preferences_dialog",
        "mytag.ui.rename_dialog",
        "mytag.ui.fingerprint_dialog",
        "mytag.ui.cover_search_dialog",
        "mytag.ui.resize_cover_dialog",
        "mytag.ui.shortcuts_dialog",
        "mytag.ui.about_dialog",
        "mytag.ui.feature_guide_dialog",
        "mytag.ui.batch_fingerprint_dialog",
        "PIL",
        "PIL.Image",
        "mutagen",
        "mutagen.flac",
        "mutagen.id3",
        "mutagen.mp3",
    ],
    hookspath=[],
    hooksconfig={
        "gi": {
            "module-versions": {
                "Gtk": "4.0",
                "Adw": "1",
            },
            "icons": ["Adwaita"],
            "themes": ["Adwaita"],
        },
    },
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MyTag",
    icon=str(ICON),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MyTag",
)
