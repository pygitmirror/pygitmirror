import logging
import os
import sys
from typing import Optional, Tuple

from .sync_repo import sync_repo

_logger = logging.getLogger(__name__)

_dir = os.path.dirname(__file__)

_sync_path = os.path.abspath(os.path.join(_dir, "temp"))

_source_url = "ssh://git@gitea.girgis.xyz:32822"
_dest_url = "ssh://git@gitea.girgis.xyz:32822"

_repos = {
    "aero-app": (
        "fullstack",
        "web-client",
        "web-middleware",
        "devops",
        "evaluation",
        "protos",
    ),
    "finance-simulations": (),
    "girgis-local": (),
    "girgis-phd": (),
    "idiscoveryinc": (),
    "legacy-aero": (),
    "legacy-aero-ti": (),
    "legacy-aero-vb": (),
    "legacy-jobs": (),
    "legacy-vb": (),
    "reactjs": (),
    "rust-by-example": (),
    "rust-infrastructure": (),
    "rust-tests": (),
    "selfcloudme": (),
    "the-rust-prog-lang": (),
    "tube-recorder": (),
}


def main(args: Optional[Tuple[str, ...]] = None) -> int:

    logging.basicConfig(level=logging.INFO)

    _logger.info("using sync path %s", _sync_path)

    for org, repos in _repos.items():
        for repo in repos:
            if sync_repo(org, repo) != 0:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
