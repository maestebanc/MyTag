"""Panel de edición de etiquetas, con soporte para edición múltiple (GTK4/Adwaita).

Cada cambio se aplica de inmediato a los temas seleccionados (en memoria);
"Guardar cambios" en la ventana principal es lo único que escribe a disco.
"""
from __future__ import annotations

from collections import Counter

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, GObject, Gtk, Pango

from .. import i18n
from ..constants import TAG_KEYS


TAG_ICONS: dict[str, str] = {
    "TITLE": "audio-x-generic-symbolic",
    "ARTIST": "avatar-default-symbolic",
    "ALBUM": "media-optical-cd-symbolic",
    "ALBUMARTIST": "system-users-symbolic",
    "DATE": "x-office-calendar-symbolic",
    "GENRE": "tag-symbolic",
    "TRACKNUMBER": "view-list-ordered-symbolic",
    "DISCNUMBER": "media-optical-dvd-symbolic",
}


class TagEditor(Gtk.Box):
    __gtype_name__ = "MyTagTagEditor"

    __gsignals__ = {
        "changes-requested": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._tracks = []
        self._loading = False
        self._rows: dict[str, Adw.EntryRow] = {}
        self._value_pickers: dict[str, Gtk.MenuButton] = {}

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_hexpand(True)
        header_box.add_css_class("editor-status-banner")

        self.status_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        self.status_icon.add_css_class("dim-label")
        header_box.append(self.status_icon)

        self.status_label = Gtk.Label(label=i18n.t("editor.select_prompt"))
        self.status_label.add_css_class("dim-label")
        self.status_label.add_css_class("caption")
        self.status_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.status_label.set_hexpand(True)
        self.status_label.set_xalign(0)
        header_box.append(self.status_label)

        self.count_badge = Gtk.Label()
        self.count_badge.add_css_class("pill-badge")
        self.count_badge.set_visible(False)
        header_box.append(self.count_badge)

        self.append(header_box)

        # Lista en caja compacta de etiquetas
        listbox = Gtk.ListBox()
        listbox.add_css_class("boxed-list")
        listbox.add_css_class("tag-editor-list")
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        for key in TAG_KEYS:
            row = Adw.EntryRow()
            row.set_title(i18n.t(f"tag.{key.lower()}"))
            icon_name = TAG_ICONS.get(key)
            if icon_name:
                icon = Gtk.Image.new_from_icon_name(icon_name)
                icon.add_css_class("dim-label")
                row.add_prefix(icon)
            row.connect("changed", self._on_row_changed, key)

            picker_btn = Gtk.MenuButton()
            picker_btn.set_icon_name("pan-down-symbolic")
            picker_btn.add_css_class("flat")
            picker_btn.set_valign(Gtk.Align.CENTER)
            picker_btn.set_tooltip_text(i18n.t("editor.picker_tooltip"))
            picker_btn.set_visible(False)
            row.add_suffix(picker_btn)
            self._value_pickers[key] = picker_btn

            self._rows[key] = row
            listbox.append(row)
        self.append(listbox)

        self.set_tracks([])

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._loading = True
        enabled = bool(tracks)
        for key, row in self._rows.items():
            row.set_sensitive(enabled)
            base_label = i18n.t(f"tag.{key.lower()}")
            picker = self._value_pickers.get(key)
            if not tracks:
                row.set_text("")
                row.set_title(base_label)
                if picker:
                    picker.set_visible(False)
                continue

            raw_values = [t.get_tag(key).strip() for t in tracks]
            unique_raw = set(raw_values)
            non_empty_counts = Counter(v for v in raw_values if v)

            if len(unique_raw) == 1:
                row.set_text(next(iter(unique_raw)))
                row.set_title(base_label)
                if picker:
                    picker.set_visible(False)
            else:
                row.set_text("")
                row.set_title(f"{base_label} · {i18n.t('editor.multiple_values')}")
                if non_empty_counts and picker:
                    self._setup_picker_popover(key, row, picker, non_empty_counts)
                    picker.set_visible(True)
                elif picker:
                    picker.set_visible(False)
        self._loading = False

        if not tracks:
            self.count_badge.set_visible(False)
            self.status_icon.set_from_icon_name("dialog-information-symbolic")
            self.status_label.set_text(i18n.t("editor.select_prompt"))
        elif len(tracks) == 1:
            self.count_badge.set_text(i18n.t("editor.badge_one"))
            self.count_badge.set_visible(True)
            self.status_icon.set_from_icon_name("audio-x-generic-symbolic")
            self.status_label.set_text(i18n.t("editor.editing_one", filename=tracks[0].filename))
        else:
            self.count_badge.set_text(i18n.t("editor.badge_many", n=len(tracks)))
            self.count_badge.set_visible(True)
            self.status_icon.set_from_icon_name("media-playlist-consecutive-symbolic")
            self.status_label.set_text(i18n.t("editor.editing_many", n=len(tracks)))

    def _setup_picker_popover(
        self, key: str, row: Adw.EntryRow, picker: Gtk.MenuButton, counts: Counter
    ) -> None:
        popover = Gtk.Popover()
        popover.add_css_class("menu")

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        outer.set_margin_top(6)
        outer.set_margin_bottom(6)
        outer.set_margin_start(6)
        outer.set_margin_end(6)

        header = Gtk.Label(label=i18n.t("editor.picker_title"), xalign=0)
        header.add_css_class("dim-label")
        header.add_css_class("caption")
        header.set_margin_start(4)
        header.set_margin_bottom(2)
        outer.append(header)

        items_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))

        for val, count in sorted_items:
            btn = Gtk.Button()
            btn.add_css_class("flat")

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            box.set_margin_start(4)
            box.set_margin_end(4)

            lbl_val = Gtk.Label(label=val, xalign=0)
            lbl_val.set_hexpand(True)
            lbl_val.set_ellipsize(Pango.EllipsizeMode.END)
            lbl_val.set_max_width_chars(28)
            box.append(lbl_val)

            lbl_cnt = Gtk.Label(label=i18n.t("editor.track_count", n=count))
            lbl_cnt.add_css_class("dim-label")
            lbl_cnt.add_css_class("caption")
            box.append(lbl_cnt)

            btn.set_child(box)

            def on_click(_b, chosen_val=val, target_row=row, target_key=key, pop=popover):
                pop.popdown()
                if target_row.get_text() == chosen_val:
                    target_row.set_title(i18n.t(f"tag.{target_key.lower()}"))
                    self.emit("changes-requested", {target_key: chosen_val})
                else:
                    target_row.set_text(chosen_val)

            btn.connect("clicked", on_click)
            items_box.append(btn)

        if len(sorted_items) > 6:
            scroller = Gtk.ScrolledWindow()
            scroller.set_max_content_height(240)
            scroller.set_propagate_natural_height(True)
            scroller.set_child(items_box)
            outer.append(scroller)
        else:
            outer.append(items_box)

        popover.set_child(outer)
        picker.set_popover(popover)

    def _on_row_changed(self, row, key: str) -> None:
        if self._loading or not self._tracks:
            return
        base_label = i18n.t(f"tag.{key.lower()}")
        row.set_title(base_label)
        self.emit("changes-requested", {key: row.get_text()})
