"""Kommandozeilen-Einstiegspunkt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pytree",
        description="Interaktiver, tastaturgesteuerter Disk-Usage-Analyzer.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Zu analysierendes Verzeichnis (default: .)"
    )
    args = parser.parse_args(argv)

    target = Path(args.path).expanduser()
    if not target.exists():
        print(f"pytree: Pfad nicht gefunden: {target}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"pytree: kein Verzeichnis: {target}", file=sys.stderr)
        return 2

    from pytree.tui.app import PyTreeApp

    app = PyTreeApp(target.resolve())
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
