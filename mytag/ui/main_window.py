"""Ventana principal de MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango

from .. import acoustid, config, i18n, integrity
from ..audio_track import AudioTrack
from ..constants import SUPPORTED_EXTENSIONS
from ..cover_utils import resize_image_bytes_exact
from .about_dialog import build_about_dialog
from .cover_panel import CoverPanel
from .cover_search_dialog import CoverSearchDialog
from .fingerprint_dialog import FingerprintDialog
from .preferences_dialog import PreferencesDialog
from .rename_dialog import RenameDialog
from .shortcuts_dialog import ShortcutsDialog
from .tag_editor import TagEditor
from .track_item import TrackItem

DEFAULT_WINDOW_WIDTH = 1150
DEFAULT_WINDOW_HEIGHT = 650

# Columnas de la tabla de pistas: solo lo imprescindible para identificar
# cada tema de un vistazo. La edición completa de tags vive en el panel
# de la derecha. (prop_name, clave i18n, ancho fijo inicial en px)
#
# Todas llevan un ancho fijo explícito (ninguna usa expand=True): una
# columna en modo "expand" reserva un ancho mínimo propio del que no baja
# aunque se arrastre el borde de la columna vecina, lo que tope el
# redimensionado de esa vecina mucho antes de lo que cabría esperar. Con
TRACK_LIST_COLUMNS = [
    # (prop_name, label_key, fixed_width, expand, resizable)
    ("tracknumber", "column.track", 76, False, False),
    ("albumartist", "column.artist", None, True, True),
    ("title", "column.title", None, True, True),
]


def _make_column(
    title: str,
    prop_name: str,
    expand: bool = False,
    fixed_width: int | None = None,
    resizable: bool = True,
) -> Gtk.ColumnViewColumn:
    factory = Gtk.SignalListItemFactory()

    def on_setup(_factory, list_item: Gtk.ListItem) -> None:
        label = Gtk.Label(xalign=0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        if prop_name == "tracknumber":
            label.add_css_class("track-number-label")
            label.set_xalign(0.5)
            label.set_margin_start(4)
            label.set_margin_end(4)
        else:
            label.set_margin_start(8)
            label.set_margin_end(8)
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
    column.set_resizable(resizable)
    return column


def _make_status_column() -> Gtk.ColumnViewColumn:
    """Columna estrecha con un icono de aviso si al tema le falta portada,
    año o género (indicador de "completitud" de un vistazo)."""
    factory = Gtk.SignalListItemFactory()

    def on_setup(_factory, list_item: Gtk.ListItem) -> None:
        image = Gtk.Image()
        image.set_pixel_size(14)
        image.add_css_class("track-warning-icon")
        list_item.set_child(image)

    def on_bind(_factory, list_item: Gtk.ListItem) -> None:
        image = list_item.get_child()
        item = list_item.get_item()

        def update(*_args) -> None:
            missing = item.get_property("missing-fields")
            if missing:
                fields = ", ".join(i18n.t(f"completeness.{code}") for code in missing.split(","))
                image.set_from_icon_name("dialog-warning-symbolic")
                image.set_tooltip_text(i18n.t("completeness.tooltip", fields=fields))
            else:
                image.clear()
                image.set_tooltip_text("")

        update()
        list_item.mytag_handler_id = item.connect("notify::missing-fields", update)
        list_item.mytag_handler_item = item

    def on_unbind(_factory, list_item: Gtk.ListItem) -> None:
        item = getattr(list_item, "mytag_handler_item", None)
        handler_id = getattr(list_item, "mytag_handler_id", None)
        if item is not None and handler_id is not None:
            item.disconnect(handler_id)

    factory.connect("setup", on_setup)
    factory.connect("bind", on_bind)
    factory.connect("unbind", on_unbind)

    column = Gtk.ColumnViewColumn(title="", factory=factory)
    column.set_fixed_width(32)
    column.set_resizable(False)
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

        self.main_stack = Adw.ViewStack()
        self.main_stack.add_named(self._build_empty_state(), "empty")
        self.main_stack.add_named(self._build_body(), "editor")
        self.main_stack.set_visible_child_name("empty")

        toolbar_view.set_content(self.main_stack)
        self.toast_overlay.set_child(toolbar_view)
        self.set_content(self.toast_overlay)

        self._setup_drop_target()
        self._setup_actions(app)
        self.connect("close-request", self._on_close_request)
        self._force_close = False

        self._update_list_status()
        self._update_title_state()

    def _setup_actions(self, app: Adw.Application) -> None:
        actions = {
            "open-files": lambda *_: self.open_files_dialog(),
            "save": lambda *_: self.save_all(),
            "toggle-search": lambda *_: self.btn_search_toggle.set_active(
                not self.btn_search_toggle.get_active()
            ),
            "remove-selected": lambda *_: self.remove_selected_rows(),
            "preferences": lambda *_: self._open_preferences(),
            "shortcuts": lambda *_: self._open_shortcuts(),
        }
        accels = {
            "open-files": ["<Control>o"],
            "save": ["<Control>s"],
            "toggle-search": ["<Control>f"],
            "remove-selected": ["Delete"],
            "preferences": ["<Control>comma"],
            "shortcuts": ["<Control>question"],
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)
            app.set_accels_for_action(f"win.{name}", accels[name])
        app.set_accels_for_action("app.quit", ["<Control>q"])

    # ---------- construcción de la interfaz ----------

    def _build_empty_state(self) -> Gtk.Widget:
        status_page = Adw.StatusPage()
        status_page.set_icon_name("folder-music-symbolic")
        status_page.set_title(i18n.t("empty.title"))
        status_page.set_description(i18n.t("empty.description"))

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)

        btn_files = Gtk.Button()
        btn_files.add_css_class("suggested-action")
        btn_files.add_css_class("pill")
        bf_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bf_box.set_margin_start(16)
        bf_box.set_margin_end(16)
        bf_box.set_margin_top(8)
        bf_box.set_margin_bottom(8)
        bf_box.append(Gtk.Image.new_from_icon_name("document-open-symbolic"))
        bf_box.append(Gtk.Label(label=i18n.t("toolbar.open_files")))
        btn_files.set_child(bf_box)
        btn_files.connect("clicked", lambda _b: self.open_files_dialog())
        box.append(btn_files)

        btn_folder = Gtk.Button()
        btn_folder.add_css_class("pill")
        bfo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bfo_box.set_margin_start(16)
        bfo_box.set_margin_end(16)
        bfo_box.set_margin_top(8)
        bfo_box.set_margin_bottom(8)
        bfo_box.append(Gtk.Image.new_from_icon_name("folder-open-symbolic"))
        bfo_box.append(Gtk.Label(label=i18n.t("toolbar.open_folder")))
        btn_folder.set_child(bfo_box)
        btn_folder.connect("clicked", lambda _b: self.open_folder_dialog())
        box.append(btn_folder)

        status_page.set_child(box)
        self.empty_page = status_page
        return status_page

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

        self.btn_save = Gtk.Button()
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        save_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
        save_lbl = Gtk.Label(label=i18n.t("toolbar.save"))
        save_box.append(save_icon)
        save_box.append(save_lbl)
        self.btn_save.set_child(save_box)
        self.btn_save.add_css_class("suggested-action")
        self.btn_save.set_sensitive(False)
        self.btn_save.connect("clicked", lambda _b: self.save_all())
        header.pack_end(self.btn_save)

        header.pack_end(self._build_primary_menu_button())

        return header

    def _build_primary_menu_button(self) -> Gtk.MenuButton:
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text(i18n.t("menu.primary"))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, icon_name: str, callback) -> None:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            ibox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ibox.set_margin_start(4)
            ibox.set_margin_end(4)
            ibox.set_margin_top(2)
            ibox.set_margin_bottom(2)
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.add_css_class("dim-label")
            text = Gtk.Label(label=label, xalign=0)
            text.set_hexpand(True)
            ibox.append(img)
            ibox.append(text)
            btn.set_child(ibox)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        add_item(i18n.t("menu.preferences"), "preferences-system-symbolic", self._open_preferences)
        add_item(i18n.t("menu.keyboard_shortcuts"), "input-keyboard-symbolic", self._open_shortcuts)
        add_item(i18n.t("menu.about"), "help-about-symbolic", self._open_about)

        popover.set_child(box)
        menu_button.set_popover(popover)
        return menu_button

    def _open_shortcuts(self) -> None:
        ShortcutsDialog().present(self)

    def _open_about(self) -> None:
        build_about_dialog().present(self)

    def _build_open_menu_button(self) -> Gtk.MenuButton:
        menu_button = Gtk.MenuButton()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name("document-open-symbolic")
        lbl = Gtk.Label(label=i18n.t("toolbar.open"))
        box.append(icon)
        box.append(lbl)
        menu_button.set_child(box)

        pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pbox.set_margin_top(6)
        pbox.set_margin_bottom(6)
        pbox.set_margin_start(6)
        pbox.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, icon_name: str, callback) -> None:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            ibox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ibox.set_margin_start(4)
            ibox.set_margin_end(4)
            ibox.set_margin_top(2)
            ibox.set_margin_bottom(2)
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.add_css_class("dim-label")
            text = Gtk.Label(label=label, xalign=0)
            text.set_hexpand(True)
            ibox.append(img)
            ibox.append(text)
            btn.set_child(ibox)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            pbox.append(btn)

        add_item(i18n.t("toolbar.open_files"), "document-open-symbolic", self.open_files_dialog)
        add_item(i18n.t("toolbar.open_folder"), "folder-open-symbolic", self.open_folder_dialog)

        popover.set_child(pbox)
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

        def add_item(label: str, icon_name: str, callback) -> None:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            ibox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ibox.set_margin_start(4)
            ibox.set_margin_end(4)
            ibox.set_margin_top(2)
            ibox.set_margin_bottom(2)
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.add_css_class("dim-label")
            text = Gtk.Label(label=label, xalign=0)
            text.set_hexpand(True)
            ibox.append(img)
            ibox.append(text)
            btn.set_child(ibox)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        add_item(i18n.t("menu.autonumber"), "view-list-ordered-symbolic", self.autonumber_selected)
        add_item(i18n.t("menu.revert_selected"), "document-revert-symbolic", self.revert_selected)
        add_item(i18n.t("menu.identify_fingerprint"), "audio-card-symbolic", self.identify_selected_by_fingerprint)
        add_item(i18n.t("menu.check_integrity"), "emblem-ok-symbolic", self.check_integrity_selected)
        add_item(i18n.t("menu.rename_from_tags"), "document-edit-symbolic", self.rename_selected_from_tags)
        box.append(Gtk.Separator())
        add_item(i18n.t("menu.fill_missing_covers"), "image-x-generic-symbolic", self.fill_missing_covers)

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
        self.column_view.add_css_class("track-table")
        self.column_view.append_column(_make_status_column())
        for prop_name, label_key, width, expand, resizable in TRACK_LIST_COLUMNS:
            self.column_view.append_column(
                _make_column(
                    i18n.t(label_key),
                    prop_name,
                    expand=expand,
                    fixed_width=width,
                    resizable=resizable,
                )
            )

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.column_view)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)

        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom_bar.add_css_class("track-list-footer")

        self.list_status_label = Gtk.Label(label="")
        self.list_status_label.add_css_class("dim-label")
        self.list_status_label.add_css_class("caption")
        self.list_status_label.set_hexpand(True)
        self.list_status_label.set_xalign(0)
        bottom_bar.append(self.list_status_label)

        self.btn_remove_selected = Gtk.Button()
        self.btn_remove_selected.set_icon_name("list-remove-symbolic")
        self.btn_remove_selected.set_tooltip_text(i18n.t("toolbar.remove"))
        self.btn_remove_selected.add_css_class("flat")
        self.btn_remove_selected.connect("clicked", lambda _b: self.remove_selected_rows())
        bottom_bar.append(self.btn_remove_selected)

        self.btn_clear_all = Gtk.Button()
        self.btn_clear_all.set_icon_name("user-trash-symbolic")
        self.btn_clear_all.set_tooltip_text(i18n.t("list.clear_all"))
        self.btn_clear_all.add_css_class("flat")
        self.btn_clear_all.add_css_class("destructive-action")
        self.btn_clear_all.connect("clicked", lambda _b: self.clear_all_tracks())
        bottom_bar.append(self.btn_clear_all)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_box.append(self.search_bar)
        left_box.append(scroller)
        left_box.append(bottom_bar)

        self.track_list_frame = Gtk.Frame()
        self.track_list_frame.add_css_class("card")
        self.track_list_frame.set_overflow(Gtk.Overflow.HIDDEN)
        self.track_list_frame.set_child(left_box)
        return self.track_list_frame

    def _track_matches_search(self, item: TrackItem, _user_data=None) -> bool:
        if not self._search_query:
            return True
        haystack = f"{item.title} {item.artist} {item.filename}".lower()
        return self._search_query in haystack

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._search_query = entry.get_text().strip().lower()
        self.search_filter.changed(Gtk.FilterChange.DIFFERENT)

    def _build_body(self) -> Gtk.Widget:
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_wide_handle(True)
        self.paned.set_position(DEFAULT_WINDOW_WIDTH // 2)
        self.paned.set_margin_top(12)
        self.paned.set_margin_bottom(12)
        self.paned.set_margin_start(12)
        self.paned.set_margin_end(12)

        self.paned.set_start_child(self._build_track_list_panel())
        self.paned.set_resize_start_child(True)

        # Un Gtk.Paned (en vez de un Gtk.Box fijo) para que el ancho relativo
        # de la portada frente a las etiquetas se pueda arrastrar con el
        # ratón, igual que el divisor entre la lista y este panel.
        side_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        side_paned.set_wide_handle(True)
        side_paned.set_position(310)
        side_paned.set_margin_top(16)
        side_paned.set_margin_bottom(16)

        self.cover_panel = CoverPanel()
        self.cover_panel.set_margin_start(16)
        self.cover_panel.set_margin_end(16)
        self.cover_panel.connect("cover-change-requested", self._on_cover_change_requested)
        self.cover_panel.connect("cover-resize-each-requested", self._on_cover_resize_each_requested)
        self.cover_panel.connect("cover-remove-requested", self._on_cover_remove_requested)
        self.cover_panel.connect("musicbrainz-search-requested", self._on_musicbrainz_search_requested)
        side_paned.set_start_child(self.cover_panel)
        side_paned.set_resize_start_child(False)

        self.tag_editor = TagEditor()
        self.tag_editor.set_margin_start(16)
        self.tag_editor.set_margin_end(16)
        self.tag_editor.set_hexpand(True)
        self.tag_editor.connect("changes-requested", self._on_tag_changes_requested)
        side_paned.set_end_child(self.tag_editor)
        side_paned.set_resize_end_child(True)

        side_scroller = Gtk.ScrolledWindow()
        side_scroller.set_child(side_paned)
        side_scroller.set_hexpand(True)
        self.paned.set_end_child(side_scroller)
        self.paned.set_resize_end_child(True)

        return self.paned

    def _setup_drop_target(self) -> None:
        actions = Gdk.DragAction.COPY | Gdk.DragAction.MOVE

        for target_widget in (self.track_list_frame, self.empty_page):
            target = Gtk.DropTarget.new(Gio.File, actions)
            target.connect("drop", self._on_drop)
            target.connect("enter", lambda *_, w=target_widget: self._on_track_drop_enter(w))
            target.connect("leave", lambda *_, w=target_widget: self._on_track_drop_leave(w))
            target_widget.add_controller(target)

            target_files = Gtk.DropTarget.new(Gdk.FileList, actions)
            target_files.connect("drop", self._on_drop_filelist)
            target_files.connect("enter", lambda *_, w=target_widget: self._on_track_drop_enter(w))
            target_files.connect("leave", lambda *_, w=target_widget: self._on_track_drop_leave(w))
            target_widget.add_controller(target_files)

    def _on_track_drop_enter(self, widget: Gtk.Widget, *_args) -> int:
        widget.add_css_class("drop-highlight")
        return Gdk.DragAction.COPY | Gdk.DragAction.MOVE

    def _on_track_drop_leave(self, widget: Gtk.Widget, *_args) -> None:
        widget.remove_css_class("drop-highlight")

    # ---------- carga de archivos ----------

    def open_files_dialog(self) -> None:
        dialog = Gtk.FileDialog(title=i18n.t("dialog.open_files.title"))
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name(i18n.t("dialog.open_files.filter_name"))
        for ext in SUPPORTED_EXTENSIONS:
            filter_audio.add_pattern(f"*{ext}")
            filter_audio.add_pattern(f"*{ext.upper()}")
        filter_audio.add_mime_type("audio/flac")
        filter_audio.add_mime_type("audio/x-flac")
        filter_audio.add_mime_type("audio/mpeg")
        filter_audio.add_mime_type("audio/mp3")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_audio)
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
        found = self._find_audio_files(folder)
        if not found:
            self._show_message(i18n.t("app.title"), i18n.t("dialog.no_flac_found"))
            return
        self.add_paths(found)

    @staticmethod
    def _find_audio_files(folder: str) -> list[str]:
        found = []
        for root, _dirs, files in os.walk(folder):
            for name in sorted(files):
                if name.lower().endswith(SUPPORTED_EXTENSIONS):
                    found.append(os.path.join(root, name))
        return found

    _find_flac_files = _find_audio_files

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

        if self.tracks:
            self.main_stack.set_visible_child_name("editor")
        self._update_list_status()
        self._update_title_state()

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
        self._update_list_status()
        self._update_title_state()

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

    def _on_cover_resize_each_requested(self, _panel, size: int) -> None:
        # A diferencia de _on_cover_change_requested, aquí cada tema tiene su
        # propia portada de origen (por eso el panel ofreció este modo en vez
        # del habitual): se recorta y escala cada una por separado al mismo
        # cuadrado, en vez de aplicar unos mismos bytes a todos los temas.
        tracks = self._selected_tracks()
        for track in tracks:
            source = track.get_cover_bytes()
            if source is None:
                continue
            data, mime = resize_image_bytes_exact(source, (size, size))
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

    def check_integrity_selected(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        if not integrity.is_available():
            self._show_message(i18n.t("integrity.title"), i18n.t("integrity.flac_not_found"))
            return
        problems = []
        for track in tracks:
            ok, message = integrity.check_integrity(track.path)
            if not ok:
                problems.append(f"{track.filename}: {message}")
        if problems:
            self._show_message(i18n.t("integrity.problems_title"), "\n".join(problems))
        else:
            self._toast(i18n.t("integrity.all_ok", n=len(tracks)))

    def identify_selected_by_fingerprint(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        api_key = config.load_config().get("acoustid_api_key", "")
        if not api_key:
            self._show_message(i18n.t("fingerprint.title"), i18n.t("fingerprint.no_api_key"))
            return
        if not acoustid.fpcalc_available():
            self._show_message(i18n.t("fingerprint.title"), i18n.t("fingerprint.fpcalc_missing"))
            return

        track = tracks[0]
        dialog = FingerprintDialog(track.path, api_key)
        dialog.connect("match-chosen", self._on_fingerprint_match_chosen, track)
        dialog.present(self)

    def _on_fingerprint_match_chosen(self, _dialog, match: dict, track: AudioTrack) -> None:
        if match.get("title"):
            track.set_tag("TITLE", match["title"])
        if match.get("artist"):
            track.set_tag("ARTIST", match["artist"])
        if match.get("album"):
            track.set_tag("ALBUM", match["album"])
        self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(self._selected_tracks())
        self._update_title_state()
        self._toast(i18n.t("fingerprint.applied"))

    def fill_missing_covers(self) -> None:
        if not self.tracks:
            return
        groups: dict[tuple[str, str], list[AudioTrack]] = {}
        for track in self.tracks:
            album = track.get_tag("ALBUM").strip()
            artist = track.get_tag("ALBUMARTIST").strip()
            if not album or not artist:
                continue
            groups.setdefault((album, artist), []).append(track)

        self._fill_covers_groups = groups
        self._fill_covers_queue = [key for key, tracks in groups.items() if not any(t.get_cover_bytes() for t in tracks)]

        if not self._fill_covers_queue:
            self._toast(i18n.t("fillcovers.none_missing"))
            return
        self._process_next_missing_cover()

    def _process_next_missing_cover(self) -> None:
        if not self._fill_covers_queue:
            self._toast(i18n.t("fillcovers.done"))
            return
        album, artist = self._fill_covers_queue.pop(0)
        dialog = CoverSearchDialog(album, artist)
        dialog.connect("cover-chosen", self._on_fill_cover_chosen, (album, artist))
        dialog.connect("closed", lambda _d: self._process_next_missing_cover())
        dialog.present(self)

    def _on_fill_cover_chosen(self, _dialog, data: bytes, mime: str, key: tuple[str, str]) -> None:
        for track in self._fill_covers_groups.get(key, []):
            track.set_cover_bytes(data, mime)
            self._refresh_row_for_track(track)
        self.cover_panel.set_tracks(self._selected_tracks())
        self._update_title_state()

    def rename_selected_from_tags(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        dialog = RenameDialog(tracks)
        dialog.connect("rename-confirmed", self._on_rename_confirmed)
        dialog.present(self)

    def _on_rename_confirmed(self, _dialog, planned: dict) -> None:
        renamed = 0
        errors = []
        for track, new_path in planned.items():
            if new_path == track.path:
                continue
            if os.path.exists(new_path):
                errors.append(i18n.t("rename.collision", name=os.path.basename(new_path)))
                continue
            try:
                os.rename(track.path, new_path)
                track.update_path(new_path)
                self._refresh_row_for_track(track)
                renamed += 1
            except OSError as exc:
                errors.append(f"{track.filename}: {exc}")
        if errors:
            self._show_message(i18n.t("rename.errors_title"), "\n".join(errors))
        self.tag_editor.set_tracks(self._selected_tracks())
        self._toast(i18n.t("rename.done", n=renamed))

    def remove_selected_rows(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return

        def do_remove() -> None:
            self._remove_tracks({id(t) for t in tracks})
            if not self.tracks:
                self.main_stack.set_visible_child_name("empty")
            self._toast(i18n.t("toast.total_files", total=len(self.tracks)))
            self._update_list_status()
            self._update_title_state()

        self._confirm_discard_unsaved(tracks, do_remove)

    def clear_all_tracks(self) -> None:
        if not self.tracks:
            return
        tracks = list(self.tracks)

        def do_clear() -> None:
            self.list_store.remove_all()
            self.tracks = []
            self.main_stack.set_visible_child_name("empty")
            self._toast(i18n.t("toast.total_files", total=0))
            self._update_list_status()
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

    def _update_list_status(self) -> None:
        total = len(self.tracks)
        selected = len(self._selected_tracks())
        if not total:
            self.list_status_label.set_text("")
            self.btn_remove_selected.set_sensitive(False)
            self.btn_clear_all.set_sensitive(False)
        elif selected:
            self.list_status_label.set_text(
                i18n.t("list.status_selected", total=total, selected=selected)
            )
            self.btn_remove_selected.set_sensitive(True)
            self.btn_clear_all.set_sensitive(True)
        else:
            self.list_status_label.set_text(i18n.t("list.status_summary", total=total))
            self.btn_remove_selected.set_sensitive(False)
            self.btn_clear_all.set_sensitive(True)

    def _update_title_state(self) -> None:
        dirty_count = sum(1 for t in self.tracks if t.is_dirty)
        if dirty_count:
            self.window_title.set_subtitle(i18n.t("window.unsaved_changes", n=dirty_count))
            self.btn_save.set_sensitive(True)
        else:
            if self.tracks:
                self.window_title.set_subtitle(i18n.t("list.status_summary", total=len(self.tracks)))
            else:
                self.window_title.set_subtitle("")
            self.btn_save.set_sensitive(False)

    # ---------- arrastrar y soltar ----------

    def _on_drop(self, _target, gfile: Gio.File, _x, _y) -> bool:
        self.track_list_frame.remove_css_class("drop-highlight")
        self.empty_page.remove_css_class("drop-highlight")
        return self._handle_dropped_paths([gfile.get_path()] if gfile.get_path() else [])

    def _on_drop_filelist(self, _target, file_list, _x, _y) -> bool:
        self.track_list_frame.remove_css_class("drop-highlight")
        self.empty_page.remove_css_class("drop-highlight")
        paths = [f.get_path() for f in file_list.get_files() if f.get_path()]
        return self._handle_dropped_paths(paths)

    def _handle_dropped_paths(self, dropped: list[str]) -> bool:
        paths = []
        for local_path in dropped:
            if not local_path:
                continue
            if os.path.isdir(local_path):
                paths.extend(self._find_audio_files(local_path))
            elif local_path.lower().endswith(SUPPORTED_EXTENSIONS):
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
