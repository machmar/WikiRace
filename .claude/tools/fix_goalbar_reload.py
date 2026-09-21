"""Issue #19: after a reload, the goal bar forgets checkpoints already made.

enterRace draws the goal bar inside showGoal, before the run's path has been
restored, and the branch for a run that is already over never draws it again,
so it keeps the empty path's picture. The mid-race branch is fine only because
navigate() redraws it. Run once from the repository root; running it again
stops on the anchor, which is the point.
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
    """    $("btn-giveup").hidden = true;
    renderCrumbs(); updateHud();
    openHub("results");""",
    """    $("btn-giveup").hidden = true;
    // showGoal drew the goal bar before the path was back, and nothing else
    // redraws it once the race is over for you.
    renderCrumbs(); updateHud(); renderGoalBar(race);
    openHub("results");""",
    "finished run redraws the goal bar",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("patched", path)
