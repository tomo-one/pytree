#!/usr/bin/env python3
"""Einfache Installation von pytree für Windows, macOS und Linux.

    python3 install.py              installieren (Windows: python install.py)
    python3 install.py --uninstall  wieder entfernen
    python3 install.py --no-deps    textual nicht per pip installieren

Es werden weder setuptools noch ein pip-Build gebraucht und keine Admin-Rechte.
Das Paket wird in ein Benutzerverzeichnis kopiert und ein Startskript
`pytree` angelegt. Nur die Abhängigkeit textual kommt per `pip install --user`.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 9)
HERE = Path(__file__).resolve().parent
SOURCE_PACKAGE = HERE / "src" / "pytree"
IS_WINDOWS = os.name == "nt"


def _locations() -> tuple[Path, Path, Path]:
    """(Verzeichnis mit dem Paket, Verzeichnis des Startskripts, Startskript)."""
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        lib_dir = base / "pytree"
        bin_dir = lib_dir / "bin"
        return lib_dir, bin_dir, bin_dir / "pytree.cmd"
    lib_dir = Path.home() / ".local" / "share" / "pytree"
    bin_dir = Path.home() / ".local" / "bin"
    return lib_dir, bin_dir, bin_dir / "pytree"


def _write_launcher(launcher: Path, lib_dir: Path, py: str) -> None:
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if IS_WINDOWS:
        text = (
            "@echo off\n"
            f'set "PYTHONPATH={lib_dir};%PYTHONPATH%"\n'
            f'"{py}" -m pytree %*\n'
        )
        with open(launcher, "w", newline="\r\n", encoding="utf-8") as fh:
            fh.write(text)
    else:
        text = (
            "#!/bin/sh\n"
            f"PYTHONPATH={shlex.quote(str(lib_dir))}${{PYTHONPATH:+:$PYTHONPATH}} "
            f'exec {shlex.quote(py)} -m pytree "$@"\n'
        )
        launcher.write_text(text, encoding="utf-8")
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def _pip_install_textual(python: str, user: bool) -> subprocess.CompletedProcess[str]:
    cmd = [python, "-m", "pip", "install", "textual>=0.58"]
    if user:
        cmd.insert(4, "--user")
    result = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result


def _private_venv_with_textual(venv_dir: Path) -> str | None:
    print(f"Lege private Umgebung an: {venv_dir}")
    created = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)], capture_output=True, text=True
    )
    if created.returncode != 0:
        print(created.stdout + created.stderr, file=sys.stderr)
        print(
            "Anlegen der venv fehlgeschlagen. Unter Debian/Ubuntu fehlt oft das Paket:\n"
            "  apt install python3-venv   (als root, sonst Admin fragen)",
            file=sys.stderr,
        )
        return None
    python = str(_venv_python(venv_dir))
    return python if _pip_install_textual(python, user=False).returncode == 0 else None


def _install_textual(venv_dir: Path) -> str | None:
    """Stellt textual bereit und liefert das Python, mit dem pytree laufen soll."""
    if importlib.util.find_spec("textual") is not None:
        print("textual ist bereits vorhanden.")
        return sys.executable
    print("Installiere textual ...")
    result = _pip_install_textual(sys.executable, user=not _in_venv())
    if result.returncode == 0:
        return sys.executable
    if "externally-managed-environment" in result.stderr and not _in_venv():
        print("\nDas System sperrt pip (PEP 668). Verwende stattdessen eine private venv.")
        python = _private_venv_with_textual(venv_dir)
        if python:
            return python
    print(
        "\nInstallation von textual fehlgeschlagen. Häufige Ursachen:\n"
        "  - pip fehlt: unter Debian/Ubuntu `apt install python3-pip` (Admin nötig)\n"
        "  - kein Internetzugang zu PyPI\n"
        "Mit --no-deps überspringt der Installer diesen Schritt (textual muss\n"
        "dann bereits vorhanden sein).",
        file=sys.stderr,
    )
    return None


def _on_path(directory: Path) -> bool:
    wanted = os.path.normcase(os.path.abspath(directory))
    entries = os.environ.get("PATH", "").split(os.pathsep)
    return any(e and os.path.normcase(os.path.abspath(e)) == wanted for e in entries)


def _print_path_hint(bin_dir: Path, launcher: Path) -> None:
    if _on_path(bin_dir):
        return
    print(f"\nHinweis: {bin_dir} liegt nicht im PATH. Direkt aufrufbar ist es trotzdem:")
    print(f"  {launcher}")
    print("Dauerhaft in den PATH aufnehmen:")
    if IS_WINDOWS:
        print(
            "  PowerShell:  [Environment]::SetEnvironmentVariable('Path', "
            f"[Environment]::GetEnvironmentVariable('Path','User') + ';{bin_dir}', 'User')"
        )
        print("  (danach ein neues Terminal öffnen)")
    else:
        print(f"  echo 'export PATH=\"{bin_dir}:$PATH\"' >> ~/.bashrc && source ~/.bashrc")


def install(with_deps: bool) -> int:
    if sys.version_info < MIN_PYTHON:
        print(
            f"pytree braucht Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} oder neuer "
            f"(gefunden: {sys.version.split()[0]}).",
            file=sys.stderr,
        )
        return 1
    if not SOURCE_PACKAGE.is_dir():
        print(f"Quellpaket nicht gefunden: {SOURCE_PACKAGE}", file=sys.stderr)
        return 1

    lib_dir, bin_dir, launcher = _locations()
    py = sys.executable
    if with_deps:
        py = _install_textual(lib_dir / "venv") or ""
        if not py:
            return 1

    target = lib_dir / "pytree"
    if target.exists():
        shutil.rmtree(target)
    lib_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        SOURCE_PACKAGE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    _write_launcher(launcher, lib_dir, py)

    env = {**os.environ, "PYTHONPATH": str(lib_dir)}
    check = subprocess.run(
        [py, "-m", "pytree", "--version"],
        env=env,
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        print("Installation kopiert, aber der Testaufruf schlug fehl:", file=sys.stderr)
        print(check.stdout + check.stderr, file=sys.stderr)
        return 1

    print(f"\nInstalliert: {check.stdout.strip()}")
    print(f"Startskript: {launcher}")
    _print_path_hint(bin_dir, launcher)
    print("\nStart:  pytree [pfad]")
    return 0


def uninstall() -> int:
    lib_dir, bin_dir, launcher = _locations()
    removed = False
    if lib_dir.exists():
        shutil.rmtree(lib_dir)
        removed = True
    if launcher.exists():
        launcher.unlink()
        removed = True
    print("pytree entfernt (textual bleibt installiert)." if removed else "Nichts zu entfernen.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="pytree installieren oder entfernen.")
    parser.add_argument("--uninstall", action="store_true", help="pytree entfernen")
    parser.add_argument(
        "--no-deps", action="store_true", help="textual nicht per pip installieren"
    )
    args = parser.parse_args()
    return uninstall() if args.uninstall else install(with_deps=not args.no_deps)


if __name__ == "__main__":
    sys.exit(main())
