import base64

import pytest

from pygitmirror import (
    PROVIDERS,
    ConfigError,
    GitHubHost,
    PlainHost,
    RepositoryRef,
    UnsupportedError,
    make_host,
)

REPO = RepositoryRef("owner", "name")


def test_make_host() -> None:
    assert set(PROVIDERS) == {"plain", "github", "gitlab", "gitea", "bitbucket"}
    assert isinstance(make_host("GitHub"), GitHubHost)
    with pytest.raises(ConfigError, match="unknown provider"):
        make_host("sourceforge")
    with pytest.raises(ConfigError, match="needs a URL"):
        make_host("gitea")
    with pytest.raises(ConfigError):
        make_host("plain", url="--upload-pack=x")


@pytest.mark.parametrize(
    ("provider", "url"),
    [
        ("github", "https://github.com/owner/name.git"),
        ("gitlab", "https://gitlab.com/owner/name.git"),
        ("bitbucket", "https://bitbucket.org/owner/name.git"),
    ],
)
def test_repository_url(provider: str, url: str) -> None:
    assert make_host(provider).repository_url(REPO) == url


def test_git_url_replaces_the_url_for_git() -> None:
    host = make_host("gitea", url="https://git.example.com/", git_url="ssh://git@example.com:2222")
    assert host.url == "https://git.example.com"
    assert host.repository_url(REPO) == "ssh://git@example.com:2222/owner/name.git"
    # A token is not sent over SSH.
    assert make_host("github", token="t", git_url="ssh://git@github.com").git_config() == {}


@pytest.mark.parametrize(
    ("provider", "user"),
    [("github", "x-access-token"), ("gitlab", "oauth2"), ("bitbucket", "x-token-auth")],
)
def test_git_config_authenticates_with_the_token(provider: str, user: str) -> None:
    host = make_host(provider, token="secret")
    ((key, value),) = host.git_config().items()
    assert key == f"http.{host.url}/.extraheader"
    assert value == "Authorization: Basic " + base64.b64encode(f"{user}:secret".encode()).decode()
    assert make_host(provider).git_config() == {}
    assert "secret" not in repr(host)


def test_username_replaces_the_default() -> None:
    (value,) = make_host("bitbucket", token="s", username="me").git_config().values()
    assert base64.b64decode(value.split()[-1]) == b"me:s"


def test_plain_host() -> None:
    host = PlainHost(url="ssh://git@example.com:7999/")
    assert host.repository_url(REPO) == "ssh://git@example.com:7999/owner/name"
    assert not host.has_api
    for call in (
        lambda: host.get_repository(REPO),
        lambda: host.create_repository(REPO),
        lambda: host.list_repositories("owner"),
        lambda: host.set_default_branch(REPO, "main"),
        lambda: host.archive_repository(REPO),
    ):
        with pytest.raises(UnsupportedError):
            call()
