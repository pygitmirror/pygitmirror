"""Names which the supported Python versions provide in different places."""

import sys
from collections.abc import Callable
from typing import TypeVar

__all__ = ["override"]

if sys.version_info >= (3, 12):
    from typing import override
else:
    _F = TypeVar("_F", bound=Callable[..., object])

    def override(method: _F, /) -> _F:
        """Mark a method which overrides one of a base class.

        :param method: the overriding method
        :returns: the method, unchanged
        """
        return method
