"""Comprobación de integridad de archivos FLAC (usa el binario `flac`)."""
from __future__ import annotations

import shutil
import subprocess

FLAC_BINARY = "flac"


def is_available() -> bool:
    return shutil.which(FLAC_BINARY) is not None


def check_integrity(path: str) -> tuple[bool, str]:
    """Devuelve (ok, mensaje). ok=True si el archivo pasa `flac --test`."""
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
