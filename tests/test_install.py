from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(os.name == "nt", reason="testet das POSIX-Startskript")
def test_install_creates_working_launcher_and_uninstall(tmp_path: Path):
    env = {**os.environ, "HOME": str(tmp_path)}
    env.pop("PYTHONPATH", None)

    def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--no-deps", *args],
            env=env,
            capture_output=True,
            text=True,
        )

    result = run_installer()
    assert result.returncode == 0, result.stdout + result.stderr

    launcher = tmp_path / ".local" / "bin" / "pytree"
    lib_dir = tmp_path / ".local" / "share" / "pytree"
    assert os.access(launcher, os.X_OK)
    assert (lib_dir / "pytree" / "__init__.py").exists()

    version = subprocess.run(
        [str(launcher), "--version"], env=env, capture_output=True, text=True, cwd=tmp_path
    )
    assert version.returncode == 0, version.stderr
    assert version.stdout.startswith("pytree ")

    result = run_installer("--uninstall")
    assert result.returncode == 0
    assert not launcher.exists()
    assert not lib_dir.exists()


def test_start_script_runs_from_source_tree():
    result = subprocess.run(
        [sys.executable, str(ROOT / "start.py"), "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("pytree ")
