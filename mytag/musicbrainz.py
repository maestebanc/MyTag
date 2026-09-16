"""Búsqueda de portadas en MusicBrainz / Cover Art Archive."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from . import i18n
from .cover_types import CoverCandidate, CoverSearchError

USER_AGENT = "MyTag/0.1 (https://github.com/maestebanc/MyTag)"
MUSICBRAINZ_SEARCH_URL = "https://musicbrainz.org/ws/2/release/"
COVER_ART_ARCHIVE_URL = "https://coverartarchive.org/release/{release_id}"
REQUEST_TIMEOUT = 12
MAX_RELEASES_CHECKED = 8


def _escape_lucene(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 503:
            raise CoverSearchError(i18n.t("error.mb_busy")) from exc
        raise
    except urllib.error.URLError as exc:
        raise CoverSearchError(i18n.t("error.mb_connect", reason=exc.reason)) from exc


def _search_releases(album: str, albumartist: str, limit: int = 15) -> list[dict]:
    query = f'release:"{_escape_lucene(album)}" AND artist:"{_escape_lucene(albumartist)}"'
    params = urllib.parse.urlencode({"query": query, "fmt": "json", "limit": limit})
    data = _get_json(f"{MUSICBRAINZ_SEARCH_URL}?{params}")
    return data.get("releases", [])


def _cover_for_release(release_id: str) -> CoverCandidate | None:
    url = COVER_ART_ARCHIVE_URL.format(release_id=release_id)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # este release no tiene portada en Cover Art Archive
        return None
    except urllib.error.URLError:
        return None

    images = data.get("images", [])
    front = next((img for img in images if img.get("front")), images[0] if images else None)
    if front is None:
        return None

    thumbnails = front.get("thumbnails", {})
    image_url = thumbnails.get("1200") or thumbnails.get("large") or thumbnails.get("500") or front.get("image")
    if not image_url:
        return None

    return CoverCandidate(source="MusicBrainz", image_url=image_url)


def search_musicbrainz_candidates(album: str, albumartist: str) -> list[CoverCandidate]:
    """Busca ediciones del álbum+artista dados y devuelve las portadas disponibles."""
    releases = _search_releases(album, albumartist)
    candidates: list[CoverCandidate] = []
    for release in releases[:MAX_RELEASES_CHECKED]:
        candidate = _cover_for_release(release["id"])
        if candidate is not None:
            candidates.append(candidate)
        time.sleep(0.2)  # ser considerados con el servicio, no forma parte de una API con límite estricto
    return candidates
