import json
from pathlib import Path
from typing import Any

import pytest

from pygitmirror import ConfigError, GiteaHost, GitHubHost, Operation, PlainHost
from pygitmirror.config import HostSettings, load_settings

FILE = """\
// The repositories of two organizations.
{
  "sync_path": "mirrors",
  "source": {"provider": "github", "token_env": "SOURCE_TOKEN"},
  "destination": {
    "provider": "gitea",
    "url": "https://git.example.com",
    "git_url": "ssh://git@git.example.com:2222"
  },
  "repos": {
    // Named one by one.
    "org-1": ["repo-1", "repo-2"],
    "org-2": "*"
  },
  "owners": {"org-1": "team"},
  "prune": false
}
"""


def _write(tmp_path: Path, content: str | dict[str, Any]) -> dict[str, Any]:
    path = tmp_path / "settings.json"
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return {"config": str(path)}


def test_file(tmp_path: Path) -> None:
    settings = load_settings(Operation.SYNC, _write(tmp_path, FILE))
    assert settings.operation is Operation.SYNC
    assert settings.source == HostSettings("github", token_env="SOURCE_TOKEN")
    assert settings.destination.git_url == "ssh://git@git.example.com:2222"
    assert settings.repos == {"org-1": ("repo-1", "repo-2"), "org-2": None}
    assert settings.owners == {"org-1": "team"}
    assert settings.sync_path == Path("mirrors")
    assert not settings.prune and not settings.archive_source and not settings.dry_run


def test_options_win_over_the_file(tmp_path: Path) -> None:
    options = {
        **_write(tmp_path, FILE),
        "source": "gitlab",
        "source_token_env": None,
        "destination_url": "https://other.example.com",
        "org": "org-3",
        "all": True,
        "destination_org": "elsewhere",
        "sync_path": "/var/mirrors",
        "dry_run": True,
    }
    settings = load_settings(Operation.MIGRATE, options)
    assert settings.source == HostSettings("gitlab", token_env="SOURCE_TOKEN")
    assert settings.destination.url == "https://other.example.com"
    assert settings.repos == {"org-3": None}
    assert settings.owners == {"org-1": "team", "org-3": "elsewhere"}
    assert settings.sync_path == Path("/var/mirrors")
    assert settings.dry_run


def test_options_alone() -> None:
    options = {"source_url": "/a", "destination_url": "/b", "org": "org", "repo": ["x", "y"]}
    settings = load_settings(Operation.CLONE, options)
    assert settings.source == HostSettings("plain", "/a")
    assert settings.repos == {"org": ("x", "y")}
    assert settings.sync_path == Path(".")
    assert settings.prune
    flags = load_settings(Operation.SYNC, {**options, "no_prune": True, "archive_source": True})
    assert not flags.prune and flags.archive_source


def test_the_keys_of_the_first_versions_are_read(tmp_path: Path) -> None:
    data = {"source_url": "ssh://a", "destination_url": "https://b", "repos": {"org": ["repo"]}}
    settings = load_settings(Operation.CLONE, _write(tmp_path, data))
    assert settings.source == HostSettings("plain", "ssh://a")
    assert settings.destination == HostSettings("plain", "https://b")


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({}, "no repositories"),
        ({"repos": {"org": []}}, "repos.org"),
        ({"repos": {"org": [1]}}, "repos.org"),
        ({"repos": ["org/repo"]}, "repos must be"),
        ({"repos": {"org": "*"}, "owners": {"org": 1}}, "owners.org"),
        ({"repos": {"org": "*"}, "owners": []}, "owners must be"),
        ({"repos": {"org": "*"}, "token": "secret"}, "unknown settings: token"),
        ({"repos": {"org": "*"}, "source": {"token": "secret"}}, "source must be"),
        ({"repos": {"org": "*"}, "source": {"url": 1}}, "source.url"),
        ({"repos": {"org": "*"}, "prune": "no"}, "prune"),
        ({"repos": {"org": "*"}, "sync_path": 1}, "sync_path"),
    ],
)
def test_invalid_files(tmp_path: Path, data: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_settings(Operation.SYNC, _write(tmp_path, data))


def test_unreadable_files(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cannot read"):
        load_settings(Operation.SYNC, {"config": str(tmp_path / "missing.json")})
    with pytest.raises(ConfigError, match="line 3"):
        load_settings(Operation.SYNC, _write(tmp_path, "// comment\n{\n  oops\n}"))
    with pytest.raises(ConfigError, match="must hold an object"):
        load_settings(Operation.SYNC, _write(tmp_path, "[]"))


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"org": "org"}, "name the repositories"),
        ({"org": "org", "repo": ["x"], "all": True}, "not both"),
        ({"repo": ["x"]}, "organization of the repositories is missing"),
        ({"destination_org": "x"}, "organization of the repositories is missing"),
    ],
)
def test_invalid_options(options: dict[str, Any], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_settings(Operation.SYNC, options)


def test_hosts_take_their_token_from_the_environment() -> None:
    environ = {"GIT_MIRROR_SOURCE_TOKEN": "one", "MINE": "two"}
    source = HostSettings("github").make_host("source", environ)
    assert isinstance(source, GitHubHost) and source.git_config()
    assert HostSettings("github").make_host("destination", environ).git_config() == {}
    named = HostSettings("gitea", "https://git.example.com", token_env="MINE")
    assert isinstance(named.make_host("destination", environ), GiteaHost)
    with pytest.raises(ConfigError, match="MINE"):
        named.make_host("destination", {})
    assert isinstance(HostSettings(url="/srv/git").make_host("source", {}), PlainHost)
