Design of the Page
==================

The look of the page, written down so that it can be extended without
drifting. The files are in ``src/pygitmirror/web/static``; every value
below is a variable of ``tokens.css``, and no other file names a color or a
font.

Character
---------

A technical instrument, not a marketing page: dense, calm, exact. Large
condensed headlines, small capitals in a monospaced face for labels, flat
surfaces separated by hairlines, and one strong accent used sparingly.
Depth comes from one soft glow behind the hero, never from shadows.

Color
-----

.. list-table::
   :header-rows: 1
   :widths: 22 18 18 42

   * - Variable
     - Light
     - Dark
     - Use
   * - ``--bg``
     - ``#f5f5fc``
     - ``#12111c``
     - the page, and the inside of fields and canvases
   * - ``--surface``
     - ``#ffffff``
     - ``#1d1b2a``
     - panels, cards, buttons
   * - ``--surface-2``
     - ``#eeeef8``
     - ``#242433``
     - the chosen item of a control, the track of a meter
   * - ``--fg``
     - ``#14131f``
     - ``#f2f1f7``
     - text
   * - ``--muted``
     - ``#5d5c74``
     - ``#9c9bb3``
     - secondary text, labels
   * - ``--line``
     - ``#e1e0ee``
     - ``#2c2b3f``
     - hairlines and borders, always 1px
   * - ``--accent``
     - ``#d81b5a``
     - ``#f33777``
     - links, focus rings, the brand mark
   * - ``--accent-fill``
     - ``#d81b5a``
     - ``#d81b5a``
     - the primary button, with ``--accent-ink`` ``#ffffff`` on it
   * - ``--signal``
     - ``#2b6a0b``
     - ``#5ada16``
     - success, and "running"
   * - ``--danger``
     - ``#b3261e``
     - ``#ff7a70``
     - errors
   * - ``--glow``
     - indigo at 10%
     - indigo at 16%
     - the radial glow of the hero

Four categorical colors mark kinds of things, never states:

.. list-table::
   :header-rows: 1
   :widths: 14 18 18 50

   * - Variable
     - Light
     - Dark
     - Marks
   * - ``--c1``
     - ``#a87200``
     - ``#ffc12d``
     - amber: sync, updates, storage
   * - ``--c2``
     - ``#4553e6``
     - ``#5e6efa``
     - indigo: the source, migrate
   * - ``--c3``
     - ``#d81b5a``
     - ``#f33777``
     - magenta: the destination, deletions
   * - ``--c4``
     - ``#3c8d10``
     - ``#5ada16``
     - green: clone, creations

The dark theme follows the system unless the reader chose one with the
switch in the header, which stores the choice in the browser. The dark
values are written twice in ``tokens.css``, once for each way of getting
there; the two blocks must stay equal.

Type
----

Three faces of the IBM Plex family, served by the package:

.. list-table::
   :header-rows: 1
   :widths: 24 30 46

   * - Variable
     - Face
     - Use
   * - ``--font-display``
     - IBM Plex Sans Condensed 600
     - headlines, the brand, large numbers
   * - ``--font-body``
     - IBM Plex Sans 400, 500, 600
     - text, buttons, field labels
   * - ``--font-mono``
     - IBM Plex Mono 400, 500
     - labels, names of repositories, what the user types

Sizes are in ``rem`` with ``1rem`` = 10px (``html`` is 62.5%).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Element
     - Size
   * - Headline of the hero
     - ``clamp(4.4rem, 6vw, 7.2rem)``, line height 0.98, tracking -0.015em
   * - Headline of a section
     - ``clamp(3rem, 3.5vw, 3.8rem)``, line height 1.1
   * - Lede
     - 1.9rem, line height 1.55, muted
   * - Body
     - 1.6rem, line height 1.6
   * - Large number
     - 3.2rem, line height 1, tabular figures
   * - Label
     - mono 1.2rem, weight 500, capitals, tracking 0.08em, muted
   * - Head of a panel
     - mono 1.1rem, tabular figures

Layout
------

* Content is at most 1152px wide, with 16px at the sides, 32px from 768px.
* The header is one row: brand left, version and theme switch right, a
  hairline below.
* The hero has the copy on the left (at most 520px) and a panel on the
  right, in columns of 0.82 to 1.18 from 1024px, stacked below that. Its
  padding is ``clamp(48px, 7vw, 96px)``.
* A section has padding ``clamp(48px, 7vw, 80px)`` and a hairline above
  it. It starts with a head: a numbered label, a headline, one sentence.
* Grids have gaps of 12px to 14px. Two columns from 768px for the servers,
  three for the operations, five for the figures.

Components
----------

**Panel.** Surface, hairline border, radius 14px, padding 10px to 14px. Its
head is a row in mono: a name with a 7px dot in the color of what the panel
is about, and a metric on the right.

**Button.** Padding 11px by 18px, radius 10px, hairline border on surface;
the border turns muted on hover. The primary button is filled with
``--accent-fill`` and brightens by 8% on hover. One primary button per
group.

**Field.** A label above an input. Inputs are mono 1.4rem on ``--bg`` with
a hairline border and radius 10px.

**Choice.** A card which is a radio button: a 3px bar on its left edge in
its categorical color, a name in mono, one sentence. The chosen one has a
border in that color.

**Figure.** A tile without a border: the 3px bar, a large number, a
caption. Used in a row which summarizes a job.

**Row.** A line of a list between hairlines: a name in mono, a pill on the
right, and a sentence below.

**Pill.** A small outlined label with a dot, for the state of a row:
neutral while waiting, green when done, amber for "would change", red for
failed. The dot of a waiting row pulses.

**Meter.** A bar 10px high with radius 2px on ``--surface-2``, filled in
amber, in red when space is low.

**Focus.** A 2px outline in the accent, 3px away, on everything which can
be focused.

Motion
------

The panel of the hero holds the one animation: commits travel on seven
lanes from the source through the local mirror to the destination. While a
job runs they move three times as fast, turn green, and rings leave the
mirror. It is drawn on a canvas in the colors of the theme.

Motion never carries information which is not also in text. The animation
draws at most 30 frames per second, stops while the tab is hidden or the
canvas is out of sight, and is a single still frame when the reader asked
for reduced motion.

Words
-----

Sentence case. A button says what it does: "List repositories", "Preview",
"Run". The operations are described in the words of the table in
:doc:`/guide/operations`. An error says what happened and, where there is
one, what to do.
