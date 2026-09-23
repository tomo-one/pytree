from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_tree(tmp_path: Path) -> Path:
    """Baut einen kleinen, deterministischen Verzeichnisbaum:

    tmp_path/
        a.txt        (100 B)
        sub1/
            b.txt    (200 B)
            sub1a/
                c.txt (50 B)
        sub2/
            d.txt    (10 B)

    Erwartete Größen: sub1a=50, sub1=250, sub2=10, root=360.
    """
    (tmp_path / "a.txt").write_bytes(b"x" * 100)

    sub1 = tmp_path / "sub1"
    sub1.mkdir()
    (sub1 / "b.txt").write_bytes(b"x" * 200)

    sub1a = sub1 / "sub1a"
    sub1a.mkdir()
    (sub1a / "c.txt").write_bytes(b"x" * 50)

    sub2 = tmp_path / "sub2"
    sub2.mkdir()
    (sub2 / "d.txt").write_bytes(b"x" * 10)

    return tmp_path
