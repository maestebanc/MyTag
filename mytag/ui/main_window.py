"""Ventana principal de MyTag (GTK4/Adwaita)."""
from __future__ import annotations

import os
import threading
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango

from .. import __version__, acoustid, config, i18n, integrity
from ..audio_track import AudioTrack
from ..constants import SUPPORTED_EXTENSIONS
from ..cover_utils import resize_image_bytes_exact
from .about_dialog import build_about_dialog
from .batch_fingerprint_dialog import BatchFingerprintDialog
from .cover_panel import CoverPanel
from .cover_search_dialog import CoverSearchDialog
from .feature_guide_dialog import FeatureGuideDialog
from .fingerprint_dialog import FingerprintDialog
from .preferences_dialog import PreferencesDialog
from .rename_dialog import RenameDialog
from .shortcuts_dialog import ShortcutsDialog
from .tag_editor import TagEditor
from .track_item import TrackItem
from ..constants import ACOUSTID_CLIENT_KEY
from ..natural_sort import natural_sort_key

DEFAULT_WINDOW_WIDTH = 1260
DEFAULT_WINDOW_HEIGHT = 860
RIGHT_PANEL_WIDTH = 290

COLUMN_SPEC = [
    # (col_id, label_key, resizable, center)
    ("status", "column.status", False, True),
    ("tracknumber", "column.track", True, True),
    ("title", "column.title", True, False),
    ("artist", "column.artist", True, False),
    ("album", "column.album", True, False),
    ("albumartist", "column.albumartist", True, False),
    ("date", "column.date", True, True),
    ("genre", "column.genre", True, False),
    ("filename", "column.filename", True, False),
    ("discnumber", "column.disc", True, True),
]

COLUMN_SPEC_MAP = {spec[0]: spec for spec in COLUMN_SPEC}


