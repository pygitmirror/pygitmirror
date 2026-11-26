import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pygitmirror import ApiError, ConfigError
from pygitmirror.hosts import ApiClient, ApiResponse
from tests.helpers import FakeTransport

BASE = "https://api.example.com/v1"


def test_request_sends_json_and_headers() -> None:
    transport = FakeTransport({("POST", f"{BASE}/things?a=1"): {"id": 7}})
    client = ApiClient(BASE + "/", {"Authorization": "Bearer t"}, transport=transport)
    response = client.request("POST", "/things", query={"a": 1}, body={"name": "x"})
    assert response.body == {"id": 7}
    assert transport.requests == [("POST", f"{BASE}/things?a=1", {"name": "x"})]
    assert transport.headers["Authorization"] == "Bearer t"
    assert transport.headers["Content-Type"] == "application/json"


@pytest.mark.parametrize(
    "body",
    [{"message": "nope"}, {"error": {"message": "nope"}}, {"error": "nope"}, "nope"],
)
def test_error_status_raises_with_the_message(body: object) -> None:
    transport = FakeTransport({("GET", f"{BASE}/x"): ApiResponse(403, {}, body)})
    with pytest.raises(ApiError, match="403: nope") as raised:
        ApiClient(BASE, transport=transport).request("GET", "/x")
    assert raised.value.status == 403


def test_paginate_follows_link_headers() -> None:
    link = {"link": f'<{BASE}/x?page=2>; rel="next", <{BASE}/x?page=9>; rel="last"'}
    transport = FakeTransport(
        {
            ("GET", f"{BASE}/x?per_page=2"): ApiResponse(200, link, [1, 2]),
            ("GET", f"{BASE}/x?page=2"): [3],
        }
    )
    client = ApiClient(BASE, transport=transport)
    assert list(client.paginate("/x", query={"per_page": 2})) == [1, 2, 3]


def test_paginate_follows_next_of_the_body() -> None:
    transport = FakeTransport(
        {
            ("GET", f"{BASE}/x"): {"values": [1], "next": f"{BASE}/x?page=2"},
            ("GET", f"{BASE}/x?page=2"): {"values": [2]},
        }
    )
    assert list(ApiClient(BASE, transport=transport).paginate("/x", values_key="values")) == [1, 2]


def test_paginate_rejects_other_shapes() -> None:
    transport = FakeTransport({("GET", f"{BASE}/x"): {"message": "not a list"}})
    with pytest.raises(ApiError):
        list(ApiClient(BASE, transport=transport).paginate("/x"))


def test_the_token_stays_on_its_server() -> None:
    link = {"link": '<https://evil.example.net/x?page=2>; rel="next"'}
    transport = FakeTransport({("GET", f"{BASE}/x"): ApiResponse(200, link, [1])})
    client = ApiClient(BASE, {"Authorization": "Bearer t"}, transport=transport)
    with pytest.raises(ApiError, match="refusing"):
        list(client.paginate("/x"))
    assert len(transport.requests) == 1


@pytest.mark.parametrize("url", ["ftp://example.com", "example.com", "file:///etc"])
def test_only_http(url: str) -> None:
    with pytest.raises(ConfigError):
        ApiClient(url)


class _Handler(BaseHTTPRequestHandler):
    seen: list[str] = []
    port = 0

    def do_GET(self) -> None:
        type(self).seen.append(self.headers.get("Authorization", ""))
        if self.path == "/away":
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{type(self).port}/json")
            self.end_headers()
        elif self.path == "/json":
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Link", '<http://x/y>; rel="next"')
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "9")
            self.end_headers()
            self.wfile.write(b"not found")

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def server() -> Iterator[str]:
    _Handler.seen = []
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    _Handler.port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def test_urllib_transport(server: str) -> None:
    client = ApiClient(server, {"Authorization": "Bearer t"})
    response = client.request("GET", "/json")
    assert response.body == {"ok": True}
    assert response.next_link == "http://x/y"
    with pytest.raises(ApiError, match="404: not found"):
        client.request("GET", "/missing")


def test_urllib_transport_does_not_follow_a_redirect_to_another_server(server: str) -> None:
    # localhost and 127.0.0.1 are the same server under two names.
    client = ApiClient(server, {"Authorization": "Bearer t"})
    with pytest.raises(ApiError, match="302"):
        client.request("GET", "/away")
    assert _Handler.seen == ["Bearer t"]


def test_unreachable_server() -> None:
    with pytest.raises(ApiError) as raised:
        ApiClient("http://127.0.0.1:9", timeout=2).request("GET", "/x")
    assert raised.value.status == 0
