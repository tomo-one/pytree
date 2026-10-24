"""Kommandozeilen-Einstiegspunkt."""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from pytree import __version__


def _make_streams_utf8_safe() -> None:
    """Verhindert Abstürze durch Unicode-Baum-/Balkenzeichen auf Konsolen mit
    nicht-UTF-8-Codepage (z.B. klassisches cmd.exe unter Windows): nicht
    darstellbare Zeichen werden ersetzt statt eine UnicodeEncodeError
    auszulösen."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass


def main(argv: list[str] | None = None) -> int:
    _make_streams_utf8_safe()

    parser = argparse.ArgumentParser(
        prog="pytree",
        description="Interaktiver, tastaturgesteuerter Disk-Usage-Analyzer.",
        epilog="Ohne Angabe von PATH wird das aktuelle Verzeichnis analysiert.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Zu analysierendes Verzeichnis (default: .)"
    )
    parser.add_argument("--version", action="version", version=f"pytree {__version__}")
    parser.add_argument(
        "--update", action="store_true", help="auf die neueste Version von GitHub aktualisieren"
    )
    parser.add_argument(
        "--check-update",
        action="store_true",
        help="nur prüfen, ob eine neuere Version verfügbar ist",
    )
    args = parser.parse_args(argv)

    if args.update or args.check_update:
        from pytree.update import run_update

        return run_update(check_only=not args.update)

    target = Path(args.path).expanduser()
    if not target.exists():
        print(f"pytree: Pfad nicht gefunden: {target}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"pytree: kein Verzeichnis: {target}", file=sys.stderr)
        return 2

    target = target.resolve()

    try:
        from pytree.tui.app import PyTreeApp
    except ModuleNotFoundError as exc:
        if exc.name != "textual":
            raise
        print(
            "pytree: Das Paket 'textual' fehlt. Installieren mit:\n"
            f"  {sys.executable} -m pip install --user textual",
            file=sys.stderr,
        )
        return 1

    print(f"pytree {__version__} – analysiere: {target}  (? = Hilfe, q = beenden)")

    try:
        app = PyTreeApp(target)
        app.run()
    except Exception:
        print("pytree: unerwarteter Fehler:", file=sys.stderr)
        traceback.print_exc()
        if sys.platform == "win32" and sys.stdin.isatty():
            input("Beliebige Taste/Enter zum Schließen ...")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
