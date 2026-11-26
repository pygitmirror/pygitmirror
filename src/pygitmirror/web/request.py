"""A request to the web application."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.cookies import CookieError, SimpleCookie
from typing import Any
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True)
class Request:
    """What the application needs to know about an HTTP request.

    It is independent of the server which received it, so that the
    application can be tested without a socket.

    :param method: the HTTP method, in upper case
    :param target: the path with its query, as sent
    :param headers: the headers, with their names in lower case
    :param body: the body
    """

    method: str
    target: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""

    @property
    def path(self) -> str:
        """The path, without the query."""
        return urlsplit(self.target).path

    def query(self, name: str) -> str | None:
        """Return the first value of a parameter of the query.

        :param name: the name of the parameter
        :returns: its value, or ``None`` if it is absent
        """
        values = parse_qs(urlsplit(self.target).query).get(name)
        return values[0] if values else None

    def cookie(self, name: str) -> str | None:
        """Return the value of a cookie.

        :param name: the name of the cookie
        :returns: its value, or ``None`` if it is absent or malformed
        """
        try:
            morsel = SimpleCookie(self.headers.get("cookie", "")).get(name)
        except CookieError:
            return None
        return morsel.value if morsel else None

    def json(self) -> dict[str, Any]:
        """Decode the body as a JSON object.

        :returns: the object
        :raises ValueError: if the body is not a JSON object
        """
        data = json.loads(self.body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("the body must be a JSON object")
        return data
