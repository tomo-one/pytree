"""Scanning-Logik: os.scandir-basiert, defensiv gegen Permission-Fehler,
kaputte Symlinks/Junctions etc. Eine einzelne fehlerhafte Datei/Verzeichnis
darf den Gesamt-Scan niemals abbrechen.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from pytree.core.model import Node, ScanIssue, ScanState


def scan_level(node: Node) -> list[ScanIssue]:
    """Scannt genau eine Ebene unterhalb von `node` (nicht rekursiv).

    Dateien erhalten sofort ihre echte Größe. Unterverzeichnisse werden als
    PENDING angelegt (children=None) - ihre Größe wird erst bei einem
    weiteren scan_level()/scan_recursive()-Aufruf ermittelt. Symlinks werden
    als eigenständige, nicht weiter verfolgte Blätter gezählt (verhindert
    Zyklen und Doppelzählung durch Junctions/Reparse-Points).
    """
    issues: list[ScanIssue] = []
    if not node.is_dir:
        node.state = ScanState.DONE
        return issues

    node.state = ScanState.SCANNING
    try:
        entries = list(os.scandir(node.path))
    except OSError as exc:
        node.state = ScanState.ERROR
        node.error = str(exc)
        node.children = []
        issues.append(ScanIssue(node.path, str(exc)))
        return issues

    children: list[Node] = []
    for entry in entries:
        try:
            if entry.is_symlink():
                st = entry.stat(follow_symlinks=False)
                child = Node(
                    path=Path(entry.path),
                    name=entry.name,
                    is_dir=False,
                    is_symlink=True,
                    size=st.st_size,
                    file_count=1,
                    children=[],
                    state=ScanState.DONE,
                    parent=node,
                )
            elif entry.is_dir(follow_symlinks=False):
                child = Node(
                    path=Path(entry.path),
                    name=entry.name,
                    is_dir=True,
                    children=None,
                    state=ScanState.PENDING,
                    parent=node,
                )
            else:
                st = entry.stat(follow_symlinks=False)
                child = Node(
                    path=Path(entry.path),
                    name=entry.name,
                    is_dir=False,
                    size=st.st_size,
                    file_count=1,
                    children=[],
                    state=ScanState.DONE,
                    parent=node,
                )
        except OSError as exc:
            issues.append(ScanIssue(Path(entry.path), str(exc)))
            continue
        children.append(child)

    node.children = children
    node.state = ScanState.DONE
    node.size = sum(c.size for c in children)
    node.file_count = sum(c.file_count for c in children)
    return issues


def scan_recursive(
    node: Node, on_progress: Callable[[Node], None] | None = None
) -> list[ScanIssue]:
    """Scannt `node` und alle Unterverzeichnisse vollständig (bottom-up
    aggregiert). Ruft `on_progress(node)` nach jedem fertig aggregierten
    Verzeichnis auf - Throttling von UI-Updates ist Sache des Aufrufers.
    Bricht bei einzelnen Fehlern nie ab, sammelt sie stattdessen.
    """
    issues: list[ScanIssue] = []
    _scan_recursive_inner(node, on_progress, issues)
    return issues


def _scan_recursive_inner(
    node: Node,
    on_progress: Callable[[Node], None] | None,
    issues: list[ScanIssue],
) -> None:
    if not node.is_dir:
        return

    if node.children is None:
        issues.extend(scan_level(node))

    for child in node.children or []:
        if child.is_dir:
            _scan_recursive_inner(child, on_progress, issues)

    if node.state != ScanState.ERROR:
        node.size = sum(c.size for c in node.children or [])
        node.file_count = sum(c.file_count for c in node.children or [])
        node.state = ScanState.DONE

    if on_progress is not None:
        on_progress(node)


def reset_node(node: Node) -> None:
    """Verwirft den gecachten Scan-Zustand eines Knotens (für Rescan)."""
    node.children = None
    node.size = 0
    node.file_count = 0
    node.state = ScanState.PENDING
    node.error = None
