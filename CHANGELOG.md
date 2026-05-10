# Changelog

All notable changes to Slots Gel Annotator are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
