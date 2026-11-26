#!/usr/bin/env python3
"""Check that the built distributions have the version of a release tag.

The version of the package is read from the git tag when it is built, so a
release tagged ``v1.2.3`` must give ``pygitmirror-1.2.3.tar.gz`` and its
wheel::

    python .github/scripts/check_release_version.py v1.2.3

It needs the standard library only.
"""

import argparse
import sys
from pathlib import Path

#: Name of the distributions, with the version left out.
PACKAGE = "pygitmirror"


def expected_files(tag: str) -> list[str]:
    """Return the names of the distributions of a release tag.

    :param tag: the tag of the release, with or without a leading ``v``
    :returns: the names of the source distribution and of the wheel
    """
    version = tag.removeprefix("v")
    return [f"{PACKAGE}-{version}.tar.gz", f"{PACKAGE}-{version}-py3-none-any.whl"]


def main() -> int:
    """Check the distributions and return the exit status."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("tag", help="the tag of the release, such as v1.2.3")
    parser.add_argument(
        "--dist", type=Path, default=Path("dist"), help="the folder of the distributions"
    )
    args = parser.parse_args()

    if not args.tag.removeprefix("v"):
        print("error: the tag is empty.", file=sys.stderr)
        return 2

    found = sorted(path.name for path in args.dist.glob("*")) if args.dist.is_dir() else []
    print(f"Distributions in {args.dist}: {', '.join(found) or 'none'}")

    missing = [name for name in expected_files(args.tag) if name not in found]
    if missing:
        print(
            f"error: {', '.join(missing)} missing; "
            f"the tag {args.tag} does not match the built version.",
            file=sys.stderr,
        )
        return 1

    print(f"The distributions have the version of the tag {args.tag}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
