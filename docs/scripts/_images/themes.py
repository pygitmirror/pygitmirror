"""The colors of the diagrams in the light and the dark theme."""

from typing import NamedTuple


class Tone(NamedTuple):
    """The colors of one kind of element."""

    stroke: str
    fill: str


#: The colors by theme and by name. ``page`` is the background, ``text`` and
#: ``muted`` have their color as stroke. The tones say what an element is:
#: ``source`` and ``destination`` for the two ends, ``good`` for what only
#: adds, ``warn`` for what overwrites or deletes, ``stop`` for what fails.
THEMES: dict[str, dict[str, Tone]] = {
    "light": {
        "page": Tone("#d1d9e0", "#ffffff"),
        "text": Tone("#1f2328", "none"),
        "muted": Tone("#59636e", "none"),
        "neutral": Tone("#afb8c1", "#f6f8fa"),
        "source": Tone("#0969da", "#ddf4ff"),
        "destination": Tone("#8250df", "#fbefff"),
        "good": Tone("#1a7f37", "#dafbe1"),
        "warn": Tone("#9a6700", "#fff8c5"),
        "stop": Tone("#cf222e", "#ffebe9"),
    },
    "dark": {
        "page": Tone("#30363d", "#131416"),
        "text": Tone("#e6edf3", "none"),
        "muted": Tone("#9198a1", "none"),
        "neutral": Tone("#545d68", "#1c2128"),
        "source": Tone("#4493f8", "#121d2f"),
        "destination": Tone("#ab7df8", "#211a33"),
        "good": Tone("#3fb950", "#12261e"),
        "warn": Tone("#d29922", "#272115"),
        "stop": Tone("#f85149", "#2a1719"),
    },
}
