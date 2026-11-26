"""Reading the references of a repository on a server."""

from collections.abc import Mapping

from pygitmirror.git.git import Git

#: The kinds of references which are mirrored: branches and tags. Hosts keep
#: others of their own, such as those of pull requests, and refuse them.
MIRRORED = ("refs/heads/", "refs/tags/")

_BRANCHES = "refs/heads/"


def parse_refs(output: str) -> dict[str, str]:
    """Read the lines of object and reference names which git prints.

    :param output: lines of an object name, white space and a reference name
    :returns: the object names of the branches and tags by reference name
    """
    refs = {}
    for line in output.splitlines():
        sha, _, name = line.partition("\t") if "\t" in line else line.partition(" ")
        if name.startswith(MIRRORED):
            refs[name.strip()] = sha.strip()
    return refs


def list_refs(git: Git, url: str, config: Mapping[str, str] | None = None) -> dict[str, str]:
    """Read the branches and tags of a repository on a server.

    :param git: the runner of git commands
    :param url: the URL of the repository
    :param config: the configuration which authenticates
    :returns: the object names by reference name; empty for an empty
        repository
    :raises GitError: if the repository cannot be read
    """
    return parse_refs(git.run("ls-remote", "--refs", url, config=config))


def default_branch(git: Git, url: str, config: Mapping[str, str] | None = None) -> str | None:
    """Read the name of the default branch of a repository on a server.

    :param git: the runner of git commands
    :param url: the URL of the repository
    :param config: the configuration which authenticates
    :returns: the branch which ``HEAD`` points to, or ``None`` when the
        server does not say, as for an empty repository
    :raises GitError: if the repository cannot be read
    """
    for line in git.run("ls-remote", "--symref", url, "HEAD", config=config).splitlines():
        target, _, name = line.partition("\t")
        if name == "HEAD" and target.startswith(f"ref: {_BRANCHES}"):
            return target.removeprefix(f"ref: {_BRANCHES}")
    return None
