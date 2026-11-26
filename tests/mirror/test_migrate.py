import pytest

from pygitmirror import DivergedError, Mirror, UnsupportedError, VerificationError
from tests.helpers import FolderHost, git, refs
from tests.mirror.conftest import World


def _api_source(world: World, *, can_archive: bool = True) -> FolderHost:
    """Make the source a host with an API."""
    bare = world.shop.bare.with_name("repo.git")
    world.shop.bare.rename(bare)
    world.shop.bare = bare
    return FolderHost(str(world.root / "source"), can_archive=can_archive)


def test_migrate_copies_and_archives(world: World) -> None:
    source = _api_source(world)
    git("tag", "v1", cwd=world.shop.work)
    world.shop.commit("on dev", branch="dev")
    git("symbolic-ref", "HEAD", "refs/heads/dev", cwd=world.shop.bare)
    result = Mirror(source, world.api).migrate("org/repo", archive_source=True)
    assert refs(world.api_repo) == refs(world.shop.bare)
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "dev"
    assert result.created and result.archived
    assert source.archived == [result.source]
    assert result.summary().endswith("source archived")


def test_migrate_again_is_up_to_date(world: World) -> None:
    mirror = world.to_api()
    mirror.migrate("org/repo")
    result = mirror.migrate("org/repo")
    assert not result.changed and not result.archived


def test_migrate_refuses_a_destination_with_more(world: World) -> None:
    mirror = world.to_plain()
    mirror.clone("org/repo")
    git("update-ref", "refs/heads/extra", "refs/heads/main", cwd=world.plain_repo)
    with pytest.raises(VerificationError, match="refs/heads/extra"):
        mirror.migrate("org/repo")


def test_migrate_refuses_a_destination_which_diverged(world: World) -> None:
    source = _api_source(world)
    mirror = Mirror(source, world.api)
    mirror.clone("org/repo")
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=world.shop.work)
    world.shop.publish()
    with pytest.raises(DivergedError):
        mirror.migrate("org/repo", archive_source=True)
    assert source.archived == []


def test_a_dry_run_does_not_archive(world: World) -> None:
    source = _api_source(world)
    result = Mirror(source, world.api).migrate("org/repo", archive_source=True, dry_run=True)
    assert not result.archived and source.archived == []
    assert not world.api_repo.exists()


def test_archiving_is_checked_before_anything_is_done(world: World) -> None:
    with pytest.raises(UnsupportedError):
        world.to_api().migrate("org/repo", archive_source=True)
    assert not world.api_repo.exists()
    source = _api_source(world, can_archive=False)
    with pytest.raises(UnsupportedError):
        Mirror(source, world.api).migrate("org/repo", archive_source=True)
    assert not world.api_repo.exists()
