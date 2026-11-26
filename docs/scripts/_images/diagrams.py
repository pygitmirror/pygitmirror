"""The diagrams of the documentation."""

from _images.canvas import Canvas


def overview(theme: str) -> str:
    """Draw how a repository travels from the source to the destination.

    :param theme: ``light`` or ``dark``
    :returns: the SVG document
    """
    canvas = Canvas(880, 300, theme)
    services = ["GitHub · GitLab · Gitea", "Bitbucket · any git server"]
    canvas.box(30, 40, 230, 110, "Source", services, "source")
    canvas.box(
        325, 40, 230, 110, "Local mirror", ["a bare repository with", "all branches and tags"]
    )
    canvas.box(620, 40, 230, 110, "Destination", services, "destination")
    canvas.arrow(260, 95, 325, 95, "fetch", mono=True)
    canvas.arrow(555, 95, 620, 95, "push", mono=True)

    canvas.box(30, 215, 230, 55, "API of the source", tone="neutral", dashed=True)
    canvas.box(620, 215, 230, 55, "API of the destination", tone="neutral", dashed=True)
    canvas.arrow(145, 215, 145, 150, dashed=True)
    canvas.arrow(735, 215, 735, 150, dashed=True)
    canvas.text(160, 188, "description, visibility", "muted", size=12, anchor="start")
    canvas.text(720, 180, "create the repository,", "muted", size=12, anchor="end")
    canvas.text(720, 196, "set its default branch", "muted", size=12, anchor="end")
    canvas.text(440, 238, "git moves the data,", "muted", size=13)
    canvas.text(440, 256, "the API manages the repositories", "muted", size=13)
    return canvas.render(
        "The source is fetched into a local mirror, which is pushed to the destination. "
        "The APIs of the two hosts read and create the repositories."
    )


def _history(canvas: Canvas, x: float, y: float, dots: int, tone: str, *, forked: bool) -> None:
    """Draw the commits of a branch as dots on a line, or a dash when it is absent."""
    if not dots:
        canvas.line(x, y, x + 54, y, "neutral", dashed=True)
        return
    canvas.line(x, y, x + 18 * (dots - 1), y, tone)
    for index in range(dots):
        last = index == dots - 1
        canvas.dot(x + 18 * index, y, tone, filled=not (forked and last))


def operations(theme: str) -> str:
    """Draw what each operation does to a branch or tag, case by case.

    :param theme: ``light`` or ``dark``
    :returns: the SVG document
    """
    canvas = Canvas(880, 368, theme)
    columns = {"clone": 440, "sync": 590, "migrate": 740}
    for name, x in columns.items():
        canvas.text(x + 55, 42, name, bold=True, size=15, mono=True)
    canvas.text(284, 38, "source", "source", size=12, anchor="start")
    canvas.text(284, 52, "destination", "destination", size=12, anchor="start")
    canvas.line(30, 64, 850, 64, "neutral")

    # A case: its name, the commits at the source and the destination,
    # whether the two differ in their last commit, and the outcomes.
    cases = [
        ("Only the source has it", 3, 0, False, ["added"] * 3, ["good"] * 3),
        ("The source is ahead", 4, 2, False, ["moved forward"] * 3, ["good"] * 3),
        (
            "The two differ",
            3,
            3,
            True,
            ["fails", "overwritten", "fails"],
            ["stop", "warn", "stop"],
        ),
        (
            "Only the destination has it",
            0,
            3,
            False,
            ["kept", "deleted", "fails"],
            ["neutral", "warn", "stop"],
        ),
    ]
    for row, (name, source, destination, forked, outcomes, tones) in enumerate(cases):
        y = 100 + row * 68
        canvas.text(30, y + 5, name, size=14, anchor="start")
        _history(canvas, 290, y - 9, source, "source", forked=False)
        _history(canvas, 290, y + 11, destination, "destination", forked=forked)
        for x, outcome, tone in zip(columns.values(), outcomes, tones, strict=True):
            canvas.pill(x, y - 11, 110, outcome, tone)
        if row < len(cases) - 1:
            canvas.line(30, y + 36, 850, y + 36, "neutral", dashed=True)
    canvas.text(
        30,
        348,
        "An operation which fails changes nothing: it stops before the push.",
        "muted",
        size=12,
        anchor="start",
    )
    return canvas.render(
        "What clone, sync and migrate do to a branch or tag which only the source has, "
        "which is ahead at the source, which differs, and which only the destination has."
    )


