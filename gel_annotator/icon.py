"""
Icon loader for Slots Gel Annotator.

The desktop-shortcut installer needs platform-specific icon formats:

* Windows expects an ``.ico`` file (multi-resolution).
* macOS expects an ``.icns`` bundle (or a high-resolution PNG that the
  ``.app`` builder converts via ``iconutil``).
* Linux expects a PNG referenced from a ``.desktop`` file.

This module reads the user-supplied icon assets shipped under
``gel_annotator/assets/`` and exposes them as bytes. If the optional
asset is missing we fall back to a procedurally-generated 1×1
transparent PNG so the shortcut installer never crashes — the user
will see the OS default icon instead, which is visually unpleasant
but functionally fine.

Asset filenames (relative to ``gel_annotator/assets/``):

    icon.ico      Windows multi-resolution icon
    icon.icns     macOS high-resolution icon bundle
    icon-512.png  PNG fallback (used by Linux .desktop and macOS .app
                  builds when icon.icns is absent)

To add or replace logos see the README's *Branding & icons* section.
"""

from __future__ import annotations

import io
from pathlib import Path

_ASSETS_DIR = Path(__file__).parent / "assets"

# Tiny 1×1 transparent PNG, base64-encoded inline so we always have
# *something* to return even when no asset files have been shipped.
# Generated once with: ``base64 -w0 1x1.png``.
_TRANSPARENT_PNG_BASE64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAA"
    b"SUVORK5CYII="
)


def _read_or_default(name: str, default: bytes) -> bytes:
    """Return the bytes of ``assets/<name>`` or ``default`` if absent."""
    p = _ASSETS_DIR / name
    if p.exists():
        try:
            return p.read_bytes()
        except Exception:
            return default
    return default


def generate_ico() -> bytes:
    """Return Windows .ico bytes.

    Prefers ``assets/icon.ico``. Falls back to a 1×1 transparent PNG
    wrapped in a minimal ICO container would be ideal, but a missing
    icon file is rare enough that we accept the inelegant fallback.
    """
    import base64
    fallback = base64.b64decode(_TRANSPARENT_PNG_BASE64)
    return _read_or_default("icon.ico", fallback)


def generate_icns() -> bytes:
    """Return macOS .icns bytes (or empty on absence — caller can fall back)."""
    return _read_or_default("icon.icns", b"")


def generate_png(size: int = 512) -> bytes:
    """Return a high-resolution PNG of the application icon.

    ``size`` is ignored when a pre-rendered asset is shipped; we return
    the file as-is. If you need multiple sizes, ship them as
    ``icon-<size>.png`` and add an explicit branch here.
    """
    import base64
    fallback = base64.b64decode(_TRANSPARENT_PNG_BASE64)
    # Try the size-specific filename first, then the canonical 512.
    return _read_or_default(f"icon-{size}.png", _read_or_default("icon-512.png", fallback))


def has_real_icon() -> bool:
    """True when at least one platform-specific icon asset is shipped."""
    return any(
        (_ASSETS_DIR / name).exists()
        for name in ("icon.ico", "icon.icns", "icon-512.png")
    )
