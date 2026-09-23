"""Kleine unterstützende Widgets: Statuszeile und modale Overlays."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from pytree.core.model import ScanIssue


class StatusBar(Static):
    """Statuszeile: aktueller Pfad, Anzahl Elemente, Scan-Status."""


HELP_TEXT = """\
[b]pytree[/b] - Tastenkürzel

  ↑/↓, j/k        Navigation
  →, Enter, l      Verzeichnis aufklappen (scannt bei Bedarf)
  ←, h             Verzeichnis zuklappen
  r                Markierten Knoten neu scannen
  e                Übersprungene Einträge anzeigen
  ?, F1            Diese Hilfe
  q, Ctrl+C        Beenden

Größen werden lazy ermittelt: ein Verzeichnis zeigt beim Aufklappen zunächst
"…" an, während im Hintergrund rekursiv weitergescannt wird. "r" erzwingt
einen erneuten Scan, um Änderungen auf der Platte zu erfassen.

[dim]Beliebige Taste zum Schließen[/dim]
"""


class HelpScreen(ModalScreen[None]):
    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT, id="help-text")

    def on_key(self, event) -> None:  # noqa: ANN001
        self.dismiss(None)

    def on_click(self) -> None:
        self.dismiss(None)


class IssuesScreen(ModalScreen[None]):
    def __init__(self, issues: list[ScanIssue]) -> None:
        super().__init__()
        self._issues = issues

    def compose(self) -> ComposeResult:
        if not self._issues:
            yield Static("Keine übersprungenen Einträge.", id="issues-text")
            return
        lines = [f"[b]{len(self._issues)} übersprungene Einträge[/b]\n"]
        for issue in self._issues[-200:]:
            lines.append(f"[red]! [/red] {issue.path}: {issue.message}")
        lines.append("\n[dim]Beliebige Taste zum Schließen[/dim]")
        with VerticalScroll():
            yield Static("\n".join(lines), id="issues-text")

    def on_key(self, event) -> None:  # noqa: ANN001
        self.dismiss(None)

    def on_click(self) -> None:
        self.dismiss(None)
