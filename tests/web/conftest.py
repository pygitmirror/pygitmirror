import json
from pathlib import Path
from typing import Any

import pytest

from pygitmirror import Git
from pygitmirror.web import Request, Response, WebApp

KEY = "test-key"
HOST = "127.0.0.1:47417"


class Client:
    """Sends requests to an application as the page does, without a socket."""

    def __init__(self, app: WebApp) -> None:
        self.app = app

    def get(self, target: str, *, key: bool = True, host: str = HOST) -> Response:
        headers = {"host": host}
        if key:
            headers["cookie"] = f"git_mirror_key={KEY}"
        return self.app.handle(Request("GET", target, headers))

    def post(self, target: str, data: Any, **changes: str | None) -> Response:
        headers: dict[str, str | None] = {
            "host": HOST,
            "cookie": f"git_mirror_key={KEY}",
            "content-type": "application/json",
            "x-git-mirror": "1",
            **changes,
        }
        sent = {name: value for name, value in headers.items() if value is not None}
        return self.app.handle(Request("POST", target, sent, json.dumps(data).encode()))


def body(response: Response) -> Any:
    return json.loads(response.body)


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    return tmp_path / "mirrors"


@pytest.fixture
def client(workdir: Path) -> Client:
    # Local folders stand in for servers in the tests, so git may read them.
    return Client(WebApp(workdir, key=KEY, git=Git()))
