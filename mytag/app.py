"""Punto de entrada de la aplicación MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

from .ui.main_window import MainWindow

APP_ID = "com.maestebanc.MyTag"

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
"""


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
            self._load_extra_css()
            self.window = MainWindow(app)
        self.window.present()

    @staticmethod
    def _load_extra_css() -> None:
        provider = Gtk.CssProvider()
        provider.load_from_string(EXTRA_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def main() -> int:
    app = MyTagApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
