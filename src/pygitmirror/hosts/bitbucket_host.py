"""Bitbucket Cloud."""

import base64
from collections.abc import Mapping
from typing import Any, ClassVar

from pygitmirror._compat import override
from pygitmirror.errors import ApiError, ConfigError, UnsupportedError
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.repository_info import RepositoryInfo
from pygitmirror.repository_ref import RepositoryRef


class BitbucketHost(Host):
    """bitbucket.org.

    The owner of a repository is a workspace, and its name is its slug. With
    a workspace, project or repository access token, give the token only.
    With an API token or an app password of a user, give the ``username``
    which Bitbucket documents for it as well.

    Bitbucket Data Center has another API and is not supported; use a plain
    host for it. Bitbucket cannot archive a repository.

    :raises ConfigError: if a URL other than that of Bitbucket Cloud is given
    """

    provider: ClassVar[str] = "bitbucket"
    default_url: ClassVar[str | None] = "https://bitbucket.org"
    can_archive: ClassVar[bool] = False
    git_username: ClassVar[str] = "x-token-auth"

    @override
    def _api_url(self) -> str:
        if self.url != self.default_url:
            raise ConfigError(
                f"only Bitbucket Cloud at {self.default_url} has a supported API, not {self.url}"
            )
        return "https://api.bitbucket.org/2.0"

    @override
    def _api_headers(self) -> dict[str, str]:
        if self._token and self._username:
            credentials = base64.b64encode(f"{self._username}:{self._token}".encode()).decode()
            return {"Authorization": f"Basic {credentials}"}
        return super()._api_headers()

    def _info(self, data: Mapping[str, Any]) -> RepositoryInfo:
        """Convert a repository of the API."""
        return RepositoryInfo(
            ref=RepositoryRef.parse(data["full_name"]),
            description=data.get("description") or "",
            private=bool(data.get("is_private", True)),
            default_branch=(data.get("mainbranch") or {}).get("name") or None,
        )

    @override
    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        try:
            response = self._api.request("GET", f"/repositories/{repository.path}")
        except ApiError as error:
            if error.status == 404:
                return None
            raise
        return self._info(response.body)

    @override
    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        body = {"scm": "git", "is_private": private, "description": description}
        response = self._api.request("POST", f"/repositories/{repository.path}", body=body)
        return self._info(response.body)

    @override
    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        items = self._api.paginate(
            f"/repositories/{owner}", query={"pagelen": 100}, values_key="values"
        )
        return [self._info(item) for item in items]

    @override
    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        body = {"mainbranch": {"type": "branch", "name": branch}}
        self._api.request("PUT", f"/repositories/{repository.path}", body=body)

    @override
    def archive_repository(self, repository: RepositoryRef) -> None:
        raise UnsupportedError("Bitbucket cannot archive a repository")
