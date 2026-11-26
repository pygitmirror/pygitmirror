"""The web application: its routes and what protects them."""

import logging
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from pygitmirror import __version__
from pygitmirror.errors import GitMirrorError
from pygitmirror.git import Git
from pygitmirror.hosts import PROVIDERS
from pygitmirror.mirror import Mirror, MirrorResult, Operation
from pygitmirror.web import _forms, _security, _storage
from pygitmirror.web._static import static
from pygitmirror.web.job_registry import JobRegistry
from pygitmirror.web.request import Request
from pygitmirror.web.response import Response

_logger = logging.getLogger(__name__)

_LOCAL = ("localhost", "127.0.0.1", "[::1]")


def _forgetting(mirror: Mirror, results: Iterator[MirrorResult]) -> Iterator[MirrorResult]:
    """Pass results on, deleting the local mirror of each repository once it is done."""
    for result in results:
        mirror.forget(result.source)
        yield result


class WebApp:
    """Answers the requests of the page, for one user on one machine.

    The application is reached with an access key, which the first visit
    exchanges for a cookie. Tokens of the hosts arrive with a request, live
    in memory while a job runs, and are never stored or logged.

    :param workdir: the folder of the local mirrors
    :param key: the access key; a random one when not given
    :param allowed_hosts: host names the application answers to, besides
        those of the local machine
    :param git: the runner of git commands; by default one which allows the
        ``https``, ``http`` and ``ssh`` transports, and no local folders
    """

    def __init__(
        self,
        workdir: Path | str,
        *,
        key: str | None = None,
        allowed_hosts: Sequence[str] = (),
        git: Git | None = None,
    ) -> None:
        self._workdir = Path(workdir)
        self.key = key or _security.new_key()
        self._allowed = frozenset(name.lower() for name in (*_LOCAL, *allowed_hosts))
        self._git = git or Git(allowed_protocols=("https", "http", "ssh"))
        self._jobs = JobRegistry()

    def handle(self, request: Request) -> Response:
        """Answer a request.

        :param request: the request
        :returns: the response, with the security headers
        """
        try:
            response = self._route(request)
        except (GitMirrorError, ValueError) as error:
            response = Response.error(400, str(error))
        return _security.harden(response)

    def _route(self, request: Request) -> Response:
        """Check a request and pass it to its route."""
        if not _security.host_allowed(request, self._allowed):
            return Response.error(403, "this address is not allowed; see --allow-host")
        if len(request.body) > _security.MAX_BODY:
            return Response.error(413, "the request is too large")
        path = request.path
        if path == "/healthz" and request.method == "GET":
            return Response(200, b"ok\n")
        if path.startswith("/static/") and request.method == "GET":
            return static(path.removeprefix("/static/")) or Response.error(404, "not found")
        if path == "/" and request.method == "GET":
            return self._page(request)
        if not path.startswith("/api/"):
            return Response.error(404, "not found")
        if not _security.same_key(request.cookie(_security.COOKIE), self.key):
            return Response.error(401, "open the link which the server printed when it started")
        if request.method == "GET":
            return self._get(path)
        if request.method != "POST":
            return Response.error(405, "method not allowed")
        if _security.cross_site(request):
            return Response.error(403, "the request did not come from the page")
        return self._post(path, request.json())

    def _page(self, request: Request) -> Response:
        """Serve the page, or exchange the access key for a cookie."""
        if _security.same_key(request.query("key"), self.key):
            # Redirect, so that the key does not stay in the address bar.
            headers = {"Location": "/", "Set-Cookie": _security.key_cookie(self.key)}
            return Response(303, headers={**headers, "Cache-Control": "no-store"})
        if not _security.same_key(request.cookie(_security.COOKIE), self.key):
            locked = static("locked.html")
            if locked is None:
                return Response.error(401, "locked")
            return Response(401, locked.body, locked.content_type, {"Cache-Control": "no-store"})
        return static("index.html") or Response.error(404, "not found")

    def _get(self, path: str) -> Response:
        """Answer a reading request to the API."""
        if path == "/api/session":
            providers = [
                {
                    "name": name,
                    "has_api": PROVIDERS[name].has_api,
                    "can_archive": PROVIDERS[name].can_archive,
                    "default_url": PROVIDERS[name].default_url,
                }
                for name in _forms.OFFERED
            ]
            return Response.json({"version": __version__, "providers": providers})
        if path == "/api/storage":
            return Response.json(_storage.usage(self._workdir))
        if path.startswith("/api/jobs/"):
            job = self._jobs.get(path.removeprefix("/api/jobs/"))
            if job is not None:
                return Response.json(job.to_dict())
        return Response.error(404, "not found")

    def _post(self, path: str, data: dict[str, Any]) -> Response:
        """Answer a request to the API which does something."""
        if path == "/api/repositories":
            host = _forms.host(data.get("host"), "source")
            owner = _forms.text(data, "owner", required=True) or ""
            listed = sorted(host.list_repositories(owner), key=lambda info: info.ref.path)
            return Response.json(
                {
                    "repositories": [
                        {
                            "name": info.ref.name,
                            "private": info.private,
                            "archived": info.archived,
                            "default_branch": info.default_branch,
                        }
                        for info in listed
                    ]
                }
            )
        if path == "/api/jobs":
            return self._start(data)
        if path == "/api/storage/clear":
            if self._jobs.busy:
                return Response.error(409, "a job is running; wait until it is finished")
            return Response.json({"deleted": _storage.clear(self._workdir)})
        return Response.error(404, "not found")

    def _start(self, data: dict[str, Any]) -> Response:
        """Start a job."""
        operation = _forms.operation(data)
        repositories = _forms.repositories(data)
        owner = repositories[0].owner
        to = _forms.text(data, "destination_owner") or owner
        mirror = Mirror(
            _forms.host(data.get("source"), "source"),
            _forms.host(data.get("destination"), "destination"),
            workdir=self._workdir,
            owners={owner: to},
            git=self._git,
        )
        mirror.destination_of(repositories[0])  # checks the owner at the destination
        results = mirror.run(
            operation,
            repositories,
            prune=operation is Operation.SYNC and not _forms.flag(data, "keep_extra"),
            archive_source=operation is Operation.MIGRATE and _forms.flag(data, "archive_source"),
            dry_run=_forms.flag(data, "dry_run"),
        )
        if not _forms.flag(data, "keep_copies"):
            results = _forgetting(mirror, results)
        job = self._jobs.start(repositories, results)
        if job is None:
            return Response.error(409, "another job is still running")
        _logger.info("job %s: %s of %d repositories", job.identifier, operation, len(repositories))
        return Response.json({"id": job.identifier}, 202)
