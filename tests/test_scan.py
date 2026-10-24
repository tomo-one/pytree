from __future__ import annotations

import os
from pathlib import Path

from pytree.core.model import Node, ScanState
from pytree.core.scan import reset_node, scan_level, scan_recursive


def _root_node(path: Path) -> Node:
    return Node(path=path, name=path.name, is_dir=True)


def test_scan_level_only_immediate_children(sample_tree: Path):
    root = _root_node(sample_tree)
    issues = scan_level(root)

    assert issues == []
    assert root.state == ScanState.DONE
    names = {c.name for c in root.children}
    assert names == {"a.txt", "sub1", "sub2"}

    sub1 = next(c for c in root.children if c.name == "sub1")
    assert sub1.is_dir
    assert sub1.children is None
    assert sub1.state == ScanState.PENDING
    # scan_level ist nicht rekursiv: sub1 traegt noch keine Groesse bei
    assert root.size == 100


def test_scan_recursive_aggregates_bottom_up(sample_tree: Path):
    root = _root_node(sample_tree)
    progressed: list[str] = []

    scan_recursive(root, on_progress=lambda n: progressed.append(n.name))

    assert root.size == 360
    sub1 = next(c for c in root.children if c.name == "sub1")
    sub2 = next(c for c in root.children if c.name == "sub2")
    assert sub1.size == 250
    assert sub2.size == 10

    sub1a = next(c for c in sub1.children if c.name == "sub1a")
    assert sub1a.size == 50

    # Bottom-up: sub1a muss vor sub1 fertig gemeldet werden
    assert progressed.index("sub1a") < progressed.index("sub1")
    assert "sub2" in progressed
    assert progressed[-1] == root.name


def test_scan_handles_permission_error_without_crashing(sample_tree: Path, monkeypatch):
    root = _root_node(sample_tree)
    real_scandir = os.scandir

    def failing_scandir(path):
        if Path(path).name == "sub1":
            raise PermissionError("Zugriff verweigert")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", failing_scandir)

    issues = scan_recursive(root)

    sub1 = next(c for c in root.children if c.name == "sub1")
    assert sub1.state == ScanState.ERROR
    assert sub1.size == 0
    assert any("sub1" in str(issue.path) for issue in issues)

    # Geschwister-Scan (sub2, a.txt) laeuft trotzdem ungestoert weiter
    sub2 = next(c for c in root.children if c.name == "sub2")
    assert sub2.size == 10
    assert root.size == 100 + 0 + 10


def test_scan_skips_broken_entry_but_continues(sample_tree: Path, monkeypatch):
    root = _root_node(sample_tree)
    real_entries = list(os.scandir(sample_tree))

    class BrokenEntry:
        name = "broken"
        path = str(sample_tree / "broken")

        def is_symlink(self):
            raise OSError("kaputter Reparse-Point")

    monkeypatch.setattr(
        os, "scandir", lambda path: iter(real_entries + [BrokenEntry()])
    )

    issues = scan_level(root)

    assert any("broken" in str(issue.path) for issue in issues)
    assert {c.name for c in root.children} == {"a.txt", "sub1", "sub2"}


def test_reset_node_clears_cached_state(sample_tree: Path):
    root = _root_node(sample_tree)
    scan_recursive(root)
    assert root.size == 360

    reset_node(root)

    assert root.children is None
    assert root.size == 0
    assert root.state == ScanState.PENDING


def test_symlink_counted_but_not_recursed(tmp_path: Path):
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "big.bin").write_bytes(b"x" * 1000)

    root_dir = tmp_path / "root"
    root_dir.mkdir()
    (root_dir / "link").symlink_to(target_dir)

    root = _root_node(root_dir)
    scan_recursive(root)

    link_node = root.children[0]
    assert link_node.is_symlink
    assert link_node.is_dir is False
    assert link_node.children == []


def test_scan_recursive_skip_leaves_subtree_untouched(sample_tree: Path):
    root = _root_node(sample_tree)
    scan_level(root)
    sub1 = next(c for c in root.children if c.name == "sub1")

    scan_recursive(root, skip=sub1)

    assert sub1.children is None
    sub2 = next(c for c in root.children if c.name == "sub2")
    assert sub2.size == 10
    assert root.size == 110
