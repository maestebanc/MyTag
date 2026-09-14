"""Búsqueda de portadas en iTunes / Apple Music (API pública, sin credenciales)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from . import i18n
from .cover_types import CoverCandidate, CoverSearchError

SEARCH_URL = "https://itunes.apple.com/search"
USER_AGENT = "MyTag/0.1 (https://github.com/maestebanc/MyTag)"
REQUEST_TIMEOUT = 12
MAX_RESULTS = 8
# La URL de artwork de iTunes admite pedir cualquier tamaño sustituyendo esta
# parte por "WxHbb"; usamos una resolución alta para tener buena calidad.
ARTWORK_SIZE = "1200x1200bb"


def search_itunes_candidates(album: str, albumartist: str) -> list[CoverCandidate]:
    term = f"{albumartist} {album}".strip()
    params = urllib.parse.urlencode({"term": term, "entity": "album", "limit": MAX_RESULTS})
    request = urllib.request.Request(f"{SEARCH_URL}?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise CoverSearchError(i18n.t("error.itunes_connect", reason=exc)) from exc

    candidates = []
    for result in data.get("results", []):
        artwork = result.get("artworkUrl100")
        if not artwork:
            continue
        image_url = artwork.replace("100x100bb", ARTWORK_SIZE)
        candidates.append(CoverCandidate(source="iTunes", image_url=image_url))
    return candidates
