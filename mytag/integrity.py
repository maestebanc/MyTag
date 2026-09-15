"""Comprobación de integridad de archivos de audio (FLAC y MP3)."""
from __future__ import annotations

import shutil
import subprocess

from mutagen.mp3 import MP3, HeaderNotFoundError

FLAC_BINARY = "flac"


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

    if not shutil.which(FLAC_BINARY):
        return False, "flac binary not found"

    try:
        result = subprocess.run(
            [FLAC_BINARY, "--test", "--silent", path],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "").strip()
