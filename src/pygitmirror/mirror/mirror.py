"""Copying repositories from one host to another."""

import logging
import tempfile
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from pygitmirror.errors import GitMirrorError
from pygitmirror.git import Git, LocalMirror
from pygitmirror.hosts import Host
from pygitmirror.mirror._transfer import Endpoint, transfer
from pygitmirror.mirror.mirror_result import MirrorResult
from pygitmirror.mirror.operation import Operation
from pygitmirror.repository_ref import RepositoryRef

_logger = logging.getLogger(__name__)


def _ref(repository: RepositoryRef | str) -> RepositoryRef:
    """Accept a repository as a reference or as ``owner/name``."""
    return RepositoryRef.parse(repository) if isinstance(repository, str) else repository


class Mirror:
    """Clone, sync and migrate repositories from a source to a destination.

    Every method takes the repository at the source, as a
    :class:`~pygitmirror.repository_ref.RepositoryRef` or as ``owner/name``.
    It goes to the repository of the same name at the destination, below
    the owner which ``owners`` maps its owner to, unless ``to`` names
    another one.

    An object holds no state between calls and changes nothing outside
    ``workdir``, so one process may use several at once.

    :param source: the host to read from
    :param destination: the host to write to
    :param workdir: the folder of the local mirrors, one per repository in
        ``owner/name.git``. Keeping it makes the next run download only what
        is new. Without it a temporary folder is used and removed.
    :param owners: owners at the destination by owner at the source, for
        the owners which are not named the same
    :param git: the runner of git commands
    """

    def __init__(
        self,
        source: Host,
        destination: Host,
        *,
        workdir: Path | str | None = None,
        owners: Mapping[str, str] | None = None,
        git: Git | None = None,
    ) -> None:
        self._source = source
        self._destination = destination
        self._workdir = Path(workdir).expanduser() if workdir is not None else None
        self._owners = dict(owners or {})
        self._git = git or Git()

    def destination_of(self, repository: RepositoryRef | str) -> RepositoryRef:
        """Return the repository at the destination which one of the source goes to.

        :param repository: the repository at the source
        :returns: the repository of the same name below the mapped owner
        """
        source = _ref(repository)
        return RepositoryRef(self._owners.get(source.owner, source.owner), source.name)

    def repositories(self, owner: str) -> list[RepositoryRef]:
        """List the repositories of an owner at the source.

        :param owner: the user, organization, workspace or group
        :returns: its repositories, sorted by name
        :raises UnsupportedError: if the source has no API
        :raises ApiError: if the request fails
        """
        return sorted(
            (info.ref for info in self._source.list_repositories(owner)), key=lambda ref: ref.path
        )

    def clone(
        self,
        repository: RepositoryRef | str,
        *,
        to: RepositoryRef | str | None = None,
        dry_run: bool = False,
    ) -> MirrorResult:
        """Copy the branches and tags which the destination does not have.

        Branches which the destination has are moved forward when the source
        is ahead of them. Nothing at the destination is overwritten or
        deleted.

        :param repository: the repository at the source
        :param to: the repository at the destination, if not the default
        :param dry_run: report what would be done without changing anything
        :returns: what was done
        :raises DivergedError: if a branch or tag of the destination has
            something which the source does not have
        :raises GitMirrorError: if a git command or a request fails
        """
        return self._mirror(Operation.CLONE, repository, to, dry_run=dry_run)

    def sync(
        self,
        repository: RepositoryRef | str,
        *,
        to: RepositoryRef | str | None = None,
        prune: bool = True,
        dry_run: bool = False,
    ) -> MirrorResult:
        """Make the branches and tags of the destination equal to those of the source.

        Branches and tags which differ are overwritten: commits which only
        the destination has are lost.

        :param repository: the repository at the source
        :param to: the repository at the destination, if not the default
        :param prune: delete the branches and tags which the source does
            not have
        :param dry_run: report what would be done without changing anything
        :returns: what was done
        :raises EmptySourceError: if the source has no branches or tags and
            ``prune`` would delete all of the destination
        :raises GitMirrorError: if a git command or a request fails
        """
        return self._mirror(Operation.SYNC, repository, to, prune=prune, dry_run=dry_run)

    def migrate(
        self,
        repository: RepositoryRef | str,
        *,
        to: RepositoryRef | str | None = None,
        archive_source: bool = False,
        dry_run: bool = False,
    ) -> MirrorResult:
        """Move a repository: clone it, check the copy and retire the source.

        :param repository: the repository at the source
        :param to: the repository at the destination, if not the default
        :param archive_source: make the source read-only once the copy is
            checked
        :param dry_run: report what would be done without changing anything
        :returns: what was done
        :raises DivergedError: as :meth:`clone`
        :raises VerificationError: if the destination has other branches
            and tags than the source
        :raises UnsupportedError: if the source cannot be archived
        :raises GitMirrorError: if a git command or a request fails
        """
        return self._mirror(
            Operation.MIGRATE, repository, to, archive_source=archive_source, dry_run=dry_run
        )

    def run(
        self,
        operation: Operation,
        repositories: Iterable[RepositoryRef | str],
        *,
        prune: bool = True,
        archive_source: bool = False,
        dry_run: bool = False,
    ) -> Iterator[MirrorResult]:
        """Apply an operation to several repositories, one after the other.

        A repository which fails does not stop the others: its result has
        the error.

        :param operation: the operation
        :param repositories: the repositories at the source
        :param prune: as for :meth:`sync`
        :param archive_source: as for :meth:`migrate`
        :param dry_run: report what would be done without changing anything
        :returns: the result of each repository, as soon as it is finished
        :raises ConfigError: if a name is invalid, before anything is done
        """
        for source in [_ref(repository) for repository in repositories]:
            try:
                yield self._mirror(
                    operation,
                    source,
                    None,
                    prune=prune,
                    archive_source=archive_source,
                    dry_run=dry_run,
                )
            except GitMirrorError as error:
                _logger.debug("%s of %s failed", operation, source, exc_info=True)
                yield MirrorResult(operation, source, self.destination_of(source), error=error)

    @contextmanager
    def _local_mirror(self, repository: RepositoryRef) -> Iterator[LocalMirror]:
        """Give the local mirror of a repository, temporary without a work folder."""
        if self._workdir is not None:
            yield LocalMirror(
                self._workdir / repository.owner / f"{repository.name}.git", self._git
            )
            return
        with tempfile.TemporaryDirectory(
            prefix="git-mirror-", ignore_cleanup_errors=True
        ) as folder:
            yield LocalMirror(Path(folder) / f"{repository.name}.git", self._git)

    def _mirror(
        self,
        operation: Operation,
        repository: RepositoryRef | str,
        to: RepositoryRef | str | None,
        *,
        prune: bool = False,
        archive_source: bool = False,
        dry_run: bool = False,
    ) -> MirrorResult:
        """Run one operation on one repository."""
        source = _ref(repository)
        destination = _ref(to) if to is not None else self.destination_of(source)
        return transfer(
            operation,
            Endpoint(self._source, source),
            Endpoint(self._destination, destination),
            self._git,
            lambda: self._local_mirror(source),
            prune=prune,
            archive_source=archive_source,
            dry_run=dry_run,
        )
