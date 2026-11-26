"""GitHub and GitHub Enterprise Server."""

from typing import ClassVar

from pygitmirror._compat import override
from pygitmirror.hosts.github_style_host import GitHubStyleHost


class GitHubHost(GitHubStyleHost):
    """github.com, or a GitHub Enterprise Server when given its URL.

    The token is a personal access token or the token of an app. To create
    repositories it needs the ``repo`` scope, or for a fine-grained token
    the "Administration" permission with write access.
    """

    provider: ClassVar[str] = "github"
    default_url: ClassVar[str | None] = "https://github.com"
    git_username: ClassVar[str] = "x-access-token"
    _page_size: ClassVar[tuple[str, int]] = ("per_page", 100)

    @override
    def _api_url(self) -> str:
        if self.url == self.default_url:
            return "https://api.github.com"
        return f"{self.url}/api/v3"

    @override
    def _api_headers(self) -> dict[str, str]:
        return {
            **super()._api_headers(),
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @override
    def _own_repositories(self) -> tuple[str, dict[str, str | int]]:
        return "/user/repos", {"affiliation": "owner"}
