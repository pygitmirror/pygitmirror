"""The steps of an operation on one repository."""

import logging
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import NamedTuple

from pygitmirror.errors import (
    ConfigError,
    DivergedError,
    EmptySourceError,
    UnsupportedError,
    VerificationError,
)
from pygitmirror.git import Git, LocalMirror, default_branch, list_refs
from pygitmirror.hosts import Host, RepositoryInfo
from pygitmirror.mirror.mirror_plan import MirrorPlan
from pygitmirror.mirror.mirror_result import MirrorResult
from pygitmirror.mirror.operation import Operation
from pygitmirror.repository_ref import RepositoryRef

_logger = logging.getLogger(__name__)

_BRANCHES = "refs/heads/"
_TAGS = "refs/tags/"


class Endpoint(NamedTuple):
    """A repository on a host: one end of an operation."""

    host: Host
    ref: RepositoryRef

    @property
    def url(self) -> str:
        """The URL which git reads and writes the repository at."""
        return self.host.repository_url(self.ref)

    @property
    def config(self) -> dict[str, str]:
        """The git configuration which authenticates."""
        return self.host.git_config()


def _ensure_exists(
    source: Endpoint, destination: Endpoint, dry_run: bool
) -> tuple[RepositoryInfo | None, bool]:
    """Create the destination when it is missing; return it and whether it was."""
    if not destination.host.has_api:
        return None, False
    info = destination.host.get_repository(destination.ref)
    if info is not None:
        return info, False
    if dry_run:
        return None, True
    # Private unless the source is known to be public.
    settings = source.host.get_repository(source.ref) if source.host.has_api else None
    _logger.info("creating %s at %s", destination.ref, destination.host.url)
    info = destination.host.create_repository(
        destination.ref,
        description=settings.description if settings else "",
        private=settings.private if settings else True,
    )
    return info, True


def _copy_default_branch(
    git: Git,
    source: Endpoint,
    destination: Endpoint,
    info: RepositoryInfo | None,
    source_refs: Mapping[str, str],
) -> None:
    """Make the default branch of the source the one of the destination."""
    if not destination.host.has_api:
        return
    branch = default_branch(git, source.url, source.config)
    if branch is None or f"{_BRANCHES}{branch}" not in source_refs:
        return
    if info is not None and info.default_branch == branch:
        return
    _logger.info("setting the default branch of %s to %s", destination.ref, branch)
    destination.host.set_default_branch(destination.ref, branch)


def _diverged(
    mirror: LocalMirror, plan: MirrorPlan, source_refs: Mapping[str, str], refs: Mapping[str, str]
) -> list[str]:
    """Return the references which cannot be updated without losing something."""
    return [
        name
        for name in plan.update
        if name.startswith(_TAGS) or not mirror.is_ancestor(refs[name], source_refs[name])
    ]


def transfer(
    operation: Operation,
    source: Endpoint,
    destination: Endpoint,
    git: Git,
    local_mirror: Callable[[], AbstractContextManager[LocalMirror]],
    *,
    prune: bool = False,
    archive_source: bool = False,
    dry_run: bool = False,
) -> MirrorResult:
    """Run one operation on one repository.

    The references of both ends are compared first, so that a destination
    which is up to date costs two listings and nothing is downloaded.

    :param operation: the operation
    :param source: the repository to read
    :param destination: the repository to write
    :param git: the runner of git commands
    :param local_mirror: gives the local mirror of the source when data has
        to be moved
    :param prune: delete what only the destination has; for a sync only
    :param archive_source: make the source read-only at the end
    :param dry_run: change nothing
    :returns: what was done, or would be
    :raises GitMirrorError: if the operation cannot be completed
    """
    force = operation is Operation.SYNC
    prune = prune and force
    if archive_source and not (source.host.has_api and source.host.can_archive):
        raise UnsupportedError(f"{source.host.url} cannot archive a repository")
    if source.url == destination.url:
        raise ConfigError(f"the source and the destination are both {source.url}")

    _logger.info("%s %s -> %s", operation, source.url, destination.url)
    source_refs = list_refs(git, source.url, source.config)
    info, created = _ensure_exists(source, destination, dry_run)
    # A repository which a dry run would create does not exist to be read.
    refs = {} if created and dry_run else list_refs(git, destination.url, destination.config)
    plan = MirrorPlan.compare(source_refs, refs)
    if prune and refs and not source_refs:
        raise EmptySourceError(
            f"{source.url} has no branches or tags; not deleting those of {destination.url}"
        )
    if operation is Operation.MIGRATE and plan.delete:
        raise VerificationError(
            f"{destination.url} has branches or tags which the source does not have, "
            f"such as {plan.delete[0]}"
        )
    set_default = created or operation is not Operation.CLONE

    if plan.changes(prune=prune):
        with local_mirror() as mirror:
            mirror.fetch(source.url, source.config)
            # What was fetched is what is pushed, should the source have moved.
            source_refs = mirror.refs()
            plan = MirrorPlan.compare(source_refs, refs)
            if not force and (diverged := _diverged(mirror, plan, source_refs, refs)):
                raise DivergedError(diverged)
            if not dry_run:
                if plan.create or plan.update:
                    mirror.push(destination.url, destination.config, force=force)
                # A host refuses to delete its default branch: when the
                # source renamed its own, the new one is made the default
                # before the old one is deleted.
                if set_default:
                    _copy_default_branch(git, source, destination, info, source_refs)
                if prune and plan.delete:
                    mirror.push(destination.url, destination.config, force=True, prune=True)
    elif set_default and not dry_run:
        _copy_default_branch(git, source, destination, info, source_refs)

    if operation is Operation.MIGRATE and not dry_run:
        if list_refs(git, destination.url, destination.config) != source_refs:
            raise VerificationError(f"{destination.url} does not match {source.url} after the push")
    if archive_source and not dry_run:
        _logger.info("archiving %s", source.url)
        source.host.archive_repository(source.ref)
    return MirrorResult(
        operation,
        source.ref,
        destination.ref,
        plan=plan,
        created=created,
        pruned=prune and bool(plan.delete),
        archived=archive_source and not dry_run,
        dry_run=dry_run,
    )
