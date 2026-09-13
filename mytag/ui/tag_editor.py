"""Panel de edición de etiquetas, con soporte para edición múltiple."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..constants import TAG_FIELDS

MULTIPLE_VALUES_PLACEHOLDER = "‹valores distintos›"


class TagEditor(QWidget):
    changesRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
        self._touched: set[str] = set()
        self._loading = False
        self._edits: dict[str, QLineEdit] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        form = QFormLayout()
        form.setSpacing(10)
        for key, label in TAG_FIELDS:
            edit = QLineEdit()
            edit.textEdited.connect(lambda _text, k=key: self._touched.add(k))
            self._edits[key] = edit
            form.addRow(QLabel(label + ":"), edit)
        outer.addLayout(form)

        self.status_label = QLabel("Selecciona uno o varios archivos FLAC en la tabla.")
        self.status_label.setObjectName("editorStatus")
        outer.addWidget(self.status_label)

        self.apply_button = QPushButton("Aplicar cambios a los temas seleccionados")
        self.apply_button.setObjectName("primaryButton")
        self.apply_button.clicked.connect(self._on_apply)
        outer.addWidget(self.apply_button)
        outer.addStretch()

        self.set_tracks([])

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._touched.clear()
        self._loading = True
        enabled = bool(tracks)
        for key, edit in self._edits.items():
            edit.setEnabled(enabled)
            if not tracks:
                edit.clear()
                edit.setPlaceholderText("")
                continue
            values = {t.get_tag(key) for t in tracks}
            if len(values) == 1:
                edit.setText(next(iter(values)))
                edit.setPlaceholderText("")
            else:
                edit.clear()
                edit.setPlaceholderText(MULTIPLE_VALUES_PLACEHOLDER)
        self._loading = False
        self.apply_button.setEnabled(enabled)

        if not tracks:
            self.status_label.setText("Selecciona uno o varios archivos FLAC en la tabla.")
        elif len(tracks) == 1:
            self.status_label.setText(f"Editando: {tracks[0].filename}")
        else:
            self.status_label.setText(f"Editando {len(tracks)} temas a la vez")

    def _on_apply(self) -> None:
        if not self._tracks or not self._touched:
            return
        changes = {key: self._edits[key].text() for key in self._touched}
        self.changesRequested.emit(changes)
        self._touched.clear()
