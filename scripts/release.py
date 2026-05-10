#!/usr/bin/env python3
"""
Slots Gel Annotator — release automation.

One command to bump the version, write a changelog entry, commit, tag,
and push. The push triggers `.github/workflows/publish.yml` which
builds the package and uploads it to PyPI.

Usage from the project root::

    python scripts/release.py 1.0.1                  # explicit version
    python scripts/release.py --patch                # 1.0.0 -> 1.0.1
    python scripts/release.py --minor                # 1.0.0 -> 1.1.0
    python scripts/release.py --major                # 1.0.0 -> 2.0.0

    python scripts/release.py --patch --message \\
        "Faster zoom; fixed band-detection edge case."   # auto-fill changelog

    python scripts/release.py 1.0.1 --dry-run         # preview only, no writes
    python scripts/release.py 1.0.1 --no-push         # bump+commit+tag, don't push

Non-destructive checks before any change:
  * Aborts if the working tree has uncommitted changes (override with --force).
  * Aborts if the target tag already exists locally or on the remote.
  * Aborts if the version is not strictly newer than the current one.

Safety pause before the push: the script shows a final summary and
asks for explicit yes/no confirmation, so a typo doesn't accidentally
ship a release. Pass --yes to skip the prompt for fully-automated runs.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
INIT_PY = ROOT / "gel_annotator" / "__init__.py"
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ── Helpers ─────────────────────────────────────────────────────────
def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Thin wrapper around subprocess.run that prints commands as they
    run (so the user can see what the script is doing)."""
    pretty = " ".join(c if " " not in c else f'"{c}"' for c in cmd)
    print(f"  $ {pretty}")
    return subprocess.run(
        cmd, cwd=str(ROOT),
        check=check,
        text=True,
        capture_output=capture,
    )


def fatal(msg: str, code: int = 1) -> None:
    print(f"\n  ERROR: {msg}\n", file=sys.stderr)
    sys.exit(code)


