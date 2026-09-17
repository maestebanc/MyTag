"""Utilidad de ordenación natural (humana / alfanumérica) para MyTag."""
from __future__ import annotations

import re


def natural_sort_key(s: str) -> list[int | str]:
    """Genera una clave de ordenación natural para strings o rutas de archivo.

    Trata las secuencias numéricas dentro del texto como números enteros,
    garantizando que '1', '2', ..., '9', '10', '11' se ordenen en secuencia
    humana natural y no según código ASCII ('1', '10', '11', '2'...).
    """
    if not s:
        return [""]
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", s)]
