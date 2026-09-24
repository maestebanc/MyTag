"""Identificación de temas por huella de audio (Chromaprint + AcoustID)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from .constants import ACOUSTID_CLIENT_KEY

LOOKUP_URL = "https://api.acoustid.org/v2/lookup"
REQUEST_TIMEOUT = 15


class AcoustIDError(Exception):
    """Error al calcular la huella de audio o al consultar AcoustID."""


def _find_fpcalc_binary() -> str | None:
    """Busca el binario fpcalc en el PATH del sistema."""
    return shutil.which("fpcalc")


def fpcalc_available() -> bool:
    return _find_fpcalc_binary() is not None


def _fingerprint(path: str) -> tuple[int, str]:
    binary = _find_fpcalc_binary()
    if not binary:
        raise AcoustIDError("fpcalc binary not found")

    try:
        result = subprocess.run(
            [binary, "-json", path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AcoustIDError(str(exc)) from exc
    if result.returncode != 0:
        raise AcoustIDError(result.stderr.strip() or "fpcalc failed")
    try:
        data = json.loads(result.stdout)
        return int(round(data["duration"])), data["fingerprint"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise AcoustIDError(str(exc)) from exc


def _best_album(release_groups: list[dict]) -> tuple[str, int]:
    """Selecciona el mejor álbum y su prioridad (mayor = mejor)."""
    if not release_groups:
        return ("", 0)
    # 1. Preferir álbum de estudio regular (tipo Álbum y sin tipos secundarios como Recopilatorio/En vivo)
    for rg in release_groups:
        if rg.get("type") == "Album" and not rg.get("secondarytypes"):
            title = rg.get("title")
            if title:
                return (title, 3)
    # 2. Preferir cualquier lanzamiento sin tipos secundarios
    for rg in release_groups:
        if not rg.get("secondarytypes"):
            title = rg.get("title")
            if title:
                return (title, 2)
    # 3. Preferir cualquier Álbum
    for rg in release_groups:
        if rg.get("type") == "Album":
            title = rg.get("title")
            if title:
                return (title, 1)
    # 4. En su defecto, el primer grupo
    return (release_groups[0].get("title", ""), 0)


def identify(path: str, api_key: str = ACOUSTID_CLIENT_KEY) -> list[dict]:
    """Calcula la huella acústica de `path` con fpcalc y consulta AcoustID."""
    if not api_key:
        raise AcoustIDError("missing_api_key")

    duration, fingerprint = _fingerprint(path)

    params = urllib.parse.urlencode(
        {
            "client": api_key,
            "duration": duration,
            "fingerprint": fingerprint,
            "meta": "recordings releasegroups compress",
        }
    )
    request = urllib.request.Request(f"{LOOKUP_URL}?{params}")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # AcoustID devuelve un cuerpo JSON con el motivo real (p. ej. "invalid
        # API key") incluso en respuestas 4xx; sin esto sólo se veía el
        # genérico "HTTP Error 400: Bad Request" de urllib, sin pista de qué
        # falló de verdad.
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("error", {}).get("message")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            message = None
        raise AcoustIDError(message or str(exc)) from exc
    except urllib.error.URLError as exc:
        raise AcoustIDError(str(exc)) from exc

    if data.get("status") != "ok":
        raise AcoustIDError(data.get("error", {}).get("message", "unknown error"))

    matches = []
    seen: set[tuple[str, str, str]] = set()
    for result in data.get("results", []):
        score = result.get("score", 0)
        for recording in result.get("recordings", []) or []:
            title = (recording.get("title") or "").strip()
            if not title:
                continue
            artists = recording.get("artists", []) or []
            artist = "".join(a.get("name", "") + a.get("joinphrase", "") for a in artists).strip()
            if not artist:
                artist = ", ".join(a.get("name", "") for a in artists if a.get("name"))
            album, priority = _best_album(recording.get("releasegroups", []) or [])
            key = (title.lower(), artist.lower(), album.lower())
            if key in seen:
                continue
            seen.add(key)
            matches.append({"title": title, "artist": artist, "album": album, "score": score, "_priority": priority})

    matches.sort(key=lambda m: (round(m["score"], 2), m["_priority"]), reverse=True)
    for m in matches:
        m.pop("_priority", None)
    return matches
