"""Utilidades de estilo compartidas: CSS extra, icono y escala de interfaz."""
from __future__ import annotations

import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

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

def _get_icon_dirs() -> list[str]:
    dirs: list[str] = []
    # Entorno congelado de PyInstaller (sys._MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dirs.append(os.path.join(sys._MEIPASS, "data", "icons"))
        dirs.append(os.path.join(sys._MEIPASS, "mytag", "resources", "icons"))
    # Árbol de directorios de desarrollo / repositorio
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dirs.append(os.path.join(root_dir, "data", "icons"))
    internal_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons")
    dirs.append(internal_dir)
    return [d for d in dirs if os.path.isdir(d)]

_icon_theme_registered: bool = False


def register_icon_theme() -> None:
    global _icon_theme_registered
    if _icon_theme_registered:
        return
    display = Gdk.Display.get_default()
    if not display:
        return
    theme = Gtk.IconTheme.get_for_display(display)
    for icon_dir in _get_icon_dirs():
        theme.add_search_path(icon_dir)
    _icon_theme_registered = True

# Estilo visual refinado para GNOME / Libadwaita
EXTRA_CSS = """
/* Paneles elevados y listas en caja */
.card,
list.boxed-list {
    background-color: alpha(@window_fg_color, 0.04);
    border: 1px solid alpha(@window_fg_color, 0.07);
    border-radius: 12px;
}

list.boxed-list > row {
    background-color: transparent;
}

/* Marco de la carátula: profundidad de funda física y esquinas redondeadas */
.album-cover-frame {
    border-radius: 12px;
    border: 1px solid alpha(@window_fg_color, 0.12);
    box-shadow: 0 10px 28px alpha(black, 0.22), 0 3px 8px alpha(black, 0.12);
    background-color: alpha(@window_fg_color, 0.03);
}

/* Espacio reservado para carátula vacía */
.album-cover-placeholder {
    border-radius: 12px;
    border: 2px dashed alpha(@window_fg_color, 0.16);
    background-color: alpha(@window_fg_color, 0.02);
    padding: 16px;
    transition: all 200ms ease;
}

.album-cover-placeholder:hover {
    border-color: alpha(@accent_bg_color, 0.45);
    background-color: alpha(@accent_bg_color, 0.04);
}

/* Botón flotante ⋮ sobre la carátula */
.cover-overlay-btn {
    background-color: alpha(@window_bg_color, 0.82);
    box-shadow: 0 2px 8px alpha(black, 0.25);
}

/* Píldora de dimensiones de la portada */
.dims-pill {
    padding: 2px 0;
}

.dims-pill entry {
    min-width: 44px;
    min-height: 24px;
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 0.88em;
    font-variant-numeric: tabular-nums;
    background-color: alpha(@window_fg_color, 0.05);
    border: 1px solid alpha(@window_fg_color, 0.08);
}

.dims-pill entry:focus {
    border-color: @accent_bg_color;
}

/* Etiqueta discreta de tamaño bajo la portada (editable inline) */
.cover-size-label {
    font-size: 0.78em;
    font-variant-numeric: tabular-nums;
    opacity: 0.75;
}

editablelabel.cover-size-label {
    min-height: 20px;
    padding: 1px 6px;
    border-radius: 4px;
    transition: all 150ms ease;
}

editablelabel.cover-size-label:hover {
    opacity: 1;
    background-color: alpha(@window_fg_color, 0.06);
}

editablelabel.cover-size-label text {
    font-size: 0.78em;
    font-variant-numeric: tabular-nums;
    padding: 1px 4px;
    margin: 0;
    min-height: 0;
    background-color: alpha(@window_fg_color, 0.08);
    border: 1px solid @accent_bg_color;
    border-radius: 4px;
    color: @window_fg_color;
}

/* Badges / Píldoras de estado y contador */
.pill-badge {
    border-radius: 9999px;
    padding: 2px 10px;
    font-size: 0.85em;
    font-weight: 600;
    background-color: alpha(@accent_bg_color, 0.12);
    color: @accent_color;
}

.pill-badge.dim {
    background-color: alpha(@window_fg_color, 0.07);
    color: alpha(@window_fg_color, 0.75);
}

/* Banner de estado en el editor de etiquetas */
.editor-status-banner {
    padding: 6px 10px;
    border-radius: 8px;
    background-color: alpha(@window_fg_color, 0.03);
}

/* Editor de etiquetas compacto (sin necesidad de scroll en ventana estándar) */
.tag-editor-list > row {
    min-height: 38px;
    padding-top: 0px;
    padding-bottom: 0px;
}

.tag-editor-list > row > box.header {
    min-height: 38px;
    padding-top: 2px;
    padding-bottom: 2px;
}

/* Pie de la lista de pistas (barra de estado compacta) */
.track-list-footer {
    padding: 6px 10px;
    border-top: 1px solid alpha(@window_fg_color, 0.06);
    background-color: alpha(@window_fg_color, 0.02);
}

/* Columna de números de pista: números tabulares */
.track-number-label {
    font-variant-numeric: tabular-nums;
    opacity: 0.65;
}

/* Icono de advertencia en pistas incompletas */
.track-warning-icon {
    color: @warning_color;
}

/* Icono de error en pistas corruptas o con fallo de integridad */
.track-error-icon {
    color: @error_color;
}

/* Resaltado durante arrastrar y soltar (Drag & Drop) */
.drop-highlight {
    outline: 2px solid @accent_bg_color;
    outline-offset: -2px;
    border-radius: 12px;
    background-color: alpha(@accent_bg_color, 0.08);
    transition: all 180ms ease-in-out;
}

/* Tarjetas de candidatos en el diálogo de búsqueda de portada */
.candidate-card {
    border-radius: 10px;
    background-color: alpha(@window_fg_color, 0.04);
    border: 1px solid alpha(@window_fg_color, 0.08);
    padding: 8px;
    transition: all 150ms ease;
}

.candidate-card:hover {
    background-color: alpha(@window_fg_color, 0.08);
    box-shadow: 0 4px 12px alpha(black, 0.16);
}

flowboxchild:selected .candidate-card {
    outline: 2px solid @accent_bg_color;
    background-color: alpha(@accent_bg_color, 0.12);
}

.candidate-thumb {
    border-radius: 6px;
    border: 1px solid alpha(@window_fg_color, 0.08);
}

/* Botones de tokens en diálogo de renombrado */
.token-button {
    font-family: monospace;
    font-size: 0.85em;
    padding: 2px 8px;
    border-radius: 6px;
}

/* Tabla de pistas compacta y alineada con aplicaciones de escritorio como Nautilus */
.track-table row {
    min-height: 32px;
}

.track-table columnviewcell {
    padding: 2px 4px;
}

/* Reordenación de columnas mediante arrastrar y soltar (Drag and Drop) */
.track-table header button.dnd-dragging {
    opacity: 0.55;
    background-color: alpha(@accent_bg_color, 0.2);
}

.track-table header button.dnd-target-left {
    box-shadow: inset 3px 0 0 0 @accent_bg_color;
    background-color: alpha(@accent_bg_color, 0.08);
}

.track-table header button.dnd-target-right {
    box-shadow: inset -3px 0 0 0 @accent_bg_color;
    background-color: alpha(@accent_bg_color, 0.08);
}
"""


