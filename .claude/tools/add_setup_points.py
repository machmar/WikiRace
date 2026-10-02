# -*- coding: utf-8 -*-
"""Issue #33: race setup says what a race will pay before it starts.

Each setting carries a faint "+20%" while it is making the race harder, the
checkpoints label carries theirs, and the Game settings header the total. The
server says which rules count (`/api/score_rules`), so setup never promises
points the race won't pay.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")
s = io.open(PATH, encoding="utf-8").read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


def pct(rule):
    return '<span class="c-pct" data-rule="%s"></span>' % rule


# -- CSS ----------------------------------------------------------------------

once("""  .fold-btn[aria-expanded="true"] .caret { transform: rotate(180deg); }
""", """  .fold-btn[aria-expanded="true"] .caret { transform: rotate(180deg); }
  /* What race setup's rules add to the points: a setting carries its share
     while it is making the race harder, and the header carries the total,
     which stays in sight with the settings folded away. Faint, because it is
     there for whoever looks rather than something to act on. */
  .c-pct { font-family: var(--mono); font-size: var(--t-xs); font-weight: 400; color: var(--fg-faint);
           text-transform: none; letter-spacing: normal; white-space: nowrap; }
  .toggle .c-pct { margin-left: auto; }
  .fold-btn .c-points { flex-shrink: 0; font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-dim); white-space: nowrap; }
""", "css")

# -- markup -------------------------------------------------------------------

once("""'pin the ones that have to be made in this order)</span></label>' +""",
     """'pin the ones that have to be made in this order)</span> %s</label>' +""" % pct("checkpoints"),
     "checkpoints label")
once("""'<span class="fold-sum" id="c-settings-sum"></span><span class="caret">▼</span></button>' +""",
     """'<span class="fold-sum" id="c-settings-sum"></span><span class="c-points" id="c-points"></span>' +
    '<span class="caret">▼</span></button>' +""",
     "header total")
for rule, old, new in [
    ("hidden", """"<span>Show where opponents are</span></div>" +""",
     """'<span>Show where opponents are</span>%s</div>' +"""),
    ("no_back", """"<span>Allow the Back button</span></div>" +""",
     """'<span>Allow the Back button</span>%s</div>' +"""),
    ("no_find", """'shortcut, not the browser menu)</span></span></div>' +""",
     """'shortcut, not the browser menu)</span></span>%s</div>' +"""),
    ("no_reveal", """'(everyone still racing has to agree)</span></span></div>' +""",
     """'(everyone still racing has to agree)</span></span>%s</div>' +"""),
    ("no_hubs", """'<span>Ban hub pages <span class="muted tiny">(United States, WWII…)</span></span></div>' +""",
     """'<span>Ban hub pages <span class="muted tiny">(United States, WWII…)</span></span>%s</div>' +"""),
    ("no_tables", """"</span></span></div>" +""", """'</span></span>%s</div>' +"""),
    ("no_contents", """Table of contents</label>' +""", """Table of contents %s</label>' +"""),
    ("time_limit", """for="c-limit">Time limit</label>' +""", """for="c-limit">Time limit %s</label>' +"""),
]:
    once(old, new % pct(rule), rule)

# -- asking the server --------------------------------------------------------

once("""function renderCheckpointChips(ov) {
  const host = ov.querySelector("#c-chips");
  if (!host) return;
""", """/* What each setting adds to the points while it is making the race harder,
   and the total on the settings header. The server says which rules count,
   the same way it will when the race is scored, so setup can't promise points
   the race won't pay. Asked again on every change; an answer that arrives
   after a newer question has been asked is dropped. */
let setupPointsAsked = 0;
async function markSetupPoints(ov) {
  const asked = ++setupPointsAsked;
  const r = await post("/score_rules", cfg);
  if (asked !== setupPointsAsked || !ov.isConnected) return;
  const hard = r && r.ok ? r.hard : [], step = r && r.ok ? r.step : 0;
  const count = key => hard.filter(k => k === key).length;
  ov.querySelectorAll(".c-pct").forEach(el => {
    const n = el.dataset.rule === "checkpoints" ? count("checkpoint") + count("order") : count(el.dataset.rule);
    el.textContent = n ? "+" + n * step + "%" : "";
  });
  const total = ov.querySelector("#c-points");
  if (total) total.textContent = hard.length ? "points +" + hard.length * step + "%" : "";
}

function renderCheckpointChips(ov) {
  const host = ov.querySelector("#c-chips");
  if (!host) return;
  markSetupPoints(ov);
""", "markSetupPoints")
once("""    q("#c-settings-sum").textContent = named ? named + (notes.length ? " · " + notes.join(", ") : "")
                                             : notes.length ? notes.join(", ") : "everything allowed";
  };
""", """    q("#c-settings-sum").textContent = named ? named + (notes.length ? " · " + notes.join(", ") : "")
                                             : notes.length ? notes.join(", ") : "everything allowed";
    markSetupPoints(ov);
  };
""", "sync asks")

io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
