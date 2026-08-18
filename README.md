# Quran App Public Assets & Fonts

[![Total Downloads](https://img.shields.io/github/downloads/x0911/quran-app-flutter-public-files/total)](https://github.com/x0911/quran-app-flutter-public-files/releases)
[![License: Public Domain / Open Data](https://img.shields.io/badge/License-Public_Domain_/_Open_Data-blue.svg)](https://github.com/x0911/quran-app-flutter-public-files)

This repository hosts the static Quran text-rendering asset bundle (per-page custom fonts, per-page word/line JSON schemas, per-surah page ranges, UI fonts, and page decoration frame elements) for the Hafs text-rendering pipeline in the Flutter Quran application. Sourced from the [Surah App](https://web.surahapp.com/en/quran) open data ecosystem, these assets enable high-fidelity, fully offline per-page Madina Mushaf typography without relying on static page images or online web services.

---

## 📊 Asset Download Statistics

<!-- DOWNLOAD_STATS_START -->
| Release Tag | Asset Name | File Size | Download Count |
| :--- | :--- | :--- | :--- |
| `v1.0.0` | `decorations.zip` | 14.97 MB | 7 |
| `v1.0.0` | `pfont.zip` | 41.73 MB | 9 |
| `v1.0.0` | `quran-pages.zip` | 0.44 MB | 8 |
| `v1.0.0` | `quran-surah-pages.zip` | 0.23 MB | 8 |
| `v1.0.0` | `ui-fonts.zip` | 2.04 MB | 7 |

**Total Asset Downloads across all releases:** `39`

*Last updated: 2026-08-18 00:37 UTC*
<!-- DOWNLOAD_STATS_END -->

---

## 📁 Repository Structure

```
quran-app-flutter-public-files/
├── pfont/                  # 604 per-page TrueType fonts (page_1.ttf .. page_604.ttf)
├── quran-pages/            # 604 per-page JSON files with word/line structures (1.json .. 604.json)
├── quran-surah-pages/      # 114 per-surah page range JSON mappings (1.json .. 114.json)
├── decorations/            # Page border frames (styles 1–5 & extra, light and -dark variants)
└── ui-fonts/               # UI label font families for Juz/Hizb/Surah header displays
    ├── Hafs/               # Hafs UI font family (v20.ttf)
    ├── Kitab/              # Kitab UI font family (Kitab-Regular.ttf, Kitab-Bold.ttf)
    └── Lotus/              # Lotus UI font family (Lotus.ttf)
```

### Folder Breakdown

- **`pfont/` (604 files, ~43 MB total)**: Per-page custom fonts mapping Private-Use-Area (PUA) Unicode codepoints to exact glyph shapes for each page of the standard 604-page Madina Mushaf layout.
- **`quran-pages/` (604 files, ~2.5 MB total)**: Detailed JSON data for every page, defining word boundaries, line positions, ayah references, and special markers (`aya: -2` for surah headers, `aya: -1` for Bismillah).
- **`quran-surah-pages/` (114 files, ~1.7 MB total)**: Surah metadata and page boundary definitions for surah-based navigation modes.
- **`decorations/`**: High-resolution PNG frame graphics (top, middle, bottom, ayah end markers) in 5 style themes plus extra variants, supporting both light mode and dark mode UI palettes.
- **`ui-fonts/`**: Dedicated Arabic font families (`Lotus`, `Hafs`, `Kitab`) used for surah header banners, juz/hizb-quarter badges, and navigation labels.

---

## 🔤 Font Format & Cross-Platform Compatibility

- **Per-Page Fonts (`pfont/`)**: The source repository supplied per-page fonts solely in `.woff` format. While WOFF works in browser environments, Flutter's engine `FontLoader` reliably requires raw TrueType (`.ttf`) or OpenType (`.otf`) fonts across iOS, Android, macOS, Linux, and Windows desktop targets. All 604 `.woff` files were systematically converted to standard TrueType (`.ttf`) using `fontTools`, and verified via glyph rendering spot-checks.
- **UI Fonts (`ui-fonts/`)**: Sourced directly from their respective `.ttf` subfolders (`Lotus.ttf`, `v20.ttf`, `Kitab-Regular.ttf`, `Kitab-Bold.ttf`) to guarantee full Flutter `FontLoader` compatibility across all native platforms.

---

## 📜 License & Attribution

- **Quranic Text & Page Data**: The Quranic text, page numbers, word mappings, and layout coordinates are public domain.
- **Fonts & Visual Assets**: Adapted from the open data approach of [Surah App](https://web.surahapp.com/en/quran) and King Fahd Glorious Quran Printing Complex (KFGQPC). Provided for open educational and religious software development.
