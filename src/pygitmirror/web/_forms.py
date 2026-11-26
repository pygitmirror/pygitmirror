"""Reading what the page sends: hosts, repositories and options."""

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from pygitmirror.errors import ConfigError
from pygitmirror.hosts import PROVIDERS, Host, make_host
from pygitmirror.mirror import Operation
from pygitmirror.repository_ref import RepositoryRef

#: The providers the page offers, in its order. Others are added as they
#: are verified against a real server; see the roadmap.
OFFERED = ("gitea", "gitlab", "plain")

#: The most repositories one job may name.
MAX_REPOSITORIES = 500


def text(data: Mapping[str, Any], key: str, *, required: bool = False) -> str | None:
    """Read a string field.

    :param data: the object of the request
    :param key: the name of the field
    :param required: whether it must be present and not empty
    :returns: the stripped value, or ``None`` if it is empty or absent
    :raises ConfigError: if it is not a string, too long, or missing
    """
    value = data.get(key)
    if value is None or value == "":
        if required:
            raise ConfigError(f"{key} is required")
        return None
    if not isinstance(value, str) or len(value) > 2000:
        raise ConfigError(f"{key} must be a short text")
    return value.strip() or None


def flag(data: Mapping[str, Any], key: str) -> bool:
    """Read a field which is true or false.

    :param data: the object of the request
    :param key: the name of the field
    :returns: its value, ``False`` if it is absent
    :raises ConfigError: if it is neither
    """
    value = data.get(key, False)
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be true or false")
    return value


def _check_url(url: str, what: str, schemes: tuple[str, ...]) -> None:
    """Refuse an address with another scheme, without a host, or with credentials."""
    parts = urlsplit(url)
    if parts.scheme not in schemes or not parts.hostname:
        raise ConfigError(f"the {what} must start with {' or '.join(s + '://' for s in schemes)}")
    if parts.password or (parts.username and parts.scheme != "ssh"):
        raise ConfigError(f"the {what} must not contain credentials; use the token field")


def host(data: Any, role: str) -> Host:
    """Create a host from what the page sent.

    :param data: the object which describes the host
    :param role: ``source`` or ``destination``, for messages
    :returns: the host
    :raises ConfigError: if a field is invalid or the provider is not offered
    """
    if not isinstance(data, dict):
        raise ConfigError(f"the {role} is missing")
    provider = text(data, "provider", required=True)
    if provider not in OFFERED or provider not in PROVIDERS:
        raise ConfigError(f"the {role} must be one of {', '.join(OFFERED)}")
    # A service with a public server needs no address.
    url = text(data, "url", required=PROVIDERS[provider].default_url is None)
    git_url = text(data, "git_url")
    if url:
        _check_url(url, f"address of the {role}", ("http", "https"))
    if git_url:
        _check_url(git_url, f"git address of the {role}", ("http", "https", "ssh"))
    return make_host(
        provider,
        url=url,
        git_url=git_url,
        token=text(data, "token"),
        username=text(data, "username"),
    )


def repositories(data: Mapping[str, Any]) -> list[RepositoryRef]:
    """Read the repositories of a job.

    :param data: the object of the request, with ``owner`` and ``names``
    :returns: the repositories at the source
    :raises ConfigError: if the owner or a name is invalid, or there are
        none or too many
    """
    owner = text(data, "owner", required=True) or ""
    names = data.get("names")
    if not isinstance(names, list) or not names or len(names) > MAX_REPOSITORIES:
        raise ConfigError(f"name between 1 and {MAX_REPOSITORIES} repositories")
    if not all(isinstance(name, str) for name in names):
        raise ConfigError("the names of the repositories must be text")
    return [RepositoryRef(owner, name.strip()) for name in names]


def operation(data: Mapping[str, Any]) -> Operation:
    """Read the operation of a job.

    :param data: the object of the request
    :returns: the operation
    :raises ConfigError: if it is not one of the three
    """
    try:
        return Operation(text(data, "operation", required=True) or "")
    except ValueError:
        choices = ", ".join(item.value for item in Operation)
        raise ConfigError(f"the operation must be one of {choices}") from None
