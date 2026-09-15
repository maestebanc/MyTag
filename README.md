# MyTag

**A clean, fast, and modern tag and cover art editor for FLAC audio files on Linux.**

MyTag is built from the ground up with Python, GTK4, and Libadwaita to provide a focused, native, and reliable workflow for managing FLAC music collections. Whether you want to quickly fix a single track or clean up metadata across hundreds of albums, MyTag gives you full control with safe batch editing and integrated artwork lookup.

![MyTag Main Window](screenshots/main-window.png)

---

## Highlights

- **Designed for the Modern Linux Desktop**: Native GTK4 and Libadwaita user interface following modern GNOME design standards. Respects system dark and light modes, supports UI scaling, and integrates seamlessly with Wayland and X11 compositors.
- **Safe Batch Tagging**: Edit individual tracks or entire albums simultaneously. When multiple files with differing tags are selected, fields clearly display `‹multiple values›`, preventing accidental data loss or unwanted overwrites.
- **Responsive Three-Pane Workflow**:
  - **Track List**: Clear status column, fixed track numbering, and auto-expanding artist and title columns that adapt fluidly to window width.
  - **Cover Art Studio**: Centered album artwork display, dimensional controls, proportional resizing, and fast context actions.
  - **Tag Editor**: Comprehensive metadata editor with dedicated fields for title, artist, album, album artist, release date/year, genre, track index/total, and disc index/total.
- **Smart Online Cover Art Search**: Search and retrieve high-resolution album covers directly from MusicBrainz Cover Art Archive and iTunes Store without opening an external browser.
- **AcoustID Audio Fingerprinting**: Identify untagged or mislabeled files using Chromaprint (`fpcalc`) and the AcoustID database, decoding both standard and high-resolution 24-bit/multi-channel FLAC streams.
- **Batch Cover Fill-in**: Scan your library to detect missing album covers and batch-search artwork for all incomplete releases in sequence.
- **File Organization & Auto-Numbering**: Rename audio files directly from tags using flexible syntax templates (e.g. `{track:02d} - {title}.flac`), or renumber tracks sequentially with a single click.
- **Integrity Verification**: Verify the audio stream integrity of any loaded FLAC file using the official `flac` validator.
- **Multi-Lingual Support**: Native translations in **English**, **Catalan** (*Català*), and **Spanish** (*Español*), automatically detected from system settings or configurable in preferences.
- **Non-Destructive In-Memory Staging**: All metadata edits, artwork changes, and file renames exist in memory until you explicitly click **Save changes**. Unsaved modifications can be inspected or reverted at any point.

![Searching for cover art on MusicBrainz and iTunes](screenshots/cover-search.png)

---

## Features Overview

| Feature | Description |
| :--- | :--- |
| **Supported Tags** | Title, Artist, Album, Album Artist, Year / Date, Genre, Track Number (and Total), Disc Number (and Total). |
| **Cover Art Sources** | Local file chooser, Drag & Drop (files or images), Clipboard paste, MusicBrainz, and iTunes. |
| **Image Operations** | Proportional resizing, square cropping, removal, export to file, and metadata extraction. |
| **Audio Fingerprinting** | Chromaprint / fpcalc integration via AcoustID API to resolve release metadata. |
| **File Renaming** | Pattern-based batch renaming with live preview and automatic directory handling. |
| **File Inspection** | Built-in per-track completeness warnings and FLAC stream integrity checking. |
| **Drag & Drop** | Full support for dropping folders or FLAC files from Nautilus, Dolphin, Thunar, etc. |
| **Shortcuts & Access** | Standard GNOME keyboard shortcuts (`Ctrl+O`, `Ctrl+S`, `Ctrl+F`, `Ctrl+,`, `Ctrl+W`, etc.). |

---

## Installation

Prebuilt packages for version **0.50.0** are available on the [GitHub Releases](https://github.com/maestebanc/MyTag/releases) page.

### Flatpak (Universal across all Linux distributions)

The Flatpak bundle includes all runtime dependencies, including GTK4, Libadwaita, and audio tools:

```bash
flatpak install mytag-0.50.0.flatpak
```

### Debian / Ubuntu (24.04 LTS+, Debian trixie/sid)

Install the `.deb` package using `apt`:

```bash
sudo apt install ./mytag_0.50.0-1_all.deb
```

### Fedora / RHEL (RPM)

Install the `.rpm` package using `dnf`:

```bash
sudo dnf install ./mytag-0.50.0-1.noarch.rpm
```

### Arch Linux

Install the prebuilt package using `pacman`:

```bash
sudo pacman -U mytag-0.50.0-1-any.pkg.tar.zst
```

Or build from source using the included `PKGBUILD`:

```bash
cd packaging/arch
makepkg -si
```

---

## Running from Source

### 1. Install System Dependencies

Ensure Python 3.11+, GTK4, Libadwaita, and PyGObject are installed on your distribution:

**Arch Linux:**
```bash
sudo pacman -S --needed python python-gobject gtk4 libadwaita flac chromaprint
```

**Debian / Ubuntu (24.04+):**
```bash
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 flac libchromaprint-tools
```

**Fedora:**
```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita flac chromaprint-tools
```

### 2. Set Up Virtual Environment

Clone the repository and prepare the Python environment:

```bash
git clone https://github.com/maestebanc/MyTag.git
cd MyTag

# Create virtual environment inheriting system site-packages (required for PyGObject)
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Install Python package dependencies
pip install mutagen Pillow

# Launch MyTag
python3 -m mytag
```

---

## Optional Dependencies

- **`flac`**: Used by the *Verify integrity* tool to check audio streams for corruption (`flac -t`).
- **`chromaprint`** (or `fpcalc` / `libchromaprint-tools`): Required for *Identify by audio fingerprint* via AcoustID.

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>O</kbd> | Open files or folders |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Save all modified tracks |
| <kbd>Ctrl</kbd> + <kbd>F</kbd> | Toggle search / filter bar |
| <kbd>Ctrl</kbd> + <kbd>A</kbd> | Select all tracks |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Open Preferences |
| <kbd>Ctrl</kbd> + <kbd>?</kbd> | Open Keyboard Shortcuts cheat-sheet |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> / <kbd>Ctrl</kbd> + <kbd>W</kbd> | Quit application |
| <kbd>Delete</kbd> | Remove selected tracks from the list |

---

## License

MyTag is open source software released under the [MIT License](LICENSE).
