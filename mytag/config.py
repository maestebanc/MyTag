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

DEFAULTS = {
    "ui_scale": 100,
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

    if is_first_run:
        save_config(merged)

    return merged


def save_config(config: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
