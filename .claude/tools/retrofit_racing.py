# -*- coding: utf-8 -*-
"""Bring the racing chrome onto the design language.

Racing chrome is everything around the article while a race is on: the top
bar with its goal line, clock and theme switch, the trail of pages, the
"someone's here too" pill, the contents list, the warning strip, the toast,
the reconnecting banner, and the strip of players on a phone.

The article itself - #article and everything inside it - is the standard's
carve-out and is not touched.

Three things here are named as pieces for the first time:

- The goal line's chips, its checkpoint markers and the phone's player strip
  are Pills, so they take .pill and keep only what is their own. A goal chip
  stays inline-block, because a title too long for its chip has to end in an
  ellipsis and a flex box will only clip it.
- The toast is a Note that floats: it carries a sentence and points at nothing,
  which is what separates it from a Tip. It takes the Note's padding and, like
  everything that floats, a lift - it had no shadow at all.
- The theme switch's knob keeps its spring. It travels and lands in a slot,
  which is what --e-spring is for; the value was already exactly the token's.

Left alone because they are the size of what they draw: the network dot and
its glow, the theme switch's track and knob, the coloured dots of who is here
and of each player on a phone, and the keyframe distances.
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


# ---- the top bar ----
once("""    display: flex; align-items: center; gap: 14px;
    padding: 9px 16px; background: var(--bg-2); border-bottom: 1px solid var(--line);
    min-height: 56px;
  }
  .brand { font-weight: 700; letter-spacing: -.3px; display: flex; align-items: center; gap: 8px; white-space: nowrap; }""",
     """    display: flex; align-items: center; gap: var(--s-5);
    padding: var(--s-3) var(--s-5); background: var(--bg-2); border-bottom: 1px solid var(--line);
    min-height: 56px;
  }
  .brand { font-weight: 700; letter-spacing: -.02em; display: flex; align-items: center; gap: var(--s-3); white-space: nowrap; }""",
     "top bar and brand")

# The goal line is a row of Pills, so it is set at the Pill's size.
once("""  #goal { display: flex; align-items: center; gap: 9px; flex: 1; min-width: 0; font-size: 14px; }
  .chip {
    background: var(--bg-3); border: 1px solid var(--line); border-radius: 999px;
    padding: 4px 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;
  }""",
     """  #goal { display: flex; align-items: center; gap: var(--s-3); flex: 1; min-width: 0; font-size: var(--t-sm); }
  /* A Pill. Inline-block rather than the Pill's flex, because a title too long
     for its chip has to end in an ellipsis, and a flex box only clips. */
  .chip {
    display: inline-block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px;
  }""",
     "goal line and chips")
once("""  .chip.lang {
    background: var(--raised); color: var(--fg-dim); font-size: 11px;
    letter-spacing: .6px; font-weight: 600; padding: 4px 9px;
  }""",
     """  .chip.lang {
    background: var(--raised); color: var(--fg-dim); font-size: var(--t-xs);
    letter-spacing: .06em; font-weight: 600; padding: var(--s-1) var(--s-3);
  }""",
     "language chip")

# The knob travels and lands in its slot: exactly what --e-spring is for.
once("""    transition: transform .2s cubic-bezier(.4, 1.3, .5, 1);
    pointer-events: none;""",
     """    transition: transform var(--m-base) var(--e-spring);
    pointer-events: none;""",
     "theme knob")
once("""    font-size: 13px; line-height: 1; color: var(--fg-faint);
    display: flex; align-items: center; justify-content: center;
  }""",
     """    font-size: var(--t-sm); line-height: 1; color: var(--fg-faint);
    display: flex; align-items: center; justify-content: center;
  }""",
     "theme buttons")

once("""  #btn-peek { display: inline-flex; align-items: center; gap: 6px; flex: none; }""",
     """  #btn-peek { display: inline-flex; align-items: center; gap: var(--s-2); flex: none; }""",
     "reveal button")
