"""Definición de los campos de etiqueta soportados por MyTag."""

# Cada entrada: (clave Vorbis Comment usada en el FLAC, etiqueta en español para la UI)
TAG_FIELDS = [
    ("TITLE", "Título"),
    ("ARTIST", "Artista"),
    ("ALBUM", "Álbum"),
    ("ALBUMARTIST", "Artista del álbum"),
    ("DATE", "Año"),
    ("GENRE", "Género"),
    ("TRACKNUMBER", "Nº de pista"),
    ("DISCNUMBER", "Nº de disco"),
]

COVER_SIZE = (500, 500)

IMAGE_FILE_FILTER = "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp)"
FLAC_FILE_FILTER = "Archivos FLAC (*.flac)"
