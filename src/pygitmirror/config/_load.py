"""Merging the settings file and the command line into settings."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pygitmirror.config._json import read_json
from pygitmirror.config.host_settings import HostSettings
from pygitmirror.config.settings import Settings
from pygitmirror.errors import ConfigError
from pygitmirror.mirror import Operation

#: In a settings file, in place of the names: all repositories of the owner.
ALL = "*"

_HOST_KEYS = ("provider", "url", "git_url", "username", "token_env")
_FILE_KEYS = {
    "sync_path", "source", "destination", "source_url", "destination_url",
    "repos", "owners", "prune", "archive_source",
}  # fmt: skip


def _text(value: Any, what: str) -> str:
    """Check that a value is a string which is not empty."""
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{what} must be a string which is not empty")
    return value


def _flag(value: Any, what: str) -> bool:
    """Check that a value is true or false."""
    if not isinstance(value, bool):
        raise ConfigError(f"{what} must be true or false")
    return value


def _host(role: str, data: Mapping[str, Any], options: Mapping[str, Any]) -> HostSettings:
    """Merge the settings of a host; the command line wins."""
    section = data.get(role, {})
    if not isinstance(section, dict) or section.keys() - set(_HOST_KEYS):
        raise ConfigError(f"{role} must be an object with keys among {', '.join(_HOST_KEYS)}")
    values = {key: _text(value, f"{role}.{key}") for key, value in section.items()}
    # The key of the files written for the first versions of the package.
    if f"{role}_url" in data:
        values.setdefault("url", _text(data[f"{role}_url"], f"{role}_url"))
    for key in _HOST_KEYS:
        option = role if key == "provider" else f"{role}_{key}"
        if options.get(option) is not None:
            values[key] = options[option]
    return HostSettings(**values)


def _repos(data: Mapping[str, Any]) -> dict[str, tuple[str, ...] | None]:
    """Read the repositories of a settings file."""
    section = data.get("repos", {})
    if not isinstance(section, dict):
        raise ConfigError("repos must be an object of names by owner")
    repos: dict[str, tuple[str, ...] | None] = {}
    for owner, names in section.items():
        if names == ALL:
            repos[owner] = None
        elif isinstance(names, list) and names:
            repos[owner] = tuple(_text(name, f"a name of repos.{owner}") for name in names)
        else:
            raise ConfigError(f'repos.{owner} must be a list of names or "{ALL}"')
    return repos


def _owners(data: Mapping[str, Any]) -> dict[str, str]:
    """Read the mapping of owners of a settings file."""
    section = data.get("owners", {})
    if not isinstance(section, dict):
        raise ConfigError("owners must be an object of destination owners by source owner")
    return {owner: _text(to, f"owners.{owner}") for owner, to in section.items()}


def load_settings(operation: Operation, options: Mapping[str, Any]) -> Settings:
    """Create the settings of a run.

    :param operation: the operation which was asked for
    :param options: the options given on the command line, by the name of
        their attribute; one which was not given is absent or ``None``. A
        ``config`` option names the settings file.
    :returns: the settings; what the command line says wins over the file
    :raises ConfigError: if the file or an option is invalid, or no
        repository is named
    """
    data = read_json(Path(options["config"])) if options.get("config") else {}
    if unknown := data.keys() - _FILE_KEYS:
        raise ConfigError(f"unknown settings: {', '.join(sorted(unknown))}")

    repos, owners = _repos(data), _owners(data)
    org, names = options.get("org"), options.get("repo")
    if names and options.get("all"):
        raise ConfigError("give the names of the repositories or ask for all, not both")
    if org:
        if not names and not options.get("all"):
            raise ConfigError("name the repositories of the organization, or ask for all")
        repos = {org: tuple(names) if names else None}
        if options.get("destination_org"):
            owners[org] = options["destination_org"]
    elif names or options.get("all") or options.get("destination_org"):
        raise ConfigError("the organization of the repositories is missing")
    if not repos:
        raise ConfigError("no repositories: name them in the settings file or on the command line")

    prune = _flag(data.get("prune", True), "prune")
    archive_source = _flag(data.get("archive_source", False), "archive_source")
    sync_path = options.get("sync_path") or data.get("sync_path") or "."
    return Settings(
        operation=operation,
        source=_host("source", data, options),
        destination=_host("destination", data, options),
        repos=repos,
        owners=owners,
        sync_path=Path(_text(sync_path, "sync_path")).expanduser(),
        prune=prune and not options.get("no_prune"),
        archive_source=archive_source or bool(options.get("archive_source")),
        dry_run=bool(options.get("dry_run")),
    )