once("""  #btn-peek .cnt { font-family: var(--mono); font-size: 11.5px; opacity: .85; }

  #hud { display: flex; align-items: center; gap: 16px; }
  .stat { text-align: right; line-height: 1.15; }
  .stat .v { font-family: var(--mono); font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .stat .k { font-size: 10px; text-transform: uppercase; letter-spacing: .9px; color: var(--fg-faint); }""",
     """  #btn-peek .cnt { font-family: var(--mono); font-size: var(--t-xs); opacity: .85; }

  #hud { display: flex; align-items: center; gap: var(--s-5); }
  .stat { text-align: right; line-height: 1.15; }
  .stat .v { font-family: var(--mono); font-size: var(--t-xl); font-weight: 600; font-variant-numeric: tabular-nums; }
  .stat .k { font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .08em; color: var(--fg-faint); }""",
     "clock")

# ---- the article stage, around the article ----
once("""    display: flex; align-items: center; gap: 6px; padding: 7px 16px;
    background: var(--bg-2); border-bottom: 1px solid var(--line-soft);
    overflow-x: auto; white-space: nowrap; font-size: 12.5px; color: var(--fg-dim);""",
     """    display: flex; align-items: center; gap: var(--s-2); padding: var(--s-2) var(--s-5);
    background: var(--bg-2); border-bottom: 1px solid var(--line-soft);
    overflow-x: auto; white-space: nowrap; font-size: var(--t-sm); color: var(--fg-dim);""",
     "trail")

# Someone arriving on your page is an arrival, so the pill keeps its spring.
once("""    display: inline-flex; align-items: center; gap: 9px; max-width: calc(100% - 24px);
    margin-top: 10px; padding: 7px 15px 7px 10px; border-radius: 999px;
    background: var(--raised); border: 1px solid var(--accent-line); color: var(--fg);
    box-shadow: 0 8px 26px var(--shadow); font-size: 13.5px; line-height: 1.3;
    animation: company-in .32s cubic-bezier(.2, 1.3, .4, 1) both;
  }
  #company .pill.bump { animation: company-bump .42s ease-out; }""",
     """    display: inline-flex; align-items: center; gap: var(--s-3); max-width: calc(100% - 2 * var(--s-4));
    margin-top: var(--s-3); padding: var(--s-2) var(--s-5) var(--s-2) var(--s-3); border-radius: var(--r-pill);
    background: var(--raised); border: 1px solid var(--accent-line); color: var(--fg);
    box-shadow: var(--el-lift); font-size: var(--t-sm); line-height: 1.3;
    animation: company-in var(--m-base) var(--e-spring) both;
  }
  #company .pill.bump { animation: company-bump var(--m-base) var(--e-out); }""",
     "someone's here too")
once("""  #company .who i + i { margin-left: -6px; }""",
     """  #company .who i + i { margin-left: calc(-1 * var(--s-2)); }""",
     "who's here dots")
once("""  #company b { font-weight: 650; }""",
     """  #company b { font-weight: 600; }""",
     "who's here names")

once("""    border-right: 1px solid var(--line); padding: 14px 0 40px;
  }
  #toc-panel h4 {
    margin: 0 14px 10px; font-size: 10px; text-transform: uppercase;
    letter-spacing: 1.1px; color: var(--fg-faint); font-weight: 700;
  }
  #toc-panel a {
    display: block; padding: 5px 14px; font-size: 12.5px; line-height: 1.35;""",
     """    border-right: 1px solid var(--line); padding: var(--s-5) 0 var(--s-8);
  }
  #toc-panel h4 {
    margin: 0 var(--s-5) var(--s-3); font-size: var(--t-xs); text-transform: uppercase;
    letter-spacing: .1em; color: var(--fg-faint); font-weight: 700;
  }
  #toc-panel a {
    display: block; padding: var(--s-2) var(--s-5); font-size: var(--t-sm); line-height: 1.35;""",
     "contents")
