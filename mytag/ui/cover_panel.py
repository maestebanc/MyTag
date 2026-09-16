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
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk

from .. import i18n
from ..constants import COVER_SIZE
from ..cover_utils import read_image_file, resize_image_bytes

PREVIEW_SIZE = 200
IMAGE_MIME_TYPES = ("image/png", "image/jpeg", "image/bmp", "image/webp")


class CoverPanel(Gtk.Box):
    __gtype_name__ = "MyTagCoverPanel"

    __gsignals__ = {
        "cover-change-requested": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
        "cover-resize-each-requested": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "cover-remove-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "musicbrainz-search-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._tracks = []

        self.frame = Gtk.Frame()
        self.frame.add_css_class("card")
        self.frame.add_css_class("album-cover-frame")
        self.frame.set_overflow(Gtk.Overflow.HIDDEN)
        self.frame.set_halign(Gtk.Align.CENTER)
        self.picture = Gtk.Picture()
        self.picture.set_can_shrink(True)
        self.picture.set_content_fit(Gtk.ContentFit.COVER)
        self.picture.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)

        self.placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.placeholder_box.add_css_class("album-cover-placeholder")
        self.placeholder_box.set_halign(Gtk.Align.CENTER)
        self.placeholder_box.set_valign(Gtk.Align.CENTER)
        self.placeholder_box.set_size_request(PREVIEW_SIZE - 24, PREVIEW_SIZE - 24)

        self.placeholder_icon = Gtk.Image.new_from_icon_name("media-optical-cd-symbolic")
        self.placeholder_icon.set_pixel_size(56)
        self.placeholder_icon.add_css_class("dim-label")
        self.placeholder_box.append(self.placeholder_icon)

        self.placeholder_label = Gtk.Label(label=i18n.t("cover.no_cover"))
        self.placeholder_label.add_css_class("dim-label")
        self.placeholder_label.add_css_class("heading")
        self.placeholder_box.append(self.placeholder_label)

        self.placeholder_sublabel = Gtk.Label(label=i18n.t("cover.drag_hint"))
        self.placeholder_sublabel.add_css_class("dim-label")
        self.placeholder_sublabel.add_css_class("caption")
        self.placeholder_sublabel.set_wrap(True)
        self.placeholder_sublabel.set_justify(Gtk.Justification.CENTER)
        self.placeholder_box.append(self.placeholder_sublabel)

        self._stack = Gtk.Stack()
        self._stack.add_named(self.placeholder_box, "placeholder")
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
        self.btn_overlay_menu.add_css_class("cover-overlay-btn")
        self.btn_overlay_menu.set_halign(Gtk.Align.END)
        self.btn_overlay_menu.set_valign(Gtk.Align.START)
        self.btn_overlay_menu.set_margin_top(8)
        self.btn_overlay_menu.set_margin_end(8)
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

        # Ratio de la imagen actualmente cargada (ancho/alto), fijado al
        # refrescar la vista previa; se usa para recalcular la otra
        # dimensión cuando el usuario edita el ancho o el alto a mano.
        self._dims_ratio: float | None = None
        self._square_mode = False
        self._updating_dims = False

        self.dims_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.dims_box.set_halign(Gtk.Align.CENTER)
        self.dims_box.add_css_class("dims-pill")

        self.width_entry = Gtk.Entry()
        self.width_entry.set_width_chars(4)
        self.width_entry.set_max_width_chars(5)
        self.width_entry.set_alignment(0.5)
        self.width_entry.set_text(str(COVER_SIZE[0]))
        self.width_entry.connect("changed", self._on_width_entry_changed)
        self.width_entry.connect("activate", lambda _e: self._on_resize(None))

        self.height_entry = Gtk.Entry()
        self.height_entry.set_width_chars(4)
        self.height_entry.set_max_width_chars(5)
        self.height_entry.set_alignment(0.5)
        self.height_entry.set_text(str(COVER_SIZE[1]))
        self.height_entry.connect("changed", self._on_height_entry_changed)
        self.height_entry.connect("activate", lambda _e: self._on_resize(None))

        self.dims_box.append(self.width_entry)
        self.dims_box.append(Gtk.Label(label="×"))
        self.dims_box.append(self.height_entry)
        self.dims_box.append(Gtk.Label(label="px"))
        self.dims_box.set_visible(False)
        self.append(self.dims_box)

        def make_action_button(label: str, icon_name: str) -> Gtk.Button:
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.set_halign(Gtk.Align.CENTER)
            box.append(Gtk.Image.new_from_icon_name(icon_name))
            box.append(Gtk.Label(label=label))
            btn.set_child(box)
            return btn

        # Botones de acción principales
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        actions_box.set_halign(Gtk.Align.CENTER)
        actions_box.set_size_request(PREVIEW_SIZE, -1)

        self.btn_select = make_action_button(i18n.t("cover.select_image"), "document-open-symbolic")
        self.btn_select.connect("clicked", self._on_select_image)
        actions_box.append(self.btn_select)

        self.btn_search = make_action_button(i18n.t("cover.search_button"), "system-search-symbolic")
        self.btn_search.connect("clicked", lambda _b: self.emit("musicbrainz-search-requested"))
        actions_box.append(self.btn_search)

        self.btn_resize = make_action_button(i18n.t("cover.resize"), "image-crop-symbolic")
        self.btn_resize.connect("clicked", self._on_resize)
        actions_box.append(self.btn_resize)

        self.append(actions_box)

        self.set_tracks([])

    def _build_actions_popover(self) -> Gtk.Popover:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        popover = Gtk.Popover()

        def add_item(label: str, icon_name: str, callback, destructive: bool = False) -> None:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            if destructive:
                btn.add_css_class("destructive-action")
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

        add_item(i18n.t("cover.paste"), "edit-paste-symbolic", lambda: self._on_paste(None))
        add_item(i18n.t("cover.musicbrainz_search"), "system-search-symbolic", lambda: self.emit("musicbrainz-search-requested"))
        add_item(i18n.t("cover.remove"), "user-trash-symbolic", lambda: self._on_remove(None), destructive=True)

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
        # Se registran controladores separados por tipo (en vez de un único
        # DropTarget con set_gtypes) porque algunos orígenes externos (p. ej.
        # gestores de archivos) sólo ofrecen la lista de archivos como
        # Gdk.FileList (deserializada a partir de text/uri-list), no como
        # Gio.File suelto; con un único controlador esa negociación de
        # formato podía fallar silenciosamente y el drop no llegaba nunca.
        # COPY | MOVE (no sólo COPY): en Hyprland/wlroots, Nautilus
        # preselecciona "move" como acción de arrastre preferida, y un
        # DropTarget que sólo admite "copy" hace que GTK rechace la
        # negociación entera sin llegar nunca a nuestro "drop" (nunca
        # movemos ni borramos el origen, aceptar "move" no cambia nada).
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
        self.btn_select.set_sensitive(enabled)
        self.btn_search.set_sensitive(enabled)
        self.btn_overlay_menu.set_sensitive(enabled)
        self.width_entry.set_sensitive(enabled)
        self.height_entry.set_sensitive(enabled)
        self.btn_resize.set_sensitive(enabled)
        self._refresh_preview()

    # ---------- helpers internos ----------

    def _set_status_text(self, text: str) -> None:
        self._dims_ratio = None
        self._square_mode = False
        self.dims_box.set_visible(False)
        self.info_label.set_visible(True)
        self.info_label.set_text(text)

    def _refresh_preview(self) -> None:
        if not self._tracks:
            self._show_placeholder(i18n.t("cover.no_tracks_loaded"))
            self._set_status_text("")
            return

        covers = {t.get_cover_bytes() for t in self._tracks}
        if len(covers) == 1:
            data = next(iter(covers))
            if data is None:
                self._show_placeholder(i18n.t("cover.no_cover"))
                self._set_status_text("")
            else:
                self._show_bytes(data)
                w, h = self._pixbuf_size(data)
                self._square_mode = False
                self._dims_ratio = (w / h) if h else None
                self._updating_dims = True
                self.width_entry.set_text(str(w))
                self.height_entry.set_text(str(h))
                self._updating_dims = False
                self.info_label.set_visible(False)
                self.dims_box.set_visible(True)
        else:
            self._show_placeholder(i18n.t("cover.multiple_covers"))
            self.info_label.set_visible(True)
            self.info_label.set_text(i18n.t("cover.tracks_selected_count", n=len(self._tracks)))
            if any(c is not None for c in covers):
                # Portadas distintas: no hay un único ratio del que partir,
                # así que se fuerza 1:1 y "Redimensionar" recorta cada
                # portada individualmente al cuadrado que se indique aquí.
                self._square_mode = True
                self._dims_ratio = 1.0
                self._updating_dims = True
                current = self.width_entry.get_text().strip() or str(COVER_SIZE[0])
                self.width_entry.set_text(current)
                self.height_entry.set_text(current)
                self._updating_dims = False
                self.dims_box.set_visible(True)
            else:
                self._square_mode = False
                self._dims_ratio = None
                self.dims_box.set_visible(False)

    def _on_width_entry_changed(self, _entry) -> None:
        if self._updating_dims or not self._dims_ratio:
            return
        text = self.width_entry.get_text().strip()
        if not text.isdigit():
            return
        val = int(text)
        if val <= 0:
            return
        self._updating_dims = True
        new_height = round(val / self._dims_ratio)
        self.height_entry.set_text(str(new_height))
        self._updating_dims = False

    def _on_height_entry_changed(self, _entry) -> None:
        if self._updating_dims or not self._dims_ratio:
            return
        text = self.height_entry.get_text().strip()
        if not text.isdigit():
            return
        val = int(text)
        if val <= 0:
            return
        self._updating_dims = True
        new_width = round(val * self._dims_ratio)
        self.width_entry.set_text(str(new_width))
        self._updating_dims = False

    def _show_placeholder(self, text: str) -> None:
        self.placeholder_label.set_text(text)
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
            self._set_status_text(i18n.t("cover.paste_no_image"))
            return
        png_bytes = texture.save_to_png_bytes()
        self.emit("cover-change-requested", png_bytes.get_data(), "image/png")

    def _on_resize(self, _button) -> None:
        if not self._tracks:
            return
        covers = {t.get_cover_bytes() for t in self._tracks}
        try:
            width = int(self.width_entry.get_text().strip())
            height = int(self.height_entry.get_text().strip())
        except ValueError:
            width, height = COVER_SIZE
        if len(covers) == 1:
            source = next(iter(covers))
            if source is None:
                self._set_status_text(i18n.t("cover.nothing_to_resize"))
                return
            data, mime = resize_image_bytes(source, size=(width, height))
            self.emit("cover-change-requested", data, mime)
        elif any(c is not None for c in covers):
            # Portadas distintas: cada tema conserva su propia imagen, sólo
            # se recorta y escala al mismo cuadrado (self._square_mode
            # asegura que width == height aquí).
            self.emit("cover-resize-each-requested", width)
        else:
            self._set_status_text(i18n.t("cover.nothing_to_resize"))

    def _on_remove(self, _button) -> None:
        if not self._tracks:
            return
        self.emit("cover-remove-requested")
