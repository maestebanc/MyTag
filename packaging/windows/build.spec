# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para generar el ejecutable de Windows de MyTag.
# Se ejecuta con: pyinstaller packaging/windows/build.spec
# desde la raíz del repositorio, dentro de un entorno MSYS2 MINGW64 con
# gtk4, libadwaita, python-gobject, python-pillow y python-mutagen
# instalados vía pacman (ver packaging/windows/bootstrap.sh).

from pathlib import Path

ROOT = Path.cwd().resolve()
ICON = ROOT / "packaging" / "windows" / "com.maestebanc.MyTag.ico"

a = Analysis(
    [str(ROOT / "mytag" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "mytag" / "resources" / "icons"), "mytag/resources/icons"),
        (str(ROOT / "data" / "icons"), "data/icons"),
        (str(ROOT / "LICENSE"), "."),
    ],
    hiddenimports=[
        "PIL",
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
