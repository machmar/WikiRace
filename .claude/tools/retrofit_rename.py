# -*- coding: utf-8 -*-
"""Free the design language's class names, and change nothing you can see.

Three names the standard needs were already taken by classes that meant
something else, and one of them was actively misleading:

- .panel was the sections of the side panel     -> .side-sec
- .card was the dialog - a Panel, not a Card    -> .panel  (and .card-head -> .panel-head)
- .row was a flex layout helper                 -> .hstack

The side panel's .panel has to move first, or the dialog would land on top of
it. Every value stays exactly as it was: this commit is renames only, so a
review can check it by looking for any visible difference and finding none.

Repeated markup is matched by count rather than exactly once - the principle
is the same, an anchor that matches more or fewer places than expected stops
the script instead of patching the wrong thing.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")

with io.open(PATH, encoding="utf-8", newline="") as f:
    s = f.read()


def exactly(old, new, n, label):
    global s
    assert s.count(old) == n, (label, "expected", n, "found", s.count(old))
    s = s.replace(old, new)


# ---- 1. the side panel's sections: .panel -> .side-sec ----
exactly("  .panel { border-bottom: 1px solid var(--line); padding: 14px 16px; }",
        "  .side-sec { border-bottom: 1px solid var(--line); padding: 14px 16px; }", 1, "side css")
exactly("  .panel h3 {", "  .side-sec h3 {", 1, "side h3 css")
exactly('    <div class="panel">', '    <div class="side-sec">', 4, "side markup")

# ---- 2. the dialog: .card -> .panel ----
exactly("  .card.wide {", "  .panel.wide {", 1, "dialog wide css")
exactly("  .card {\n    background: var(--bg-2);", "  .panel {\n    background: var(--bg-2);", 1, "dialog css")
exactly("  .card h2 {", "  .panel h2 {", 1, "dialog h2 css")
exactly("  .card p.lede {", "  .panel p.lede {", 1, "dialog lede css")
exactly("  .card-head {", "  .panel-head {", 1, "dialog head css")
exactly("  .card-head h2 {", "  .panel-head h2 {", 1, "dialog head h2 css")
exactly("    .card { padding: 20px 16px; }", "    .panel { padding: 20px 16px; }", 1, "dialog narrow css")
exactly('input.closest(".card")', 'input.closest(".panel")', 1, "dialog lookup")
exactly('<div class="card wide">', '<div class="panel wide">', 2, "dialog wide markup")
exactly("'<div class=\"card-head\">'", "'<div class=\"panel-head\">'", 1, "dialog head markup")
exactly("'<div class=\"card\">'", "'<div class=\"panel\">'", 1, "offline dialog markup")

# ---- 3. the layout helper: .row -> .hstack ----
exactly("  .row { display: flex; align-items: center; gap: 9px; }",
        "  .hstack { display: flex; align-items: center; gap: 9px; }", 1, "hstack css")
exactly('<div class="row">', '<div class="hstack">', 4, "hstack markup")
exactly('<div class="row" style="margin-bottom:16px">', '<div class="hstack" style="margin-bottom:16px">', 1,
        "hstack styled markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("renamed: .panel -> .side-sec, .card -> .panel, .row -> .hstack")
