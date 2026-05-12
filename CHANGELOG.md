# Changelog

All notable changes to Slots Gel Annotator are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.8] — 2026-05-12

Clean shutdown when the terminal / cmd window is closed. Lock file is now removed even on hard-close paths (window X button on Windows, SIGHUP on POSIX) that previously bypassed atexit. The OS releases the listening port immediately on process death; the port-fallback logic continues to cover the brief TIME_WAIT window when re-launching.

## [1.0.7] — 2026-05-12

Logo now preserves the white that sits behind the trees inside the green emblem. The previous transparent-logo pass uniformly stripped every white pixel; this version uses edge-flood-fill so only background-connected whites become transparent, while interior whites stay opaque.

## [1.0.6] — 2026-05-11

Toolbar condensed: Save + Load -> Project dropdown; Export PNG + Export SVG -> Export dropdown. Confirm dialog before uploading a new image when one is already loaded so accidental drag-drop or file-pick doesn't wipe annotations.

## [1.0.5] — 2026-05-11

Pan + zoom: you can now pan to see the whole image when zoomed in. Previously the left half of the zoomed-in SVG was unreachable because flex centering pushed the overflow into negative-scroll territory.

## [1.0.4] — 2026-05-11

Toolbar logo no longer has a white square background — all icon assets now have transparent-background variants generated via GIMP-style color-to-alpha unmultiplication, and the /favicon.png server route prefers them.

## [1.0.3] — 2026-05-10

Auto-update check now runs on every launch, matching proker. Previously, headless launches (e.g. clicking a Windows shortcut) and single-instance 'open existing tab' launches could skip the check entirely. The synchronous prompt now fires every time, terminal or headless.

## [1.0.2] — 2026-05-10

Toolbar logo + stacked Undo/Redo. Port-fallback in main() now matches proker — falls forward up to 20 ports when the default is taken instead of crashing. /favicon.png serves a real PNG so the in-app logo renders.

## [1.0.1] — 2026-05-10

Anchor metadata-column row labels (e.g. "Treatment", "Type") to the region's left edge instead of the image's left edge. Previously, when the image was not cropped to region, row labels rendered far from their bracket row above the region; brackets and lines were already region-anchored, so this fix realigns the row labels with the rest of their column.

## [1.0.0] — 2026-05-10

Initial public release as **Slots Gel Annotator** on PyPI as
`slotsgeltool`, with the `slots` console-script entry point.

### Highlights

* Vector-native rendering — the on-screen SVG IS the export.
* Multi-format input (PNG / JPEG / TIFF / 16-bit raw / 16-bit TIFF), with
  channel-max RGB→grayscale conversion that preserves imager-baked red
  saturation contours from Bio-Rad / GelDoc / ChemiDoc TIFs.
* Auto-stretched LUT (p1 .. p99.5) so dark gels are visible on first
  load.
* Saturation overlay tracks the source dynamic range (not the
  auto-stretched preview), so flagged pixels are the imager's intent.
* Smart bracket rotation — minimum number of labels rotated to 90°
  when overlap would otherwise occur.
* Multi-ladder support: any combination of left-flank, right-flank, or
  internal ladders. Hide-Ladders collapses flanks only.
* Spreadsheet-style metadata table: drag-select cell ranges,
  type-to-fill, click-out clears, Tab navigation respects ranges.
* Drag-to-reorder columns; per-column / per-lane visibility toggles.
* Undo / Redo for every state-changing action.
* Smooth (delta-proportional) wheel zoom + right-click drag pan.
* Single-instance launcher: re-running `slots` reuses the existing
  window.
* Self-contained sessions: image embedded in the saved JSON.

### Bundled

* `slots` CLI with `--port`, `--host`, `--no-browser`, `--install`,
  `--update`, `--no-update`, `--version`.
* Desktop-shortcut installer for Windows / macOS / Linux.
* `Install_Windows.bat` and `Install_macOS.command` wrappers around
  `pip install -e .`.

### Known limitations

* The shortcut installer requires `tkinter`. Most Python distributions
  include it; on minimal Linux installs run
  `apt install python3-tk` (or your distro's equivalent) first.
* macOS `.app` icons require the system `sips` tool (always present on
  macOS) for PNG → ICNS conversion. Failure is non-fatal — the
  bundle works without an icon.
