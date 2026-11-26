"""The base class of the hosts whose API follows that of GitHub."""

from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar

from pygitmirror._compat import override
from pygitmirror.errors import ApiError
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.repository_info import RepositoryInfo
from pygitmirror.repository_ref import RepositoryRef


class GitHubStyleHost(Host):
    """A host with the repository API of GitHub, which Gitea has adopted.

    A repository is at ``/repos/{owner}/{name}``. Organizations and users
    are different kinds of owners: a repository is created and listed below
    ``/orgs/{owner}`` for the first, and below ``/user`` or
    ``/users/{owner}`` for the second. Which one an owner is, is found by
    asking for the organization first.
    """

    #: The parameter which sets the number of items of a page, and its value.
    _page_size: ClassVar[tuple[str, int]]

    @abstractmethod
    def _own_repositories(self) -> tuple[str, dict[str, str | int]]:
        """Return the path and the parameters which list the account's own repositories."""

    def _info(self, data: Mapping[str, Any]) -> RepositoryInfo:
        """Convert a repository of the API."""
        return RepositoryInfo(
            ref=RepositoryRef.parse(data["full_name"]),
            description=data.get("description") or "",
            private=bool(data.get("private", True)),
            default_branch=data.get("default_branch") or None,
            archived=bool(data.get("archived", False)),
        )

    def _is_account(self, owner: str) -> bool:
        """Tell whether an owner is the account of the token."""
        if not self._token:
            return False
        login = self._api.request("GET", "/user").body.get("login", "")
        return str(login).lower() == owner.lower()

    @override
    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        try:
            response = self._api.request("GET", f"/repos/{repository.path}")
        except ApiError as error:
            if error.status == 404:
                return None
            raise
        return self._info(response.body)

    @override
    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        body = {"name": repository.name, "description": description, "private": private}
        try:
            response = self._api.request("POST", f"/orgs/{repository.owner}/repos", body=body)
        except ApiError as error:
            # Not an organization: the owner can only be the account itself.
            if error.status != 404 or not self._is_account(repository.owner):
                raise
            response = self._api.request("POST", "/user/repos", body=body)
        return self._info(response.body)

    @override
    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        size = dict([self._page_size])
        try:
            items = list(self._api.paginate(f"/orgs/{owner}/repos", query=size))
        except ApiError as error:
            if error.status != 404:
                raise
            if self._is_account(owner):
                # The only list which has the private repositories of a user.
                path, query = self._own_repositories()
                items = list(self._api.paginate(path, query={**query, **size}))
                items = [i for i in items if i["owner"]["login"].lower() == owner.lower()]
            else:
                items = list(self._api.paginate(f"/users/{owner}/repos", query=size))
        return [self._info(item) for item in items]

    @override
    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        self._api.request("PATCH", f"/repos/{repository.path}", body={"default_branch": branch})

    @override
    def archive_repository(self, repository: RepositoryRef) -> None:
        self._api.request("PATCH", f"/repos/{repository.path}", body={"archived": True})
