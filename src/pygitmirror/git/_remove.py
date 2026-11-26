"""Deleting a repository from the disk."""

import logging
import os
import shutil
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


def _make_writable(function: Callable[[str], Any], name: str, _error: object) -> None:
    """Make a file writable and try again to delete it."""
    os.chmod(name, stat.S_IWRITE)
    function(name)


def remove_tree(path: Path) -> bool:
    """Delete a folder with everything in it.

    git marks the files of its object store as read-only, and Windows
    refuses to delete a read-only file. Such a file is made writable and
    deleted then.

    :param path: the folder
    :returns: whether the folder is gone; a failure is logged, not raised,
        since what could not be deleted is only a cache
    """
    try:
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_make_writable)
        else:
            shutil.rmtree(path, onerror=_make_writable)
    except OSError as error:
        _logger.warning("could not delete %s: %s", path, error)
    return not path.exists()
