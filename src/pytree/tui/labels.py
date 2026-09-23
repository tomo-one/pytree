"""Node -> Rich-Text-Label-Rendering und Sortierung für die Baumansicht."""

from __future__ import annotations

from rich.text import Text

from pytree.core.format import human_size, size_bar
from pytree.core.model import Node, ScanState


def sort_children(children: list[Node]) -> list[Node]:
    """Größte zuerst; noch nicht gescannte Verzeichnisse (size=0) rutschen
    dadurch automatisch ans Ende und können bei Bekanntwerden ihrer Größe
    wieder nach oben wandern."""
    return sorted(children, key=lambda n: (-(n.size or 0), n.name.lower()))


def _bar_style(fraction: float | None) -> str:
    if fraction is None:
        return "dim"
    if fraction > 0.75:
        return "red"
    if fraction > 0.40:
        return "yellow"
    return "green"


def node_label(node: Node) -> Text:
    text = Text()

    if node.state == ScanState.ERROR:
        text.append("! ", style="bold red")
    elif node.is_dir and node.state == ScanState.PENDING:
        text.append("… ", style="dim")
    elif node.is_dir and node.state == ScanState.SCANNING:
        text.append("⟳ ", style="cyan")

    if node.is_symlink:
        name = f"{node.name} @"
    elif node.is_dir:
        name = f"{node.name}/"
    else:
        name = node.name
    text.append(name)

    text.append("  ")
    if node.is_dir and node.state == ScanState.PENDING:
        text.append("…", style="dim")
    else:
        text.append(human_size(node.size), style="bold")

    if node.parent is not None:
        fraction = node.percent_of_parent()
        text.append("  ")
        text.append(size_bar(fraction), style=_bar_style(fraction))

    if node.state == ScanState.ERROR and node.error:
        text.append(f"  ({node.error})", style="red dim")

    return text
