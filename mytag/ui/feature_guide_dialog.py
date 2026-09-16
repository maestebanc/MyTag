"""Diálogo visual con la guía estructurada de funciones de MyTag."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from .. import i18n


class FeatureGuideDialog(Adw.Dialog):
    __gtype_name__ = "MyTagFeatureGuideDialog"

    def __init__(self):
        super().__init__()
        self.set_title(i18n.t("guide.title"))
        self.set_content_width(680)
        self.set_content_height(600)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("guide.title"), subtitle=i18n.t("guide.subtitle")))
        toolbar_view.add_top_bar(header)

        page = Adw.PreferencesPage()
        page.set_vexpand(True)

        features = [
            (
                "audio-card-symbolic",
                "guide.fingerprint_title",
                "guide.fingerprint_desc",
            ),
            (
                "image-x-generic-symbolic",
                "guide.cover_title",
                "guide.cover_desc",
            ),
            (
                "document-edit-symbolic",
                "guide.tags_title",
                "guide.tags_desc",
            ),
            (
                "edit-find-replace-symbolic",
                "guide.renaming_title",
                "guide.renaming_desc",
            ),
            (
                "emblem-ok-symbolic",
                "guide.integrity_title",
                "guide.integrity_desc",
            ),
            (
                "input-mouse-symbolic",
                "guide.context_title",
                "guide.context_desc",
            ),
        ]

        group = Adw.PreferencesGroup()
        for icon_name, title_key, desc_key in features:
            row = Adw.ActionRow()
            row.set_title(i18n.t(title_key))
            row.set_subtitle(i18n.t(desc_key))
            row.set_subtitle_lines(0)  # Permitir salto de línea completo sin truncar

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(24)
            icon.add_css_class("accent")
            icon.set_valign(Gtk.Align.START)
            icon.set_margin_top(4)
            row.add_prefix(icon)

            group.add(row)

        page.add(group)
        toolbar_view.set_content(page)

        # Botón inferior de cerrar
        action_bar = Gtk.ActionBar()
        btn_close = Gtk.Button(label=i18n.t("action.close") if i18n.t("action.close") != "action.close" else "Cerrar")
        btn_close.set_halign(Gtk.Align.CENTER)
        btn_close.add_css_class("suggested-action")
        btn_close.connect("clicked", lambda _b: self.close())
        action_bar.set_center_widget(btn_close)
        toolbar_view.add_bottom_bar(action_bar)

        self.set_child(toolbar_view)
