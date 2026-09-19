"""Configuración persistente de MyTag (idioma, escala de interfaz)."""
from __future__ import annotations

import json
import os

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

SUPPORTED_LANGUAGES = ["es", "en", "ca"]
# Si el idioma del sistema no es ninguno de los soportados, se usa este.
DEFAULT_LANGUAGE_FALLBACK = "en"

DEFAULT_COLUMNS = {
    "status": {"visible": True, "width": 36},
    "tracknumber": {"visible": True, "width": 56},
    "title": {"visible": True, "width": 280},
    "artist": {"visible": True, "width": 200},
    "album": {"visible": True, "width": 220},
    "albumartist": {"visible": False, "width": 200},
    "date": {"visible": False, "width": 80},
    "genre": {"visible": False, "width": 130},
    "filename": {"visible": False, "width": 260},
    "discnumber": {"visible": True, "width": 65},
}

DEFAULT_COLUMN_ORDER = list(DEFAULT_COLUMNS.keys())

DEFAULTS = {
    "ui_scale": 100,
    "theme": "system",  # "system", "light" o "dark"
    "autonumber_zero_padding": False,
    "default_rename_pattern": "%tracknumber% - %artist% - %title%",
    "check_integrity_on_import": True,
    "columns": DEFAULT_COLUMNS,
    "column_order": DEFAULT_COLUMN_ORDER,
    "window_width": 1260,
    "window_height": 860,
    "window_maximized": False,
}


def _detect_system_language() -> str:
    """Idioma del sistema (variables LANGUAGE/LC_ALL/LC_MESSAGES/LANG), si es
    uno de los soportados; si no, DEFAULT_LANGUAGE_FALLBACK."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if not value:
            continue
        for part in value.split(":"):
            code = part.split(".")[0].split("_")[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code
    try:
        import locale
        loc = locale.getlocale()[0]
        if loc:
            code = loc.split("_")[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code
    except Exception:
        pass
    return DEFAULT_LANGUAGE_FALLBACK


def _config_path() -> str:
    config_dir = os.path.join(GLib.get_user_config_dir(), "mytag")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def load_config() -> dict:
    path = _config_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    is_first_run = "language" not in data
    if is_first_run:
        data["language"] = _detect_system_language()

    merged = dict(DEFAULTS)
    merged.update(data)

    # Asegurar que columns contiene todas las claves por defecto completas
    cols = {k: dict(v) for k, v in DEFAULT_COLUMNS.items()}
    if "columns" in data and isinstance(data["columns"], dict):
        for k, v in data["columns"].items():
            if k in cols and isinstance(v, dict):
                cols[k].update(v)
    merged["columns"] = cols

    # Asegurar orden de columnas coherente y completo
    order = list(DEFAULT_COLUMN_ORDER)
    if "column_order" in data and isinstance(data["column_order"], list):
        user_order = [k for k in data["column_order"] if k in DEFAULT_COLUMNS]
        for k in DEFAULT_COLUMN_ORDER:
            if k not in user_order:
                user_order.append(k)
        order = user_order
    merged["column_order"] = order

    if "base_dpi" in merged:
        del merged["base_dpi"]

    if "base_dpi" in data:
        del data["base_dpi"]
        save_config(data)

    if is_first_run:
        save_config(merged)

    return merged


def save_config(config: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