def _make_column(
    title: str,
    prop_name: str,
    fixed_width: int = 200,
    resizable: bool = True,
    center: bool = False,
) -> Gtk.ColumnViewColumn:
    factory = Gtk.SignalListItemFactory()

    def on_setup(_factory, list_item: Gtk.ListItem) -> None:
        label = Gtk.Label(xalign=0.5 if center else 0.0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        if prop_name in ("tracknumber", "discnumber"):
            label.add_css_class("track-number-label")
            label.set_margin_start(2)
            label.set_margin_end(2)
        else:
            label.set_margin_start(8)
            label.set_margin_end(8)
        list_item.set_child(label)

    def on_bind(_factory, list_item: Gtk.ListItem) -> None:
        label = list_item.get_child()
        label._mytag_list_item = list_item
        item = list_item.get_item()

        def update(*_args) -> None:
            val = item.get_property(prop_name)
            label.set_text(val or "")

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
    if prop_name == "tracknumber":
        expr = Gtk.PropertyExpression.new(TrackItem, None, "track_order_key")
        column.set_sorter(Gtk.NumericSorter.new(expr))
    elif prop_name == "discnumber":
        expr = Gtk.PropertyExpression.new(TrackItem, None, "disc_order_key")
        column.set_sorter(Gtk.NumericSorter.new(expr))
    elif prop_name == "filename":
        def _compare_filename(a, b) -> int:
            if a is None or b is None:
                return 0
            ka = natural_sort_key(getattr(a, "filename", ""))
            kb = natural_sort_key(getattr(b, "filename", ""))
            return -1 if ka < kb else (1 if ka > kb else 0)

        column.set_sorter(Gtk.CustomSorter.new(_compare_filename))
    else:
        expr = Gtk.PropertyExpression.new(TrackItem, None, prop_name)
        sorter = Gtk.StringSorter.new(expr)
        sorter.set_ignore_case(True)
        column.set_sorter(sorter)

    column.set_expand(False)
    column.set_fixed_width(fixed_width)
    column.set_resizable(resizable)
    return column


def _make_status_column(fixed_width: int = 36) -> Gtk.ColumnViewColumn:
    """Columna estrecha con un icono de aviso si al tema le falta portada,
    año o género (indicador de "completitud" de un vistazo) o error de integridad."""
    factory = Gtk.SignalListItemFactory()

    def on_setup(_factory, list_item: Gtk.ListItem) -> None:
        image = Gtk.Image()
        image.set_pixel_size(14)
        image.add_css_class("track-warning-icon")
        list_item.set_child(image)

    def on_bind(_factory, list_item: Gtk.ListItem) -> None:
        image = list_item.get_child()
        image._mytag_list_item = list_item
        item = list_item.get_item()

        def update(*_args) -> None:
            err = getattr(item.track, "integrity_error", None)
            if err:
                image.remove_css_class("track-warning-icon")
                image.add_css_class("track-error-icon")
                image.set_from_icon_name("dialog-error-symbolic")
                image.set_tooltip_text(f"{i18n.t('integrity.error_tooltip')}: {err}")
                return

            image.remove_css_class("track-error-icon")
            image.add_css_class("track-warning-icon")
            missing = item.get_property("missing-fields")
            if missing:
                fields = ", ".join(i18n.t(f"completeness.{code}") for code in missing.split(","))
                image.set_from_icon_name("dialog-warning-symbolic")
                image.set_tooltip_text(i18n.t("completeness.tooltip", fields=fields))
            else:
                image.clear()
                image.set_tooltip_text("")

        update()
        h1 = item.connect("notify::missing-fields", update)
        h2 = item.connect("notify::integrity-error", update)
        list_item.mytag_handlers = [(item, h1), (item, h2)]

    def on_unbind(_factory, list_item: Gtk.ListItem) -> None:
        handlers = getattr(list_item, "mytag_handlers", [])
        for obj, handler_id in handlers:
            obj.disconnect(handler_id)
        list_item.mytag_handlers = []

    factory.connect("setup", on_setup)
    factory.connect("bind", on_bind)
    factory.connect("unbind", on_unbind)

    column = Gtk.ColumnViewColumn(title="", factory=factory)
    column.set_fixed_width(fixed_width)
    column.set_resizable(False)
    column.set_expand(False)
    expr = Gtk.PropertyExpression.new(TrackItem, None, "status_sort_key")
    sorter = Gtk.StringSorter.new(expr)
    column.set_sorter(sorter)
    return column


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title=f"MyTag {__version__}")

        cfg = config.load_config()
        w = cfg.get("window_width", DEFAULT_WINDOW_WIDTH)
        h = cfg.get("window_height", DEFAULT_WINDOW_HEIGHT)
        self.set_default_size(max(900, w), max(600, h))
        if cfg.get("window_maximized", False):
            self.maximize()

        self._column_save_timeout_id: int | None = None
        self._columns: dict[str, Gtk.ColumnViewColumn] = {}
        self._reordering_columns: bool = False
        self._col_dnd_source_idx: int | None = None
        self._col_dnd_source_col: Gtk.ColumnViewColumn | None = None
        self._col_dnd_source_widget: Gtk.Widget | None = None
        self._col_dnd_is_dragging: bool = False
        self._col_dnd_target_info: tuple[int, Gtk.ColumnViewColumn, str] | None = None
        self._col_dnd_start_x: float = 0.0
        self._col_drag_gesture: Gtk.GestureDrag | None = None

        self.tracks: list[AudioTrack] = []
        self._search_query = ""
        self.list_store = Gio.ListStore(item_type=TrackItem)
        self.sort_model = Gtk.SortListModel(model=self.list_store)
        self.search_filter = Gtk.CustomFilter.new(self._track_matches_search)
        self.filter_model = Gtk.FilterListModel(model=self.sort_model, filter=self.search_filter)
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
        GLib.idle_add(self._adjust_initial_paned_position)

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

        self.window_title = Adw.WindowTitle(title=f"{i18n.t('app.title')} {__version__}", subtitle="")
        header.set_title_widget(self.window_title)

        header.pack_start(self._build_open_menu_button())

        self.btn_search_toggle = Gtk.ToggleButton()
        self.btn_search_toggle.set_icon_name("system-search-symbolic")
        self.btn_search_toggle.set_tooltip_text(i18n.t("toolbar.search"))
        header.pack_start(self.btn_search_toggle)

        header.pack_end(self._build_primary_menu_button())

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

        self.btn_revert = Gtk.Button()
        revert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        revert_icon = Gtk.Image.new_from_icon_name("document-revert-symbolic")
        revert_lbl = Gtk.Label(label=i18n.t("toolbar.revert"))
        revert_box.append(revert_icon)
        revert_box.append(revert_lbl)
        self.btn_revert.set_child(revert_box)
        self.btn_revert.add_css_class("flat")
        self.btn_revert.set_tooltip_text(i18n.t("toolbar.revert"))
        self.btn_revert.set_sensitive(False)
        self.btn_revert.connect("clicked", lambda _b: self.revert_all_or_selected())
        header.pack_end(self.btn_revert)

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
        add_item(i18n.t("menu.feature_guide"), "help-browser-symbolic", self._open_feature_guide)
        add_item(i18n.t("menu.about"), "help-about-symbolic", self._open_about)

        popover.set_child(box)
        menu_button.set_popover(popover)
        return menu_button

    def _open_feature_guide(self) -> None:
        FeatureGuideDialog().present(self)

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

    def _setup_track_list_context_menu(self) -> None:
        gesture = Gtk.GestureClick()
        gesture.set_button(Gdk.BUTTON_SECONDARY)
        gesture.connect("pressed", self._on_track_list_secondary_click)
        self.column_view.add_controller(gesture)

    def _on_track_list_secondary_click(self, _gesture, _n_press, x: float, y: float) -> None:
        if not self.tracks:
            return

        w = self.column_view.pick(x, y, Gtk.PickFlags.DEFAULT)
        target_pos = None
        while w and w != self.column_view:
            if hasattr(w, "_mytag_list_item"):
                target_pos = w._mytag_list_item.get_position()
                break
            w = w.get_parent()

        if target_pos is None:
            return

        # Si el elemento clicado NO estaba en la selección, se selecciona en exclusiva.
        # Si YA formaba parte de la selección, se conserva la selección múltiple.
        if not self.selection_model.is_selected(target_pos):
            self.selection_model.select_item(target_pos, True)

        selected = self._selected_tracks()
        if not selected:
            return

        popover = Gtk.Popover()
        popover.set_parent(self.column_view)
        popover.set_has_arrow(False)
        popover.connect("closed", lambda p: p.unparent())

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

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
            btn.connect("clicked", lambda _b: (popover.popdown(), callback()))
            box.append(btn)

        add_item(i18n.t("menu.identify_fingerprint"), "audio-card-symbolic", self.identify_selected_by_fingerprint)
        add_item(i18n.t("menu.autonumber"), "view-list-ordered-symbolic", self.autonumber_selected)
        add_item(i18n.t("menu.rename_from_tags"), "document-edit-symbolic", self.rename_selected_from_tags)
        add_item(i18n.t("menu.fill_missing_covers"), "image-x-generic-symbolic", self.fill_missing_covers)
        box.append(Gtk.Separator())
        add_item(i18n.t("menu.revert_selected"), "document-revert-symbolic", self.revert_selected)
        add_item(i18n.t("toolbar.remove"), "list-remove-symbolic", self.remove_selected_rows)

        popover.set_child(box)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        popover.set_pointing_to(rect)
        popover.popup()

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
        self.column_view.set_reorderable(False)
        self.sort_model.set_sorter(self.column_view.get_sorter())
        self.column_view.add_css_class("track-table")

        cfg = config.load_config()
        cols_cfg = cfg.get("columns", {})
        col_order = cfg.get("column_order", config.DEFAULT_COLUMN_ORDER)

        for col_id in col_order:
            if col_id not in COLUMN_SPEC_MAP:
                continue
            _cid, label_key, resizable, center = COLUMN_SPEC_MAP[col_id]
            col_info = cols_cfg.get(col_id, {})
            def_info = config.DEFAULT_COLUMNS[col_id]
            width = col_info.get("width", def_info["width"])
            visible = col_info.get("visible", def_info["visible"])

            if col_id == "status":
                col = _make_status_column(fixed_width=width)
            else:
                col = _make_column(
                    title=i18n.t(label_key),
                    prop_name=col_id,
                    fixed_width=width,
                    resizable=resizable,
                    center=center,
                )

            col.set_id(col_id)
            col.set_fixed_width(width)
            col.set_visible(visible)
            col.set_expand(False)
            if resizable:
                col.connect("notify::fixed-width", self._on_column_width_changed)
            self._columns[col_id] = col
            self.column_view.append_column(col)

        columns_menu = self._setup_columns_menu()
        self._update_last_column_expand()
        self.column_view.get_columns().connect("items-changed", self._on_columns_model_changed)
        self._setup_track_list_context_menu()
        self._setup_column_drag_and_drop()

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

        self.btn_columns = Gtk.MenuButton()
        self.btn_columns.set_icon_name("view-more-symbolic")
        self.btn_columns.set_tooltip_text(i18n.t("column.menu_tooltip"))
        self.btn_columns.set_menu_model(columns_menu)
        self.btn_columns.add_css_class("flat")
        bottom_bar.append(self.btn_columns)

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
        haystack = f"{item.title} {item.artist} {item.album} {item.filename}".lower()
        return self._search_query in haystack

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._search_query = entry.get_text().strip().lower()
        self.search_filter.changed(Gtk.FilterChange.DIFFERENT)

    # ---------- configuración de columnas ----------

    def _setup_columns_menu(self) -> Gio.Menu:
        menu = Gio.Menu()
        section = Gio.Menu()
        for col_id, label_key, _resizable, _center in COLUMN_SPEC:
            action_name = f"toggle_col_{col_id}"
            is_visible = self._columns[col_id].get_visible()
            action = Gio.SimpleAction.new_stateful(
                action_name,
                None,
                GLib.Variant.new_boolean(is_visible),
            )
            action.connect(
                "change-state",
                lambda act, val, cid=col_id: self._on_toggle_column(act, val, cid),
            )
            self.add_action(action)
            section.append(i18n.t(label_key), f"win.{action_name}")
        menu.append_section(None, section)

        reset_section = Gio.Menu()
        reset_action = Gio.SimpleAction.new("reset_column_widths", None)
        reset_action.connect("activate", lambda *_: self.reset_default_column_widths())
        self.add_action(reset_action)
        reset_section.append(i18n.t("column.reset_widths"), "win.reset_column_widths")
        menu.append_section(None, reset_section)

        for col in self._columns.values():
            col.set_header_menu(menu)

        return menu

    def _update_last_column_expand(self) -> None:
        """Asegura que la última columna visible tenga expand=True para que
        rellene todo el ancho restante del panel izquierdo hasta el borde,
        mientras que las anteriores tienen expand=False para que sus anchos
        sean fijos y redimensionables de forma independiente."""
        cols_model = self.column_view.get_columns()
        last_visible_col: Gtk.ColumnViewColumn | None = None

        for i in range(cols_model.get_n_items()):
            col = cols_model.get_item(i)
            if col.get_visible():
                last_visible_col = col

        for i in range(cols_model.get_n_items()):
            col = cols_model.get_item(i)
            should_expand = (col is last_visible_col)
            if col.get_expand() != should_expand:
                col.set_expand(should_expand)

    def _on_toggle_column(self, action: Gio.SimpleAction, new_state: GLib.Variant, col_id: str) -> None:
        target_visible = new_state.get_boolean()
        if not target_visible:
            visible_count = sum(1 for c in self._columns.values() if c.get_visible())
            if visible_count <= 1:
                return
        action.set_state(new_state)
        col = self._columns.get(col_id)
        if col:
            col.set_visible(target_visible)
            self._update_last_column_expand()
            self._save_column_config()

    def _on_columns_model_changed(self, model: Gio.ListModel, _position: int, _removed: int, _added: int) -> None:
        if getattr(self, "_reordering_columns", False):
            return
        if model.get_n_items() < len(self._columns):
            return
        self._update_last_column_expand()
        self._save_column_config()

    def _on_column_width_changed(self, _col: Gtk.ColumnViewColumn, _pspec) -> None:
        if self._column_save_timeout_id:
            GLib.source_remove(self._column_save_timeout_id)

        def do_save() -> bool:
            self._column_save_timeout_id = None
            self._save_column_config()
            return False

        self._column_save_timeout_id = GLib.timeout_add(400, do_save)

    def _save_column_config(self) -> None:
        cfg = config.load_config()
        cols_model = self.column_view.get_columns()
        order = []
        for i in range(cols_model.get_n_items()):
            col = cols_model.get_item(i)
            cid = col.get_id()
            if cid:
                order.append(cid)

        cols_cfg = {}
        for col_id, col in self._columns.items():
            cols_cfg[col_id] = {
                "visible": bool(col.get_visible()),
                "width": max(30, int(col.get_fixed_width())),
            }
        cfg["columns"] = cols_cfg
        if order:
            cfg["column_order"] = order
        config.save_config(cfg)

    def reset_default_column_widths(self) -> None:
        self._reordering_columns = True
        try:
            for target_idx, col_id in enumerate(config.DEFAULT_COLUMN_ORDER):
                col = self._columns.get(col_id)
                if not col:
                    continue
                cols_model = self.column_view.get_columns()
                current_idx = -1
                for i in range(cols_model.get_n_items()):
                    if cols_model.get_item(i) is col:
                        current_idx = i
                        break
                if current_idx != -1 and current_idx != target_idx:
                    self.column_view.remove_column(col)
                    self.column_view.insert_column(target_idx, col)

            for col_id, def_info in config.DEFAULT_COLUMNS.items():
                col = self._columns.get(col_id)
                if col:
                    col.set_fixed_width(def_info["width"])
                    col.set_visible(def_info["visible"])
                    action = self.lookup_action(f"toggle_col_{col_id}")
                    if action:
                        action.set_state(GLib.Variant.new_boolean(def_info["visible"]))
        finally:
            self._reordering_columns = False

        self._update_last_column_expand()
        self._save_column_config()

    def _setup_column_drag_and_drop(self) -> None:
        header = self.column_view.get_first_child()
        if not header:
            return

        gesture = Gtk.GestureDrag()
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        gesture.set_button(Gdk.BUTTON_PRIMARY)
        gesture.connect("drag-begin", self._on_col_drag_begin)
        gesture.connect("drag-update", self._on_col_drag_update)
        gesture.connect("drag-end", self._on_col_drag_end)
        gesture.connect("cancel", self._on_col_drag_cancel)
        header.add_controller(gesture)
        self._col_drag_gesture = gesture

    def _get_visible_column_title_items(self) -> list[tuple[int, Gtk.ColumnViewColumn, Gtk.Widget, Any]]:
        """Devuelve una lista de tuplas (índice_modelo, columna, widget_cabecera, límites)
        para todas las columnas actualmente visibles."""
        header = self.column_view.get_first_child()
        if not header:
            return []
        cols_model = self.column_view.get_columns()
        n_cols = cols_model.get_n_items()

        items: list[tuple[int, Gtk.ColumnViewColumn, Gtk.Widget, Any]] = []
        child = header.get_first_child()
        idx = 0
        while child and idx < n_cols:
            col = cols_model.get_item(idx)
            if col.get_visible() and child.get_visible():
                ok, bounds = child.compute_bounds(header)
                if ok:
                    items.append((idx, col, child, bounds))
            child = child.get_next_sibling()
            idx += 1
        return items

    def _clear_column_dnd_classes(self) -> None:
        """Limpia todas las clases visuales de arrastre de las cabeceras."""
        header = self.column_view.get_first_child()
        if not header:
            return
        child = header.get_first_child()
        while child:
            child.remove_css_class("dnd-dragging")
            child.remove_css_class("dnd-target-left")
            child.remove_css_class("dnd-target-right")
            child = child.get_next_sibling()

    def _on_col_drag_begin(self, gesture: Gtk.GestureDrag, start_x: float, start_y: float) -> None:
        self._col_dnd_source_idx = None
        self._col_dnd_source_col = None
        self._col_dnd_source_widget = None
        self._col_dnd_is_dragging = False
        self._col_dnd_target_info = None

        items = self._get_visible_column_title_items()
        if not items:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        clicked_item = None
        prev_item = None
        for i, item in enumerate(items):
            idx, col, widget, bounds = item
            bx = bounds.get_x()
            bw = bounds.get_width()
            if bx <= start_x < bx + bw:
                clicked_item = item
                prev_item = items[i - 1] if i > 0 else None
                break

        if not clicked_item:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        col_idx, col, widget, bounds = clicked_item

        # Si el usuario hace clic en el borde de redimensionado (8px a la derecha de una
        # columna redimensionable o 6px a la izquierda del divisor), denegamos
        # para que GTK gestione nativamente el redimensionado del ancho de columnas.
        bx = bounds.get_x()
        bw = bounds.get_width()
        if col.get_resizable() and (bx + bw - start_x) <= 8:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        if prev_item is not None and prev_item[1].get_resizable() and (start_x - bx) <= 6:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        # Clic en el cuerpo del botón de la columna: reclamamos la secuencia para gestionar
        # con total precisión tanto la ordenación al hacer clic como el arrastre DnD.
        self._col_dnd_source_idx = col_idx
        self._col_dnd_source_col = col
        self._col_dnd_source_widget = widget
        self._col_dnd_start_x = start_x
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def _on_col_drag_update(self, gesture: Gtk.GestureDrag, offset_x: float, offset_y: float) -> None:
        if self._col_dnd_source_col is None or self._col_dnd_source_widget is None:
            return

        # Se requiere un desplazamiento mínimo de 8px horizontal para activar el modo de arrastre
        if not self._col_dnd_is_dragging:
            if abs(offset_x) >= 8:
                self._col_dnd_is_dragging = True
                self._col_dnd_source_widget.add_css_class("dnd-dragging")
                header = self.column_view.get_first_child()
                if header:
                    header.set_cursor_from_name("grabbing")
            else:
                return

        items = self._get_visible_column_title_items()
        if not items:
            return

        current_x = self._col_dnd_start_x + offset_x

        first_item = items[0]
        last_item = items[-1]

        target_idx = None
        target_col = None
        target_widget = None
        target_side = "left"

        if current_x <= first_item[3].get_x():
            target_idx, target_col, target_widget, _ = first_item
            target_side = "left"
        elif current_x >= (last_item[3].get_x() + last_item[3].get_width()):
            target_idx, target_col, target_widget, _ = last_item
            target_side = "right"
        else:
            for item in items:
                idx, col, widget, bounds = item
                bx = bounds.get_x()
                bw = bounds.get_width()
                if bx <= current_x <= bx + bw:
                    target_idx = idx
                    target_col = col
                    target_widget = widget
                    mid = bx + bw / 2.0
                    target_side = "left" if current_x < mid else "right"
                    break

        # Actualizar clases de indicador de destino
        header = self.column_view.get_first_child()
        if header:
            child = header.get_first_child()
            while child:
                if child != self._col_dnd_source_widget:
                    child.remove_css_class("dnd-target-left")
                    child.remove_css_class("dnd-target-right")
                child = child.get_next_sibling()

        if target_widget and target_col is not None and target_idx is not None:
            self._col_dnd_target_info = (target_idx, target_col, target_side)
            if target_widget != self._col_dnd_source_widget:
                target_widget.add_css_class(f"dnd-target-{target_side}")
        else:
            self._col_dnd_target_info = None

    def _on_col_drag_end(self, gesture: Gtk.GestureDrag, offset_x: float, offset_y: float) -> None:
        header = self.column_view.get_first_child()
        if header:
            header.set_cursor(None)
        self._clear_column_dnd_classes()

        source_col = self._col_dnd_source_col
        source_idx = self._col_dnd_source_idx
        is_dragging = self._col_dnd_is_dragging
        target_info = self._col_dnd_target_info

        self._col_dnd_source_idx = None
        self._col_dnd_source_col = None
        self._col_dnd_source_widget = None
        self._col_dnd_is_dragging = False
        self._col_dnd_target_info = None
        self._col_dnd_start_x = 0.0

        if source_col is None or source_idx is None:
            return

        if not is_dragging:
            # Clic simple: ordenación de columna
            self._on_column_header_clicked(source_col)
        else:
            # Arrastre completado: reordenar columnas
            if target_info:
                target_idx, target_col, target_side = target_info
                self._reorder_column(source_idx, source_col, target_idx, target_col, target_side)

    def _on_col_drag_cancel(self, _gesture: Gtk.GestureDrag, _sequence) -> None:
        header = self.column_view.get_first_child()
        if header:
            header.set_cursor(None)
        self._clear_column_dnd_classes()
        self._col_dnd_source_idx = None
        self._col_dnd_source_col = None
        self._col_dnd_source_widget = None
        self._col_dnd_is_dragging = False
        self._col_dnd_target_info = None
        self._col_dnd_start_x = 0.0

    def _on_column_header_clicked(self, col: Gtk.ColumnViewColumn) -> None:
        if not col.get_sorter():
            return
        sorter = self.column_view.get_sorter()
        if sorter.get_primary_sort_column() == col:
            order = sorter.get_primary_sort_order()
            new_order = Gtk.SortType.DESCENDING if order == Gtk.SortType.ASCENDING else Gtk.SortType.ASCENDING
        else:
            new_order = Gtk.SortType.ASCENDING
        self.column_view.sort_by_column(col, new_order)

    def _reorder_column(
        self,
        source_idx: int,
        source_col: Gtk.ColumnViewColumn,
        target_idx: int,
        target_col: Gtk.ColumnViewColumn,
        target_side: str,
    ) -> None:
        if source_col is target_col:
            return

        if source_idx < target_idx:
            adj_target_idx = target_idx - 1
        else:
            adj_target_idx = target_idx
        insert_pos = adj_target_idx if target_side == "left" else adj_target_idx + 1

        if insert_pos == source_idx:
            return

        self._reordering_columns = True
        try:
            self.column_view.remove_column(source_col)
            self.column_view.insert_column(insert_pos, source_col)
        finally:
            self._reordering_columns = False

        self._update_last_column_expand()
        self._save_column_config()


    def _save_window_state(self) -> None:
        cfg = config.load_config()
        cfg["window_width"] = self.get_width()
        cfg["window_height"] = self.get_height()
        cfg["window_maximized"] = self.is_maximized()
        config.save_config(cfg)

    def _build_body(self) -> Gtk.Widget:
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_wide_handle(True)
        self.paned.set_position(DEFAULT_WINDOW_WIDTH - RIGHT_PANEL_WIDTH)
        self.paned.set_margin_top(12)
        self.paned.set_margin_bottom(12)
        self.paned.set_margin_start(12)
        self.paned.set_margin_end(12)

        self.paned.set_start_child(self._build_track_list_panel())
        self.paned.set_resize_start_child(True)

        # Panel lateral unificado: carátula arriba (ancla visual), editor de tags abajo
        side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        side_box.set_margin_top(4)
        side_box.set_margin_bottom(8)
        side_box.set_margin_start(8)
        side_box.set_margin_end(8)

        self.cover_panel = CoverPanel()
        self.cover_panel.connect("cover-change-requested", self._on_cover_change_requested)
        self.cover_panel.connect("cover-resize-each-requested", self._on_cover_resize_each_requested)
        self.cover_panel.connect("cover-remove-requested", self._on_cover_remove_requested)
        self.cover_panel.connect("musicbrainz-search-requested", self._on_musicbrainz_search_requested)
        side_box.append(self.cover_panel)

        self.tag_editor = TagEditor()
        self.tag_editor.connect("changes-requested", self._on_tag_changes_requested)
        side_box.append(self.tag_editor)

        # Espaciador para absorber el exceso vertical en pantallas altas y evitar estiramientos
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        side_box.append(spacer)

        side_scroller = Gtk.ScrolledWindow()
        side_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        side_scroller.set_child(side_box)
        side_scroller.set_size_request(260, -1)
        self.paned.set_end_child(side_scroller)
        self.paned.set_resize_end_child(False)

        return self.paned

    def _adjust_initial_paned_position(self) -> bool:
        width = self.paned.get_width()
        if width > RIGHT_PANEL_WIDTH + 200:
            self.paned.set_position(width - RIGHT_PANEL_WIDTH)
        return False

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
        for root, dirs, files in os.walk(folder):
            dirs.sort(key=natural_sort_key)
            for name in sorted(files, key=natural_sort_key):
                if name.lower().endswith(SUPPORTED_EXTENSIONS):
                    found.append(os.path.join(root, name))
        return found

    _find_flac_files = _find_audio_files

    def add_paths(self, paths: list[str]) -> None:
        paths = sorted(paths, key=natural_sort_key)
        existing = {t.path for t in self.tracks}
        errors = []
        new_tracks = []
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
            new_tracks.append(track)
            added += 1

        if errors:
            self._show_message(i18n.t("dialog.load_errors_title"), "\n".join(errors))
        self._toast(i18n.t("toast.files_added", added=added, total=len(self.tracks)))

        if added and self.selection_model.get_selection().get_size() == 0:
            self.selection_model.select_item(0, True)

        if self.tracks:
            self.main_stack.set_visible_child_name("editor")
            GLib.idle_add(self._adjust_initial_paned_position)
        self._update_list_status()
        self._update_title_state()

        if new_tracks and config.load_config().get("check_integrity_on_import", True):
            threading.Thread(
                target=self._check_integrity_worker,
                args=(new_tracks,),
                daemon=True,
            ).start()

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
        zero_pad = config.load_config().get("autonumber_zero_padding", False)
        for index, track in enumerate(tracks, start=1):
            num_str = f"{index:02d}" if zero_pad else str(index)
            track.set_tag("TRACKNUMBER", num_str)
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(self._selected_tracks())
        self._update_title_state()
        self._toast(i18n.t("toast.autonumbered", n=len(tracks)))

    def revert_all_or_selected(self) -> None:
        selected = [t for t in self._selected_tracks() if t.is_dirty]
        target_tracks = selected if selected else [t for t in self.tracks if t.is_dirty]
        if not target_tracks:
            return
        for track in target_tracks:
            track.revert()
            self._refresh_row_for_track(track)
        self.tag_editor.set_tracks(self._selected_tracks())
        self.cover_panel.set_tracks(self._selected_tracks())
        self._update_title_state()
        self._toast(i18n.t("toast.reverted", n=len(target_tracks)))

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

    def _check_integrity_worker(self, tracks: list[AudioTrack]) -> None:
        corrupted = []
        for track in tracks:
            if track not in self.tracks:
                continue
            if not track.path.lower().endswith((".flac", ".mp3")):
                continue
            ok, message = integrity.check_integrity(track.path)
            if not ok:
                track.integrity_error = message
                corrupted.append((track, message))
                GLib.idle_add(self._on_track_integrity_updated, track)
            else:
                if track.integrity_error:
                    track.integrity_error = None
                    GLib.idle_add(self._on_track_integrity_updated, track)

        if corrupted:
            GLib.idle_add(self._notify_integrity_problems, corrupted)

    def _on_track_integrity_updated(self, track: AudioTrack) -> None:
        if track in self.tracks:
            try:
                idx = self.tracks.index(track)
                item = self.list_store.get_item(idx)
                if item:
                    item.notify("integrity-error")
                    item.notify("status-sort-key")
                    item.notify("missing-fields")
            except (ValueError, IndexError):
                pass

    def _notify_integrity_problems(self, corrupted: list[tuple[AudioTrack, str]]) -> None:
        lines = [f"• {t.filename}: {msg}" for t, msg in corrupted]
        summary = i18n.t("integrity.problems_found_desc", n=len(corrupted))
        self._show_message(i18n.t("integrity.problems_title"), f"{summary}\n\n" + "\n".join(lines))

    def identify_selected_by_fingerprint(self) -> None:
        tracks = self._selected_tracks()
        if not tracks:
            return
        if not acoustid.fpcalc_available():
            self._show_message(i18n.t("fingerprint.title"), i18n.t("fingerprint.fpcalc_missing"))
            return

        if len(tracks) == 1:
            track = tracks[0]
            dialog = FingerprintDialog(track.path)
            dialog.connect("match-chosen", self._on_fingerprint_match_chosen, track)
            dialog.present(self)
        else:
            dialog = BatchFingerprintDialog(tracks)
            dialog.connect("matches-applied", self._on_batch_fingerprint_applied)
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

    def _on_batch_fingerprint_applied(self, _dialog, results: list[tuple[AudioTrack, dict]]) -> None:
        count = 0
        for track, match in results:
            if match.get("title"):
                track.set_tag("TITLE", match["title"])
            if match.get("artist"):
                track.set_tag("ARTIST", match["artist"])
            if match.get("album"):
                track.set_tag("ALBUM", match["album"])
            self._refresh_row_for_track(track)
            count += 1
        self.tag_editor.set_tracks(self._selected_tracks())
        self._update_title_state()
        self._toast(i18n.t("fingerprint.batch_applied", n=count))

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
            self.btn_revert.set_sensitive(True)
        else:
            if self.tracks:
                self.window_title.set_subtitle(i18n.t("list.status_summary", total=len(self.tracks)))
            else:
                self.window_title.set_subtitle("")
            self.btn_save.set_sensitive(False)
            self.btn_revert.set_sensitive(False)

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
        if self._column_save_timeout_id:
            GLib.source_remove(self._column_save_timeout_id)
            self._column_save_timeout_id = None
            self._save_column_config()
        self._save_window_state()
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
