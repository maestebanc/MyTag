"""Panel de previsualización y edición de la portada del álbum (GTK4/Adwaita).

Cada acción (elegir imagen, redimensionar, quitar) se aplica de inmediato a
los temas seleccionados (en memoria); "Guardar cambios" en la ventana
principal es lo único que escribe a disco.

Las acciones sobre la portada viven en su menú contextual (clic derecho sobre
la imagen, o el botón de menú superpuesto "⋮"). Debajo de la carátula se muestra
únicamente el tamaño actual en píxeles.
"""
from __future__ import annotations

import os
import re
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk, Pango

from .. import i18n
from ..constants import COVER_SIZE
from ..cover_utils import read_image_file, resize_image_bytes
from .resize_cover_dialog import ResizeCoverDialog

MAX_PREVIEW_TEXTURE_SIZE = 1000
IMAGE_MIME_TYPES = ("image/png", "image/jpeg", "image/bmp", "image/webp")


class AspectRatioBox(Gtk.Widget):
    """Contenedor que mantiene a su hijo en proporción cuadrada 1:1

    adaptándose al ancho completo de la columna.
    """
    __gtype_name__ = "MyTagAspectRatioBox"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._child: Gtk.Widget | None = None

    def set_child(self, child: Gtk.Widget | None) -> None:
        if self._child:
            self._child.unparent()
        self._child = child
        if child:
            child.set_parent(self)

    def get_child(self) -> Gtk.Widget | None:
        return self._child

    def do_dispose(self) -> None:
        if self._child:
            self._child.unparent()
            self._child = None
        Gtk.Widget.do_dispose(self)

    def do_get_request_mode(self) -> Gtk.SizeRequestMode:
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_measure(self, orientation: Gtk.Orientation, for_size: int) -> tuple[int, int, int, int]:
        if orientation == Gtk.Orientation.HORIZONTAL:
            if self._child:
                c_min, c_nat, _, _ = self._child.measure(orientation, for_size)
                return max(80, c_min), max(260, c_nat), -1, -1
            return 80, 260, -1, -1
        else:
            if for_size > 0:
                return for_size, for_size, -1, -1
            return 260, 260, -1, -1

    def do_size_allocate(self, width: int, height: int, baseline: int) -> None:
        if self._child:
            self._child.allocate(width, width, baseline, None)


