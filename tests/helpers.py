"""Repositories on disk and stand-ins for the hosts, shared by the tests."""

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

from pygitmirror import Host, RepositoryInfo, RepositoryRef
from pygitmirror.hosts import ApiResponse

_IDENTITY = ("-c", "user.name=Test", "-c", "user.email=test@example.com")


def git(*args: str, cwd: Path) -> str:
    """Run git in a folder and return its output."""
    result = subprocess.run(
        ["git", *_IDENTITY, *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def refs(path: Path) -> dict[str, str]:
    """Return the branches and tags of a repository on disk."""
    lines = git("for-each-ref", "--format=%(refname) %(objectname)", cwd=path).splitlines()
    pairs = (line.partition(" ") for line in lines)
    return {name: sha for name, _, sha in pairs}


class Workshop:
    """A working repository whose commits are published to a bare one."""

    def __init__(self, root: Path, bare: Path) -> None:
        self.work = root / "work"
        self.bare = bare
        self.work.mkdir(parents=True)
        bare.mkdir(parents=True)
        git("init", "-q", "-b", "main", cwd=self.work)
        git("init", "-q", "--bare", "-b", "main", cwd=bare)
        self.commit("first")

    def commit(self, message: str, branch: str = "main") -> str:
        """Add a commit to a branch, publish it and return its name."""
        git("checkout", "-q", "-B", branch, cwd=self.work)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=self.work)
        self.publish()
        return git("rev-parse", "HEAD", cwd=self.work)

    def publish(self, *options: str) -> None:
        """Push all branches and tags to the bare repository."""
        git("push", "-q", "--force", *options, str(self.bare), "refs/*:refs/*", cwd=self.work)


class FakeTransport:
    """Answer the requests of an API from a table, and record them."""

    def __init__(self, answers: Mapping[tuple[str, str], Any]) -> None:
        self.answers = dict(answers)
        self.requests: list[tuple[str, str, Any]] = []
        self.headers: dict[str, str] = {}

    def __call__(
        self, method: str, url: str, headers: Mapping[str, str], data: bytes | None, timeout: float
    ) -> ApiResponse:
        self.requests.append((method, url, json.loads(data) if data else None))
        self.headers = dict(headers)
        answer = self.answers.get((method, url), ApiResponse(404, {}, {"message": "Not Found"}))
        return answer if isinstance(answer, ApiResponse) else ApiResponse(200, {}, answer)


class FolderHost(Host):
    """A host with an API whose repositories are bare ones in a folder."""

    provider: ClassVar[str] = "folder"

    def __init__(self, url: str, *, can_archive: bool = True) -> None:
        super().__init__(url=url)
        self.archivable = can_archive
        self.archived: list[RepositoryRef] = []
        self.created: dict[RepositoryRef, RepositoryInfo] = {}

    @property
    def can_archive(self) -> bool:  # type: ignore[override]
        return self.archivable

    def _path(self, repository: RepositoryRef) -> Path:
        return Path(self.repository_url(repository))

    def get_repository(self, repository: RepositoryRef) -> RepositoryInfo | None:
        path = self._path(repository)
        if not path.is_dir():
            return None
        head = git("symbolic-ref", "--short", "HEAD", cwd=path)
        return RepositoryInfo(repository, default_branch=head, private=False)

    def create_repository(
        self, repository: RepositoryRef, *, description: str = "", private: bool = True
    ) -> RepositoryInfo:
        path = self._path(repository)
        path.mkdir(parents=True)
        git("init", "-q", "--bare", "-b", "trunk", cwd=path)
        info = RepositoryInfo(repository, description, private, "trunk")
        self.created[repository] = info
        return info

    def list_repositories(self, owner: str) -> list[RepositoryInfo]:
        folder = Path(self.url) / owner
        return [
            RepositoryInfo(RepositoryRef(owner, path.name.removesuffix(".git")))
            for path in folder.glob("*.git")
        ]

    def set_default_branch(self, repository: RepositoryRef, branch: str) -> None:
        git("symbolic-ref", "HEAD", f"refs/heads/{branch}", cwd=self._path(repository))

    def archive_repository(self, repository: RepositoryRef) -> None:
        self.archived.append(repository)
