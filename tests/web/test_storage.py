from pathlib import Path

from pygitmirror.web import _storage
from tests.helpers import git


def _mirror(path: Path) -> Path:
    path.mkdir(parents=True)
    git("init", "-q", "--bare", cwd=path)
    return path


def test_only_local_mirrors_are_counted_and_deleted(tmp_path: Path) -> None:
    _mirror(tmp_path / "org" / "one.git")
    _mirror(tmp_path / "group" / "sub" / "two.git")
    notes = tmp_path / "org" / "notes.txt"
    notes.write_text("keep me")
    fake = tmp_path / "other" / "folder.git"
    fake.mkdir(parents=True)
    (fake / "file").write_text("not a repository")

    usage = _storage.usage(tmp_path)
    assert usage["mirrors"] == 2 and usage["used"] > 0
    assert usage["total"] >= usage["free"] > 0 and usage["path"] == str(tmp_path)

    assert _storage.clear(tmp_path) == 2
    assert notes.read_text() == "keep me" and (fake / "file").is_file()
    assert not (tmp_path / "group").exists()
    assert _storage.usage(tmp_path)["mirrors"] == 0


def test_a_folder_which_does_not_exist_yet(tmp_path: Path) -> None:
    usage = _storage.usage(tmp_path / "later")
    assert usage["mirrors"] == 0 and usage["free"] > 0
    assert _storage.clear(tmp_path / "later") == 0
