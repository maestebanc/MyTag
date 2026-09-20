%define srcdir %{getenv:MYTAG_SRCDIR}
%define pysitelib %(python3 -c "import sys; print(f'/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages')")

Name:           mytag
Version:        0.62.1
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
MyTag is a simple, focused tag and cover art editor for FLAC, MP3, M4A, OGG
and OPUS music files on Linux. Load a file or a whole folder of albums at once,
edit as many tracks together as you like, and search for cover art
online (MusicBrainz and iTunes) without leaving the app.

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
* Sun Sep 20 2026 Miguel Angel Esteban - 0.62.1-1
- Expanded format support: edit tags and cover art on M4A/MP4, Ogg Vorbis, and Opus.
- Automatic audio file integrity check on import with background async verification.
- Clear error icons, tooltip diagnostics, and top-of-table sorting for corrupt files.
- Dedicated Disc Number column enabled by default with numeric sorting.
- Application title bar displays program name and active version number.
- Python 3.14 compatibility and dynamic sitelib detection.

* Fri Sep 18 2026 Miguel Angel Esteban - 0.62.0-1
- Interactive drag-and-drop column reordering with visual drop indicators.
- Column customization: toggle visibility, adjust widths, and preserve custom order across sessions.
- Dynamic table sizing with automatic expansion of the last visible column to fill remaining space.
- Embedded symbolic SVG icons for full cross-distribution compatibility including Debian.

* Thu Sep 17 2026 Miguel Angel Esteban - 0.61.0-1
- Inspector panel redesign with album cover at the top as visual anchor.
- Compact zero-scroll layout with all metadata fields visible simultaneously.
- Direct inline editing of cover dimensions maintaining aspect ratio.
- Unified compact status banner in tag editor.

* Wed Sep 16 2026 Miguel Angel Esteban - 0.60.0-1
- Unified two-pane layout with merged tag and cover inspector panel and full-width track table.
- Added Album column to track list with integrated search filtering.
- Right-click context menu for all track actions directly from the song table.
- Simplified header bar with dedicated Revert changes button.
- Built-in AcoustID client key with zero-configuration fingerprinting.
- Bundled chromaprint (fpcalc) and host music collection access in Flatpak.
- Clean cover resize inputs without stepper buttons.
- Refined completeness warnings restricted to missing Title, Artist/AlbumArtist, or Cover.
- Added Feature Guide dialog explaining all functions and options.
- Customizable track number zero-padding and renaming pattern in Preferences.

* Wed Sep 16 2026 Miguel Angel Esteban - 0.52.0-1
- Batch audio fingerprint identification for multiple tracks with progress and candidate selection.
- Multi-track tag dropdown picker to inspect distinct values and unify tags across tracks in one click.
- Fixed AcoustID metadata resolution and smart original studio album ranking.

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
