"""Diálogo para identificar varios temas a la vez por huella de audio (AcoustID)."""
from __future__ import annotations

import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, GObject, Gtk

from .. import acoustid, i18n
from ..audio_track import AudioTrack
from ..constants import ACOUSTID_CLIENT_KEY


class BatchFingerprintDialog(Adw.Dialog):
    __gtype_name__ = "MyTagBatchFingerprintDialog"

    __gsignals__ = {
        "matches-applied": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, tracks: list[AudioTrack], api_key: str = ACOUSTID_CLIENT_KEY):
        super().__init__()
        self._tracks = tracks
        self._api_key = api_key
        self._cancelled = False
        self._row_data: list[dict] = []

        self.set_title(i18n.t("fingerprint.batch_title"))
        self.set_content_width(680)
        self.set_content_height(560)

        self.connect("closed", self._on_closed)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=i18n.t("fingerprint.batch_title")))
        toolbar_view.add_top_bar(header)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer_box.set_margin_top(12)
        outer_box.set_margin_bottom(12)
        outer_box.set_margin_start(14)
        outer_box.set_margin_end(14)

        # Barra y etiqueta de progreso superior
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_label = Gtk.Label(
            label=i18n.t(
                "fingerprint.batch_progress",
                current=1,
                total=len(self._tracks),
                filename=self._tracks[0].filename if self._tracks else "",
            ),
            xalign=0,
        )
        self.status_label.add_css_class("caption")
        top_box.append(self.status_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        top_box.append(self.progress_bar)

        # Botones rápidos seleccionar / deseleccionar todos
        quick_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_sel_all = Gtk.Button(label=i18n.t("fingerprint.select_all"))
        btn_sel_all.add_css_class("flat")
        btn_sel_all.add_css_class("caption")
        btn_sel_all.connect("clicked", lambda _b: self._set_all_checks(True))
        quick_bar.append(btn_sel_all)

        btn_desel_all = Gtk.Button(label=i18n.t("fingerprint.deselect_all"))
        btn_desel_all.add_css_class("flat")
        btn_desel_all.add_css_class("caption")
        btn_desel_all.connect("clicked", lambda _b: self._set_all_checks(False))
        quick_bar.append(btn_desel_all)

        top_box.append(quick_bar)
        outer_box.append(top_box)

        # Lista scrolleable de temas
        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        self.results_list = Gtk.ListBox()
        self.results_list.add_css_class("boxed-list")
        self.results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroller.set_child(self.results_list)
        outer_box.append(scroller)

        toolbar_view.set_content(outer_box)
        toolbar_view.add_bottom_bar(self._build_action_bar())
        self.set_child(toolbar_view)

        # Construir filas iniciales con spinners
        for track in self._tracks:
            row = Adw.ActionRow(title=track.filename)
            row.set_subtitle(i18n.t("fingerprint.loading"))

            check = Gtk.CheckButton()
            check.set_active(False)
            check.set_sensitive(False)
            check.connect("toggled", lambda _c: self._update_apply_button())
            row.add_prefix(check)

            spinner = Gtk.Spinner()
            spinner.start()
            row.add_suffix(spinner)

            self.results_list.append(row)
            self._row_data.append({
                "track": track,
                "row": row,
                "check": check,
                "suffix_widget": spinner,
                "candidates": [],
                "chosen": None,
            })

        threading.Thread(target=self._worker, daemon=True).start()

    def _build_action_bar(self) -> Gtk.Widget:
        bar = Gtk.ActionBar()

        btn_cancel = Gtk.Button(label=i18n.t("action.cancel"))
        btn_cancel.connect("clicked", self._on_cancel)
        bar.pack_start(btn_cancel)

        self.btn_apply = Gtk.Button()
        apply_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        apply_box.append(Gtk.Image.new_from_icon_name("object-select-symbolic"))
        self.apply_label = Gtk.Label(label=i18n.t("fingerprint.apply_button", n=0))
        apply_box.append(self.apply_label)
        self.btn_apply.set_child(apply_box)
        self.btn_apply.add_css_class("suggested-action")
        self.btn_apply.set_sensitive(False)
        self.btn_apply.connect("clicked", self._on_apply)
        bar.pack_end(self.btn_apply)

        return bar

    def _on_closed(self, _dialog) -> None:
        self._cancelled = True

    def _on_cancel(self, _button) -> None:
        self._cancelled = True
        self.close()

    def _set_all_checks(self, active: bool) -> None:
        for data in self._row_data:
            if data["candidates"]:
                data["check"].set_active(active)
        self._update_apply_button()

    def _update_apply_button(self) -> None:
        count = sum(1 for d in self._row_data if d["check"].get_active() and d["chosen"])
        self.apply_label.set_label(i18n.t("fingerprint.apply_button", n=count))
        self.btn_apply.set_sensitive(count > 0)

    # ---------- trabajo en segundo plano ----------

    def _worker(self) -> None:
        total = len(self._tracks)
        found_count = 0

        for idx, item in enumerate(self._row_data):
            if self._cancelled:
                return

            track = item["track"]
            # Actualizar progreso en UI
            GLib.idle_add(self._update_progress, idx, total, track.filename)

            # Identificar mediante AcoustID
            candidates: list[dict] = []
            try:
                candidates = acoustid.identify(track.path, self._api_key)
            except Exception:
                candidates = []

            if candidates:
                found_count += 1

            GLib.idle_add(self._on_track_identified, item, candidates)

            # Pequeña pausa respetando el límite de AcoustID (máx 3 req/s)
            for _ in range(7):
                if self._cancelled:
                    return
                time.sleep(0.05)

        if not self._cancelled:
            GLib.idle_add(self._on_all_finished, found_count, total)

    def _update_progress(self, current_idx: int, total: int, filename: str) -> bool:
        if self._cancelled:
            return False
        self.progress_bar.set_fraction(current_idx / max(total, 1))
        self.status_label.set_label(
            i18n.t("fingerprint.batch_progress", current=current_idx + 1, total=total, filename=filename)
        )
        return False

    def _on_track_identified(self, item: dict, candidates: list[dict]) -> bool:
        if self._cancelled:
            return False

        row: Adw.ActionRow = item["row"]
        check: Gtk.CheckButton = item["check"]
        old_suffix = item.get("suffix_widget")
        if old_suffix:
            row.remove(old_suffix)
            item["suffix_widget"] = None

        item["candidates"] = candidates

        if candidates:
            chosen = candidates[0]
            item["chosen"] = chosen
            check.set_active(True)
            check.set_sensitive(True)

            subtitle_text = " · ".join(part for part in (chosen.get("title"), chosen.get("artist"), chosen.get("album")) if part)
            row.set_subtitle(subtitle_text)

            if len(candidates) > 1:
                # Selector desplegable si hay múltiples versiones o lanzamientos
                labels = [
                    " · ".join(part for part in (c.get("album"), c.get("title")) if part) or c.get("title", "")
                    for c in candidates
                ]
                dropdown = Gtk.DropDown.new_from_strings(labels)
                dropdown.set_valign(Gtk.Align.CENTER)

                def on_candidate_changed(dd, _param, data_dict=item, cands=candidates, target_row=row):
                    selected_idx = dd.get_selected()
                    if 0 <= selected_idx < len(cands):
                        new_chosen = cands[selected_idx]
                        data_dict["chosen"] = new_chosen
                        sub = " · ".join(part for part in (new_chosen.get("title"), new_chosen.get("artist"), new_chosen.get("album")) if part)
                        target_row.set_subtitle(sub)

                dropdown.connect("notify::selected", on_candidate_changed)
                row.add_suffix(dropdown)
                item["suffix_widget"] = dropdown
            else:
                ok_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                ok_icon.add_css_class("accent")
                ok_icon.set_valign(Gtk.Align.CENTER)
                row.add_suffix(ok_icon)
                item["suffix_widget"] = ok_icon
        else:
            check.set_active(False)
            check.set_sensitive(False)
            row.set_subtitle(i18n.t("fingerprint.no_match"))
            none_label = Gtk.Label(label="—")
            none_label.add_css_class("dim-label")
            none_label.set_valign(Gtk.Align.CENTER)
            row.add_suffix(none_label)
            item["suffix_widget"] = none_label

        self._update_apply_button()
        return False

    def _on_all_finished(self, found_count: int, total: int) -> bool:
        if self._cancelled:
            return False
        self.progress_bar.set_fraction(1.0)
        self.status_label.set_label(
            i18n.t("fingerprint.batch_done", found=found_count, total=total)
        )
        self._update_apply_button()
        return False

    def _on_apply(self, _button) -> None:
        results: list[tuple[AudioTrack, dict]] = []
        for item in self._row_data:
            if item["check"].get_active() and item["chosen"]:
                results.append((item["track"], item["chosen"]))

        if results:
            self.emit("matches-applied", results)
        self.close()
