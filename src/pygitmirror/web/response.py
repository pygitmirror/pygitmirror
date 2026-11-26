"""A response of the web application."""

import json
from dataclasses import dataclass, field
from typing import Any, Self


@dataclass(frozen=True)
class Response:
    """The status, headers and body which answer a request.

    :param status: the HTTP status
    :param body: the body
    :param content_type: the media type of the body
    :param headers: further headers
    """

    status: int = 200
    body: bytes = b""
    content_type: str = "text/plain; charset=utf-8"
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def json(cls, data: Any, status: int = 200) -> Self:
        """Create a response with a JSON body, which is never cached.

        :param data: what to encode
        :param status: the HTTP status
        :returns: the response
        """
        body = json.dumps(data, separators=(",", ":")).encode()
        return cls(status, body, "application/json", {"Cache-Control": "no-store"})

    @classmethod
    def error(cls, status: int, message: str) -> Self:
        """Create a response which reports an error as JSON.

        :param status: the HTTP status
        :param message: what went wrong, shown to the user
        :returns: the response
        """
        return cls.json({"error": message}, status)
