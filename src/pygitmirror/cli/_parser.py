"""The options of the command line."""

from argparse import ArgumentParser

from pygitmirror import PROVIDERS, __version__
from pygitmirror.mirror import Operation

_HELP = {
    Operation.CLONE: "copy what the destination does not have, without overwriting anything",
    Operation.SYNC: "make the destination equal to the source, overwriting what differs",
    Operation.MIGRATE: "clone, check the copy and optionally archive the source",
}


def _add_host(parser: ArgumentParser, role: str) -> None:
    """Add the options which describe the source or the destination."""
    group = parser.add_argument_group(f"{role} host")
    group.add_argument(
        f"--{role}",
        choices=sorted(PROVIDERS),
        metavar="PROVIDER",
        help=f"service of the {role}: %(choices)s (default: plain, a git server without an API)",
    )
    group.add_argument(
        f"--{role}-url",
        f"--{role}_url",
        metavar="URL",
        help="address of the server; not needed for github.com, gitlab.com and bitbucket.org",
    )
    group.add_argument(
        f"--{role}-git-url",
        metavar="URL",
        help="address for git when it differs, such as ssh://git@github.com",
    )
    group.add_argument(
        f"--{role}-username", metavar="NAME", help="user name sent with the token, if needed"
    )
    group.add_argument(
        f"--{role}-token-env",
        metavar="VARIABLE",
        help=f"environment variable of the token (default: GIT_MIRROR_{role.upper()}_TOKEN)",
    )


def _common() -> ArgumentParser:
    """Create the options which every command has."""
    # A default of None tells an option which was not given from one which
    # was, so that it does not override the settings file.
    parser = ArgumentParser(add_help=False, argument_default=None)
    parser.add_argument(
        "--config", "--json", metavar="FILE", help="settings file in JSON; options override it"
    )
    _add_host(parser, "source")
    _add_host(parser, "destination")
    group = parser.add_argument_group("repositories")
    group.add_argument("--org", metavar="OWNER", help="owner of the repositories at the source")
    group.add_argument("--repo", nargs="+", metavar="NAME", help="names of the repositories")
    group.add_argument(
        "--all", action="store_true", default=None, help="all repositories of the owner"
    )
    group.add_argument(
        "--destination-org", metavar="OWNER", help="owner at the destination, if not the same"
    )
    parser.add_argument(
        "--sync-path",
        "--sync_path",
        metavar="FOLDER",
        help="folder of the local mirrors (default: the current folder)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="report what would be done without changing anything",
    )
    parser.add_argument(
        "--log",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="log level (default: %(default)s)",
    )
    return parser


def build_parser() -> ArgumentParser:
    """Create the parser of the ``git-mirror`` command.

    :returns: a parser with one command per operation
    """
    parser = ArgumentParser(
        prog="git-mirror",
        description="Clone, sync and migrate git repositories between hosts.",
        epilog="Tokens are read from the environment, never from options or the settings file.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="operation", required=True, metavar="COMMAND")
    common = _common()
    for operation in Operation:
        command = commands.add_parser(
            operation.value, parents=[common], help=_HELP[operation], description=_HELP[operation]
        )
        if operation is Operation.SYNC:
            command.add_argument(
                "--no-prune",
                action="store_true",
                default=None,
                help="keep the branches and tags which the source does not have",
            )
        if operation is Operation.MIGRATE:
            command.add_argument(
                "--archive-source",
                action="store_true",
                default=None,
                help="make the source read-only once the copy is checked",
            )
    return parser
