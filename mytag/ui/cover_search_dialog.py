"""Diálogo para buscar y elegir una portada de MusicBrainz/Cover Art Archive."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, GLib, GObject, Gtk

from .. import musicbrainz


class CoverSearchDialog(Adw.Dialog):
    __gtype_name__ = "MyTagCoverSearchDialog"

    __gsignals__ = {
        "cover-chosen": (GObject.SignalFlags.RUN_FIRST, None, (object, str)),
    }

    def __init__(self, album: str, artist: str):
        super().__init__()
        self._album = album
        self._artist = artist
        self.set_title("Buscar portada en MusicBrainz")
        self.set_content_width(640)
        self.set_content_height(520)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        subtitle = Adw.WindowTitle(title="Buscar portada en MusicBrainz", subtitle=f"{artist} — {album}")
        header.set_title_widget(subtitle)
        toolbar_view.add_top_bar(header)

        self._stack = Gtk.Stack()
        self._stack.add_named(self._build_loading_page(), "loading")
        self._status_page = Adw.StatusPage()
        self._stack.add_named(self._status_page, "message")
        self._stack.add_named(self._build_results_page(), "results")
        toolbar_view.set_content(self._stack)

        self.set_child(toolbar_view)
        self._stack.set_visible_child_name("loading")

        threading.Thread(target=self._search_worker, daemon=True).start()

    def _build_loading_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        box.append(spinner)
        self._loading_label = Gtk.Label(label="Buscando portadas en MusicBrainz…")
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
        self._flow.set_selection_mode(Gtk.SelectionMode.NONE)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self._flow)
        scroller.set_vexpand(True)
        return scroller

    # ---------- búsqueda en segundo plano ----------

    def _search_worker(self) -> None:
        try:
            candidates = musicbrainz.search_cover_candidates(self._album, self._artist)
        except musicbrainz.MusicBrainzError as exc:
            GLib.idle_add(self._show_message, "dialog-warning-symbolic", "No se pudo buscar", str(exc))
            return
        GLib.idle_add(self._show_results, candidates)

    def _show_message(self, icon_name: str, title: str, description: str) -> bool:
        self._status_page.set_icon_name(icon_name)
        self._status_page.set_title(title)
        self._status_page.set_description(description)
        self._stack.set_visible_child_name("message")
        return False

    def _show_results(self, candidates: list) -> bool:
        if not candidates:
            self._show_message(
                "edit-find-symbolic",
                "Sin portadas",
                "No se encontró ninguna portada en MusicBrainz para este álbum y artista.",
            )
            return False
        for candidate in candidates:
            self._flow.append(self._build_candidate_widget(candidate))
        self._stack.set_visible_child_name("results")
        return False

    def _build_candidate_widget(self, candidate: musicbrainz.CoverCandidate) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_size_request(150, 150)

        picture = Gtk.Picture()
        picture.set_content_fit(Gtk.ContentFit.COVER)
        picture.set_size_request(140, 140)
        box.append(picture)

        detail = " · ".join(part for part in (candidate.date, candidate.country) if part)
        label = Gtk.Label(label=detail or "Edición sin fecha")
        label.add_css_class("dim-label")
        label.add_css_class("caption")
        box.append(label)

        button = Gtk.Button()
        button.set_child(box)
        button.add_css_class("flat")
        button.set_tooltip_text("Usar esta portada")
        button.connect("clicked", self._on_candidate_clicked, candidate)

        threading.Thread(target=self._load_thumbnail, args=(candidate, picture), daemon=True).start()
        return button

    def _load_thumbnail(self, candidate: musicbrainz.CoverCandidate, picture: Gtk.Picture) -> None:
        try:
            data = musicbrainz.download_bytes(candidate.thumbnail_url)
        except musicbrainz.MusicBrainzError:
            return
        GLib.idle_add(self._set_picture_bytes, picture, data)

    def _set_picture_bytes(self, picture: Gtk.Picture, data: bytes) -> bool:
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            texture = Gdk.Texture.new_for_pixbuf(loader.get_pixbuf())
            picture.set_paintable(texture)
        except GLib.Error:
            pass
        return False

    # ---------- elegir portada ----------

    def _on_candidate_clicked(self, _button, candidate: musicbrainz.CoverCandidate) -> None:
        self._loading_label.set_text("Descargando portada…")
        self._stack.set_visible_child_name("loading")
        threading.Thread(target=self._download_and_finish, args=(candidate,), daemon=True).start()

    def _download_and_finish(self, candidate: musicbrainz.CoverCandidate) -> None:
        try:
            data = musicbrainz.download_bytes(candidate.large_url)
        except musicbrainz.MusicBrainzError as exc:
            GLib.idle_add(self._show_message, "dialog-warning-symbolic", "No se pudo descargar", str(exc))
            return
        GLib.idle_add(self._finish, data)

    def _finish(self, data: bytes) -> bool:
        self.emit("cover-chosen", data, "image/jpeg")
        self.close()
        return False
