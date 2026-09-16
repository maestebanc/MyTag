"""Definición de los campos de etiqueta soportados por MyTag."""

# Claves Vorbis Comment usadas en el FLAC. Las etiquetas visibles en la
# interfaz se obtienen vía i18n.t(f"tag.{key.lower()}").
TAG_KEYS = [
    "TITLE",
    "ARTIST",
    "ALBUM",
    "ALBUMARTIST",
    "DATE",
    "GENRE",
    "TRACKNUMBER",
    "DISCNUMBER",
]

COVER_SIZE = (500, 500)

SUPPORTED_EXTENSIONS = (".flac", ".mp3")

# Clave de cliente de la aplicación registrada para AcoustID (pública)
ACOUSTID_CLIENT_KEY = "paY8Ml6JIz"
