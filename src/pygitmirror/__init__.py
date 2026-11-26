"""Clone, sync and migrate git repositories between hosts.

The package copies the branches and tags of repositories from one host to
another: GitHub, GitLab, Gitea, Bitbucket or any git server.

.. code-block:: python

    from pygitmirror import Mirror, make_host

    source = make_host("github", token="...")
    destination = make_host("gitea", url="https://git.example.com", token="...")
    mirror = Mirror(source, destination, workdir="~/.cache/git-mirror")
    result = mirror.sync("owner/name")
"""

from importlib.metadata import PackageNotFoundError, version

from pygitmirror.errors import (
    ApiError,
    ConfigError,
    DivergedError,
    EmptySourceError,
    GitError,
    GitMirrorError,
    UnsupportedError,
    VerificationError,
)
from pygitmirror.git import Git, LocalMirror
from pygitmirror.hosts import (
    PROVIDERS,
    BitbucketHost,
    GiteaHost,
    GitHubHost,
    GitLabHost,
    Host,
    PlainHost,
    RepositoryInfo,
    make_host,
)
from pygitmirror.mirror import Mirror, MirrorPlan, MirrorResult, Operation
from pygitmirror.repository_ref import RepositoryRef

try:
    __version__ = version("pygitmirror")
except PackageNotFoundError:  # pragma: no cover - a source tree which is not installed
    __version__ = "0+unknown"

__all__ = [
    "PROVIDERS",
    "ApiError",
    "BitbucketHost",
    "ConfigError",
    "DivergedError",
    "EmptySourceError",
    "Git",
    "GitError",
    "GitHubHost",
    "GitLabHost",
    "GitMirrorError",
    "GiteaHost",
    "Host",
    "LocalMirror",
    "Mirror",
    "MirrorPlan",
    "MirrorResult",
    "Operation",
    "PlainHost",
    "RepositoryInfo",
    "RepositoryRef",
    "UnsupportedError",
    "VerificationError",
    "__version__",
    "make_host",
]
