"""Ventana de atajos de teclado."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from .. import i18n

# (clave i18n, combinación de teclas en formato Gtk.accelerator)
SHORTCUTS = [
    ("shortcuts.open_files", "<Control>o"),
    ("shortcuts.save", "<Control>s"),
    ("shortcuts.toggle_search", "<Control>f"),
    ("shortcuts.remove_selected", "Delete"),
    ("shortcuts.preferences", "<Control>comma"),
    ("shortcuts.shortcuts_window", "<Control>question"),
    ("shortcuts.quit", "<Control>q"),
]


class ShortcutsDialog(Adw.Dialog):
    __gtype_name__ = "MyTagShortcutsDialog"

    def __init__(self):
        super().__init__()
        self.set_title(i18n.t("shortcuts.title"))
        self.set_content_width(420)
        self.set_content_height(440)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("shortcuts.title")))
        toolbar_view.add_top_bar(header)

        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title=i18n.t("shortcuts.group_general"))
        for label_key, accel in SHORTCUTS:
            row = Adw.ActionRow(title=i18n.t(label_key))
            shortcut_label = Gtk.ShortcutLabel(accelerator=accel)
            shortcut_label.set_valign(Gtk.Align.CENTER)
            row.add_suffix(shortcut_label)
            group.add(row)
        page.add(group)

        toolbar_view.set_content(page)
        self.set_child(toolbar_view)
