"""The entry point of the command line."""

import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from pygitmirror.cli._parser import SERVE, build_parser
from pygitmirror.config import Settings, load_settings
from pygitmirror.errors import GitMirrorError
from pygitmirror.mirror import Mirror, Operation
from pygitmirror.repository_ref import RepositoryRef
from pygitmirror.web import WebApp, serve

_logger = logging.getLogger("pygitmirror")

#: The environment variable which fixes the access key of the page.
KEY_VARIABLE = "GIT_MIRROR_KEY"

#: Options which are answered without a command.
_NO_COMMAND = ("-h", "--help", "--version")


def cache_folder() -> Path:
    """Return the folder in which the page keeps the local mirrors by default.

    :returns: ``git-mirror`` in the cache folder of the user: the one named
        by ``XDG_CACHE_HOME`` or, on Windows, ``LOCALAPPDATA``, and
        ``~/.cache`` otherwise
    """
    base = os.environ.get("XDG_CACHE_HOME") or os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / ".cache") / "git-mirror"


def _repositories(mirror: Mirror, settings: Settings) -> list[RepositoryRef]:
    """Return the repositories of the settings, listing the owners named in full."""
    repositories = []
    for owner, names in settings.repos.items():
        if names is None:
            repositories += mirror.repositories(owner)
        else:
            repositories += [RepositoryRef(owner, name) for name in names]
    return repositories


def _run(settings: Settings) -> int:
    """Run the operation of the settings and return the number of failures."""
    mirror = Mirror(
        settings.source.make_host("source", os.environ),
        settings.destination.make_host("destination", os.environ),
        workdir=settings.sync_path,
        owners=settings.owners,
    )
    repositories = _repositories(mirror, settings)
    results = mirror.run(
        settings.operation,
        repositories,
        prune=settings.prune,
        archive_source=settings.archive_source,
        dry_run=settings.dry_run,
    )
    failed = 0
    for result in results:
        _logger.log(logging.INFO if result.ok else logging.ERROR, "%s", result.summary())
        if result.advice:
            _logger.error("%s: %s", result.source, result.advice)
        failed += not result.ok
    _logger.info("%d of %d repositories failed", failed, len(repositories))
    return failed


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``git-mirror`` command.

    :param argv: the arguments, without the name of the program; those of
        the process when not given
    :returns: the exit status: 0 when every repository succeeded, 1 when
        one failed, 2 when the settings are invalid or nothing could be
        started
    """
    args = list(sys.argv[1:] if argv is None else argv)
    operations = [*(operation.value for operation in Operation), SERVE]
    # The first versions had no commands and did what clone does.
    if args and args[0] not in operations and args[0] not in _NO_COMMAND:
        args.insert(0, Operation.CLONE.value)
    options = vars(build_parser().parse_args(args))
    logging.basicConfig(level=options["log"], format="%(asctime)s %(levelname)-7s %(message)s")
    if options["operation"] == SERVE:
        folder = Path(options["sync_path"]).expanduser() if options["sync_path"] else cache_folder()
        _logger.info("local copies are kept in %s", folder)
        app = WebApp(
            folder,
            key=os.environ.get(KEY_VARIABLE) or None,
            allowed_hosts=options["allow_host"],
        )
        serve(app, options["host"], options["port"])
        return 0
    try:
        failed = _run(load_settings(Operation(options["operation"]), options))
    except GitMirrorError as error:
        _logger.error("%s", error)
        return 2
    return 1 if failed else 0
