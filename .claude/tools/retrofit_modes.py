# -*- coding: utf-8 -*-
"""Bring the mode picker onto the design language.

The dialog around it was done in step zero, so this is the three mode cards
and the row of actions under them.

A mode card is a Card you can press: it is a button, so it behaves like a
Control, but among its two siblings it reads as a Card and keeps the Card's
shape. The miniature behind each card's words - the .pv family - is a picture
of a setup screen drawn at picture scale, and is left exactly as it is, for
the same reason the route maps are: its sizes describe the picture, not the
interface.

.actions is shared with the race setup and the offline dialog. Its values
already sit on the scale, so tokenising it changes nothing there.
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


once("""  .modes { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
  .mode {
    position: relative; overflow: hidden; text-align: left; padding: 0;
    min-height: 196px; display: flex; flex-direction: column; justify-content: flex-end;
    border: 1px solid var(--line); border-radius: 12px; background: var(--bg-3);
  }""",
     """  .modes { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--s-4); }
  /* A Card you can press: a button, so it behaves like a Control, but it keeps
     the Card's shape because it sits among siblings. */
  .mode {
    position: relative; overflow: hidden; text-align: left; padding: 0;
    min-height: 196px; display: flex; flex-direction: column; justify-content: flex-end;
    border: 1px solid var(--line); border-radius: var(--r-card); background: var(--bg-3);
  }""",
     "mode grid and card")

once("""  .mode .mtx {
    position: relative; padding: 26px 13px 13px;""",
     """  .mode .mtx {
    position: relative; padding: var(--s-7) var(--s-4) var(--s-4);""",
     "mode words padding")

once("""  .mode .mt { display: block; font-size: 16px; font-weight: 650; }
  .mode .md { font-size: 12.5px; line-height: 1.45; color: var(--fg-dim); margin: 5px 0 0; }""",
     """  .mode .mt { display: block; font-size: var(--t-md); font-weight: 600; }
  .mode .md { font-size: var(--t-sm); line-height: 1.45; color: var(--fg-dim); margin: var(--s-2) 0 0; }""",
     "mode title and blurb")

once("""  .mode .mv { position: absolute; inset: 0; opacity: .18; transition: opacity .18s; pointer-events: none; }""",
     """  .mode .mv { position: absolute; inset: 0; opacity: .18; transition: opacity var(--m-base); pointer-events: none; }""",
     "mode preview fade")

once("""    .mode .md { max-height: 0; opacity: 0; overflow: hidden; transition: max-height .18s, opacity .18s, margin .18s; margin-top: 0; }
    .mode:hover .md, .mode:focus-visible .md { max-height: 130px; opacity: 1; margin-top: 5px; }""",
     """    .mode .md { max-height: 0; opacity: 0; overflow: hidden; transition: max-height var(--m-base), opacity var(--m-base), margin var(--m-base); margin-top: 0; }
    .mode:hover .md, .mode:focus-visible .md { max-height: 130px; opacity: 1; margin-top: var(--s-2); }""",
     "mode blurb reveal")

once("""  .actions { display: flex; gap: 9px; margin-top: 20px; }""",
     """  .actions { display: flex; gap: var(--s-3); margin-top: var(--s-6); }""",
     "actions")

# The mode picker overrode .actions with its own 18px, two pixels off the
# spacing every other dialog uses; it now takes the shared value.
once("""'<div class="actions" style="margin-top:18px"><button class="ghost" id="m-cancel">Cancel</button></div></div>'""",
     """'<div class="actions"><button class="ghost" id="m-cancel">Cancel</button></div></div>'""",
     "mode actions markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("mode picker retrofitted")
