"""Issue #55: take the Add box away at six checkpoints, and give the dice a new home.

Six is the most a race takes, and the box that adds a seventh did nothing but
answer "Six checkpoints is plenty" when used. It is now hidden once the list is
full and comes back when a stop is removed. The shuffle button lived in that
box, so it moves to the line under the list, beside the sentence describing the
order, where it stays whether or not the box is there. Run once from the
repository root; running it again stops on the anchor, which is the point.
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
    """  .cp-box > .cp-add:last-child { border-radius: 0 0 var(--cp-in) var(--cp-in); }
""",
    """  .cp-box > .cp-add:last-child { border-radius: 0 0 var(--cp-in) var(--cp-in); }
  /* With the add box gone, the list's own last row closes the box. */
  .cp-box.full > div:first-child > .cp-row:last-child { border-radius: 0 0 var(--cp-in) var(--cp-in); }
  .cp-box.full > div:first-child > .cp-row:only-child { border-radius: var(--cp-in); }
""",
    "rounding",
)
once(
    "  .cp-add { grid-template-columns: 1fr auto auto; gap:",
    "  .cp-add { grid-template-columns: 1fr auto; gap:",
    "add columns",
)
once(
    """  .cp-add .icon { padding: var(--s-2) var(--s-3); }
  .cp-phrase { margin: var(--s-3) 0 0; }
""",
    """  .cp-foot { display: flex; align-items: center; justify-content: space-between; gap: var(--s-3); margin-top: var(--s-3); }
  .cp-foot .icon { padding: var(--s-2) var(--s-3); font-size: var(--t-sm); }
  .cp-phrase { margin: 0; }
""",
    "foot css",
)
once(
    """    '<div class="cp-row cp-add">' +""",
    """    '<div class="cp-row cp-add" id="c-add-row">' +""",
    "add row id",
)
once(
    """    '<button id="c-shuffle" class="icon" title="A new order, and a new amount of order" hidden>🎲</button>' +
    "</div></div>" +
    '<p class="cp-phrase muted tiny" id="c-phrase"></p></div>' +
""",
    """    "</div></div>" +
    '<div class="cp-foot"><p class="cp-phrase muted tiny" id="c-phrase"></p>' +
    '<button id="c-shuffle" class="icon" title="A new order, and a new amount of order" hidden>🎲</button></div></div>' +
""",
    "markup",
)
once(
    """  const n = cfg.checkpoints.length;
  setFlag(ov.querySelector("#c-shuffle"), "hidden", n < 2);
""",
    """  const n = cfg.checkpoints.length;
  // A full list has no use for a box that adds another.
  setFlag(ov.querySelector("#c-add-row"), "hidden", n >= MAX_CHECKPOINTS);
  ov.querySelector(".cp-box").classList.toggle("full", n >= MAX_CHECKPOINTS);
  setFlag(ov.querySelector("#c-shuffle"), "hidden", n < 2);
""",
    "render",
)
once(
    """function renderCheckpointChips(ov) {""",
    """const MAX_CHECKPOINTS = 6;
function renderCheckpointChips(ov) {""",
    "const",
)
once(
    "if (cfg.checkpoints.length >= 6) { toast(",
    "if (cfg.checkpoints.length >= MAX_CHECKPOINTS) { toast(",
    "guard",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
