#!/usr/bin/env python3
"""Write the diagrams of the documentation to ``docs/_static``.

Every diagram is drawn twice, for the light and the dark theme of the
documentation, as ``<name>-light.svg`` and ``<name>-dark.svg``::

    python docs/scripts/make_images.py

It needs the standard library only. The files are committed; run this again
after changing a diagram in ``_images/diagrams.py``.
"""

import sys
from pathlib import Path

from _images.diagrams import DIAGRAMS
from _images.themes import THEMES

OUTPUT = Path(__file__).parent.parent / "_static"


def main() -> None:
    """Write every diagram in every theme."""
    for name, draw in DIAGRAMS.items():
        for theme in THEMES:
            path = OUTPUT / f"{name}-{theme}.svg"
            path.write_text(draw(theme), encoding="utf-8")
            sys.stdout.write(f"wrote {path.relative_to(OUTPUT.parent.parent)}\n")


if __name__ == "__main__":
    main()
