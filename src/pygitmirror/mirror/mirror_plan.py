"""The difference between the references of a source and a destination."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class MirrorPlan:
    """The branches and tags which differ between a source and a destination.

    References are named in full, such as ``refs/heads/main``.

    :param create: those which only the source has
    :param update: those which point to different objects
    :param delete: those which only the destination has
    :param unchanged: the number of those which are equal
    """

    create: tuple[str, ...] = ()
    update: tuple[str, ...] = ()
    delete: tuple[str, ...] = ()
    unchanged: int = 0

    @classmethod
    def compare(cls, source: Mapping[str, str], destination: Mapping[str, str]) -> Self:
        """Compare the references of two repositories.

        :param source: the object names of the source by reference name
        :param destination: those of the destination
        :returns: the plan which makes the destination equal to the source
        """
        shared = source.keys() & destination.keys()
        update = sorted(name for name in shared if source[name] != destination[name])
        return cls(
            create=tuple(sorted(source.keys() - destination.keys())),
            update=tuple(update),
            delete=tuple(sorted(destination.keys() - source.keys())),
            unchanged=len(shared) - len(update),
        )

    def changes(self, *, prune: bool) -> int:
        """Count the references which an operation would change.

        :param prune: whether the operation deletes what only the
            destination has
        :returns: the number of references to create, update and, with
            ``prune``, delete
        """
        return len(self.create) + len(self.update) + (len(self.delete) if prune else 0)
