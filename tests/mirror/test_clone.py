import pytest

from pygitmirror import ConfigError, DivergedError, GitError, Mirror, Operation
from tests.helpers import FolderHost, git, refs
from tests.mirror.conftest import World


def test_clone_copies_branches_and_tags(world: World) -> None:
    git("tag", "-a", "v1", "-m", "one", cwd=world.shop.work)
    world.shop.commit("on dev", branch="dev")
    result = world.to_plain().clone("org/repo")
    assert refs(world.plain_repo) == refs(world.shop.bare)
    assert len(result.plan.create) == 3 and result.changed
    assert result.operation is Operation.CLONE
    assert (world.workdir / "org" / "repo.git" / "HEAD").is_file()


def test_clone_again_is_up_to_date_and_downloads_nothing(world: World) -> None:
    mirror = Mirror(world.source, world.plain)
    assert world.plain_repo
    mirror.clone("org/repo")
    result = mirror.clone("org/repo")
    assert not result.changed
    assert result.summary().endswith("up to date")


def test_clone_moves_branches_forward_and_keeps_the_rest(world: World) -> None:
    mirror = world.to_plain()
    mirror.clone("org/repo")
    git("update-ref", "refs/heads/local", "refs/heads/main", cwd=world.plain_repo)
    world.shop.commit("second")
    result = mirror.clone("org/repo")
    assert result.plan.update == ("refs/heads/main",)
    assert refs(world.plain_repo)["refs/heads/main"] == refs(world.shop.bare)["refs/heads/main"]
    assert "refs/heads/local" in refs(world.plain_repo)


def test_clone_refuses_to_overwrite(world: World) -> None:
    git("tag", "v1", cwd=world.shop.work)
    world.shop.publish()
    mirror = world.to_plain()
    mirror.clone("org/repo")
    before = refs(world.plain_repo)
    git("commit", "-q", "--amend", "--allow-empty", "-m", "rewritten", cwd=world.shop.work)
    git("tag", "-f", "v1", cwd=world.shop.work)
    world.shop.publish()
    with pytest.raises(DivergedError) as raised:
        mirror.clone("org/repo")
    assert raised.value.refs == ("refs/heads/main", "refs/tags/v1")
    assert refs(world.plain_repo) == before


def test_dry_run_changes_nothing(world: World) -> None:
    result = world.to_plain().clone("org/repo", dry_run=True)
    assert result.dry_run and len(result.plan.create) == 1 and not result.changed
    assert refs(world.plain_repo) == {}
    api = world.to_api().clone("org/repo", dry_run=True)
    assert api.created and not world.api_repo.exists()


def test_destination_is_created_with_the_default_branch_of_the_source(world: World) -> None:
    world.shop.commit("on dev", branch="dev")
    result = world.to_api().clone("org/repo")
    assert result.created
    assert "repository created" in result.summary()
    assert refs(world.api_repo) == refs(world.shop.bare)
    # The host created it with "trunk"; the source has "main".
    assert git("symbolic-ref", "--short", "HEAD", cwd=world.api_repo) == "main"
    # Without an API at the source its visibility is unknown: private.
    assert world.api.created[result.destination].private


def test_settings_are_copied_from_a_source_with_an_api(world: World) -> None:
    world.shop.bare.rename(world.shop.bare.with_name("repo.git"))
    world.shop.bare = world.shop.bare.with_name("repo.git")
    source = FolderHost(str(world.root / "source"))
    result = Mirror(source, world.api).clone("org/repo")
    assert not world.api.created[result.destination].private


def test_a_missing_destination_without_an_api_fails(world: World) -> None:
    with pytest.raises(GitError):
        Mirror(world.source, world.plain).clone("org/repo")


def test_owners_and_to(world: World) -> None:
    mirror = Mirror(world.source, world.api, owners={"org": "team"})
    assert mirror.destination_of("org/repo").path == "team/repo"
    assert mirror.destination_of("other/repo").path == "other/repo"
    assert mirror.clone("org/repo").destination.path == "team/repo"
    assert mirror.clone("org/repo", to="else/renamed").destination.path == "else/renamed"
    assert (world.root / "api" / "else" / "renamed.git").is_dir()


def test_source_and_destination_must_differ(world: World) -> None:
    with pytest.raises(ConfigError, match="both"):
        Mirror(world.source, world.source).clone("org/repo")


def test_repositories_are_listed_by_name(world: World) -> None:
    world.to_api().clone("org/repo")
    Mirror(world.source, world.api).clone("org/repo", to="org/another")
    listed = Mirror(world.api, world.plain).repositories("org")
    assert [ref.path for ref in listed] == ["org/another", "org/repo"]
