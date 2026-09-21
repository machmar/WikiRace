# -*- coding: utf-8 -*-
"""Step zero: the pieces every screen shares, and the seven base classes.

Every screen leans on the base button, the text fields, the small-print
helpers, the standings table and the dialog, so these are brought onto the
design language once, here, rather than by whichever screen happened to get to
them first and silently changed all the others.

It also adds the base classes the standard names, and switches the lobby over
to them, so the documented pattern - class="card lobby-card" - is real code
and not just advice.

Deliberately left alone, each for its own screen: the side panel sections, the
racer rows, the #company pill and the overlay behind a dialog, whose .93 scrim
is much darker than the --scrim token and needs a decision rather than a snap.
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


# ---- Control: the button, the text field and the select ----
# Buttons keep font: inherit. A Control takes the size of wherever it sits -
# fifteen pixels on an open screen, less in the side panel - and forcing one
# size on every button would be a restyle, not a snap.
once("""  button {
    font: inherit; cursor: pointer; color: var(--fg);
    background: var(--bg-3); border: 1px solid var(--line);
    padding: 7px 13px; border-radius: 7px;
    transition: background .12s, border-color .12s, transform .06s;
  }""",
     """  button {
    font: inherit; cursor: pointer; color: var(--fg);
    background: var(--bg-3); border: 1px solid var(--line);
    padding: var(--s-2) var(--s-4); border-radius: var(--r-box);
    /* The press is quicker than --m-fast on purpose: it is the one motion that
       has to feel like it happened under your finger. */
    transition: background var(--m-fast), border-color var(--m-fast), transform .06s;
  }""",
     "button")

once("""  input[type=text], input[type=number] {
    font: inherit; color: var(--fg); background: var(--bg);
    border: 1px solid var(--line); border-radius: 7px; padding: 7px 10px; width: 100%;
  }
  input[type=text]:focus, input[type=number]:focus { outline: none; border-color: var(--accent); }""",
     """  input[type=text], input[type=number] {
    font: inherit; color: var(--fg); background: var(--bg);
    border: 1px solid var(--line); border-radius: var(--r-box); padding: var(--s-2) var(--s-4); width: 100%;
  }
  /* A coloured border alone is easy to miss, especially for anyone who does
     not see the accent well; the ring is what makes focus unmistakable. */
  input[type=text]:focus, input[type=number]:focus {
    outline: none; border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent);
  }""",
     "text fields")

once("""  select {
    font: inherit; color: var(--fg); background: var(--bg);
    border: 1px solid var(--line); border-radius: 7px; padding: 7px 10px; width: 100%;
  }
  select:focus { outline: none; border-color: var(--accent); }""",
     """  select {
    font: inherit; color: var(--fg); background: var(--bg);
    border: 1px solid var(--line); border-radius: var(--r-box); padding: var(--s-2) var(--s-4); width: 100%;
  }
  select:focus { outline: none; border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }

  /* ---------- the seven pieces ----------
     docs/DesignLanguage.md. Every surface is one of these; a screen adds its
     own namespaced class beside the base one - class="card lobby-card" - and
     that class carries only what is particular to the screen. Control is the
     button, text field and select above; Panel is .panel, the dialog, below. */

  /* Pill: a standalone token you read. */
  .pill {
    display: inline-flex; align-items: center; gap: var(--s-2);
    background: var(--bg-3); border: 1px solid var(--line); color: var(--fg);
    border-radius: var(--r-pill); padding: var(--s-1) var(--s-4); font-size: var(--t-sm);
  }

  /* Row: one of many. Boxed on its own; inside a card it drops the box and is
     divided by a hairline instead, because a box inside a box is heavy. */
  .row {
    display: flex; align-items: center; gap: var(--s-3);
    background: var(--bg-3); border: 1px solid var(--line);
    border-radius: var(--r-box); padding: var(--s-3) var(--s-4); font-size: var(--t-sm);
  }
  .row.in-card {
    background: none; border: 0; border-bottom: 1px solid var(--line-soft);
    border-radius: 0; padding: var(--s-3) 0;
  }
  .row.in-card:last-child { border-bottom: none; }

  /* Note: one of one, tinted, and centred so it reads as a message rather than
     a row - except beside a field, where centring would detach it from the
     thing it is about. */
  .note {
    border-radius: var(--r-box); padding: var(--s-3) var(--s-4);
    font-size: var(--t-sm); text-align: center; border: 1px solid;
  }
  .note.at-field { text-align: left; }
  .note.good { background: var(--good-bg); border-color: var(--good-line); color: var(--good-fg); }
  .note.warn { background: var(--warn-bg); border-color: var(--warn-line); color: var(--warn-fg); }
  .note.bad  { background: var(--bad-bg);  border-color: var(--bad-line);  color: var(--bad-fg); }
  .note.info { background: var(--info-bg); border-color: var(--info-line); color: var(--fg); }

  /* Tip: floating, pointing at what is under it. Never in the way of a click. */
  .tip {
    background: var(--bg-3); border: 1px solid var(--line-strong); color: var(--fg);
    border-radius: var(--r-box); padding: var(--s-1) var(--s-3);
    font-size: var(--t-sm); box-shadow: var(--el-lift); pointer-events: none;
  }

  /* Card: a grouped thing among its siblings. No shadow - depth comes from the
     ground it sits on. */
  .card {
    background: var(--bg-2); border: 1px solid var(--line);
    border-radius: var(--r-card); padding: var(--s-5);
  }""",
     "select, and the seven pieces")

# ---- small print and helpers ----
once("""  .hstack { display: flex; align-items: center; gap: 9px; }
  .muted { color: var(--fg-dim); }
  .tiny { font-size: 12px; }
  .empty { color: var(--fg-faint); font-size: 13px; font-style: italic; padding: 3px 0; }""",
     """  .hstack { display: flex; align-items: center; gap: var(--s-3); }
  .muted { color: var(--fg-dim); }
  .tiny { font-size: var(--t-xs); }
  .empty { color: var(--fg-faint); font-size: var(--t-sm); font-style: italic; padding: var(--s-1) 0; }""",
     "helpers")

# ---- the standings table, shared by the lobby and the side panel ----
once("""  table.board { width: 100%; border-collapse: collapse; font-size: 13px; }
  table.board td { padding: 5px 0; border-bottom: 1px solid var(--line-soft); }""",
     """  table.board { width: 100%; border-collapse: collapse; font-size: var(--t-sm); }
  table.board td { padding: var(--s-2) 0; border-bottom: 1px solid var(--line-soft); }""",
     "board")
once("""  .sub { color: var(--fg-faint); font-size: 11px; }""",
     """  .sub { color: var(--fg-faint); font-size: var(--t-xs); }""",
     "board sub line")

# ---- Panel: the dialog ----
once("""  .panel {
    background: var(--bg-2); border: 1px solid var(--line); border-radius: 14px;
    padding: 28px 30px; max-width: 560px; width: 100%;
    box-shadow: 0 22px 60px rgba(0,0,0,.55);
  }
  .panel h2 { margin: 0 0 6px; font-size: 22px; letter-spacing: -.4px; }""",
     """  /* Panel: the container the rest sits inside. Rounded more than the cards in
     it, never less, and its shadow is built from --shadow so it stays clean on
     the light themes, where a literal black went muddy. */
  .panel {
    background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-panel);
    padding: var(--s-7); max-width: 560px; width: 100%;
    box-shadow: var(--el-float);
  }
  .panel h2 { margin: 0 0 var(--s-2); font-size: var(--t-xl); letter-spacing: -.02em; }""",
     "dialog panel")
once("""  .panel p.lede { margin: 0 0 20px; color: var(--fg-dim); font-size: 14px; }""",
     """  .panel p.lede { margin: 0 0 var(--s-6); color: var(--fg-dim); font-size: var(--t-md); }""",
     "dialog lede")
once("""  .panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }""",
     """  .panel-head { display: flex; align-items: center; gap: var(--s-3); margin-bottom: var(--s-2); }""",
     "dialog head")
once("""    .panel { padding: 20px 16px; }""",
     """    .panel { padding: var(--s-6) var(--s-5); }""",
     "dialog narrow")

# ---- big buttons: the lobby's and the name picker's ----
once("""  button.big { padding: 12px 26px; font-size: 15px; border-radius: 9px; }""",
     """  button.big { padding: var(--s-4) var(--s-7); font-size: var(--t-md); border-radius: var(--r-box); }""",
     "big button")

# ---- the lobby, onto the base classes ----
# The lobby card's own rule shrinks to nothing but what the base .card already
# says, so it goes; the class stays in the markup as the lobby's hook.
once("""  .lobby-card {
    background: var(--bg-2); border: 1px solid var(--line);
    border-radius: var(--r-card); padding: var(--s-5);
  }
  .lobby-card h3 {""",
     """  .lobby-card h3 {""",
     "lobby card rule")
once("""          <div class="lobby-card">
            <h3>In the lobby""",
     """          <div class="card lobby-card">
            <h3>In the lobby""",
     "lobby players card")
once("""          <div class="lobby-card">
            <h3>Standings</h3>""",
     """          <div class="card lobby-card">
            <h3>Standings</h3>""",
     "lobby standings card")
once("""<div class="lobby-card" id="share-card\"""",
     """<div class="card lobby-card" id="share-card\"""",
     "lobby share card")

once("""  .lp {
    display: flex; align-items: center; gap: var(--s-3); padding: var(--s-3) 0;
    border-bottom: 1px solid var(--line-soft); font-size: var(--t-sm);
  }
  .lp:last-child { border-bottom: none; }
  .lp .nm""",
     """  .lp .nm""",
     "lobby row rule")
once("""    '<div class="lp"><span class="swatch\"""",
     """    '<div class="row in-card lp"><span class="swatch\"""",
     "lobby row markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("step zero applied")
