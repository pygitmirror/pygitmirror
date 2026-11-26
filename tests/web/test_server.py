import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

from pygitmirror.cli._main import cache_folder
from pygitmirror.cli._parser import build_parser
from pygitmirror.web import DEFAULT_PORT, WebApp, make_server


@pytest.fixture
def address(tmp_path: Path) -> Iterator[str]:
    server = make_server(WebApp(tmp_path, key="k"), port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_the_server_answers(address: str) -> None:
    with urllib.request.urlopen(f"{address}/healthz", timeout=5) as response:
        assert response.read() == b"ok\n"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Server"].strip() == "git-mirror"
    request = urllib.request.Request(
        f"{address}/api/session", headers={"Cookie": "git_mirror_key=k"}
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        assert json.load(response)["providers"][0]["name"] == "gitea"


def test_the_server_refuses_without_the_key_and_large_bodies(address: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as raised:
        urllib.request.urlopen(f"{address}/api/session", timeout=5)
    assert raised.value.code == 401
    request = urllib.request.Request(
        f"{address}/api/jobs", data=b"x" * 70_000, headers={"Content-Type": "application/json"}
    )
    with pytest.raises(urllib.error.HTTPError) as raised:
        urllib.request.urlopen(request, timeout=5)
    assert raised.value.code == 413


def test_the_default_port_is_not_a_common_one() -> None:
    assert DEFAULT_PORT not in (80, 443, 3000, 4000, 5000, 8000, 8080, 8443, 8888, 9000)
    options = build_parser().parse_args(["serve"])
    assert (options.host, options.port, options.allow_host) == ("127.0.0.1", DEFAULT_PORT, [])
    assert options.sync_path is None


def test_the_default_folder_is_in_the_cache_of_the_user(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert cache_folder() == tmp_path / "git-mirror"
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert cache_folder() == Path.home() / ".cache" / "git-mirror"
