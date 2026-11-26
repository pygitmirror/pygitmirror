#!/usr/bin/env python3
"""Check that the image of the page starts, answers and is locked down.

Runs a container from the image, waits for it to answer, and checks that it
does not run as root and that the page is locked without the access key::

    python .github/scripts/check_image.py git-mirror:dev

It needs Docker and the standard library only.
"""

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request

#: A port which is unlikely to be taken on the machine which runs the check.
PORT = 47418


def docker(*args: str) -> str:
    """Run a docker command and return what it printed."""
    result = subprocess.run(["docker", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def status(path: str) -> int:
    """Return the HTTP status of a path of the page, 0 if it does not answer."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=2) as response:
            return int(response.status)
    except urllib.error.HTTPError as error:
        return error.code
    except OSError:
        return 0


def main() -> int:
    """Check the image and return the exit status."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("image", help="the name of the image, such as git-mirror:dev")
    image = parser.parse_args().image

    size = int(docker("image", "inspect", "--format", "{{.Size}}", image))
    print(f"{image} is {size / 1e6:.0f} MB")
    container = docker(
        "run", "--detach", "--rm", "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",
        "--publish", f"127.0.0.1:{PORT}:47417", image,
    )  # fmt: skip
    try:
        for _ in range(40):
            if status("/healthz") == 200:
                break
            time.sleep(0.5)
        checks = {
            "the page answers": status("/healthz") == 200,
            "the page is locked without the key": status("/") == 401,
            "the API is locked without the key": status("/api/session") == 401,
            "it does not run as root": docker("exec", container, "id", "-u") != "0",
            "git is installed": docker("exec", container, "git", "--version").startswith("git"),
        }
    finally:
        docker("stop", container)
    for name, passed in checks.items():
        print(f"{'ok  ' if passed else 'FAIL'} {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