def load_extra_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_string(EXTRA_CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


DEFAULT_DPI_1024 = 98304  # 96 DPI * 1024 (estándar de fuentes en X11/Wayland)


_gnome_settings: Gio.Settings | None = None
_gnome_settings_connected: bool = False
_current_ui_scale_percent: int = 100


def _get_linux_system_font_scale() -> float:
    """Obtiene el factor de escala de tipografía configurado en el sistema (GNOME/Linux).

    Por ejemplo, si en GNOME Tweaks o Accesibilidad la escala está al 1.33 o 1.25,
    devuelve 1.33. Si no está configurado o no está disponible, devuelve 1.0.
    """
    global _gnome_settings, _gnome_settings_connected
    if _gnome_settings is None:
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source and source.lookup("org.gnome.desktop.interface", True):
                _gnome_settings = Gio.Settings.new("org.gnome.desktop.interface")
        except Exception:
            _gnome_settings = None

    if _gnome_settings is not None:
        if not _gnome_settings_connected:
            try:
                _gnome_settings.connect("changed::text-scaling-factor", _on_system_text_scaling_changed)
                _gnome_settings_connected = True
            except Exception:
                pass
        try:
            factor = _gnome_settings.get_double("text-scaling-factor")
            if factor and factor > 0:
                return float(factor)
        except Exception:
            pass

    return 1.0


def _on_system_text_scaling_changed(_settings: Gio.Settings, _key: str) -> None:
    """Si el usuario cambia el escalado de fuentes en GNOME mientras MyTag está abierto,
    recalcula y reaplica la escala proporcional en tiempo real."""
    apply_ui_scale(_current_ui_scale_percent)


def apply_ui_scale(percent: int) -> None:
    global _current_ui_scale_percent
    _current_ui_scale_percent = percent

    settings = Gtk.Settings.get_default()
    if settings is None:
        return

    # En Linux/GNOME, obtenemos el factor de escala de fuentes del sistema (ej. 1.33).
    # Al 100% de escala en MyTag, la tipografía coincide exactamente con la escala de GNOME.
    # Por encima o por debajo (110%, 125%, 90%), escala proporcionalmente a partir de esa base.
    font_scale = _get_linux_system_font_scale()
    base_dpi = 96.0 * font_scale
    dpi_1024 = int(round(base_dpi * 1024 * (percent / 100.0)))
    settings.set_property("gtk-xft-dpi", dpi_1024)


