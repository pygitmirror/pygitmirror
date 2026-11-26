"""Creating a host from the name of its service."""

from typing import Any

from pygitmirror.errors import ConfigError
from pygitmirror.hosts.bitbucket_host import BitbucketHost
from pygitmirror.hosts.gitea_host import GiteaHost
from pygitmirror.hosts.github_host import GitHubHost
from pygitmirror.hosts.gitlab_host import GitLabHost
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.plain_host import PlainHost

#: The host classes by the name of their service.
PROVIDERS: dict[str, type[Host]] = {
    cls.provider: cls for cls in (PlainHost, GitHubHost, GitLabHost, GiteaHost, BitbucketHost)
}


def make_host(provider: str, **options: Any) -> Host:
    """Create the host of a service.

    :param provider: ``github``, ``gitlab``, ``gitea``, ``bitbucket``, or
        ``plain`` for a git server without an API
    :param options: the arguments of :class:`~pygitmirror.hosts.host.Host`
    :returns: the host
    :raises ConfigError: if the service is unknown or an argument is invalid
    """
    try:
        cls = PROVIDERS[provider.lower()]
    except KeyError:
        known = ", ".join(sorted(PROVIDERS))
        raise ConfigError(f"unknown provider {provider!r}; expected one of {known}") from None
    return cls(**options)
