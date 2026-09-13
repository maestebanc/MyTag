"""Panel de edición de etiquetas, con soporte para edición múltiple (GTK4/Adwaita)."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GObject, Gtk

from ..constants import TAG_FIELDS

MULTIPLE_VALUES_PLACEHOLDER = "‹valores distintos›"


class TagEditor(Gtk.Box):
    __gtype_name__ = "MyTagTagEditor"

    __gsignals__ = {
        "changes-requested": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._tracks = []
        self._touched: set[str] = set()
        self._loading = False
        self._rows: dict[str, Adw.EntryRow] = {}

        self._labels: dict[str, str] = dict(TAG_FIELDS)

        group = Adw.PreferencesGroup()
        group.set_title("Etiquetas")
        for key, label in TAG_FIELDS:
            row = Adw.EntryRow()
            row.set_title(label)
            row.connect("changed", self._on_row_changed, key)
            self._rows[key] = row
            group.add(row)
        self.append(group)

        self.status_label = Gtk.Label(label="Selecciona uno o varios archivos FLAC en la tabla.")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_wrap(True)
        self.status_label.set_xalign(0)
        self.append(self.status_label)

        self.apply_button = Gtk.Button(label="Aplicar cambios a los seleccionados")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.connect("clicked", lambda _b: self.apply_pending())
        self.append(self.apply_button)

        self.set_tracks([])

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._touched.clear()
        self._loading = True
        enabled = bool(tracks)
        for key, row in self._rows.items():
            row.set_sensitive(enabled)
            base_label = self._labels[key]
            if not tracks:
                row.set_text("")
                row.set_title(base_label)
                continue
            values = {t.get_tag(key) for t in tracks}
            if len(values) == 1:
                row.set_text(next(iter(values)))
                row.set_title(base_label)
            else:
                row.set_text("")
                row.set_title(f"{base_label} · {MULTIPLE_VALUES_PLACEHOLDER}")
        self._loading = False
        self.apply_button.set_sensitive(enabled)

        if not tracks:
            self.status_label.set_text("Selecciona uno o varios archivos FLAC en la tabla.")
        elif len(tracks) == 1:
            self.status_label.set_text(f"Editando: {tracks[0].filename}")
        else:
            self.status_label.set_text(f"Editando {len(tracks)} temas a la vez")

    def has_pending_changes(self) -> bool:
        return bool(self._tracks and self._touched)

    def apply_pending(self) -> None:
        if not self.has_pending_changes():
            return
        changes = {key: self._rows[key].get_text() for key in self._touched}
        self.emit("changes-requested", changes)
        self._touched.clear()

    def _on_row_changed(self, row, key: str) -> None:
        if self._loading:
            return
        self._touched.add(key)
