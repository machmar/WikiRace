# -*- coding: utf-8 -*-
"""Bring the lobby onto the design language (docs/DesignLanguage.md).

Only rules that belong to the lobby are touched. The lobby also leans on
pieces every other screen shares - the base button, button.big, table.board,
.card - and snapping those here would change screens nobody has looked at,
so they wait for their own step.

Kept, per workflows.md, as a record of exactly what changed.
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


# ---- CSS ----

once("""  .lobby-inner { max-width: 820px; margin: 0 auto; padding: 40px 30px 60px; }
  .lobby-hero { text-align: center; margin-bottom: 30px; }
  .lobby-hero .flag { font-size: 46px; line-height: 1; margin-bottom: 10px; }
  .lobby-hero h1 { font-size: 30px; margin: 0 0 6px; letter-spacing: -.6px; }
  .lobby-hero .lede { margin: 0; color: var(--fg-dim); font-size: 14.5px; }
  #lobby-room { margin-top: 8px; }

  .lobby-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }""",
     """  .lobby-inner { max-width: 820px; margin: 0 auto; padding: var(--s-8) var(--s-7) var(--s-9); }
  .lobby-hero { text-align: center; margin-bottom: var(--s-7); }
  .lobby-hero .flag { font-size: var(--t-3xl); line-height: 1; margin-bottom: var(--s-3); }
  .lobby-hero h1 { font-size: var(--t-2xl); margin: 0 0 var(--s-2); letter-spacing: -.02em; }
  .lobby-hero .lede { margin: 0; color: var(--fg-dim); font-size: var(--t-md); }
  #lobby-room { margin-top: var(--s-3); }

  .lobby-cols { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-4); }""",
     "lobby hero and columns")

# The lobby cards are Cards in the standard's sense. They are not given the
# .card base class yet, because .card in this file is still the dialog class
# (a Panel) - see the note in DesignLanguage.md.
once("""  .lobby-card {
    background: var(--bg-2); border: 1px solid var(--line);
    border-radius: 12px; padding: 16px 18px;
  }
  .lobby-card h3 {
    margin: 0 0 12px; font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.1px;
    color: var(--fg-faint); font-weight: 700;
  }
  .lobby-actions { display: flex; gap: 12px; justify-content: center; margin-top: 26px; }""",
     """  .lobby-card {
    background: var(--bg-2); border: 1px solid var(--line);
    border-radius: var(--r-card); padding: var(--s-5);
  }
  .lobby-card h3 {
    margin: 0 0 var(--s-4); font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .1em;
    color: var(--fg-faint); font-weight: 700;
  }
  .lobby-actions { display: flex; gap: var(--s-4); justify-content: center; margin-top: var(--s-7); }""",
     "lobby cards and actions")

once("""  .lp {
    display: flex; align-items: center; gap: 10px; padding: 8px 0;
    border-bottom: 1px solid var(--line-soft); font-size: 14px;
  }
  .lp:last-child { border-bottom: none; }
  .lp .nm { font-weight: 600; }
  .lp .you { color: var(--accent); font-size: 11px; }
  .lp .state { margin-left: auto; font-size: 12px; color: var(--fg-faint); }""",
     """  .lp {
    display: flex; align-items: center; gap: var(--s-3); padding: var(--s-3) 0;
    border-bottom: 1px solid var(--line-soft); font-size: var(--t-sm);
  }
  .lp:last-child { border-bottom: none; }
  .lp .nm { font-weight: 600; }
  .lp .you { color: var(--accent); font-size: var(--t-xs); }
  .lp .state { margin-left: auto; font-size: var(--t-xs); color: var(--fg-faint); }""",
     "lobby player rows")

once("""    .lobby-inner { padding: 22px 14px 40px; }""",
     """    .lobby-inner { padding: var(--s-6) var(--s-5) var(--s-8); }""",
     "lobby narrow padding")

# ---- markup: the inline spacing ----

once("""<button id="lobby-ready" class="primary" style="width:100%;margin-top:12px">""",
     """<button id="lobby-ready" class="primary" style="width:100%;margin-top:var(--s-4)">""",
     "ready button")
once("""<div id="lobby-last" class="tiny muted" style="margin-top:10px"></div>""",
     """<div id="lobby-last" class="tiny muted" style="margin-top:var(--s-3)"></div>""",
     "last race line")
# The invite card sits under the two columns, so its gap matches theirs and the
# three read as one group.
once("""<div class="lobby-card" id="share-card" style="margin-top:16px" hidden>""",
     """<div class="lobby-card" id="share-card" style="margin-top:var(--s-4)" hidden>""",
     "share card")
once("""<p class="tiny muted" style="margin:0 0 10px" id="share-note">""",
     """<p class="tiny muted" style="margin:0 0 var(--s-3)" id="share-note">""",
     "share note")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("lobby retrofitted")
