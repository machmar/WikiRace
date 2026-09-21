# -*- coding: utf-8 -*-
"""Bring the hub's Results and My run onto the design language.

The hub bar and the Results and My run tabs. Watching is the spectator view and
Replay has its own step; the countdown's rules sit in this part of the file but
belong with the big moments.

- The honours are Cards, not Notes: a grid of siblings, each an icon, a label
  and a name. The best-route box is a neutral box of content, so it is a Card
  too. The standard used to call both centred Notes; it now says what they are.
- My run is the canonical Row: boxed steps, with the stripe for the start, the
  checkpoints and the target. The steps sit a little closer, at the scale's
  nearest step.
- The finishing order is a list of Rows in a Card. Each finisher's route sits
  under their name, past the medal column, however that column's gap moves.
- "Click any step to re-read it" was an instruction set in the label's
  capitals; it becomes a hint in plain case. And the clause "checkpoints
  outlined in green" goes: checkpoints are outlined in amber - green is the
  target - and the steps already carry a "checkpoint" tag, so a sentence that
  leans on colour only told some players something, and told them wrong.
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


# ---- the hub bar and the panes ----
once("""  #hub-bar {
    display: flex; align-items: center; gap: 12px; padding: 9px 16px;""",
     """  #hub-bar {
    display: flex; align-items: center; gap: var(--s-4); padding: var(--s-3) var(--s-5);""",
     "hub bar")
once("""  #results-pane, #myrun-pane, #replay-pane { max-width: 860px; margin: 0 auto; padding: 24px 28px 60px; width: 100%; }

  .hub-h2 { font-size: 20px; margin: 0 0 4px; letter-spacing: -.3px; }
  .hub-sub { color: var(--fg-dim); font-size: 13.5px; margin: 0 0 20px; }
  .hub-sec { margin-bottom: 26px; }
  .hub-sec h4 {
    font-size: 10.5px; text-transform: uppercase; letter-spacing: 1.1px;
    color: var(--fg-faint); font-weight: 700; margin: 0 0 10px;
  }""",
     """  #results-pane, #myrun-pane, #replay-pane { max-width: 860px; margin: 0 auto; padding: var(--s-7) var(--s-7) var(--s-9); width: 100%; }

  .hub-h2 { font-size: var(--t-xl); margin: 0 0 var(--s-1); letter-spacing: -.02em; }
  .hub-sub { color: var(--fg-dim); font-size: var(--t-sm); margin: 0 0 var(--s-6); }
  .hub-sec { margin-bottom: var(--s-7); }
  .hub-sec h4 {
    font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .1em;
    color: var(--fg-faint); font-weight: 700; margin: 0 0 var(--s-3);
  }
  /* A hint inside a label is a sentence, so it keeps its own case. */
  .hub-sec h4 .muted { text-transform: none; letter-spacing: normal; font-weight: 400; }""",
     "panes and headings")

# ---- honours: Cards ----
once("""  .awards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }
  .award {
    background: var(--bg-2); border: 1px solid var(--line); border-radius: 10px;
    padding: 11px 13px; display: flex; gap: 10px; align-items: center;
  }
  .award .ic { font-size: 20px; }
  .award .t { font-size: 10.5px; text-transform: uppercase; letter-spacing: .8px; color: var(--fg-faint); font-weight: 700; }
  .award .v { font-weight: 600; font-size: 14px; }
  .award .d { font-size: 11.5px; color: var(--fg-dim); }

  .fact {
    background: var(--bg-2); border: 1px solid var(--line); border-radius: 10px;
    padding: 13px 15px; font-size: 13.5px; color: var(--fg-dim);
  }""",
     """  .awards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--s-3); }
  /* A Card: one of a grid of honours. */
  .award { display: flex; gap: var(--s-3); align-items: center; }
  .award .ic { font-size: var(--t-xl); }
  .award .t { font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .08em; color: var(--fg-faint); font-weight: 700; }
  .award .v { font-weight: 600; font-size: var(--t-sm); }
  .award .d { font-size: var(--t-xs); color: var(--fg-dim); }

  /* A Card holding a finding - the best route, or where the reader will show
     a step once one is picked. */
  .fact { font-size: var(--t-sm); color: var(--fg-dim); }""",
     "honours and facts")

# ---- my run: the canonical Row ----
once("""  .step {
    display: flex; align-items: center; gap: 11px; padding: 8px 11px;
    border: 1px solid var(--line); border-radius: 9px; margin-bottom: 7px;
    background: var(--bg-2); cursor: pointer; transition: border-color .12s, background .12s;
  }""",
     """  /* A Row, and the example the standard points at: boxed, one of many, with
     a stripe for the steps that mean something. */
  .step {
    margin-bottom: var(--s-2); cursor: pointer;
    transition: border-color var(--m-fast), background var(--m-fast);
  }""",
     "steps")
once("""  .step .n { font-family: var(--mono); color: var(--fg-faint); font-size: 12px; width: 20px; }
  .step .ti { flex: 1; font-weight: 600; font-size: 14px; }
  .step .at { font-family: var(--mono); font-size: 12px; color: var(--fg-dim); }
  .step .tag { font-size: 10px; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--line); color: var(--fg-faint); }""",
     """  .step .n { font-family: var(--mono); color: var(--fg-faint); font-size: var(--t-xs); width: 20px; }
  .step .ti { flex: 1; font-weight: 600; font-size: var(--t-sm); }
  .step .at { font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-dim); }
  .step .tag { font-size: var(--t-xs); padding: 1px var(--s-2); border-radius: var(--r-pill); border: 1px solid var(--line); color: var(--fg-faint); }""",
     "step parts")

# ---- the finishing order ----
once("""  .result-row { display: flex; align-items: baseline; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line-soft); }
  .result-row .medal { width: 26px; font-size: 16px; }
  .result-row .rn { flex: 1; font-weight: 600; }
  .result-row .rs { font-family: var(--mono); font-size: 13px; color: var(--fg-dim); }
  .path-line { font-size: 11.5px; color: var(--fg-faint); margin-left: 36px; word-break: break-word; line-height: 1.45; }""",
     """  /* Rows in a Card, lined up on the baseline so a medal sits with its name,
     and a size up from other lists: the finishing order is what this screen
     is for. */
  .result-row { align-items: baseline; font-size: var(--t-md); }
  .result-row .medal { width: 26px; font-size: var(--t-md); }
  .result-row .rn { flex: 1; font-weight: 600; }
  .result-row .rs { font-family: var(--mono); font-size: var(--t-sm); color: var(--fg-dim); }
  /* Under the name, past the medal column and the row's gap. */
  .path-line { font-size: var(--t-xs); color: var(--fg-faint); margin-left: calc(26px + var(--s-3)); word-break: break-word; line-height: 1.45; }""",
     "finishing order")

# ---- phones ----
once("""    #results-pane, #myrun-pane, #replay-pane { padding: 16px 14px 50px; }""",
     """    #results-pane, #myrun-pane, #replay-pane { padding: var(--s-5) var(--s-5) var(--s-8); }""",
     "narrow panes")

