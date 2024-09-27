import logging
import git

from .constants import DESTINATION_NAME, ORIGIN_NAME

_logger = logging.getLogger(__name__)


def push_origin_destination(
    sync_path: str,
) -> None:

    repo = git.Repo(sync_path)

    origin = None
    for remote in repo.remotes:
        if remote.name == ORIGIN_NAME:
            origin = remote
            break

    if origin is None:
        raise RuntimeError(f"{ORIGIN_NAME} remote does not exist")

    destination = None
    for remote in repo.remotes:
        if remote.name == DESTINATION_NAME:
            destination = remote
            break

    if destination is None:
        raise RuntimeError(f"{DESTINATION_NAME} remote does not exist")

    for branch in origin.refs:
        if branch.remote_head == "HEAD":
            continue

        _logger.info("%s", branch.name)

        origin.pull(f"{branch.remote_head}:{branch.remote_head}")

        destination.push(f"{branch.remote_head}:{branch.remote_head}")
