%define srcdir %{getenv:MYTAG_SRCDIR}
%define pysitelib /usr/lib/python3.13/site-packages

Name:           mytag
Version:        0.51.0
Release:        1%{?dist}
Summary:        Edit tags and cover art on your FLAC and MP3 music files
License:        MIT
URL:            https://github.com/maestebanc/MyTag
BuildArch:      noarch

Requires:       python3 >= 3.11
Requires:       python3-mutagen
Requires:       python3-pillow
Requires:       python3-gobject
Requires:       gtk4 >= 4.10
Requires:       libadwaita >= 1.4

%description
MyTag is a simple, focused tag and cover art editor for FLAC and MP3 music
files on Linux. Load a file or a whole folder of albums at once,
edit as many tracks together as you like, and search for cover art
online (MusicBrainz and iTunes) without leaving the app.

This package targets distributions using Python 3.13 at
%{pysitelib}; adjust that path when building for a different Python
version.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{pysitelib}
cp -r %{srcdir}/mytag %{buildroot}%{pysitelib}/
find %{buildroot}%{pysitelib}/mytag -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

mkdir -p %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/mytag <<'LAUNCHER'
#!/usr/bin/python3
import sys
from mytag.app import main
if __name__ == "__main__":
    sys.exit(main())
LAUNCHER
chmod 755 %{buildroot}/usr/bin/mytag

mkdir -p %{buildroot}/usr/share/applications
cp %{srcdir}/data/com.maestebanc.MyTag.desktop %{buildroot}/usr/share/applications/

mkdir -p %{buildroot}/usr/share/metainfo
cp %{srcdir}/data/com.maestebanc.MyTag.metainfo.xml %{buildroot}/usr/share/metainfo/

for size in 16 22 24 32 48 64 128 256 512; do
  mkdir -p %{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps
  cp %{srcdir}/data/icons/hicolor/${size}x${size}/apps/com.maestebanc.MyTag.png %{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps/
done
mkdir -p %{buildroot}/usr/share/icons/hicolor/scalable/apps
cp %{srcdir}/data/icons/hicolor/scalable/apps/com.maestebanc.MyTag.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/

%files
%{pysitelib}/mytag
/usr/bin/mytag
/usr/share/applications/com.maestebanc.MyTag.desktop
/usr/share/metainfo/com.maestebanc.MyTag.metainfo.xml
/usr/share/icons/hicolor/*/apps/com.maestebanc.MyTag.png
/usr/share/icons/hicolor/*/apps/com.maestebanc.MyTag.svg

%post
update-desktop-database -q /usr/share/applications &>/dev/null || :
gtk-update-icon-cache -q /usr/share/icons/hicolor &>/dev/null || :

%changelog
* Wed Sep 16 2026 Miguel Angel Esteban - 0.51.0-1
- Full MP3 support with ID3v2.4 frames and embedded APIC cover art.
- Audio stream integrity checks for MP3 and FLAC.
- AcoustID audio fingerprinting across both formats.
- Extension-aware filename pattern renaming.
- Typography refinement aligned with native desktop DPI and Nautilus font metrics.

* Tue Sep 15 2026 Miguel Angel Esteban - 0.50.0-1
- Major UI modernization with responsive track table layout.
- Balanced margins, symmetrical layout and composite action buttons.
- Robust AcoustID fingerprinting decoding 24-bit/multi-channel FLACs.
- Updated documentation and screenshots.

* Tue Sep 15 2026 Miguel Angel Esteban - 0.20.0-0.1.alpha0
- Fix drag & drop from external apps (Nautilus) on Hyprland/wlroots.
- Fix saving after renaming files from tags.
- Cover resize: edit width/height directly, proportionally linked;
  selecting tracks with different covers now resizes each one to a
  matching square instead of refusing.
- Track list columns reordered (Nº, Artist, Title) and freed from a
  hidden minimum width that capped how far they could be resized.
- Cover and tags panels can now be resized against each other.
- Drop CSV export.
* Tue Sep 15 2026 Miguel Angel Esteban - 0.11.0-0.1.alpha0
- Second alpha release: context menus, new icon, light/dark theme
  override, About dialog, keyboard shortcuts, drag & drop for cover
  images, audio fingerprint identification (AcoustID), FLAC
  integrity check, batch cover fill-in, completeness indicator,
  CSV export, and renaming files from tags.
* Mon Sep 14 2026 Miguel Angel Esteban - 0.10.0-0.1.alpha0
- First preliminary alpha release.
