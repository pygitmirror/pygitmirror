import pytest

from pygitmirror import (
    BitbucketHost,
    ConfigError,
    RepositoryInfo,
    RepositoryRef,
    UnsupportedError,
)
from tests.helpers import FakeTransport

API = "https://api.bitbucket.org/2.0"
REPO = RepositoryRef("workspace", "name")
DATA = {
    "full_name": "workspace/name",
    "description": "d",
    "is_private": False,
    "mainbranch": {"type": "branch", "name": "main"},
}
INFO = RepositoryInfo(REPO, "d", False, "main")


def test_get() -> None:
    transport = FakeTransport({("GET", f"{API}/repositories/workspace/name"): DATA})
    host = BitbucketHost(token="t", transport=transport)
    assert host.get_repository(REPO) == INFO
    assert transport.headers["Authorization"] == "Bearer t"
    assert host.get_repository(RepositoryRef("workspace", "other")) is None


def test_an_empty_repository_has_no_default_branch() -> None:
    data = {**DATA, "mainbranch": None}
    transport = FakeTransport({("GET", f"{API}/repositories/workspace/name"): data})
    found = BitbucketHost(transport=transport).get_repository(REPO)
    assert found is not None and found.default_branch is None


def test_a_username_switches_to_basic_authentication() -> None:
    transport = FakeTransport({})
    BitbucketHost(token="t", username="me@example.com", transport=transport).get_repository(REPO)
    assert transport.headers["Authorization"].startswith("Basic ")


def test_create_and_changes() -> None:
    url = f"{API}/repositories/workspace/name"
    transport = FakeTransport({("POST", url): DATA, ("PUT", url): DATA})
    host = BitbucketHost(token="t", transport=transport)
    assert host.create_repository(REPO, description="d", private=False) == INFO
    host.set_default_branch(REPO, "dev")
    assert transport.requests == [
        ("POST", url, {"scm": "git", "is_private": False, "description": "d"}),
        ("PUT", url, {"mainbranch": {"type": "branch", "name": "dev"}}),
    ]
    assert not host.can_archive
    with pytest.raises(UnsupportedError):
        host.archive_repository(REPO)


def test_list() -> None:
    first = f"{API}/repositories/workspace?pagelen=100"
    transport = FakeTransport(
        {
            ("GET", first): {"values": [DATA], "next": f"{first}&page=2"},
            ("GET", f"{first}&page=2"): {"values": [{**DATA, "full_name": "workspace/two"}]},
        }
    )
    listed = BitbucketHost(transport=transport).list_repositories("workspace")
    assert [info.ref.name for info in listed] == ["name", "two"]


def test_data_center_is_not_supported() -> None:
    host = BitbucketHost(url="https://bitbucket.example.com")
    with pytest.raises(ConfigError, match="Bitbucket Cloud"):
        host.get_repository(REPO)
