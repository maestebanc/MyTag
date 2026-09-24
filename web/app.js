/**
 * MyTag — Official Landing Page Script
 * Multi-language engine (ES, EN, CA), theme handling, interactive gallery, and copy helpers.
 */

// ==========================================
// 1. Translations Dictionary (ES, EN, CA)
// ==========================================
const translations = {
  es: {
    page_title: "MyTag — Editor nativo de etiquetas y carátulas para Linux",
    meta_desc: "MyTag es un editor de etiquetas y carátulas de audio nativo, moderno y rápido para Linux, diseñado con GTK4 y Libadwaita. Soporta FLAC, MP3, M4A, OGG y Opus.",
    
    // Header
    nav_features: "Características",
    nav_screenshots: "Capturas",
    nav_formats: "Formatos",
    nav_download: "Descargar",
    
    // Hero
    hero_badge: "Diseñado nativamente para GNOME & Linux",
    hero_title: "El editor de etiquetas y carátulas nativo para Linux",
    hero_subtitle: "Rápido, enfocado y diseñado con GTK4 y Libadwaita. Edita metadatos por lotes con total seguridad, busca portadas en alta resolución e identifica canciones con AcoustID.",
    btn_download: "Descargar para Linux",
    btn_github: "Código en GitHub",
    
    // Features Section
    feat_section_title: "Diseñado para amantes de la música",
    feat_section_desc: "Sin reproductores innecesarios ni bibliotecas pesadas. Sólo una herramienta precisa y moderna para dejar tus archivos de audio impecables.",
    
    feat_gtk_title: "GTK4 & Libadwaita Nativo",
    feat_gtk_text: "Integración total con el escritorio Linux moderno (GNOME, Wayland y X11). Sigue automáticamente tu tema claro u oscuro y respeta la escala de fuentes de tu sistema.",
    
    feat_batch_title: "Edición por Lotes Segura",
    feat_batch_text: "Edita álbumes completos a la vez. Cuando hay valores discrepantes, MyTag lo indica con claridad y te permite unificarlos mediante un selector desplegable. Nada se guarda en disco sin tu confirmación.",
    
    feat_cover_title: "Gestor Integral de Portadas",
    feat_cover_text: "Busca carátulas en MusicBrainz e iTunes sin salir de la app. Arrastra y suelta imágenes, pega desde el portapapeles, redimensiona con proporciones exactas y exporta la portada a archivo.",
    
    feat_acoustid_title: "Huella Acústica AcoustID",
    feat_acoustid_text: "¿Canciones sin etiquetar o con nombres incorrectos? Identifica pistas automáticamente mediante su huella de audio con Chromaprint (fpcalc), sin registros ni claves API que configurar.",
    
    feat_integrity_title: "Comprobación de Integridad",
    feat_integrity_text: "Verifica en segundo plano los flujos de audio al cargar carpetas. Detecta archivos dañados o incompletos con alertas visuales inmediatas antes de guardarlos.",
    
    feat_rename_title: "Renombrado & Listas M3U8",
    feat_rename_text: "Renombra tus archivos según sus metadatos con patrones configurables (%track% - %title%), autonumera pistas con ceros opcionales y genera listas de reproducción estándar M3U8.",
    
    // Gallery Section
    gallery_title: "Elegante, funcional y claro",
    gallery_desc: "Cada elemento está ubicado pensando en la máxima eficiencia y comodidad de uso.",
    tab_main: "Ventana Principal",
    tab_search: "Búsqueda de Carátulas",
    caption_main: "Vista principal: lista ordenada de pistas con indicadores de estado, panel inspector de carátula y etiquetas directas.",
    caption_search: "Búsqueda en línea: portadas en alta resolución descargadas directamente desde MusicBrainz e iTunes Store.",
    zoom_hint: "Haz clic para ampliar la imagen",
    gallery_title_main: "MyTag — Ventana Principal",
    gallery_title_search: "MyTag — Búsqueda de Carátulas",
    
    // Formats
    formats_title: "Compatibilidad amplia de formatos",
    formats_desc: "Soporta las extensiones y estándares más populares manteniendo intacta la calidad del audio.",
    fmt_flac_desc: "Comentarios Vorbis nativos e inserción de carátulas sin pérdidas en bloques de imagen FLAC.",
    fmt_mp3_desc: "Marcos estándar ID3v2.4 completos y portadas incrustadas en marcos APIC frontales.",
    fmt_m4a_desc: "Átomos estándar de metadatos de audio de Apple e imágenes incrustadas de alta resolución.",
    fmt_ogg_desc: "Etiquetas estándar Vorbis y portadas codificadas en bloques METADATA_BLOCK_PICTURE.",
    
    // Downloads
    download_title: "Instala MyTag en tu distribución",
    download_desc: "Elige el método de instalación que prefieras para tu sistema operativo Linux.",
    tag_universal: "Universal",
    tab_source: "Código Fuente",
    copy_btn: "Copiar",
    copied_btn: "¡Copiado!",
    
    inst_flatpak_title: "Paquete Flatpak Universal",
    inst_flatpak_desc: "La forma más recomendada. Incluye todas las dependencias aisladas, Chromaprint (fpcalc) y acceso a tu carpeta de música.",
    flathub_note: "Próximamente disponible de forma directa en Flathub (submission en revisión).",
    
    inst_deb_title: "Paquete para Debian, Ubuntu y derivados",
    inst_deb_desc: "Compatible con Ubuntu 24.04 LTS+, Linux Mint, Debian Trixie/Sid y sistemas basados en APT.",
    
    inst_fedora_title: "Paquete RPM para Fedora y RHEL",
    inst_fedora_desc: "Compatible con Fedora 40, 41, 42, Rawhide y distribuciones compatibles con DNF / RPM.",
    
    inst_arch_title: "Instalación en Arch Linux / Manjaro",
    inst_arch_desc: "Instala el paquete binario precompilado con Pacman o compílalo tú mismo con makepkg:",
    
    inst_source_title: "Ejecutar desde el código fuente",
    inst_source_desc: "Clona el repositorio oficial de GitHub y ejecútalo directamente con Python:",
    
    releases_text: "¿Buscas archivos individuales de instalación o notas de versión?",
    btn_releases: "Ver todas las descargas en GitHub Releases",
    
    // Footer
    footer_desc: "Editor de etiquetas y carátulas de audio nativo y enfocado para Linux.",
    footer_project: "Proyecto",
    footer_releases: "Versiones",
    footer_issues: "Informar de un error",
    footer_license_title: "Licencia",
    footer_author: "Por Miguel Angel Esteban"
  },

  en: {
    page_title: "MyTag — Native audio tag and cover art editor for Linux",
    meta_desc: "MyTag is a fast, clean, and native audio tag and cover art editor for Linux, crafted with GTK4 and Libadwaita. Supports FLAC, MP3, M4A, OGG, and Opus.",
    
    // Header
    nav_features: "Features",
    nav_screenshots: "Screenshots",
    nav_formats: "Formats",
    nav_download: "Download",
    
    // Hero
    hero_badge: "Natively crafted for GNOME & Linux",
    hero_title: "The native audio tag and cover art editor for Linux",
    hero_subtitle: "Fast, focused, and crafted with GTK4 and Libadwaita. Safe batch metadata editing, high-resolution cover art lookup, and AcoustID acoustic fingerprinting.",
    btn_download: "Download for Linux",
    btn_github: "GitHub Repository",
    
    // Features Section
    feat_section_title: "Built for music lovers",
    feat_section_desc: "No bloated playback engines or unnecessary libraries. Just a focused and reliable tool to get your audio metadata right.",
    
    feat_gtk_title: "Native GTK4 & Libadwaita",
    feat_gtk_text: "Seamless integration with the modern Linux desktop (GNOME, Wayland, and X11). Follows system dark or light style and desktop font scaling automatically.",
    
    feat_batch_title: "Safe Batch Editing",
    feat_batch_text: "Edit entire albums at once. When selected tracks have differing tags, MyTag flags them clearly and lets you unify values in a single click. Nothing is touched on disk until you hit Save.",
    
    feat_cover_title: "Comprehensive Cover Art Tools",
    feat_cover_text: "Search album covers from MusicBrainz and iTunes right within the app. Drag and drop images, paste from clipboard, resize with exact proportions, and export artwork to disk.",
    
    feat_acoustid_title: "AcoustID Audio Fingerprinting",
    feat_acoustid_text: "Untagged tracks or mislabeled files? Automatically identify songs by their audio fingerprint using Chromaprint (fpcalc), with zero API key configuration needed.",
    
    feat_integrity_title: "Audio Integrity Verification",
    feat_integrity_text: "Background async stream verification on import across all formats. Instantly highlights corrupt or truncated files before you save changes.",
    
    feat_rename_title: "File Renaming & M3U8 Playlists",
    feat_rename_text: "Rename files on disk directly from tags with customizable patterns (%track% - %title%), auto-number tracks with optional zero-padding, and export standard M3U8 playlists.",
    
    // Gallery Section
    gallery_title: "Clean, functional and intuitive",
    gallery_desc: "Every control is positioned for maximum productivity and ease of use.",
    tab_main: "Main Window",
    tab_search: "Cover Search",
    caption_main: "Main view: structured track table with status indicators, cover inspector, and instant tag editors.",
    caption_search: "Online search: high-resolution album artwork retrieved directly from MusicBrainz and iTunes Store.",
    zoom_hint: "Click to zoom image",
    gallery_title_main: "MyTag — Main Window",
    gallery_title_search: "MyTag — Cover Art Search",
    
    // Formats
    formats_title: "Comprehensive Format Support",
    formats_desc: "Full metadata and artwork compatibility across popular audio formats while preserving audio stream quality.",
    fmt_flac_desc: "Native Vorbis comments and lossless artwork blocks embedded in FLAC files.",
    fmt_mp3_desc: "Full ID3v2.4 frame editing and front cover art embedded in APIC frames.",
    fmt_m4a_desc: "Standard Apple audio metadata atoms and embedded high-resolution cover art.",
    fmt_ogg_desc: "Standard Vorbis comments and embedded METADATA_BLOCK_PICTURE artwork.",
    
    // Downloads
    download_title: "Install MyTag on your distribution",
    download_desc: "Select the installation method tailored for your Linux distribution.",
    tag_universal: "Universal",
    tab_source: "Source Code",
    copy_btn: "Copy",
    copied_btn: "Copied!",
    
    inst_flatpak_title: "Universal Flatpak Package",
    inst_flatpak_desc: "The recommended way. Includes all sandboxed dependencies, Chromaprint (fpcalc), and music folder access out of the box.",
    flathub_note: "Coming soon directly to Flathub (submission awaiting review).",
    
    inst_deb_title: "Debian, Ubuntu & Derivatives Package",
    inst_deb_desc: "Compatible with Ubuntu 24.04 LTS+, Linux Mint, Debian Trixie/Sid, and APT-based systems.",
    
    inst_fedora_title: "RPM Package for Fedora and RHEL",
    inst_fedora_desc: "Compatible with Fedora 40, 41, 42, Rawhide, and DNF / RPM-based systems.",
    
    inst_arch_title: "Arch Linux / Manjaro Installation",
    inst_arch_desc: "Install the prebuilt binary package using Pacman or compile from source using the included PKGBUILD:",
    
    inst_source_title: "Run from Source",
    inst_source_desc: "Clone the official GitHub repository and run directly with Python:",
    
    releases_text: "Looking for standalone packages or release notes?",
    btn_releases: "View all releases on GitHub",
    
    // Footer
    footer_desc: "Focused and native audio tag and cover art editor for Linux.",
    footer_project: "Project",
    footer_releases: "Releases",
    footer_issues: "Report an issue",
    footer_license_title: "License",
    footer_author: "By Miguel Angel Esteban"
  },

  ca: {
    page_title: "MyTag — Editor natiu d'etiquetes i caràtules per a Linux",
    meta_desc: "MyTag és un editor d'etiquetes i caràtules d'àudio natiu, modern i ràpid per a Linux, dissenyat amb GTK4 i Libadwaita. Suporta FLAC, MP3, M4A, OGG i Opus.",
    
    // Header
    nav_features: "Característiques",
    nav_screenshots: "Captures",
    nav_formats: "Formats",
    nav_download: "Descarregar",
    
    // Hero
    hero_badge: "Dissenyat nativament per a GNOME & Linux",
    hero_title: "L'editor d'etiquetes i caràtules natiu per a Linux",
    hero_subtitle: "Ràpid, enfocat i dissenyat amb GTK4 i Libadwaita. Edita metadades per lots amb total seguretat, cerca caràtules en alta resolució i identifica cançons amb AcoustID.",
    btn_download: "Descarregar per a Linux",
    btn_github: "Codi a GitHub",
    
    // Features Section
    feat_section_title: "Dissenyat per a amants de la música",
    feat_section_desc: "Sense reproductors innecessaris ni biblioteques feixugues. Només una eina precisa i moderna per deixar els teus fitxers d'àudio impecables.",
    
    feat_gtk_title: "GTK4 & Libadwaita Natiu",
    feat_gtk_text: "Integració total amb l'escriptori Linux modern (GNOME, Wayland i X11). Segueix automàticament el teu tema clar o fosc i respecta l'escala de lletra del teu sistema.",
    
    feat_batch_title: "Edició per Lots Segura",
    feat_batch_text: "Edita àlbums complets alhora. Quan hi ha valors diferents, MyTag ho indica clarament i et permet unificar-los amb un sol clic. Res no es desa al disc sense la teva confirmació.",
    
    feat_cover_title: "Gestor Integral de Caràtules",
    feat_cover_text: "Cerca caràtules a MusicBrainz i iTunes sense sortir de l'aplicació. Arrossega imatges, enganxa des del porta-retalls, redimensiona amb proporcions exactes i exporta la caràtula a un fitxer.",
    
    feat_acoustid_title: "Petjada Acústica AcoustID",
    feat_acoustid_text: "Cançons sense etiquetar o amb noms incorrectes? Identifica cançons automàticament mitjançant la seva petjada d'àudio amb Chromaprint (fpcalc), sense cap clau d'API.",
    
    feat_integrity_title: "Comprovació d'Integritat",
    feat_integrity_text: "Verificació en segon pla dels fluxos d'àudio en carregar carpetes. Detecta fitxers danyats o incomplets amb alertes visuals immediates abans de desar-los.",
    
    feat_rename_title: "Reanomenat & Llistes M3U8",
    feat_rename_text: "Reanomena els teus fitxers segons les seves metadades amb patrons configurables (%track% - %title%), autonumera pistes amb zeros opcionals i genera llistes estàndard M3U8.",
    
    // Gallery Section
    gallery_title: "Elegant, funcional i clar",
    gallery_desc: "Cada element està col·locat pensant en la màxima eficiència i comoditat d'ús.",
    tab_main: "Finestra Principal",
    tab_search: "Cerca de Caràtules",
    caption_main: "Vista principal: llista ordenada de pistes amb indicadors d'estat, inspector de caràtula i etiquetes directes.",
    caption_search: "Cerca en línia: caràtules en alta resolució descarregades directament des de MusicBrainz i iTunes Store.",
    zoom_hint: "Fes clic per ampliar la imatge",
    gallery_title_main: "MyTag — Finestra Principal",
    gallery_title_search: "MyTag — Cerca de Caràtules",
    
    // Formats
    formats_title: "Àmplia compatibilitat de formats",
    formats_desc: "Suporta les extensions i estàndards més populars mantenint intacta la qualitat de l'àudio.",
    fmt_flac_desc: "Comentaris Vorbis natius i inserció de caràtules sense pèrdues en blocs d'imatge FLAC.",
    fmt_mp3_desc: "Marcs estàndard ID3v2.4 complets i caràtules incrustades en marcs APIC frontals.",
    fmt_m4a_desc: "Àtoms estàndard de metadades d'àudio d'Apple i imatges incrustades en alta resolució.",
    fmt_ogg_desc: "Etiquetes estàndard Vorbis i caràtules codificades en blocs METADATA_BLOCK_PICTURE.",
    
    // Downloads
    download_title: "Instal·la MyTag a la teva distribució",
    download_desc: "Tria el mètode d'instal·lació preferit per al teu sistema operatiu Linux.",
    tag_universal: "Universal",
    tab_source: "Codi Font",
    copy_btn: "Copiar",
    copied_btn: "Copiat!",
    
    inst_flatpak_title: "Paquet Flatpak Universal",
    inst_flatpak_desc: "La manera més recomanada. Inclou totes les dependències aïllades, Chromaprint (fpcalc) i accés a la teva carpeta de música.",
    flathub_note: "Properament disponible directament a Flathub (submission en revisió).",
    
    inst_deb_title: "Paquet per a Debian, Ubuntu i derivats",
    inst_deb_desc: "Compatible amb Ubuntu 24.04 LTS+, Linux Mint, Debian Trixie/Sid i sistemes basats en APT.",
    
    inst_fedora_title: "Paquet RPM per a Fedora i RHEL",
    inst_fedora_desc: "Compatible amb Fedora 40, 41, 42, Rawhide i distribucions compatibles amb DNF / RPM.",
    
    inst_arch_title: "Instal·lació a Arch Linux / Manjaro",
    inst_arch_desc: "Instal·la el paquet binari precompilat amb Pacman o compila'l tu mateix amb makepkg:",
    
    inst_source_title: "Executar des del codi font",
    inst_source_desc: "Clona el repositori oficial de GitHub i executa'l directament amb Python:",
    
    releases_text: "Busques paquets individuals d'instal·lació o notes de la versió?",
    btn_releases: "Veure totes les descàrregues a GitHub Releases",
    
    // Footer
    footer_desc: "Editor d'etiquetes i caràtules d'àudio natiu i enfocat per a Linux.",
    footer_project: "Projecte",
    footer_releases: "Versions",
    footer_issues: "Informar d'un error",
    footer_license_title: "Llicència",
    footer_author: "Per Miguel Angel Esteban"
  }
};

