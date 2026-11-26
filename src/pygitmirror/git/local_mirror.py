"""The local copy which data passes through on its way between two hosts."""

import shutil
from collections.abc import Mapping
from pathlib import Path

from pygitmirror.git._remote import MIRRORED, parse_refs
from pygitmirror.git.git import Git

_REFSPECS = tuple(f"{prefix}*:{prefix}*" for prefix in MIRRORED)


class LocalMirror:
    """A bare repository which holds the branches and tags of a source.

    It has no working tree and no configured remotes: every fetch and push
    names its URL, so that no address or credential is stored in it. After
    :meth:`fetch` its branches and tags are exactly those of the source,
    which makes pushing all of them the same as copying the source.

    Kept between runs, it makes the next fetch download only what is new.

    :param path: the folder of the repository, created by the first fetch
    :param git: the runner of git commands
    """

    def __init__(self, path: Path, git: Git) -> None:
        self._path = path
        self._git = git

    @property
    def path(self) -> Path:
        """The folder of the repository."""
        return self._path

    @staticmethod
    def is_mirror(path: Path) -> bool:
        """Tell whether a folder looks like a local mirror.

        :param path: a folder
        :returns: whether it is a bare git repository
        """
        return (path / "HEAD").is_file() and (path / "objects").is_dir()

    def delete(self) -> None:
        """Delete the repository from the disk, if it is one.

        The next fetch downloads everything again.
        """
        if self.is_mirror(self._path):
            shutil.rmtree(self._path, ignore_errors=True)

    def fetch(self, url: str, config: Mapping[str, str] | None = None) -> None:
        """Make the branches and tags equal to those of a repository.

        Branches and tags which the repository no longer has are deleted,
        and those which were rewritten are overwritten.

        :param url: the URL of the repository to copy
        :param config: the configuration which authenticates
        :raises GitError: if the repository cannot be read
        """
        if not self.is_mirror(self._path):
            self._path.mkdir(parents=True, exist_ok=True)
            self._git.run("init", "--quiet", "--bare", str(self._path))
        refspecs = [f"+{refspec}" for refspec in _REFSPECS]
        self._git.run(
            "fetch", "--quiet", "--prune", "--no-tags", url, *refspecs,
            cwd=self._path, config=config,
        )  # fmt: skip

    def refs(self) -> dict[str, str]:
        """Return the object names of the branches and tags by reference name."""
        output = self._git.run(
            "for-each-ref", "--format=%(objectname)%09%(refname)", *MIRRORED, cwd=self._path
        )
        return parse_refs(output)

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Tell whether a commit can be reached from another.

        :param ancestor: the object name of the commit which may be older
        :param descendant: the object name of the commit to start from
        :returns: ``True`` if moving a branch from the first to the second
            loses nothing; ``False`` also when the first is unknown here
        """
        return (
            self._git.status("merge-base", "--is-ancestor", ancestor, descendant, cwd=self._path)
            == 0
        )

    def push(
        self,
        url: str,
        config: Mapping[str, str] | None = None,
        *,
        force: bool = False,
        prune: bool = False,
    ) -> None:
        """Send all branches and tags to a repository.

        :param url: the URL of the repository to write to
        :param config: the configuration which authenticates
        :param force: overwrite the branches and tags which differ there
            instead of failing
        :param prune: delete the branches and tags there which are not here
        :raises GitError: if the server refuses the push
        """
        refspecs = [f"+{refspec}" if force else refspec for refspec in _REFSPECS]
        options = ["--prune"] if prune else []
        self._git.run("push", "--quiet", *options, url, *refspecs, cwd=self._path, config=config)
