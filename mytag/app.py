"""Punto de entrada de la aplicación MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

from .ui.main_window import MainWindow

APP_ID = "com.maestebanc.MyTag"


class MyTagApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window: MainWindow | None = None
        self.connect("activate", self._on_activate)

    def _on_activate(self, app: Adw.Application) -> None:
        if self.window is None:
            self.window = MainWindow(app)
        self.window.present()


def main() -> int:
    app = MyTagApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