// ==========================================
// 2. Language Detection & Switching Engine
// ==========================================
let currentLang = 'es';

function detectSystemLanguage() {
  // Check localStorage first
  const stored = localStorage.getItem('mytag_lang');
  if (stored && ['es', 'en', 'ca'].includes(stored)) {
    return stored;
  }

  // Detect from browser/system language list
  const navLanguages = navigator.languages || [navigator.language || 'en'];
  for (const lang of navLanguages) {
    const code = lang.toLowerCase();
    if (code.startsWith('ca')) return 'ca';
    if (code.startsWith('es')) return 'es';
    if (code.startsWith('en')) return 'en';
  }

  return 'en';
}

function setLanguage(lang) {
  if (!translations[lang]) lang = 'en';
  currentLang = lang;
  localStorage.setItem('mytag_lang', lang);

  // Update HTML lang attribute
  document.documentElement.setAttribute('lang', lang);

  // Update Document Title & Meta Description
  document.title = translations[lang].page_title;
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.setAttribute('content', translations[lang].meta_desc);

  // Update all elements with data-i18n
  const translatableElements = document.querySelectorAll('[data-i18n]');
  translatableElements.forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (translations[lang][key]) {
      el.innerHTML = translations[lang][key];
    }
  });

  // Update active state in language buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    if (btn.getAttribute('data-lang') === lang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update gallery caption according to active gallery tab
  updateGalleryContent();
}

