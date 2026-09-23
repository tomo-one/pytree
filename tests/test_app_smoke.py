from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from pytree.tui.app import PyTreeApp


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
