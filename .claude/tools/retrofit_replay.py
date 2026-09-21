# -*- coding: utf-8 -*-
"""Bring the replay's chrome onto the design language.

The last of the screens. The replay is where the carve-out matters most: the
timeline and the four maps are drawings, and are left exactly as they are -
the map surface, the diagram's own palette (--dg-*, which already follows the
theme), the dimming while a replay runs, the pings, and the positions of the
boxes laid over a map, which are placed against one another by hand (the info
box clears the play button at 60px; a name sits beside it at 148px), so a
pixel's nudge to one would misalign the rest.

What follows the standard is the chrome around the drawings and over them:

- The map's screen is a Panel, so it takes --r-panel. It was the last user of
  the old --radius token, which goes from :root with it.
- The play control is a Pill; its clock stops using weight 500, which is not
  one of the three.
- The zoom and view buttons, and the hint, info and name boxes on a map, snap
  their own padding, corners and type. They sit on the map's own glass rather
  than lifting off the page: they are inside the screen, not above it.
- The timeline's tooltip is a Tip, and takes the Tip's shape and lift - it had
  the last literal shadow in the file.
- The player boxes under the view keep their shape and snap onto the scale;
  the page each player is on is small print, as it is in the side panel.

The legend and range-slider rules of an older routes view go: the player boxes
replaced the legend, and nothing builds any of those classes any more.
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


# ---- :root: the old radius token has no users left ----
once("""    --radius: 10px;
""", "", "old radius token")
once("""    /* Radius. Four roles; thirteen values were in use to express them. --radius
       above is what these replace - it was used three times and was already
       overloaded across two of the four roles, so leave it alone and let it go
       as its last users are converted. */""",
     """    /* Radius. Four roles; thirteen values were in use to express them, and
       the single --radius token that existed was overloaded across two. */""",
     "radius comment")

# ---- dead: an older routes view's legend and slider ----
once("""  /* routes view */
  .rp-scroll { overflow-x: auto; overflow-y: hidden; padding-bottom: 6px; }
  .rp-tools { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .rp-tools input[type=range] { flex: 1; max-width: 260px; accent-color: var(--accent); }
  .tiny-btn { padding: 4px 11px; font-size: 12px; }
  .leg.pick.latched { outline: 1px solid var(--accent); outline-offset: 3px; border-radius: 3px; }

""", "", "dead routes view")
once("""  .rp-legend { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 12px; font-size: 12.5px; }
  .leg { display: inline-flex; align-items: center; gap: 6px; }
  .leg .sw { width: 16px; height: 3px; border-radius: 2px; }
  .leg .sw.dash {
    background: none;
    border-top: 3px dashed var(--fg-faint);
  }
  .leg .sub { color: var(--fg-faint); font-family: var(--mono); font-size: 11px; }
  .leg.pick { cursor: pointer; transition: opacity .12s; }
  .leg.pick.faded { opacity: .3; }
""", "", "dead legend")
once("""  .rp-legend .leg.still { cursor: default; }
""", "", "dead legend still")

# ---- the timeline's tooltip: a Tip ----
once("""  .rp-tip {
    position: absolute; z-index: 5; transform: translateX(-50%);
    background: var(--bg-3); border: 1px solid var(--line); border-radius: 6px;
    padding: 3px 9px; font-size: 12px; white-space: nowrap; pointer-events: none;
    box-shadow: 0 6px 18px rgba(0,0,0,.45);
  }""",
     """  /* A Tip: the shape, surface and lift come from .tip. */
  .rp-tip { position: absolute; z-index: 5; transform: translateX(-50%); white-space: nowrap; }""",
     "timeline tooltip")
once("""<div class="rp-tip" hidden></div>""",
     """<div class="tip rp-tip" hidden></div>""",
     "timeline tooltip markup")

# ---- the map's screen, its bar and the boxes over it ----
once("""  .rm-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; margin-bottom: 12px; }""",
     """  .rm-bar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s-3) var(--s-5); margin-bottom: var(--s-4); }""",
     "view bar")
once("""    border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; background: var(--dg-bg);""",
     """    border: 1px solid var(--line); border-radius: var(--r-panel); overflow: hidden; background: var(--dg-bg);""",
     "map screen")
once("""  .rm-tools { position: absolute; top: 10px; right: 10px; z-index: 2; display: flex; align-items: center; gap: 6px; }
  .rm-tools button {
    min-width: 34px; height: 34px; padding: 0 10px; border-radius: 8px;
    border: 1px solid var(--dg-line); background: var(--dg-glass); color: var(--dg-text); font-size: 15px; line-height: 1;
  }""",
     """  .rm-tools { position: absolute; top: 10px; right: 10px; z-index: 2; display: flex; align-items: center; gap: var(--s-2); }
  .rm-tools button {
    min-width: 34px; height: 34px; padding: 0 var(--s-3); border-radius: var(--r-box);
    border: 1px solid var(--dg-line); background: var(--dg-glass); color: var(--dg-text); font-size: var(--t-md); line-height: 1;
  }""",
     "map buttons")
once("""  .rm-zoom { font: 12px var(--mono); color: var(--dg-faint); min-width: 44px; text-align: right; }""",
     """  .rm-zoom { font: var(--t-xs) var(--mono); color: var(--dg-faint); min-width: 44px; text-align: right; }""",
     "zoom level")
once("""    font-size: 12px; color: var(--dg-faint); background: var(--dg-glass);
    border: 1px solid var(--dg-line); border-radius: 7px; padding: 3px 9px; transition: color .25s, border-color .25s;""",
     """    font-size: var(--t-xs); color: var(--dg-faint); background: var(--dg-glass);
    border: 1px solid var(--dg-line); border-radius: var(--r-box); padding: var(--s-1) var(--s-3); transition: color var(--m-base), border-color var(--m-base);""",
     "map hint")
once("""    border: 1px solid var(--dg-line); border-radius: 8px; padding: 7px 11px;
    color: var(--dg-text); font-size: 13.5px; line-height: 1.4; display: flex; flex-direction: column; gap: 2px;
  }
  .rm-info[hidden] { display: none; }
  .rm-info span { color: var(--dg-ink); font-size: 12px; }""",
     """    border: 1px solid var(--dg-line); border-radius: var(--r-box); padding: var(--s-2) var(--s-4);
    color: var(--dg-text); font-size: var(--t-sm); line-height: 1.4; display: flex; flex-direction: column; gap: var(--s-1);
  }
  .rm-info[hidden] { display: none; }
  .rm-info span { color: var(--dg-ink); font-size: var(--t-xs); }""",
     "map info")
once("""    display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; color: var(--dg-text);
    background: var(--dg-glass); border: 1px solid var(--dg-line); border-radius: 7px; padding: 3px 9px;
  }
  .rm-pname .c { font: 11.5px var(--mono); color: var(--dg-faint); font-weight: 400; }
  .rm-caption { margin-top: 6px; }""",
     """    display: flex; align-items: center; gap: var(--s-2); font-size: var(--t-sm); font-weight: 600; color: var(--dg-text);
    background: var(--dg-glass); border: 1px solid var(--dg-line); border-radius: var(--r-box); padding: var(--s-1) var(--s-3);
  }
  .rm-pname .c { font: var(--t-xs) var(--mono); color: var(--dg-faint); font-weight: 400; }
  .rm-caption { margin-top: var(--s-2); }""",
     "map name")

# ---- the play control: a Pill ----
once("""    display: flex; align-items: center; gap: 10px; padding: 4px 14px 4px 4px;
    background: var(--dg-glass); border: 1px solid var(--dg-line); border-radius: 999px;""",
     """    display: flex; align-items: center; gap: var(--s-3); padding: var(--s-1) var(--s-5) var(--s-1) var(--s-1);
    background: var(--dg-glass); border: 1px solid var(--dg-line); border-radius: var(--r-pill);""",
     "play control")
once("""  .rp-clock { font: 600 16px/1 var(--mono); font-variant-numeric: tabular-nums; color: var(--dg-text); min-width: 3.4em; }
  .rp-clock.still { color: var(--dg-faint); font-weight: 500; }""",
     """  .rp-clock { font: 600 var(--t-md)/1 var(--mono); font-variant-numeric: tabular-nums; color: var(--dg-text); min-width: 3.4em; }
  .rp-clock.still { color: var(--dg-faint); font-weight: 400; }""",
     "replay clock")

# ---- the player boxes under the view ----
once("""  .rp-places { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 8px; margin-top: 12px; }
  .rp-place {
    position: relative; text-align: left; min-width: 0;
    display: flex; flex-direction: column; gap: 3px;
    padding: 8px 11px 9px 15px; border-radius: 8px;
    border: 1px solid var(--line); background: var(--bg-2); color: var(--fg);
    font-size: 13px; line-height: 1.3; transition: opacity .2s, border-color .2s, background .12s;
  }""",
     """  .rp-places { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: var(--s-3); margin-top: var(--s-4); }
  .rp-place {
    position: relative; text-align: left; min-width: 0;
    display: flex; flex-direction: column; gap: var(--s-1);
    padding: var(--s-3) var(--s-4) var(--s-3) var(--s-5); border-radius: var(--r-box);
    border: 1px solid var(--line); background: var(--bg-2); color: var(--fg);
    font-size: var(--t-sm); line-height: 1.3; transition: opacity var(--m-base), border-color var(--m-base), background var(--m-fast);
  }""",
     "player boxes")
once("""  .rp-place .top { display: flex; align-items: baseline; gap: 8px; min-width: 0; }""",
     """  .rp-place .top { display: flex; align-items: baseline; gap: var(--s-3); min-width: 0; }""",
     "player box top line")
once("""  .rp-place .cl { font: 12px var(--mono); font-variant-numeric: tabular-nums; color: var(--fg-faint); flex: none; }
  .rp-place .at { color: var(--fg-dim); font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }""",
     """  .rp-place .cl { font: var(--t-xs) var(--mono); font-variant-numeric: tabular-nums; color: var(--fg-faint); flex: none; }
  .rp-place .at { color: var(--fg-dim); font-size: var(--t-xs); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }""",
     "player box details")
once("""  .rp-note { margin-top: 10px; }""",
     """  .rp-note { margin-top: var(--s-3); }""",
     "replay note")
once("""  @media (pointer: coarse) { .rm-tools button { min-width: 42px; height: 42px; font-size: 17px; } }""",
     """  @media (pointer: coarse) { .rm-tools button { min-width: 42px; height: 42px; font-size: var(--t-lg); } }""",
     "map buttons by touch")
once("""    #rp-type button { flex: 1; padding: 6px 4px; font-size: 12.5px; }
    .rp-places { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
    .rp-place { padding: 7px 9px 8px 14px; }""",
     """    #rp-type button { flex: 1; padding: var(--s-2) var(--s-1); font-size: var(--t-sm); }
    .rp-places { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--s-2); }
    .rp-place { padding: var(--s-2) var(--s-3) var(--s-2) var(--s-5); }""",
     "narrow replay")

# ---- a stale comment left by the racing chrome step ----
once("""  /* compact per-player pill for the mobile strip */
  /* A Pill, compact""",
     """  /* A Pill, compact""",
     "doubled comment")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("replay chrome retrofitted")