// ==========================================
// 3. Theme Engine (Light / Dark / Auto)
// ==========================================
function initTheme() {
  const storedTheme = localStorage.getItem('mytag_theme') || 'auto';
  document.documentElement.setAttribute('data-theme', storedTheme);

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'auto';
      let nextTheme;
      if (current === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        nextTheme = prefersDark ? 'light' : 'dark';
      } else if (current === 'light') {
        nextTheme = 'dark';
      } else {
        nextTheme = 'auto';
      }

      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('mytag_theme', nextTheme);
    });
  }
}

// ==========================================
// 4. Interactive Gallery & Tabs
// ==========================================
let activeGalleryTab = 'main';

function initGallery() {
  const galleryTabs = document.querySelectorAll('.gallery-tab');
  const galleryMainImg = document.getElementById('galleryMainImg');
  const galleryWindowTitle = document.getElementById('galleryWindowTitle');

  galleryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      galleryTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const imgSrc = tab.getAttribute('data-img');
      const captionKey = tab.getAttribute('data-caption-i18n');
      
      activeGalleryTab = captionKey === 'caption_main' ? 'main' : 'search';

      if (galleryMainImg) {
        galleryMainImg.style.opacity = '0.3';
        setTimeout(() => {
          galleryMainImg.src = imgSrc;
          galleryMainImg.style.opacity = '1';
        }, 120);
      }

      updateGalleryContent();
    });
  });
}

