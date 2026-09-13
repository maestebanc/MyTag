"""Ventana principal de MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango

from ..audio_track import AudioTrack
from ..constants import TAG_FIELDS
from .cover_panel import CoverPanel
from .tag_editor import TagEditor
from .track_item import TrackItem

COLUMNS = [("__file__", "Archivo")] + TAG_FIELDS


def _make_column(title: str, prop_name: str, expand: bool = False) -> Gtk.ColumnViewColumn:
    factory = Gtk.SignalListItemFactory()

    def on_setup(_factory, list_item: Gtk.ListItem) -> None:
        label = Gtk.Label(xalign=0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_margin_start(6)
        label.set_margin_end(6)
        list_item.set_child(label)

    def on_bind(_factory, list_item: Gtk.ListItem) -> None:
        label = list_item.get_child()
        item = list_item.get_item()

        def update(*_args) -> None:
            label.set_text(item.get_property(prop_name) or "")

        update()
        list_item.mytag_handler_id = item.connect(f"notify::{prop_name}", update)
        list_item.mytag_handler_item = item

    def on_unbind(_factory, list_item: Gtk.ListItem) -> None:
        item = getattr(list_item, "mytag_handler_item", None)
        handler_id = getattr(list_item, "mytag_handler_id", None)
        if item is not None and handler_id is not None:
            item.disconnect(handler_id)

    factory.connect("setup", on_setup)
    factory.connect("bind", on_bind)
    factory.connect("unbind", on_unbind)

    column = Gtk.ColumnViewColumn(title=title, factory=factory)
    if expand:
        column.set_expand(True)
    column.set_resizable(True)
    return column


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="MyTag")
        self.set_default_size(1150, 650)

        self.tracks: list[AudioTrack] = []
        self.list_store = Gio.ListStore(item_type=TrackItem)
        self.selection_model = Gtk.MultiSelection(model=self.list_store)
        self.selection_model.connect("selection-changed", self._on_selection_changed)

        self.toast_overlay = Adw.ToastOverlay()
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(self._build_headerbar())
        toolbar_view.set_content(self._build_body())
        self.toast_overlay.set_child(toolbar_view)
        self.set_content(self.toast_overlay)

        self._setup_drop_target()
        self.connect("close-request", self._on_close_request)
        self._force_close = False

        self._toast("Abre archivos o una carpeta con FLAC para empezar.")

    # ---------- construcción de la interfaz ----------

    def _build_headerbar(self) -> Adw.HeaderBar:
        header = Adw.HeaderBar()

        btn_open_files = Gtk.Button(label="Abrir archivos…")
        btn_open_files.connect("clicked", lambda _b: self.open_files_dialog())
        header.pack_start(btn_open_files)

        btn_open_folder = Gtk.Button(label="Abrir carpeta…")
        btn_open_folder.connect("clicked", lambda _b: self.open_folder_dialog())
        header.pack_start(btn_open_folder)

        btn_remove = Gtk.Button(label="Quitar de la lista")
        btn_remove.connect("clicked", lambda _b: self.remove_selected_rows())
        header.pack_start(btn_remove)

        btn_save = Gtk.Button(label="Guardar cambios")
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", lambda _b: self.save_all())
        header.pack_end(btn_save)

        return header

    def _build_body(self) -> Gtk.Widget:
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.set_position(700)

        self.column_view = Gtk.ColumnView(model=self.selection_model)
        self.column_view.append_column(_make_column("Archivo", "filename", expand=True))
        for key, label in TAG_FIELDS:
            self.column_view.append_column(_make_column(label, key.lower()))

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.column_view)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        paned.set_start_child(scroller)
        paned.set_resize_start_child(True)

        side_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        side_box.set_margin_top(16)
        side_box.set_margin_bottom(16)
        side_box.set_margin_start(16)
        side_box.set_margin_end(16)

        self.cover_panel = CoverPanel()
        self.cover_panel.connect("cover-change-requested", self._on_cover_change_requested)
        self.cover_panel.connect("cover-remove-requested", self._on_cover_remove_requested)
        side_box.append(self.cover_panel)

        self.tag_editor = TagEditor()
        self.tag_editor.set_hexpand(True)
        self.tag_editor.connect("changes-requested", self._on_tag_changes_requested)
        side_box.append(self.tag_editor)

        side_scroller = Gtk.ScrolledWindow()
        side_scroller.set_child(side_box)
        side_scroller.set_hexpand(True)
        paned.set_end_child(side_scroller)
        paned.set_resize_end_child(False)

        return paned

    def _setup_drop_target(self) -> None:
        target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        target.connect("drop", self._on_drop)
        self.column_view.add_controller(target)

        target_files = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        target_files.connect("drop", self._on_drop_filelist)
        self.column_view.add_controller(target_files)

    # ---------- carga de archivos ----------

    def open_files_dialog(self) -> None:
        dialog = Gtk.FileDialog(title="Abrir archivos FLAC")
        filter_flac = Gtk.FileFilter()
        filter_flac.set_name("Archivos FLAC")
        filter_flac.add_pattern("*.flac")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_flac)
        dialog.set_filters(filters)
        dialog.open_multiple(self, None, self._on_open_files_finished)

    def _on_open_files_finished(self, dialog, result) -> None:
        try:
            files = dialog.open_multiple_finish(result)
        except GLib.Error:
            return
        if not files:
            return
        paths = [f.get_path() for f in files if f.get_path()]
        self.add_paths(paths)

    def open_folder_dialog(self) -> None:
        dialog = Gtk.FileDialog(title="Abrir carpeta")
        dialog.select_folder(self, None, self._on_open_folder_finished)

    def _on_open_folder_finished(self, dialog, result) -> None:
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if gfile is None:
            return
        folder = gfile.get_path()
        if not folder:
            return
        found = self._find_flac_files(folder)
        if not found:
            self._show_message("MyTag", "No se encontraron archivos FLAC en esa carpeta.")
            return
        self.add_paths(found)

    @staticmethod
    def _find_flac_files(folder: str) -> list[str]:
        found = []
        for root, _dirs, files in os.walk(folder):
            for name in sorted(files):
                if name.lower().endswith(".flac"):
                    found.append(os.path.join(root, name))
        return found

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
            self.list_store.append(TrackItem(track))
            added += 1

        if errors:
            self._show_message("Algunos archivos no se pudieron cargar", "\n".join(errors))
        self._toast(f"{added} archivo(s) añadido(s). Total: {len(self.tracks)}.")

    def _refresh_row_for_track(self, track: AudioTrack) -> None:
        index = self.tracks.index(track)
        item = self.list_store.get_item(index)
        item.refresh()

    # ---------- selección ----------

    def _selected_tracks(self) -> list[AudioTrack]:
        tracks = []
        n = self.list_store.get_n_items()
        for i in range(n):
            if self.selection_model.is_selected(i):
                tracks.append(self.list_store.get_item(i).track)
        return tracks

    def _on_selection_changed(self, _model, _pos, _n_items) -> None:
        tracks = self._selected_tracks()
        self.tag_editor.set_tracks(tracks)
        self.cover_panel.set_tracks(tracks)

    # ---------- aplicar cambios ----------

    def _on_tag_changes_requested(self, _editor, changes: dict) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            for key, value in changes.items():
                track.set_tag(key, value)
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(tracks)
        self._toast(f"Cambios aplicados a {len(tracks)} tema(s). Recuerda guardar.")

    def _on_cover_change_requested(self, _panel, data: bytes, mime: str) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.set_cover_bytes(data, mime)
        self.cover_panel.set_tracks(tracks)
        self._toast(f"Portada aplicada a {len(tracks)} tema(s). Recuerda guardar.")

    def _on_cover_remove_requested(self, _panel) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.remove_cover()
        self.cover_panel.set_tracks(tracks)
        self._toast(f"Portada eliminada de {len(tracks)} tema(s). Recuerda guardar.")

    def remove_selected_rows(self) -> None:
        indexes = sorted(
            (i for i in range(self.list_store.get_n_items()) if self.selection_model.is_selected(i)),
            reverse=True,
        )
        for i in indexes:
            del self.tracks[i]
            self.list_store.remove(i)
        self._toast(f"Total: {len(self.tracks)} archivo(s) en la lista.")

    # ---------- guardar ----------

    def save_all(self) -> None:
        if self.tag_editor.has_pending_changes():
            self.tag_editor.apply_pending()
        if self.cover_panel.has_pending_changes():
            self.cover_panel.apply_pending()

        dirty = [t for t in self.tracks if t.is_dirty]
        if not dirty:
            self._toast("No hay cambios pendientes de guardar.")
            return
        errors = []
        for track in dirty:
            try:
                track.save()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{track.filename}: {exc}")
        if errors:
            self._show_message("Error al guardar", "\n".join(errors))
        self._toast(f"Guardado completado ({len(dirty) - len(errors)} archivo(s)).")

    def _has_unsaved_changes(self) -> bool:
        return any(t.is_dirty for t in self.tracks)

    # ---------- arrastrar y soltar ----------

    def _on_drop(self, _target, gfile: Gio.File, _x, _y) -> bool:
        return self._handle_dropped_paths([gfile.get_path()] if gfile.get_path() else [])

    def _on_drop_filelist(self, _target, file_list, _x, _y) -> bool:
        paths = [f.get_path() for f in file_list.get_files() if f.get_path()]
        return self._handle_dropped_paths(paths)

    def _handle_dropped_paths(self, dropped: list[str]) -> bool:
        paths = []
        for local_path in dropped:
            if not local_path:
                continue
            if os.path.isdir(local_path):
                paths.extend(self._find_flac_files(local_path))
            elif local_path.lower().endswith(".flac"):
                paths.append(local_path)
        if paths:
            self.add_paths(paths)
            return True
        return False

    # ---------- utilidades de UI ----------

    def _toast(self, text: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast(title=text, timeout=4))

    def _show_message(self, heading: str, body: str) -> None:
        dialog = Adw.AlertDialog(heading=heading, body=body)
        dialog.add_response("ok", "Vale")
        dialog.present(self)

    # ---------- cierre ----------

    def _on_close_request(self, _window) -> bool:
        if self._force_close or not self._has_unsaved_changes():
            return False  # permitir el cierre

        dialog = Adw.AlertDialog(
            heading="Cambios sin guardar",
            body="Hay cambios sin guardar. ¿Quieres salir sin guardarlos?",
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("discard", "Salir sin guardar")
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_close_dialog_response)
        dialog.present(self)
        return True  # bloquear el cierre hasta que el usuario decida

    def _on_close_dialog_response(self, _dialog, response: str) -> None:
        if response == "discard":
            self._force_close = True
            self.close()
