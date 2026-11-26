"""The operations which copy a repository from one host to another."""

from enum import StrEnum


class Operation(StrEnum):
    """What may change at the destination, and what is done besides copying.

    All three create the destination repository when it does not exist and
    copy every branch and tag. They differ in what they do to branches and
    tags which the destination already has.
    """

    #: Add what is missing and move branches forward. Nothing at the
    #: destination is overwritten or deleted.
    CLONE = "clone"
    #: Make the destination equal to the source: overwrite what differs and
    #: delete what the source no longer has.
    SYNC = "sync"
    #: Clone, check that the destination equals the source, and optionally
    #: archive the source.
    MIGRATE = "migrate"
