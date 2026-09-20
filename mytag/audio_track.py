"""Representa un archivo de audio (FLAC, MP3, M4A/MP4, OGG, OPUS) cargado, con sus cambios pendientes de guardar."""
from __future__ import annotations

import base64
import os

from mutagen.flac import FLAC, Picture
from mutagen.id3 import (
    APIC,
    TALB,
    TCON,
    TDRC,
    TIT2,
    TPOS,
    TPE1,
    TPE2,
    TRCK,
    TYER,
    PictureType,
)
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

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

# Mapeo de claves estándar a átomos de cuatro caracteres para MP4 / M4A
MP4_TAG_MAP = {
    "TITLE": "\xa9nam",
    "ARTIST": "\xa9ART",
    "ALBUM": "\xa9alb",
    "ALBUMARTIST": "aART",
    "DATE": "\xa9day",
    "GENRE": "\xa9gen",
}


def _detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp3":
        return "mp3"
    if ext in (".m4a", ".mp4"):
        return "mp4"
    if ext in (".ogg", ".oga"):
        return "ogg"
    if ext == ".opus":
        return "opus"
    return "flac"


class AudioTrack:
    def __init__(self, path: str):
        self.path = path
        self.format = _detect_format(path)
        self.is_mp3 = (self.format == "mp3")
        self.dirty_tags = False
        self.integrity_error: str | None = None
        # None -> sin cambio pendiente; (data, mime) -> nueva portada pendiente;
        # False -> pendiente de eliminar la portada.
        self.pending_cover: tuple[bytes, str] | bool | None = None
        self._load()

    def _load(self) -> None:
        if self.format == "mp3":
            self.audio = MP3(self.path)
            if self.audio.tags is None:
                self.audio.add_tags()
        elif self.format == "mp4":
            self.audio = MP4(self.path)
            if self.audio.tags is None:
                self.audio.add_tags()
        elif self.format == "ogg":
            self.audio = OggVorbis(self.path)
            if self.audio.tags is None:
                self.audio.add_tags()
        elif self.format == "opus":
            self.audio = OggOpus(self.path)
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
        self.format = _detect_format(new_path)
        self.is_mp3 = (self.format == "mp3")

    @property
    def is_dirty(self) -> bool:
        return self.dirty_tags or self.pending_cover is not None

    def get_tag(self, key: str) -> str:
        if self.format == "mp3":
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
        elif self.format == "mp4":
            if self.audio.tags is None:
                return ""
            if key == "TRACKNUMBER":
                trkn = self.audio.tags.get("trkn")
                if trkn and len(trkn) > 0:
                    num, total = trkn[0]
                    if total:
                        return f"{num}/{total}"
                    elif num:
                        return str(num)
                return ""
            elif key == "DISCNUMBER":
                disk = self.audio.tags.get("disk")
                if disk and len(disk) > 0:
                    num, total = disk[0]
                    if total:
                        return f"{num}/{total}"
                    elif num:
                        return str(num)
                return ""
            else:
                atom = MP4_TAG_MAP.get(key)
                if atom:
                    values = self.audio.tags.get(atom)
                    if values:
                        return str(values[0])
                return ""
        else:
            # FLAC, Ogg Vorbis, Opus (comentarios Vorbis estándar)
            values = self.audio.get(key)
            return values[0] if values else ""

    def set_tag(self, key: str, value: str) -> None:
        value = (value or "").strip()
        if self.format == "mp3":
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
        elif self.format == "mp4":
            if self.audio.tags is None:
                self.audio.add_tags()
            if key == "TRACKNUMBER":
                if not value:
                    self.audio.tags.pop("trkn", None)
                else:
                    parts = value.split("/")
                    num = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                    existing_tot = 0
                    if "trkn" in self.audio.tags and self.audio.tags["trkn"]:
                        existing_tot = self.audio.tags["trkn"][0][1]
                    tot = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else existing_tot
                    self.audio.tags["trkn"] = [(num, tot)]
            elif key == "DISCNUMBER":
                if not value:
                    self.audio.tags.pop("disk", None)
                else:
                    parts = value.split("/")
                    num = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                    existing_tot = 0
                    if "disk" in self.audio.tags and self.audio.tags["disk"]:
                        existing_tot = self.audio.tags["disk"][0][1]
                    tot = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else existing_tot
                    self.audio.tags["disk"] = [(num, tot)]
            else:
                atom = MP4_TAG_MAP.get(key)
                if atom:
                    if value:
                        self.audio.tags[atom] = [value]
                    else:
                        self.audio.tags.pop(atom, None)
        else:
            # FLAC, Ogg Vorbis, Opus
            if value:
                self.audio[key] = [value]
            elif key in self.audio:
                del self.audio[key]
        self.dirty_tags = True

    def _saved_cover_bytes(self) -> bytes | None:
        if self.format == "mp3":
            if self.audio.tags is None:
                return None
            apics = [v for k, v in self.audio.tags.items() if k.startswith("APIC")]
            front = next((f for f in apics if getattr(f, "type", None) == PictureType.COVER_FRONT), None)
            if front is None and apics:
                front = apics[0]
            return bytes(front.data) if front else None
        elif self.format == "mp4":
            if self.audio.tags is None:
                return None
            covr = self.audio.tags.get("covr")
            if covr and len(covr) > 0:
                return bytes(covr[0])
            return None
        elif self.format == "flac":
            pictures = getattr(self.audio, "pictures", [])
            return pictures[0].data if pictures else None
        else:
            # Ogg Vorbis / Opus
            if self.audio.tags is None:
                return None
            pics = self.audio.tags.get("METADATA_BLOCK_PICTURE", [])
            if pics:
                try:
                    pic = Picture(base64.b64decode(pics[0]))
                    return pic.data
                except Exception:
                    pass
            covers = self.audio.tags.get("COVERART", [])
            if covers:
                try:
                    return base64.b64decode(covers[0])
                except Exception:
                    pass
            return None

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
            if self.format == "mp3":
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
            elif self.format == "mp4":
                if self.audio.tags is None:
                    self.audio.add_tags()
                if self.pending_cover:
                    data, mime = self.pending_cover
                    fmt = MP4Cover.FORMAT_PNG if "png" in mime.lower() else MP4Cover.FORMAT_JPEG
                    self.audio.tags["covr"] = [MP4Cover(data, imageformat=fmt)]
                else:
                    self.audio.tags.pop("covr", None)
            elif self.format == "flac":
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
            elif self.format in ("ogg", "opus"):
                if self.audio.tags is None:
                    self.audio.add_tags()
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
                    encoded = base64.b64encode(picture.write()).decode("ascii")
                    self.audio.tags["METADATA_BLOCK_PICTURE"] = [encoded]
                    for k in ("COVERART", "COVERARTMIME"):
                        if k in self.audio.tags:
                            del self.audio.tags[k]
                else:
                    for k in ("METADATA_BLOCK_PICTURE", "COVERART", "COVERARTMIME"):
                        if k in self.audio.tags:
                            del self.audio.tags[k]
            self.pending_cover = None

        if self.dirty_tags or had_cover_change:
            self.audio.save()
        self.dirty_tags = False

    def revert(self) -> None:
        """Descarta los cambios pendientes (tags y portada), releyendo del disco."""
        self._load()
        self.pending_cover = None
        self.dirty_tags = False
