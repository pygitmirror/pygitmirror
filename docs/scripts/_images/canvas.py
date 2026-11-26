"""Drawing a diagram as SVG."""

from collections.abc import Sequence
from xml.sax.saxutils import escape

from _images.themes import THEMES

_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


class Canvas:
    """A drawing made of boxes, text and arrows, in the colors of a theme.

    Positions are in pixels from the top left corner. An element is colored
    by the name of its tone; see :data:`_images.themes.THEMES`.

    :param width: the width of the drawing
    :param height: the height of the drawing
    :param theme: ``light`` or ``dark``
    """

    def __init__(self, width: int, height: int, theme: str) -> None:
        self._width = width
        self._height = height
        self._tones = THEMES[theme]
        self._parts: list[str] = []
        self.rect(0.75, 0.75, width - 1.5, height - 1.5, "page", radius=12)

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        tone: str = "neutral",
        *,
        radius: float = 8,
        dashed: bool = False,
        filled: bool = True,
    ) -> None:
        """Draw a rectangle with rounded corners.

        :param x: the left edge
        :param y: the top edge
        :param width: the width
        :param height: the height
        :param tone: the name of its colors
        :param radius: the radius of the corners
        :param dashed: draw the outline with dashes
        :param filled: fill it; otherwise only the outline is drawn
        """
        stroke, fill = self._tones[tone]
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self._parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
            f'fill="{fill if filled else "none"}" stroke="{stroke}" stroke-width="1.5"{dash}/>'
        )

    def text(
        self,
        x: float,
        y: float,
        content: str,
        tone: str = "text",
        *,
        size: int = 14,
        bold: bool = False,
        anchor: str = "middle",
        mono: bool = False,
    ) -> None:
        """Write one line of text.

        :param x: the position which ``anchor`` refers to
        :param y: the baseline
        :param content: the text
        :param tone: the name of its color
        :param size: the size of the font
        :param bold: write it in bold
        :param anchor: ``start``, ``middle`` or ``end``
        :param mono: use a font of fixed width
        """
        family = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" if mono else _FONT
        self._parts.append(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{600 if bold else 400}" text-anchor="{anchor}" '
            f'fill="{self._tones[tone].stroke}">{escape(content)}</text>'
        )

    def box(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        lines: Sequence[str] = (),
        tone: str = "neutral",
        *,
        dashed: bool = False,
    ) -> None:
        """Draw a rectangle with a title and lines of smaller text, centered.

        :param x: the left edge
        :param y: the top edge
        :param width: the width
        :param height: the height
        :param title: the title, in bold
        :param lines: the lines below the title
        :param tone: the name of its colors
        :param dashed: draw the outline with dashes
        """
        self.rect(x, y, width, height, tone, dashed=dashed)
        top = y + height / 2 - (len(lines) * 18) / 2 + 5
        self.text(x + width / 2, top, title, bold=True, size=15)
        for index, line in enumerate(lines, start=1):
            self.text(x + width / 2, top + index * 18 + 2, line, "muted", size=12)

    def pill(self, x: float, y: float, width: float, label: str, tone: str) -> None:
        """Draw a small label with a colored background.

        :param x: the left edge
        :param y: the top edge
        :param width: the width
        :param label: the text
        :param tone: the name of its colors
        """
        self.rect(x, y, width, 24, tone, radius=12)
        # The outline of a neutral element is too faint for text.
        color = self._tones["muted" if tone == "neutral" else tone].stroke
        self._parts.append(
            f'<text x="{x + width / 2}" y="{y + 16}" font-family="{_FONT}" font-size="12" '
            f'font-weight="600" text-anchor="middle" fill="{color}">'
            f"{escape(label)}</text>"
        )

    def dot(
        self, x: float, y: float, tone: str = "muted", *, radius: float = 5, filled: bool = True
    ) -> None:
        """Draw a circle.

        :param x: the center
        :param y: the center
        :param tone: the name of its color
        :param radius: the radius
        :param filled: fill it with the color of its outline
        """
        stroke = self._tones[tone].stroke
        fill = stroke if filled else self._tones["page"].fill
        self._parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" '
            'stroke-width="1.5"/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        tone: str = "muted",
        *,
        dashed: bool = False,
    ) -> None:
        """Draw a straight line.

        :param x1: the start
        :param y1: the start
        :param x2: the end
        :param y2: the end
        :param tone: the name of its color
        :param dashed: draw it with dashes
        """
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self._parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{self._tones[tone].stroke}" stroke-width="1.5"{dash}/>'
        )

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        tone: str = "muted",
        *,
        dashed: bool = False,
        mono: bool = False,
    ) -> None:
        """Draw a horizontal or vertical arrow, with a label beside it.

        :param x1: the start
        :param y1: the start
        :param x2: the tip
        :param y2: the tip
        :param label: text above a horizontal arrow, or right of a vertical one
        :param tone: the name of its color
        :param dashed: draw the line with dashes
        :param mono: write the label in a font of fixed width
        """
        color = self._tones[tone].stroke
        if y1 == y2:
            way = 1 if x2 > x1 else -1
            self.line(x1, y1, x2 - 7 * way, y2, tone, dashed=dashed)
            head = f"{x2},{y2} {x2 - 9 * way},{y2 - 5} {x2 - 9 * way},{y2 + 5}"
            if label:
                self.text((x1 + x2) / 2, y1 - 9, label, tone, size=12, mono=mono)
        else:
            way = 1 if y2 > y1 else -1
            self.line(x1, y1, x2, y2 - 7 * way, tone, dashed=dashed)
            head = f"{x2},{y2} {x2 - 5},{y2 - 9 * way} {x2 + 5},{y2 - 9 * way}"
            if label:
                self.text(
                    x1 + 10, (y1 + y2) / 2 + 4, label, tone, size=12, anchor="start", mono=mono
                )
        self._parts.append(f'<polygon points="{head}" fill="{color}"/>')

    def render(self, description: str) -> str:
        """Return the drawing as an SVG document.

        :param description: what the drawing shows, for readers who cannot
            see it
        :returns: the text of the SVG file
        """
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self._width} {self._height}" '
            f'width="{self._width}" height="{self._height}" role="img">\n'
            f"<title>{escape(description)}</title>\n" + "\n".join(self._parts) + "\n</svg>\n"
        )
