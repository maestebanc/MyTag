"""Ventana principal de MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango

from .. import i18n
from ..audio_track import AudioTrack
from .cover_panel import CoverPanel
from .cover_search_dialog import CoverSearchDialog
from .preferences_dialog import PreferencesDialog
from .tag_editor import TagEditor
from .track_item import TrackItem

DEFAULT_WINDOW_WIDTH = 1150
DEFAULT_WINDOW_HEIGHT = 650

# Columnas de la tabla de pistas: solo lo imprescindible para identificar
# cada tema de un vistazo. La edición completa de tags vive en el panel
# de la derecha. (prop_name, clave i18n, ancho fijo en px o None si se expande)
TRACK_LIST_COLUMNS = [
    ("tracknumber", "column.track", 56),
    ("title", "column.title", None),
    ("albumartist", "column.artist", 150),
]


def _make_column(
    title: str, prop_name: str, expand: bool = False, fixed_width: int | None = None
) -> Gtk.ColumnViewColumn:
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
    if fixed_width is not None:
        column.set_fixed_width(fixed_width)
    column.set_resizable(True)
    return column


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="MyTag")
        self.set_default_size(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        self.tracks: list[AudioTrack] = []
        self._search_query = ""
        self.list_store = Gio.ListStore(item_type=TrackItem)
        self.search_filter = Gtk.CustomFilter.new(self._track_matches_search)
        self.filter_model = Gtk.FilterListModel(model=self.list_store, filter=self.search_filter)
        self.selection_model = Gtk.MultiSelection(model=self.filter_model)
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

        self._toast(i18n.t("toast.startup"))

    # ---------- construcción de la interfaz ----------

    def _build_headerbar(self) -> Adw.HeaderBar:
        header = Adw.HeaderBar()

        self.window_title = Adw.WindowTitle(title=i18n.t("app.title"), subtitle="")
        header.set_title_widget(self.window_title)

        header.pack_start(self._build_open_menu_button())

        self.btn_search_toggle = Gtk.ToggleButton()
        self.btn_search_toggle.set_icon_name("system-search-symbolic")
        self.btn_search_toggle.set_tooltip_text(i18n.t("toolbar.search"))
        header.pack_start(self.btn_search_toggle)

        header.pack_start(self._build_more_menu_button())

        btn_save = Gtk.Button(label=i18n.t("toolbar.save"))
        btn_save.add_css_class("suggested-action")
        btn_save.connect("clicked", lambda _b: self.save_all())
        header.pack_end(btn_save)

        btn_preferences = Gtk.Button()
        btn_preferences.set_icon_name("emblem-system-symbolic")
        btn_preferences.set_tooltip_text(i18n.t("toolbar.preferences"))
        btn_preferences.connect("clicked", lambda _b: self._open_preferences())
        header.pack_end(btn_preferences)

        return header

    def _build_open_menu_button(self) -> Gtk.MenuButton:
        menu_button = Gtk.MenuButton(label=i18n.t("toolbar.open"))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, callback) -> None:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.get_child().set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        add_item(i18n.t("toolbar.open_files"), self.open_files_dialog)
        add_item(i18n.t("toolbar.open_folder"), self.open_folder_dialog)

        popover.set_child(box)
        menu_button.set_popover(popover)
        return menu_button

    def _build_more_menu_button(self) -> Gtk.MenuButton:
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("view-more-symbolic")
        menu_button.set_tooltip_text(i18n.t("toolbar.more_actions"))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, callback) -> None:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.get_child().set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        add_item(i18n.t("menu.autonumber"), self.autonumber_selected)
        add_item(i18n.t("menu.revert_selected"), self.revert_selected)

        popover.set_child(box)
        menu_button.set_popover(popover)
        return menu_button

    def _open_preferences(self) -> None:
        dialog = PreferencesDialog()
        dialog.present(self)

    def _build_track_list_panel(self) -> Gtk.Widget:
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(i18n.t("list.search_placeholder"))
        self.search_entry.connect("changed", self._on_search_changed)

        self.search_bar = Gtk.SearchBar()
        self.search_bar.set_child(self.search_entry)
        self.search_bar.connect_entry(self.search_entry)
        self.btn_search_toggle.bind_property(
            "active",
            self.search_bar,
            "search-mode-enabled",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        self.column_view = Gtk.ColumnView(model=self.selection_model)
        for prop_name, label_key, width in TRACK_LIST_COLUMNS:
            self.column_view.append_column(
                _make_column(i18n.t(label_key), prop_name, expand=width is None, fixed_width=width)
            )

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.column_view)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)

        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom_bar.set_margin_top(8)
        bottom_bar.set_margin_bottom(8)
        bottom_bar.set_margin_start(8)
        bottom_bar.set_margin_end(8)

        btn_remove_selected = Gtk.Button(label=i18n.t("toolbar.remove"))
        btn_remove_selected.set_hexpand(True)
        btn_remove_selected.connect("clicked", lambda _b: self.remove_selected_rows())
        bottom_bar.append(btn_remove_selected)

        btn_clear_all = Gtk.Button(label=i18n.t("list.clear_all"))
        btn_clear_all.set_hexpand(True)
        btn_clear_all.add_css_class("destructive-action")
        btn_clear_all.connect("clicked", lambda _b: self.clear_all_tracks())
        bottom_bar.append(btn_clear_all)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.append(self.search_bar)
        left_box.append(scroller)
        left_box.append(Gtk.Separator())
        left_box.append(bottom_bar)

        left_frame = Gtk.Frame()
        left_frame.add_css_class("card")
        left_frame.set_overflow(Gtk.Overflow.HIDDEN)
        left_frame.set_child(left_box)
        return left_frame

    def _track_matches_search(self, item: TrackItem, _user_data=None) -> bool:
        if not self._search_query:
            return True
        haystack = f"{item.title} {item.artist} {item.filename}".lower()
        return self._search_query in haystack

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._search_query = entry.get_text().strip().lower()
        self.search_filter.changed(Gtk.FilterChange.DIFFERENT)

    def _build_body(self) -> Gtk.Widget:
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.set_position(DEFAULT_WINDOW_WIDTH // 2)
        paned.set_margin_top(12)
        paned.set_margin_bottom(12)
        paned.set_margin_start(12)
        paned.set_margin_end(12)

        paned.set_start_child(self._build_track_list_panel())
        paned.set_resize_start_child(True)

        side_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        side_box.set_margin_top(20)
        side_box.set_margin_bottom(20)
        side_box.set_margin_start(20)
        side_box.set_margin_end(20)

        self.cover_panel = CoverPanel()
        self.cover_panel.connect("cover-change-requested", self._on_cover_change_requested)
        self.cover_panel.connect("cover-remove-requested", self._on_cover_remove_requested)
        self.cover_panel.connect("musicbrainz-search-requested", self._on_musicbrainz_search_requested)
        side_box.append(self.cover_panel)

        self.tag_editor = TagEditor()
        self.tag_editor.set_hexpand(True)
        self.tag_editor.connect("changes-requested", self._on_tag_changes_requested)
        side_box.append(self.tag_editor)

        side_scroller = Gtk.ScrolledWindow()
        side_scroller.set_child(side_box)
        side_scroller.set_hexpand(True)
        paned.set_end_child(side_scroller)
        paned.set_resize_end_child(True)

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
        dialog = Gtk.FileDialog(title=i18n.t("dialog.open_files.title"))
        filter_flac = Gtk.FileFilter()
        filter_flac.set_name(i18n.t("dialog.open_files.filter_name"))
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
        dialog = Gtk.FileDialog(title=i18n.t("dialog.open_folder.title"))
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
            self._show_message(i18n.t("app.title"), i18n.t("dialog.no_flac_found"))
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
            self._show_message(i18n.t("dialog.load_errors_title"), "\n".join(errors))
        self._toast(i18n.t("toast.files_added", added=added, total=len(self.tracks)))

        if added and self.selection_model.get_selection().get_size() == 0:
            self.selection_model.select_item(0, True)

    def _refresh_row_for_track(self, track: AudioTrack) -> None:
        index = self.tracks.index(track)
        item = self.list_store.get_item(index)
        item.refresh()

    # ---------- selección ----------

    def _selected_tracks(self) -> list[AudioTrack]:
        tracks = []
        n = self.selection_model.get_n_items()
        for i in range(n):
            if self.selection_model.is_selected(i):
                tracks.append(self.selection_model.get_item(i).track)
        return tracks

    def _on_selection_changed(self, _model, _pos, _n_items) -> None:
        tracks = self._selected_tracks()
        self.tag_editor.set_tracks(tracks)
        self.cover_panel.set_tracks(tracks)

    # ---------- aplicar cambios (en memoria, en vivo) ----------

    def _on_tag_changes_requested(self, _editor, changes: dict) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            for key, value in changes.items():
                track.set_tag(key, value)
            self._refresh_row_for_track(track)
        self._update_title_state()

    def _on_cover_change_requested(self, _panel, data: bytes, mime: str) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.set_cover_bytes(data, mime)
        self.cover_panel.set_tracks(tracks)
        self._update_title_state()

    def _on_cover_remove_requested(self, _panel) -> None:
        tracks = self._selected_tracks()
        for track in tracks:
            track.remove_cover()
        self.cover_panel.set_tracks(tracks)
        self._update_title_state()

    def _on_musicbrainz_search_requested(self, _panel) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message(i18n.t("mb.title"), i18n.t("mb.select_tracks_first"))
            return

        albums = {t.get_tag("ALBUM").strip() for t in tracks}
        artists = {t.get_tag("ALBUMARTIST").strip() for t in tracks}
        if len(albums) != 1 or len(artists) != 1 or not next(iter(albums)) or not next(iter(artists)):
            self._show_message(i18n.t("mb.title"), i18n.t("mb.need_same_album_artist"))
            return

        album = next(iter(albums))
        artist = next(iter(artists))
        dialog = CoverSearchDialog(album, artist)
        dialog.connect("cover-chosen", self._on_musicbrainz_cover_chosen)
        dialog.present(self)

    def _on_musicbrainz_cover_chosen(self, _dialog, data: bytes, mime: str) -> None:
        self._on_cover_change_requested(None, data, mime)
        self._toast(i18n.t("toast.cover_mb_applied"))

    # ---------- otras acciones sobre los seleccionados ----------

    def autonumber_selected(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        for index, track in enumerate(tracks, start=1):
            track.set_tag("TRACKNUMBER", str(index))
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(self._selected_tracks())
        self._update_title_state()
        self._toast(i18n.t("toast.autonumbered", n=len(tracks)))

    def revert_selected(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        for track in tracks:
            track.revert()
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(tracks)
        self.cover_panel.set_tracks(tracks)
        self._update_title_state()
        self._toast(i18n.t("toast.reverted", n=len(tracks)))

    def remove_selected_rows(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return

        def do_remove() -> None:
            self._remove_tracks({id(t) for t in tracks})
            self._toast(i18n.t("toast.total_files", total=len(self.tracks)))
            self._update_title_state()

        self._confirm_discard_unsaved(tracks, do_remove)

    def clear_all_tracks(self) -> None:
        if not self.tracks:
            return
        tracks = list(self.tracks)

        def do_clear() -> None:
            self.list_store.remove_all()
            self.tracks = []
            self._toast(i18n.t("toast.total_files", total=0))
            self._update_title_state()

        self._confirm_discard_unsaved(tracks, do_clear)

    def _remove_tracks(self, ids: set[int]) -> None:
        for i in reversed(range(self.list_store.get_n_items())):
            if id(self.list_store.get_item(i).track) in ids:
                self.list_store.remove(i)
        self.tracks = [t for t in self.tracks if id(t) not in ids]

    def _confirm_discard_unsaved(self, tracks: list[AudioTrack], on_confirmed) -> None:
        dirty_count = sum(1 for t in tracks if t.is_dirty)
        if not dirty_count:
            on_confirmed()
            return

        dialog = Adw.AlertDialog(
            heading=i18n.t("dialog.unsaved_title"),
            body=i18n.t("confirm.discard_unsaved_body", n=dirty_count),
        )
        dialog.add_response("cancel", i18n.t("action.cancel"))
        dialog.add_response("continue", i18n.t("action.continue"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, response: on_confirmed() if response == "continue" else None)
        dialog.present(self)

    # ---------- guardar ----------

    def save_all(self) -> None:
        dirty = [t for t in self.tracks if t.is_dirty]
        if not dirty:
            self._toast(i18n.t("toast.no_pending_changes"))
            return
        errors = []
        for track in dirty:
            try:
                track.save()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{track.filename}: {exc}")
        if errors:
            self._show_message(i18n.t("dialog.save_error_title"), "\n".join(errors))
        self._toast(i18n.t("toast.save_done", saved=len(dirty) - len(errors)))
        self._update_title_state()

    def _has_unsaved_changes(self) -> bool:
        return any(t.is_dirty for t in self.tracks)

    def _update_title_state(self) -> None:
        dirty_count = sum(1 for t in self.tracks if t.is_dirty)
        if dirty_count:
            self.window_title.set_subtitle(i18n.t("window.unsaved_changes", n=dirty_count))
        else:
            self.window_title.set_subtitle("")

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
        dialog.add_response("ok", i18n.t("action.ok"))
        dialog.present(self)

    # ---------- cierre ----------

    def _on_close_request(self, _window) -> bool:
        if self._force_close or not self._has_unsaved_changes():
            return False  # permitir el cierre

        dialog = Adw.AlertDialog(
            heading=i18n.t("dialog.unsaved_title"),
            body=i18n.t("dialog.unsaved_body"),
        )
        dialog.add_response("cancel", i18n.t("action.cancel"))
        dialog.add_response("discard", i18n.t("action.discard"))
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
