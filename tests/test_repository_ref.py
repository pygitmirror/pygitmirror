import pytest

from pygitmirror import ConfigError, RepositoryRef


def test_parse() -> None:
    ref = RepositoryRef.parse("group/subgroup/name.git")
    assert (ref.owner, ref.name) == ("group/subgroup", "name")
    assert str(ref) == ref.path == "group/subgroup/name"
    assert RepositoryRef.parse("owner/.github") == RepositoryRef("owner", ".github")


@pytest.mark.parametrize(
    "path", ["name", "", "owner/", "/name", "owner/..", "../name", "owner/-x", "a b/c", "a//b"]
)
def test_invalid(path: str) -> None:
    with pytest.raises(ConfigError):
        RepositoryRef.parse(path)


def test_invalid_segments() -> None:
    with pytest.raises(ConfigError):
        RepositoryRef("owner", "a/b")
    with pytest.raises(ConfigError):
        RepositoryRef("owner;rm", "name")
