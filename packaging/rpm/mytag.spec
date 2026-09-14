%define srcdir %{getenv:MYTAG_SRCDIR}
%define pysitelib /usr/lib/python3.13/site-packages

Name:           mytag
Version:        0.10.0
Release:        0.1.alpha0%{?dist}
Summary:        Edit tags and cover art on your FLAC music files
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
MyTag is a simple, focused tag and cover art editor for FLAC music
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

%files
%{pysitelib}/mytag
/usr/bin/mytag
/usr/share/applications/com.maestebanc.MyTag.desktop
/usr/share/metainfo/com.maestebanc.MyTag.metainfo.xml
/usr/share/icons/hicolor/*/apps/com.maestebanc.MyTag.png

%post
update-desktop-database -q /usr/share/applications &>/dev/null || :
gtk-update-icon-cache -q /usr/share/icons/hicolor &>/dev/null || :

%changelog
* Mon Sep 14 2026 maestebanc - 0.10.0-0.1.alpha0
- First preliminary alpha release.
