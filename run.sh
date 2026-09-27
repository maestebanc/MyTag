#!/usr/bin/env bash
# Lanza MyTag usando el entorno virtual del proyecto o Python del sistema.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Seleccionar intérprete de Python
if [ -x "$DIR/.venv/bin/python" ]; then
    PYTHON="$DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Error: No se encontró Python 3 en el sistema." >&2
    exit 1
fi

# Comprobar si faltan dependencias básicas (mutagen, Pillow, PyGObject)
if ! "$PYTHON" -c "import mutagen, PIL, gi" >/dev/null 2>&1; then
    # Si no existe .venv, intentar crearlo automáticamente con acceso a librerías del sistema
    if [ ! -d "$DIR/.venv" ]; then
        echo "==> Configurando entorno para MyTag por primera vez..."
        if python3 -m venv --system-site-packages "$DIR/.venv" 2>/dev/null && [ -x "$DIR/.venv/bin/pip" ]; then
            echo "==> Instalando dependencias (mutagen, Pillow)..."
            "$DIR/.venv/bin/pip" install --quiet mutagen Pillow
            PYTHON="$DIR/.venv/bin/python"
        fi
    fi

    # Si aún faltan dependencias, guiar al usuario según su distribución
    if ! "$PYTHON" -c "import mutagen, PIL, gi" >/dev/null 2>&1; then
        echo "" >&2
        echo "⚠️  Faltan dependencias para ejecutar MyTag." >&2
        echo "" >&2
        echo "Para instalarlas en Debian / Ubuntu / Linux Mint:" >&2
        echo "  sudo apt install python3-mutagen python3-pil python3-gi gir1.2-gtk-4.0 gir1.2-adw-1" >&2
        echo "" >&2
        echo "Para instalarlas en Fedora:" >&2
        echo "  sudo dnf install python3-mutagen python3-pillow python3-gobject gtk4 libadwaita" >&2
        echo "" >&2
        echo "Para instalarlas en Arch Linux:" >&2
        echo "  sudo pacman -S python-mutagen python-pillow python-gobject gtk4 libadwaita" >&2
        echo "" >&2
        echo "O bien crea un entorno virtual manual:" >&2
        echo "  python3 -m venv --system-site-packages .venv" >&2
        echo "  .venv/bin/pip install mutagen Pillow" >&2
        echo "" >&2
        exit 1
    fi
fi

export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m mytag "$@"
