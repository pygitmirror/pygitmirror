import time
from pathlib import Path
from typing import Any

import pytest

from pygitmirror import PlainHost
from pygitmirror.web import _forms
from tests.helpers import Workshop, git, refs
from tests.web.conftest import Client, body


@pytest.fixture
def servers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Workshop, Path]:
    """Two folders which stand in for servers, whatever address the page sends."""
    shop = Workshop(tmp_path, tmp_path / "source" / "org" / "repo")
    destination = tmp_path / "destination" / "org" / "repo"
    destination.mkdir(parents=True)
    git("init", "-q", "--bare", cwd=destination)

    def host(data: Any, role: str) -> PlainHost:
        return PlainHost(url=str(tmp_path / role), token=(data or {}).get("token"))

    monkeypatch.setattr(_forms, "host", host)
    return shop, destination


def _job(client: Client, **changes: Any) -> dict[str, Any]:
    data = {
        "operation": "clone",
        "source": {"token": "source-secret"},
        "destination": {"token": "destination-secret"},
        "owner": "org",
        "names": ["repo"],
        "keep_copies": True,
        **changes,
    }
    started = client.post("/api/jobs", data)
    assert started.status == 202, started.body
    identifier = body(started)["id"]
    for _ in range(200):
        job: dict[str, Any] = body(client.get(f"/api/jobs/{identifier}"))
        if job["state"] == "done":
            return job
        time.sleep(0.05)
    raise AssertionError("the job did not finish")


def test_a_job_copies_and_reports(client: Client, servers: tuple[Workshop, Path]) -> None:
    shop, destination = servers
    job = _job(client)
    assert refs(destination) == refs(shop.bare)
    assert job["repositories"] == ["org/repo"] and job["error"] is None
    (result,) = job["results"]
    assert result["ok"] and result["changed"] and result["plan"]["create"] == ["refs/heads/main"]
    assert result["summary"] == "clone org/repo -> org/repo: 1 created, 0 updated"
    assert "secret" not in str(job)


def test_a_preview_changes_nothing(client: Client, servers: tuple[Workshop, Path]) -> None:
    _, destination = servers
    job = _job(client, operation="sync", dry_run=True)
    assert job["results"][0]["dry_run"] and refs(destination) == {}


def test_failures_are_reported_per_repository(
    client: Client, servers: tuple[Workshop, Path]
) -> None:
    job = _job(client, names=["missing", "repo"])
    assert [result["ok"] for result in job["results"]] == [False, True]
    assert "does not appear to be a git repository" in job["results"][0]["error"]


def test_copies_are_kept_or_deleted(
    client: Client, servers: tuple[Workshop, Path], workdir: Path
) -> None:
    _job(client, keep_copies=False)
    assert not (workdir / "org" / "repo.git").exists()
    servers[0].commit("second")
    _job(client)
    assert (workdir / "org" / "repo.git" / "HEAD").is_file()
    storage = body(client.get("/api/storage"))
    assert storage["mirrors"] == 1 and storage["used"] > 0 and storage["free"] > 0
    assert body(client.post("/api/storage/clear", {})) == {"deleted": 1}
    assert not (workdir / "org").exists() and workdir.is_dir()


def test_invalid_jobs_are_refused(client: Client, servers: tuple[Workshop, Path]) -> None:
    invalid: list[dict[str, Any]] = [
        {"operation": "erase"},
        {"names": []},
        {"destination_owner": "../x"},
    ]
    for changes in invalid:
        data = {"operation": "clone", "owner": "org", "names": ["repo"], **changes}
        response = client.post("/api/jobs", data)
        assert response.status == 400 and body(response)["error"]
