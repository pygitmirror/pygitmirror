"""The settings of a run of the command line."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from pygitmirror.config.host_settings import HostSettings
from pygitmirror.mirror import Operation


@dataclass(frozen=True)
class Settings:
    """Everything a run needs, merged from the settings file and the command line.

    :param operation: what to do
    :param source: the host to read from
    :param destination: the host to write to
    :param repos: the names of the repositories by owner at the source;
        ``None`` in place of the names stands for all repositories of the
        owner
    :param owners: owners at the destination by owner at the source
    :param sync_path: the folder of the local mirrors
    :param prune: whether a sync deletes what the source does not have
    :param archive_source: whether a migration archives the source
    :param dry_run: whether nothing is changed
    """

    operation: Operation
    source: HostSettings
    destination: HostSettings
    repos: Mapping[str, tuple[str, ...] | None]
    owners: Mapping[str, str] = field(default_factory=dict)
    sync_path: Path = field(default_factory=Path.cwd)
    prune: bool = True
    archive_source: bool = False
    dry_run: bool = False
