"""A client for the JSON API of a host."""

import json
import logging
from collections.abc import Iterator, Mapping
from typing import Any
from urllib.parse import urlencode, urlsplit

from pygitmirror.errors import ApiError, ConfigError
from pygitmirror.hosts._transport import Transport, same_origin, send
from pygitmirror.hosts.api_response import ApiResponse

_logger = logging.getLogger(__name__)


class ApiClient:
    """Send requests to one API and decode its JSON answers.

    The client talks to one server only: a path is appended to the base URL,
    and a link to a next page is followed only when it stays on that server,
    so that the token is never sent anywhere else.

    :param base_url: the URL which the paths of the API are appended to
    :param headers: headers sent with every request, the authorization
        included
    :param timeout: the number of seconds to wait for the server
    :param transport: the function which sends a request; the default uses
        ``urllib``
    :raises ConfigError: if the URL is not an HTTP or HTTPS URL
    """

    def __init__(
        self,
        base_url: str,
        headers: Mapping[str, str] | None = None,
        *,
        timeout: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        parts = urlsplit(base_url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ConfigError(f"the API needs an http or https URL, not {base_url!r}")
        self._base_url = base_url.rstrip("/")
        self._headers = {"Accept": "application/json", **(headers or {})}
        self._timeout = timeout
        self._transport = transport or send
        if parts.scheme == "http" and "Authorization" in self._headers:
            _logger.warning("the token for %s is sent without encryption", self._base_url)

    @property
    def base_url(self) -> str:
        """The URL which the paths of the API are appended to."""
        return self._base_url

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str | int] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> ApiResponse:
        """Send a request and return its response.

        :param method: the HTTP method
        :param path: the path below the base URL, starting with a slash, or
            a full URL on the same server
        :param query: parameters to append to the URL
        :param body: an object to send as JSON
        :returns: the response
        :raises ApiError: if the server cannot be reached, answers with an
            error status, or the URL is on another server
        """
        url = path if "://" in path else self._base_url + path
        if not same_origin(url, self._base_url):
            raise ApiError(f"refusing to send a request for {self._base_url} to {url}")
        if query:
            url += ("&" if "?" in url else "?") + urlencode(query)
        headers = dict(self._headers)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        _logger.debug("%s %s", method, url)
        response = self._transport(method, url, headers, data, self._timeout)
        # A redirect which was not followed points to another server.
        if not 200 <= response.status < 300:
            detail = f": {response.message}" if response.message else ""
            raise ApiError(
                f"{method} {url} answered {response.status}{detail}", status=response.status
            )
        return response

    def paginate(
        self,
        path: str,
        *,
        query: Mapping[str, str | int] | None = None,
        values_key: str | None = None,
    ) -> Iterator[Any]:
        """Request a list and the pages which follow it.

        :param path: the path of the first page
        :param query: parameters of the first page
        :param values_key: the key of the items when a page is an object
            which names the next page under ``next``; without it a page is a
            list and the next page is named by the ``Link`` header
        :returns: the items of all pages
        :raises ApiError: as :meth:`request`, or if a page has another shape
        """
        url: str | None = path
        while url:
            response = self.request("GET", url, query=query)
            query = None
            page = response.body
            if values_key is None:
                items, url = page, response.next_link
            else:
                items = page.get(values_key) if isinstance(page, dict) else None
                url = page.get("next") if isinstance(page, dict) else None
            if not isinstance(items, list):
                raise ApiError(f"GET {path} did not answer with a list")
            yield from items
