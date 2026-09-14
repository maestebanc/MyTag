"""Configuración persistente de MyTag (idioma, escala de interfaz)."""
from __future__ import annotations

import json
import os

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

DEFAULTS = {
    "language": "es",
    "ui_scale": 100,
}


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
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save_config(config: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
