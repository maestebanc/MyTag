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
    # ---- pantalla de bienvenida / estado vacío ----
    "empty.title": {
        "es": "Edita las etiquetas de tu música",
        "en": "Edit your music tags",
        "ca": "Edita les etiquetes de la teva música",
    },
    "empty.description": {
        "es": "Abre archivos de audio (FLAC, MP3) o arrastra carpetas directamente aquí para comenzar.",
        "en": "Open audio files (FLAC, MP3) or drag folders directly here to get started.",
        "ca": "Obre fitxers d'àudio (FLAC, MP3) o arrossega carpetes directament aquí per començar.",
    },
    "list.status_summary": {
        "es": "{total} tema(s)",
        "en": "{total} track(s)",
        "ca": "{total} tema(es)",
    },
    "list.status_selected": {
        "es": "{total} tema(s) · {selected} seleccionado(s)",
        "en": "{total} track(s) · {selected} selected",
        "ca": "{total} tema(es) · {selected} seleccionat(s)",
    },
    "cover.search_button": {
        "es": "Buscar portada…",
        "en": "Search cover…",
        "ca": "Cerca portada…",
    },
    "cover.drag_hint": {
        "es": "Arrastra una imagen o busca en línea",
        "en": "Drag an image or search online",
        "ca": "Arrossega una imatge o cerca en línia",
    },
    "editor.badge_one": {
        "es": "1 tema",
        "en": "1 track",
        "ca": "1 tema",
    },
    "editor.badge_many": {
        "es": "{n} temas",
        "en": "{n} tracks",
        "ca": "{n} temes",
    },
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
        "es": "Abre archivos o una carpeta con FLAC o MP3 para empezar.",
        "en": "Open files or a folder with FLAC or MP3 to get started.",
        "ca": "Obre fitxers o una carpeta amb FLAC o MP3 per començar.",
    },
    # ---- diálogos de archivo ----
    "dialog.open_files.title": {"es": "Abrir archivos de audio", "en": "Open audio files", "ca": "Obre fitxers d'àudio"},
    "dialog.open_files.filter_name": {"es": "Archivos de audio compatibles (*.flac, *.mp3, *.m4a, *.ogg, *.opus)", "en": "Supported audio files (*.flac, *.mp3, *.m4a, *.ogg, *.opus)", "ca": "Fitxers d'àudio compatibles (*.flac, *.mp3, *.m4a, *.ogg, *.opus)"},
    "dialog.open_folder.title": {"es": "Abrir carpeta", "en": "Open folder", "ca": "Obre una carpeta"},
    "dialog.no_flac_found": {
        "es": "No se encontraron archivos de audio compatibles (FLAC, MP3, M4A, OGG, OPUS) en esa carpeta.",
        "en": "No supported audio files (FLAC, MP3, M4A, OGG, OPUS) were found in that folder.",
        "ca": "No s'ha trobat cap fitxer d'àudio compatible (FLAC, MP3, M4A, OGG, OPUS) en aquesta carpeta.",
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
    "action.close": {"es": "Cerrar", "en": "Close", "ca": "Tanca"},
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
    "column.status": {"es": "Estado / Avisos", "en": "Status / Warnings", "ca": "Estat / Avisos"},
    "column.track": {"es": "Nº", "en": "Trk", "ca": "Núm."},
    "column.title": {"es": "Título", "en": "Title", "ca": "Títol"},
    "column.artist": {"es": "Artista", "en": "Artist", "ca": "Artista"},
    "column.album": {"es": "Álbum", "en": "Album", "ca": "Àlbum"},
    "column.albumartist": {"es": "Artista del álbum", "en": "Album artist", "ca": "Artista de l'àlbum"},
    "column.date": {"es": "Año", "en": "Year", "ca": "Any"},
    "column.genre": {"es": "Género", "en": "Genre", "ca": "Gènere"},
    "column.disc": {"es": "Disco", "en": "Disc", "ca": "Disc"},
    "column.filename": {"es": "Nombre de archivo", "en": "Filename", "ca": "Nom de fitxer"},
    "column.menu_title": {"es": "Columnas", "en": "Columns", "ca": "Columnes"},
    "column.menu_tooltip": {"es": "Configurar columnas visibles", "en": "Configure visible columns", "ca": "Configura columnes visibles"},
    "column.reset_widths": {"es": "Restablecer orden y anchos predeterminados", "en": "Reset to default order and widths", "ca": "Restaura l'ordre i les amplades per defecte"},
    "completeness.title": {"es": "título", "en": "title", "ca": "títol"},
    "completeness.artist": {"es": "artista", "en": "artist", "ca": "artista"},
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
        "es": "Selecciona uno o varios archivos en la tabla.",
        "en": "Select one or more files in the table.",
        "ca": "Selecciona un o diversos fitxers a la taula.",
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
    "editor.picker_tooltip": {
        "es": "Elegir entre los valores de los temas seleccionados",
        "en": "Choose from values in selected tracks",
        "ca": "Tria entre els valors dels temes seleccionats",
    },
    "editor.picker_title": {
        "es": "Valores en la selección",
        "en": "Values in selection",
        "ca": "Valors a la selecció",
    },
    "editor.track_count": {
        "es": "{n} tema(s)",
        "en": "{n} track(s)",
        "ca": "{n} tema(es)",
    },
    # ---- panel de portada ----
    "cover.select_image": {"es": "Seleccionar imagen…", "en": "Select image…", "ca": "Selecciona una imatge…"},
    "cover.musicbrainz_search": {
        "es": "Buscar en MusicBrainz…",
        "en": "Search on MusicBrainz…",
        "ca": "Cerca a MusicBrainz…",
    },
    "cover.resize": {"es": "Redimensionar", "en": "Resize", "ca": "Redimensiona"},
    "cover.resize_action": {
        "es": "Redimensionar portada…",
        "en": "Resize cover…",
        "ca": "Redimensiona la portada…",
    },
    "cover.resize_dialog_title": {
        "es": "Redimensionar portada",
        "en": "Resize cover",
        "ca": "Redimensiona la portada",
    },
    "cover.current_size": {
        "es": "Tamaño actual: {w} × {h} px",
        "en": "Current size: {w} × {h} px",
        "ca": "Mida actual: {w} × {h} px",
    },
    "cover.different_sizes": {
        "es": "Múltiples portadas (se ajustarán a un cuadrado)",
        "en": "Multiple covers (will be cropped to a square)",
        "ca": "Múltiples portades (s'ajustaran a un quadrat)",
    },
    "cover.target_dimensions": {
        "es": "Dimensiones deseadas",
        "en": "Target dimensions",
        "ca": "Dimensions desitjades",
    },
    "cover.width_label": {
        "es": "Ancho (px)",
        "en": "Width (px)",
        "ca": "Amplada (px)",
    },
    "cover.height_label": {
        "es": "Alto (px)",
        "en": "Height (px)",
        "ca": "Alçada (px)",
    },
    "cover.proportional_switch": {
        "es": "Mantener proporciones",
        "en": "Keep aspect ratio",
        "ca": "Mantenir proporcions",
    },
    "cover.apply_resize": {
        "es": "Redimensionar",
        "en": "Resize",
        "ca": "Redimensiona",
    },
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
    "cover.nothing_to_resize": {
        "es": "No hay portada que redimensionar.",
        "en": "There is no cover to resize.",
        "ca": "No hi ha cap portada per redimensionar.",
    },
    "cover.edit_dimensions_tooltip": {
        "es": "Clic para cambiar tamaño (Intro para aplicar)",
        "en": "Click to resize (Enter to apply)",
        "ca": "Clica per canviar la mida (Intro per aplicar)",
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
    "prefs.check_integrity_on_import": {
        "es": "Comprobar integridad al importar",
        "en": "Check integrity on import",
        "ca": "Comprova la integritat en importar",
    },
    "prefs.check_integrity_on_import_subtitle": {
        "es": "Verifica en segundo plano los archivos FLAC y MP3 y avisa si hay errores",
        "en": "Background-checks FLAC and MP3 files and alerts if corruption is detected",
        "ca": "Verifica en segon pla els fitxers FLAC i MP3 i avisa si hi ha errors",
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
    "prefs.organization_group": {
        "es": "Archivos y numeración",
        "en": "Files & numbering",
        "ca": "Fitxers i numeració",
    },
    "prefs.naming_options": {
        "es": "Opciones de numeración y renombrado",
        "en": "Numbering & renaming options",
        "ca": "Opcions de numeració i reanomenat",
    },
    "prefs.naming_options_subtitle": {
        "es": "Plantilla de nombrado y formato de pista",
        "en": "Naming template and track number format",
        "ca": "Plantilla d'anomenat i format de pista",
    },
    "prefs.zero_padding": {
        "es": "Rellenar pista con ceros (01, 02…)",
        "en": "Pad track numbers with zero (01, 02…)",
        "ca": "Omple la pista amb zeros (01, 02…)",
    },
    "prefs.zero_padding_subtitle": {
        "es": "Usa dos dígitos en lugar de '1, 2…' al autonumerar",
        "en": "Use two digits instead of '1, 2…' when auto-numbering",
        "ca": "Usa dos dígits en lloc d'«1, 2…» en numerar automàticament",
    },
    "prefs.default_rename_pattern": {
        "es": "Patrón de renombrado por defecto",
        "en": "Default renaming pattern",
        "ca": "Patró de reanomenat per defecte",
    },
    "toolbar.revert": {
        "es": "Deshacer cambios sin guardar",
        "en": "Discard unsaved changes",
        "ca": "Desfés els canvis sense desar",
    },
    "menu.feature_guide": {
        "es": "Guía de funciones",
        "en": "Feature Guide",
        "ca": "Guia de funcions",
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
        "es": "Edita etiquetas y portadas de tus archivos FLAC y MP3",
        "en": "Edit tags and cover art on your FLAC and MP3 music files",
        "ca": "Edita etiquetes i portades dels teus fitxers FLAC i MP3",
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
    "integrity.problems_found_desc": {
        "es": "Se han detectado problemas de integridad en {n} archivo(s):",
        "en": "Integrity problems detected in {n} file(s):",
        "ca": "S'han detectat problemes d'integritat en {n} fitxer(s):",
    },
    "integrity.error_tooltip": {
        "es": "Error de integridad",
        "en": "Integrity error",
        "ca": "Error d'integritat",
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
    "fingerprint.batch_title": {
        "es": "Identificar temas por huella de audio",
        "en": "Identify tracks by audio fingerprint",
        "ca": "Identifica temes per empremta d'àudio",
    },
    "fingerprint.batch_progress": {
        "es": "Identificando {current} de {total}: {filename}…",
        "en": "Identifying {current} of {total}: {filename}…",
        "ca": "Identificant {current} de {total}: {filename}…",
    },
    "fingerprint.batch_done": {
        "es": "Identificación completada: {found} de {total} tema(s) identificados.",
        "en": "Identification complete: {found} of {total} track(s) identified.",
        "ca": "Identificació completada: {found} de {total} tema(es) identificats.",
    },
    "fingerprint.batch_applied": {
        "es": "Etiquetas aplicadas a {n} tema(s).",
        "en": "Tags applied to {n} track(s).",
        "ca": "Etiquetes aplicades a {n} tema(es).",
    },
    "fingerprint.apply_button": {
        "es": "Aplicar a {n} tema(s)",
        "en": "Apply to {n} track(s)",
        "ca": "Aplica a {n} tema(es)",
    },
    "fingerprint.no_match": {
        "es": "Sin coincidencias",
        "en": "No match found",
        "ca": "Sense coincidències",
    },
    "fingerprint.select_all": {
        "es": "Seleccionar todos",
        "en": "Select all",
        "ca": "Selecciona-ho tot",
    },
    "fingerprint.deselect_all": {
        "es": "Deseleccionar todos",
        "en": "Deselect all",
        "ca": "Deselecciona-ho tot",
    },
    # ---- guía de funciones ----
    "guide.title": {
        "es": "Guía de funciones de MyTag",
        "en": "MyTag Feature Guide",
        "ca": "Guia de funcions de MyTag",
    },
    "guide.subtitle": {
        "es": "Resumen estructurado de herramientas y flujos de trabajo",
        "en": "Structured overview of tools and workflows",
        "ca": "Resum estructurat d'eines i fluxos de treball",
    },
    "guide.fingerprint_title": {
        "es": "Identificación por huella acústica (AcoustID)",
        "en": "Audio Fingerprint Identification (AcoustID)",
        "ca": "Identificació per empremta acústica (AcoustID)",
    },
    "guide.fingerprint_desc": {
        "es": "Calcula la huella digital de tus archivos con fpcalc y consulta la base de datos de AcoustID/MusicBrainz. Funciona de manera individual o por lotes con selector de álbumes candidatos, priorizando álbumes de estudio originales.",
        "en": "Calculates acoustic fingerprints with fpcalc and queries AcoustID/MusicBrainz. Operates individually or in bulk with candidate release selection, prioritizing original studio albums.",
        "ca": "Calcula l'empremta digital dels teus fitxers amb fpcalc i consulta la base de dades d'AcoustID/MusicBrainz. Funciona individualment o per lots amb selector d'àlbums candidats, prioritzant àlbums d'estudi originals.",
    },
    "guide.cover_title": {
        "es": "Búsqueda y gestión de carátulas",
        "en": "Cover Art Search & Management",
        "ca": "Cerca i gestió de caràtules",
    },
    "guide.cover_desc": {
        "es": "Descarga carátulas de alta resolución desde MusicBrainz e iTunes Store, arrastra imágenes directamente a la ventana, redimensiona proporcionalmente al tamaño que elijas y recorta a formato cuadrado.",
        "en": "Fetch high-resolution covers from MusicBrainz and iTunes Store, drag and drop images directly into the window, resize proportionally to any dimension, and crop to square.",
        "ca": "Descarrega caràtules d'alta resolució des de MusicBrainz i iTunes Store, arrossega imatges directament a la finestra, redimensiona proporcionalment a la mida que triïs i retalla a format quadrat.",
    },
    "guide.tags_title": {
        "es": "Editor de etiquetas y selector múltiple",
        "en": "Tag Editor & Multi-Value Picker",
        "ca": "Editor d'etiquetes i selector múltiple",
    },
    "guide.tags_desc": {
        "es": "Edita metadatos completos en FLAC y MP3. En selecciones múltiples con valores distintos, un desplegable te muestra todos los valores existentes y te permite unificarlos en todas las pistas de un solo clic.",
        "en": "Full metadata editing across FLAC and MP3. On multi-track selections with mixed values, a dropdown lets you view all values and unify them across all tracks in a single click.",
        "ca": "Edita metadades completes a FLAC i MP3. En seleccions múltiples amb valors diferents, un desplegable et mostra tots els valors existents i et permet unificar-los a tots els temes d'un sol clic.",
    },
    "guide.renaming_title": {
        "es": "Renombrado de archivos y autonumeración",
        "en": "File Renaming & Auto-Numbering",
        "ca": "Reanomenat de fitxers i autonumeració",
    },
    "guide.renaming_desc": {
        "es": "Renombra tus archivos de música a partir de sus etiquetas usando plantillas (%tracknumber% - %artist% - %title%) manteniendo su extensión. Autonumera canciones en orden secuencial con o sin ceros a la izquierda.",
        "en": "Batch-rename files from tags with pattern templates (%tracknumber% - %artist% - %title%) preserving original extensions. Automatically number tracks with optional zero padding.",
        "ca": "Reanomena els teus fitxers a partir de les seves etiquetes usant plantilles (%tracknumber% - %artist% - %title%) mantenint la seva extensió. Autonumera cançons en ordre seqüencial amb o sense zeros.",
    },
    "guide.integrity_title": {
        "es": "Verificación de integridad de audio",
        "en": "Audio Stream Integrity Verification",
        "ca": "Verificació d'integritat d'àudio",
    },
    "guide.integrity_desc": {
        "es": "Detecta archivos dañados validando el flujo de audio con 'flac --test' en pistas FLAC e inspeccionando tramas y cabeceras en archivos MP3 para asegurar que tu colección esté perfecta.",
        "en": "Detects damaged audio files by verifying stream data via 'flac --test' on FLAC files and inspecting frames and headers on MP3 tracks.",
        "ca": "Detecta fitxers danyats validant el flux d'àudio amb 'flac --test' en pistes FLAC i inspeccionant trames i capçaleres en fitxers MP3 per assegurar que la teva col·lecció estigui perfecta.",
    },
    "guide.context_title": {
        "es": "Menú contextual y acciones rápidas",
        "en": "Context Menu & Quick Actions",
        "ca": "Menú contextual i accions ràpides",
    },
    "guide.context_desc": {
        "es": "Haz clic derecho sobre cualquier tema de la tabla para acceder a todas las acciones de forma inmediata. Usa el botón 'Deshacer cambios' en la cabecera para revertir cambios sin guardar antes de confirmar.",
        "en": "Right-click any track in the list to access all actions immediately. Use the 'Discard unsaved changes' button in the header bar to revert in-memory edits before saving.",
        "ca": "Fes clic dret sobre qualsevol tema de la taula per accedir a totes les accions d'immediat. Usa el botó 'Desfés els canvis sense desar' a la capçalera per revertir canvis abans de desar.",
    },
}
