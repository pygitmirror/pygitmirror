import importlib
import subprocess
import sys
from pathlib import Path
from pkgutil import walk_packages

import pytest

import pygitmirror

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "src" / "pygitmirror"
MAX_LINES = 300


def all_modules() -> list[str]:
    return [module.name for module in walk_packages([str(SOURCE)], prefix="pygitmirror.")]


@pytest.mark.parametrize("module_name", all_modules())
def test_loads(module_name: str) -> None:
    importlib.import_module(module_name)


def test_exports_exist() -> None:
    for name in pygitmirror.__all__:
        assert hasattr(pygitmirror, name)
    assert sorted(pygitmirror.__all__, key=str.lower) == sorted(
        set(pygitmirror.__all__), key=str.lower
    )


def test_runs_as_a_module() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pygitmirror", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == f"git-mirror {pygitmirror.__version__}"


def written_by_hand() -> list[Path]:
    """Return the tracked text files, without those which nobody writes by hand."""
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.splitlines()  # empty outside a git repository, as in a source distribution
    generated = ("uv.lock", "LICENSE", "OFL.txt")
    binary = (".woff2", ".png", ".svg")
    return [
        ROOT / name
        for name in listed
        if not name.endswith((*generated, *binary)) and (ROOT / name).is_file()
    ]


@pytest.mark.parametrize("path", written_by_hand(), ids=lambda path: str(path.relative_to(ROOT)))
def test_no_file_is_long(path: Path) -> None:
    assert len(path.read_text(encoding="utf-8").splitlines()) <= MAX_LINES
