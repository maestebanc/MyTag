"""Diálogo para renombrar archivos FLAC a partir de sus etiquetas, con
vista previa y confirmación (renombrar es inmediato en disco, no hay
"deshacer" como con el resto de cambios)."""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GObject, Gtk

from .. import config, i18n
from ..rename_pattern import DEFAULT_PATTERN, render_filename


class RenameDialog(Adw.Dialog):
    __gtype_name__ = "MyTagRenameDialog"

    __gsignals__ = {
        "rename-confirmed": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, tracks: list):
        super().__init__()
        self._tracks = tracks
        self._planned: dict = {}

        self.set_title(i18n.t("rename.title"))
        self.set_content_width(560)
        self.set_content_height(560)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("rename.title")))
        toolbar_view.add_top_bar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)

        pattern_list = Gtk.ListBox()
        pattern_list.add_css_class("boxed-list")
        pattern_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pattern_row = Adw.EntryRow(title=i18n.t("rename.pattern"))
        cfg_pattern = config.load_config().get("default_rename_pattern", DEFAULT_PATTERN)
        self.pattern_row.set_text(cfg_pattern or DEFAULT_PATTERN)
        self.pattern_row.connect("changed", lambda _r: self._refresh_preview())
        pattern_list.append(self.pattern_row)
        outer.append(pattern_list)

        hint = Gtk.Label(label=i18n.t("rename.tokens_hint"))
        hint.add_css_class("dim-label")
        hint.add_css_class("caption")
        hint.set_wrap(True)
        hint.set_xalign(0)
        outer.append(hint)

        tokens_flow = Gtk.FlowBox()
        tokens_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        tokens_flow.set_max_children_per_line(7)
        tokens_flow.set_min_children_per_line(3)
        tokens_flow.set_row_spacing(4)
        tokens_flow.set_column_spacing(4)
        for token in ("%track%", "%title%", "%artist%", "%album%", "%year%", "%genre%", "%disc%"):
            btn = Gtk.Button(label=token)
            btn.add_css_class("flat")
            btn.add_css_class("token-button")
            btn.set_tooltip_text(f"Insertar {token}")
            btn.connect("clicked", lambda _b, t=token: self._insert_token(t))
            tokens_flow.append(btn)
        outer.append(tokens_flow)

        self.preview_list = Gtk.ListBox()
        self.preview_list.add_css_class("boxed-list")
        self.preview_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.preview_list)
        scroller.set_vexpand(True)
        outer.append(scroller)

        toolbar_view.set_content(outer)
        toolbar_view.add_bottom_bar(self._build_action_bar())
        self.set_child(toolbar_view)

        self._refresh_preview()

    def _insert_token(self, token: str) -> None:
        current = self.pattern_row.get_text()
        self.pattern_row.set_text(current + token)

    def _refresh_preview(self) -> None:
        row = self.preview_list.get_row_at_index(0)
        while row is not None:
            self.preview_list.remove(row)
            row = self.preview_list.get_row_at_index(0)

        pattern = self.pattern_row.get_text()
        self._planned = {}
        for track in self._tracks:
            new_name = render_filename(track, pattern)
            new_path = os.path.join(os.path.dirname(track.path), new_name)
            self._planned[track] = new_path

            action_row = Adw.ActionRow(title=track.filename)
            icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
            icon.add_css_class("dim-label")
            action_row.add_prefix(icon)
            if new_path != track.path:
                action_row.set_subtitle(f"→ {new_name}")
            else:
                action_row.set_subtitle(i18n.t("rename.unchanged"))
            self.preview_list.append(action_row)

    def _build_action_bar(self) -> Gtk.Widget:
        bar = Gtk.ActionBar()

        btn_cancel = Gtk.Button(label=i18n.t("action.cancel"))
        btn_cancel.connect("clicked", lambda _b: self.close())
        bar.pack_start(btn_cancel)

        btn_rename = Gtk.Button()
        ren_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ren_box.append(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
        ren_box.append(Gtk.Label(label=i18n.t("rename.confirm")))
        btn_rename.set_child(ren_box)
        btn_rename.add_css_class("suggested-action")
        btn_rename.connect("clicked", self._on_confirm)
        bar.pack_end(btn_rename)

        return bar

    def _on_confirm(self, _button) -> None:
        self.emit("rename-confirmed", dict(self._planned))
        self.close()
