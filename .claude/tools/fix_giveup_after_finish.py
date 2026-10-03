"""Issue #47: Give up stays in the top bar after you finish a race.

A run can end three ways in the page, and two of them, giveUp() and
outOfTime(), put the button away. win() never did, so it stayed on Results, My
run and Watching until a reload, which goes through the branch of enterRace()
for a run that is already over and hides it. It goes after the game has
accepted the win, next to where the other two do it, so a win the game turns
down leaves the button where it was. Run once from the repository root;
running it again stops on the anchor, which is the point.
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
    """    return;
  }
  openHub("results");
  celebrateFinish(secs);""",
    """    return;
  }
  // The run is over, so there is nothing left to give up; giveUp() and
  // outOfTime() put it away too. It waits for the game to accept the win,
  // because a refusal above puts you back in the race, and you still need it.
  $("btn-giveup").hidden = true;
  openHub("results");
  celebrateFinish(secs);""",
    "a win puts Give up away",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("patched", path)
