"""Pantalla de preferencias: idioma y escala de la interfaz."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from .. import config, i18n
from .style import apply_ui_scale


class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "MyTagPreferencesDialog"

    def __init__(self):
        super().__init__()
        self.set_title(i18n.t("prefs.title"))
        self.set_content_width(480)

        page = Adw.PreferencesPage()

        general_group = Adw.PreferencesGroup(title=i18n.t("prefs.general_group"))
        general_group.add(self._build_language_row())
        page.add(general_group)

        appearance_group = Adw.PreferencesGroup(title=i18n.t("prefs.appearance_group"))
        appearance_group.add(self._build_scale_row())
        page.add(appearance_group)

        self.add(page)

    def _build_language_row(self) -> Adw.ComboRow:
        codes = i18n.SUPPORTED_LANGUAGES
        names = Gtk.StringList.new([i18n.LANGUAGE_NAMES[code] for code in codes])
        row = Adw.ComboRow(title=i18n.t("prefs.language"), model=names)
        row.set_subtitle(i18n.t("prefs.language_restart_note"))
        current = i18n.get_language()
        row.set_selected(codes.index(current) if current in codes else 0)
        row.connect("notify::selected", self._on_language_changed, codes)
        return row

    @staticmethod
    def _on_language_changed(row: Adw.ComboRow, _pspec, codes: list[str]) -> None:
        index = row.get_selected()
        if 0 <= index < len(codes):
            i18n.set_language(codes[index])

    def _build_scale_row(self) -> Adw.SpinRow:
        current_scale = config.load_config().get("ui_scale", 100)
        adjustment = Gtk.Adjustment(value=current_scale, lower=50, upper=200, step_increment=10, page_increment=25)
        row = Adw.SpinRow(title=i18n.t("prefs.ui_scale"), adjustment=adjustment)
        row.set_digits(0)
        row.set_numeric(True)
        row.connect("notify::value", self._on_scale_changed)
        return row

    @staticmethod
    def _on_scale_changed(row: Adw.SpinRow, _pspec) -> None:
        percent = int(row.get_value())
        apply_ui_scale(percent)
        cfg = config.load_config()
        cfg["ui_scale"] = percent
        config.save_config(cfg)