# The indent is what says a heading is nested; the size only drops once, at the
# deepest level, where the fainter colour does the rest.
once("""  #toc-panel a.lv3 { padding-left: 26px; font-size: 12px; }
  #toc-panel a.lv4 { padding-left: 38px; font-size: 11.5px; color: var(--fg-faint); }
  #toc-panel .empty { padding: 0 14px; }""",
     """  #toc-panel a.lv3 { padding-left: var(--s-7); }
  #toc-panel a.lv4 { padding-left: var(--s-8); font-size: var(--t-xs); color: var(--fg-faint); }
  #toc-panel .empty { padding: 0 var(--s-5); }""",
     "contents levels")

# ---- the goal line's other pills, the warning strip, the toast ----
once("""  .cpcount {
    font-family: var(--mono); font-size: 11px; color: var(--fg-faint);
    padding: 0 2px;
  }""",
     """  .cpcount {
    font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-faint);
    padding: 0 var(--s-1);
  }""",
     "checkpoint count")
once("""    padding: 9px 16px; background: var(--warn-bg); border-bottom: 1px solid var(--warn-line);
    color: var(--warn-fg); font-size: 13px; font-weight: 600;""",
     """    padding: var(--s-3) var(--s-5); background: var(--warn-bg); border-bottom: 1px solid var(--warn-line);
    color: var(--warn-fg); font-size: var(--t-sm); font-weight: 600;""",
     "warning strip")
once("""  .cp {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 11px; border-radius: 999px;
    border: 1px solid var(--line); background: var(--bg-3); color: var(--fg-dim);
  }
  .cp .mark { font-size: 11px; }""",
     """  /* A Pill, quieter than the goal chips until it is made. */
  .cp { color: var(--fg-dim); }
  .cp .mark { font-size: var(--t-xs); }""",
     "checkpoint markers")
once("""  .cpn { margin-left: 5px; font-size: 10px; letter-spacing: .04em; color: var(--warn-fg); }""",
     """  .cpn { margin-left: var(--s-2); font-size: var(--t-xs); letter-spacing: .04em; color: var(--warn-fg); }""",
     "checkpoint order")

# A Note that floats: it carries a sentence and points at nothing.
once("""  #toast {
    position: absolute; bottom: 22px; left: 50%; transform: translateX(-50%);
    background: var(--bg-3); border: 1px solid var(--line); border-radius: 9px;
    padding: 9px 18px; font-size: 13.5px; z-index: 60; pointer-events: none;
    opacity: 0; transition: opacity .2s;
  }""",
     """  /* A Note that floats: it carries a sentence and points at nothing, which is
     what makes it a Note and not a Tip. Floating, it lifts. */
  #toast {
    position: absolute; bottom: var(--s-6); left: 50%; transform: translateX(-50%);
    background: var(--bg-3); border: 1px solid var(--line); border-radius: var(--r-box);
    padding: var(--s-3) var(--s-4); font-size: var(--t-sm); z-index: 60; pointer-events: none;
    box-shadow: var(--el-lift); opacity: 0; transition: opacity var(--m-base);
  }""",
     "toast")

# ---- the phone's strip of players ----
once("""  .mp {
    display: inline-flex; align-items: center; gap: 5px; flex: none;
    font-size: 11.5px; padding: 2px 8px 2px 6px; border-radius: 999px;
    background: var(--bg-3); border: 1px solid var(--line); color: var(--fg-dim);
    max-width: 42vw;
  }""",
     """  /* A Pill, compact: a phone has one thin strip for everybody. */
  .mp {
    flex: none; font-size: var(--t-xs); padding: var(--s-1) var(--s-3) var(--s-1) var(--s-2);
    color: var(--fg-dim); max-width: 42vw;
  }""",
     "mini players")
once("""  .mp .n { font-family: var(--mono); font-size: 11px; color: var(--fg-faint); }""",
     """  .mp .n { font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-faint); }""",
     "mini player count")

