"""Sending HTTP requests with the standard library."""

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from http.client import HTTPMessage
from typing import IO, Any
from urllib.parse import urlsplit

from pygitmirror.errors import ApiError
from pygitmirror.hosts.api_response import ApiResponse

#: A function which sends a request and returns the response, whatever its
#: status: ``transport(method, url, headers, data, timeout)``. Tests replace
#: it to answer without a network.
Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], ApiResponse]


def same_origin(url: str, other: str) -> bool:
    """Tell whether two URLs have the same scheme, host and port.

    :param url: a URL
    :param other: another URL
    :returns: whether a token meant for one may be sent to the other
    """
    first, second = urlsplit(url), urlsplit(other)
    return (first.scheme, first.netloc) == (second.scheme, second.netloc)


class _SameOriginRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to the server which was asked.

    ``urllib`` sends the headers of a request, the token included, to
    wherever a redirect points.
    """

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        if not same_origin(req.full_url, newurl):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_SameOriginRedirects)


def _decode(data: bytes) -> Any:
    """Decode a response body as JSON, or as text when it is not JSON."""
    if not data.strip():
        return None
    text = data.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        return text


def send(
    method: str, url: str, headers: Mapping[str, str], data: bytes | None, timeout: float
) -> ApiResponse:
    """Send a request with ``urllib`` and return the response.

    :param method: the HTTP method
    :param url: the URL, which the caller has checked to be HTTP or HTTPS
    :param headers: the headers of the request
    :param data: the encoded body, if any
    :param timeout: the number of seconds to wait for the server
    :returns: the response, also when its status is an error
    :raises ApiError: if the server cannot be reached
    """
    request = urllib.request.Request(  # noqa: S310 - the scheme is checked by ApiClient
        url, data=data, headers=dict(headers), method=method
    )
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            status, received, content = response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        status, received, content = error.code, error.headers, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise ApiError(f"{method} {url} failed: {reason}") from error
    lowered = {name.lower(): value for name, value in received.items()}
    return ApiResponse(status, lowered, _decode(content))
