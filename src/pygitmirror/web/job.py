"""An operation on several repositories which runs in the background."""

import logging
import threading
from collections.abc import Iterator, Sequence
from typing import Any

from pygitmirror.mirror import MirrorResult
from pygitmirror.repository_ref import RepositoryRef

_logger = logging.getLogger(__name__)


class Job:
    """Runs an operation in a thread and collects its results as they arrive.

    The job is given the results as an iterator, which holds the hosts and
    their tokens. It drops the iterator when it is finished, so that a
    finished job holds no credential.

    :param identifier: the name of the job in the URLs of the API
    :param repositories: the repositories it processes, in order
    :param results: yields the result of each repository
    """

    def __init__(
        self,
        identifier: str,
        repositories: Sequence[RepositoryRef],
        results: Iterator[MirrorResult],
    ) -> None:
        self.identifier = identifier
        self._names = [repository.path for repository in repositories]
        self._results: Iterator[MirrorResult] | None = results
        self._done: list[dict[str, Any]] = []
        self._error: str | None = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name=f"job-{identifier}", daemon=True)

    def start(self) -> None:
        """Start the job in its thread."""
        self._thread.start()

    def wait(self, timeout: float | None = None) -> None:
        """Wait until the job is finished.

        :param timeout: the number of seconds to wait at most
        """
        self._thread.join(timeout)

    @property
    def running(self) -> bool:
        """Whether the job has results still to come."""
        with self._lock:
            return self._results is not None

    def _run(self) -> None:
        """Take the results one by one."""
        results = self._results
        try:
            for result in results or ():
                with self._lock:
                    self._done.append(result.to_dict())
        except Exception as error:  # noqa: BLE001 - reported to the page, and logged
            _logger.exception("job %s stopped", self.identifier)
            with self._lock:
                self._error = f"the job stopped: {type(error).__name__}"
        finally:
            with self._lock:
                self._results = None

    def to_dict(self) -> dict[str, Any]:
        """Return the state of the job as plain data.

        :returns: its identifier, whether it runs, the repositories, the
            results so far and, if it stopped early, why
        """
        with self._lock:
            return {
                "id": self.identifier,
                "state": "running" if self._results is not None else "done",
                "repositories": list(self._names),
                "results": list(self._done),
                "error": self._error,
            }