once("""    background: var(--warn); color: var(--bg); text-align: center;
    font-size: 12.5px; font-weight: 600; padding: 4px;""",
     """    background: var(--warn); color: var(--bg); text-align: center;
    font-size: var(--t-sm); font-weight: 600; padding: var(--s-1);""",
     "reconnecting banner")

# ---- phones ----
once("""    #toc-panel {
      position: fixed; top: 0; left: 0; bottom: 0; z-index: 80;
      width: min(290px, 82vw); border-right: 1px solid var(--line);
      transform: translateX(-101%); transition: transform .22s ease;
      box-shadow: 14px 0 44px rgba(0, 0, 0, .55); padding-top: 18px;
    }""",
     """    /* The shadow falls sideways because the drawer slides in from the side;
       its colour is the theme's, so it stays clean on the light themes. */
    #toc-panel {
      position: fixed; top: 0; left: 0; bottom: 0; z-index: 80;
      width: min(290px, 82vw); border-right: 1px solid var(--line);
      transform: translateX(-101%); transition: transform var(--m-base) var(--e-out);
      box-shadow: 14px 0 44px var(--shadow); padding-top: var(--s-6);
    }""",
     "contents drawer")
once("""    #topbar { gap: 6px; padding: 7px 6px; min-height: 46px; }""",
     """    #topbar { gap: var(--s-2); padding: var(--s-2); min-height: 46px; }""",
     "narrow top bar")
once("""    #goal { font-size: 12.5px; gap: 6px; }
    .chip { max-width: 34vw; padding: 3px 9px; }
    .cp { padding: 2px 8px; }
    #hud { gap: 10px; }
    .stat .v { font-size: 16px; }
    .stat .k { font-size: 9px; letter-spacing: .6px; }""",
     """    #goal { gap: var(--s-2); }
    .chip { max-width: 34vw; padding: var(--s-1) var(--s-3); }
    .cp { padding: var(--s-1) var(--s-3); }
    #hud { gap: var(--s-3); }
    .stat .v { font-size: var(--t-md); }
    .stat .k { letter-spacing: .06em; }""",
     "narrow goal and clock")
once("""    #theme button { width: 19px; height: 19px; font-size: 10.5px; }
    #btn-back, #btn-giveup, #btn-peek { padding: 6px 7px; font-size: 12.5px; }""",
     """    #theme button { width: 19px; height: 19px; font-size: var(--t-xs); }
    #btn-back, #btn-giveup, #btn-peek { padding: var(--s-2); font-size: var(--t-sm); }""",
     "narrow buttons")
once("""      font-size: 17px; line-height: 1; padding: 6px 10px; flex: none;""",
     """      font-size: var(--t-lg); line-height: 1; padding: var(--s-2) var(--s-3); flex: none;""",
     "menu buttons")
once("""      display: flex; gap: 6px; align-items: center;
      padding: 5px 10px; background: var(--bg-2);""",
     """      display: flex; gap: var(--s-2); align-items: center;
      padding: var(--s-2) var(--s-3); background: var(--bg-2);""",
     "mini player strip")

# ---- markup: the Pills ----
once("""  let html = '<span class="chip lang">'""",
     """  let html = '<span class="pill chip lang">'""",
     "language chip markup")
once("""             '<span class="chip"' + (race.lost""",
     """             '<span class="pill chip"' + (race.lost""",
     "start chip markup")
once("""      return '<span class="cp' + (hit ? " hit" : "") + '" title="checkpoint">' +""",
     """      return '<span class="pill cp' + (hit ? " hit" : "") + '" title="checkpoint">' +""",
     "checkpoint marker markup")
once("""          '<span class="chip target">' + esc(race.target) + "</span>";""",
     """          '<span class="pill chip target">' + esc(race.target) + "</span>";""",
     "target chip markup")
once("""    return '<span class="mp ' + cls + '" title="' +""",
     """    return '<span class="pill mp ' + cls + '" title="' +""",
     "mini player markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("racing chrome retrofitted")
