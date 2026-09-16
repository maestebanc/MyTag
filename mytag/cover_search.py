"""Combina las distintas fuentes de búsqueda de portadas, en un orden fijo."""
from __future__ import annotations

from . import itunes, musicbrainz
from .cover_types import CoverCandidate, CoverSearchError

# Primero MusicBrainz y luego iTunes, tal y como se pidió.
_SOURCES = (
    musicbrainz.search_musicbrainz_candidates,
    itunes.search_itunes_candidates,
)


def search_all(album: str, albumartist: str) -> tuple[list[CoverCandidate], list[str]]:
    """Busca en todas las fuentes. Devuelve (candidatos, errores).

    Si una fuente falla no bloquea a las demás; sus errores se devuelven
    aparte para que la interfaz decida cómo mostrarlos (p. ej. solo si
    ninguna fuente encontró nada).
    """
    candidates: list[CoverCandidate] = []
    errors: list[str] = []
    for search_fn in _SOURCES:
        try:
            candidates.extend(search_fn(album, albumartist))
        except CoverSearchError as exc:
            errors.append(str(exc))
    return candidates, errors