function updateGalleryContent() {
  const captionEl = document.getElementById('galleryCaption');
  const windowTitleEl = document.getElementById('galleryWindowTitle');

  if (activeGalleryTab === 'main') {
    if (captionEl) captionEl.innerHTML = translations[currentLang].caption_main;
    if (windowTitleEl) windowTitleEl.textContent = translations[currentLang].gallery_title_main;
  } else {
    if (captionEl) captionEl.innerHTML = translations[currentLang].caption_search;
    if (windowTitleEl) windowTitleEl.textContent = translations[currentLang].gallery_title_search;
  }
}

// ==========================================
// 5. Lightbox Modal
// ==========================================
function initLightbox() {
  const modal = document.getElementById('lightboxModal');
  const modalImg = document.getElementById('lightboxImg');
  const modalCaption = document.getElementById('lightboxCaption');
  const closeBtn = document.getElementById('lightboxClose');
  const backdrop = document.getElementById('lightboxBackdrop');

  const zoomables = document.querySelectorAll('.zoomable-img');

  function openLightbox(src, caption) {
    if (!modal || !modalImg) return;
    modalImg.src = src;
    if (modalCaption) modalCaption.textContent = caption || '';
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    if (!modal) return;
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  zoomables.forEach(img => {
    img.addEventListener('click', () => {
      const captionText = img.id === 'heroScreenshot' 
        ? translations[currentLang].caption_main 
        : (document.getElementById('galleryCaption')?.textContent || '');
      openLightbox(img.src, captionText);
    });
  });

  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  if (backdrop) backdrop.addEventListener('click', closeLightbox);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal?.classList.contains('active')) {
      closeLightbox();
    }
  });
}

