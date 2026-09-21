# -*- coding: utf-8 -*-
"""Carve the countdown and the splashes out of the design language.

The countdown before a race and the splashes for a checkpoint and the finish
are the game's big moments: loud, arcade-like, drawn at their own sizes and in
their own colours on purpose. They join the standard's carve-out beside the
article, the maps and the illustrations, and this marks them where they are
defined so nobody snaps them onto the scale by mistake.

One thing on the countdown screen is not artwork: the warning that find is off
for this race. It is a message saying how things stand - the example the
standard itself gives of a centred Note - so it becomes one, the same way the
interface around a carved-out map still follows the standard.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")

with io.open(PATH, encoding="utf-8", newline="") as f:
    s = f.read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


once("""  #countdown { font-size: 130px;""",
     """  /* The countdown is one of the big moments, and the design language's
     carve-out: its number, the goal line above it and the lost-race line are a
     composition drawn at their own sizes. The warning under it is a message,
     and is a Note. */
  #countdown { font-size: 130px;""",
     "countdown marker")
once("""  .cd-warn {
    margin-top: 16px; padding: 9px 16px; border-radius: 9px;
    background: var(--warn-bg); border: 1px solid var(--warn-line); color: var(--warn-fg);
    font-size: 13.5px; max-width: 420px;
  }""",
     """  .cd-warn { margin-top: var(--s-5); max-width: 420px; }""",
     "countdown warning")
once("""     Deliberately loud and arcade-like - it's a celebration, not a notice. A""",
     """     Deliberately loud and arcade-like - it's a celebration, not a notice, and
     so it is the design language's carve-out: its sizes, glows and colours are
     its own and are not snapped onto the scale. A""",
     "splash marker")
once("""        ? '<div class="cd-warn">Find is off this race""",
     """        ? '<div class="note warn cd-warn">Find is off this race""",
     "countdown warning markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("big moments carved out")
