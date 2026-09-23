"""Reine String-Formatierung, keine Abhängigkeiten - unabhängig testbar."""

from __future__ import annotations

_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


def human_size(num_bytes: int | None) -> str:
    """Binäre Größenformatierung (÷1024) mit vertrauten Labels (KB/MB/...,
    bewusst nicht KiB-pedantisch)."""
    if num_bytes is None:
        return "?"
    if num_bytes < 0:
        raise ValueError("num_bytes must not be negative")

    size = float(num_bytes)
    for unit in _UNITS:
        if size < 1024 or unit == _UNITS[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {_UNITS[-1]}"


def size_bar(fraction: float | None, width: int = 10) -> str:
    """Block-Balken für den Prozentanteil an der Elterngröße, z.B.
    "[████████░░] 82.3%". `fraction=None` (unbekannt) ergibt einen leeren
    Balken mit "?"-Anzeige."""
    if fraction is None:
        return f"[{'?' * width}]  ?%"

    clamped = max(0.0, min(1.0, fraction))
    filled = round(clamped * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {clamped * 100:5.1f}%"