class CoverPanel(Gtk.Box):
    __gtype_name__ = "MyTagCoverPanel"

    __gsignals__ = {
        "cover-change-requested": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
        "cover-resize-each-requested": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "cover-remove-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "musicbrainz-search-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_valign(Gtk.Align.START)
        self.set_hexpand(True)
        self._tracks = []
        self._current_width = 0
        self._current_height = 0
        self._current_cover_bytes: bytes | None = None
        self._has_different_covers = False
        self._context_popover: Gtk.Popover | None = None

        self.aspect_box = AspectRatioBox()
        self.aspect_box.set_hexpand(True)

        overlay = Gtk.Overlay()
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        self.aspect_box.set_child(overlay)

        self.frame = Gtk.Frame()
        self.frame.add_css_class("card")
        self.frame.add_css_class("album-cover-frame")
        self.frame.set_overflow(Gtk.Overflow.HIDDEN)
        self.frame.set_hexpand(True)
        self.frame.set_vexpand(True)
        overlay.set_child(self.frame)

        self.picture = Gtk.Picture()
        self.picture.set_can_shrink(True)
        self.picture.set_content_fit(Gtk.ContentFit.COVER)
        self.picture.set_hexpand(True)
        self.picture.set_vexpand(True)

        self.placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.placeholder_box.add_css_class("album-cover-placeholder")
        self.placeholder_box.set_hexpand(True)
        self.placeholder_box.set_vexpand(True)
        self.placeholder_box.set_margin_start(8)
        self.placeholder_box.set_margin_end(8)
        self.placeholder_box.set_margin_top(8)
        self.placeholder_box.set_margin_bottom(8)

        placeholder_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        placeholder_inner.set_valign(Gtk.Align.CENTER)
        placeholder_inner.set_halign(Gtk.Align.CENTER)
        placeholder_inner.set_vexpand(True)
        placeholder_inner.set_hexpand(True)

        self.placeholder_icon = Gtk.Image.new_from_icon_name("media-optical-cd-symbolic")
        self.placeholder_icon.set_pixel_size(44)
        self.placeholder_icon.add_css_class("dim-label")
        placeholder_inner.append(self.placeholder_icon)

        self.placeholder_label = Gtk.Label(label=i18n.t("cover.no_cover"))
        self.placeholder_label.add_css_class("dim-label")
        self.placeholder_label.add_css_class("caption")
        placeholder_inner.append(self.placeholder_label)

        self.placeholder_sublabel = Gtk.Label(label=i18n.t("cover.drag_hint"))
        self.placeholder_sublabel.add_css_class("dim-label")
        self.placeholder_sublabel.add_css_class("caption")
        self.placeholder_sublabel.set_wrap(True)
        self.placeholder_sublabel.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.placeholder_sublabel.set_max_width_chars(20)
        self.placeholder_sublabel.set_justify(Gtk.Justification.CENTER)
        placeholder_inner.append(self.placeholder_sublabel)

        self.placeholder_box.append(placeholder_inner)

        # Clic principal en el placeholder abre el selector de imagen
        placeholder_click = Gtk.GestureClick()
        placeholder_click.set_button(Gdk.BUTTON_PRIMARY)
        placeholder_click.connect("pressed", lambda *_a: self._on_select_image(None))
        self.placeholder_box.add_controller(placeholder_click)

        self._stack = Gtk.Stack()
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)
        self._stack.add_named(self.placeholder_box, "placeholder")
        self._stack.add_named(self.picture, "picture")
        self.frame.set_child(self._stack)

        self.btn_overlay_menu = Gtk.MenuButton()
        self.btn_overlay_menu.set_icon_name("view-more-symbolic")
        self.btn_overlay_menu.add_css_class("osd")
        self.btn_overlay_menu.add_css_class("circular")
        self.btn_overlay_menu.add_css_class("cover-overlay-btn")
        self.btn_overlay_menu.set_halign(Gtk.Align.END)
        self.btn_overlay_menu.set_valign(Gtk.Align.START)
        self.btn_overlay_menu.set_margin_top(6)
        self.btn_overlay_menu.set_margin_end(6)
        self.btn_overlay_menu.set_popover(self._build_actions_popover())
        overlay.add_overlay(self.btn_overlay_menu)
        self.append(self.aspect_box)

        self._setup_context_menu()
        self._setup_drop_target()

        # Texto discreto bajo la portada con el tamaño actual de la imagen (editable inline)
        self.size_label = Gtk.EditableLabel()
        self.size_label.add_css_class("dim-label")
        self.size_label.add_css_class("caption")
        self.size_label.add_css_class("cover-size-label")
        self.size_label.set_halign(Gtk.Align.CENTER)
        self.size_label.set_margin_top(2)
        self.size_label.set_cursor_from_name("text")
        self.size_label.connect("notify::editing", self._on_size_label_editing_changed)
        self.append(self.size_label)

        self.set_tracks([])

    def _build_actions_popover(self) -> Gtk.Popover:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, icon_name: str, callback, destructive: bool = False, sensitive: bool = True) -> None:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            if destructive:
                btn.add_css_class("destructive-action")
            btn.set_sensitive(sensitive)
            ibox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ibox.set_margin_start(4)
            ibox.set_margin_end(4)
            ibox.set_margin_top(2)
            ibox.set_margin_bottom(2)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.add_css_class("dim-label")
            lbl = Gtk.Label(label=label, xalign=0)
            lbl.set_hexpand(True)
            ibox.append(icon)
            ibox.append(lbl)
            btn.set_child(ibox)
            btn.connect("clicked", lambda _b: (callback(), popover.popdown()))
            box.append(btn)

        has_tracks = bool(self._tracks)
        has_cover = any(t.get_cover_bytes() is not None for t in self._tracks) if self._tracks else False

        add_item(i18n.t("cover.select_image"), "document-open-symbolic", lambda: self._on_select_image(None), sensitive=has_tracks)
        add_item(i18n.t("cover.paste"), "edit-paste-symbolic", lambda: self._on_paste(None), sensitive=has_tracks)
        add_item(i18n.t("cover.copy"), "edit-copy-symbolic", self._on_copy, sensitive=has_cover)
        add_item(i18n.t("cover.export"), "document-save-as-symbolic", self._on_export, sensitive=has_cover)
        add_item(i18n.t("cover.musicbrainz_search"), "system-search-symbolic", lambda: self.emit("musicbrainz-search-requested"), sensitive=has_tracks)
        add_item(i18n.t("cover.resize_action"), "image-crop-symbolic", self._open_resize_dialog, sensitive=has_cover)
        box.append(Gtk.Separator())
        add_item(i18n.t("cover.remove"), "user-trash-symbolic", lambda: self._on_remove(None), destructive=True, sensitive=has_cover)

        popover.set_child(box)
        return popover

    def _setup_context_menu(self) -> None:
        gesture = Gtk.GestureClick()
        gesture.set_button(Gdk.BUTTON_SECONDARY)
        gesture.connect("pressed", self._on_secondary_click)
        self.frame.add_controller(gesture)

    def _on_secondary_click(self, _gesture, _n_press, x: float, y: float) -> None:
        if not self._tracks:
            return
        if self._context_popover is not None:
            self._context_popover.popdown()
            self._context_popover.unparent()
            self._context_popover = None

        popover = self._build_actions_popover()
        popover.set_parent(self.frame)
        popover.set_has_arrow(False)
        self._context_popover = popover

        def _on_closed(p):
            if self._context_popover == p:
                self._context_popover = None
            p.unparent()

        popover.connect("closed", _on_closed)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        popover.set_pointing_to(rect)
        popover.popup()

    def _setup_drop_target(self) -> None:
        actions = Gdk.DragAction.COPY | Gdk.DragAction.MOVE
        target_file = Gtk.DropTarget.new(Gio.File, actions)
        target_file.connect("drop", self._on_drop)
        target_file.connect("enter", self._on_drop_enter)
        target_file.connect("leave", self._on_drop_leave)
        self.frame.add_controller(target_file)

        target_filelist = Gtk.DropTarget.new(Gdk.FileList, actions)
        target_filelist.connect("drop", self._on_drop)
        target_filelist.connect("enter", self._on_drop_enter)
        target_filelist.connect("leave", self._on_drop_leave)
        self.frame.add_controller(target_filelist)

        target_texture = Gtk.DropTarget.new(Gdk.Texture, actions)
        target_texture.connect("drop", self._on_drop)
        target_texture.connect("enter", self._on_drop_enter)
        target_texture.connect("leave", self._on_drop_leave)
        self.frame.add_controller(target_texture)

    def _on_drop_enter(self, *_args) -> int:
        if self._tracks:
            self.frame.add_css_class("drop-highlight")
        return Gdk.DragAction.COPY | Gdk.DragAction.MOVE

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
        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            if files:
                path = files[0].get_path()
                if path:
                    data, mime = read_image_file(path)
                    self.emit("cover-change-requested", data, mime)
                    return True
            return False
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
        self.btn_overlay_menu.set_sensitive(enabled)
        self._refresh_preview()
        self.btn_overlay_menu.set_popover(self._build_actions_popover())

    def _refresh_preview(self) -> None:
        if not self._tracks:
            self._show_placeholder(i18n.t("cover.no_tracks_loaded"))
            self.size_label.set_text("")
            self.size_label.set_visible(False)
            self.size_label.set_editable(False)
            self.size_label.set_tooltip_text(None)
            self._current_cover_bytes = None
            self._current_width = 0
            self._current_height = 0
            self._has_different_covers = False
            return

        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            data = next(iter(covers))
            if data is None:
                self._show_placeholder(i18n.t("cover.no_cover"))
                self.size_label.set_text("")
                self.size_label.set_visible(False)
                self.size_label.set_editable(False)
                self.size_label.set_tooltip_text(None)
                self._current_cover_bytes = None
                self._current_width = 0
                self._current_height = 0
                self._has_different_covers = False
            else:
                self._show_bytes(data)
                w, h = self._pixbuf_size(data)
                self._current_cover_bytes = data
                self._current_width = w
                self._current_height = h
                self._has_different_covers = False
                self.size_label.set_text(f"{w} × {h} px")
                self.size_label.set_visible(True)
                self.size_label.set_editable(True)
                self.size_label.set_tooltip_text(i18n.t("cover.edit_dimensions_tooltip"))
        else:
            self._show_placeholder(i18n.t("cover.multiple_covers"))
            self._current_cover_bytes = None
            self._has_different_covers = any(c is not None for c in covers)
            self._current_width = COVER_SIZE[0]
            self._current_height = COVER_SIZE[1]
            self.size_label.set_text(i18n.t("cover.tracks_selected_count", n=len(self._tracks)))
            self.size_label.set_visible(True)
            self.size_label.set_editable(False)
            self.size_label.set_tooltip_text(None)

    def _on_size_label_editing_changed(self, widget: Gtk.EditableLabel, _pspec) -> None:
        if not self._tracks or self._current_cover_bytes is None:
            return

        is_editing = widget.get_property("editing")
        if is_editing:
            # Al entrar en modo edición: muestra el ancho si es cuadrada (ej: 500) o "800 × 600"
            if self._current_width == self._current_height:
                edit_text = str(self._current_width)
            else:
                edit_text = f"{self._current_width} × {self._current_height}"
            widget.set_text(edit_text)
            GLib.idle_add(lambda: widget.select_region(0, -1) or False)
        else:
            entered = widget.get_text().strip()
            self._parse_and_apply_dimension(entered)

    def _parse_and_apply_dimension(self, text: str) -> None:
        orig_w = self._current_width
        orig_h = self._current_height
        reset_label = f"{orig_w} × {orig_h} px"

        if not text or orig_w <= 0 or orig_h <= 0:
            self.size_label.set_text(reset_label)
            return

        clean = text.lower().replace("px", "").strip()
        nums = [int(n) for n in re.findall(r"\d+", clean)]
        if not nums:
            self.size_label.set_text(reset_label)
            return

        if len(nums) == 1:
            target_w = nums[0]
            target_h = max(1, round(target_w * orig_h / orig_w))
        else:
            cand_w, cand_h = nums[0], nums[1]
            if cand_w != orig_w and cand_h == orig_h:
                target_w = cand_w
                target_h = max(1, round(target_w * orig_h / orig_w))
            elif cand_h != orig_h and cand_w == orig_w:
                target_h = cand_h
                target_w = max(1, round(target_h * orig_w / orig_h))
            else:
                target_w = cand_w
                target_h = max(1, round(target_w * orig_h / orig_w))

        target_w = max(50, min(4000, target_w))
        target_h = max(50, min(4000, target_h))

        if target_w == orig_w and target_h == orig_h:
            self.size_label.set_text(reset_label)
            return

        self._apply_resize(target_w, target_h)

    def _apply_resize(self, width: int, height: int) -> None:
        if not self._tracks:
            return
        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            source = next(iter(covers))
            if source is not None:
                data, mime = resize_image_bytes(source, size=(width, height))
                self.emit("cover-change-requested", data, mime)
        elif any(c is not None for c in covers):
            self.emit("cover-resize-each-requested", width)

    def _show_placeholder(self, text: str) -> None:
        self.placeholder_label.set_text(text)
        self._stack.set_visible_child_name("placeholder")

    def _show_bytes(self, data: bytes) -> None:
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            w = pixbuf.get_width()
            h = pixbuf.get_height()
            if w > 0 and h > 0 and max(w, h) > MAX_PREVIEW_TEXTURE_SIZE:
                scale = MAX_PREVIEW_TEXTURE_SIZE / max(w, h)
                nw = max(1, int(w * scale))
                nh = max(1, int(h * scale))
                scaled = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
                texture = Gdk.Texture.new_for_pixbuf(scaled)
            else:
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

    def _open_resize_dialog(self) -> None:
        if not self._tracks:
            return
        root = self.get_root()
        dialog = ResizeCoverDialog(
            cover_bytes=self._current_cover_bytes,
            original_width=self._current_width,
            original_height=self._current_height,
            is_multiple=self._has_different_covers,
        )
        dialog.connect("resize-requested", self._on_resize_dialog_applied)
        dialog.present(root)

    def _on_resize_dialog_applied(self, _dialog, width: int, height: int) -> None:
        self._apply_resize(width, height)

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
            return
        png_bytes = texture.save_to_png_bytes()
        self.emit("cover-change-requested", png_bytes.get_data(), "image/png")

    def _on_remove(self, _button) -> None:
        if not self._tracks:
            return
        self.emit("cover-remove-requested")

    def _on_copy(self) -> None:
        data = self._current_cover_bytes
        if not data and self._tracks:
            data = next((t.get_cover_bytes() for t in self._tracks if t.get_cover_bytes() is not None), None)
        if not data:
            return

        try:
            gbytes = GLib.Bytes.new(data)
            texture = Gdk.Texture.new_from_bytes(gbytes)
        except Exception:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            if pixbuf:
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            else:
                return

        clipboard = self.get_clipboard()
        clipboard.set(texture)
        root = self.get_root()
        if root and hasattr(root, "_toast"):
            root._toast(i18n.t("cover.copied_to_clipboard"))

    def _on_export(self) -> None:
        data = self._current_cover_bytes
        if not data and self._tracks:
            data = next((t.get_cover_bytes() for t in self._tracks if t.get_cover_bytes() is not None), None)
        if not data:
            return

        dialog = Gtk.FileDialog(title=i18n.t("cover.export_dialog_title"))

        ext = ".jpg"
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = ".png"
        elif data.startswith(b"RIFF") and b"WEBP" in data[:16]:
            ext = ".webp"

        dialog.set_initial_name(f"cover{ext}")

        if self._tracks and self._tracks[0].path:
            track_dir = os.path.dirname(self._tracks[0].path)
            if os.path.isdir(track_dir):
                dialog.set_initial_folder(Gio.File.new_for_path(track_dir))

        filter_images = Gtk.FileFilter()
        filter_images.set_name(i18n.t("cover.images_filter_name"))
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            filter_images.add_pattern(pattern)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)

        root = self.get_root()
        dialog.save(root, None, lambda d, res, cdata=data: self._on_export_cover_finished(d, res, cdata))

    def _on_export_cover_finished(self, dialog: Gtk.FileDialog, result, data: bytes) -> None:
        try:
            gfile = dialog.save_finish(result)
        except GLib.Error:
            return
        if gfile is None:
            return
        path = gfile.get_path()
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(data)
            root = self.get_root()
            if root and hasattr(root, "_toast"):
                root._toast(i18n.t("cover.exported_success", name=os.path.basename(path)))
        except OSError as err:
            root = self.get_root()
            if root and hasattr(root, "_show_message"):
                root._show_message(i18n.t("cover.export_error_title"), str(err))

