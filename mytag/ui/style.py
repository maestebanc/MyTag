"""Utilidades de estilo compartidas: CSS extra, icono y escala de interfaz."""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from .. import config

THEMES = {
    "system": Adw.ColorScheme.DEFAULT,
    "light": Adw.ColorScheme.FORCE_LIGHT,
    "dark": Adw.ColorScheme.FORCE_DARK,
}


def apply_theme(theme: str) -> None:
    scheme = THEMES.get(theme, Adw.ColorScheme.DEFAULT)
    Adw.StyleManager.get_default().set_color_scheme(scheme)

APP_ID = "com.maestebanc.MyTag"

# Cuando se ejecuta desde el propio repositorio (./run.sh) los iconos no
# están instalados en el tema de iconos del sistema; en un paquete
# (deb/rpm/flatpak) sí lo estarán en /usr/share/icons, donde GTK ya busca
# por defecto, y esta ruta extra simplemente no existirá.
_REPO_ICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "icons"
)


def register_icon_theme() -> None:
    if os.path.isdir(_REPO_ICON_DIR):
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(_REPO_ICON_DIR)

# Un pequeño toque de profundidad: los paneles "elevados" (.card, listas en
# caja) se tiñen con una fracción del color de primer plano del tema activo,
# en vez de un color fijo. Así se ven ligeramente distintos del fondo tanto
# en temas claros como oscuros, sin romper la integración con el tema nativo.
EXTRA_CSS = """
.card,
list.boxed-list {
    background-color: alpha(@window_fg_color, 0.05);
}
list.boxed-list > row {
    background-color: transparent;
}
.drop-highlight {
    outline: 3px solid @accent_bg_color;
    outline-offset: -3px;
    border-radius: 8px;
}
"""


def load_extra_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_string(EXTRA_CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def _base_dpi() -> int:
    """DPI (en 1024os) que corresponde al 100%: el que tenía el sistema la
    primera vez que se ejecutó MyTag, capturado antes de aplicar ningún
    ajuste propio. Se guarda para que 100% siga significando siempre lo
    mismo, aunque cambie el DPI del sistema más adelante."""
    cfg = config.load_config()
    if "base_dpi" not in cfg:
        cfg["base_dpi"] = Gtk.Settings.get_default().get_property("gtk-xft-dpi")
        config.save_config(cfg)
    return cfg["base_dpi"]


def apply_ui_scale(percent: int) -> None:
    dpi_1024 = int(_base_dpi() * percent / 100)
    Gtk.Settings.get_default().set_property("gtk-xft-dpi", dpi_1024)
