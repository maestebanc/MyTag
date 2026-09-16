"""Tipos y utilidades compartidas por las distintas fuentes de búsqueda de portadas."""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass

from . import i18n

USER_AGENT = "MyTag/0.50.0 (https://github.com/maestebanc/MyTag)"
REQUEST_TIMEOUT = 12


class CoverSearchError(Exception):
    """Error de red o del servicio al buscar/descargar una portada."""


@dataclass
class CoverCandidate:
    source: str  # p. ej. "MusicBrainz" o "iTunes"
    image_url: str


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise CoverSearchError(i18n.t("error.download_image", reason=exc)) from exc
