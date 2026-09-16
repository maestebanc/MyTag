"""Diálogo para buscar y elegir una portada (MusicBrainz, iTunes, ...)."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, GLib, GObject, Gtk

from .. import cover_search, i18n
from ..cover_types import CoverCandidate, CoverSearchError, download_bytes


class CoverSearchDialog(Adw.Dialog):
    __gtype_name__ = "MyTagCoverSearchDialog"

    __gsignals__ = {
        "cover-chosen": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
    }

    def __init__(self, album: str, artist: str):
        super().__init__()
        self._album = album
        self._artist = artist
        self._selected_candidate: CoverCandidate | None = None
        # bytes ya descargados por candidato, para no volver a bajarlos al aceptar
        self._downloaded: dict[int, bytes] = {}
        self.set_title(i18n.t("coversearch.title"))
        self.set_content_width(640)
        self.set_content_height(560)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        subtitle = Adw.WindowTitle(title=i18n.t("coversearch.title"), subtitle=f"{artist} — {album}")
        header.set_title_widget(subtitle)
        toolbar_view.add_top_bar(header)

        self._stack = Gtk.Stack()
        self._stack.add_named(self._build_loading_page(), "loading")
        self._status_page = Adw.StatusPage()
        self._stack.add_named(self._status_page, "message")
        self._stack.add_named(self._build_results_page(), "results")
        toolbar_view.set_content(self._stack)

        toolbar_view.add_bottom_bar(self._build_action_bar())

        self.set_child(toolbar_view)
        self._stack.set_visible_child_name("loading")

        threading.Thread(target=self._search_worker, daemon=True).start()

    def _build_loading_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        box.append(spinner)
        self._loading_label = Gtk.Label(label=i18n.t("coversearch.loading"))
        box.append(self._loading_label)
        return box

    def _build_results_page(self) -> Gtk.Widget:
        self._flow = Gtk.FlowBox()
        self._flow.set_valign(Gtk.Align.START)
        self._flow.set_max_children_per_line(4)
        self._flow.set_min_children_per_line(2)
        self._flow.set_row_spacing(16)
        self._flow.set_column_spacing(16)
        self._flow.set_margin_top(16)
        self._flow.set_margin_bottom(16)
        self._flow.set_margin_start(16)
        self._flow.set_margin_end(16)
        self._flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._flow.connect("selected-children-changed", self._on_selection_changed)
        self._flow.connect("child-activated", self._on_child_activated)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self._flow)
        scroller.set_vexpand(True)
        return scroller

    def _build_action_bar(self) -> Gtk.Widget:
        bar = Gtk.ActionBar()

        btn_cancel = Gtk.Button(label=i18n.t("action.cancel"))
        btn_cancel.connect("clicked", lambda _b: self.close())
        bar.pack_start(btn_cancel)

        self.btn_accept = Gtk.Button()
        accept_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        accept_box.append(Gtk.Image.new_from_icon_name("object-select-symbolic"))
        accept_box.append(Gtk.Label(label=i18n.t("action.accept")))
        self.btn_accept.set_child(accept_box)
        self.btn_accept.add_css_class("suggested-action")
        self.btn_accept.set_sensitive(False)
        self.btn_accept.connect("clicked", self._on_accept_clicked)
        bar.pack_end(self.btn_accept)

        return bar

    # ---------- búsqueda en segundo plano ----------

    def _search_worker(self) -> None:
        candidates, errors = cover_search.search_all(self._album, self._artist)
        GLib.idle_add(self._show_results, candidates, errors)

    def _show_message(self, icon_name: str, title: str, description: str) -> bool:
        self._status_page.set_icon_name(icon_name)
        self._status_page.set_title(title)
        self._status_page.set_description(description)
        self._stack.set_visible_child_name("message")
        return False

    def _show_results(self, candidates: list[CoverCandidate], errors: list[str]) -> bool:
        if not candidates:
            if errors:
                self._show_message(
                    "dialog-warning-symbolic", i18n.t("coversearch.search_failed_title"), "\n".join(errors)
                )
            else:
                self._show_message(
                    "edit-find-symbolic",
                    i18n.t("coversearch.no_results_title"),
                    i18n.t("coversearch.no_results_desc"),
                )
            return False
        for candidate in candidates:
            self._flow.append(self._build_candidate_widget(candidate))
        self._stack.set_visible_child_name("results")
        return False

    def _build_candidate_widget(self, candidate: CoverCandidate) -> Gtk.FlowBoxChild:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("candidate-card")
        card.set_size_request(160, 216)

        thumb_frame = Gtk.Frame()
        thumb_frame.add_css_class("candidate-thumb")
        thumb_frame.set_overflow(Gtk.Overflow.HIDDEN)
        picture = Gtk.Picture()
        picture.set_content_fit(Gtk.ContentFit.COVER)
        picture.set_size_request(144, 144)
        thumb_frame.set_child(picture)
        card.append(thumb_frame)

        meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        meta_box.set_halign(Gtk.Align.CENTER)

        size_label = Gtk.Label(label=i18n.t("coversearch.loading_item"))
        size_label.add_css_class("dim-label")
        size_label.add_css_class("caption")
        meta_box.append(size_label)

        source_badge = Gtk.Label(label=candidate.source)
        source_badge.add_css_class("pill-badge")
        source_badge.add_css_class("dim")
        meta_box.append(source_badge)

        card.append(meta_box)

        child = Gtk.FlowBoxChild()
        child.set_child(card)
        child.mytag_candidate = candidate

        threading.Thread(target=self._load_image, args=(candidate, picture, size_label), daemon=True).start()
        return child

    def _load_image(self, candidate: CoverCandidate, picture: Gtk.Picture, size_label: Gtk.Label) -> None:
        try:
            data = download_bytes(candidate.image_url)
        except CoverSearchError:
            GLib.idle_add(size_label.set_text, i18n.t("coversearch.load_error"))
            return
        self._downloaded[id(candidate)] = data
        GLib.idle_add(self._set_picture_bytes, picture, size_label, data)

    def _set_picture_bytes(self, picture: Gtk.Picture, size_label: Gtk.Label, data: bytes) -> bool:
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            picture.set_paintable(texture)
            size_label.set_text(f"{pixbuf.get_width()}×{pixbuf.get_height()}px")
        except GLib.Error:
            size_label.set_text(i18n.t("cover.invalid_image"))
        return False

    # ---------- elegir portada ----------

    def _on_selection_changed(self, flow_box: Gtk.FlowBox) -> None:
        selected = flow_box.get_selected_children()
        self._selected_candidate = selected[0].mytag_candidate if selected else None
        self.btn_accept.set_sensitive(self._selected_candidate is not None)

    def _on_child_activated(self, _flow_box, child: Gtk.FlowBoxChild) -> None:
        # doble clic (o Enter): equivale a seleccionar y aceptar directamente
        self._selected_candidate = child.mytag_candidate
        self._accept(self._selected_candidate)

    def _on_accept_clicked(self, _button) -> None:
        if self._selected_candidate is not None:
            self._accept(self._selected_candidate)

    def _accept(self, candidate: CoverCandidate) -> None:
        cached = self._downloaded.get(id(candidate))
        if cached is not None:
            self._finish(cached)
            return
        self._loading_label.set_text(i18n.t("coversearch.downloading"))
        self._stack.set_visible_child_name("loading")
        self.btn_accept.set_sensitive(False)
        threading.Thread(target=self._download_and_finish, args=(candidate,), daemon=True).start()

    def _download_and_finish(self, candidate: CoverCandidate) -> None:
        try:
            data = download_bytes(candidate.image_url)
        except CoverSearchError as exc:
            GLib.idle_add(
                self._show_message, "dialog-warning-symbolic", i18n.t("coversearch.download_failed_title"), str(exc)
            )
            return
        GLib.idle_add(self._finish, data)

    def _finish(self, data: bytes) -> bool:
        self.emit("cover-chosen", data, "image/jpeg")
        self.close()
        return False
