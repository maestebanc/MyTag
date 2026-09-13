"""Punto de entrada de la aplicación MyTag."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f5f7;
    color: #23262b;
    font-size: 13px;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dcdfe4;
    padding: 6px;
    spacing: 6px;
}
QToolBar QToolButton {
    padding: 6px 10px;
    border-radius: 6px;
}
QToolBar QToolButton:hover {
    background-color: #e7ecff;
}
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #dcdfe4;
    border-radius: 8px;
    gridline-color: #edeff2;
    selection-background-color: #d6e0ff;
    selection-color: #1a1c20;
}
QHeaderView::section {
    background-color: #f0f1f4;
    color: #4a4f57;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #dcdfe4;
    font-weight: 600;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #ccd0d7;
    border-radius: 6px;
    padding: 5px 8px;
}
QLineEdit:focus {
    border: 1px solid #5b7cfa;
}
QLineEdit:disabled {
    background-color: #eceef1;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #ccd0d7;
    border-radius: 6px;
    padding: 7px 12px;
}
QPushButton:hover {
    background-color: #eef1f8;
}
QPushButton:disabled {
    color: #9aa0a8;
}
QPushButton#primaryButton {
    background-color: #5b7cfa;
    border: none;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: #4a6bf0;
}
QLabel#coverPreview {
    background-color: #ffffff;
    border: 1px dashed #ccd0d7;
    border-radius: 8px;
    color: #9aa0a8;
}
QLabel#coverInfo {
    color: #6b7078;
    font-size: 11px;
}
QLabel#editorStatus {
    color: #6b7078;
    font-style: italic;
}
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #dcdfe4;
}
QSplitter::handle {
    background-color: #dcdfe4;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MyTag")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
