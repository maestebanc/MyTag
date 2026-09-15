"""Representa un archivo de audio (FLAC o MP3) cargado, con sus cambios pendientes de guardar."""
from __future__ import annotations

import os

from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.id3 import (
    APIC,
    TIT2,
    TPE1,
    TALB,
    TPE2,
    TDRC,
    TYER,
    TCON,
    TRCK,
    TPOS,
    PictureType,
)

from .cover_utils import image_dimensions

# Mapeo de claves estándar a clases de marco ID3 para MP3
ID3_FRAME_CLASSES = {
    "TITLE": TIT2,
    "ARTIST": TPE1,
    "ALBUM": TALB,
    "ALBUMARTIST": TPE2,
    "DATE": TDRC,
    "GENRE": TCON,
    "TRACKNUMBER": TRCK,
    "DISCNUMBER": TPOS,
}


class AudioTrack:
    def __init__(self, path: str):
        self.path = path
        self.is_mp3 = path.lower().endswith(".mp3")
        self.dirty_tags = False
        # None -> sin cambio pendiente; (data, mime) -> nueva portada pendiente;
        # False -> pendiente de eliminar la portada.
        self.pending_cover: tuple[bytes, str] | bool | None = None
        self._load()

    def _load(self) -> None:
        if self.is_mp3:
            self.audio = MP3(self.path)
            if self.audio.tags is None:
                self.audio.add_tags()
        else:
            self.audio = FLAC(self.path)

    @property
    def flac(self):
        """Compatibilidad hacia atrás por si algún componente legacy consulta .flac."""
        return self.audio

    @flac.setter
    def flac(self, value):
        self.audio = value

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    def update_path(self, new_path: str) -> None:
        """Actualiza la ruta tras un renombrado externo (en disco).

        mutagen guarda su propio nombre de archivo interno en el momento de cargarlo;
        si sólo se actualizara self.path, save() seguiría intentando escribir en la
        ruta antigua, que ya no existe.
        """
        self.path = new_path
        self.audio.filename = new_path
        self.is_mp3 = new_path.lower().endswith(".mp3")

    @property
    def is_dirty(self) -> bool:
        return self.dirty_tags or self.pending_cover is not None

    def get_tag(self, key: str) -> str:
        if self.is_mp3:
            if self.audio.tags is None:
                return ""
            frame_cls = ID3_FRAME_CLASSES.get(key)
            if frame_cls is None:
                return ""
            frame_id = frame_cls.__name__
            frame = self.audio.tags.get(frame_id)
            if frame is None and key == "DATE":
                frame = self.audio.tags.get("TYER")
            if frame is not None and getattr(frame, "text", None):
                return str(frame.text[0])
            return ""
        else:
            values = self.audio.get(key)
            return values[0] if values else ""

    def set_tag(self, key: str, value: str) -> None:
        value = (value or "").strip()
        if self.is_mp3:
            if self.audio.tags is None:
                self.audio.add_tags()
            frame_cls = ID3_FRAME_CLASSES.get(key)
            if frame_cls is not None:
                frame_id = frame_cls.__name__
                if value:
                    self.audio.tags[frame_id] = frame_cls(encoding=3, text=[value])
                    if key == "DATE":
                        self.audio.tags.delall("TYER")
                else:
                    self.audio.tags.delall(frame_id)
                    if key == "DATE":
                        self.audio.tags.delall("TYER")
        else:
            if value:
                self.audio[key] = [value]
            elif key in self.audio:
                del self.audio[key]
        self.dirty_tags = True

    def _saved_cover_bytes(self) -> bytes | None:
        if self.is_mp3:
            if self.audio.tags is None:
                return None
            apics = [v for k, v in self.audio.tags.items() if k.startswith("APIC")]
            front = next((f for f in apics if getattr(f, "type", None) == PictureType.COVER_FRONT), None)
            if front is None and apics:
                front = apics[0]
            return bytes(front.data) if front else None
        else:
            pictures = getattr(self.audio, "pictures", [])
            return pictures[0].data if pictures else None

    def get_cover_bytes(self) -> bytes | None:
        if self.pending_cover is not None:
            return None if self.pending_cover is False else self.pending_cover[0]
        return self._saved_cover_bytes()

    def has_saved_cover(self) -> bool:
        return self._saved_cover_bytes() is not None

    def set_cover_bytes(self, data: bytes, mime: str) -> None:
        self.pending_cover = (data, mime)

    def remove_cover(self) -> None:
        self.pending_cover = False

    def save(self) -> None:
        had_cover_change = self.pending_cover is not None
        if had_cover_change:
            if self.is_mp3:
                if self.audio.tags is None:
                    self.audio.add_tags()
                self.audio.tags.delall("APIC")
                if self.pending_cover:
                    data, mime = self.pending_cover
                    self.audio.tags.add(
                        APIC(
                            encoding=3,
                            mime=mime,
                            type=PictureType.COVER_FRONT,
                            desc="Cover",
                            data=data,
                        )
                    )
            else:
                self.audio.clear_pictures()
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
                    self.audio.add_picture(picture)
            self.pending_cover = None

        if self.dirty_tags or had_cover_change:
            self.audio.save()
        self.dirty_tags = False

    def revert(self) -> None:
        """Descarta los cambios pendientes (tags y portada), releyendo del disco."""
        self._load()
        self.pending_cover = None
        self.dirty_tags = False
