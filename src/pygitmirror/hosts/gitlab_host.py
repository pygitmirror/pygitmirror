"""GitLab."""

from collections.abc import Mapping
from typing import Any, ClassVar
from urllib.parse import quote

from pygitmirror._compat import override
from pygitmirror.errors import ApiError
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.repository_info import RepositoryInfo
from pygitmirror.repository_ref import RepositoryRef


def _id(path: str) -> str:
    """Encode a path for use as the identifier of a project or a group."""
    return quote(path, safe="")


class GitLabHost(Host):
    """gitlab.com, or a GitLab server when given its URL.

    A repository is a project, and its owner is a group, which may be
    nested (``group/subgroup``), or a user. The token is a personal, group
    or project access token with the ``api`` scope.
    """

    provider: ClassVar[str] = "gitlab"
    default_url: ClassVar[str | None] = "https://gitlab.com"
    git_username: ClassVar[str] = "oauth2"

    @override
    def _api_url(self) -> str:
        return f"{self.url}/api/v4"

    def _info(self, data: Mapping[str, Any]) -> RepositoryInfo:
        """Convert a project of the API."""
        return RepositoryInfo(
            ref=RepositoryRef.parse(data["path_with_namespace"]),
            description=data.get("description") or "",
            # "internal" is visible to every user of the server, not to the public.
            private=data.get("visibility", "private") != "public",
            default_branch=data.get("default_branch") or None,
            archived=bool(data.get("archived", False)),
        )

    @override
    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        try:
            response = self._api.request("GET", f"/projects/{_id(repository.path)}")
        except ApiError as error:
            if error.status == 404:
                return None
            raise
        return self._info(response.body)

    @override
    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        # Groups and users are both namespaces, which a project is created in.
        namespace = self._api.request("GET", f"/namespaces/{_id(repository.owner)}").body
        body = {
            "name": repository.name,
            "path": repository.name,
            "namespace_id": namespace["id"],
            "description": description,
            "visibility": "private" if private else "public",
        }
        return self._info(self._api.request("POST", "/projects", body=body).body)

    @override
    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        try:
            items = list(
                self._api.paginate(
                    f"/groups/{_id(owner)}/projects",
                    # Without the projects of subgroups and those shared with
                    # the group, which have other owners.
                    query={"per_page": 100, "with_shared": "false"},
                )
            )
        except ApiError as error:
            if error.status != 404:
                raise
            items = list(
                self._api.paginate(f"/users/{_id(owner)}/projects", query={"per_page": 100})
            )
        return [self._info(item) for item in items]

    @override
    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        self._api.request(
            "PUT", f"/projects/{_id(repository.path)}", body={"default_branch": branch}
        )

    @override
    def archive_repository(self, repository: RepositoryRef) -> None:
        self._api.request("POST", f"/projects/{_id(repository.path)}/archive")
