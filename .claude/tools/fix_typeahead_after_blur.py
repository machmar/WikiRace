"""Issue #50: title suggestions can open after you have left the field, and stay open.

The list closes on `blur`, but the search behind it is asynchronous. Type a
title and press Add, or tab away, before Wikipedia has answered, and the answer
lands on a field that has already lost focus: `draw()` opens the list, and
nothing closes it, because the blur it would close on has come and gone. It sat
over Game settings until the field was focused and left again.

An answer is now drawn only if the field still has focus when it arrives. A
field you have come back to still gets its suggestions, since that is a
field you are typing in. The same function serves the start, target and
checkpoint boxes. Run once from the repository root; running it again stops on
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
    """        items = await suggestTitles(text, getLang());
        active = -1;
        draw();
""",
    """        const found = await suggestTitles(text, getLang());
        // The answer can come back after the field has been left, and the
        // blur that closes the list has already happened by then, so a list
        // opened now would have nothing left to close it.
        if (document.activeElement !== input) return;
        items = found;
        active = -1;
        draw();
""",
    "draw only into a field that still has focus",
)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("patched", path)
