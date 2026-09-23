# -*- coding: utf-8 -*-
"""Issue #18: tell the others when somebody wants the target revealed.

Adds one thing and removes one thing. The new thing is a Tip that hangs off
the reveal button, says who asked and how the tally stands, and goes away by
itself; pressing it opens the vote card rather than casting a vote. The
removed thing is the grant toast, which said the same news in a place you
could not press and could barely see.

The reveal button itself is untouched, deliberately - see decisions.md.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI = os.path.join(ROOT, "ui.html")

s = io.open(UI, encoding="utf-8").read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


# ---------------------------------------------------------------- CSS
once(
    "  #btn-peek .cnt { font-family: var(--mono); font-size: var(--t-xs); opacity: .85; }\n",
    "  #btn-peek .cnt { font-family: var(--mono); font-size: var(--t-xs); opacity: .85; }\n"
    "\n"
    "  /* The reveal popup. A Tip, because it points at the button it is about,\n"
    "     and a pressable one, because the sentence saying a vote is open and the\n"
    "     way to answer it should not be two separate things. Like a pressable\n"
    "     Card it is a button that keeps its piece's shape; it carries a sentence\n"
    "     rather than a label, so it takes the Note's padding and tint. */\n"
    "  #reveal-tip { display: none; }\n"
    "  #reveal-tip:not([hidden]) {\n"
    "    position: fixed; z-index: 70; display: block; text-align: left;\n"
    "    /* Wide enough for a name and a tally on one line, and no wider. */\n"
    "    width: min(310px, calc(100vw - var(--s-6)));\n"
    "    margin-top: var(--s-2);              /* clears the caret */\n"
    "    padding: var(--s-3) var(--s-4) var(--s-6);   /* the drain sits in the extra bottom */\n"
    "    background: var(--warn-bg); border-color: var(--warn-line); color: var(--fg);\n"
    "    /* The Tip is unpressable by default; this is the one that is not. */\n"
    "    pointer-events: auto; line-height: 1.45;\n"
    "  }\n"
    "  #reveal-tip b { color: var(--warn-fg); }\n"
    "  #reveal-tip:hover { background: var(--warn-bg); border-color: var(--warn-fg); }\n"
    "  #reveal-tip .rv-sub {\n"
    "    display: flex; align-items: baseline; gap: var(--s-3);\n"
    "    font-size: var(--t-xs); color: var(--fg-dim); margin-top: var(--s-2);\n"
    "  }\n"
    "  #reveal-tip .rv-act { margin-left: auto; color: var(--warn-fg); font-weight: 600; white-space: nowrap; }\n"
    "  /* The caret is a square stood on its corner, so it takes the Tip's own\n"
    "     border and tint instead of needing a second colour. --rv-caret is set\n"
    "     from the button's middle when the Tip is placed, the same way the maps\n"
    "     are measured off the page rather than chosen. */\n"
    "  #reveal-tip::before {\n"
    "    content: \"\"; position: absolute; top: calc(var(--s-3) / -2);\n"
    "    right: var(--rv-caret, var(--s-6)); width: var(--s-3); height: var(--s-3);\n"
    "    background: var(--warn-bg);\n"
    "    border-left: 1px solid var(--warn-line); border-top: 1px solid var(--warn-line);\n"
    "    transform: rotate(45deg);\n"
    "  }\n"
    "  #reveal-tip.open:not([hidden]), #reveal-tip.open::before {\n"
    "    background: var(--good-bg); border-color: var(--good-line);\n"
    "  }\n"
    "  #reveal-tip.open b, #reveal-tip.open .rv-act { color: var(--good-fg); }\n"
    "  #reveal-tip.open:hover { background: var(--good-bg); border-color: var(--good-fg); }\n"
    "  /* It times out, and says so with a hairline draining over the twenty\n"
    "     seconds rather than a number counting down at someone mid-paragraph.\n"
    "     The twenty is repeated in REVEAL_TIP_MS and the two go together. */\n"
    "  #reveal-tip .rv-drain {\n"
    "    position: absolute; left: var(--s-4); right: var(--s-4); bottom: var(--s-3);\n"
    "    height: 2px;                         /* a rule, not a bar: thin enough to ignore */\n"
    "    border-radius: var(--r-pill); background: var(--warn-line);\n"
    "    transform-origin: left; animation: rv-drain 20s linear forwards;\n"
    "  }\n"
    "  #reveal-tip.open .rv-drain { background: var(--good-line); }\n"
    "  @keyframes rv-drain { to { transform: scaleX(0); } }\n"
    "  /* The drain is information as well as motion, so it stays put rather\n"
    "     than disappearing; the timer still takes the Tip away. */\n"
    "  @media (prefers-reduced-motion: reduce) {\n"
    "    #reveal-tip .rv-drain { animation: none; }\n"
    "  }\n",
    "css",
)

# ---------------------------------------------------------------- markup
once(
    '  <div id="scrim" hidden></div>\n',
    '  <div id="scrim" hidden></div>\n'
    '\n'
    '  <button type="button" id="reveal-tip" class="tip" hidden></button>\n',
    "markup",
)

# ---------------------------------------------------------------- the toast it replaces
once(
    "const peek = { title: null, html: null, loading: false, scroll: 0, seen: false };\n",
    "const peek = { title: null, html: null, loading: false, scroll: 0 };\n",
    "peek state",
)

once(
    '    btn.title = "Read the target page - agreed by everyone";\n'
    "    if (!peek.seen) {                        // announce the moment it opens\n"
    "      peek.seen = true;\n"
    '      toast("Everyone agreed — the target is open to study", 3200);\n'
    "    }\n"
    "  } else {\n"
    "    peek.seen = false;\n"
    "    const rows = (snap && snap.peek_tally) || [];\n",
    '    btn.title = "Read the target page - agreed by everyone";\n'
    "    // The news that it opened is the reveal Tip's to break, below: a toast\n"
    "    // could not be pressed, and this one wants to be the way in.\n"
    "  } else {\n"
    "    const rows = (snap && snap.peek_tally) || [];\n",
    "grant toast",
)

once(
    "    if (!$(\"peek-scrim\").hidden) closePeek();\n"
    "  }\n"
    "  renderVote(snap);\n"
    "}\n",
    "    if (!$(\"peek-scrim\").hidden) closePeek();\n"
    "  }\n"
    "  renderVote(snap);\n"
    "  // After the button, so the Tip measures where the button actually is.\n"
    "  renderRevealTip(snap);\n"
    "}\n",
    "renderPeek call",
)

# ---------------------------------------------------------------- the Tip itself
once(
    '$("btn-peek").onclick = () => {\n',
    '''/* ------------------------------------------------------------------ *
 * Saying out loud that somebody wants the target open
 *
 * The button has carried the tally for as long as the vote has existed, but
 * the button is in the chrome and the game is played in the article, so an
 * ask could pass a whole table by. This says it once, next to the button it
 * is about, and takes itself away. Pressing it opens the vote card rather
 * than casting a vote: being told a vote is open is not being asked to rush
 * it.
 *
 * It speaks to everyone, including people who have already answered, because
 * "three of us are waiting on you" is news to the three as well. What it will
 * not do is tell you about your own vote.
 * ------------------------------------------------------------------ */
const REVEAL_TIP_MS = 20000;               // in step with the drain in the CSS
const revealTip = { race: null, yes: [], mine: null, shown: null, up: null, timer: null };

function hideRevealTip() {
  clearTimeout(revealTip.timer);
  revealTip.timer = null;
  revealTip.up = null;
  setFlag($("reveal-tip"), "hidden", true);
}

/* Under the reveal button, with the caret on the button's middle however far
   the Tip had to slide to stay on screen. Measured off the page, like the
   maps, rather than chosen. */
function placeRevealTip() {
  const el = $("reveal-tip"), btn = $("btn-peek");
  if (!el || el.hidden || !btn || btn.hidden) return;
  const b = btn.getBoundingClientRect();
  const w = el.offsetWidth;
  const gutter = 12;                       // the gap the phone layout leaves at the edge
  const caretW = 9;                        // the square the caret is made of
  const left = Math.max(gutter, Math.min(b.right - w, window.innerWidth - w - gutter));
  el.style.left = left + "px";
  el.style.top = b.bottom + "px";
  // Kept off the corners: on a narrow phone the button can slide almost out of
  // reach, and a caret sitting on the rounded edge reads as a mistake rather
  // than as pointing at anything.
  const caret = left + w - (b.left + b.width / 2);
  el.style.setProperty("--rv-caret",
                       Math.round(Math.min(Math.max(caret, gutter), w - gutter - caretW)) + "px");
}

function announceReveal(key, open, lead, sub, act) {
  if (revealTip.shown === key) return;     // the tally moves on every snapshot; this must not
  revealTip.shown = key;
  revealTip.up = key;
  const el = $("reveal-tip");
  el.classList.toggle("open", open);
  // Written straight rather than through setHTML: a fresh drain node is what
  // restarts the twenty seconds.
  // The newlines are for the reading of it: this is a button, so its whole
  // text is its name, and without them a screen reader runs the sentence and
  // the tally together. Whitespace between blocks draws nothing.
  el.innerHTML = "<div>" + lead + "</div>\\n" +
                 '<div class="rv-sub"><span>' + sub + "</span>\\n" +
                 '<span class="rv-act">' + act + " →</span></div>\\n" +
                 '<div class="rv-drain"></div>';
  el.hidden = false;
  placeRevealTip();
  clearTimeout(revealTip.timer);
  revealTip.timer = setTimeout(hideRevealTip, REVEAL_TIP_MS);
}

function renderRevealTip(snap) {
  const race = snap && snap.race;
  if (!race) {
    revealTip.race = null; revealTip.yes = []; revealTip.mine = null; revealTip.shown = null;
    hideRevealTip();
    return;
  }

  const rows = snap.peek_tally || [];
  const yes = rows.filter(r => r.vote === "yes").map(r => r.name);
  const me = (snap.me && snap.me.name) || "";
  const mine = myVote(snap);

  // First sight of a race: take the tally down without saying anything.
  // Arriving mid-vote is not news about anybody, and the button already says
  // one is open.
  if (revealTip.race !== race.race_id) {
    revealTip.race = race.race_id; revealTip.yes = yes;
    revealTip.mine = mine; revealTip.shown = null;
    hideRevealTip();
    return;
  }

  // Nothing is said while the countdown or the results have the screen. The
  // tally to compare against is deliberately left where it was rather than
  // moved on, so somebody asking while you were still getting your bearings
  // is news the moment you land rather than something you never hear about.
  if (!S.running || S.done || $("btn-peek").hidden) { hideRevealTip(); return; }

  const before = revealTip.yes;
  const answered = revealTip.mine === null && mine !== null;
  revealTip.yes = yes;
  revealTip.mine = mine;

  // Answering is the end of it as far as you are concerned. So is the asker
  // changing their mind - and that one is forgotten rather than remembered,
  // so that asking again is news again.
  if (!yes.length && !race.peek) { revealTip.shown = null; hideRevealTip(); }
  else if (revealTip.up && answered) hideRevealTip();

  if (race.peek) {
    announceReveal("open:" + race.race_id, true,
                   "<b>Everyone</b> agreed — the target is open.",
                   "Read it whenever you like", "Open it");
  } else {
    const fresh = yes.filter(n => n !== me && before.indexOf(n) < 0);
    if (fresh.length) {
      const lead = before.length
        ? "<b>" + esc(fresh[0]) + "</b> agreed too."
        : "<b>" + esc(fresh[0]) + "</b> wants the target page opened.";
      const left = rows.filter(r => r.vote !== "yes").map(r => r.name);
      const sub = yes.length + " of " + rows.length + " agreed" +
                  (left.length === 1 ? " · waiting on " + esc(left[0] === me ? "you" : left[0]) : "");
      announceReveal("ask:" + race.race_id + ":" + yes.join("|"), false,
                     lead, sub, mine === null ? "Have your say" : "See who");
    }
  }
  placeRevealTip();                        // the chrome reflows; the Tip follows
}

$("reveal-tip").onclick = () => {
  const race = raceNow();
  hideRevealTip();
  if (race && race.peek) openPeek();
  else openVote();
};
window.addEventListener("resize", placeRevealTip);

$("btn-peek").onclick = () => {
''',
    "reveal tip",
)

once(
    '  if (!$("peek-scrim").hidden) { closePeek(); ev.preventDefault(); }\n'
    '  else if (!$("vote-scrim").hidden) { closeVote(); ev.preventDefault(); }\n',
    '  if (!$("peek-scrim").hidden) { closePeek(); ev.preventDefault(); }\n'
    '  else if (!$("vote-scrim").hidden) { closeVote(); ev.preventDefault(); }\n'
    '  else if (!$("reveal-tip").hidden) { hideRevealTip(); ev.preventDefault(); }\n',
    "escape",
)

io.open(UI, "w", encoding="utf-8", newline="").write(s)
print("patched", UI)
