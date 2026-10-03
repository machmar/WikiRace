# -*- coding: utf-8 -*-
"""The side panel can be resized, and its rules strip stops growing (issue #35).

Needs a game on 8477 - see workflows.md - and Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_side_panel.py [port]

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is never reached: the panel is on screen in the lobby as
much as in a race, and it only needs to see a race's rules.

Prints PASS/FAIL per check and exits non-zero on failure.
"""
import json
import os
import sys
import threading
import urllib.request

from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8477"
BASE = "http://127.0.0.1:" + PORT
CHROME = os.environ.get("WIKIRACE_CHROME") or None
ASTA = "sidAsta"
ME = "browserseat1"

DEFAULT_W, MIN_W, MAX_W, KEY_STEP = 270, 220, 480, 15


def post(path, sid, body=None):
    req = urllib.request.Request("%s/api%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


class Keepalive(threading.Thread):
    """Players nobody asks after time out and leave, taking the race with them."""
    daemon = True

    def __init__(self, sids):
        super().__init__()
        self.sids = sids
        self.stop = threading.Event()

    def run(self):
        while not self.stop.wait(3):
            for s in self.sids:
                try:
                    urllib.request.urlopen("%s/api/state?sid=%s" % (BASE, s), timeout=10).read()
                except Exception:
                    pass


fails = []


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: got %r want %r" % (label, got, want))
    print(("PASS " if ok else "FAIL ") + label + " -> " + repr(got))


def start_race(pg, **rules):
    before = pg.evaluate("() => (S.snap && S.snap.race && S.snap.race.race_id) || null")
    post("/start_race", ASTA, dict({"start": "Karel IV.", "target": "Pulsar", "lang": "cs"}, **rules))
    pg.wait_for_function("old => S.snap && S.snap.race && S.snap.race.race_id !== old",
                         arg=before, timeout=30000)
    pg.wait_for_function("() => document.querySelectorAll('#rules .pill').length > 0", timeout=10000)


def side_w(pg):
    return round(pg.evaluate("() => document.getElementById('side').getBoundingClientRect().width"))


def grip(pg):
    return pg.evaluate("""() => {
      const g = document.getElementById('side-grip');
      if (!g) return null;
      const r = g.getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height, role: g.getAttribute('role'),
               now: g.getAttribute('aria-valuenow'), display: getComputedStyle(g).display };
    }""")


def drag_by(pg, dx):
    """Pull the edge dx pixels to the right (negative widens the panel)."""
    g = grip(pg)
    x, y = g["x"] + g["w"] / 2, 400
    wide = pg.viewport_size["width"]
    pg.mouse.move(x, y)
    pg.mouse.down()
    # Stay inside the window: a long pull is "as far as the screen goes".
    pg.mouse.move(max(2, min(x + dx, wide - 2)), y, steps=8)
    pg.mouse.up()


def saved(pg):
    return pg.evaluate("() => localStorage.getItem('wr_side')")


def strip(pg):
    return pg.evaluate("""() => {
      const el = document.getElementById('rules');
      return { pills: el.querySelectorAll('.pill').length, box: el.clientHeight,
               content: el.scrollHeight, overflow: getComputedStyle(el).overflowY };
    }""")


ka = Keepalive([ASTA, ME])
ka.start()
post("/name", ASTA, {"name": "Asta"})
post("/name", ME, {"name": "machmar"})

with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    # Not the width: that has to survive the reloads below.
    pg.add_init_script("localStorage.setItem('wr_sid','%s');"
                       "localStorage.setItem('wr_name','machmar');"
                       "localStorage.setItem('wr_theme','dark');" % ME)
    pg.goto(BASE + "/")
    pg.wait_for_function("() => S.snap", timeout=30000)

    # ---- the width ----
    check("narrower than it was by default", side_w(pg), DEFAULT_W)
    g = grip(pg)
    check("there is an edge to pull", g is not None, True)
    check("it is a separator", g and g["role"], "separator")
    check("it says how wide the panel is", g and g["now"], str(DEFAULT_W))
    check("and nothing is saved until it is moved", saved(pg), None)

    drag_by(pg, -100)
    check("dragging left widens the panel", side_w(pg), DEFAULT_W + 100)
    check("the width is remembered", saved(pg), str(DEFAULT_W + 100))
    check("the separator reports it", grip(pg)["now"], str(DEFAULT_W + 100))

    drag_by(pg, 40)
    check("dragging right narrows it", side_w(pg), DEFAULT_W + 60)

    drag_by(pg, -2000)
    check("no wider than the maximum", side_w(pg), MAX_W)
    drag_by(pg, 2000)
    check("no narrower than the minimum", side_w(pg), MIN_W)

    drag_by(pg, -100)
    want = MIN_W + 100
    pg.reload()
    pg.wait_for_function("() => S.snap", timeout=30000)
    check("it survives a reload", side_w(pg), want)

    pg.focus("#side-grip")
    pg.keyboard.press("ArrowLeft")
    check("the left arrow widens it", side_w(pg), want + KEY_STEP)
    pg.keyboard.press("ArrowRight")
    pg.keyboard.press("ArrowRight")
    check("the right arrow narrows it", side_w(pg), want - KEY_STEP)
    check("and the key is remembered too", saved(pg), str(want - KEY_STEP))

    pg.dblclick("#side-grip")
    check("double-click puts it back", side_w(pg), DEFAULT_W)
    check("and forgets the saved width", saved(pg), None)

    # ---- a window too small for the saved width ----
    drag_by(pg, -2000)
    check("widest, in a wide window", side_w(pg), MAX_W)
    pg.set_viewport_size({"width": 800, "height": 900})
    check("never more than half a smaller window", side_w(pg), 400)
    check("without losing what was saved", saved(pg), str(MAX_W))

    # ---- a phone has a drawer, not an edge ----
    pg.set_viewport_size({"width": 700, "height": 900})
    check("no edge to pull on a phone", grip(pg)["display"], "none")
    check("the drawer keeps its own width", side_w(pg), 330)
    pg.set_viewport_size({"width": 1440, "height": 900})
    pg.dblclick("#side-grip")

    # ---- the rules strip ----
    start_race(pg, kind="advanced", checkpoints=["Praha", "Vltava", "Evropa"],
               checkpoint_slots=[1, 2, 3], time_limit=300, ban_hubs=True, allow_back=False,
               allow_find=False, show_positions=False, allow_peek=False, allow_tables=False, toc=0)
    s = strip(pg)
    check("a crowded race has a crowd of rules", s["pills"] >= 12, True)
    check("the strip scrolls rather than growing", s["overflow"], "auto")
    check("and it has stopped at a few rows", s["box"] <= 120, True)
    check("with more behind it", s["content"] > s["box"], True)

    start_race(pg, kind="classic", checkpoints=[], allow_tables=True, toc=1)
    s = strip(pg)
    check("an easy race has fewer", s["pills"] < 10, True)
    check("and shows them all without scrolling", s["content"] <= s["box"] + 1, True)

    check("no page errors", errs, [])
    b.close()

ka.stop.set()
print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
