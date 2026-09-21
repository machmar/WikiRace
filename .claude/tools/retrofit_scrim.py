# -*- coding: utf-8 -*-
"""Every backdrop behind a Panel is --scrim.

Two backdrops hard-coded the dark theme's colour and so never followed the
theme: the one behind the mode picker, race setup and offline dialogs sat at
93% near-black even on the light theme, and the mobile side drawer's at 60%
dark. The peek sheet, the vote card and the name picker already used --scrim,
so the game had three different dimmings for one idea.

The blurs are left as they were: they are what keeps a busy screen behind a
lighter scrim from competing with the dialog, and nothing in the standard says
what they should be yet.
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


once("background: rgba(6, 10, 15, .93); backdrop-filter: blur(5px);",
     "background: var(--scrim); backdrop-filter: blur(5px);",
     "dialog backdrop")
once("background: rgba(6, 10, 15, .6); backdrop-filter: blur(2px);",
     "background: var(--scrim); backdrop-filter: blur(2px);",
     "side drawer backdrop")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("backdrops now follow the theme")
