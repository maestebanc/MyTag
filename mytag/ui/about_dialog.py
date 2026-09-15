"""Diálogo "Acerca de MyTag"."""
from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk

from .. import __version__, i18n
from .style import APP_ID


def build_about_dialog() -> Adw.AboutDialog:
    dialog = Adw.AboutDialog(
        application_name="MyTag",
        application_icon=APP_ID,
        developer_name="maestebanc",
        version=__version__,
        comments=i18n.t("about.comments"),
        website="https://github.com/maestebanc/MyTag",
        issue_url="https://github.com/maestebanc/MyTag/issues",
        developers=["maestebanc"],
        copyright="© 2026 maestebanc",
        license_type=Gtk.License.MIT_X11,
    )
    return dialog
