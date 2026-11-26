"""The base class of the hosts."""

import base64
from abc import ABC, abstractmethod
from typing import ClassVar

from pygitmirror.errors import ConfigError
from pygitmirror.hosts._transport import Transport
from pygitmirror.hosts.api_client import ApiClient
from pygitmirror.hosts.repository_info import RepositoryInfo
from pygitmirror.repository_ref import RepositoryRef


class Host(ABC):
    """A server which holds git repositories, and the account used on it.

    A host answers two questions: where the git data of a repository is, and
    how to read and change the repositories themselves through the API of
    the service. A subclass implements the second for one service.

    :param url: the address of the server, such as ``https://github.com``;
        services with a public server have it as default
    :param token: the access token of the account, used for the API and for
        git over HTTP
    :param username: the user name sent with the token, for the services
        which need a specific one
    :param git_url: the address which the paths of the repositories are
        appended to for git, when it differs from ``url``, such as
        ``ssh://git@github.com``
    :param timeout: the number of seconds to wait for an answer of the API
    :param transport: the function which sends the requests to the API; the
        default uses ``urllib``
    :raises ConfigError: if no address is given and the service has no
        public server, or an address starts with a hyphen
    """

    #: The name of the service, as used in settings.
    provider: ClassVar[str]
    #: The address of the public server of the service, if it has one.
    default_url: ClassVar[str | None] = None
    #: Whether repositories can be read, created and changed through an API.
    has_api: ClassVar[bool] = True
    #: Whether a repository can be made read-only through the API.
    can_archive: ClassVar[bool] = True
    #: The user name which the service expects with a token for git.
    git_username: ClassVar[str] = "git"
    #: What follows the path of a repository in its git URL.
    git_suffix: ClassVar[str] = ".git"

    def __init__(
        self,
        *,
        url: str | None = None,
        token: str | None = None,
        username: str | None = None,
        git_url: str | None = None,
        timeout: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        url = url or self.default_url
        if not url:
            raise ConfigError(f"a {self.provider} host needs a URL")
        for address in (url, git_url or ""):
            # git would read it as an option.
            if address.startswith("-"):
                raise ConfigError(f"invalid URL {address!r}")
        self._url = url.rstrip("/")
        self._git_url = (git_url or url).rstrip("/")
        self._token = token
        self._username = username
        self._timeout = timeout
        self._transport = transport
        self._client: ApiClient | None = None

    def __repr__(self) -> str:
        # The token is left out: a representation ends up in logs.
        return f"{type(self).__name__}(url={self._url!r})"

    @property
    def url(self) -> str:
        """The address of the server, without a trailing slash."""
        return self._url

    def repository_url(self, repository: RepositoryRef) -> str:
        """Return the URL which git reads and writes a repository at.

        :param repository: the repository
        :returns: the URL, without credentials
        """
        return f"{self._git_url}/{repository.path}{self.git_suffix}"

    def git_config(self) -> dict[str, str]:
        """Return the git configuration which authenticates with the token.

        It is an HTTP header limited to the URLs of this host. It is given
        to git through its environment, so the token is neither written to
        a file nor visible in the list of processes.

        :returns: configuration keys and values; empty without a token or
            when git does not use HTTP
        """
        if not self._token or not self._git_url.startswith(("http://", "https://")):
            return {}
        user = self._username or self.git_username
        credentials = base64.b64encode(f"{user}:{self._token}".encode()).decode()
        return {f"http.{self._git_url}/.extraheader": f"Authorization: Basic {credentials}"}

    @property
    def _api(self) -> ApiClient:
        """The client of the API, created when it is first used."""
        if self._client is None:
            self._client = ApiClient(
                self._api_url(),
                self._api_headers(),
                timeout=self._timeout,
                transport=self._transport,
            )
        return self._client

    def _api_url(self) -> str:
        """Return the base URL of the API."""
        raise NotImplementedError

    def _api_headers(self) -> dict[str, str]:
        """Return the headers of every request to the API."""
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    @abstractmethod
    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        """Read the settings of a repository.

        :param repository: the repository
        :returns: its settings, or ``None`` if it does not exist or the
            account cannot see it
        :raises ApiError: if the request fails
        :raises UnsupportedError: if the host has no API
        """

    @abstractmethod
    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        """Create an empty repository.

        :param repository: the owner and the name of the new repository
        :param description: its description
        :param private: whether it is hidden from the public
        :returns: the settings of the new repository
        :raises ApiError: if the request fails, for example because the
            owner does not exist or the token may not create repositories
        :raises UnsupportedError: if the host has no API
        """

    @abstractmethod
    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        """List the repositories of an owner which the account can see.

        :param owner: the user, organization, workspace or group
        :returns: the settings of its repositories
        :raises ApiError: if the request fails
        :raises UnsupportedError: if the host has no API
        """

    @abstractmethod
    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        """Change the default branch of a repository.

        :param repository: the repository
        :param branch: the name of a branch which exists in it
        :raises ApiError: if the request fails
        :raises UnsupportedError: if the host has no API
        """

    @abstractmethod
    def archive_repository(self, repository: RepositoryRef) -> None:
        """Make a repository read-only.

        :param repository: the repository
        :raises ApiError: if the request fails
        :raises UnsupportedError: if the host cannot archive
        """
