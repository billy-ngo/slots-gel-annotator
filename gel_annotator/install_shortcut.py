"""
Slots Gel Annotator — desktop shortcut installer.

Pops a small Tkinter dialog letting the user choose where to place the
shortcut, then creates a platform-appropriate launcher:

* **Windows** — ``.lnk`` via PowerShell (referencing a small ``.bat``
  shim that calls ``python -m gel_annotator``). Custom icon embedded
  from ``assets/icon.ico``.
* **macOS** — ``.app`` bundle with a launcher script + ``Info.plist``.
  The icon is converted from a PNG to ``.icns`` via the system ``sips``
  utility (always present on macOS).
* **Linux** — freedesktop ``.desktop`` file in the chosen directory.
  Icon shipped as a sibling PNG.

Failures are surfaced through the dialog rather than silently swallowed
so the user knows whether to fall back to ``slots --install`` later or
debug their environment.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from gel_annotator.icon import generate_ico, generate_png

_APP_NAME = "Slots Gel Annotator"
_BUNDLE_ID = "com.slots.gel-annotator"
_LINUX_BASENAME = "slots-gel-annotator"


# ── Helpers ─────────────────────────────────────────────────────────
def _find_exe() -> str | None:
    """Return the absolute path to the installed ``slots`` console script.

    Used as the launcher target on Linux and as a shortcut hint on
    macOS. Falls through several candidates because pip can install
    scripts to surprising places (user site-packages, virtualenv bins,
    framework dirs, etc.).
    """
    found = shutil.which("slots")
    if found:
        return os.path.realpath(found)
    if sys.platform == "win32":
        candidate = Path(sys.executable).parent / "Scripts" / "slots.exe"
    else:
        candidate = Path(sys.executable).parent / "slots"
    if candidate.exists():
        return str(candidate)
    return None


def _default_desktop() -> str:
    """Best-effort path to the user's desktop directory."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("USERPROFILE", "~"), "Desktop")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Desktop")
    # Linux — ask xdg-user-dir if available; else fall back to ~/Desktop.
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or os.path.expanduser("~/Desktop")
    except Exception:
        return os.path.expanduser("~/Desktop")


# ── Per-platform installers ─────────────────────────────────────────
def _install_windows(target_dir: str) -> str:
    """Create a Windows .lnk pointing at a launcher batch file."""
    target_dir_p = Path(target_dir)
    target_dir_p.mkdir(parents=True, exist_ok=True)

    config_dir = Path.home() / ".slots-gel-annotator"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write the icon next to the launcher so the .lnk's IconLocation
    # resolves consistently regardless of pip-install path.
    ico_path = config_dir / "slots_icon.ico"
    ico_path.write_bytes(generate_ico())

    # The launcher .bat does the actual launch. ``start /min`` keeps the
    # console hidden after Python takes over. ``--no-update`` avoids the
    # pip-install path from a shortcut click (which usually has no
    # terminal to prompt against).
    python_exe = sys.executable
    bat_path = config_dir / "launch_slots.bat"
    bat_path.write_text(
        "@echo off\n"
        f'start /min "" "{python_exe}" -m gel_annotator --no-update\n'
    )

    lnk_path = target_dir_p / f"{_APP_NAME}.lnk"

    ps_script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{lnk_path}'); "
        f"$s.TargetPath = '{bat_path}'; "
        f"$s.IconLocation = '{ico_path},0'; "
        f"$s.Description = '{_APP_NAME}'; "
        f"$s.WorkingDirectory = '{Path.home()}'; "
        "$s.WindowStyle = 7; "
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        check=True, capture_output=True, timeout=30,
    )
    return str(lnk_path)


def _install_macos(target_dir: str) -> str:
    """Create a macOS .app bundle that double-clicks into the annotator."""
    target_dir_p = Path(target_dir)
    target_dir_p.mkdir(parents=True, exist_ok=True)

    app_dir = target_dir_p / f"{_APP_NAME}.app"
    contents = app_dir / "Contents"
    macos_dir = contents / "MacOS"
    resources = contents / "Resources"
    for d in (macos_dir, resources):
        d.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable
    launcher = macos_dir / "launcher"
    # Add Homebrew paths to PATH so a brew-installed Python that uses
    # /opt/homebrew/bin still finds tools its dependencies need.
    launcher.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$PATH"
        exec "{python_exe}" -m gel_annotator --no-update "$@"
    """))
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Best-effort icon conversion via the bundled `sips` tool (built
    # into macOS). Failure is non-fatal — the bundle still works,
    # macOS just shows the default Application icon.
    icon_set = False
    tmp_png: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(generate_png(512))
            tmp_png = tmp.name
        icns_path = resources / "icon.icns"
        subprocess.run(
            ["sips", "-s", "format", "icns", tmp_png, "--out", str(icns_path)],
            check=True, capture_output=True, timeout=30,
        )
        icon_set = True
    except Exception:
        pass
    finally:
        try:
            if tmp_png:
                os.unlink(tmp_png)
        except Exception:
            pass

    from gel_annotator import __version__
    plist = contents / "Info.plist"
    icon_entry = (
        "<key>CFBundleIconFile</key>\n    <string>icon</string>"
        if icon_set else ""
    )
    plist.write_text(textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>CFBundleName</key>
            <string>{_APP_NAME}</string>
            <key>CFBundleExecutable</key>
            <string>launcher</string>
            <key>CFBundleIdentifier</key>
            <string>{_BUNDLE_ID}</string>
            <key>CFBundleVersion</key>
            <string>{__version__}</string>
            <key>CFBundlePackageType</key>
            <string>APPL</string>
            {icon_entry}
        </dict>
        </plist>
    """))
    return str(app_dir)


def _install_linux(target_dir: str) -> str:
    """Create a freedesktop .desktop entry for Linux."""
    exe = _find_exe()
    if not exe:
        raise RuntimeError("Cannot locate the 'slots' executable.")

    target_dir_p = Path(target_dir)
    target_dir_p.mkdir(parents=True, exist_ok=True)

    icon_path = target_dir_p / f"{_LINUX_BASENAME}.png"
    icon_path.write_bytes(generate_png(256))

    desktop_path = target_dir_p / f"{_LINUX_BASENAME}.desktop"
    desktop_path.write_text(textwrap.dedent(f"""\
        [Desktop Entry]
        Type=Application
        Name={_APP_NAME}
        Comment=Vector-native gel annotation
        Exec={exe}
        Icon={icon_path}
        Terminal=false
        Categories=Science;Biology;Graphics;
    """))
    desktop_path.chmod(
        desktop_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    return str(desktop_path)


# ── Entry point ─────────────────────────────────────────────────────
def main() -> None:
    """Open a directory-picker dialog, create the shortcut, report result."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()

    chosen = filedialog.askdirectory(
        title=f"Choose shortcut location — {_APP_NAME}",
        initialdir=_default_desktop(),
    )
    if not chosen:
        root.destroy()
        return

    try:
        if sys.platform == "win32":
            result = _install_windows(chosen)
        elif sys.platform == "darwin":
            result = _install_macos(chosen)
        else:
            result = _install_linux(chosen)
        messagebox.showinfo("Shortcut Created", f"Shortcut installed:\n{result}")
    except Exception as exc:
        messagebox.showerror("Error", f"Failed to create shortcut:\n{exc}")
    finally:
        root.destroy()
