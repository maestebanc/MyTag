import os
import sys

# Configurar entorno de Windows antes de inicializar bibliotecas gráficas
if sys.platform == "win32":
    try:
        import ctypes
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
        for cand in (
            os.path.join(base_dir, "etc", "fonts"),
            os.path.join(os.path.dirname(sys.executable), "_internal", "etc", "fonts"),
        ):
            if os.path.isdir(cand):
                os.environ.setdefault("FONTCONFIG_PATH", cand)
                break

from mytag.app import main

if __name__ == "__main__":
    sys.exit(main())
