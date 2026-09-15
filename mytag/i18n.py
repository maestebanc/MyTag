"""Internacionalización de MyTag: español, inglés y catalán."""
from __future__ import annotations

from . import config as _config
from .config import SUPPORTED_LANGUAGES

# El nombre de cada idioma se muestra siempre en sí mismo (autoglotónimo),
# no se traduce según el idioma activo.
LANGUAGE_NAMES = {"es": "Español", "en": "English", "ca": "Català"}

FALLBACK_LANGUAGE = "es"

_cfg = _config.load_config()
_current_language = _cfg.get("language", FALLBACK_LANGUAGE)
if _current_language not in SUPPORTED_LANGUAGES:
    _current_language = FALLBACK_LANGUAGE


def get_language() -> str:
    return _current_language


def set_language(lang: str) -> None:
    global _current_language
    if lang not in SUPPORTED_LANGUAGES:
        return
    _current_language = lang
    cfg = _config.load_config()
    cfg["language"] = lang
    _config.save_config(cfg)


def t(key: str, **kwargs) -> str:
    """Traduce `key` al idioma activo, con placeholders opcionales estilo str.format."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_language) or entry.get(FALLBACK_LANGUAGE) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


STRINGS: dict[str, dict[str, str]] = {
    # ---- barra de herramientas / ventana principal ----
    "toolbar.open": {"es": "Abrir", "en": "Open", "ca": "Obre"},
    "toolbar.open_files": {"es": "Abrir archivos…", "en": "Open files…", "ca": "Obre fitxers…"},
    "toolbar.open_folder": {"es": "Abrir carpeta…", "en": "Open folder…", "ca": "Obre una carpeta…"},
    "toolbar.remove": {"es": "Quitar seleccionados", "en": "Remove selected", "ca": "Treu els seleccionats"},
    "toolbar.save": {"es": "Guardar cambios", "en": "Save changes", "ca": "Desa els canvis"},
    "toolbar.preferences": {"es": "Preferencias", "en": "Preferences", "ca": "Preferències"},
    "toolbar.search": {"es": "Buscar", "en": "Search", "ca": "Cerca"},
    "toolbar.more_actions": {"es": "Más acciones", "en": "More actions", "ca": "Més accions"},
    "menu.autonumber": {
        "es": "Autonumerar pistas seleccionadas",
        "en": "Auto-number selected tracks",
        "ca": "Numera automàticament els temes seleccionats",
    },
    "menu.revert_selected": {
        "es": "Revertir cambios de los seleccionados",
        "en": "Revert changes to selected tracks",
        "ca": "Reverteix els canvis dels temes seleccionats",
    },
    "menu.identify_fingerprint": {
        "es": "Identificar por huella de audio…",
        "en": "Identify by audio fingerprint…",
        "ca": "Identifica per empremta d'àudio…",
    },
    "menu.check_integrity": {
        "es": "Verificar integridad",
        "en": "Verify integrity",
        "ca": "Verifica la integritat",
    },
    "menu.rename_from_tags": {
        "es": "Renombrar según etiquetas…",
        "en": "Rename from tags…",
        "ca": "Reanomena segons les etiquetes…",
    },
    "menu.fill_missing_covers": {
        "es": "Rellenar portadas que faltan…",
        "en": "Fill in missing covers…",
        "ca": "Omple les portades que falten…",
    },
    "list.clear_all": {"es": "Vaciar lista", "en": "Clear list", "ca": "Buida la llista"},
    "list.search_placeholder": {
        "es": "Buscar por título o artista…",
        "en": "Search by title or artist…",
        "ca": "Cerca per títol o artista…",
    },
    "window.unsaved_changes": {
        "es": "{n} cambio(s) sin guardar",
        "en": "{n} unsaved change(s)",
        "ca": "{n} canvi(s) sense desar",
    },
    "toast.startup": {
        "es": "Abre archivos o una carpeta con FLAC para empezar.",
        "en": "Open files or a folder with FLAC to get started.",
        "ca": "Obre fitxers o una carpeta amb FLAC per començar.",
    },
    # ---- diálogos de archivo ----
    "dialog.open_files.title": {"es": "Abrir archivos FLAC", "en": "Open FLAC files", "ca": "Obre fitxers FLAC"},
    "dialog.open_files.filter_name": {"es": "Archivos FLAC", "en": "FLAC files", "ca": "Fitxers FLAC"},
    "dialog.open_folder.title": {"es": "Abrir carpeta", "en": "Open folder", "ca": "Obre una carpeta"},
    "dialog.no_flac_found": {
        "es": "No se encontraron archivos FLAC en esa carpeta.",
        "en": "No FLAC files were found in that folder.",
        "ca": "No s'ha trobat cap fitxer FLAC en aquesta carpeta.",
    },
    "dialog.load_errors_title": {
        "es": "Algunos archivos no se pudieron cargar",
        "en": "Some files could not be loaded",
        "ca": "Alguns fitxers no s'han pogut carregar",
    },
    "dialog.save_error_title": {"es": "Error al guardar", "en": "Error saving", "ca": "Error en desar"},
    "dialog.unsaved_title": {"es": "Cambios sin guardar", "en": "Unsaved changes", "ca": "Canvis sense desar"},
    "dialog.unsaved_body": {
        "es": "Hay cambios sin guardar. ¿Quieres salir sin guardarlos?",
        "en": "There are unsaved changes. Do you want to quit without saving them?",
        "ca": "Hi ha canvis sense desar. Vols sortir sense desar-los?",
    },
    "app.title": {"es": "MyTag", "en": "MyTag", "ca": "MyTag"},
    # ---- toasts ----
    "toast.files_added": {
        "es": "{added} archivo(s) añadido(s). Total: {total}.",
        "en": "{added} file(s) added. Total: {total}.",
        "ca": "{added} fitxer(s) afegit(s). Total: {total}.",
    },
    "toast.total_files": {
        "es": "Total: {total} archivo(s) en la lista.",
        "en": "Total: {total} file(s) in the list.",
        "ca": "Total: {total} fitxer(s) a la llista.",
    },
    "toast.cover_mb_applied": {
        "es": "Portada de MusicBrainz aplicada. Recuerda guardar.",
        "en": "Cover from MusicBrainz applied. Remember to save.",
        "ca": "Portada de MusicBrainz aplicada. Recorda desar.",
    },
    "toast.no_pending_changes": {
        "es": "No hay cambios pendientes de guardar.",
        "en": "There are no pending changes to save.",
        "ca": "No hi ha canvis pendents de desar.",
    },
    "toast.save_done": {
        "es": "Guardado completado ({saved} archivo(s)).",
        "en": "Save complete ({saved} file(s)).",
        "ca": "Desat completat ({saved} fitxer(s)).",
    },
    # ---- acciones comunes ----
    "action.cancel": {"es": "Cancelar", "en": "Cancel", "ca": "Cancel·la"},
    "action.discard": {"es": "Salir sin guardar", "en": "Quit without saving", "ca": "Surt sense desar"},
    "action.ok": {"es": "Vale", "en": "OK", "ca": "D'acord"},
    "action.accept": {"es": "Aceptar", "en": "Accept", "ca": "Accepta"},
    "action.continue": {"es": "Continuar", "en": "Continue", "ca": "Continua"},
    "action.save": {"es": "Guardar", "en": "Save", "ca": "Desa"},
    # ---- confirmaciones de pérdida de cambios sin guardar ----
    "confirm.discard_unsaved_body": {
        "es": "Hay {n} tema(s) con cambios sin guardar. Si continúas, se perderán. "
        "¿Quieres continuar?",
        "en": "There are {n} track(s) with unsaved changes. If you continue, they "
        "will be lost. Do you want to continue?",
        "ca": "Hi ha {n} tema(es) amb canvis sense desar. Si continues, es "
        "perdran. Vols continuar?",
    },
    # ---- toasts de las nuevas acciones de lista ----
    "toast.autonumbered": {
        "es": "Numeración aplicada a {n} tema(s).",
        "en": "Numbering applied to {n} track(s).",
        "ca": "Numeració aplicada a {n} tema(es).",
    },
    "toast.reverted": {
        "es": "Cambios descartados en {n} tema(s).",
        "en": "Changes discarded for {n} track(s).",
        "ca": "Canvis descartats a {n} tema(es).",
    },
    # ---- portada: pegar desde el portapapeles ----
    "cover.paste": {"es": "Pegar portada", "en": "Paste cover", "ca": "Enganxa la portada"},
    "cover.paste_no_image": {
        "es": "El portapapeles no contiene ninguna imagen.",
        "en": "The clipboard doesn't contain an image.",
        "ca": "El porta-retalls no conté cap imatge.",
    },
    # ---- MusicBrainz (validación) ----
    "mb.title": {"es": "MusicBrainz", "en": "MusicBrainz", "ca": "MusicBrainz"},
    "mb.select_tracks_first": {
        "es": "Selecciona antes uno o varios temas.",
        "en": "Select one or more tracks first.",
        "ca": "Selecciona abans un o diversos temes.",
    },
    "mb.need_same_album_artist": {
        "es": "Todos los temas seleccionados deben compartir el mismo Álbum y el mismo "
        "Artista del álbum (y ninguno de los dos puede estar vacío) para poder "
        "buscar la portada.",
        "en": "All selected tracks must share the same Album and the same Album "
        "Artist (and neither can be empty) to search for a cover.",
        "ca": "Tots els temes seleccionats han de compartir el mateix Àlbum i el mateix "
        "Artista de l'àlbum (i cap dels dos pot estar buit) per poder cercar la portada.",
    },
    # ---- columnas de la tabla de pistas ----
    "column.track": {"es": "Nº", "en": "Trk", "ca": "Núm."},
    "column.title": {"es": "Título", "en": "Title", "ca": "Títol"},
    "column.artist": {"es": "Artista", "en": "Artist", "ca": "Artista"},
    "completeness.cover": {"es": "portada", "en": "cover", "ca": "portada"},
    "completeness.date": {"es": "año", "en": "year", "ca": "any"},
    "completeness.genre": {"es": "género", "en": "genre", "ca": "gènere"},
    "completeness.tooltip": {
        "es": "Falta: {fields}",
        "en": "Missing: {fields}",
        "ca": "Falta: {fields}",
    },
    # ---- campos de etiqueta ----
    "tag.title": {"es": "Título", "en": "Title", "ca": "Títol"},
    "tag.artist": {"es": "Artista", "en": "Artist", "ca": "Artista"},
    "tag.album": {"es": "Álbum", "en": "Album", "ca": "Àlbum"},
    "tag.albumartist": {"es": "Artista del álbum", "en": "Album artist", "ca": "Artista de l'àlbum"},
    "tag.date": {"es": "Año", "en": "Year", "ca": "Any"},
    "tag.genre": {"es": "Género", "en": "Genre", "ca": "Gènere"},
    "tag.tracknumber": {"es": "Nº de pista", "en": "Track number", "ca": "Núm. de pista"},
    "tag.discnumber": {"es": "Nº de disco", "en": "Disc number", "ca": "Núm. de disc"},
    # ---- editor de etiquetas ----
    "editor.heading": {"es": "Etiquetas", "en": "Tags", "ca": "Etiquetes"},
    "editor.select_prompt": {
        "es": "Selecciona uno o varios archivos FLAC en la tabla.",
        "en": "Select one or more FLAC files in the table.",
        "ca": "Selecciona un o diversos fitxers FLAC a la taula.",
    },
    "editor.editing_one": {"es": "Editando: {filename}", "en": "Editing: {filename}", "ca": "Editant: {filename}"},
    "editor.editing_many": {
        "es": "Editando {n} temas a la vez",
        "en": "Editing {n} tracks at once",
        "ca": "Editant {n} temes alhora",
    },
    "editor.multiple_values": {
        "es": "‹valores distintos›",
        "en": "‹multiple values›",
        "ca": "‹valors diferents›",
    },
    # ---- panel de portada ----
    "cover.select_image": {"es": "Seleccionar imagen…", "en": "Select image…", "ca": "Selecciona una imatge…"},
    "cover.musicbrainz_search": {
        "es": "Buscar en MusicBrainz…",
        "en": "Search on MusicBrainz…",
        "ca": "Cerca a MusicBrainz…",
    },
    "cover.resize": {"es": "Redimensionar", "en": "Resize", "ca": "Redimensiona"},
    "cover.remove": {"es": "Quitar portada", "en": "Remove cover", "ca": "Treu la portada"},
    "cover.no_cover": {"es": "Sin portada", "en": "No cover", "ca": "Sense portada"},
    "cover.no_tracks_loaded": {"es": "Sin temas cargados", "en": "No tracks loaded", "ca": "Cap tema carregat"},
    "cover.multiple_covers": {
        "es": "Varias portadas distintas",
        "en": "Multiple different covers",
        "ca": "Diverses portades diferents",
    },
    "cover.tracks_selected_count": {
        "es": "{n} temas seleccionados",
        "en": "{n} tracks selected",
        "ca": "{n} temes seleccionats",
    },
    "cover.invalid_image": {"es": "Imagen no válida", "en": "Invalid image", "ca": "Imatge no vàlida"},
    "cover.select_dialog_title": {
        "es": "Seleccionar portada",
        "en": "Select cover",
        "ca": "Selecciona la portada",
    },
    "cover.images_filter_name": {"es": "Imágenes", "en": "Images", "ca": "Imatges"},
    "cover.different_covers_cant_resize": {
        "es": "Los temas seleccionados tienen portadas distintas.",
        "en": "The selected tracks have different covers.",
        "ca": "Els temes seleccionats tenen portades diferents.",
    },
    "cover.nothing_to_resize": {
        "es": "No hay portada que redimensionar.",
        "en": "There is no cover to resize.",
        "ca": "No hi ha cap portada per redimensionar.",
    },
    # ---- diálogo de búsqueda de portada ----
    "coversearch.title": {"es": "Buscar portada", "en": "Search for cover", "ca": "Cerca la portada"},
    "coversearch.loading": {
        "es": "Buscando portadas…",
        "en": "Searching for covers…",
        "ca": "Cercant portades…",
    },
    "coversearch.downloading": {
        "es": "Descargando portada…",
        "en": "Downloading cover…",
        "ca": "Descarregant la portada…",
    },
    "coversearch.no_results_title": {"es": "Sin portadas", "en": "No covers", "ca": "Sense portades"},
    "coversearch.no_results_desc": {
        "es": "No se encontró ninguna portada para este álbum y artista.",
        "en": "No cover was found for this album and artist.",
        "ca": "No s'ha trobat cap portada per a aquest àlbum i artista.",
    },
    "coversearch.search_failed_title": {
        "es": "No se pudo buscar",
        "en": "Search failed",
        "ca": "No s'ha pogut cercar",
    },
    "coversearch.download_failed_title": {
        "es": "No se pudo descargar",
        "en": "Download failed",
        "ca": "No s'ha pogut descarregar",
    },
    "coversearch.loading_item": {"es": "Cargando…", "en": "Loading…", "ca": "Carregant…"},
    "coversearch.load_error": {"es": "Error al cargar", "en": "Error loading", "ca": "Error en carregar"},
    # ---- errores de red ----
    "error.mb_busy": {
        "es": "El servidor de MusicBrainz está ocupado ahora mismo. Inténtalo de nuevo en unos segundos.",
        "en": "The MusicBrainz server is busy right now. Try again in a few seconds.",
        "ca": "El servidor de MusicBrainz està ocupat ara mateix. Torna-ho a provar d'aquí a uns segons.",
    },
    "error.mb_connect": {
        "es": "No se pudo conectar con MusicBrainz: {reason}",
        "en": "Could not connect to MusicBrainz: {reason}",
        "ca": "No s'ha pogut connectar amb MusicBrainz: {reason}",
    },
    "error.itunes_connect": {
        "es": "No se pudo conectar con iTunes: {reason}",
        "en": "Could not connect to iTunes: {reason}",
        "ca": "No s'ha pogut connectar amb iTunes: {reason}",
    },
    "error.download_image": {
        "es": "No se pudo descargar la imagen: {reason}",
        "en": "Could not download the image: {reason}",
        "ca": "No s'ha pogut descarregar la imatge: {reason}",
    },
    # ---- preferencias ----
    "prefs.title": {"es": "Preferencias", "en": "Preferences", "ca": "Preferències"},
    "prefs.general_group": {"es": "General", "en": "General", "ca": "General"},
    "prefs.language": {"es": "Idioma", "en": "Language", "ca": "Idioma"},
    "prefs.language_restart_note": {
        "es": "MyTag debe reiniciarse para aplicar el nuevo idioma.",
        "en": "MyTag needs to restart to apply the new language.",
        "ca": "El MyTag s'ha de reiniciar per aplicar el nou idioma.",
    },
    "prefs.appearance_group": {"es": "Apariencia", "en": "Appearance", "ca": "Aparença"},
    "prefs.ui_scale": {
        "es": "Escala de la interfaz",
        "en": "Interface scale",
        "ca": "Escala de la interfície",
    },
    "prefs.ui_scale_custom": {"es": "Personalizada (%)", "en": "Custom (%)", "ca": "Personalitzada (%)"},
    "prefs.ui_scale_custom_option": {"es": "Personalizada…", "en": "Custom…", "ca": "Personalitzada…"},
    "prefs.save": {"es": "Guardar", "en": "Save", "ca": "Desa"},
    "prefs.theme": {"es": "Tema", "en": "Theme", "ca": "Tema"},
    "prefs.theme_system": {"es": "Del sistema", "en": "System", "ca": "Del sistema"},
    "prefs.theme_light": {"es": "Claro", "en": "Light", "ca": "Clar"},
    "prefs.theme_dark": {"es": "Oscuro", "en": "Dark", "ca": "Fosc"},
    "prefs.acoustid_group": {
        "es": "AcoustID (identificación por huella de audio)",
        "en": "AcoustID (audio fingerprint identification)",
        "ca": "AcoustID (identificació per empremta d'àudio)",
    },
    "prefs.acoustid_key": {"es": "Clave de API", "en": "API key", "ca": "Clau d'API"},
    "prefs.acoustid_key_note": {
        "es": "Gratis en acoustid.org/api-key. También hace falta tener instalado "
        "el programa «fpcalc» (paquete chromaprint).",
        "en": "Free at acoustid.org/api-key. You also need the “fpcalc” tool "
        "installed (chromaprint package).",
        "ca": "Gratuïta a acoustid.org/api-key. També cal tenir instal·lat el "
        "programa «fpcalc» (paquet chromaprint).",
    },
    # ---- menú principal / acerca de / atajos ----
    "menu.primary": {"es": "Menú principal", "en": "Main menu", "ca": "Menú principal"},
    "menu.preferences": {"es": "Preferencias", "en": "Preferences", "ca": "Preferències"},
    "menu.keyboard_shortcuts": {
        "es": "Atajos de teclado",
        "en": "Keyboard Shortcuts",
        "ca": "Dreceres de teclat",
    },
    "menu.about": {"es": "Acerca de MyTag", "en": "About MyTag", "ca": "Quant al MyTag"},
    "about.comments": {
        "es": "Edita etiquetas y portadas de tus archivos FLAC",
        "en": "Edit tags and cover art on your FLAC music files",
        "ca": "Edita etiquetes i portades dels teus fitxers FLAC",
    },
    "shortcuts.title": {"es": "Atajos de teclado", "en": "Keyboard Shortcuts", "ca": "Dreceres de teclat"},
    "shortcuts.group_general": {"es": "General", "en": "General", "ca": "General"},
    "shortcuts.open_files": {"es": "Abrir archivos", "en": "Open files", "ca": "Obre fitxers"},
    "shortcuts.save": {"es": "Guardar cambios", "en": "Save changes", "ca": "Desa els canvis"},
    "shortcuts.toggle_search": {"es": "Buscar en la lista", "en": "Search the list", "ca": "Cerca a la llista"},
    "shortcuts.remove_selected": {
        "es": "Quitar temas seleccionados",
        "en": "Remove selected tracks",
        "ca": "Treu els temes seleccionats",
    },
    "shortcuts.preferences": {"es": "Preferencias", "en": "Preferences", "ca": "Preferències"},
    "shortcuts.shortcuts_window": {
        "es": "Mostrar esta ventana",
        "en": "Show this window",
        "ca": "Mostra aquesta finestra",
    },
    "shortcuts.quit": {"es": "Salir de MyTag", "en": "Quit MyTag", "ca": "Surt del MyTag"},
    # ---- verificación de integridad ----
    "integrity.title": {"es": "Verificar integridad", "en": "Verify integrity", "ca": "Verifica la integritat"},
    "integrity.flac_not_found": {
        "es": "No se encontró el programa «flac» en el sistema, necesario para esta comprobación.",
        "en": "The “flac” tool was not found on this system; it's required for this check.",
        "ca": "No s'ha trobat el programa «flac» al sistema, necessari per a aquesta comprovació.",
    },
    "integrity.problems_title": {
        "es": "Problemas de integridad encontrados",
        "en": "Integrity problems found",
        "ca": "S'han trobat problemes d'integritat",
    },
    "integrity.all_ok": {
        "es": "{n} archivo(s) verificado(s) sin problemas.",
        "en": "{n} file(s) verified with no problems.",
        "ca": "{n} fitxer(s) verificat(s) sense problemes.",
    },
    # ---- rellenar portadas que faltan ----
    "fillcovers.none_missing": {
        "es": "Ningún álbum cargado tiene la portada sin poner.",
        "en": "No loaded album is missing a cover.",
        "ca": "Cap àlbum carregat li falta la portada.",
    },
    "fillcovers.done": {
        "es": "Revisión de portadas completada.",
        "en": "Cover review complete.",
        "ca": "Revisió de portades completada.",
    },
    # ---- renombrar según etiquetas ----
    "rename.title": {"es": "Renombrar según etiquetas", "en": "Rename from tags", "ca": "Reanomena segons les etiquetes"},
    "rename.pattern": {"es": "Patrón", "en": "Pattern", "ca": "Patró"},
    "rename.tokens_hint": {
        "es": "Campos disponibles: %title% %artist% %album% %albumartist% %date% "
        "%genre% %tracknumber% %discnumber%. El número de pista y de disco se "
        "rellenan a 2 dígitos en el nombre de archivo.",
        "en": "Available fields: %title% %artist% %album% %albumartist% %date% "
        "%genre% %tracknumber% %discnumber%. Track and disc numbers are "
        "zero-padded to 2 digits in the filename.",
        "ca": "Camps disponibles: %title% %artist% %album% %albumartist% %date% "
        "%genre% %tracknumber% %discnumber%. El número de pista i de disc "
        "s'omplen a 2 dígits en el nom de fitxer.",
    },
    "rename.unchanged": {"es": "(sin cambios)", "en": "(unchanged)", "ca": "(sense canvis)"},
    "rename.confirm": {"es": "Renombrar", "en": "Rename", "ca": "Reanomena"},
    "rename.done": {
        "es": "{n} archivo(s) renombrado(s).",
        "en": "{n} file(s) renamed.",
        "ca": "{n} fitxer(s) reanomenat(s).",
    },
    "rename.errors_title": {
        "es": "Algunos archivos no se pudieron renombrar",
        "en": "Some files could not be renamed",
        "ca": "Alguns fitxers no s'han pogut reanomenar",
    },
    "rename.collision": {
        "es": "Ya existe un archivo llamado «{name}»",
        "en": "A file named “{name}” already exists",
        "ca": "Ja existeix un fitxer anomenat «{name}»",
    },
    # ---- identificación por huella de audio ----
    "fingerprint.title": {
        "es": "Identificar por huella de audio",
        "en": "Identify by audio fingerprint",
        "ca": "Identifica per empremta d'àudio",
    },
    "fingerprint.no_api_key": {
        "es": "Configura tu clave de API de AcoustID en Preferencias antes de usar esto.",
        "en": "Set your AcoustID API key in Preferences before using this.",
        "ca": "Configura la teva clau d'API d'AcoustID a Preferències abans d'utilitzar-ho.",
    },
    "fingerprint.fpcalc_missing": {
        "es": "No se encontró el programa «fpcalc» (paquete chromaprint) en el sistema.",
        "en": "The “fpcalc” tool (chromaprint package) was not found on this system.",
        "ca": "No s'ha trobat el programa «fpcalc» (paquet chromaprint) al sistema.",
    },
    "fingerprint.loading": {
        "es": "Calculando huella de audio…",
        "en": "Calculating audio fingerprint…",
        "ca": "Calculant l'empremta d'àudio…",
    },
    "fingerprint.no_matches_title": {
        "es": "Sin coincidencias",
        "en": "No matches",
        "ca": "Sense coincidències",
    },
    "fingerprint.no_matches_desc": {
        "es": "No se encontró ninguna coincidencia para este tema.",
        "en": "No match was found for this track.",
        "ca": "No s'ha trobat cap coincidència per a aquest tema.",
    },
    "fingerprint.error_title": {
        "es": "No se pudo identificar",
        "en": "Could not identify",
        "ca": "No s'ha pogut identificar",
    },
    "fingerprint.applied": {
        "es": "Etiquetas aplicadas desde la identificación.",
        "en": "Tags applied from the identification.",
        "ca": "Etiquetes aplicades des de la identificació.",
    },
}
