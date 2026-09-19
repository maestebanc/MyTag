"""Comprobación de integridad de archivos de audio (FLAC y MP3)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from mutagen.mp3 import MP3, HeaderNotFoundError


def _find_flac_binary() -> str | None:
    """Busca el binario flac en el bundle empaquetado o en el PATH del sistema."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            for ext in (".exe", "") if sys.platform == "win32" else ("",):
                cand = os.path.join(meipass, f"flac{ext}")
                if os.path.isfile(cand):
                    return cand
        exe_dir = os.path.dirname(sys.executable)
        for sub in ("", "_internal"):
            for ext in (".exe", "") if sys.platform == "win32" else ("",):
                cand = os.path.join(exe_dir, sub, f"flac{ext}")
                if os.path.isfile(cand):
                    return cand
    return shutil.which("flac")


def is_available() -> bool:
    return True


def check_integrity(path: str) -> tuple[bool, str]:
    """Devuelve (ok, mensaje). ok=True si el archivo pasa la verificación."""
    if path.lower().endswith(".mp3"):
        try:
            audio = MP3(path)
            if audio.info is None:
                return False, "Stream MP3 ilegible o encabezado corrupto"
            return True, ""
        except (HeaderNotFoundError, Exception) as exc:
            return False, str(exc)

    flac_bin = _find_flac_binary()
    if not flac_bin:
        return False, "flac binary not found"

    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            [flac_bin, "--test", "--silent", path],
            capture_output=True,
            text=True,
            timeout=120,
            **kwargs,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "").strip()