def layers(theme: str) -> str:
    """Draw the packages and which of them uses which.

    :param theme: ``light`` or ``dark``
    :returns: the SVG document
    """
    canvas = Canvas(880, 400, theme)
    canvas.box(60, 30, 330, 64, "cli + config", ["the git-mirror command and its settings"])
    canvas.box(490, 30, 330, 64, "web", ["the page, its server and its jobs"])
    canvas.rect(30, 132, 820, 240, "neutral", dashed=True, filled=False, radius=12)
    canvas.text(50, 156, "the library", "muted", size=12, anchor="start")
    canvas.box(
        275, 168, 330, 64, "mirror", ["clone, sync, migrate: the plan and the result"], "good"
    )
    canvas.box(60, 284, 330, 64, "hosts", ["one class per service, and the API client"], "source")
    canvas.box(490, 284, 330, 64, "git", ["the git executable and the local mirror"], "destination")
    canvas.line(225, 94, 225, 200)
    canvas.arrow(225, 200, 275, 200)
    canvas.line(655, 94, 655, 200)
    canvas.arrow(655, 200, 605, 200)
    canvas.arrow(360, 232, 360, 284)
    canvas.arrow(520, 232, 520, 284)
    canvas.text(440, 264, "uses", "muted", size=12)
    return canvas.render(
        "The command and the page use the mirror package, which uses "
        "the hosts and the git packages. Hosts and git do not use each other."
    )


def steps(theme: str) -> str:
    """Draw the steps of an operation and which operation takes which.

    :param theme: ``light`` or ``dark``
    :returns: the SVG document
    """
    rows = [
        ("List the branches and tags of the source", "111", False),
        ("Create the destination repository if it is missing", "111", True),
        ("List the branches and tags of the destination", "111", False),
        ("Plan, and stop if nothing has to change", "111", False),
        ("Fetch the source into the local mirror", "111", False),
        ("Check that nothing would be overwritten", "101", False),
        ("Push to the destination", "111", True),
        ("Set the default branch", "111", True),
        ("Delete what the source does not have", "010", True),
        ("Verify that the destination equals the source", "001", False),
        ("Archive the source, if asked", "001", True),
    ]
    canvas = Canvas(880, 78 + 36 * len(rows) + 44, theme)
    columns = [570, 660, 750]
    for x, name in zip(columns, ("clone", "sync", "migrate"), strict=True):
        canvas.text(x + 40, 42, name, bold=True, size=14, mono=True)
    canvas.line(30, 58, 850, 58, "neutral")
    for index, (name, taken, changes) in enumerate(rows):
        y = 84 + index * 36
        canvas.dot(46, y - 4, "warn" if changes else "neutral", radius=12, filled=False)
        canvas.text(46, y + 1, str(index + 1), "warn" if changes else "muted", size=12, bold=True)
        canvas.text(72, y + 1, name, size=14, anchor="start")
        for x, flag in zip(columns, taken, strict=True):
            if flag == "1":
                canvas.dot(x + 40, y - 4, "good", radius=7)
            else:
                canvas.line(x + 33, y - 4, x + 47, y - 4, "neutral")
    bottom = 84 + len(rows) * 36 + 8
    canvas.line(30, bottom - 16, 850, bottom - 16, "neutral")
    canvas.dot(46, bottom + 6, "warn", radius=9, filled=False)
    canvas.text(
        66, bottom + 11, "changes a host: skipped in a dry run", "muted", size=12, anchor="start"
    )
    note = "clone sets the default branch only when it creates; sync pushes with force"
    canvas.text(850, bottom + 11, note, "muted", size=12, anchor="end")
    return canvas.render(
        "The eleven steps of an operation, from listing the source to archiving it, "
        "and which of clone, sync and migrate takes each."
    )


#: The diagrams by the name of their files.
DIAGRAMS = {"overview": overview, "operations": operations, "layers": layers, "steps": steps}
