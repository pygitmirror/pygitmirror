"""Saying what went wrong, and what to do, in words a person can act on."""

import re

from pygitmirror.errors import ApiError, GitError, GitMirrorError

_URL = re.compile(r"(?:https?|ssh)://[^\s'\"]+")

#: What git or a server says, in lower case, and what it means. The first
#: match wins, so the more specific phrases come first. ``{url}`` stands for
#: the repository the command was about.
_GIT = (
    (
        ("protected branch",),
        "The server protects this branch against being overwritten. Allow forced pushes "
        "for it in the settings of the repository at the destination, then sync again. "
        "GitLab protects the default branch of every new project.",
    ),
    (
        ("no space left on device", "disk quota exceeded"),
        "The disk of the local copies is full. Delete the local copies or free some "
        "space, then run it again; nothing was changed at the destination.",
    ),
    (
        ("file size limit", "large files detected"),
        "The destination refuses a file of this size. The repository cannot be copied "
        "there as it is.",
    ),
    (
        (
            "authentication failed",
            "could not read username",
            "could not read password",
            "invalid username",
            "http basic: access denied",
            "terminal prompts disabled",
        ),
        "The server did not accept the token for {url}. Check that the token is "
        "complete, has not expired, and belongs to this server.",
    ),  # fmt: skip
    (
        ("permission denied", "access denied", "not allowed to push", "403"),
        "The token is not allowed to do this at {url}. It needs to read the source and "
        "to write the destination.",
    ),
    (
        ("is archived", "archived"),
        "The repository at {url} is archived, which makes it read-only. Unarchive it to "
        "write to it.",
    ),
    (
        (
            "repository not found",
            "not found",
            "does not appear to be a git repository",
            "does not exist",
        ),
        "There is no repository at {url}, or the token cannot see it. Check the owner "
        "and the name.",
    ),  # fmt: skip
    (
        (
            "could not resolve host",
            "connection refused",
            "failed to connect",
            "connection timed out",
            "network is unreachable",
            "ssl",
            "certificate",
        ),
        "The server of {url} cannot be reached. Check the address. Inside a container, "
        "a server on this machine is host.docker.internal, not localhost.",
    ),  # fmt: skip
    (
        ("remote rejected", "pre-receive hook declined", "hook declined"),
        "The destination refused the push to {url}. Its message is in the details.",
    ),
)

#: What an API answers, by HTTP status.
_API = {
    0: "The server cannot be reached. Check the address. Inside a container, a server on "
    "this machine is host.docker.internal, not localhost.",
    401: "The server did not accept the token. Check that it is complete, has not "
    "expired, and belongs to this server.",
    403: "The token is not allowed to do this. To create repositories it needs write "
    "access to the owner at the destination.",
    404: "The owner does not exist on the server, or the token cannot see it. An owner "
    "is not created: create the user, organization or group first.",
    409: "The server says a repository of this name exists already but cannot be used.",
    422: "The server refused the request. A repository of this name may exist already, "
    "or the name is not allowed there.",
    429: "The server limits how many requests it takes. Wait a while and run it again.",
}


def _of_git(error: GitError) -> str | None:
    """Explain a failed git command."""
    said = error.output.lower()
    found = _URL.search(error.command)
    url = found.group(0) if found else "the server"
    for phrases, advice in _GIT:
        if any(phrase in said for phrase in phrases):
            return advice.format(url=url)
    if error.returncode is None:
        return "git could not be run, or took too long. Is git installed?"
    return None


def advise(error: GitMirrorError) -> str | None:
    """Say what an error means and what to do about it.

    :param error: an error of an operation
    :returns: a sentence or two for the person who ran the operation, or
        ``None`` when the message of the error is the best there is
    """
    if isinstance(error, GitError):
        return _of_git(error)
    if isinstance(error, ApiError):
        if error.status >= 500:
            return "The server failed while answering. Try again later."
        return _API.get(error.status)
    return None
