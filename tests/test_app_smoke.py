from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from pytree.tui.app import PyTreeApp
from pytree.tui.labels import is_parent_link


@pytest.mark.asyncio
async def test_app_starts_and_shows_root(sample_tree: Path):
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("Tree")
        assert tree.root.data is not None
        assert tree.root.data.path == sample_tree


@pytest.mark.asyncio
async def test_navigation_and_quit_do_not_crash(sample_tree: Path):
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("up")
        await pilot.press("question_mark")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_arrow_and_vi_keys_expand_and_navigate(sample_tree: Path):
    """Regressionstest: Pfeil-links/rechts würden vom geerbten Scroll-Binding
    des Tree geschluckt, sobald das Root-Label breiter als das Terminal ist
    (lange tmp_path-Pfade reproduzieren das). j/k/h/l gab es vorher gar nicht."""
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("Tree")

        await pilot.press("j")
        await pilot.pause()
        cursor_after_j = tree.cursor_node
        assert cursor_after_j is not None
        assert cursor_after_j is not tree.root

        sub1 = next(c for c in tree.root.children if c.data.name == "sub1")
        tree.move_cursor(sub1)
        await pilot.pause()
        assert not sub1.is_expanded

        await pilot.press("right")
        await pilot.pause()
        assert sub1.is_expanded

        await pilot.press("left")
        await pilot.pause()
        assert not sub1.is_expanded

        await pilot.press("l")
        await pilot.pause()
        assert sub1.is_expanded

        await pilot.press("h")
        await pilot.pause()
        assert not sub1.is_expanded

        tree.move_cursor(sub1)
        await pilot.pause()
        line_before = tree.cursor_line
        await pilot.press("k")
        await pilot.pause()
        assert tree.cursor_line == line_before - 1


@pytest.mark.asyncio
async def test_expand_triggers_lazy_scan(sample_tree: Path):
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("Tree")
        sub1 = next(c for c in tree.root.children if c.data.name == "sub1")
        sub1.expand()
        await pilot.pause()
        # Warten, bis der Hintergrund-Worker den rekursiven Scan beendet hat.
        for _ in range(50):
            if sub1.data.size == 250:
                break
            await asyncio.sleep(0.05)
        assert sub1.data.size == 250


def _names(tree_node) -> list[str]:
    """Kinder-Namen ohne den ".."-Eintrag zur Elternebene."""
    return [c.data.name for c in tree_node.children if not is_parent_link(c.data)]


async def _wait_for_root_scan(app: PyTreeApp, expected_size: int = 360) -> None:
    for _ in range(50):
        if app._root_node.size == expected_size:
            return
        await asyncio.sleep(0.05)
    raise AssertionError("Scan nicht innerhalb der Wartezeit abgeschlossen")


@pytest.mark.asyncio
async def test_sort_toggle_switches_between_size_and_name(sample_tree: Path):
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _wait_for_root_scan(app)
        tree = app.query_one("Tree")

        # Direkt nach dem initialen Scan spiegelt die Baum-Reihenfolge noch
        # den Stand beim ersten Populieren wider (Unterverzeichnisgrößen
        # waren da noch nicht final bekannt) - "s" erzwingt eine Neusortierung
        # mit den inzwischen vollständigen Größen.
        await pilot.press("s")  # -> Name
        await pilot.pause()
        names = _names(tree.root)
        assert names == ["a.txt", "sub1", "sub2"]

        await pilot.press("s")  # -> Größe (sub1=250, a.txt=100, sub2=10)
        await pilot.pause()
        names = _names(tree.root)
        assert names == ["sub1", "a.txt", "sub2"]

        await pilot.press("s")  # -> Name
        await pilot.pause()
        names = _names(tree.root)
        assert names == ["a.txt", "sub1", "sub2"]


@pytest.mark.asyncio
async def test_sort_toggle_preserves_expanded_state(sample_tree: Path):
    app = PyTreeApp(sample_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _wait_for_root_scan(app)
        tree = app.query_one("Tree")

        sub1 = next(c for c in tree.root.children if c.data.name == "sub1")
        sub1.expand()
        await pilot.pause()
        assert sub1.is_expanded
        assert {c.data.name for c in sub1.children} == {"b.txt", "sub1a"}

        await pilot.press("s")
        await pilot.pause()

        sub1 = next(c for c in tree.root.children if c.data.name == "sub1")
        assert sub1.is_expanded
        assert {c.data.name for c in sub1.children} == {"b.txt", "sub1a"}


@pytest.mark.asyncio
async def test_parent_link_is_first_entry_of_root(sample_tree: Path):
    app = PyTreeApp(sample_tree / "sub1")
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = app.query_one("Tree")
        first = tree.root.children[0]
        assert is_parent_link(first.data)
        assert first.data.path == sample_tree
        assert not first.allow_expand


@pytest.mark.asyncio
async def test_go_up_with_key_u_keeps_scanned_subtree(sample_tree: Path):
    sub1_path = sample_tree / "sub1"
    app = PyTreeApp(sub1_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _wait_for_root_scan(app, expected_size=250)
        old_root = app._root_node

        await pilot.press("u")
        await pilot.pause()

        assert app._root_path == sample_tree
        assert app._root_node.path == sample_tree
        tree = app.query_one("Tree")
        assert set(_names(tree.root)) == {"a.txt", "sub1", "sub2"}

        sub1 = next(c for c in tree.root.children if c.data.name == "sub1")
        assert sub1.data is old_root
        assert sub1.data.parent is app._root_node
        assert sub1.is_expanded
        assert tree.cursor_node is sub1

        await _wait_for_root_scan(app, expected_size=360)
        assert sub1.data.size == 250


@pytest.mark.asyncio
async def test_go_up_via_parent_link_with_enter_and_right_arrow(sample_tree: Path):
    for key in ("enter", "right"):
        app = PyTreeApp(sample_tree / "sub1" / "sub1a")
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("Tree")
            tree.move_cursor(tree.root.children[0])
            await pilot.pause()
            assert is_parent_link(tree.cursor_node.data)

            await pilot.press(key)
            await pilot.pause()
            assert app._root_path == sample_tree / "sub1", key


@pytest.mark.asyncio
async def test_go_up_twice_and_backspace(sample_tree: Path):
    app = PyTreeApp(sample_tree / "sub1" / "sub1a")
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        assert app._root_path == sample_tree
        await _wait_for_root_scan(app)
        tree = app.query_one("Tree")
        assert set(_names(tree.root)) == {"a.txt", "sub1", "sub2"}


@pytest.mark.asyncio
async def test_go_up_refused_when_parent_unreadable(sample_tree: Path, monkeypatch):
    import os

    real_scandir = os.scandir

    def deny_parent(path):
        if Path(path) == sample_tree:
            raise PermissionError("Zugriff verweigert")
        return real_scandir(path)

    app = PyTreeApp(sample_tree / "sub1")
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(os, "scandir", deny_parent)
        await pilot.press("u")
        await pilot.pause()
        assert app._root_path == sample_tree / "sub1"
