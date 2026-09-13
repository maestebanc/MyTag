"""Ventana principal de MyTag."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QWidget,
)

from ..audio_track import AudioTrack
from ..constants import FLAC_FILE_FILTER, TAG_FIELDS
from .cover_panel import CoverPanel
from .tag_editor import TagEditor

COLUMNS = [("__file__", "Archivo")] + TAG_FIELDS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyTag")
        self.resize(1150, 650)
        self.setAcceptDrops(True)

        self.tracks: list[AudioTrack] = []

        self._build_toolbar()
        self._build_central_widget()
        self.statusBar().showMessage("Listo. Abre archivos o una carpeta con FLAC para empezar.")

    # ---------- construcción de la interfaz ----------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        act_open_files = QAction("Abrir archivos…", self)
        act_open_files.setShortcut(QKeySequence.Open)
        act_open_files.triggered.connect(self.open_files_dialog)
        toolbar.addAction(act_open_files)

        act_open_folder = QAction("Abrir carpeta…", self)
        act_open_folder.triggered.connect(self.open_folder_dialog)
        toolbar.addAction(act_open_folder)

        toolbar.addSeparator()

        act_save = QAction("Guardar cambios", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.save_all)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        act_remove = QAction("Quitar de la lista", self)
        act_remove.triggered.connect(self.remove_selected_rows)
        toolbar.addAction(act_remove)

    def _build_central_widget(self) -> None:
        splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels([label for _, label in COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.table)

        side_panel = QWidget()
        side_layout = QHBoxLayout(side_panel)

        self.cover_panel = CoverPanel()
        self.cover_panel.coverChangeRequested.connect(self._on_cover_change_requested)
        self.cover_panel.coverRemoveRequested.connect(self._on_cover_remove_requested)
        side_layout.addWidget(self.cover_panel)

        self.tag_editor = TagEditor()
        self.tag_editor.changesRequested.connect(self._on_tag_changes_requested)
        side_layout.addWidget(self.tag_editor, stretch=1)

        splitter.addWidget(side_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.setCentralWidget(splitter)

    # ---------- carga de archivos ----------

    def open_files_dialog(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Abrir archivos FLAC", "", FLAC_FILE_FILTER)
        if paths:
            self.add_paths(paths)

    def open_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta")
        if not folder:
            return
        found = []
        for root, _dirs, files in os.walk(folder):
            for name in sorted(files):
                if name.lower().endswith(".flac"):
                    found.append(os.path.join(root, name))
        if not found:
            QMessageBox.information(self, "MyTag", "No se encontraron archivos FLAC en esa carpeta.")
            return
        self.add_paths(found)

    def add_paths(self, paths: list[str]) -> None:
        existing = {t.path for t in self.tracks}
        errors = []
        added = 0
        for path in paths:
            if path in existing:
                continue
            try:
                track = AudioTrack(path)
            except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier fallo de mutagen
                errors.append(f"{os.path.basename(path)}: {exc}")
                continue
            self.tracks.append(track)
            self._append_row(track)
            added += 1

        if errors:
            QMessageBox.warning(
                self,
                "Algunos archivos no se pudieron cargar",
                "\n".join(errors),
            )
        self.statusBar().showMessage(f"{added} archivo(s) añadido(s). Total: {len(self.tracks)}.")

    def _append_row(self, track: AudioTrack) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._fill_row(row, track)

    def _fill_row(self, row: int, track: AudioTrack) -> None:
        self.table.setItem(row, 0, QTableWidgetItem(track.filename))
        for col, (key, _label) in enumerate(TAG_FIELDS, start=1):
            self.table.setItem(row, col, QTableWidgetItem(track.get_tag(key)))

    def _refresh_row_for_track(self, track: AudioTrack) -> None:
        row = self.tracks.index(track)
        self._fill_row(row, track)

    # ---------- selección ----------

    def _selected_tracks(self) -> list[AudioTrack]:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        return [self.tracks[r] for r in rows]

    def _on_selection_changed(self) -> None:
        tracks = self._selected_tracks()
        self.tag_editor.set_tracks(tracks)
        self.cover_panel.set_tracks(tracks)

    # ---------- aplicar cambios ----------

    def _on_tag_changes_requested(self, changes: dict) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            for key, value in changes.items():
                track.set_tag(key, value)
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(tracks)
        self._update_title()
        self.statusBar().showMessage(
            f"Cambios aplicados a {len(tracks)} tema(s). Recuerda guardar."
        )

    def _on_cover_change_requested(self, data: bytes, mime: str) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.set_cover_bytes(data, mime)
        self.cover_panel.set_tracks(tracks)
        self._update_title()
        self.statusBar().showMessage(
            f"Portada aplicada a {len(tracks)} tema(s). Recuerda guardar."
        )

    def _on_cover_remove_requested(self) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.remove_cover()
        self.cover_panel.set_tracks(tracks)
        self._update_title()
        self.statusBar().showMessage(f"Portada eliminada de {len(tracks)} tema(s). Recuerda guardar.")

    def remove_selected_rows(self) -> None:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            del self.tracks[row]
            self.table.removeRow(row)
        self.statusBar().showMessage(f"Total: {len(self.tracks)} archivo(s) en la lista.")

    # ---------- guardar ----------

    def save_all(self) -> None:
        # Confirma automáticamente cualquier edición de tags o portada que se
        # vea en pantalla pero que el usuario no haya pulsado "Aplicar" para
        # ella, para que "Guardar cambios" nunca se quede sin efecto.
        if self.tag_editor.has_pending_changes():
            self.tag_editor.apply_pending()
        if self.cover_panel.has_pending_changes():
            self.cover_panel.apply_pending()

        dirty = [t for t in self.tracks if t.is_dirty]
        if not dirty:
            self.statusBar().showMessage("No hay cambios pendientes de guardar.")
            return
        errors = []
        for track in dirty:
            try:
                track.save()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{track.filename}: {exc}")
        if errors:
            QMessageBox.critical(self, "Error al guardar", "\n".join(errors))
        self._update_title()
        self.statusBar().showMessage(f"Guardado completado ({len(dirty) - len(errors)} archivo(s)).")

    def _has_unsaved_changes(self) -> bool:
        return any(t.is_dirty for t in self.tracks)

    def _update_title(self) -> None:
        suffix = " — cambios sin guardar" if self._has_unsaved_changes() else ""
        self.setWindowTitle(f"MyTag{suffix}")

    # ---------- arrastrar y soltar ----------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.isdir(local_path):
                for root, _dirs, files in os.walk(local_path):
                    for name in sorted(files):
                        if name.lower().endswith(".flac"):
                            paths.append(os.path.join(root, name))
            elif local_path.lower().endswith(".flac"):
                paths.append(local_path)
        if paths:
            self.add_paths(paths)

    # ---------- cierre ----------

    def closeEvent(self, event) -> None:
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Quieres salir sin guardarlos?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()
