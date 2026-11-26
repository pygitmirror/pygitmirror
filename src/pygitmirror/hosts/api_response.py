"""The response to a request to the API of a host."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

_NEXT_LINK = re.compile(r'<([^>]+)>\s*;[^,]*\brel="?next"?')


@dataclass(frozen=True)
class ApiResponse:
    """The status, headers and decoded body of an HTTP response.

    :param status: the HTTP status
    :param headers: the headers, with their names in lower case
    :param body: the decoded JSON body, the text of a body which is not
        JSON, or ``None`` for an empty one
    """

    status: int
    headers: Mapping[str, str] = field(default_factory=dict)
    body: Any = None

    @property
    def next_link(self) -> str | None:
        """The URL of the next page named by the ``Link`` header, if any."""
        match = _NEXT_LINK.search(self.headers.get("link", ""))
        return match.group(1) if match else None

    @property
    def message(self) -> str:
        """The error message of the body, in the forms the hosts use."""
        body = self.body
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict):
                error = error.get("message")
            body = body.get("message") or error or body
        return str(body) if body else ""
