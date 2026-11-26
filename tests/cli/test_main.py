import json
import logging
from pathlib import Path

import pytest

import pygitmirror
from pygitmirror.cli import main
from tests.helpers import Workshop, git, refs


@pytest.fixture
def folders(tmp_path: Path) -> tuple[Workshop, Path, list[str]]:
    """A source repository, an empty destination and the options which name them."""
    shop = Workshop(tmp_path, tmp_path / "source" / "org" / "repo")
    destination = tmp_path / "destination" / "org" / "repo"
    destination.mkdir(parents=True)
    git("init", "-q", "--bare", cwd=destination)
    options = [
        "--source-url", str(tmp_path / "source"),
        "--destination-url", str(tmp_path / "destination"),
        "--sync-path", str(tmp_path / "mirrors"),
    ]  # fmt: skip
    return shop, destination, options


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--version"])
    assert raised.value.code == 0
    assert capsys.readouterr().out.strip() == f"git-mirror {pygitmirror.__version__}"


def test_a_command_is_needed() -> None:
    with pytest.raises(SystemExit) as raised:
        main([])
    assert raised.value.code == 2


def test_sync(folders: tuple[Workshop, Path, list[str]], caplog: pytest.LogCaptureFixture) -> None:
    shop, destination, options = folders
    caplog.set_level(logging.INFO, logger="pygitmirror")
    assert main(["sync", *options, "--org", "org", "--repo", "repo"]) == 0
    assert refs(destination) == refs(shop.bare)
    assert "sync org/repo -> org/repo: 1 created, 0 updated" in caplog.text
    assert "0 of 1 repositories failed" in caplog.text


def test_dry_run(folders: tuple[Workshop, Path, list[str]]) -> None:
    _, destination, options = folders
    assert main(["migrate", *options, "--org", "org", "--repo", "repo", "--dry-run"]) == 0
    assert refs(destination) == {}


def test_the_options_of_the_first_versions_clone(
    folders: tuple[Workshop, Path, list[str]], tmp_path: Path
) -> None:
    shop, destination, _ = folders
    options = [
        "--source_url", str(tmp_path / "source"),
        "--destination_url", str(tmp_path / "destination"),
        "--sync_path", str(tmp_path / "mirrors"),
        "--org", "org", "--repo", "repo",
    ]  # fmt: skip
    assert main(options) == 0
    assert refs(destination) == refs(shop.bare)
    # A clone does not overwrite.
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=shop.work)
    shop.publish()
    assert main(options) == 1
    assert refs(destination) != refs(shop.bare)


def test_settings_file_and_failures(
    folders: tuple[Workshop, Path, list[str]], tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    shop, destination, _ = folders
    caplog.set_level(logging.INFO, logger="pygitmirror")
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "sync_path": str(tmp_path / "mirrors"),
                "source_url": str(tmp_path / "source"),
                "destination_url": str(tmp_path / "destination"),
                "repos": {"org": ["missing", "repo"]},
            }
        )
    )
    assert main(["sync", "--json", str(settings)]) == 1
    assert refs(destination) == refs(shop.bare)
    assert "1 of 2 repositories failed" in caplog.text


def test_invalid_settings(caplog: pytest.LogCaptureFixture) -> None:
    assert main(["sync", "--org", "org"]) == 2
    assert "name the repositories" in caplog.text
    # A plain server cannot list the repositories of an owner.
    assert (
        main(["sync", "--source-url", "/a", "--destination-url", "/b", "--org", "o", "--all"]) == 2
    )
    assert main(["sync", "--source", "gitea", "--org", "o", "--repo", "r"]) == 2
    assert "needs a URL" in caplog.text


def test_options_of_other_commands_are_rejected() -> None:
    with pytest.raises(SystemExit):
        main(["clone", "--no-prune", "--org", "o", "--repo", "r"])
    with pytest.raises(SystemExit):
        main(["sync", "--archive-source", "--org", "o", "--repo", "r"])
