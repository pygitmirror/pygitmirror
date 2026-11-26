from typing import Any

import pytest

from pygitmirror import ApiError, Host, RepositoryInfo, RepositoryRef, make_host
from pygitmirror.hosts import ApiResponse
from tests.helpers import FakeTransport

REPO = RepositoryRef("owner", "name")
DATA = {
    "full_name": "owner/name",
    "description": None,
    "private": False,
    "default_branch": "main",
    "archived": True,
    "owner": {"login": "owner"},
}
INFO = RepositoryInfo(REPO, "", False, "main", True)

#: The provider, the base URL of its API and the parameter of its page size.
CASES = [
    ("github", None, "https://api.github.com", "per_page=100"),
    ("github", "https://ghe.example.com", "https://ghe.example.com/api/v3", "per_page=100"),
    ("gitea", "https://git.example.com", "https://git.example.com/api/v1", "limit=50"),
]


def _host(provider: str, url: str | None, answers: dict[tuple[str, str], Any]) -> Any:
    transport = FakeTransport(answers)
    return make_host(provider, url=url, token="t", transport=transport), transport


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_get(provider: str, url: str | None, api: str, size: str) -> None:
    host, transport = _host(provider, url, {("GET", f"{api}/repos/owner/name"): DATA})
    assert host.get_repository(REPO) == INFO
    assert host.get_repository(RepositoryRef("owner", "other")) is None
    expected = "token t" if provider == "gitea" else "Bearer t"
    assert transport.headers["Authorization"] == expected


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_get_reports_other_errors(provider: str, url: str | None, api: str, size: str) -> None:
    answers = {("GET", f"{api}/repos/owner/name"): ApiResponse(401, {}, {"message": "Bad"})}
    host, _ = _host(provider, url, answers)
    with pytest.raises(ApiError, match="401"):
        host.get_repository(REPO)


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_create_in_an_organization(provider: str, url: str | None, api: str, size: str) -> None:
    host, transport = _host(provider, url, {("POST", f"{api}/orgs/owner/repos"): DATA})
    assert host.create_repository(REPO, description="d", private=False) == INFO
    body = {"name": "name", "description": "d", "private": False}
    assert transport.requests == [("POST", f"{api}/orgs/owner/repos", body)]


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_create_for_the_account(provider: str, url: str | None, api: str, size: str) -> None:
    answers = {("GET", f"{api}/user"): {"login": "Owner"}, ("POST", f"{api}/user/repos"): DATA}
    host, transport = _host(provider, url, answers)
    assert host.create_repository(REPO) == INFO
    assert transport.requests[-1][2]["private"] is True


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_create_for_someone_else_fails(provider: str, url: str | None, api: str, size: str) -> None:
    host, transport = _host(provider, url, {("GET", f"{api}/user"): {"login": "me"}})
    with pytest.raises(ApiError, match="404"):
        host.create_repository(REPO)
    assert all(method != "POST" or "/orgs/" in url for method, url, _ in transport.requests)


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_list_of_an_organization(provider: str, url: str | None, api: str, size: str) -> None:
    host, _ = _host(provider, url, {("GET", f"{api}/orgs/owner/repos?{size}"): [DATA]})
    assert host.list_repositories("owner") == [INFO]


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_list_of_the_account(provider: str, url: str | None, api: str, size: str) -> None:
    own = "affiliation=owner&" if provider == "github" else ""
    other = {**DATA, "full_name": "org/shared", "owner": {"login": "org"}}
    answers = {
        ("GET", f"{api}/user"): {"login": "owner"},
        ("GET", f"{api}/user/repos?{own}{size}"): [DATA, other],
    }
    host, _ = _host(provider, url, answers)
    assert host.list_repositories("owner") == [INFO]


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_list_of_another_user(provider: str, url: str | None, api: str, size: str) -> None:
    answers = {
        ("GET", f"{api}/user"): {"login": "me"},
        ("GET", f"{api}/users/owner/repos?{size}"): [DATA],
    }
    host, _ = _host(provider, url, answers)
    assert host.list_repositories("owner") == [INFO]


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_list_without_a_token(provider: str, url: str | None, api: str, size: str) -> None:
    transport = FakeTransport({("GET", f"{api}/users/owner/repos?{size}"): [DATA]})
    host = make_host(provider, url=url, transport=transport)
    assert host.list_repositories("owner") == [INFO]
    assert "Authorization" not in transport.headers
    assert ("GET", f"{api}/user", None) not in transport.requests


@pytest.mark.parametrize(("provider", "url", "api", "size"), CASES)
def test_changes(provider: str, url: str | None, api: str, size: str) -> None:
    host: Host
    host, transport = _host(provider, url, {("PATCH", f"{api}/repos/owner/name"): DATA})
    host.set_default_branch(REPO, "dev")
    host.archive_repository(REPO)
    assert [body for _, _, body in transport.requests] == [
        {"default_branch": "dev"},
        {"archived": True},
    ]
