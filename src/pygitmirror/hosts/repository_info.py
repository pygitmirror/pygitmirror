"""What a host knows about a repository."""

from dataclasses import dataclass

from pygitmirror.repository_ref import RepositoryRef


@dataclass(frozen=True)
class RepositoryInfo:
    """The settings of a repository which are carried from one host to another.

    :param ref: the owner and the name, as the host spells them
    :param description: the description, empty when there is none
    :param private: whether the repository is hidden from the public; a
        visibility between the two, such as "internal" on GitLab, counts as
        private
    :param default_branch: the name of the default branch, or ``None`` for an
        empty repository
    :param archived: whether the repository is read-only
    """

    ref: RepositoryRef
    description: str = ""
    private: bool = True
    default_branch: str | None = None
    archived: bool = False
