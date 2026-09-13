"""Panel de previsualización y edición de la portada del álbum."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..constants import IMAGE_FILE_FILTER
from ..cover_utils import read_image_file, resize_image_bytes

PREVIEW_SIZE = 260


class CoverPanel(QWidget):
    coverChangeRequested = Signal(bytes, str)
    coverRemoveRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
        self._pending_data: bytes | None = None
        self._pending_mime: str = "image/jpeg"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview = QLabel("Sin portada")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)
        self.preview.setFrameShape(QFrame.StyledPanel)
        self.preview.setObjectName("coverPreview")
        self.preview.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(self.preview)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setObjectName("coverInfo")
        layout.addWidget(self.info_label)

        btn_select = QPushButton("Seleccionar imagen…")
        btn_select.clicked.connect(self._on_select_image)

        btn_resize = QPushButton("Redimensionar a 500 × 500")
        btn_resize.clicked.connect(self._on_resize)

        btn_apply = QPushButton("Aplicar a los temas seleccionados")
        btn_apply.setObjectName("primaryButton")
        btn_apply.clicked.connect(self.apply_pending)

        btn_remove = QPushButton("Quitar portada")
        btn_remove.clicked.connect(self._on_remove)

        for btn in (btn_select, btn_resize, btn_apply, btn_remove):
            layout.addWidget(btn)

        layout.addStretch()
        self._refresh_preview()

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._pending_data = None
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self._pending_data is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(self._pending_data)
            self._set_pixmap(pixmap)
            w, h = self._pending_wh()
            self.info_label.setText(f"Pendiente de aplicar · {w}×{h}px")
            return

        if not self._tracks:
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Sin temas cargados")
            self.info_label.setText("")
            return

        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            data = next(iter(covers))
            if data is None:
                self.preview.setPixmap(QPixmap())
                self.preview.setText("Sin portada")
                self.info_label.setText("")
            else:
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                self._set_pixmap(pixmap)
                self.info_label.setText(f"{pixmap.width()}×{pixmap.height()}px")
        else:
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Varias portadas distintas")
            self.info_label.setText(f"{len(self._tracks)} temas seleccionados")

    def _pending_wh(self) -> tuple[int, int]:
        pixmap = QPixmap()
        pixmap.loadFromData(self._pending_data)
        return pixmap.width(), pixmap.height()

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            self.preview.setText("Imagen no válida")
            return
        scaled = pixmap.scaled(
            PREVIEW_SIZE, PREVIEW_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview.setPixmap(scaled)

    def _on_select_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar portada", "", IMAGE_FILE_FILTER)
        if not path:
            return
        data, mime = read_image_file(path)
        self._pending_data = data
        self._pending_mime = mime
        self._refresh_preview()

    def _on_resize(self) -> None:
        source = self._pending_data
        if source is None:
            if len(self._tracks) == 1:
                source = self._tracks[0].get_cover_bytes()
        if source is None:
            return
        data, mime = resize_image_bytes(source)
        self._pending_data = data
        self._pending_mime = mime
        self._refresh_preview()

    def has_pending_changes(self) -> bool:
        return bool(self._pending_data is not None and self._tracks)

    def apply_pending(self) -> None:
        if not self.has_pending_changes():
            return
        self.coverChangeRequested.emit(self._pending_data, self._pending_mime)
        self._pending_data = None
        self._refresh_preview()

    def _on_remove(self) -> None:
        if not self._tracks:
            return
        self._pending_data = None
        self.coverRemoveRequested.emit()
        self._refresh_preview()
