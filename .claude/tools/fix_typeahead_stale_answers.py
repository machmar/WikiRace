"""Issue #52: title suggestions can show the answer to a search you have moved on from.

Only the 180ms wait before a search went out was ever cancelled when the text
changed. A search that was already out was left to come back and draw whatever
it found, so an answer could land in a field you were still in and be wrong for
it: an older search answering after a newer one, under a box you had emptied,
after you picked a title, or after you pressed Escape. A search that failed did
the same with its `close()`, shutting a list that a newer search had drawn.

`latest` is now which search the box is waiting on. Typing moves it on, and so
do picking a title and Escape, which both mean "I am done with those". A search
remembers its own number and, when it comes back, finds out whether it is still
the one being waited for. If not, neither its answer nor its failure counts.

It sits beside the check from #50 and does not replace it: that one is about a
field you have left, this one about a search you have left behind, and a field
you come back to still wants an answer that is the latest. Run once from the
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
    """  let timer = null, items = [], active = -1;

  const close = () => { list.hidden = true; active = -1; };
  const choose = (t) => { input.value = t; close(); input.dispatchEvent(new Event("change")); };
""",
    """  let timer = null, items = [], active = -1;
  // Which search the box is waiting on. A search that is out cannot be called
  // back, so each one remembers its number and, when it returns, drops itself
  // if the box has moved on: typing, picking a title and Escape all do.
  let latest = 0;

  const close = () => { list.hidden = true; active = -1; };
  const choose = (t) => { latest++; input.value = t; close(); input.dispatchEvent(new Event("change")); };
""",
    "the search the box is waiting on",
)

once(
    """    clearTimeout(timer);
    const text = input.value;
    if (!text.trim()) { items = []; close(); return; }
    timer = setTimeout(async () => {
      try {
        const found = await suggestTitles(text, getLang());
""",
    """    clearTimeout(timer);
    const mine = ++latest, text = input.value;
    if (!text.trim()) { items = []; close(); return; }
    timer = setTimeout(async () => {
      try {
        const found = await suggestTitles(text, getLang());
        if (mine !== latest) return;
""",
    "a search remembers its number",
)

once(
    """      } catch (e) { close(); }
    }, 180);
""",
    """      } catch (e) { if (mine === latest) close(); }
    }, 180);
""",
    "a failed search that has been replaced does not close the list",
)

once(
    """    else if (e.key === "Escape") { close(); }
  });

  input.addEventListener("blur", () => setTimeout(close, 120));""",
    """    else if (e.key === "Escape") { latest++; close(); }
  });

  input.addEventListener("blur", () => setTimeout(close, 120));""",
    "Escape ends the search",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("patched", path)
