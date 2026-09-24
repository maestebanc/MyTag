"""Módulo para generación y exportación de listas de reproducción (.m3u / .m3u8)."""
from __future__ import annotations

import os
from typing import Sequence
from .audio_track import AudioTrack


def generate_m3u_content(tracks: Sequence[AudioTrack], playlist_path: str) -> str:
    """Genera el contenido de una lista de reproducción M3U8 extendida.

    Usa rutas relativas si los archivos de audio comparten ubicación o subcarpeta
    con el archivo de la lista, facilitando su portabilidad. De lo contrario, usa
    rutas absolutas.
    """
    playlist_dir = os.path.dirname(os.path.abspath(playlist_path))
    lines: list[str] = ["#EXTM3U\n"]

    for track in tracks:
        duration = -1
        try:
            if hasattr(track.audio, "info") and hasattr(track.audio.info, "length") and track.audio.info.length:
                duration = int(track.audio.info.length)
        except Exception:
            duration = -1

        artist = track.get_tag("ARTIST") or ""
        title = track.get_tag("TITLE") or track.filename
        display_name = f"{artist} - {title}" if artist else title

        lines.append(f"#EXTINF:{duration},{display_name}\n")

        try:
            rel = os.path.relpath(track.path, playlist_dir)
            lines.append(f"{rel}\n")
        except ValueError:
            lines.append(f"{track.path}\n")

    return "".join(lines)


def write_m3u_file(tracks: Sequence[AudioTrack], playlist_path: str) -> None:
    """Escribe la lista de reproducción en disco en codificación UTF-8."""
    content = generate_m3u_content(tracks, playlist_path)
    with open(playlist_path, "w", encoding="utf-8") as f:
        f.write(content)
