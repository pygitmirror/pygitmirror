import pytest

from pygitmirror import ConfigError, EmptySourceError, Operation
from tests.helpers import git, refs
from tests.mirror.conftest import World


def _rewrite(world: World) -> None:
    """Rewrite main, delete dev and add a tag at the source."""
    git("checkout", "-q", "main", cwd=world.shop.work)
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=world.shop.work)
    git("branch", "-q", "-D", "dev", cwd=world.shop.work)
    git("tag", "v2", cwd=world.shop.work)
    git("update-ref", "-d", "refs/heads/dev", cwd=world.shop.bare)
    world.shop.publish()


def test_sync_overwrites_and_deletes(world: World) -> None:
    world.shop.commit("on dev", branch="dev")
    mirror = world.to_plain()
    assert mirror.sync("org/repo").plan.create == ("refs/heads/dev", "refs/heads/main")
    _rewrite(world)
    result = mirror.sync("org/repo")
    assert refs(world.plain_repo) == refs(world.shop.bare)
    assert result.plan.create == ("refs/tags/v2",)
    assert result.plan.update == ("refs/heads/main",)
    assert result.plan.delete == ("refs/heads/dev",)
    assert result.pruned
    assert not mirror.sync("org/repo").changed


def test_sync_without_prune_keeps_what_the_source_lacks(world: World) -> None:
    world.shop.commit("on dev", branch="dev")
    mirror = world.to_plain()
    mirror.sync("org/repo")
    _rewrite(world)
    result = mirror.sync("org/repo", prune=False)
    assert not result.pruned
    assert set(refs(world.plain_repo)) == {"refs/heads/main", "refs/heads/dev", "refs/tags/v2"}
    assert refs(world.plain_repo)["refs/heads/main"] == refs(world.shop.bare)["refs/heads/main"]
    assert not mirror.sync("org/repo", prune=False).changed


def test_sync_only_deleting(world: World) -> None:
    mirror = world.to_plain()
    mirror.sync("org/repo")
    git("update-ref", "refs/heads/extra", "refs/heads/main", cwd=world.plain_repo)
    result = mirror.sync("org/repo")
    assert result.plan.delete == ("refs/heads/extra",) and result.changed
    assert refs(world.plain_repo) == refs(world.shop.bare)


def test_dry_run(world: World) -> None:
    world.shop.commit("on dev", branch="dev")
    mirror = world.to_plain()
    mirror.sync("org/repo")
    before = refs(world.plain_repo)
    _rewrite(world)
    result = mirror.sync("org/repo", dry_run=True)
    assert result.summary().endswith("would be: 1 created, 1 updated, 1 deleted")
    assert refs(world.plain_repo) == before


def test_an_empty_source_does_not_empty_the_destination(world: World) -> None:
    mirror = world.to_plain()
    mirror.sync("org/repo")
    before = refs(world.plain_repo)
    git("update-ref", "-d", "refs/heads/main", cwd=world.shop.bare)
    with pytest.raises(EmptySourceError):
        mirror.sync("org/repo")
    assert refs(world.plain_repo) == before
    assert not mirror.sync("org/repo", prune=False).changed


def test_a_renamed_default_branch_follows(world: World) -> None:
    mirror = world.to_api()
    mirror.sync("org/repo")
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "main"
    git("branch", "-q", "-m", "main", "stable", cwd=world.shop.work)
    git("update-ref", "-d", "refs/heads/main", cwd=world.shop.bare)
    git("symbolic-ref", "HEAD", "refs/heads/stable", cwd=world.shop.bare)
    world.shop.publish()
    # As a host does, refuse to delete the default branch.
    git("config", "receive.denyDeleteCurrent", "true", cwd=world.api_repo)
    mirror.sync("org/repo")
    assert set(refs(world.api_repo)) == {"refs/heads/stable"}
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "stable"


def test_the_default_branch_is_kept_in_sync_when_nothing_else_changes(world: World) -> None:
    world.shop.commit("on dev", branch="dev")
    mirror = world.to_api()
    mirror.sync("org/repo")
    git("symbolic-ref", "HEAD", "refs/heads/dev", cwd=world.shop.bare)
    assert not mirror.sync("org/repo").changed
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "dev"
    # A clone leaves the settings of an existing repository alone.
    git("symbolic-ref", "HEAD", "refs/heads/main", cwd=world.shop.bare)
    mirror.clone("org/repo")
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "dev"


def test_run_continues_after_a_failure(world: World) -> None:
    mirror = world.to_plain()
    results = list(mirror.run(Operation.SYNC, ["org/missing", "org/repo"]))
    assert [result.ok for result in results] == [False, True]
    assert "failed" in results[0].summary()
    assert results[0].destination.path == "org/missing"
    assert refs(world.plain_repo) == refs(world.shop.bare)


def test_run_checks_the_names_first(world: World) -> None:
    with pytest.raises(ConfigError):
        list(world.to_plain().run(Operation.SYNC, ["org/repo", "not a name"]))
    assert refs(world.plain_repo) == {}
