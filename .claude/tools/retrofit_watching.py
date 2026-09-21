# -*- coding: utf-8 -*-
"""Bring the Watching tab onto the design language.

Watching is the spectator view: a bar to choose tiled or single and whom to
watch, then a tile per player showing the article they are on, scrolled to
where they are.

- Each tile is a Card - one of a grid of siblings - whose contents run flush:
  a header strip, then the article. So it takes .card for its shape and
  surface and gives up the Card's padding. The class is set from script, so
  the base class goes in there too.
- The bar matches the hub bar above it, and the header strip snaps onto the
  scale.
- The article inside a tile is a reading surface, like the race's own, so its
  type, its infobox sizing, its title and its padding are the standard's
  carve-out and stay as they are.
- "Spectating opens once everyone has finished" named the thing by a word the
  game uses nowhere else; the tab is Watching, so it now says "You can watch".
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


once("""  #spec-bar {
    display: flex; align-items: center; gap: 11px; padding: 9px 16px;""",
     """  #spec-bar {
    display: flex; align-items: center; gap: var(--s-4); padding: var(--s-3) var(--s-5);""",
     "spectator bar")
once("""  #spec-body { flex: 1; overflow: hidden; padding: 12px; }
  #spec-body.tiles {
    display: grid; gap: 12px; overflow-y: auto;""",
     """  #spec-body { flex: 1; overflow: hidden; padding: var(--s-4); }
  #spec-body.tiles {
    display: grid; gap: var(--s-4); overflow-y: auto;""",
     "tile grid")
once("""  .spec-tile {
    display: flex; flex-direction: column; min-height: 0;
    background: var(--bg-2); border: 1px solid var(--line);
    border-radius: 10px; overflow: hidden;
  }""",
     """  /* A Card whose contents run flush - a header strip, then the article - so
     it keeps the Card's shape and surface and gives up its padding. */
  .spec-tile {
    display: flex; flex-direction: column; min-height: 0; padding: 0; overflow: hidden;
  }""",
     "tile")
once("""    display: flex; align-items: center; gap: 8px; padding: 7px 11px;
    background: var(--bg-3); border-bottom: 1px solid var(--line); flex: none; font-size: 13px;""",
     """    display: flex; align-items: center; gap: var(--s-3); padding: var(--s-2) var(--s-4);
    background: var(--bg-3); border-bottom: 1px solid var(--line); flex: none; font-size: var(--t-sm);""",
     "tile header")
once("""    margin-left: auto; color: var(--fg-dim); font-size: 11.5px;""",
     """    margin-left: auto; color: var(--fg-dim); font-size: var(--t-xs);""",
     "tile header meta")
once("""  .spec-empty { color: var(--fg-faint); font-style: italic; padding: 26px; text-align: center; font-size: 13px; }""",
     """  .spec-empty { color: var(--fg-faint); font-style: italic; padding: var(--s-7); text-align: center; font-size: var(--t-sm); }""",
     "nothing to watch")

once("""      tile.className = "spec-tile";""",
     """      tile.className = "card spec-tile";""",
     "tile markup")
once("""Spectating opens once everyone has finished.""",
     """You can watch once everyone has finished.""",
     "hidden positions copy")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("watching retrofitted")
