"""Pantalla de preferencias: idioma y escala de la interfaz.

Los cambios se guardan en memoria mientras el diálogo está abierto y solo se
aplican y persisten al pulsar "Guardar"; "Cancelar" cierra sin tocar nada.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from .. import config, i18n
from .style import apply_theme, apply_ui_scale

THEME_CODES = ["system", "light", "dark"]

SCALE_PRESETS = [75, 90, 100, 110, 125, 150, 175, 200]
MIN_SCALE = 25
MAX_SCALE = 400


def _parse_percent(text: str, fallback: int) -> int:
    try:
        value = int(float(text))
    except ValueError:
        return fallback
    return max(MIN_SCALE, min(MAX_SCALE, value))


class PreferencesDialog(Adw.Dialog):
    __gtype_name__ = "MyTagPreferencesDialog"

    def __init__(self):
        super().__init__()
        self.set_title(i18n.t("prefs.title"))
        self.set_content_width(640)
        self.set_content_height(680)

        saved_config = config.load_config()
        saved_scale = saved_config.get("ui_scale", 100)
        self._pending_language = i18n.get_language()
        self._pending_scale = saved_scale
        self._pending_theme = saved_config.get("theme", "system")
        self._pending_acoustid_key = saved_config.get("acoustid_api_key", "")

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("prefs.title")))
        toolbar_view.add_top_bar(header)

        page = Adw.PreferencesPage()
        page.set_vexpand(True)

        general_group = Adw.PreferencesGroup(title=i18n.t("prefs.general_group"))
        general_group.add(self._build_language_row())
        page.add(general_group)

        appearance_group = Adw.PreferencesGroup(title=i18n.t("prefs.appearance_group"))
        appearance_group.add(self._build_theme_row())
        scale_row, custom_row, revealer = self._build_scale_rows(saved_scale)
        appearance_group.add(scale_row)
        appearance_group.add(revealer)
        page.add(appearance_group)

        acoustid_group = Adw.PreferencesGroup(
            title=i18n.t("prefs.acoustid_group"), description=i18n.t("prefs.acoustid_key_note")
        )
        acoustid_group.add(self._build_acoustid_row())
        page.add(acoustid_group)

        toolbar_view.set_content(page)
        toolbar_view.add_bottom_bar(self._build_action_bar())

        self.set_child(toolbar_view)

    def _build_theme_row(self) -> Adw.ComboRow:
        names = Gtk.StringList.new(
            [i18n.t("prefs.theme_system"), i18n.t("prefs.theme_light"), i18n.t("prefs.theme_dark")]
        )
        row = Adw.ComboRow(title=i18n.t("prefs.theme"), model=names)
        current = self._pending_theme
        row.set_selected(THEME_CODES.index(current) if current in THEME_CODES else 0)

        def on_changed(row: Adw.ComboRow, _pspec) -> None:
            index = row.get_selected()
            if 0 <= index < len(THEME_CODES):
                self._pending_theme = THEME_CODES[index]

        row.connect("notify::selected", on_changed)
        return row

    def _build_acoustid_row(self) -> Adw.EntryRow:
        row = Adw.EntryRow(title=i18n.t("prefs.acoustid_key"))
        row.set_text(self._pending_acoustid_key)
        row.add_css_class("caption")

        def on_changed(entry: Adw.EntryRow) -> None:
            self._pending_acoustid_key = entry.get_text().strip()

        row.connect("changed", on_changed)
        return row

    def _build_language_row(self) -> Adw.ComboRow:
        codes = i18n.SUPPORTED_LANGUAGES
        names = Gtk.StringList.new([i18n.LANGUAGE_NAMES[code] for code in codes])
        row = Adw.ComboRow(title=i18n.t("prefs.language"), model=names)
        row.set_subtitle(i18n.t("prefs.language_restart_note"))
        current = i18n.get_language()
        row.set_selected(codes.index(current) if current in codes else 0)

        def on_changed(row: Adw.ComboRow, _pspec) -> None:
            index = row.get_selected()
            if 0 <= index < len(codes):
                self._pending_language = codes[index]

        row.connect("notify::selected", on_changed)
        return row

    def _build_scale_rows(self, saved_scale: int) -> tuple[Adw.ComboRow, Adw.EntryRow, Gtk.Revealer]:
        options = [f"{p}%" for p in SCALE_PRESETS] + [i18n.t("prefs.ui_scale_custom_option")]
        model = Gtk.StringList.new(options)
        combo = Adw.ComboRow(title=i18n.t("prefs.ui_scale"), model=model)

        # Adw.EntryRow en vez de un SpinRow: es un campo de texto sin
        # botones +/-, tal y como se pidió; solo se puede escribir el número
        # o elegir un valor del desplegable de arriba.
        custom_row = Adw.EntryRow(title=i18n.t("prefs.ui_scale_custom"))
        custom_row.set_input_purpose(Gtk.InputPurpose.NUMBER)
        custom_row.set_text(str(saved_scale))

        revealer = Gtk.Revealer()
        revealer.set_child(custom_row)
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        is_preset = saved_scale in SCALE_PRESETS
        combo.set_selected(SCALE_PRESETS.index(saved_scale) if is_preset else len(SCALE_PRESETS))
        revealer.set_reveal_child(not is_preset)

        def on_combo_changed(combo: Adw.ComboRow, _pspec) -> None:
            index = combo.get_selected()
            if index < len(SCALE_PRESETS):
                self._pending_scale = SCALE_PRESETS[index]
                revealer.set_reveal_child(False)
            else:
                revealer.set_reveal_child(True)
                self._pending_scale = _parse_percent(custom_row.get_text(), self._pending_scale)

        def on_custom_changed(row: Adw.EntryRow) -> None:
            self._pending_scale = _parse_percent(row.get_text(), self._pending_scale)

        combo.connect("notify::selected", on_combo_changed)
        custom_row.connect("changed", on_custom_changed)
        return combo, custom_row, revealer

    def _build_action_bar(self) -> Gtk.Widget:
        bar = Gtk.ActionBar()

        btn_cancel = Gtk.Button(label=i18n.t("action.cancel"))
        btn_cancel.connect("clicked", lambda _b: self.close())
        bar.pack_start(btn_cancel)

        btn_save = Gtk.Button(label=i18n.t("prefs.save"))
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", self._on_save_clicked)
        bar.pack_end(btn_save)

        return bar

    def _on_save_clicked(self, _button) -> None:
        i18n.set_language(self._pending_language)
        cfg = config.load_config()
        cfg["ui_scale"] = self._pending_scale
        cfg["theme"] = self._pending_theme
        cfg["acoustid_api_key"] = self._pending_acoustid_key
        config.save_config(cfg)
        apply_ui_scale(self._pending_scale)
        apply_theme(self._pending_theme)
        self.close()