# ---- markup ----
once("""    '<div class="result-row"><span class="medal">' + (medals[i]""",
     """    '<div class="row in-card result-row"><span class="medal">' + (medals[i]""",
     "finisher row")
once("""    '<div class="result-row"><span class="medal">—</span>' +""",
     """    '<div class="row in-card result-row"><span class="medal">—</span>' +""",
     "gave-up row")
once("""        '<div class="award"><span class="ic">'""",
     """        '<div class="card award"><span class="ic">'""",
     "honour markup")
once("""    '<div class="fact" id="shortest-fact">Working out the shortest possible route…</div></div>';""",
     """    '<div class="card fact" id="shortest-fact">Working out the shortest possible route…</div></div>';""",
     "best route markup")
once("""  html += '<div class="hub-sec"><h4>Where you went — click any step to re-read it';
  if (stops.size) html += ' · checkpoints outlined in green';
  html += "</h4>";""",
     """  html += '<div class="hub-sec"><h4>Where you went <span class="muted">— click any step to re-read it</span></h4>';""",
     "my run heading")
once("""    return '<div class="step' + kind + '" data-i="' + i + '">' +""",
     """    return '<div class="row step' + kind + '" data-i="' + i + '">' +""",
     "step markup")
once("""    '<div id="myrun-reader" class="fact">Pick a step above to read it again.</div></div>';""",
     """    '<div id="myrun-reader" class="card fact">Pick a step above to read it again.</div></div>';""",
     "reader markup")
# The reader drops its box while it shows an article and takes it back for a
# message, so the message state has to carry the Card base as well.
once("""        reader.className = "fact";""",
     """        reader.className = "card fact";""",
     "reader message state")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("hub results retrofitted")
