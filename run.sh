#!/usr/bin/env bash
# Lanza MyTag usando el entorno virtual del proyecto.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/.venv/bin/python" -m mytag "$@"
