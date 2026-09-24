"""Comprobación de integridad de archivos de audio (FLAC, MP3, M4A, OGG, OPUS)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis


def _find_flac_binary() -> str | None:
    """Busca el binario flac en el PATH del sistema."""
    return shutil.which("flac")


def is_available() -> bool:
    return True


def check_integrity(path: str) -> tuple[bool, str]:
    """Devuelve (ok, mensaje). ok=True si el archivo pasa la verificación."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp3":
        try:
            audio = MP3(path)
            if audio.info is None:
                return False, "Stream MP3 ilegible o encabezado corrupto"
            return True, ""
        except (HeaderNotFoundError, Exception) as exc:
            return False, str(exc)
    elif ext in (".m4a", ".mp4"):
        try:
            audio = MP4(path)
            if audio.info is None:
                return False, "Contenedor MP4/M4A ilegible o sin stream de audio válido"
            return True, ""
        except Exception as exc:
            return False, str(exc)
    elif ext in (".ogg", ".oga"):
        try:
            audio = OggVorbis(path)
            if audio.info is None:
                return False, "Stream Ogg Vorbis corrupto o ilegible"
            return True, ""
        except Exception as exc:
            return False, str(exc)
    elif ext == ".opus":
        try:
            audio = OggOpus(path)
            if audio.info is None:
                return False, "Stream Ogg Opus corrupto o ilegible"
            return True, ""
        except Exception as exc:
            return False, str(exc)

    # Verificación estricta de FLAC mediante bitstream test
    flac_bin = _find_flac_binary()
    if not flac_bin:
        return False, "flac binary not found"

    try:
        result = subprocess.run(
            [flac_bin, "--test", "--silent", path],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "").strip()
