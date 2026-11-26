from typing import Any

import pytest

from pygitmirror import ConfigError, GiteaHost, Operation, PlainHost
from pygitmirror.web import _forms

GITEA = {"provider": "gitea", "url": "http://localhost:47301", "token": "secret"}


def test_host() -> None:
    host = _forms.host(GITEA, "source")
    assert isinstance(host, GiteaHost) and host.git_config()
    plain = _forms.host({"provider": "plain", "url": "https://git.example.com/"}, "source")
    assert isinstance(plain, PlainHost) and plain.url == "https://git.example.com"
    gitlab = _forms.host({"provider": "gitlab", "token": "t"}, "destination")
    assert gitlab.url == "https://gitlab.com"
    ssh = _forms.host({**GITEA, "git_url": "ssh://git@localhost:47322"}, "source")
    assert ssh.git_config() == {}


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (None, "missing"),
        ({}, "provider is required"),
        ({"provider": "github", "url": "https://github.com"}, "must be one of"),
        ({"provider": "gitea"}, "url is required"),
        ({"provider": "plain", "url": "/srv/git"}, "must start with"),
        ({"provider": "plain", "url": "file:///srv/git"}, "must start with"),
        ({"provider": "plain", "url": "ext::sh -c id"}, "must start with"),
        ({"provider": "plain", "url": "https://user:pass@example.com"}, "credentials"),
        ({"provider": "plain", "url": "https://token@example.com"}, "credentials"),
        ({**GITEA, "git_url": "git://example.com"}, "git address"),
        ({**GITEA, "token": 5}, "token must be"),
        ({**GITEA, "url": "http://" + "a" * 2100}, "short text"),
    ],
)
def test_invalid_hosts(data: Any, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        _forms.host(data, "source")


def test_repositories() -> None:
    listed = _forms.repositories({"owner": " org ", "names": ["a", " b "]})
    assert [ref.path for ref in listed] == ["org/a", "org/b"]


@pytest.mark.parametrize(
    "data",
    [
        {"names": ["a"]},
        {"owner": "org"},
        {"owner": "org", "names": []},
        {"owner": "org", "names": "a"},
        {"owner": "org", "names": [1]},
        {"owner": "org", "names": ["../x"]},
        {"owner": "..", "names": ["x"]},
        {"owner": "org", "names": ["x"] * 501},
    ],
)
def test_invalid_repositories(data: dict[str, Any]) -> None:
    with pytest.raises(ConfigError):
        _forms.repositories(data)


def test_operation_and_flags() -> None:
    assert _forms.operation({"operation": "sync"}) is Operation.SYNC
    with pytest.raises(ConfigError, match="one of clone, sync, migrate"):
        _forms.operation({"operation": "delete"})
    assert _forms.flag({"x": True}, "x") and not _forms.flag({}, "x")
    with pytest.raises(ConfigError):
        _forms.flag({"x": "yes"}, "x")
