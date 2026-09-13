"""Representa un archivo FLAC cargado, con sus cambios pendientes de guardar."""
from __future__ import annotations

import os

from mutagen.flac import FLAC, Picture

from .cover_utils import image_dimensions


class AudioTrack:
    def __init__(self, path: str):
        self.path = path
        self.flac = FLAC(path)
        self.dirty_tags = False
        # None -> sin cambio pendiente; (data, mime) -> nueva portada pendiente;
        # False -> pendiente de eliminar la portada.
        self.pending_cover: tuple[bytes, str] | bool | None = None

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def is_dirty(self) -> bool:
        return self.dirty_tags or self.pending_cover is not None

    def get_tag(self, key: str) -> str:
        values = self.flac.get(key)
        return values[0] if values else ""

    def set_tag(self, key: str, value: str) -> None:
        value = (value or "").strip()
        if value:
            self.flac[key] = [value]
        elif key in self.flac:
            del self.flac[key]
        self.dirty_tags = True

    def get_cover_bytes(self) -> bytes | None:
        if self.pending_cover is not None:
            return None if self.pending_cover is False else self.pending_cover[0]
        pictures = self.flac.pictures
        return pictures[0].data if pictures else None

    def has_saved_cover(self) -> bool:
        return bool(self.flac.pictures)

    def set_cover_bytes(self, data: bytes, mime: str) -> None:
        self.pending_cover = (data, mime)

    def remove_cover(self) -> None:
        self.pending_cover = False

    def save(self) -> None:
        had_cover_change = self.pending_cover is not None
        if had_cover_change:
            self.flac.clear_pictures()
            if self.pending_cover:
                data, mime = self.pending_cover
                picture = Picture()
                picture.data = data
                picture.type = 3  # Cover (front)
                picture.mime = mime
                width, height = image_dimensions(data)
                picture.width = width
                picture.height = height
                picture.depth = 24
                self.flac.add_picture(picture)
            self.pending_cover = None
        if self.dirty_tags or had_cover_change:
            self.flac.save()
        self.dirty_tags = False
