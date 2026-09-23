from __future__ import annotations

import pytest

from pytree.core.format import human_size, size_bar


def test_human_size_bytes():
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"


def test_human_size_exact_kb_boundary():
    assert human_size(1024) == "1.0 KB"
    assert human_size(1023) == "1023 B"


def test_human_size_gb():
    assert human_size(int(1.5 * 1024**3)) == "1.5 GB"


def test_human_size_large_tb():
    assert human_size(5 * 1024**4) == "5.0 TB"


def test_human_size_unknown():
    assert human_size(None) == "?"


def test_human_size_rejects_negative():
    with pytest.raises(ValueError):
        human_size(-1)


def test_size_bar_zero():
    bar = size_bar(0.0, width=10)
    assert bar.startswith("[") and "0.0%" in bar
    assert "█" not in bar


def test_size_bar_full():
    bar = size_bar(1.0, width=10)
    assert "100.0%" in bar
    assert "░" not in bar


def test_size_bar_clamps_over_one():
    bar = size_bar(1.5, width=10)
    assert "100.0%" in bar


def test_size_bar_unknown():
    bar = size_bar(None, width=4)
    assert "?" in bar
