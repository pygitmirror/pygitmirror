"""Exceptions raised by the package.

They all derive from :class:`GitMirrorError`, so that a caller can catch
what the package reports and let programming errors through. They are kept
in one module because none has behavior of its own.
"""

from collections.abc import Sequence


class GitMirrorError(Exception):
    """Base class of the errors which the package reports."""


class ConfigError(GitMirrorError):
    """A setting, argument or name is missing or invalid."""


class UnsupportedError(GitMirrorError):
    """A host cannot do what was asked of it."""


class GitError(GitMirrorError):
    """A git command failed.

    :param command: the command, with credentials removed
    :param returncode: the exit status of git, or ``None`` when it did not
        finish
    :param output: what git wrote to its error stream, with credentials
        removed
    """

    def __init__(self, command: str, returncode: int | None, output: str) -> None:
        self.command = command
        self.returncode = returncode
        self.output = output
        status = "did not finish" if returncode is None else f"failed with status {returncode}"
        detail = f": {output.strip()}" if output.strip() else ""
        super().__init__(f"{command} {status}{detail}")


class ApiError(GitMirrorError):
    """A request to the API of a host failed.

    :param message: what went wrong
    :param status: the HTTP status, or 0 when there was no response
    """

    def __init__(self, message: str, status: int = 0) -> None:
        self.status = status
        super().__init__(message)


class DivergedError(GitMirrorError):
    """The destination has commits or tags which the source does not have.

    :param refs: the references which cannot be updated without losing
        something at the destination
    """

    def __init__(self, refs: Sequence[str]) -> None:
        self.refs = tuple(refs)
        shown = ", ".join(self.refs[:5]) + (" and others" if len(self.refs) > 5 else "")
        super().__init__(
            f"the destination differs from the source in {shown}; "
            "use sync to overwrite the destination"
        )


class EmptySourceError(GitMirrorError):
    """The source has no branches or tags, and a sync would empty the destination."""


class VerificationError(GitMirrorError):
    """The destination does not match the source after a migration."""
