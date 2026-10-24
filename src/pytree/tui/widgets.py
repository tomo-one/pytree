"""Kleine unterstützende Widgets: Statuszeile und modale Overlays."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Tree

from pytree.core.model import Node, ScanIssue
from pytree.tui.labels import is_parent_link


class StatusBar(Static):
    """Statuszeile: aktueller Pfad, Anzahl Elemente, Scan-Status."""


class PyTreeView(Tree[Node]):
    """Tree mit Pfeil-/Vi-Tasten für Auf-/Zuklappen und Navigation.

    Textuals Tree erbt von ScrollableContainer, das Pfeil-links/-rechts für
    horizontales Scrollen bindet. Sobald ein Label breiter als das Terminal
    ist (lange Pfade), würde das App-Level-Bindings übertrumpfen. Die Tasten
    müssen daher hier am Widget selbst liegen."""

    BINDINGS = [
        Binding("right", "expand_node", "Aufklappen", show=False),
        Binding("l", "expand_node", "Aufklappen", show=False),
        Binding("left", "collapse_node", "Zuklappen", show=False),
        Binding("h", "collapse_node", "Zuklappen", show=False),
        Binding("j", "cursor_down", "Runter", show=False),
        Binding("k", "cursor_up", "Hoch", show=False),
    ]

    def action_expand_node(self) -> None:
        node = self.cursor_node
        if node is not None and is_parent_link(node.data):
            self.app.action_go_up()  # type: ignore[attr-defined]
            return
        if node is not None and node.allow_expand and not node.is_expanded:
            node.expand()

    def action_collapse_node(self) -> None:
        node = self.cursor_node
        if node is not None and node.allow_expand and node.is_expanded:
            node.collapse()


HELP_TEXT = """\
[b]pytree[/b] - Tastenkürzel

  ↑/↓, j/k        Navigation
  →, Enter, l      Verzeichnis aufklappen (scannt bei Bedarf)
  ←, h             Verzeichnis zuklappen
  r                Markierten Knoten neu scannen
  u, Backspace     Eine Ebene höher (auch: ".." wählen)
  s                Sortierung umschalten (Größe/Name)
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
