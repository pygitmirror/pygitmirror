"""Gitea and the servers which share its API."""

from typing import ClassVar

from pygitmirror._compat import override
from pygitmirror.hosts.github_style_host import GitHubStyleHost


class GiteaHost(GitHubStyleHost):
    """A Gitea server, or one with the same API such as Forgejo.

    There is no public server to default to: the URL is required. The token
    needs the ``repository`` scope with write access, and the
    ``organization`` and ``user`` scopes with read access.
    """

    provider: ClassVar[str] = "gitea"
    _page_size: ClassVar[tuple[str, int]] = ("limit", 50)

    @override
    def _api_url(self) -> str:
        return f"{self.url}/api/v1"

    @override
    def _api_headers(self) -> dict[str, str]:
        return {"Authorization": f"token {self._token}"} if self._token else {}

    @override
    def _own_repositories(self) -> tuple[str, dict[str, str | int]]:
        return "/user/repos", {}
