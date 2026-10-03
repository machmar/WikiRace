"""Issue #38: the Lost race's rule pill wraps to two lines at the narrowest panel.

Two changes, because the wording was only the first thing wrong with it.

The pill read "lost: everyone starts somewhere different". The strip's first
pill already says "Lost", so the prefix repeated what sat beside it; and cutting
only the prefix still leaves 190px of words for a strip that is 179px wide at
the 220px minimum, so it would have wrapped anyway. It is now "different
starts". The Tip's line for the same rule, and the countdown's, are written for
a different place and stay as they were.

Other pills wrap at that width too (a long contents label, a checkpoint with a
long name), so a Pill that will not fit on a line now wraps tidily instead. A
fully round pill with two lines in it is a stretched capsule whose ends cut into
the words, and its lines were left ragged ("everyone starts somewhere" over
"different"). The words now break evenly, and the corner is the one a one-line
pill has - half a line plus the padding and the border - so the pill turns into
a rounded box with the same curve as the capsules beside it. A word with no
break in it is broken, not left to push the strip sideways.

Run once from the repository root; running it again stops on the anchor, which
is the point.
"""
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "ui.html"
with open(path, encoding="utf-8", newline="") as f:
    s = f.read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


once(
    """  /* Pill: a standalone token you read. */
  .pill {
    display: inline-flex; align-items: center; gap: var(--s-2);
    background: var(--bg-3); border: 1px solid var(--line); color: var(--fg);
    border-radius: var(--r-pill); padding: var(--s-1) var(--s-4); font-size: var(--t-sm);
  }
""",
    """  /* Pill: a standalone token you read. When its words will not fit on a line
     it breaks them evenly and keeps the corner a one-line pill has, so it
     becomes a rounded box rather than a stretched capsule whose ends cut into
     the text; a word with no break in it is broken rather than left to push
     the strip sideways. */
  .pill {
    display: inline-flex; align-items: center; gap: var(--s-2);
    background: var(--bg-3); border: 1px solid var(--line); color: var(--fg);
    border-radius: var(--r-pill); padding: var(--s-1) var(--s-4); font-size: var(--t-sm);
    overflow-wrap: anywhere; text-wrap: balance;
  }
  /* Half a line, the padding and the border: exactly a one-line pill's capsule,
     and a rounded box with the same corner when there are two. The 1px is the
     border's width. Where there is no lh unit the capsule above stands. */
  @supports (height: 1lh) {
    .pill { border-radius: calc(.5lh + var(--s-1) + 1px); }
  }
""",
    "the pill's corner and line breaks",
)

once(
    """"lost: everyone starts somewhere different"), "lost");""",
    """"different starts"), "lost");""",
    "the Lost pill's wording",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("ui.html patched")
