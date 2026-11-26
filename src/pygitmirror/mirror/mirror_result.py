"""The outcome of an operation on one repository."""

from dataclasses import dataclass, field

from pygitmirror.errors import GitMirrorError
from pygitmirror.mirror.mirror_plan import MirrorPlan
from pygitmirror.mirror.operation import Operation
from pygitmirror.repository_ref import RepositoryRef


@dataclass(frozen=True)
class MirrorResult:
    """What an operation did, or would do, to one repository.

    :param operation: the operation
    :param source: the repository which was read
    :param destination: the repository which was written
    :param plan: how the destination differed from the source before the
        operation; without changes when it was up to date
    :param created: whether the destination repository was created, or
        would be in a dry run
    :param pruned: whether the branches and tags of ``plan.delete`` were
        deleted, or would be in a dry run
    :param archived: whether the source was archived
    :param dry_run: whether nothing was changed
    :param error: why the operation failed, or ``None`` if it succeeded;
        set only by :meth:`~pygitmirror.mirror.mirror.Mirror.run`, as the
        other methods raise
    """

    operation: Operation
    source: RepositoryRef
    destination: RepositoryRef
    plan: MirrorPlan = field(default_factory=MirrorPlan)
    created: bool = False
    pruned: bool = False
    archived: bool = False
    dry_run: bool = False
    error: GitMirrorError | None = None

    @property
    def ok(self) -> bool:
        """Whether the operation succeeded."""
        return self.error is None

    @property
    def changed(self) -> bool:
        """Whether anything was changed at the destination or the source."""
        if self.dry_run or not self.ok:
            return False
        return bool(self.created or self.archived or self.plan.changes(prune=self.pruned))

    def summary(self) -> str:
        """Describe the outcome in one line.

        :returns: the operation, the two repositories and what happened
        """
        title = f"{self.operation} {self.source} -> {self.destination}"
        if self.error is not None:
            return f"{title}: failed: {self.error}"
        plan = self.plan
        parts = []
        if self.created:
            parts.append("repository created")
        if plan.changes(prune=self.pruned):
            parts.append(f"{len(plan.create)} created, {len(plan.update)} updated")
            if self.pruned:
                parts[-1] += f", {len(plan.delete)} deleted"
        if self.archived:
            parts.append("source archived")
        outcome = ", ".join(parts) or "up to date"
        return f"{title}: {'would be: ' if self.dry_run and parts else ''}{outcome}"
