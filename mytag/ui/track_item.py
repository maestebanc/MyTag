"""Envoltorio GObject de un AudioTrack, para usarlo en un Gio.ListStore."""
from __future__ import annotations

import gi

import re

gi.require_version("GObject", "2.0")
from gi.repository import GObject

from ..audio_track import AudioTrack
from ..constants import TAG_KEYS

_PROPERTY_NAMES = ["filename", "missing-fields", "integrity-error", "status-sort-key", "track_order_key"] + [key.lower() for key in TAG_KEYS]


class TrackItem(GObject.Object):
    __gtype_name__ = "MyTagTrackItem"

    def __init__(self, track: AudioTrack):
        super().__init__()
        self.track = track

    @GObject.Property(type=str)
    def filename(self) -> str:
        return self.track.filename

    @GObject.Property(type=str)
    def title(self) -> str:
        return self.track.get_tag("TITLE")

    @GObject.Property(type=str)
    def artist(self) -> str:
        return self.track.get_tag("ARTIST") or self.track.get_tag("ALBUMARTIST")

    @GObject.Property(type=str)
    def album(self) -> str:
        return self.track.get_tag("ALBUM")

    @GObject.Property(type=str)
    def albumartist(self) -> str:
        return self.track.get_tag("ALBUMARTIST")

    @GObject.Property(type=str)
    def date(self) -> str:
        return self.track.get_tag("DATE")

    @GObject.Property(type=str)
    def genre(self) -> str:
        return self.track.get_tag("GENRE")

    @GObject.Property(type=str)
    def tracknumber(self) -> str:
        return self.track.get_tag("TRACKNUMBER")

    @GObject.Property(type=str)
    def discnumber(self) -> str:
        return self.track.get_tag("DISCNUMBER")

    @GObject.Property(type=int)
    def track_order_key(self) -> int:
        raw_disc = self.track.get_tag("DISCNUMBER")
        disc_nums = re.findall(r"\d+", raw_disc or "")
        disc = int(disc_nums[0]) if disc_nums else 1

        raw_track = self.track.get_tag("TRACKNUMBER")
        track_nums = re.findall(r"\d+", raw_track or "")
        track = int(track_nums[0]) if track_nums else 99999
        return disc * 100000 + track

    @GObject.Property(type=str)
    def missing_fields(self) -> str:
        """Campos esenciales que faltan (para la columna de completitud).
        Solo avisa si falta título, artista del álbum (o artista) o portada."""
        missing = []
        if not self.track.get_tag("TITLE").strip():
            missing.append("title")
        if not (self.track.get_tag("ALBUMARTIST").strip() or self.track.get_tag("ARTIST").strip()):
            missing.append("artist")
        if not self.track.get_cover_bytes():
            missing.append("cover")
        return ",".join(missing)

    @GObject.Property(type=str)
    def integrity_error(self) -> str:
        return self.track.integrity_error or ""

    @GObject.Property(type=str)
    def status_sort_key(self) -> str:
        """Clave de ordenación para la columna de estado: errores primero (0_), incompletos (1_), correctos (2_)."""
        if self.track.integrity_error:
            return f"0_error_{self.track.integrity_error}"
        missing = self.missing_fields
        if missing:
            return f"1_missing_{missing}"
        return "2_ok"

    def refresh(self) -> None:
        """Notifica a las vistas ligadas que los valores han cambiado."""
        for name in _PROPERTY_NAMES:
            self.notify(name)
