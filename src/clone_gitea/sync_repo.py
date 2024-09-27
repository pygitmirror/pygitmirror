import logging

_logger = logging.getLogger(__name__)


def sync_repo(org: str, repo: str) -> int:
    _logger.info("syncing %s/%s", org, repo)

    return 0
