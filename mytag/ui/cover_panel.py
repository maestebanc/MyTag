"""Panel de previsualización y edición de la portada del álbum (GTK4/Adwaita).

Cada acción (elegir imagen, redimensionar, quitar) se aplica de inmediato a
los temas seleccionados (en memoria); "Guardar cambios" en la ventana
principal es lo único que escribe a disco.

Las acciones menos frecuentes (pegar, buscar en MusicBrainz, quitar) viven
en un menú contextual sobre la propia portada (clic derecho, o el botón
"⋮" superpuesto para quien no piense en el clic derecho).
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk

from .. import i18n
from ..constants import COVER_SIZE
from ..cover_utils import read_image_file, resize_image_bytes

PREVIEW_SIZE = 260
IMAGE_MIME_TYPES = ("image/png", "image/jpeg", "image/bmp", "image/webp")


class CoverPanel(Gtk.Box):
    __gtype_name__ = "MyTagCoverPanel"

    __gsignals__ = {
        "cover-change-requested": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
        "cover-remove-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "musicbrainz-search-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._tracks = []

        self.frame = Gtk.Frame()
        self.frame.add_css_class("card")
        self.frame.set_halign(Gtk.Align.CENTER)
        self.picture = Gtk.Picture()
        self.picture.set_content_fit(Gtk.ContentFit.COVER)
        self.picture.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)
        self.placeholder = Gtk.Label(label=i18n.t("cover.no_cover"))
        self.placeholder.add_css_class("dim-label")

        self._stack = Gtk.Stack()
        self._stack.add_named(self.placeholder, "placeholder")
        self._stack.add_named(self.picture, "picture")
        self._stack.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)
        self.frame.set_child(self._stack)

        overlay = Gtk.Overlay()
        overlay.set_child(self.frame)
        overlay.set_halign(Gtk.Align.CENTER)

        self.btn_overlay_menu = Gtk.MenuButton()
        self.btn_overlay_menu.set_icon_name("view-more-symbolic")
        self.btn_overlay_menu.add_css_class("osd")
        self.btn_overlay_menu.add_css_class("circular")
        self.btn_overlay_menu.set_halign(Gtk.Align.END)
        self.btn_overlay_menu.set_valign(Gtk.Align.START)
        self.btn_overlay_menu.set_margin_top(6)
        self.btn_overlay_menu.set_margin_end(6)
        self.btn_overlay_menu.set_popover(self._build_actions_popover())
        overlay.add_overlay(self.btn_overlay_menu)
        self.append(overlay)

        self._setup_context_menu()
        self._setup_drop_target()

        self.info_label = Gtk.Label(label="")
        self.info_label.add_css_class("dim-label")
        self.info_label.add_css_class("caption")
        self.info_label.set_wrap(True)
        self.info_label.set_justify(Gtk.Justification.CENTER)
        self.append(self.info_label)

        self.btn_select = Gtk.Button(label=i18n.t("cover.select_image"))
        self.btn_select.connect("clicked", self._on_select_image)
        self.append(self.btn_select)

        self.size_row = Adw.SpinRow(
            title=i18n.t("cover.size_label"),
            adjustment=Gtk.Adjustment(value=COVER_SIZE[0], lower=16, upper=4000, step_increment=10, page_increment=100),
        )
        self.size_row.set_digits(0)
        self.size_row.set_numeric(True)
        size_listbox = Gtk.ListBox()
        size_listbox.add_css_class("boxed-list")
        size_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        size_listbox.append(self.size_row)
        self.append(size_listbox)

        self.btn_resize = Gtk.Button(label=i18n.t("cover.resize"))
        self.btn_resize.connect("clicked", self._on_resize)
        self.append(self.btn_resize)

        self.set_tracks([])

    def _build_actions_popover(self) -> Gtk.Popover:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, callback, destructive: bool = False) -> None:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            if destructive:
                btn.add_css_class("destructive-action")
            btn.get_child().set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        add_item(i18n.t("cover.paste"), lambda: self._on_paste(None))
        add_item(i18n.t("cover.musicbrainz_search"), lambda: self.emit("musicbrainz-search-requested"))
        add_item(i18n.t("cover.remove"), lambda: self._on_remove(None), destructive=True)

        popover.set_child(box)
        return popover

    def _setup_context_menu(self) -> None:
        self._context_popover = self._build_actions_popover()
        self._context_popover.set_parent(self.frame)
        self._context_popover.set_has_arrow(False)

        gesture = Gtk.GestureClick()
        gesture.set_button(Gdk.BUTTON_SECONDARY)
        gesture.connect("pressed", self._on_secondary_click)
        self.frame.add_controller(gesture)

    def _on_secondary_click(self, _gesture, _n_press, x: float, y: float) -> None:
        if not self._tracks:
            return
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        self._context_popover.set_pointing_to(rect)
        self._context_popover.popup()

    def _setup_drop_target(self) -> None:
        target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        target.set_gtypes([Gio.File, Gdk.Texture])
        target.connect("drop", self._on_drop)
        target.connect("enter", self._on_drop_enter)
        target.connect("leave", self._on_drop_leave)
        self.frame.add_controller(target)

    def _on_drop_enter(self, *_args) -> int:
        if self._tracks:
            self.frame.add_css_class("drop-highlight")
        return Gdk.DragAction.COPY

    def _on_drop_leave(self, *_args) -> None:
        self.frame.remove_css_class("drop-highlight")

    def _on_drop(self, _target, value, _x, _y) -> bool:
        self.frame.remove_css_class("drop-highlight")
        if not self._tracks:
            return False
        if isinstance(value, Gdk.Texture):
            png_bytes = value.save_to_png_bytes()
            self.emit("cover-change-requested", png_bytes.get_data(), "image/png")
            return True
        if isinstance(value, Gio.File):
            path = value.get_path()
            if path:
                data, mime = read_image_file(path)
                self.emit("cover-change-requested", data, mime)
                return True
        return False

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        enabled = bool(tracks)
        self.btn_select.set_sensitive(enabled)
        self.btn_overlay_menu.set_sensitive(enabled)
        self.size_row.set_sensitive(enabled)
        self.btn_resize.set_sensitive(enabled)
        self._refresh_preview()

    # ---------- helpers internos ----------

    def _refresh_preview(self) -> None:
        if not self._tracks:
            self._show_placeholder(i18n.t("cover.no_tracks_loaded"))
            self.info_label.set_text("")
            return

        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            data = next(iter(covers))
            if data is None:
                self._show_placeholder(i18n.t("cover.no_cover"))
                self.info_label.set_text("")
            else:
                self._show_bytes(data)
                w, h = self._pixbuf_size(data)
                self.info_label.set_text(f"{w}×{h}px")
        else:
            self._show_placeholder(i18n.t("cover.multiple_covers"))
            self.info_label.set_text(i18n.t("cover.tracks_selected_count", n=len(self._tracks)))

    def _show_placeholder(self, text: str) -> None:
        self.placeholder.set_text(text)
        self._stack.set_visible_child_name("placeholder")

    def _show_bytes(self, data: bytes) -> None:
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.picture.set_paintable(texture)
            self._stack.set_visible_child_name("picture")
        except GLib.Error:
            self._show_placeholder(i18n.t("cover.invalid_image"))

    @staticmethod
    def _pixbuf_size(data: bytes) -> tuple[int, int]:
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        return pixbuf.get_width(), pixbuf.get_height()

    # ---------- acciones ----------

    def _on_select_image(self, _button) -> None:
        dialog = Gtk.FileDialog(title=i18n.t("cover.select_dialog_title"))
        filter_images = Gtk.FileFilter()
        filter_images.set_name(i18n.t("cover.images_filter_name"))
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"):
            filter_images.add_pattern(pattern)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)

        root = self.get_root()
        dialog.open(root, None, self._on_select_image_finished)

    def _on_select_image_finished(self, dialog, result) -> None:
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        if gfile is None or not self._tracks:
            return
        path = gfile.get_path()
        if not path:
            return
        data, mime = read_image_file(path)
        self.emit("cover-change-requested", data, mime)

    def _on_paste(self, _button) -> None:
        if not self._tracks:
            return
        clipboard = self.get_clipboard()
        clipboard.read_texture_async(None, self._on_paste_texture_ready)

    def _on_paste_texture_ready(self, clipboard: Gdk.Clipboard, result) -> None:
        try:
            texture = clipboard.read_texture_finish(result)
        except GLib.Error:
            texture = None
        if texture is None:
            self.info_label.set_text(i18n.t("cover.paste_no_image"))
            return
        png_bytes = texture.save_to_png_bytes()
        self.emit("cover-change-requested", png_bytes.get_data(), "image/png")

    def _on_resize(self, _button) -> None:
        if not self._tracks:
            return
        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) != 1:
            self.info_label.set_text(i18n.t("cover.different_covers_cant_resize"))
            return
        source = next(iter(covers))
        if source is None:
            self.info_label.set_text(i18n.t("cover.nothing_to_resize"))
            return
        size = int(self.size_row.get_value())
        data, mime = resize_image_bytes(source, size=(size, size))
        self.emit("cover-change-requested", data, mime)

    def _on_remove(self, _button) -> None:
        if not self._tracks:
            return
        self.emit("cover-remove-requested")
