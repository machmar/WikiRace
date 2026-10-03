# -*- coding: utf-8 -*-
"""Results say why everyone got the points they got (issues #13 and #34).

Needs a game on 8477 - see workflows.md - and Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_points_ui.py [port]

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is stubbed, so this runs with no internet. The sums
themselves are test_points.py's; this only asks that the page tells them.

Prints PASS/FAIL per check and exits non-zero on failure.
"""
import json
import os
import sys
import threading
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

PORT = sys.argv[1] if len(sys.argv) > 1 else "8477"
BASE = "http://127.0.0.1:" + PORT
CHROME = os.environ.get("WIKIRACE_CHROME") or None
SIDS = ["sidAsta", "sidBen", "sidCleo"]
ME = "browserseat1"

EASY = {"show_positions": True, "allow_back": True, "allow_find": True, "allow_peek": True,
        "ban_hubs": False, "allow_tables": True, "toc": 3, "time_limit": 0}
NORMAL = dict(EASY, allow_back=False, allow_find=False, allow_tables=False, toc=1)


def post(path, sid, body=None):
    req = urllib.request.Request("%s/api%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def get(path, sid):
    return json.loads(urllib.request.urlopen("%s/api%s?sid=%s" % (BASE, path, sid), timeout=10).read())


class Keepalive(threading.Thread):
    """Players nobody asks after time out and leave."""
    daemon = True

    def __init__(self, sids):
        super().__init__()
        self.sids = sids
        self.stop = threading.Event()

    def run(self):
        while not self.stop.wait(3):
            for s in self.sids:
                try:
                    get("/state", s)
                except Exception:
                    pass


def stub_wikipedia(context):
    """No internet needed: the article is not what is on trial."""
    def handler(route):
        url = route.request.url
        if "action=parse" in url:
            title = "Chess"
            for part in url.split("&"):
                if part.startswith("page="):
                    title = urllib.parse.unquote(part[5:]).replace("+", " ")
            body = {"parse": {"title": title, "text": {"*": "<div class='mw-parser-output'><p>Text.</p></div>"}}}
        else:
            body = {"query": {"pages": {}}}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
    context.route("**/w/api.php*", handler)


fails = []


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: got %r want %r" % (label, got, want))
    print(("PASS " if ok else "FAIL ") + label + " -> " + repr(got))


def finish(sid, path, secs):
    post("/progress", sid, {"article": path[-1], "clicks": len(path) - 1, "path": path,
                            "times": list(range(len(path))), "elapsed": secs})
    post("/finish", sid, {"path": path, "times": list(range(len(path))), "elapsed": secs, "clicks": len(path) - 1})


# What the page says about a race, read the same way wherever it is drawn.
READ = """host => {
  const pane = document.querySelector(host);
  const tip = pane.querySelector('.race-rules');
  return {
    heading: pane.querySelector('.hub-sec h4').textContent,
    rows: [...pane.querySelectorAll('.result-row')].map(r => {
      const next = r.nextElementSibling;
      return [r.querySelector('.rn').textContent, (r.querySelector('.pts') || {}).textContent,
              next && next.classList.contains('score-line') ? next.textContent : null];
    }),
    marked: [...tip.querySelectorAll('li')].filter(li => li.querySelector('.rr-pct'))
              .map(li => li.firstChild.textContent + ' ' + li.querySelector('.rr-pct').textContent),
    points: [...tip.querySelectorAll(':scope > div')].map(g => g.querySelector('.rr-h').textContent + ': ' +
              [...g.querySelectorAll('li')].map(li => li.textContent).join(' | ')).pop(),
  };
}"""

NORMAL_SEEN = {
    "heading": "Finishing order — fastest time wins · points ×1.6 for 3 things that made it harder",
    "rows": [["Asta", "13", "8 for 1st (beat 3), ×1.6"],
             ["Cleo", "–", "A guest takes the place, not the points"],
             ["Ben", "10", "4 for 3rd (beat 1) + 2 for fewest clicks, ×1.6"],
             ["machmar", "0", None]],
    "marked": ["No going back +20%", "No find on page +20%", "Tables of links hidden +20%"],
    "points": "Points: Worth ×1.6: each rule marked +20% made it harder",
}

ka = Keepalive(SIDS + [ME])
ka.start()
for sid, who in [("sidAsta", "Asta"), ("sidBen", "Ben"), (ME, "machmar")]:
    post("/name", sid, {"name": who})
post("/name", "sidCleo", {"name": "Cleo", "guest": True})

# Three rules harder than the easiest game. Ben comes third on the clock but
# took the fewest clicks; the guest between them still takes second.
normal = post("/start_race", "sidAsta", dict(NORMAL, start="Chess", target="Neutron star", kind="classic"))["race"]
finish("sidAsta", ["Chess", "Energy", "Star", "Neutron star"], 7)
finish("sidCleo", ["Chess", "Star", "Neutron star"], 8)
finish("sidBen", ["Chess", "Neutron star"], 9)
post("/give_up", ME, {"path": [], "times": [], "elapsed": 9, "clicks": 0})

with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    stub_wikipedia(ctx)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("localStorage.setItem('wr_sid','browserseat1');"
                       "localStorage.setItem('wr_name','machmar');"
                       "localStorage.setItem('wr_theme','dark');")
    pg.goto(BASE + "/")
    pg.wait_for_selector("#results-pane .result-row", timeout=20000)

    seen = pg.evaluate(READ, "#results-pane")
    for k in NORMAL_SEEN:
        check("results: " + k, seen[k], NORMAL_SEEN[k])
    check("the racing strip says what the race pays",
          pg.evaluate("() => [...document.querySelectorAll('#rules .rule')].pop().textContent"), "points ×1.6")

    # The easiest game pays the usual points and says so, with no sum to show.
    post("/start_race", "sidAsta", dict(EASY, start="Chess", target="Neutron star", kind="classic"))
    finish("sidAsta", ["Chess", "Neutron star"], 5)
    post("/give_up", "sidBen", {"path": [], "times": [], "elapsed": 6, "clicks": 0})
    post("/give_up", ME, {"path": [], "times": [], "elapsed": 6, "clicks": 0})
    pg.wait_for_function("old => S.snap && S.snap.race && S.snap.race.race_id !== old",
                         arg=normal["race_id"], timeout=20000)
    pg.reload()
    pg.wait_for_selector("#results-pane .result-row", timeout=20000)
    seen = pg.evaluate(READ, "#results-pane")
    check("easy: no multiplier in the heading", seen["heading"], "Finishing order — fastest time wins")
    check("easy: the only finisher beat the two who gave up, and has no bonus to win",
          seen["rows"][0], ["Asta", "6", "6 for 1st (beat 2)"])
    check("easy: nothing marked", seen["marked"], [])
    check("easy: the usual points", seen["points"], "Points: The usual points: nothing made it harder")

    # A past race's own page tells the same story as Results did.
    pg.goto(BASE + "/#race=" + normal["race_id"])
    pg.wait_for_selector("#racepage-results .result-row", timeout=20000)
    seen = pg.evaluate(READ, "#racepage-results")
    check("race page: same rows", seen["rows"], NORMAL_SEEN["rows"])
    check("race page: same reasons", seen["marked"], NORMAL_SEEN["marked"])

    # Race setup: a setting says what it adds while it is making the race
    # harder, and the settings header carries the total, folded or not.
    SETUP = """() => ({
      total: document.querySelector('#c-points').textContent,
      marked: [...document.querySelectorAll('.c-pct')].filter(s => s.textContent)
                .map(s => s.dataset.rule + ' ' + s.textContent),
    })"""
    WAIT = "want => document.querySelector('#c-points') && document.querySelector('#c-points').textContent === want"
    pg.goto(BASE + "/")
    pg.wait_for_selector("#results-pane .result-row", timeout=20000)
    pg.evaluate("() => openConfigurator('advanced')")
    pg.click("#c-settings-btn")
    pg.click('[data-preset="easy"]')
    pg.wait_for_function("() => document.querySelector('#c-points').textContent === ''", timeout=5000)
    check("easy: nothing marked, no total", pg.evaluate(SETUP), {"total": "", "marked": []})
    pg.evaluate("() => { cfg.checkpoints = ['Energy', 'Star']; cfg.checkpoint_slots = [1, 2];"
                " renderCheckpointChips(document); }")
    pg.click('[data-preset="normal"]')
    pg.wait_for_function(WAIT, arg="points +120%", timeout=5000)
    check("normal with two stops in order",
          pg.evaluate(SETUP)["marked"],
          ["checkpoints +60%", "no_back +20%", "no_find +20%", "no_tables +20%"])
    pg.click("#c-back")
    pg.wait_for_function(WAIT, arg="points +100%", timeout=5000)
    check("allowing the back button takes its mark away", "no_back +20%" in pg.evaluate(SETUP)["marked"], False)
    pg.click('[data-preset="hard"]')
    pg.wait_for_function(WAIT, arg="points +220%", timeout=5000)
    check("hard marks every setting but the handicap",
          pg.evaluate(SETUP)["marked"],
          ["checkpoints +60%", "hidden +20%", "no_back +20%", "no_find +20%", "no_reveal +20%",
           "no_hubs +20%", "no_tables +20%", "no_contents +20%", "time_limit +20%"])
    pg.click("#c-settings-btn")
    check("folded away, the total still shows",
          pg.evaluate("() => [document.querySelector('#c-settings').hidden,"
                      " document.querySelector('#c-points').offsetWidth > 0]"), [True, True])

    check("no page errors", errs, [])
    b.close()
ka.stop.set()
print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
