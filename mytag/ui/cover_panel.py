"""Panel de previsualización y edición de la portada del álbum (GTK4/Adwaita)."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gdk, GdkPixbuf, Gio, GObject, Gtk

from ..cover_utils import read_image_file, resize_image_bytes

PREVIEW_SIZE = 260


class CoverPanel(Gtk.Box):
    __gtype_name__ = "MyTagCoverPanel"

    __gsignals__ = {
        "cover-change-requested": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
        "cover-remove-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._tracks = []
        self._pending_data: bytes | None = None
        self._pending_mime: str = "image/jpeg"

        frame = Gtk.Frame()
        frame.add_css_class("card")
        frame.set_halign(Gtk.Align.CENTER)
        self.picture = Gtk.Picture()
        self.picture.set_content_fit(Gtk.ContentFit.COVER)
        self.picture.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)
        self.placeholder = Gtk.Label(label="Sin portada")
        self.placeholder.add_css_class("dim-label")

        self._stack = Gtk.Stack()
        self._stack.add_named(self.placeholder, "placeholder")
        self._stack.add_named(self.picture, "picture")
        self._stack.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)
        frame.set_child(self._stack)
        self.append(frame)

        self.info_label = Gtk.Label(label="")
        self.info_label.add_css_class("dim-label")
        self.info_label.add_css_class("caption")
        self.append(self.info_label)

        btn_select = Gtk.Button(label="Seleccionar imagen…")
        btn_select.connect("clicked", self._on_select_image)
        self.append(btn_select)

        btn_resize = Gtk.Button(label="Redimensionar a 500 × 500")
        btn_resize.connect("clicked", self._on_resize)
        self.append(btn_resize)

        btn_apply = Gtk.Button(label="Aplicar a los seleccionados")
        btn_apply.add_css_class("suggested-action")
        btn_apply.connect("clicked", self._on_apply)
        self.append(btn_apply)

        btn_remove = Gtk.Button(label="Quitar portada")
        btn_remove.add_css_class("destructive-action")
        btn_remove.connect("clicked", self._on_remove)
        self.append(btn_remove)

        self._refresh_preview()

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        self._pending_data = None
        self._refresh_preview()

    def has_pending_changes(self) -> bool:
        return bool(self._pending_data is not None and self._tracks)

    def apply_pending(self) -> None:
        if not self.has_pending_changes():
            return
        self.emit("cover-change-requested", self._pending_data, self._pending_mime)
        self._pending_data = None
        self._refresh_preview()

    # ---------- helpers internos ----------

    def _refresh_preview(self) -> None:
        if self._pending_data is not None:
            self._show_bytes(self._pending_data)
            w, h = self._pixbuf_size(self._pending_data)
            self.info_label.set_text(f"Pendiente de aplicar · {w}×{h}px")
            return

        if not self._tracks:
            self._show_placeholder("Sin temas cargados")
            self.info_label.set_text("")
            return

        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            data = next(iter(covers))
            if data is None:
                self._show_placeholder("Sin portada")
                self.info_label.set_text("")
            else:
                self._show_bytes(data)
                w, h = self._pixbuf_size(data)
                self.info_label.set_text(f"{w}×{h}px")
        else:
            self._show_placeholder("Varias portadas distintas")
            self.info_label.set_text(f"{len(self._tracks)} temas seleccionados")

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
        except GObject.GError:
            self._show_placeholder("Imagen no válida")

    @staticmethod
    def _pixbuf_size(data: bytes) -> tuple[int, int]:
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        return pixbuf.get_width(), pixbuf.get_height()

    # ---------- acciones ----------

    def _on_select_image(self, _button) -> None:
        dialog = Gtk.FileDialog(title="Seleccionar portada")
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Imágenes")
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
        except GObject.GError:
            return
        if gfile is None:
            return
        path = gfile.get_path()
        if not path:
            return
        data, mime = read_image_file(path)
        self._pending_data = data
        self._pending_mime = mime
        self._refresh_preview()

    def _on_resize(self, _button) -> None:
        source = self._pending_data
        if source is None and len(self._tracks) == 1:
            source = self._tracks[0].get_cover_bytes()
        if source is None:
            return
        data, mime = resize_image_bytes(source)
        self._pending_data = data
        self._pending_mime = mime
        self._refresh_preview()

    def _on_apply(self, _button) -> None:
        self.apply_pending()

    def _on_remove(self, _button) -> None:
        if not self._tracks:
            return
        self._pending_data = None
        self.emit("cover-remove-requested")
        self._refresh_preview()
