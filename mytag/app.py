"""Punto de entrada de la aplicación MyTag."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow

# Solo ajustes de espaciado/forma: los colores se dejan en manos del tema
# nativo de la plataforma (en Omarchy, Qt hereda el tema GTK/Adwaita activo
# vía QT_QPA_PLATFORMTHEME=gtk3, igual que Nautilus). Usar `palette(...)`
# en vez de colores fijos hace que esto siga funcionando en claro y oscuro.
STYLESHEET = """
QToolBar {
    padding: 6px;
    spacing: 6px;
}
QToolBar QToolButton {
    padding: 6px 10px;
    border-radius: 6px;
}
QToolBar QToolButton:hover {
    background-color: palette(midlight);
}
QTableWidget {
    border-radius: 6px;
}
QHeaderView::section {
    padding: 6px;
    font-weight: 600;
}
QLineEdit {
    border-radius: 6px;
    padding: 5px 8px;
}
QPushButton {
    border-radius: 6px;
    padding: 7px 12px;
}
QPushButton#primaryButton {
    background-color: palette(highlight);
    color: palette(highlighted-text);
    border: none;
    font-weight: 600;
    padding: 8px 12px;
}
QLabel#coverPreview {
    border: 1px dashed palette(mid);
    border-radius: 8px;
}
QLabel#coverInfo {
    color: palette(mid);
    font-size: 11px;
}
QLabel#editorStatus {
    color: palette(mid);
    font-style: italic;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MyTag")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
