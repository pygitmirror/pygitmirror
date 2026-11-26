"""Reading a settings file."""

import json
from pathlib import Path
from typing import Any

from pygitmirror.errors import ConfigError


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file which may have comment lines.

    A line whose first characters, after white space, are ``//`` is a
    comment. This is the only extension of JSON which is accepted.

    :param path: the path of the file
    :returns: the object of the file
    :raises ConfigError: if the file cannot be read, is not valid JSON or
        does not hold an object
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ConfigError(f"cannot read {path}: {error.strerror}") from error
    # A comment becomes an empty line, so that errors name the right line.
    text = "\n".join("" if line.lstrip().startswith("//") else line for line in lines)
    try:
        data = json.loads(text)
    except ValueError as error:
        raise ConfigError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must hold an object")
    return data
