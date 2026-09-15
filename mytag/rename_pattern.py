"""Genera nombres de archivo a partir de las etiquetas, según un patrón."""
from __future__ import annotations

import os
import re

from .audio_track import AudioTrack

DEFAULT_PATTERN = "%tracknumber%. %artist% - %title%"

# Estos campos se rellenan a 2 dígitos en el NOMBRE DE ARCHIVO (para que el
# orden alfabético coincida con el orden real), aunque el valor del propio
# tag se deje tal cual (p. ej. TRACKNUMBER puede seguir siendo "1").
_ZERO_PADDED = {"tracknumber", "discnumber"}

_TOKEN_RE = re.compile(r"%([a-zA-Z]+)%")
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _field_value(track: AudioTrack, field: str) -> str:
    value = track.get_tag(field.upper()).strip()
    if field in _ZERO_PADDED:
        digits = value.split("/")[0].strip()
        if digits.isdigit():
            return digits.zfill(2)
    return value


def render_filename(track: AudioTrack, pattern: str) -> str:
    base, ext = os.path.splitext(track.filename)
    name = _TOKEN_RE.sub(lambda m: _field_value(track, m.group(1).lower()), pattern)
    name = _INVALID_CHARS.sub("_", name).strip()
    if not name:
        name = base
    return f"{name}{ext}"
