"""The files of the page."""

from importlib import resources

from pygitmirror.web.response import Response

_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
}


def _files() -> dict[str, tuple[bytes, str]]:
    """Read the files of the ``static`` folder, by name."""
    files = {}
    for entry in resources.files("pygitmirror.web").joinpath("static").iterdir():
        suffix = "." + entry.name.rsplit(".", 1)[-1]
        if entry.is_file() and suffix in _TYPES:
            files[entry.name] = (entry.read_bytes(), _TYPES[suffix])
    return files


#: The files by name, read once. A request can only name one of them, so no
#: path of a request ever reaches the file system.
FILES = _files()


def static(name: str) -> Response | None:
    """Return the response which serves a file of the page.

    :param name: the name of the file, without a folder
    :returns: the response, or ``None`` if there is no such file
    """
    found = FILES.get(name)
    if found is None:
        return None
    body, content_type = found
    # Fonts never change. Everything else is small and asked for again, so
    # that a browser never runs the scripts of an older version.
    cache = "public, max-age=604800" if name.endswith(".woff2") else "no-cache"
    return Response(200, body, content_type, {"Cache-Control": cache})
