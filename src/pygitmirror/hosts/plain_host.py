"""A git server without an API."""

from typing import ClassVar, NoReturn

from pygitmirror._compat import override
from pygitmirror.errors import UnsupportedError
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.repository_info import RepositoryInfo
from pygitmirror.repository_ref import RepositoryRef


class PlainHost(Host):
    """Any git server, reached through git only.

    The URL of a repository is the address of the server followed by the
    owner and the name, with nothing added: ``ssh://git@example.com/owner/name``.
    The address may also be a local folder.

    Repositories cannot be created, listed or changed, so the destination
    of an operation must exist already.
    """

    provider: ClassVar[str] = "plain"
    has_api: ClassVar[bool] = False
    can_archive: ClassVar[bool] = False
    git_suffix: ClassVar[str] = ""

    def _unsupported(self, action: str) -> NoReturn:
        raise UnsupportedError(
            f"{self.url} is a plain git server, which cannot {action}; "
            "name its service to use the API"
        )

    @override
    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        self._unsupported("read the settings of a repository")

    @override
    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        self._unsupported("create a repository")

    @override
    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        self._unsupported("list repositories")

    @override
    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        self._unsupported("change the default branch")

    @override
    def archive_repository(self, repository: RepositoryRef) -> None:
        self._unsupported("archive a repository")
