import logging
import git
import os

_logger = logging.getLogger(__name__)


def _clone_repo(
    sync_path: str,
    source_url: str,
) -> None:
    _logger.info(
        "cloning new repo from %s to %s",
        source_url,
        sync_path,
    )

    git.Repo.clone_from(source_url, sync_path)


def _fetch_repo() -> None:
    _logger.info("fetching existing repo")


def sync_repo(
    sync_path: str,
    source_url: str,
    destination_url: str,
    org: str,
    repo: str,
) -> int:
    _logger.info("syncing %s/%s", org, repo)

    repo_sync_path = os.path.join(sync_path, org, repo)
    repo_source_url = f"{source_url}/{org}/{repo}"
    repo_destination_url = f"{destination_url}/{org}/{repo}"

    _logger.info("repo_sync_path: %s", repo_sync_path)
    _logger.info("repo_source_url: %s", repo_source_url)
    _logger.info("repo_destination_url: %s", repo_destination_url)

    if os.path.isdir(repo_sync_path):
        _fetch_repo()
    else:
        _clone_repo(repo_sync_path, repo_source_url)

    return 0
