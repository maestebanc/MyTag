"""Utilidades para cargar y redimensionar portadas de álbum."""
from __future__ import annotations

import io
import mimetypes

from PIL import Image

from .constants import COVER_SIZE


def read_image_file(path: str) -> tuple[bytes, str]:
    """Lee un archivo de imagen del disco y devuelve (bytes, mime_type)."""
    with open(path, "rb") as f:
        data = f.read()
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/jpeg"
    return data, mime


def resize_image_bytes(data: bytes, size: tuple[int, int] = COVER_SIZE) -> tuple[bytes, str]:
    """Redimensiona una imagen (bytes) para que quepa en el tamaño dado,
    manteniendo su proporción original (sin recortar). Por ejemplo, una
    imagen de 5000x4900 con size=(500, 500) queda en 500x490."""
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    max_w, max_h = size
    ratio = min(max_w / img.width, max_h / img.height)
    new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    resized = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def image_dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size
