import importlib
import subprocess
import sys
from pathlib import Path
from pkgutil import walk_packages

import pytest

import pygitmirror

SOURCE = Path(__file__).parent.parent / "src" / "pygitmirror"
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


@pytest.mark.parametrize("path", sorted(SOURCE.rglob("*.py")), ids=lambda path: path.name)
def test_files_stay_short(path: Path) -> None:
    assert len(path.read_text(encoding="utf-8").splitlines()) < MAX_LINES
