from pathlib import Path

import pytest

from pygitmirror import Git, GitError
from pygitmirror.git import default_branch, list_refs
from pygitmirror.git._redact import redact
from tests.helpers import Workshop, git


def test_redact() -> None:
    assert redact("git fetch https://user:secret@example.com/a/b") == (
        "git fetch https://***@example.com/a/b"
    )
    assert redact("ssh://git@example.com/a/b") == "ssh://git@example.com/a/b"


def test_run_returns_output() -> None:
    assert Git().run("--version").startswith("git version")


def test_failure_is_reported_without_credentials(tmp_path: Path) -> None:
    with pytest.raises(GitError) as raised:
        Git().run("ls-remote", "https://user:secret@invalid.invalid/a/b", cwd=tmp_path)
    assert "secret" not in str(raised.value)
    assert raised.value.returncode not in (0, None)


def test_missing_executable() -> None:
    with pytest.raises(GitError) as raised:
        Git("git-which-does-not-exist").run("--version")
    assert raised.value.returncode is None


def test_config_reaches_git_through_the_environment(tmp_path: Path) -> None:
    git("init", "-q", cwd=tmp_path)
    output = Git().run("config", "--get", "test.key", cwd=tmp_path, config={"test.key": "value"})
    assert output.strip() == "value"


def test_status(tmp_path: Path) -> None:
    git("init", "-q", cwd=tmp_path)
    assert Git().status("rev-parse", "--git-dir", cwd=tmp_path) == 0
    assert Git().status("rev-parse", "--verify", "-q", "missing", cwd=tmp_path) != 0


def test_protocols_can_be_restricted(tmp_path: Path) -> None:
    shop = Workshop(tmp_path, tmp_path / "bare")
    assert list_refs(Git(), str(shop.bare))
    with pytest.raises(GitError):
        list_refs(Git(allowed_protocols=("https", "ssh")), str(shop.bare))
    with pytest.raises(GitError):
        list_refs(Git(), "ext::sh -c 'echo unsafe >&2'")


def test_list_refs_and_default_branch(tmp_path: Path) -> None:
    shop = Workshop(tmp_path, tmp_path / "bare")
    git("tag", "-a", "v1", "-m", "annotated", cwd=shop.work)
    main = shop.commit("second")
    listed = list_refs(Git(), str(shop.bare))
    assert listed["refs/heads/main"] == main
    assert set(listed) == {"refs/heads/main", "refs/tags/v1"}
    assert default_branch(Git(), str(shop.bare)) == "main"


def test_empty_repository(tmp_path: Path) -> None:
    git("init", "-q", "--bare", cwd=tmp_path)
    assert list_refs(Git(), str(tmp_path)) == {}
