from pathlib import Path

import pytest

from pygitmirror import Git, GitError, LocalMirror
from tests.helpers import Workshop, git, refs


@pytest.fixture
def shop(tmp_path: Path) -> Workshop:
    return Workshop(tmp_path, tmp_path / "source.git")


def test_fetch_equals_the_source(shop: Workshop, tmp_path: Path) -> None:
    git("tag", "v1", cwd=shop.work)
    shop.commit("on dev", branch="dev")
    mirror = LocalMirror(tmp_path / "nested" / "mirror.git", Git())
    mirror.fetch(str(shop.bare))
    assert mirror.refs() == refs(shop.bare)
    assert set(mirror.refs()) == {"refs/heads/main", "refs/heads/dev", "refs/tags/v1"}
    # Nothing about the source is stored in the mirror.
    assert "source.git" not in (mirror.path / "config").read_text()


def test_fetch_follows_deletions_and_rewrites(shop: Workshop, tmp_path: Path) -> None:
    shop.commit("on dev", branch="dev")
    mirror = LocalMirror(tmp_path / "mirror.git", Git())
    mirror.fetch(str(shop.bare))
    git("update-ref", "-d", "refs/heads/dev", cwd=shop.bare)
    git("checkout", "-q", "main", cwd=shop.work)
    git("branch", "-q", "-D", "dev", cwd=shop.work)
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=shop.work)
    shop.publish()
    mirror.fetch(str(shop.bare))
    assert mirror.refs() == refs(shop.bare)
    assert set(mirror.refs()) == {"refs/heads/main"}


def test_is_ancestor(shop: Workshop, tmp_path: Path) -> None:
    first = git("rev-parse", "HEAD", cwd=shop.work)
    second = shop.commit("second")
    mirror = LocalMirror(tmp_path / "mirror.git", Git())
    mirror.fetch(str(shop.bare))
    assert mirror.is_ancestor(first, second)
    assert not mirror.is_ancestor(second, first)
    assert not mirror.is_ancestor("0" * 39 + "1", second)


def test_push(shop: Workshop, tmp_path: Path) -> None:
    destination = tmp_path / "destination.git"
    destination.mkdir()
    git("init", "-q", "--bare", cwd=destination)
    mirror = LocalMirror(tmp_path / "mirror.git", Git())
    mirror.fetch(str(shop.bare))
    mirror.push(str(destination))
    assert refs(destination) == refs(shop.bare)

    git("update-ref", "refs/heads/extra", "refs/heads/main", cwd=destination)
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=shop.work)
    shop.publish()
    mirror.fetch(str(shop.bare))
    with pytest.raises(GitError):
        mirror.push(str(destination))
    mirror.push(str(destination), force=True)
    assert "refs/heads/extra" in refs(destination)
    mirror.push(str(destination), force=True, prune=True)
    assert refs(destination) == refs(shop.bare)
