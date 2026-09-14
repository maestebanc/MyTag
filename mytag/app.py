"""Punto de entrada de la aplicación MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from . import config
from .ui.main_window import MainWindow
from .ui.style import APP_ID, apply_ui_scale, load_extra_css, register_icon_theme


class MyTagApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        # Omarchy fija gtk-application-prefer-dark-theme=1 en el settings.ini
        # global de GTK, una propiedad heredada de GTK3 que libadwaita ya no
        # usa (avisa por consola si la ve activa). El tema oscuro real sigue
        # detectándose bien a través de Adw.StyleManager, así que aquí solo
        # la desactivamos para evitar el aviso, sin afectar al aspecto.
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", False)
        self.window: MainWindow | None = None
        self.connect("activate", self._on_activate)

    def _on_activate(self, app: Adw.Application) -> None:
        if self.window is None:
            register_icon_theme()
            Gtk.Window.set_default_icon_name(APP_ID)
            load_extra_css()
            apply_ui_scale(config.load_config().get("ui_scale", 100))
            self.window = MainWindow(app)
        self.window.present()


def main() -> int:
    app = MyTagApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
