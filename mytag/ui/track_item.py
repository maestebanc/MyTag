"""Envoltorio GObject de un AudioTrack, para usarlo en un Gio.ListStore."""
from __future__ import annotations

import gi

gi.require_version("GObject", "2.0")
from gi.repository import GObject

from ..audio_track import AudioTrack
from ..constants import TAG_KEYS

_PROPERTY_NAMES = ["filename", "missing-fields"] + [key.lower() for key in TAG_KEYS]


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
        return self.track.get_tag("ARTIST")

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

    @GObject.Property(type=str)
    def missing_fields(self) -> str:
        """Campos "deseables" que faltan, separados por coma (para la
        columna de completitud). Cadena vacía si no falta nada."""
        missing = []
        if not self.track.get_cover_bytes():
            missing.append("cover")
        if not self.track.get_tag("DATE"):
            missing.append("date")
        if not self.track.get_tag("GENRE"):
            missing.append("genre")
        return ",".join(missing)

    def refresh(self) -> None:
        """Notifica a las vistas ligadas que los valores han cambiado."""
        for name in _PROPERTY_NAMES:
            self.notify(name)