def confirm(prompt: str) -> bool:
    """Prompt the user; return True only on an unambiguous "yes"."""
    try:
        ans = input(f"  {prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return ans in ("y", "yes")


# ── Version IO ──────────────────────────────────────────────────────
def read_init_version() -> str:
    """Pull __version__ from gel_annotator/__init__.py."""
    txt = INIT_PY.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', txt, flags=re.MULTILINE)
    if not m:
        fatal(f"Could not find __version__ in {INIT_PY}")
    return m.group(1)


def write_init_version(new_version: str) -> None:
    txt = INIT_PY.read_text(encoding="utf-8")
    new_txt = re.sub(
        r'(^__version__\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        txt,
        flags=re.MULTILINE,
    )
    INIT_PY.write_text(new_txt, encoding="utf-8")


def read_pyproject_version() -> str:
    """Pull version = "X.Y.Z" from pyproject.toml's [project] table."""
    txt = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', txt, flags=re.MULTILINE)
    if not m:
        fatal(f"Could not find version in {PYPROJECT}")
    return m.group(1)


def write_pyproject_version(new_version: str) -> None:
    txt = PYPROJECT.read_text(encoding="utf-8")
    new_txt = re.sub(
        r'(^version\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        txt,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(new_txt, encoding="utf-8")


# ── Semantic bumping ────────────────────────────────────────────────
def parse_version(v: str) -> tuple[int, int, int]:
    if not VERSION_RE.match(v):
        fatal(f"Version '{v}' is not in MAJOR.MINOR.PATCH form (e.g. 1.0.1)")
    a, b, c = v.split(".")
    return int(a), int(b), int(c)


def bump(current: str, mode: str) -> str:
    a, b, c = parse_version(current)
    if mode == "major": return f"{a + 1}.0.0"
    if mode == "minor": return f"{a}.{b + 1}.0"
    if mode == "patch": return f"{a}.{b}.{c + 1}"
    raise ValueError(mode)


def is_strictly_newer(new: str, old: str) -> bool:
    return parse_version(new) > parse_version(old)


# ── Git checks ──────────────────────────────────────────────────────
def is_working_tree_clean() -> bool:
    res = run(["git", "status", "--porcelain"], capture=True)
    return res.stdout.strip() == ""


def tag_exists_locally(tag: str) -> bool:
    res = run(["git", "tag", "-l", tag], capture=True)
    return res.stdout.strip() == tag


def tag_exists_on_remote(tag: str) -> bool:
    """Best-effort check of `git ls-remote --tags origin <tag>`. Returns
    False on any network or auth error (and prints a warning)."""
    try:
        res = run(
            ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
            capture=True,
            check=False,
        )
        return tag in res.stdout
    except Exception as e:
        print(f"  WARNING: could not check remote tags ({e}); proceeding anyway.")
        return False


def current_branch() -> str:
    res = run(["git", "branch", "--show-current"], capture=True)
    return res.stdout.strip()


# ── CHANGELOG writing ───────────────────────────────────────────────
CHANGELOG_HEADER_RE = re.compile(
    r"^## \[(\d+\.\d+\.\d+)\]", flags=re.MULTILINE,
)


def insert_changelog_section(new_version: str, message: Optional[str]) -> str:
    """Insert a new `## [X.Y.Z] — YYYY-MM-DD` section at the top of the
    version-history portion of CHANGELOG.md (just above the previous
    most-recent release). If `message` is provided it's used verbatim
    as the section body; otherwise an editor is opened so the user can
    write the notes by hand. Returns the body that was inserted (so
    the caller can show it to the user before committing)."""
    txt = CHANGELOG.read_text(encoding="utf-8")
    today = date.today().isoformat()  # YYYY-MM-DD

    # Find the first existing release header. The new section gets
    # inserted immediately ABOVE that line so the most-recent release
    # always sits at the top.
    m = CHANGELOG_HEADER_RE.search(txt)
    if not m:
        fatal(
            f"Could not find any '## [X.Y.Z]' section in {CHANGELOG}. "
            "Add at least one release section manually before automating."
        )
    insert_at = m.start()

    if message is None:
        # Open the user's editor on a temp file pre-filled with a
        # bullet-list scaffold. They write the notes, save, exit.
        scaffold = (
            f"## [{new_version}] — {today}\n\n"
            "### Added\n- \n\n"
            "### Changed\n- \n\n"
            "### Fixed\n- \n"
        )
        body = _edit_in_pager(scaffold)
        if not body or body.strip() == scaffold.strip():
            fatal("Empty / unchanged release notes — aborting.")
    else:
        body = (
            f"## [{new_version}] — {today}\n\n"
            f"{message.strip()}\n"
        )

    # Make sure the inserted section ends with a single blank line
    # before the next existing section (no double-blanks, no missing
    # separator).
    body = body.rstrip() + "\n\n"

    new_txt = txt[:insert_at] + body + txt[insert_at:]
    CHANGELOG.write_text(new_txt, encoding="utf-8")
    return body


def _edit_in_pager(initial: str) -> str:
    """Open the user's $EDITOR on a temp file pre-filled with `initial`
    text. Returns the saved content. On Windows where $EDITOR isn't
    set, falls back to Notepad."""
    editor = (
        os.environ.get("VISUAL")
        or os.environ.get("EDITOR")
        or ("notepad" if sys.platform == "win32" else "vi")
    )
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8",
    ) as tmp:
        tmp.write(initial)
        tmp_path = tmp.name
    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── Main flow ───────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        prog="release.py",
        description=(
            "Bump the version, append a CHANGELOG entry, commit, tag, "
            "and push. Pushing the tag triggers the GitHub Actions "
            "workflow that publishes the package to PyPI."
        ),
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("version", nargs="?", help="Explicit version (e.g. 1.0.1)")
    grp.add_argument("--major", action="store_true", help="Bump major version")
    grp.add_argument("--minor", action="store_true", help="Bump minor version")
    grp.add_argument("--patch", action="store_true", help="Bump patch version")

    parser.add_argument("--message", "-m",
                        help="Inline changelog body. If omitted, $EDITOR opens.")
    parser.add_argument("--remote", default="origin",
                        help="Git remote to push to (default: origin)")
    parser.add_argument("--branch", default=None,
                        help="Branch to push (default: current branch)")
    parser.add_argument("--no-push", action="store_true",
                        help="Do everything except the push (commits + tags only)")
    parser.add_argument("--force", action="store_true",
                        help="Skip the working-tree-clean check")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen; touch nothing")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip the final yes/no confirmation prompt")
    args = parser.parse_args()

    # ── Resolve target version ─────────────────────────────────────
    current = read_init_version()
    pyproject_current = read_pyproject_version()
    if current != pyproject_current:
        print(f"  WARNING: __init__.py version ({current}) differs from "
              f"pyproject.toml ({pyproject_current}). Using __init__.py as the source of truth.")

    if args.version:
        new = args.version.lstrip("v")
        parse_version(new)  # validates format
    else:
        mode = "major" if args.major else "minor" if args.minor else "patch"
        new = bump(current, mode)

    if not is_strictly_newer(new, current):
        fatal(f"Target version {new} is not strictly newer than current {current}")

    print()
    print(f"  Current version : {current}")
    print(f"  Target version  : {new}")
    print(f"  Tag             : v{new}")
    print()

    # ── Pre-flight checks ──────────────────────────────────────────
    if not args.force and not is_working_tree_clean():
        fatal(
            "Working tree has uncommitted changes. Commit or stash them first, "
            "or pass --force to bypass this check."
        )
    if tag_exists_locally(f"v{new}"):
        fatal(f"Tag v{new} already exists locally. Pick a different version.")
    if tag_exists_on_remote(f"v{new}"):
        fatal(f"Tag v{new} already exists on the remote.")

    branch = args.branch or current_branch()
    if not branch:
        fatal("Could not determine current branch (detached HEAD?).")

    if args.dry_run:
        print("  --dry-run: would do all of the above PLUS:")
        print(f"    * write {new} to {INIT_PY.name}")
        print(f"    * write {new} to {PYPROJECT.name}")
        print(f"    * insert a new CHANGELOG section dated {date.today().isoformat()}")
        print(f"    * git commit -m 'Release v{new}'")
        print(f"    * git tag -a v{new}")
        if not args.no_push:
            print(f"    * git push {args.remote} {branch}")
            print(f"    * git push {args.remote} v{new}")
        else:
            print("    * (push skipped: --no-push)")
        return 0

    # ── Apply the changes ──────────────────────────────────────────
    print("  Updating version files ...")
    write_init_version(new)
    write_pyproject_version(new)

    print("  Updating CHANGELOG.md ...")
    body = insert_changelog_section(new, args.message)
    print()
    print("  Inserted into CHANGELOG.md:")
    print("  " + "-" * 60)
    for line in body.splitlines():
        print(f"  {line}")
    print("  " + "-" * 60)
    print()

    # ── Confirm + commit + tag + push ──────────────────────────────
    if not args.yes and not confirm(f"Commit + tag v{new}{' + push' if not args.no_push else ''}?"):
        print("  Aborted. Your file changes are still on disk — `git diff` to see them, "
              "`git checkout -- gel_annotator/__init__.py pyproject.toml CHANGELOG.md` to revert.")
        return 1

    print("  Committing ...")
    run(["git", "add",
         str(INIT_PY.relative_to(ROOT)),
         str(PYPROJECT.relative_to(ROOT)),
         str(CHANGELOG.relative_to(ROOT))])
    run(["git", "commit", "-m", f"Release v{new}"])

    print("  Tagging ...")
    run(["git", "tag", "-a", f"v{new}", "-m", f"v{new}"])

    if args.no_push:
        print()
        print("  Done. Run these to publish when ready:")
        print(f"    git push {args.remote} {branch}")
        print(f"    git push {args.remote} v{new}")
        return 0

    print("  Pushing ...")
    run(["git", "push", args.remote, branch])
    run(["git", "push", args.remote, f"v{new}"])

    print()
    print(f"  ✓ v{new} released. Watch the workflow:")
    print(f"    https://github.com/billy-ngo/slots-gel-annotator/actions")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
