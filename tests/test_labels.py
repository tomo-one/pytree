from __future__ import annotations

from pytree.core.model import Node
from pytree.tui.labels import SortMode, sort_children


def _node(name: str, size: int, is_dir: bool = False) -> Node:
    return Node(path=None, name=name, is_dir=is_dir, size=size)  # type: ignore[arg-type]


def test_sort_by_size_descending_default():
    children = [_node("b", 10), _node("a", 100), _node("c", 50)]
    result = sort_children(children)
    assert [c.name for c in result] == ["a", "c", "b"]


def test_sort_by_size_ties_broken_alphabetically():
    children = [_node("b", 10), _node("a", 10)]
    result = sort_children(children, SortMode.SIZE)
    assert [c.name for c in result] == ["a", "b"]


def test_sort_by_name_ignores_size():
    children = [_node("b", 10), _node("a", 100), _node("C", 50)]
    result = sort_children(children, SortMode.NAME)
    assert [c.name for c in result] == ["a", "b", "C"]


def test_sort_mode_toggle():
    assert SortMode.SIZE.other is SortMode.NAME
    assert SortMode.NAME.other is SortMode.SIZE
