"""Panel de previsualización y edición de la portada del álbum (GTK4/Adwaita).

Cada acción (elegir imagen, redimensionar, quitar) se aplica de inmediato a
los temas seleccionados (en memoria); "Guardar cambios" en la ventana
principal es lo único que escribe a disco.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk

from ..cover_utils import read_image_file, resize_image_bytes

PREVIEW_SIZE = 260


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
        self.info_label.set_wrap(True)
        self.info_label.set_justify(Gtk.Justification.CENTER)
        self.append(self.info_label)

        self.btn_select = Gtk.Button(label="Seleccionar imagen…")
        self.btn_select.connect("clicked", self._on_select_image)
        self.append(self.btn_select)

        self.btn_musicbrainz = Gtk.Button(label="Buscar en MusicBrainz…")
        self.btn_musicbrainz.connect("clicked", lambda _b: self.emit("musicbrainz-search-requested"))
        self.append(self.btn_musicbrainz)

        self.btn_resize = Gtk.Button(label="Redimensionar (máx. 500 px)")
        self.btn_resize.connect("clicked", self._on_resize)
        self.append(self.btn_resize)

        self.btn_remove = Gtk.Button(label="Quitar portada")
        self.btn_remove.add_css_class("destructive-action")
        self.btn_remove.connect("clicked", self._on_remove)
        self.append(self.btn_remove)

        self.set_tracks([])

    def set_tracks(self, tracks) -> None:
        self._tracks = tracks
        enabled = bool(tracks)
        self.btn_select.set_sensitive(enabled)
        self.btn_musicbrainz.set_sensitive(enabled)
        self.btn_resize.set_sensitive(enabled)
        self.btn_remove.set_sensitive(enabled)
        self._refresh_preview()

    # ---------- helpers internos ----------

    def _refresh_preview(self) -> None:
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
        except GLib.Error:
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
        except GLib.Error:
            return
        if gfile is None or not self._tracks:
            return
        path = gfile.get_path()
        if not path:
            return
        data, mime = read_image_file(path)
        self.emit("cover-change-requested", data, mime)

    def _on_resize(self, _button) -> None:
        if not self._tracks:
            return
        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) != 1:
            self.info_label.set_text("Los temas seleccionados tienen portadas distintas.")
            return
        source = next(iter(covers))
        if source is None:
            self.info_label.set_text("No hay portada que redimensionar.")
            return
        data, mime = resize_image_bytes(source)
        self.emit("cover-change-requested", data, mime)

    def _on_remove(self, _button) -> None:
        if not self._tracks:
            return
        self.emit("cover-remove-requested")
