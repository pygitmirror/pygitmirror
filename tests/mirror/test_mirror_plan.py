from pygitmirror import MirrorPlan, MirrorResult, Operation, RepositoryRef
from pygitmirror.errors import GitMirrorError

REPO = RepositoryRef("a", "b")


def test_compare() -> None:
    plan = MirrorPlan.compare(
        {"refs/heads/new": "1", "refs/heads/moved": "2", "refs/heads/same": "3"},
        {"refs/heads/old": "9", "refs/heads/moved": "8", "refs/heads/same": "3"},
    )
    assert plan == MirrorPlan(
        ("refs/heads/new",), ("refs/heads/moved",), ("refs/heads/old",), unchanged=1
    )
    assert plan.changes(prune=False) == 2
    assert plan.changes(prune=True) == 3
    assert MirrorPlan.compare({}, {}).changes(prune=True) == 0


def test_summary() -> None:
    plan = MirrorPlan(("x",), (), ("y", "z"))
    result = MirrorResult(Operation.SYNC, REPO, REPO, plan=plan, created=True, pruned=True)
    assert (
        result.summary() == "sync a/b -> a/b: repository created, 1 created, 0 updated, 2 deleted"
    )
    assert result.changed and result.ok
    kept = MirrorResult(Operation.SYNC, REPO, REPO, plan=MirrorPlan(delete=("y",)))
    assert kept.summary() == "sync a/b -> a/b: up to date"
    assert not kept.changed
    dry = MirrorResult(Operation.CLONE, REPO, REPO, plan=plan, dry_run=True)
    assert dry.summary() == "clone a/b -> a/b: would be: 1 created, 0 updated"
    assert not dry.changed
    failed = MirrorResult(Operation.MIGRATE, REPO, REPO, error=GitMirrorError("broken"))
    assert failed.summary() == "migrate a/b -> a/b: failed: broken"
    assert not failed.ok and not failed.changed