// ==========================================
// 6. Installation Tabs
// ==========================================
function initInstallTabs() {
  const tabs = document.querySelectorAll('.install-tab');
  const panels = document.querySelectorAll('.install-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-target');

      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(`panel-${target}`);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }
    });
  });
}

// ==========================================
// 7. Clipboard Copy Helper
// ==========================================
function initCopyButtons() {
  const copyButtons = document.querySelectorAll('.copy-btn');

  copyButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const textToCopy = btn.getAttribute('data-copy');
      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
      } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }

      // Visual feedback
      const textSpan = btn.querySelector('.copy-text');
      const originalText = textSpan ? textSpan.textContent : '';
      btn.classList.add('copied');
      if (textSpan) textSpan.textContent = translations[currentLang].copied_btn || 'Copied!';

      setTimeout(() => {
        btn.classList.remove('copied');
        if (textSpan) textSpan.textContent = translations[currentLang].copy_btn || 'Copy';
      }, 2000);
    });
  });
}

// ==========================================
// 8. Mobile Navigation Menu
// ==========================================
function initMobileMenu() {
  const toggle = document.getElementById('mobileToggle');
  const menu = document.getElementById('navMenu');

  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const isOpen = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close when clicking a link
    menu.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }
}

// ==========================================
// 9. Main Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Language Switcher Buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      setLanguage(lang);
    });
  });

  // Set initial language (detected or stored)
  const initialLang = detectSystemLanguage();
  setLanguage(initialLang);

  // Initialize components
  initTheme();
  initGallery();
  initLightbox();
  initInstallTabs();
  initCopyButtons();
  initMobileMenu();
});
