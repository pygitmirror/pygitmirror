"""The settings of one host."""

from collections.abc import Mapping
from dataclasses import dataclass

from pygitmirror.errors import ConfigError
from pygitmirror.hosts import Host, make_host


@dataclass(frozen=True)
class HostSettings:
    """What a settings file or the command line says about a host.

    The token is not among the settings: they name the environment variable
    which holds it, so that it is neither stored in a file nor shown in the
    list of processes.

    :param provider: the name of the service, ``plain`` for a git server
        without an API
    :param url: the address of the server
    :param git_url: the address for git, when it differs
    :param username: the user name sent with the token
    :param token_env: the name of the environment variable of the token;
        ``GIT_MIRROR_SOURCE_TOKEN`` or ``GIT_MIRROR_DESTINATION_TOKEN`` when
        not given
    """

    provider: str = "plain"
    url: str | None = None
    git_url: str | None = None
    username: str | None = None
    token_env: str | None = None

    def make_host(self, role: str, environ: Mapping[str, str]) -> Host:
        """Create the host, with its token from the environment.

        :param role: ``source`` or ``destination``
        :param environ: the environment variables
        :returns: the host
        :raises ConfigError: if the named variable is not set, or a setting
            is invalid
        """
        token = environ.get(self.token_env or f"GIT_MIRROR_{role.upper()}_TOKEN")
        if self.token_env and not token:
            raise ConfigError(
                f"the environment variable {self.token_env} of the {role} token is not set"
            )
        return make_host(
            self.provider,
            url=self.url,
            git_url=self.git_url,
            username=self.username,
            token=token or None,
        )
