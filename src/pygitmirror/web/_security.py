"""The checks every request passes, and the headers every response gets."""

import hmac
import secrets

from pygitmirror.web.request import Request
from pygitmirror.web.response import Response

#: The cookie which holds the access key after the first visit.
COOKIE = "git_mirror_key"
#: The header which a page of another site cannot send without asking first.
MARKER = "x-git-mirror"
#: The largest body of a request, in bytes.
MAX_BODY = 64 * 1024

#: Sent with every response. Scripts, styles and fonts load from the
#: application only, nothing may frame it, and nothing leaves in a referrer.
HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def new_key() -> str:
    """Create an access key which cannot be guessed.

    :returns: 32 random bytes as text which is safe in a URL
    """
    return secrets.token_urlsafe(32)


def same_key(given: str | None, key: str) -> bool:
    """Compare an access key in constant time.

    :param given: what the request presented
    :param key: the key of the application
    :returns: whether they are equal
    """
    return given is not None and hmac.compare_digest(given.encode(), key.encode())


def host_allowed(request: Request, allowed: frozenset[str]) -> bool:
    """Tell whether a request names the application as its host.

    A page of another site can make a browser resolve its own name to this
    machine. Its requests then carry that name, which is refused here.

    :param request: the request
    :param allowed: the host names the application answers to, in lower case
    :returns: whether the ``Host`` header, without its port, is one of them
    """
    host = request.headers.get("host", "").lower()
    name = host.rsplit(":", 1)[0] if not host.endswith("]") else host
    return name in allowed


def cross_site(request: Request) -> bool:
    """Tell whether a request which changes something comes from another site.

    :param request: a request to the API
    :returns: ``True`` if it lacks the marker header, is not JSON, or has an
        ``Origin`` other than the application
    """
    if request.headers.get(MARKER) != "1":
        return True
    if not request.headers.get("content-type", "").startswith("application/json"):
        return True
    origin = request.headers.get("origin")
    host = request.headers.get("host", "")
    return origin is not None and origin.split("://", 1)[-1] != host


def key_cookie(key: str) -> str:
    """Return the ``Set-Cookie`` header which stores the access key.

    :param key: the access key
    :returns: a cookie which scripts cannot read and other sites cannot send
    """
    return f"{COOKIE}={key}; Path=/; HttpOnly; SameSite=Strict"


def harden(response: Response) -> Response:
    """Add the security headers to a response.

    :param response: the response of a route
    :returns: the response with the headers of :data:`HEADERS`
    """
    return Response(
        response.status,
        response.body,
        response.content_type,
        {**HEADERS, **response.headers},
    )
