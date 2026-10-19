"""Textual-App: interaktive, tastaturgesteuerte Disk-Usage-Baumansicht."""

from __future__ import annotations

import time
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from pytree.core.format import human_size
from pytree.core.model import Node, ScanIssue, ScanState
from pytree.core.scan import reset_node, scan_level, scan_recursive
from pytree.tui.labels import SortMode, node_label, sort_children
from pytree.tui.widgets import HelpScreen, IssuesScreen, PyTreeView, StatusBar

_PROGRESS_THROTTLE_SECONDS = 0.15


class PyTreeApp(App[None]):
    """Read-only Disk-Usage-Analyzer: lazy Scan pro aufgeklapptem Teilbaum."""

    CSS = """
    Tree {
        height: 1fr;
    }
    StatusBar {
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("r", "rescan_selected", "Rescan"),
        Binding("s", "toggle_sort", "Sortierung"),
        Binding("e", "show_issues", "Issues"),
        Binding("question_mark", "show_help", "Hilfe"),
        Binding("f1", "show_help", "Hilfe", show=False),
        Binding("q", "quit", "Beenden"),
    ]

    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self._root_path = root_path
        self._root_node = Node(
            path=root_path, name=str(root_path), is_dir=root_path.is_dir()
        )
        self._treenodes: dict[int, TreeNode[Node]] = {}
        self._issues: list[ScanIssue] = []
        self._scanning_count = 0
        self._sort_mode = SortMode.SIZE

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield PyTreeView(
                node_label(self._root_node), data=self._root_node, id="tree"
            )
            yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        self._treenodes[id(self._root_node)] = tree.root
        if self._root_node.is_dir:
            self._begin_scan(self._root_node, tree.root, auto_expand=True)
        else:
            self._root_node.state = ScanState.DONE
        self._refresh_status()
        tree.focus()

    # -- Baum-Interaktion ---------------------------------------------------

    def on_tree_node_expanded(self, event: Tree.NodeExpanded[Node]) -> None:
        core_node = event.node.data
        if core_node is None or not core_node.is_dir:
            return
        self._treenodes[id(core_node)] = event.node
        if core_node.children is None:
            self._begin_scan(core_node, event.node)
        elif not event.node.children:
            # Daten wurden bereits durch den rekursiven Hintergrund-Scan
            # eines Vorfahren geladen, die UI-Knoten fehlen aber noch.
            self._populate_children(event.node, core_node)

    def action_rescan_selected(self) -> None:
        tree = self.query_one(Tree)
        tree_node = tree.cursor_node
        if tree_node is None or tree_node.data is None:
            return
        core_node = tree_node.data
        if not core_node.is_dir:
            return
        reset_node(core_node)
        tree_node.remove_children()
        tree_node.set_label(node_label(core_node))
        self._begin_scan(core_node, tree_node)

    def action_toggle_sort(self) -> None:
        self._sort_mode = self._sort_mode.other
        tree = self.query_one(Tree)
        expanded_ids: set[int] = set()
        self._collect_expanded_ids(tree.root, expanded_ids)
        self._rebuild_sorted(tree.root)
        self._apply_expanded_ids(tree.root, expanded_ids)
        self._refresh_status()

    def action_show_issues(self) -> None:
        self.push_screen(IssuesScreen(list(self._issues)))

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    # -- Scanning -------------------------------------------------------

    def _begin_scan(
        self, core_node: Node, tree_node: TreeNode[Node], auto_expand: bool = False
    ) -> None:
        issues = scan_level(core_node)
        self._issues.extend(issues)
        self._populate_children(tree_node, core_node)
        if auto_expand:
            tree_node.expand()
        self._scanning_count += 1
        self._refresh_status()
        self._scan_recursive_worker(core_node)

    @work(thread=True, exclusive=False)
    def _scan_recursive_worker(self, core_node: Node) -> None:
        last_update = 0.0

        def on_progress(node: Node) -> None:
            nonlocal last_update
            now = time.monotonic()
            if node is not core_node and now - last_update < _PROGRESS_THROTTLE_SECONDS:
                return
            last_update = now
            self.call_from_thread(self._apply_progress, node)

        issues = scan_recursive(core_node, on_progress=on_progress)
        self.call_from_thread(self._finish_scan, issues)

    def _apply_progress(self, node: Node) -> None:
        self._refresh_label(node)
        ancestor = node.parent
        while ancestor is not None:
            if ancestor.children is not None:
                ancestor.size = sum(c.size for c in ancestor.children)
                ancestor.file_count = sum(c.file_count for c in ancestor.children)
            self._refresh_label(ancestor)
            ancestor = ancestor.parent
        self._refresh_status()

    def _finish_scan(self, issues: list[ScanIssue]) -> None:
        self._issues.extend(issues)
        self._scanning_count = max(0, self._scanning_count - 1)
        for tree_node in list(self._treenodes.values()):
            core_node = tree_node.data
            if core_node is not None:
                tree_node.set_label(node_label(core_node))
        self._refresh_status()

    # -- UI-Hilfsfunktionen -----------------------------------------------

    def _populate_children(self, tree_node: TreeNode[Node], core_node: Node) -> None:
        tree_node.remove_children()
        for child in sort_children(core_node.children or [], self._sort_mode):
            label = node_label(child)
            if child.is_dir:
                child_tree_node = tree_node.add(label, data=child, allow_expand=True)
            else:
                child_tree_node = tree_node.add_leaf(label, data=child)
            self._treenodes[id(child)] = child_tree_node
        tree_node.set_label(node_label(core_node))

    def _collect_expanded_ids(self, tree_node: TreeNode[Node], acc: set[int]) -> None:
        if tree_node.data is not None and tree_node.is_expanded:
            acc.add(id(tree_node.data))
        for child in tree_node.children:
            self._collect_expanded_ids(child, acc)

    def _rebuild_sorted(self, tree_node: TreeNode[Node]) -> None:
        core_node = tree_node.data
        if core_node is None or not core_node.is_dir or core_node.children is None:
            return
        self._populate_children(tree_node, core_node)
        for child in tree_node.children:
            self._rebuild_sorted(child)

    def _apply_expanded_ids(self, tree_node: TreeNode[Node], expanded_ids: set[int]) -> None:
        if tree_node.data is not None and id(tree_node.data) in expanded_ids:
            tree_node.expand()
        for child in tree_node.children:
            self._apply_expanded_ids(child, expanded_ids)

    def _refresh_label(self, node: Node) -> None:
        tree_node = self._treenodes.get(id(node))
        if tree_node is not None:
            tree_node.set_label(node_label(node))

    def _refresh_status(self) -> None:
        status = self.query_one(StatusBar)
        root = self._root_node
        parts = [
            str(self._root_path),
            human_size(root.size),
            f"{root.file_count} Dateien",
            f"sortiert: {self._sort_mode.label} (s)",
        ]
        if self._issues:
            parts.append(f"{len(self._issues)} übersprungen (e)")
        if self._scanning_count > 0:
            parts.append("scanne…")
        status.update("  |  ".join(parts))
