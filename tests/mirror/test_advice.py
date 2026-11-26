import pytest

from pygitmirror import (
    ApiError,
    DivergedError,
    GitError,
    MirrorResult,
    Operation,
    RepositoryRef,
)
from pygitmirror.mirror._advice import advise

URL = "http://git.example.com/acme/api.git"
REPO = RepositoryRef("acme", "api")

#: What git and servers said in real runs, or say according to their sources.
SAID = [
    ("remote: Repository not found\nfatal: repository 'x' not found", "There is no repository"),
    ("fatal: '/srv/x' does not appear to be a git repository", "There is no repository"),
    ("fatal: Authentication failed for 'http://git.example.com/'", "did not accept the token"),
    ("fatal: could not read Username for 'x': terminal prompts disabled", "did not accept"),
    ("remote: HTTP Basic: Access denied\nfatal: Authentication failed", "did not accept"),
    ("fatal: unable to access 'x': The requested URL returned error: 403", "not allowed"),
    (
        "remote: GitLab: You are not allowed to force push code to a protected branch on "
        "this project.\n ! [remote rejected] main -> main (pre-receive hook declined)",
        "Allow forced pushes",
    ),
    ("error: unable to write file: No space left on device", "disk of the local copies is full"),
    ("remote: error: File big.bin is 150 MB; this exceeds the file size limit of 100 MB", "size"),
    ("remote: This repository is archived.", "archived"),
    ("fatal: unable to access 'x': Could not resolve host: git.example.com", "cannot be reached"),
    ("fatal: unable to access 'x': Failed to connect to localhost port 3000", "host.docker"),
    (" ! [remote rejected] main -> main (pre-receive hook declined)", "refused the push"),
]


@pytest.mark.parametrize(("said", "expected"), SAID)
def test_what_git_says_is_explained(said: str, expected: str) -> None:
    advice = advise(GitError(f"git push --quiet {URL}", 1, said))
    assert advice is not None and expected in advice


def test_the_repository_is_named() -> None:
    advice = advise(GitError(f"git ls-remote --refs {URL}", 128, "remote: Repository not found"))
    assert advice is not None and URL in advice
    local = advise(GitError("git ls-remote --refs /srv/git/x", 128, "fatal: not found"))
    assert local is not None and "the server" in local


def test_git_which_cannot_run() -> None:
    advice = advise(GitError("git --version", None, "No such file or directory"))
    assert advice is not None and "Is git installed" in advice


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (0, "cannot be reached"),
        (401, "did not accept the token"),
        (403, "not allowed"),
        (404, "owner does not exist"),
        (422, "exist already"),
        (429, "Wait a while"),
        (502, "Try again later"),
    ],
)
def test_what_an_api_answers_is_explained(status: int, expected: str) -> None:
    advice = advise(ApiError(f"POST http://x answered {status}", status))
    assert advice is not None and expected in advice


def test_errors_which_explain_themselves_get_no_advice() -> None:
    assert advise(DivergedError(["refs/heads/main"])) is None
    assert advise(GitError("git push", 1, "something nobody has seen before")) is None
    assert advise(ApiError("GET http://x answered 418", 418)) is None


def test_a_result_carries_the_advice() -> None:
    error = GitError(f"git ls-remote {URL}", 128, "remote: Repository not found")
    failed = MirrorResult(Operation.SYNC, REPO, REPO, error=error)
    assert failed.advice is not None and failed.to_dict()["advice"] == failed.advice
    assert "Repository not found" in failed.to_dict()["error"]
    done = MirrorResult(Operation.SYNC, REPO, REPO)
    assert done.advice is None and done.to_dict()["advice"] is None
