from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest

from pytree import update

ROOT = Path(__file__).resolve().parent.parent


def test_parse_version_and_latest_tag():
    assert update.parse_version("v1.2.3") == (1, 2, 3)
    assert update.parse_version("0.10.0") == (0, 10, 0)
    assert update.parse_version("v1.2") is None
    assert update.parse_version("release-1") is None
    names = ["v0.9.0", "v0.10.0", "v0.5.1", "nightly", "v0.10.0-rc1"]
    assert update.latest_tag(names) == "v0.10.0"
    assert update.latest_tag(["foo"]) is None


def test_is_newer():
    assert update.is_newer("v0.6.0", "0.5.9")
    assert not update.is_newer("v0.5.1", "0.5.1")
    assert not update.is_newer("v0.5.0", "0.5.1")
    assert not update.is_newer("garbage", "0.5.1")


def test_check_update_reports_new_and_current(monkeypatch, capsys):
    monkeypatch.setattr(update, "__version__", "0.5.1")
    monkeypatch.setattr(update, "fetch_latest_tag", lambda: "v0.6.0")
    assert update.run_update(check_only=True) == 0
    assert "v0.6.0" in capsys.readouterr().out

    monkeypatch.setattr(update, "fetch_latest_tag", lambda: "v0.5.1")
    assert update.run_update(check_only=True) == 0
    assert "aktuell" in capsys.readouterr().out


def test_update_refused_when_not_managed(monkeypatch, capsys):
    monkeypatch.delenv("PYTREE_MANAGED", raising=False)
    assert update.run_update() == 2
    assert "install.py" in capsys.readouterr().err


def test_network_error_is_reported_not_raised(monkeypatch, capsys):
    def boom(url: str) -> bytes:
        raise urllib.error.URLError("kein Netz")

    monkeypatch.setenv("PYTREE_MANAGED", "1")
    monkeypatch.setattr(update, "_http_get", boom)
    assert update.run_update() == 1
    assert "kein Netz" in capsys.readouterr().err


def _repo_zip() -> bytes:
    """Archiv wie von GitHub: ein Wurzelordner mit install.py und src/pytree."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.write(ROOT / "install.py", "pytree-9.9.9/install.py")
        for path in (ROOT / "src" / "pytree").rglob("*.py"):
            zf.write(path, f"pytree-9.9.9/{path.relative_to(ROOT).as_posix()}")
    return buf.getvalue()


@pytest.mark.skipif(os.name == "nt", reason="prüft das POSIX-Startskript")
def test_full_update_installs_downloaded_version(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PYTREE_MANAGED", "1")
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.setattr(update, "__version__", "0.0.1")

    def fake_get(url: str) -> bytes:
        if url == update.TAGS_URL:
            return json.dumps([{"name": "v9.9.9"}, {"name": "v0.5.0"}]).encode()
        assert url == update.ARCHIVE_URL.format(tag="v9.9.9")
        return _repo_zip()

    monkeypatch.setattr(update, "_http_get", fake_get)

    assert update.run_update() == 0, capsys.readouterr()

    launcher = tmp_path / ".local" / "bin" / "pytree"
    assert (tmp_path / ".local" / "share" / "pytree" / "pytree" / "update.py").exists()
    result = subprocess.run(
        [str(launcher), "--check-update"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert "PYTREE_MANAGED=1" in launcher.read_text()
    assert result.returncode in (0, 1), result.stderr


def test_corrupt_archive_is_reported(monkeypatch, tmp_path: Path):
    archive = tmp_path / "x.zip"
    archive.write_bytes(b"kein zip")
    with pytest.raises(zipfile.BadZipFile):
        update.install_from_archive(archive)
