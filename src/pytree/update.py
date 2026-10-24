"""Selbst-Update: holt die neueste getaggte Version von GitHub und installiert sie.

Nur Standardbibliothek, damit es auch funktioniert, wenn textual defekt ist.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from pytree import __version__

REPO = "tomo-one/pytree"
TAGS_URL = f"https://api.github.com/repos/{REPO}/tags?per_page=100"
ARCHIVE_URL = f"https://github.com/{REPO}/archive/refs/tags/{{tag}}.zip"
_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
_TIMEOUT_SECONDS = 20


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = _TAG_RE.match(text if text.startswith("v") else f"v{text}")
    return tuple(int(g) for g in match.groups()) if match else None  # type: ignore[return-value]


def latest_tag(tag_names: list[str]) -> str | None:
    versions = [(parse_version(name), name) for name in tag_names]
    versions = [(v, name) for v, name in versions if v is not None]
    return max(versions)[1] if versions else None


def is_newer(candidate: str, current: str) -> bool:
    cand, cur = parse_version(candidate), parse_version(current)
    return cand is not None and cur is not None and cand > cur


def _http_get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"pytree/{__version__}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return response.read()


def fetch_latest_tag() -> str:
    names = [entry["name"] for entry in json.loads(_http_get(TAGS_URL))]
    tag = latest_tag(names)
    if tag is None:
        raise RuntimeError("Im Repository wurde keine Version (vX.Y.Z) gefunden.")
    return tag


def install_from_archive(archive: Path) -> int:
    """Entpackt das Archiv und führt dessen install.py mit demselben Python aus,
    damit Interpreter und private venv der bestehenden Installation erhalten bleiben."""
    with tempfile.TemporaryDirectory(prefix="pytree-update-") as tmp:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmp)
        roots = [p for p in Path(tmp).iterdir() if p.is_dir()]
        if len(roots) != 1 or not (roots[0] / "install.py").is_file():
            print("pytree: Archiv hat nicht die erwartete Struktur.", file=sys.stderr)
            return 1
        return subprocess.run([sys.executable, str(roots[0] / "install.py")]).returncode


def run_update(check_only: bool = False) -> int:
    if not check_only and not os.environ.get("PYTREE_MANAGED"):
        print(
            "pytree: --update gilt nur für eine mit install.py installierte Version.\n"
            "Aus einem Quellordner stattdessen `git pull` und `python3 install.py`.",
            file=sys.stderr,
        )
        return 2

    try:
        tag = fetch_latest_tag()
    except (urllib.error.URLError, OSError, ValueError, RuntimeError, KeyError) as exc:
        print(
            f"pytree: Versionsabfrage bei GitHub fehlgeschlagen: {exc}\n"
            f"Manuell: https://github.com/{REPO}/releases bzw. Tags herunterladen "
            "und `python3 install.py` ausführen.",
            file=sys.stderr,
        )
        return 1

    if not is_newer(tag, __version__):
        print(f"pytree {__version__} ist aktuell.")
        return 0
    if check_only:
        print(f"Neue Version {tag} verfügbar (installiert: {__version__}). Update: pytree --update")
        return 0

    print(f"Aktualisiere {__version__} -> {tag} ...", flush=True)
    try:
        data = _http_get(ARCHIVE_URL.format(tag=tag))
    except (urllib.error.URLError, OSError) as exc:
        print(f"pytree: Download fehlgeschlagen: {exc}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="pytree-dl-") as tmp:
        archive = Path(tmp) / f"{tag}.zip"
        archive.write_bytes(data)
        try:
            code = install_from_archive(archive)
        except zipfile.BadZipFile:
            print("pytree: Heruntergeladenes Archiv ist beschädigt.", file=sys.stderr)
            return 1
    if code == 0:
        print(f"Fertig. pytree {tag} ist beim nächsten Start aktiv.")
    return code
