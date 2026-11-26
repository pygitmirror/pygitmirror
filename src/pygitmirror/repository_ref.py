"""The name of a repository on a host."""

import re
from dataclasses import dataclass
from typing import Self

from pygitmirror.errors import ConfigError

#: One segment of a repository path. It is used in URLs and in the path of
#: the local mirror, so nothing which could leave either is allowed.
_SEGMENT = re.compile(r"(?!-)[A-Za-z0-9_.~-]+")


@dataclass(frozen=True)
class RepositoryRef:
    """The owner and the name which identify a repository on a host.

    The owner is a user or an organization on GitHub and Gitea, a workspace
    on Bitbucket and a group on GitLab, where it may have several segments,
    such as ``group/subgroup``.

    :param owner: the user, organization, workspace or group
    :param name: the name of the repository, without ``.git``
    :raises ConfigError: if a segment is empty, is ``.`` or ``..``, starts
        with a hyphen or has a character other than letters, digits and
        ``_ . ~ -``
    """

    owner: str
    name: str

    def __post_init__(self) -> None:
        segments = [*self.owner.split("/"), self.name]
        for segment in segments:
            if not _SEGMENT.fullmatch(segment) or segment in (".", ".."):
                raise ConfigError(f"invalid repository name {self.owner}/{self.name}")

    @classmethod
    def parse(cls, path: str) -> Self:
        """Create a reference from a path such as ``owner/name``.

        :param path: the owner and the name separated by a slash; a trailing
            ``.git`` is dropped
        :returns: the reference
        :raises ConfigError: if the path has no owner or is invalid
        """
        owner, slash, name = path.strip("/").removesuffix(".git").rpartition("/")
        if not slash:
            raise ConfigError(f"expected owner/name, not {path!r}")
        return cls(owner, name)

    @property
    def path(self) -> str:
        """The owner and the name separated by a slash."""
        return f"{self.owner}/{self.name}"

    def __str__(self) -> str:
        return self.path
