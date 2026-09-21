# -*- coding: utf-8 -*-
"""Bring the side panel onto the design language.

Four sections - you, the racers, the standings and the play-by-play. The
standings table was done with the shared pieces.

- The racer rows become Rows in a Card, like the player lists in the lobby and
  in race setup, so every list of players in the game is drawn one way. Each
  row gains two pixels.
- The "someone else is called that" warning and the guest line were coloured
  text; they are messages about the name field, so they become Notes at the
  field's edge, the way the name picker shows the same messages.
- The rule chips under the racers are compact Pills.
- The highlight on your own racer row was the dark theme's blue written out as
  an rgba, so on the light themes it stayed the dark blue. It is now the
  theme's accent.
- The phone drawer's shadow takes the theme's colour.

The play-by-play ticker and feed are a log: fine print, glanced at and never
read, so they drop to --t-xs and keep their tight lines. Spacing them like
Rows would make an insignificant log look like a feature.

Left alone because they are the size of what they draw: the player colour
swatches, the standings' position column, and the single pixels that centre
the tiny pips on a racer's name.
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


# ---- the sections ----
once("""  .side-sec { border-bottom: 1px solid var(--line); padding: 14px 16px; }
  .side-sec h3 {
    margin: 0 0 11px; font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.1px;""",
     """  .side-sec { border-bottom: 1px solid var(--line); padding: var(--s-5); }
  .side-sec h3 {
    margin: 0 0 var(--s-4); font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .1em;""",
     "sections")

# ---- the racers: Rows in a Card ----
once("""  .racer {
    display: flex; align-items: center; gap: 9px; padding: 7px 0;
    border-bottom: 1px solid var(--line-soft);
  }
  .racer:last-child { border-bottom: none; }
  .swatch""",
     """  .swatch""",
     "racer row")
once("""  .racer .nm { font-weight: 600; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .racer .at { font-size: 11.5px; color: var(--fg-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }""",
     """  .racer .nm { font-weight: 600; font-size: var(--t-sm); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .racer .at { font-size: var(--t-xs); color: var(--fg-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }""",
     "racer name and page")
once("""  .racer .n { font-family: var(--mono); font-size: 15px; font-variant-numeric: tabular-nums; }""",
     """  .racer .n { font-family: var(--mono); font-size: var(--t-md); font-variant-numeric: tabular-nums; }""",
     "racer clicks")
# The pips are tiny Pills on the line of a name; the single pixels centre them
# optically against the name's capitals.
once("""  .racer .pip.cp {
    margin-left: 6px; font-size: 9.5px; font-weight: 700; letter-spacing: .5px;
    padding: 1px 6px; border-radius: 999px; vertical-align: 1px;""",
     """  .racer .pip.cp {
    margin-left: var(--s-2); font-size: var(--t-xs); font-weight: 700; letter-spacing: .04em;
    padding: 1px var(--s-2); border-radius: var(--r-pill); vertical-align: 1px;""",
     "checkpoint pip")
once("""  .racer.near .pip {
    margin-left: 6px; font-size: 9.5px; font-weight: 700; letter-spacing: .5px;
    text-transform: uppercase; padding: 1px 6px; border-radius: 999px;""",
     """  .racer.near .pip {
    margin-left: var(--s-2); font-size: var(--t-xs); font-weight: 700; letter-spacing: .04em;
    text-transform: uppercase; padding: 1px var(--s-2); border-radius: var(--r-pill);""",
     "one-away pip")
# Your own row bleeds to the section's edges, so its margin is the section's
# padding; its tint is the theme's accent rather than the dark theme's blue.
once("""  .racer.me { background: linear-gradient(90deg, rgba(88,166,255,.09), transparent); margin: 0 -16px; padding: 7px 16px; }""",
     """  .racer.me {
    background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 9%, transparent), transparent);
    margin: 0 calc(-1 * var(--s-5)); padding: var(--s-3) var(--s-5);
  }""",
     "your racer row")

# ---- the play-by-play: logs, so they stay dense ----
once("""  #ticker { max-height: 200px; overflow-y: auto; margin-bottom: 9px; }""",
     """  #ticker { max-height: 200px; overflow-y: auto; margin-bottom: var(--s-3); }""",
     "ticker box")
once("""    display: flex; align-items: baseline; gap: 6px; font-size: 12.5px;
    padding: 4px 0; border-bottom: 1px solid var(--line-soft);""",
     """    display: flex; align-items: baseline; gap: var(--s-2); font-size: var(--t-xs);
    padding: var(--s-1) 0; border-bottom: 1px solid var(--line-soft);""",
     "ticker lines")
once("""  .tk .cl { font-family: var(--mono); font-size: 11px; color: var(--fg-faint); }""",
     """  .tk .cl { font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-faint); }""",
     "ticker clicks")
once("""  #feed { max-height: 190px; overflow-y: auto; font-size: 12.5px; }
  #feed .e { padding: 3px 0; color: var(--fg-dim); border-bottom: 1px solid var(--line-soft); }""",
     """  /* A log is fine print: glanced at, never read, so it never competes with
     the racers above it. */
  #feed { max-height: 190px; overflow-y: auto; font-size: var(--t-xs); }
  #feed .e { padding: var(--s-1) 0; color: var(--fg-dim); border-bottom: 1px solid var(--line-soft); }""",
     "feed")

# ---- the rule chips: compact Pills ----
once("""  #rules { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }""",
     """  #rules { display: flex; flex-wrap: wrap; gap: var(--s-2); margin-bottom: var(--s-3); }""",
     "rule chips box")
once("""  .rule {
    font-size: 10.5px; padding: 2px 8px; border-radius: 999px;
    background: var(--bg-3); border: 1px solid var(--line); color: var(--fg-dim);
  }""",
     """  /* A Pill, compact: a race can carry half a dozen rules. */
  .rule { font-size: var(--t-xs); padding: var(--s-1) var(--s-3); color: var(--fg-dim); }""",
     "rule chips")

# ---- the name notes ----
once("""  #guest-note { margin-top: 8px; font-size: 12px; color: var(--fg-dim); line-height: 1.4; }""",
     """  #guest-note { margin-top: var(--s-3); line-height: 1.4; }""",
     "guest note")
once("""  #name-twin { margin-top: 8px; font-size: 12px; line-height: 1.4; color: var(--warn-fg); }""",
     """  #name-twin { margin-top: var(--s-3); line-height: 1.4; }""",
     "name twin")
once("""  #btn-rollname { flex: none; padding: 6px 9px; font-size: 15px; line-height: 1; }""",
     """  #btn-rollname { flex: none; padding: var(--s-2) var(--s-3); font-size: var(--t-md); line-height: 1; }""",
     "name dice")

# ---- phones: the drawer ----
once("""      transform: translateX(101%); transition: transform .22s ease;
      box-shadow: -14px 0 44px rgba(0, 0, 0, .55);""",
     """      transform: translateX(101%); transition: transform var(--m-base) var(--e-out);
      /* Sideways, because the drawer slides in from the side. */
      box-shadow: -14px 0 44px var(--shadow);""",
     "side drawer")

# ---- markup ----
once("""      <div id="name-twin" hidden>""",
     """      <div id="name-twin" class="note warn at-field" hidden>""",
     "name twin markup")
once("""      <div id="guest-note" hidden>""",
     """      <div id="guest-note" class="note info at-field" hidden>""",
     "guest note markup")
once("""<button id="btn-ready" style="width:100%;margin-top:11px">""",
     """<button id="btn-ready" style="width:100%;margin-top:var(--s-4)">""",
     "ready button")
once("""<button id="btn-reset" class="ghost tiny" style="padding:2px 7px;font-size:11px">""",
     """<button id="btn-reset" class="ghost tiny" style="padding:var(--s-1) var(--s-2)">""",
     "clear button")
once("""  setHTML(host, bits.map(b => '<span class="rule">'""",
     """  setHTML(host, bits.map(b => '<span class="pill rule">'""",
     "rule chip markup")
once("""    host.innerHTML = '<div class="racer me"><div class="swatch\"""",
     """    host.innerHTML = '<div class="row in-card racer me"><div class="swatch\"""",
     "lone racer markup")
once("""    return '<div class="racer' + (r.me ? " me" : "")""",
     """    return '<div class="row in-card racer' + (r.me ? " me" : "")""",
     "racer markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("side panel retrofitted")
