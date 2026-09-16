"""Diálogo modal compacto para redimensionar la portada de los temas seleccionados."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Adw, Gdk, GdkPixbuf, GLib, GObject, Gtk

from .. import i18n

DIALOG_PREVIEW_SIZE = 120


class ResizeCoverDialog(Adw.Dialog):
    __gtype_name__ = "MyTagResizeCoverDialog"

    __gsignals__ = {
        "resize-requested": (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
    }

    def __init__(
        self,
        cover_bytes: bytes | None,
        original_width: int = 500,
        original_height: int = 500,
        is_multiple: bool = False,
    ):
        super().__init__()
        self._cover_bytes = cover_bytes
        self._orig_w = original_width if original_width > 0 else 500
        self._orig_h = original_height if original_height > 0 else 500
        self._is_multiple = is_multiple
        self._ratio = (self._orig_w / self._orig_h) if (self._orig_h and not is_multiple) else 1.0
        self._updating = False

        self.set_title(i18n.t("cover.resize_dialog_title"))
        self.set_content_width(340)
        self.set_content_height(370)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("cover.resize_dialog_title")))

        btn_cancel = Gtk.Button(label=i18n.t("action.cancel"))
        btn_cancel.connect("clicked", lambda _b: self.close())
        header.pack_start(btn_cancel)

        self.btn_apply = Gtk.Button(label=i18n.t("cover.apply_resize"))
        self.btn_apply.add_css_class("suggested-action")
        self.btn_apply.connect("clicked", self._on_apply)
        header.pack_end(self.btn_apply)

        toolbar_view.add_top_bar(header)

        body_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        body_box.set_margin_top(12)
        body_box.set_margin_bottom(16)
        body_box.set_margin_start(16)
        body_box.set_margin_end(16)

        # 1. Vista previa de la portada (tamaño compacto)
        preview_frame = Gtk.Frame()
        preview_frame.add_css_class("card")
        preview_frame.add_css_class("album-cover-frame")
        preview_frame.set_halign(Gtk.Align.CENTER)
        preview_frame.set_overflow(Gtk.Overflow.HIDDEN)

        picture = Gtk.Picture()
        picture.set_can_shrink(True)
        picture.set_content_fit(Gtk.ContentFit.COVER)
        picture.set_size_request(DIALOG_PREVIEW_SIZE, DIALOG_PREVIEW_SIZE)

        if cover_bytes:
            try:
                loader = GdkPixbuf.PixbufLoader()
                loader.write(cover_bytes)
                loader.close()
                pixbuf = loader.get_pixbuf()
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                picture.set_paintable(texture)
            except GLib.Error:
                pass
        else:
            placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            placeholder_box.set_halign(Gtk.Align.CENTER)
            placeholder_box.set_valign(Gtk.Align.CENTER)
            placeholder_box.set_size_request(DIALOG_PREVIEW_SIZE, DIALOG_PREVIEW_SIZE)
            icon = Gtk.Image.new_from_icon_name("media-optical-cd-symbolic")
            icon.set_pixel_size(40)
            icon.add_css_class("dim-label")
            placeholder_box.append(icon)
            preview_frame.set_child(placeholder_box)

        if cover_bytes:
            preview_frame.set_child(picture)
        body_box.append(preview_frame)

        # 2. Información del tamaño actual
        if is_multiple:
            info_text = i18n.t("cover.different_sizes")
        else:
            info_text = i18n.t("cover.current_size", w=self._orig_w, h=self._orig_h)

        info_lbl = Gtk.Label(label=info_text)
        info_lbl.add_css_class("dim-label")
        info_lbl.add_css_class("caption")
        info_lbl.set_halign(Gtk.Align.CENTER)
        body_box.append(info_lbl)

        # 3. Controles compactos de dimensiones
        group = Adw.PreferencesGroup()

        self.width_row = Adw.EntryRow(title=i18n.t("cover.width_label"))
        self.width_row.set_text(str(self._orig_w))
        self.width_row.connect("changed", self._on_width_changed)
        self.width_row.connect("entry-activated", lambda _e: self._on_apply(None))
        group.add(self.width_row)

        if not is_multiple:
            self.height_row = Adw.EntryRow(title=i18n.t("cover.height_label"))
            self.height_row.set_text(str(self._orig_h))
            self.height_row.connect("changed", self._on_height_changed)
            self.height_row.connect("entry-activated", lambda _e: self._on_apply(None))
            group.add(self.height_row)

            self.ratio_switch = Adw.SwitchRow(title=i18n.t("cover.proportional_switch"))
            self.ratio_switch.set_active(True)
            group.add(self.ratio_switch)
        else:
            self.height_row = None
            self.ratio_switch = None

        body_box.append(group)

        # Directamente al toolbar_view sin ScrolledWindow para evitar scroll
        toolbar_view.set_content(body_box)
        self.set_child(toolbar_view)

    def _on_width_changed(self, entry: Adw.EntryRow) -> None:
        if self._updating or self.height_row is None:
            return
        if self.ratio_switch and not self.ratio_switch.get_active():
            return
        text = entry.get_text().strip()
        if not text.isdigit():
            return
        val = int(text)
        if val <= 0:
            return
        self._updating = True
        calc_h = round(val / self._ratio) if self._ratio else val
        self.height_row.set_text(str(calc_h))
        self._updating = False

    def _on_height_changed(self, entry: Adw.EntryRow) -> None:
        if self._updating or self.height_row is None:
            return
        if self.ratio_switch and not self.ratio_switch.get_active():
            return
        text = entry.get_text().strip()
        if not text.isdigit():
            return
        val = int(text)
        if val <= 0:
            return
        self._updating = True
        calc_w = round(val * self._ratio) if self._ratio else val
        self.width_row.set_text(str(calc_w))
        self._updating = False

    def _on_apply(self, _button) -> None:
        w_text = self.width_row.get_text().strip()
        if not w_text.isdigit():
            return
        w = int(w_text)
        if w <= 0:
            return
        if self._is_multiple or self.height_row is None:
            h = w
        else:
            h_text = self.height_row.get_text().strip()
            if not h_text.isdigit():
                return
            h = int(h_text)
            if h <= 0:
                return
        self.emit("resize-requested", w, h)
        self.close()
