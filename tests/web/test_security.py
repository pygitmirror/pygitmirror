import pytest

from pygitmirror.web import Request, WebApp
from pygitmirror.web._security import HEADERS, new_key
from tests.web.conftest import KEY, Client, body


def test_every_response_has_the_security_headers(client: Client) -> None:
    for response in (client.get("/"), client.get("/api/session"), client.get("/nothing")):
        for name, value in HEADERS.items():
            assert response.headers[name] == value
    policy = HEADERS["Content-Security-Policy"]
    assert "default-src 'none'" in policy and "unsafe" not in policy


def test_the_key_is_exchanged_for_a_cookie(client: Client) -> None:
    response = client.get(f"/?key={KEY}", key=False)
    assert response.status == 303 and response.headers["Location"] == "/"
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith(f"git_mirror_key={KEY};")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    assert client.get("/").status == 200
    assert b"<title>git-mirror</title>" in client.get("/").body


@pytest.mark.parametrize("target", ["/", "/?key=wrong", "/?key="])
def test_the_page_is_locked_without_the_key(client: Client, target: str) -> None:
    response = client.get(target, key=False)
    assert response.status == 401 and b"locked" in response.body
    assert "Set-Cookie" not in response.headers


def test_the_api_needs_the_key(client: Client) -> None:
    assert client.get("/api/session", key=False).status == 401
    assert client.post("/api/jobs", {}, cookie="git_mirror_key=wrong").status == 401
    assert client.post("/api/jobs", {}, cookie="not a cookie;;=").status == 401
    assert client.get("/api/session").status == 200


@pytest.mark.parametrize(
    "host", ["evil.example", "evil.example:47417", "", "127.0.0.1.evil.example"]
)
def test_other_host_names_are_refused(client: Client, host: str) -> None:
    assert client.get("/api/session", host=host).status == 403
    assert client.get("/healthz", host=host).status == 403


@pytest.mark.parametrize("host", ["localhost:47417", "LOCALHOST", "[::1]:47417", "127.0.0.1"])
def test_local_host_names_are_accepted(client: Client, host: str) -> None:
    assert client.get("/api/session", host=host).status == 200


def test_further_host_names_can_be_allowed(workdir: object) -> None:
    client = Client(WebApp(str(workdir), key=KEY, allowed_hosts=["Mirror.Example"]))
    assert client.get("/api/session", host="mirror.example:47417").status == 200


@pytest.mark.parametrize(
    "changes",
    [
        {"x-git-mirror": None},
        {"content-type": "text/plain"},
        {"content-type": None},
        {"origin": "https://evil.example"},
        {"origin": "http://127.0.0.1:9"},
    ],
)
def test_requests_of_other_sites_are_refused(client: Client, changes: dict[str, str]) -> None:
    response = client.post("/api/storage/clear", {}, **changes)
    assert response.status == 403
    assert "did not come from the page" in body(response)["error"]


def test_the_page_itself_may_post(client: Client) -> None:
    assert client.post("/api/storage/clear", {}, origin="http://127.0.0.1:47417").status == 200


def test_large_and_malformed_bodies(client: Client) -> None:
    assert client.post("/api/jobs", {"names": ["x" * 70_000]}).status == 413
    assert client.post("/api/jobs", ["not", "an", "object"]).status == 400


def test_methods_and_unknown_paths(client: Client) -> None:
    headers = {"host": "localhost", "cookie": f"git_mirror_key={KEY}"}
    assert client.app.handle(Request("DELETE", "/api/jobs/x", headers)).status == 405
    assert client.get("/api/unknown").status == 404
    assert client.get("/api/jobs/unknown").status == 404
    assert client.post("/api/unknown", {}).status == 404
    assert client.get("/etc/passwd").status == 404


def test_the_session_names_what_the_page_offers(client: Client) -> None:
    providers = body(client.get("/api/session"))["providers"]
    assert [item["name"] for item in providers] == ["gitea", "gitlab", "plain"]
    assert providers[1]["default_url"] == "https://gitlab.com" and providers[2]["has_api"] is False


def test_keys_are_long_and_random() -> None:
    assert len(new_key()) >= 40 and new_key() != new_key()
    assert WebApp("x").key != WebApp("x").key
