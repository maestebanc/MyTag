"""Identificación de temas por huella de audio (Chromaprint + AcoustID)."""
from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

FPCALC_BINARY = "fpcalc"
LOOKUP_URL = "https://api.acoustid.org/v2/lookup"
REQUEST_TIMEOUT = 15


class AcoustIDError(Exception):
    """Error al calcular la huella de audio o al consultar AcoustID."""


def fpcalc_available() -> bool:
    return shutil.which(FPCALC_BINARY) is not None


def _fingerprint(path: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            [FPCALC_BINARY, "-json", path],
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


def identify(path: str, api_key: str) -> list[dict]:
    """Devuelve candidatos [{title, artist, album, score}, ...], mejor primero."""
    if not api_key:
        raise AcoustIDError("missing_api_key")

    duration, fingerprint = _fingerprint(path)

    params = urllib.parse.urlencode(
        {
            "client": api_key,
            "duration": duration,
            "fingerprint": fingerprint,
            "meta": "recordings+releasegroups+compress",
        }
    )
    request = urllib.request.Request(f"{LOOKUP_URL}?{params}")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise AcoustIDError(str(exc)) from exc

    if data.get("status") != "ok":
        raise AcoustIDError(data.get("error", {}).get("message", "unknown error"))

    matches = []
    for result in data.get("results", []):
        score = result.get("score", 0)
        for recording in result.get("recordings", []) or []:
            title = recording.get("title", "")
            if not title:
                continue
            artist = ", ".join(a.get("name", "") for a in recording.get("artists", []) or [])
            release_groups = recording.get("releasegroups", []) or []
            album = release_groups[0].get("title", "") if release_groups else ""
            matches.append({"title": title, "artist": artist, "album": album, "score": score})

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches
