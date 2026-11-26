"""Removing credentials from text which is logged or reported."""

import re

_CREDENTIALS = re.compile(r"\b([A-Za-z][A-Za-z0-9+.-]*://)[^/\s:@]*:[^/\s@]+@")


def redact(text: str) -> str:
    """Hide the user name and password of the URLs in a text.

    The package never puts a token in a URL, but a user may give an address
    of the form ``https://user:password@example.com``.

    :param text: a command, a message or the output of git
    :returns: the text with ``***`` in place of the credentials
    """
    return _CREDENTIALS.sub(r"\1***@", text)
