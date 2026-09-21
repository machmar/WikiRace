# -*- coding: utf-8 -*-
"""Bring race setup onto the design language.

Race setup is the densest screen in the game: fields, a typeahead, the
checkpoint list, a fold of settings with toggles and a stepper, and the list
of who is ready.

Three of its pieces are shared, and are done here because this is where most
of their weight is - the changes elsewhere are a pixel at most:

- the segmented control (.seg) is also the hub tabs, the spectator bar and the
  replay's view switcher;
- the dropdown (.dd) is also the spectator's pick of whom to watch;
- both dropdown lists hard-coded rgba(0, 0, 0, .5) in their shadow, which went
  muddy on the light themes. They are popovers, so they take --el-lift.

The players list becomes a Row in a Card, so it matches the lobby's player
list exactly instead of sitting three pixels tighter.

The .chips and .chip.pick rules - "checkpoint chips in the configurator" - go:
the checkpoint list replaced them, and nothing builds either class any more.

Left alone, because they are the size of what they draw rather than a place on
the scale: the track of the toggle switch, the stepper's arrow buttons and
their glyph, the back button's square and its icon, and the column widths of
the checkpoint rows.
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


def exactly(old, new, n, label):
    global s
    assert s.count(old) == n, (label, "expected", n, "found", s.count(old))
    s = s.replace(old, new)


# ---- the dropdown, shared with the spectator bar ----
once("""    justify-content: space-between; gap: 8px;
    background: var(--bg); border: 1px solid var(--line);
  }""",
     """    justify-content: space-between; gap: var(--s-3);
    background: var(--bg); border: 1px solid var(--line);
  }""",
     "dropdown button")
once("""  .dd-btn .caret { color: var(--fg-faint); font-size: 10px; }
  .dd-list {
    position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 75;
    background: var(--bg-3); border: 1px solid var(--line); border-radius: 8px;
    max-height: 250px; overflow-y: auto; box-shadow: 0 12px 32px rgba(0,0,0,.5);
  }
  .dd-item { padding: 7px 11px; font-size: 13.5px; cursor: pointer; }""",
     """  .dd-btn .caret { color: var(--fg-faint); font-size: var(--t-xs); }
  /* A list that opens over the page is a popover, so it lifts like a Tip. */
  .dd-list {
    position: absolute; top: calc(100% + var(--s-1)); left: 0; right: 0; z-index: 75;
    background: var(--bg-3); border: 1px solid var(--line); border-radius: var(--r-box);
    max-height: 250px; overflow-y: auto; box-shadow: var(--el-lift);
  }
  .dd-item { padding: var(--s-2) var(--s-4); font-size: var(--t-sm); cursor: pointer; }""",
     "dropdown list")

# ---- the typeahead ----
once("""  .ta-list {
    position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 70;
    background: var(--bg-3); border: 1px solid var(--line); border-radius: 8px;
    max-height: 230px; overflow-y: auto; box-shadow: 0 12px 32px rgba(0,0,0,.5);
  }
  .ta-list.up { top: auto; bottom: calc(100% + 4px); }
  .ta-item { padding: 7px 11px; font-size: 13.5px; cursor: pointer; }""",
     """  .ta-list {
    position: absolute; top: calc(100% + var(--s-1)); left: 0; right: 0; z-index: 70;
    background: var(--bg-3); border: 1px solid var(--line); border-radius: var(--r-box);
    max-height: 230px; overflow-y: auto; box-shadow: var(--el-lift);
  }
  .ta-list.up { top: auto; bottom: calc(100% + var(--s-1)); }
  .ta-item { padding: var(--s-2) var(--s-4); font-size: var(--t-sm); cursor: pointer; }""",
     "typeahead")

once("""  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }""",
     """  .two { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-4); }""",
     "two columns")

# ---- the players list: a Row in a Card, like the lobby's ----
once("""  .ready-row {
    display: flex; align-items: center; gap: 9px; padding: 6px 0;
    border-bottom: 1px solid var(--line-soft); font-size: 13.5px;
  }
  .ready-row:last-child { border-bottom: none; }
  .ready-row .sub { margin-left: auto; }
  .tick {
    width: 20px; height: 20px; border-radius: 50%; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; background: var(--bg-3); color: var(--fg-faint);""",
     """  .ready-row .sub { margin-left: auto; }
  .tick {
    width: 20px; height: 20px; border-radius: 50%; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: var(--t-xs); background: var(--bg-3); color: var(--fg-faint);""",
     "ready rows")
once("""'<div class="ready-row"><span class="tick'""",
     """'<div class="row in-card ready-row"><span class="tick'""",
     "ready row markup")

# ---- the toggle switch ----
once("""  .track {
    width: 36px; height: 20px; border-radius: 999px; background: var(--bg-3);
    border: 1px solid var(--line); position: relative; transition: background .15s, border-color .15s; flex: none;
  }
  .track::after {
    content: ""; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
    border-radius: 50%; background: var(--fg-faint); transition: transform .15s, background .15s;
  }""",
     """  .track {
    width: 36px; height: 20px; border-radius: var(--r-pill); background: var(--bg-3);
    border: 1px solid var(--line); position: relative; transition: background var(--m-fast), border-color var(--m-fast); flex: none;
  }
  .track::after {
    content: ""; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
    border-radius: 50%; background: var(--fg-faint); transition: transform var(--m-fast), background var(--m-fast);
  }""",
     "toggle track")
once("""  .toggle { display: flex; align-items: center; gap: 9px; cursor: pointer; user-select: none; font-size: 13px; }""",
     """  .toggle { display: flex; align-items: center; gap: var(--s-3); cursor: pointer; user-select: none; font-size: var(--t-sm); }""",
     "toggle")

# ---- the checkpoint list ----
# The rows round their own corners inside the box, so their radius is the
# box's less its border; otherwise the corners poke through by a pixel.
once("""  .cp-box { border: 1px solid var(--line); border-radius: 9px; }
  .cp-box > div:first-child > .cp-row:first-child { border-radius: 8px 8px 0 0; }
  .cp-box > .cp-add:last-child { border-radius: 0 0 8px 8px; }
  .cp-box > div:first-child:empty + .cp-add { border-top: 0; border-radius: 8px; }
  .cp-row {
    display: grid; grid-template-columns: 1fr 46px repeat(4, 28px); align-items: center; gap: 6px;
    padding: 4px 8px 4px 12px; background: var(--bg-3);
  }""",
     """  .cp-box { --cp-in: calc(var(--r-box) - 1px); border: 1px solid var(--line); border-radius: var(--r-box); }
  .cp-box > div:first-child > .cp-row:first-child { border-radius: var(--cp-in) var(--cp-in) 0 0; }
  .cp-box > .cp-add:last-child { border-radius: 0 0 var(--cp-in) var(--cp-in); }
  .cp-box > div:first-child:empty + .cp-add { border-top: 0; border-radius: var(--cp-in); }
  .cp-row {
    display: grid; grid-template-columns: 1fr 46px repeat(4, 28px); align-items: center; gap: var(--s-2);
    padding: var(--s-1) var(--s-3) var(--s-1) var(--s-4); background: var(--bg-3);
  }""",
     "checkpoint box and rows")
once("""  .cp-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; }
  .cp-row .slot {
    padding: 1px 0; font-size: 11px; line-height: 1.6; text-align: center; border-radius: 999px;""",
     """  .cp-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--t-sm); }
  /* The slot is a Pill whose height comes from its line-height; the single
     pixel only keeps the number optically centred. */
  .cp-row .slot {
    padding: 1px 0; font-size: var(--t-xs); line-height: 1.6; text-align: center; border-radius: var(--r-pill);""",
     "checkpoint name and slot")
once("""    padding: 0; height: 24px; font-size: 11px; line-height: 1;""",
     """    padding: 0; height: 24px; font-size: var(--t-xs); line-height: 1;""",
     "checkpoint buttons")
once("""  .cp-add { grid-template-columns: 1fr auto auto; gap: 8px; padding: 6px 8px; background: var(--bg-2); }
  .cp-add .ta { min-width: 0; }
  .cp-add input[type=text] { border-color: transparent; background: transparent; padding-left: 4px; }
  .cp-add button { padding: 5px 12px; font-size: 13px; }
  .cp-add .icon { padding: 5px 9px; }
  .cp-phrase { margin: 8px 0 0; }""",
     """  .cp-add { grid-template-columns: 1fr auto auto; gap: var(--s-3); padding: var(--s-2) var(--s-3); background: var(--bg-2); }
  .cp-add .ta { min-width: 0; }
  .cp-add input[type=text] { border-color: transparent; background: transparent; padding-left: var(--s-1); }
  .cp-add button { font-size: var(--t-sm); }
  .cp-add .icon { padding: var(--s-2) var(--s-3); }
  .cp-phrase { margin: var(--s-3) 0 0; }""",
     "checkpoint add row")

# ---- the stepper ----
once("""  .num { display: flex; align-items: center; gap: 9px; }
  .num input { flex: 1; min-width: 0; }
  .num .unit { flex: none; color: var(--fg-dim); font-size: 13px; }""",
     """  .num { display: flex; align-items: center; gap: var(--s-3); }
  .num input { flex: 1; min-width: 0; }
  .num .unit { flex: none; color: var(--fg-dim); font-size: var(--t-sm); }""",
     "stepper")
once("""margin-left: -5px; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }""",
     """margin-left: calc(-1 * var(--s-2)); border: 1px solid var(--line); border-radius: var(--r-box); overflow: hidden; }""",
     "stepper arrows box")
# The arrows are glyphs sized to their eighteen-pixel buttons, not text.
once("""background: var(--bg-3); color: var(--fg-dim); font-size: 8px; line-height: 1; }""",
     """background: var(--bg-3); color: var(--fg-dim); font-size: 8px; line-height: 1; } /* a glyph sized to its 18px button */""",
     "stepper glyph")

# ---- the fold and the fields ----
once("""  .fold-btn { width: 100%; display: flex; align-items: center; gap: 10px; text-align: left; }
  .fold-btn .fold-sum { flex: 1; color: var(--fg-dim); font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .fold-btn .caret { color: var(--fg-faint); font-size: 10px; transition: transform .15s; }""",
     """  .fold-btn { width: 100%; display: flex; align-items: center; gap: var(--s-3); text-align: left; }
  .fold-btn .fold-sum { flex: 1; color: var(--fg-dim); font-size: var(--t-sm); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .fold-btn .caret { color: var(--fg-faint); font-size: var(--t-xs); transition: transform var(--m-base); }""",
     "fold")
once("""  .fold-body { margin-top: 12px; }""",
     """  .fold-body { margin-top: var(--s-4); }""",
     "fold body")
once("""  .field { margin-bottom: 13px; }
  .field label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: .9px; color: var(--fg-faint); margin-bottom: 5px; font-weight: 600; }""",
     """  .field { margin-bottom: var(--s-4); }
  .field label { display: block; font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .08em; color: var(--fg-faint); margin-bottom: var(--s-2); font-weight: 600; }
  /* A hint inside a label is a sentence, not part of the label, so it must not
     inherit the label's capitals - otherwise it shouts. */
  .field label .muted { text-transform: none; letter-spacing: normal; font-weight: 400; }""",
     "fields")

# ---- the segmented control, shared with the hub, spectator bar and replay ----
once("""  .seg { display: flex; border: 1px solid var(--line); border-radius: 7px; overflow: hidden; }
  .seg button { border: none; border-radius: 0; background: transparent; padding: 6px 13px; font-size: 13px; }""",
     """  .seg { display: flex; border: 1px solid var(--line); border-radius: var(--r-box); overflow: hidden; }
  .seg button { border: none; border-radius: 0; background: transparent; padding: var(--s-2) var(--s-4); font-size: var(--t-sm); }""",
     "segmented control")

# ---- dead: the chips the checkpoint list replaced ----
once("""  /* checkpoint chips in the configurator */
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; min-height: 22px; align-items: center; }
  .chip.pick { display: inline-flex; align-items: center; gap: 6px; max-width: none; }
  .chip.pick button {
    border: none; background: none; color: var(--fg-faint); padding: 0 0 0 2px;
    font-size: 15px; line-height: 1; cursor: pointer;
  }
  .chip.pick button:hover { color: var(--bad); background: none; }
""",
     "",
     "dead chips")

# ---- the markup's own spacing ----
# Everything between fields sits on the same rhythm as the fields themselves.
once("""'<div class="hstack" style="margin-bottom:16px">'""",
     """'<div class="hstack" style="margin-bottom:var(--s-4)">'""",
     "random buttons row")
once("""'<div class="seg wide" id="c-preset" style="margin-bottom:10px">'""",
     """'<div class="seg wide" id="c-preset" style="margin-bottom:var(--s-3)">'""",
     "presets")
exactly("""style="margin-top:8px"><div class="track"></div>""",
        """style="margin-top:var(--s-3)"><div class="track"></div>""", 5, "toggle spacing")
once("""'<div class="two" style="margin-top:14px">'""",
     """'<div class="two" style="margin-top:var(--s-5)">'""",
     "toc and limit row")
once("""<div id="c-anyway" class="tiny" style="text-align:center;margin-top:9px" hidden>""",
     """<div id="c-anyway" class="tiny" style="text-align:center;margin-top:var(--s-3)" hidden>""",
     "start anyway")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("race setup retrofitted")
