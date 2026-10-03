"""Issue #37: the rules under a race's name come back open by themselves.

Pressing the mode (or Escape) to put them away while the pointer is still on
the mode adds a `shut` class, so the stylesheet's hover peek sits out until the
pointer leaves. The class went on the element, and Results is rebuilt about
once a second, so the next rebuild made a new element without it and the peek
came straight back, under a pointer that had not moved. The same lost class is
what made test_race_name.py pass or fail on the same code, depending on where
in that second it read.

The memory now lives in `raceRulesShut`, beside `raceRulesOpen`, and is drawn
into the markup. Run once from the repository root; running it again stops on
the anchor, which is the point.
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
    """let raceRulesOpen = "";
""",
    """let raceRulesOpen = "";

/* Which race name has had its rules put away while the pointer is still on
   its mode, so the hover peek sits out until the pointer leaves. It is kept
   here for the same reason as the open state: a class on the element would
   go with the element, and Results is rebuilt about once a second, which
   would bring the peek back under a pointer that had not moved. */
let raceRulesShut = "";
""",
    "the memory beside the open state",
)

once(
    """  const open = raceRulesOpen === where, id = "race-rules-" + where;
  return '<div class="hub-sub race-name' + (open ? " open" : "") + '" data-where="' + where + '">' +""",
    """  const open = raceRulesOpen === where, shut = raceRulesShut === where, id = "race-rules-" + where;
  return '<div class="hub-sub race-name' + (open ? " open" : "") + (shut ? " shut" : "") +
    '" data-where="' + where + '">' +""",
    "drawn into the markup",
)

once(
    """    if (!on && el.classList.contains("open") && chip.matches(":hover")) el.classList.add("shut");
    el.classList.toggle("open", on);
""",
    """    if (!on && el.classList.contains("open") && chip.matches(":hover")) raceRulesShut = el.dataset.where;
    el.classList.toggle("open", on);
    el.classList.toggle("shut", raceRulesShut === el.dataset.where);
""",
    "put away under the pointer",
)

once(
    """  if (chip && !chip.contains(ev.relatedTarget)) chip.closest(".race-name").classList.remove("shut");
""",
    """  if (!chip || chip.contains(ev.relatedTarget)) return;
  const el = chip.closest(".race-name");
  if (raceRulesShut === el.dataset.where) raceRulesShut = "";
  el.classList.remove("shut");
""",
    "the pointer leaving",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("patched", path)
