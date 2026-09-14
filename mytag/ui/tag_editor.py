"""Panel de edición de etiquetas, con soporte para edición múltiple (GTK4/Adwaita).

Cada cambio se aplica de inmediato a los temas seleccionados (en memoria);
"Guardar cambios" en la ventana principal es lo único que escribe a disco.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GObject, Gtk

from .. import i18n
from ..constants import TAG_KEYS


class TagEditor(Gtk.Box):
    __gtype_name__ = "MyTagTagEditor"

    __gsignals__ = {
        "changes-requested": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._tracks = []
        self._loading = False
        self._rows: dict[str, Adw.EntryRow] = {}

        heading = Gtk.Label(label=i18n.t("editor.heading"))
        heading.add_css_class("heading")
        heading.set_xalign(0)
        self.append(heading)

        # Adw.PreferencesGroup solo aplica el estilo de "lista en caja"
        # dentro de un Adw.PreferencesPage; aquí lo construimos a mano con un
        # Gtk.ListBox para tener ese mismo aspecto también fuera de ese
        # contexto.
        listbox = Gtk.ListBox()
        listbox.add_css_class("boxed-list")
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        for key in TAG_KEYS:
            row = Adw.EntryRow()
            row.set_title(i18n.t(f"tag.{key.lower()}"))
            row.connect("changed", self._on_row_changed, key)
            self._rows[key] = row
            listbox.append(row)
        self.append(listbox)

        self.status_label = Gtk.Label(label=i18n.t("editor.select_prompt"))
        self.status_label.add_css_class("dim-label")
        self.status_label.set_wrap(True)
        self.status_label.set_xalign(0)
        self.append(self.status_label)

        self.set_tracks([])

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._loading = True
        enabled = bool(tracks)
        for key, row in self._rows.items():
            row.set_sensitive(enabled)
            base_label = i18n.t(f"tag.{key.lower()}")
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
                row.set_title(f"{base_label} · {i18n.t('editor.multiple_values')}")
        self._loading = False

        if not tracks:
            self.status_label.set_text(i18n.t("editor.select_prompt"))
        elif len(tracks) == 1:
            self.status_label.set_text(i18n.t("editor.editing_one", filename=tracks[0].filename))
        else:
            self.status_label.set_text(i18n.t("editor.editing_many", n=len(tracks)))

    def _on_row_changed(self, row, key: str) -> None:
        if self._loading or not self._tracks:
            return
        self.emit("changes-requested", {key: row.get_text()})
