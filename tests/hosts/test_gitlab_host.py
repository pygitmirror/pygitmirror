import pytest

from pygitmirror import ApiError, GitLabHost, RepositoryInfo, RepositoryRef
from pygitmirror.hosts import ApiResponse
from tests.helpers import FakeTransport

API = "https://gitlab.example.com/api/v4"
REPO = RepositoryRef("group/sub", "name")
PROJECT = f"{API}/projects/group%2Fsub%2Fname"
DATA = {
    "path_with_namespace": "group/sub/name",
    "description": "d",
    "visibility": "internal",
    "default_branch": "main",
    "archived": False,
}
INFO = RepositoryInfo(REPO, "d", True, "main", False)


def _host(transport: FakeTransport) -> GitLabHost:
    return GitLabHost(url="https://gitlab.example.com", token="t", transport=transport)


def test_default_api() -> None:
    transport = FakeTransport({})
    assert GitLabHost(transport=transport).get_repository(REPO) is None
    assert transport.requests[0][1] == "https://gitlab.com/api/v4/projects/group%2Fsub%2Fname"


def test_get() -> None:
    transport = FakeTransport({("GET", PROJECT): DATA})
    assert _host(transport).get_repository(REPO) == INFO
    assert transport.headers["Authorization"] == "Bearer t"
    public = FakeTransport({("GET", PROJECT): {**DATA, "visibility": "public"}})
    found = _host(public).get_repository(REPO)
    assert found is not None and not found.private
    failing = FakeTransport({("GET", PROJECT): ApiResponse(500, {}, None)})
    with pytest.raises(ApiError, match="500"):
        _host(failing).get_repository(REPO)


def test_create() -> None:
    transport = FakeTransport(
        {("GET", f"{API}/namespaces/group%2Fsub"): {"id": 42}, ("POST", f"{API}/projects"): DATA}
    )
    assert _host(transport).create_repository(REPO, description="d", private=False) == INFO
    assert transport.requests[-1][2] == {
        "name": "name",
        "path": "name",
        "namespace_id": 42,
        "description": "d",
        "visibility": "public",
    }


def test_list_of_a_group_and_of_a_user() -> None:
    query = "per_page=100&with_shared=false"
    group = FakeTransport({("GET", f"{API}/groups/group%2Fsub/projects?{query}"): [DATA]})
    assert _host(group).list_repositories("group/sub") == [INFO]
    data = {**DATA, "path_with_namespace": "me/name"}
    user = FakeTransport({("GET", f"{API}/users/me/projects?per_page=100"): [data]})
    assert [info.ref.path for info in _host(user).list_repositories("me")] == ["me/name"]


def test_changes() -> None:
    transport = FakeTransport({("PUT", PROJECT): DATA, ("POST", f"{PROJECT}/archive"): DATA})
    host = _host(transport)
    host.set_default_branch(REPO, "dev")
    host.archive_repository(REPO)
    assert transport.requests == [
        ("PUT", PROJECT, {"default_branch": "dev"}),
        ("POST", f"{PROJECT}/archive", None),
    ]
