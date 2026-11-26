"""The disk space of the local mirrors."""

import shutil
from pathlib import Path
from typing import Any

from pygitmirror.git import LocalMirror


def _mirrors(workdir: Path) -> list[Path]:
    """Return the folders below a work folder which are local mirrors."""
    if not workdir.is_dir():
        return []
    return [
        path
        for path in workdir.rglob("*.git")
        if LocalMirror.is_mirror(path) and not any(p.suffix == ".git" for p in path.parents)
    ]


def _size(folder: Path) -> int:
    """Return the number of bytes of the files below a folder."""
    return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())


def usage(workdir: Path) -> dict[str, Any]:
    """Measure the local mirrors and the disk they are on.

    :param workdir: the folder of the local mirrors
    :returns: the folder, the number of mirrors, the bytes they use, and
        the free and total bytes of the disk
    """
    mirrors = _mirrors(workdir)
    disk = shutil.disk_usage(workdir if workdir.is_dir() else workdir.parent)
    return {
        "path": str(workdir),
        "mirrors": len(mirrors),
        "used": sum(_size(mirror) for mirror in mirrors),
        "free": disk.free,
        "total": disk.total,
    }


def clear(workdir: Path) -> int:
    """Delete the local mirrors, and nothing else, below a work folder.

    :param workdir: the folder of the local mirrors
    :returns: the number of mirrors which were deleted
    """
    mirrors = _mirrors(workdir)
    for mirror in mirrors:
        shutil.rmtree(mirror, ignore_errors=True)
        # The folders of the owners, once they are empty.
        for parent in mirror.parents:
            if parent == workdir or workdir not in parent.parents:
                break
            try:
                parent.rmdir()
            except OSError:
                break
    return len(mirrors)
