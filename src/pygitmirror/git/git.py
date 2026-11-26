"""Running the git executable."""

import logging
import os
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from pygitmirror.errors import GitError
from pygitmirror.git._redact import redact

_logger = logging.getLogger(__name__)


class Git:
    """Run git commands without ever waiting for input.

    A command which would ask for a user name, a password or the
    confirmation of an SSH host key fails instead, so that an unattended
    run cannot hang.

    :param executable: the name or the path of the git executable
    :param allowed_protocols: the transports git may use. The default allows
        local folders (``file``); a service which takes addresses from its
        users should allow ``https`` and ``ssh`` only.
    :param timeout: the number of seconds a command may take, or ``None``
        for no limit
    """

    def __init__(
        self,
        executable: str = "git",
        *,
        allowed_protocols: Sequence[str] = ("https", "http", "ssh", "git", "file"),
        timeout: float | None = None,
    ) -> None:
        self._executable = executable
        self._allowed_protocols = tuple(allowed_protocols)
        self._timeout = timeout

    def _environment(self, config: Mapping[str, str] | None) -> dict[str, str]:
        """Return the environment of a command, with its configuration."""
        env = dict(os.environ)
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ALLOW_PROTOCOL"] = ":".join(self._allowed_protocols)
        env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
        # Configuration in the environment, which git reads as if it were
        # given with -c, without showing it in the list of processes.
        count = int(env.get("GIT_CONFIG_COUNT") or 0)
        for key, value in (config or {}).items():
            env[f"GIT_CONFIG_KEY_{count}"] = key
            env[f"GIT_CONFIG_VALUE_{count}"] = value
            count += 1
        env["GIT_CONFIG_COUNT"] = str(count)
        return env

    def _run(
        self, args: Sequence[str], cwd: Path | None, config: Mapping[str, str] | None
    ) -> "subprocess.CompletedProcess[str]":
        """Run a command and return it once it has finished."""
        command = redact(shlex.join([self._executable, *args]))
        _logger.debug("%s", command)
        try:
            return subprocess.run(  # noqa: S603 - a list of arguments, without a shell
                [self._executable, *args],
                cwd=cwd,
                env=self._environment(config),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise GitError(command, None, f"no result after {self._timeout} seconds") from error
        except OSError as error:
            raise GitError(command, None, str(error)) from error

    def run(
        self,
        *args: str,
        cwd: Path | None = None,
        config: Mapping[str, str] | None = None,
    ) -> str:
        """Run a git command and return what it wrote.

        :param args: the arguments of git, starting with the command
        :param cwd: the folder to run in
        :param config: git configuration for this command only, such as the
            one which :meth:`~pygitmirror.hosts.host.Host.git_config` returns
        :returns: the standard output of the command
        :raises GitError: if git cannot be run, fails or takes too long
        """
        result = self._run(args, cwd, config)
        if result.returncode != 0:
            command = redact(shlex.join([self._executable, *args]))
            raise GitError(command, result.returncode, redact(result.stderr))
        return result.stdout

    def status(self, *args: str, cwd: Path | None = None) -> int:
        """Run a git command which answers with its exit status.

        :param args: the arguments of git, starting with the command
        :param cwd: the folder to run in
        :returns: the exit status
        :raises GitError: if git cannot be run or takes too long
        """
        return self._run(args, cwd, None).returncode
