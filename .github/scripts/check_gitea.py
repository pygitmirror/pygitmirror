#!/usr/bin/env python3
"""Copy between two real Gitea servers, with tokens, and check the result.

Starts two Gitea containers, creates a user and a token on each, and runs
clone, sync and migrate from one to the other through the library::

    uv run python .github/scripts/check_gitea.py

It needs Docker. The containers listen on ports 47303 and 47304 of this
machine only, and are removed at the end.
"""

import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from pygitmirror import Git, Host, Mirror, RepositoryRef, make_host
from pygitmirror.git import list_refs

IMAGE = "gitea/gitea:latest"
SERVERS = {"git-mirror-check-source": 47303, "git-mirror-check-destination": 47304}
SETTINGS = {
    "GITEA__security__INSTALL_LOCK": "true",
    "GITEA__database__DB_TYPE": "sqlite3",
    "GITEA__server__DISABLE_SSH": "true",
    "GITEA__service__DISABLE_REGISTRATION": "true",
}
API = RepositoryRef("acme", "api")
NOTES = RepositoryRef("tester", "notes")

failures: list[str] = []


def check(name: str, passed: object) -> None:
    """Print a check and remember it if it failed."""
    print(f"{'ok  ' if passed else 'FAIL'} {name}")
    if not passed:
        failures.append(name)


def run(*command: str, cwd: Path | None = None) -> str:
    """Run a command and return what it printed."""
    result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def start(name: str, port: int) -> Host:
    """Start a Gitea server and return it as a host, with the token of a new user."""
    subprocess.run(["docker", "rm", "--force", name], check=False, capture_output=True)
    settings = [f"--env={key}={value}" for key, value in SETTINGS.items()]
    url = f"http://127.0.0.1:{port}"
    publish = f"--publish=127.0.0.1:{port}:3000"
    run("docker", "run", "--detach", "--name", name, publish, *settings, IMAGE)
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"{url}/api/v1/version", timeout=2):
                break
        except OSError:
            time.sleep(0.5)
    gitea = ("docker", "exec", "--user", "git", name, "gitea", "admin", "user")
    run(*gitea, "create", "--admin", "--username", "tester", "--password", "Check-pass-12345",
        "--email", "tester@example.com", "--must-change-password=false")  # fmt: skip
    token = run(*gitea, "generate-access-token", "--username", "tester", "--token-name", "check",
                "--scopes", "all", "--raw")  # fmt: skip
    return make_host("gitea", url=url, token=token.splitlines()[-1])


def organization(host: Host, name: str) -> None:
    """Create an organization, which the package itself never does."""
    host._api.request("POST", "/orgs", body={"username": name})  # noqa: SLF001


def checks(source: Host, destination: Host, work: Path) -> None:
    """Run the operations and check what they did."""
    git = Git()

    def commit(*args: str) -> None:
        run("git", "-c", "user.name=Check", "-c", "user.email=check@example.com", *args, cwd=work)

    def push(repository: RepositoryRef, *refspecs: str) -> None:
        url, config = source.repository_url(repository), source.git_config()
        git.run("push", "--quiet", "--force", url, *refspecs, cwd=work, config=config)

    def refs(host: Host, repository: RepositoryRef) -> dict[str, str]:
        return list_refs(git, host.repository_url(repository), host.git_config())

    organization(source, "acme")
    organization(destination, "acme-copy")
    created = source.create_repository(API, description="The API", private=False)
    check("create a repository in an organization", created.ref == API and not created.private)
    own = source.create_repository(NOTES, description="notes", private=True)
    check("create a private repository for the account", own.private)
    check("a missing repository is reported as missing",
          source.get_repository(RepositoryRef("acme", "missing")) is None)  # fmt: skip
    check("list an organization", [i.ref for i in source.list_repositories("acme")] == [API])
    listed = [(info.ref, info.private) for info in source.list_repositories("tester")]
    check("list the account, private repositories included", listed == [(NOTES, True)])

    commit("init", "--quiet", "--initial-branch=main")
    commit("commit", "--quiet", "--allow-empty", "--message=one")
    commit("tag", "--annotate", "v1", "--message=v1")
    commit("branch", "dev")
    push(API, "refs/heads/*:refs/heads/*", "refs/tags/*:refs/tags/*")
    check("push with a token", len(refs(source, API)) == 3)

    mirror = Mirror(source, destination, workdir=work / "mirrors", owners={"acme": "acme-copy"})
    copy = mirror.destination_of(API)
    preview = mirror.clone(API, dry_run=True)
    check("a preview creates nothing", preview.created and destination.get_repository(copy) is None)
    result = mirror.clone(API)
    info = destination.get_repository(copy)
    check("clone creates the repository", result.created and info is not None)
    check("the description and visibility are copied",
          info is not None and info.description == "The API" and not info.private)  # fmt: skip
    check("the branches and tags are equal", refs(destination, copy) == refs(source, API))
    check("a second clone changes nothing", not mirror.clone(API).changed)

    # The source rewrites its history, renames its default branch and drops one.
    commit("commit", "--quiet", "--amend", "--allow-empty", "--message=rewritten")
    commit("branch", "--move", "main", "stable")
    push(API, "refs/heads/stable:refs/heads/stable")
    source.set_default_branch(API, "stable")
    push(API, ":refs/heads/main", ":refs/heads/dev")
    result = mirror.sync(API)
    check("sync deletes what the source dropped", refs(destination, copy) == refs(source, API))
    info = destination.get_repository(copy)
    check("the default branch follows a rename", info and info.default_branch == "stable")
    check("a second sync changes nothing", not mirror.sync(API).changed)

    push(NOTES, "refs/heads/stable:refs/heads/main")
    plain = Mirror(source, destination, workdir=work / "mirrors")
    result = plain.migrate(NOTES, archive_source=True)
    moved = destination.get_repository(NOTES)
    check("migrate keeps a private repository private", moved is not None and moved.private)
    archived = source.get_repository(NOTES)
    check("migrate archives the source", result.archived and archived and archived.archived)
    anonymous = make_host("gitea", url=destination.url)
    check("a private repository is hidden without a token",
          anonymous.get_repository(NOTES) is None)  # fmt: skip


def main() -> int:
    """Start the servers, run the checks, remove the servers."""
    try:
        source, destination = (start(name, port) for name, port in SERVERS.items())
        with tempfile.TemporaryDirectory() as folder:
            checks(source, destination, Path(folder))
    finally:
        subprocess.run(["docker", "rm", "--force", *SERVERS], check=False, capture_output=True)
    print(f"{len(failures)} checks failed" if failures else "all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
