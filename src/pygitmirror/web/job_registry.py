"""The jobs of the application."""

import secrets
import threading
from collections.abc import Iterator, Sequence

from pygitmirror.mirror import MirrorResult
from pygitmirror.repository_ref import RepositoryRef
from pygitmirror.web.job import Job


class JobRegistry:
    """Starts jobs, one at a time, and remembers the most recent ones.

    One job at a time keeps two operations from using the same local mirror
    at once.

    :param keep: the number of finished jobs to remember
    """

    def __init__(self, keep: int = 20) -> None:
        self._keep = keep
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(
        self, repositories: Sequence[RepositoryRef], results: Iterator[MirrorResult]
    ) -> Job | None:
        """Start a job unless one is running.

        :param repositories: the repositories it processes
        :param results: yields the result of each repository
        :returns: the job, or ``None`` if another one is still running
        """
        with self._lock:
            if any(job.running for job in self._jobs.values()):
                return None
            job = Job(secrets.token_urlsafe(9), repositories, results)
            self._jobs[job.identifier] = job
            for identifier in list(self._jobs)[: -self._keep]:
                del self._jobs[identifier]
            job.start()
            return job

    @property
    def busy(self) -> bool:
        """Whether a job is running."""
        with self._lock:
            return any(job.running for job in self._jobs.values())

    def get(self, identifier: str) -> Job | None:
        """Return a job by its identifier.

        :param identifier: the identifier
        :returns: the job, or ``None`` if it is unknown or forgotten
        """
        with self._lock:
            return self._jobs.get(identifier)
