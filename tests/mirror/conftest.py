from pathlib import Path

import pytest

from pygitmirror import Mirror, PlainHost
from tests.helpers import FolderHost, Workshop, git


class World:
    """A source repository ``org/repo`` and two kinds of destination hosts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.shop = Workshop(root, root / "source" / "org" / "repo")
        self.source = PlainHost(url=str(root / "source"))
        self.plain = PlainHost(url=str(root / "plain"))
        self.api = FolderHost(str(root / "api"))
        self.workdir = root / "mirrors"

    @property
    def plain_repo(self) -> Path:
        """The destination repository on the plain host, created empty."""
        path = self.root / "plain" / "org" / "repo"
        if not path.is_dir():
            path.mkdir(parents=True)
            git("init", "-q", "--bare", "-b", "main", cwd=path)
        return path

    @property
    def api_repo(self) -> Path:
        """Where the destination repository of the host with an API is."""
        return self.root / "api" / "org" / "repo.git"

    def to_plain(self) -> Mirror:
        """Return a mirror to the plain host, whose repository exists."""
        assert self.plain_repo
        return Mirror(self.source, self.plain, workdir=self.workdir)

    def to_api(self) -> Mirror:
        """Return a mirror to the host with an API."""
        return Mirror(self.source, self.api, workdir=self.workdir)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)
