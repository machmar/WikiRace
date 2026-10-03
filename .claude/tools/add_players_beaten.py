# -*- coding: utf-8 -*-
"""Issue #34: the line under a finisher says how many players they beat.

Place points are now 2 for finishing and 2 for every player beaten, so "8 for
1st" on its own no longer explains itself. The server sends `beaten` beside
`place_points`; this only draws it, and says nothing when it is none, since
there is nothing to explain about the last finisher's 2. A server that predates
the field leaves it out, which reads as none.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")
s = io.open(PATH, encoding="utf-8").read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


once("""             why: p.place_points + " for " + ordinal(p.place) +
                  (p.bonus ? " + " + p.bonus + " for " + bonusFor : "") + (mult > 1 ? ", ×" + mult : "") };""",
     """             why: p.place_points + " for " + ordinal(p.place) + (p.beaten ? " (beat " + p.beaten + ")" : "") +
                  (p.bonus ? " + " + p.bonus + " for " + bonusFor : "") + (mult > 1 ? ", ×" + mult : "") };""",
     "score line")

io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
