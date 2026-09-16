"""Diálogo de identificación de un tema por huella de audio (AcoustID)."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, GObject, Gtk

from .. import acoustid, i18n
from ..constants import ACOUSTID_CLIENT_KEY


class FingerprintDialog(Adw.Dialog):
    __gtype_name__ = "MyTagFingerprintDialog"

    __gsignals__ = {
        "match-chosen": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, path: str, api_key: str = ACOUSTID_CLIENT_KEY):
        super().__init__()
        self._path = path
        self._api_key = api_key
        self._selected_match: dict | None = None

        self.set_title(i18n.t("fingerprint.title"))
        self.set_content_width(520)
        self.set_content_height(480)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("fingerprint.title")))
        toolbar_view.add_top_bar(header)

        self._stack = Gtk.Stack()
        self._stack.add_named(self._build_loading_page(), "loading")
        self._status_page = Adw.StatusPage()
        self._stack.add_named(self._status_page, "message")
        self._stack.add_named(self._build_results_page(), "results")
        toolbar_view.set_content(self._stack)
        toolbar_view.add_bottom_bar(self._build_action_bar())

        self.set_child(toolbar_view)

        threading.Thread(target=self._worker, daemon=True).start()

    def _build_loading_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        box.append(spinner)
        box.append(Gtk.Label(label=i18n.t("fingerprint.loading")))
        return box

    def _build_results_page(self) -> Gtk.Widget:
        self._results_list = Gtk.ListBox()
        self._results_list.add_css_class("boxed-list")
        self._results_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._results_list.connect("row-selected", self._on_row_selected)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self._results_list)
        scroller.set_vexpand(True)
        scroller.set_margin_top(12)
        scroller.set_margin_bottom(12)
        scroller.set_margin_start(12)
        scroller.set_margin_end(12)
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
        self.btn_accept.connect("clicked", self._on_accept)
        bar.pack_end(self.btn_accept)

        return bar

    # ---------- trabajo en segundo plano ----------

    def _worker(self) -> None:
        try:
            matches = acoustid.identify(self._path, self._api_key)
        except acoustid.AcoustIDError as exc:
            GLib.idle_add(self._show_error, str(exc))
            return
        GLib.idle_add(self._show_results, matches)

    def _show_error(self, message: str) -> bool:
        self._status_page.set_icon_name("dialog-warning-symbolic")
        self._status_page.set_title(i18n.t("fingerprint.error_title"))
        self._status_page.set_description(message)
        self._stack.set_visible_child_name("message")
        return False

    def _show_results(self, matches: list[dict]) -> bool:
        if not matches:
            self._status_page.set_icon_name("edit-find-symbolic")
            self._status_page.set_title(i18n.t("fingerprint.no_matches_title"))
            self._status_page.set_description(i18n.t("fingerprint.no_matches_desc"))
            self._stack.set_visible_child_name("message")
            return False

        for match in matches[:15]:
            subtitle = " · ".join(part for part in (match.get("artist"), match.get("album")) if part)
            row = Adw.ActionRow(title=match["title"], subtitle=subtitle)
            icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
            icon.add_css_class("dim-label")
            row.add_prefix(icon)
            row.mytag_match = match
            self._results_list.append(row)

        self._stack.set_visible_child_name("results")
        return False

    def _on_row_selected(self, _listbox, row) -> None:
        self._selected_match = getattr(row, "mytag_match", None) if row else None
        self.btn_accept.set_sensitive(self._selected_match is not None)

    def _on_accept(self, _button) -> None:
        if self._selected_match is not None:
            self.emit("match-chosen", self._selected_match)
            self.close()
