# -*- coding: utf-8 -*-
"""Bring the name picker onto the design language.

The name picker's .np-card was the third spelling of "card" the design study
found, and it was never a Card: it is a dialog, so it becomes a Panel and
takes the dialog's shape, surface and shadow from .panel instead of its own
14px corners, --raised ground and private shadow. That makes it the same
colour as every other dialog in the game, a shade darker than it was on the
dark theme.

Its error and its info line become Notes. Both sit on the name field and are
about it, so they are the standard's carve-out: left-aligned at the field's
edge rather than centred.

The entrance keeps its fade and lift but loses its overshoot. --e-spring is
kept for arrivals - a checkpoint, the finish - and a dialog opening is not one.

The guest note, the name-twin warning and the dice button beside the name in
the side panel belong to the side panel and wait for it.
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
once("""    display: flex; align-items: center; justify-content: center; padding: 16px;
  }
  #namepick[hidden] { display: none; }
  .np-card {
    width: min(420px, 100%); background: var(--raised); border: 1px solid var(--line);
    border-radius: 14px; padding: 24px; box-shadow: 0 24px 60px var(--shadow);
    display: flex; flex-direction: column; gap: 12px;
    animation: np-in .22s cubic-bezier(.2, 1.2, .4, 1) both;
  }
  .np-card h2 { margin: 0; font-size: 21px; letter-spacing: -.3px; }
  .np-card p { margin: 0; }
  .np-sub { color: var(--fg-dim); font-size: 14px; line-height: 1.45; }
  .np-error {
    color: var(--bad-fg); background: var(--bad-bg); border: 1px solid var(--bad-line);
    border-radius: 8px; padding: 8px 11px; font-size: 13.5px;
  }
  .np-error[hidden] { display: none; }
  .np-note {
    color: var(--fg); background: var(--info-bg); border: 1px solid var(--info-line);
    border-radius: 8px; padding: 8px 11px; font-size: 13.5px; line-height: 1.45;
  }
  .np-note[hidden] { display: none; }
  .np-row { display: flex; gap: 8px; }
  .np-row input { flex: 1; min-width: 0; font-size: 17px; padding: 11px 13px; }
  .np-roll {
    flex: none; width: 50px; font-size: 22px; line-height: 1; padding: 0;
    display: inline-flex; align-items: center; justify-content: center;
  }
  .np-roll.rolling span { display: inline-block; animation: np-spin .6s linear infinite; }
  .np-hint { color: var(--fg-faint); font-size: 12.5px; }
  .np-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
  .np-actions button { width: 100%; }
  .np-guest-note { color: var(--fg-faint); font-size: 12px; text-align: center; line-height: 1.4; }""",
     """    display: flex; align-items: center; justify-content: center; padding: var(--s-5);
  }
  #namepick[hidden] { display: none; }
  /* A Panel: the shape, surface and shadow come from .panel. What is its own
     is the narrower width and the stack of lines with even gaps between. */
  .np-card {
    width: min(420px, 100%);
    display: flex; flex-direction: column; gap: var(--s-4);
    animation: np-in var(--m-base) var(--e-out) both;
  }
  .np-card h2 { margin: 0; }
  .np-card p { margin: 0; }
  /* Balanced, so the last line of the explanation never ends on one word. */
  .np-sub { color: var(--fg-dim); font-size: var(--t-md); line-height: 1.45; text-wrap: pretty; }
  .np-error[hidden] { display: none; }
  .np-note { line-height: 1.45; }
  .np-note[hidden] { display: none; }
  .np-row { display: flex; gap: var(--s-3); }
  .np-row input { flex: 1; min-width: 0; font-size: var(--t-lg); padding: var(--s-4); }
  .np-roll {
    flex: none; width: 50px; font-size: var(--t-xl); line-height: 1; padding: 0;
    display: inline-flex; align-items: center; justify-content: center;
  }
  .np-roll.rolling span { display: inline-block; animation: np-spin var(--m-slow) linear infinite; }
  .np-hint { color: var(--fg-faint); font-size: var(--t-xs); }
  .np-actions { display: flex; flex-direction: column; gap: var(--s-3); margin-top: var(--s-1); }
  .np-actions button { width: 100%; }
  .np-guest-note { color: var(--fg-faint); font-size: var(--t-xs); text-align: center; line-height: 1.4; }""",
     "name picker css")

# ---- markup: onto the base classes ----
once("""    <div class="np-card">
      <h2 id="np-title">""",
     """    <div class="panel np-card">
      <h2 id="np-title">""",
     "name picker panel")
once("""<p class="np-error" id="np-error" role="alert" hidden></p>""",
     """<p class="note bad at-field np-error" id="np-error" role="alert" hidden></p>""",
     "name error note")
once("""<p class="np-note" id="np-note" role="status" hidden></p>""",
     """<p class="note info at-field np-note" id="np-note" role="status" hidden></p>""",
     "name info note")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("name picker retrofitted")
