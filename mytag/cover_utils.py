"""Utilidades para cargar y redimensionar portadas de álbum."""
from __future__ import annotations

import io
import mimetypes

from PIL import Image, ImageOps

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
    """Recorta y redimensiona una imagen (bytes) al tamaño dado, devolviendo JPEG."""
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    fitted = ImageOps.fit(img, size, Image.LANCZOS)
    buf = io.BytesIO()
    fitted.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def image_dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size
