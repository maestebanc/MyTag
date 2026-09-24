#!/usr/bin/env python3
"""Script para actualizar la versión de MyTag en todos los manifiestos, metadatos y la web.

Uso:
    python3 scripts/bump_version.py <nueva_version>

Ejemplo:
    python3 scripts/bump_version.py 0.63.0
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def update_pyproject(new_ver: str) -> None:
    path = ROOT / "pyproject.toml"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_ver}"', content, count=1)
    path.write_text(content, encoding="utf-8")
    print(f"✓ pyproject.toml -> {new_ver}")


def update_init(new_ver: str) -> None:
    path = ROOT / "mytag" / "__init__.py"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_ver}"', content, count=1)
    path.write_text(content, encoding="utf-8")
    print(f"✓ mytag/__init__.py -> {new_ver}")


def update_metainfo(new_ver: str) -> None:
    path = ROOT / "data" / "com.maestebanc.MyTag.metainfo.xml"
    content = path.read_text(encoding="utf-8")
    today = datetime.date.today().isoformat()

    # Si la versión ya está presente, solo actualizamos la fecha si es necesario
    if f'<release version="{new_ver}"' in content:
        content = re.sub(rf'<release version="{new_ver}" date="[^"]+"', f'<release version="{new_ver}" date="{today}"', content)
    else:
        # Insertar nuevo bloque de release al principio de <releases>
        release_block = f"""    <release version="{new_ver}" date="{today}">
      <description>
        <p>
          Version {new_ver} release notes.
        </p>
      </description>
    </release>
"""
        content = re.sub(r"(\s*<releases>\n)", r"\1" + release_block, content, count=1)

    path.write_text(content, encoding="utf-8")
    print(f"✓ data/com.maestebanc.MyTag.metainfo.xml -> {new_ver}")


def update_rpm_spec(new_ver: str) -> None:
    path = ROOT / "packaging" / "rpm" / "mytag.spec"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"Version:\s*[^\n]+", f"Version:        {new_ver}", content, count=1)
    path.write_text(content, encoding="utf-8")
    print(f"✓ packaging/rpm/mytag.spec -> {new_ver}")


def update_arch(new_ver: str) -> None:
    path = ROOT / "packaging" / "arch" / "PKGBUILD"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"pkgver=[^\n]+", f"pkgver={new_ver}", content, count=1)
    path.write_text(content, encoding="utf-8")
    print(f"✓ packaging/arch/PKGBUILD -> {new_ver}")


def update_windows(new_ver: str) -> None:
    path = ROOT / "packaging" / "windows" / "installer.iss"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'#define MyAppVersion\s*"[^"]+"', f'#define MyAppVersion "{new_ver}"', content, count=1)
    path.write_text(content, encoding="utf-8")
    print(f"✓ packaging/windows/installer.iss -> {new_ver}")


def update_flatpak_manifest(new_ver: str) -> None:
    path = ROOT / "packaging" / "flatpak" / "com.maestebanc.MyTag.yml"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"/tags/v[0-9.]+\.tar\.gz", f"/tags/v{new_ver}.tar.gz", content)
        path.write_text(content, encoding="utf-8")
        print(f"✓ packaging/flatpak/com.maestebanc.MyTag.yml -> {new_ver}")


def update_web(new_ver: str) -> None:
    index_path = ROOT / "web" / "index.html"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")

    # 1. Version badge
    content = re.sub(r'<span class="version-badge"[^>]*>v[0-9.]+</span>', f'<span class="version-badge">v{new_ver}</span>', content)

    # 2. Window title
    content = re.sub(r'<div class="window-title"[^>]*>MyTag — [0-9.]+</div>', f'<div class="window-title">MyTag — {new_ver}</div>', content)

    # 3. Flatpak command
    content = re.sub(r'mytag-[0-9.]+\.flatpak', f'mytag-{new_ver}.flatpak', content)

    # 4. Deb command
    content = re.sub(r'mytag_[0-9.]+-1_all\.deb', f'mytag_{new_ver}-1_all.deb', content)

    # 5. RPM command
    content = re.sub(r'mytag-[0-9.]+-1\.noarch\.rpm', f'mytag-{new_ver}-1.noarch.rpm', content)

    # 6. Arch command
    content = re.sub(r'mytag-[0-9.]+-1-any\.pkg\.tar\.zst', f'mytag-{new_ver}-1-any.pkg.tar.zst', content)

    index_path.write_text(content, encoding="utf-8")
    print(f"✓ web/index.html -> v{new_ver} (badge, títulos y comandos actualizados)")


def main() -> int:
    if len(sys.argv) < 2:
        print("Error: especifica la nueva versión (ej. 0.63.0)")
        return 1

    new_ver = sys.argv[1].strip().lstrip("v")
    print(f"=== Actualizando MyTag a versión {new_ver} ===")
    update_pyproject(new_ver)
    update_init(new_ver)
    update_metainfo(new_ver)
    update_rpm_spec(new_ver)
    update_arch(new_ver)
    update_windows(new_ver)
    update_flatpak_manifest(new_ver)
    update_web(new_ver)
    print(f"=== Actualización completa para versión {new_ver} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
