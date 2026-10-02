# -*- coding: utf-8 -*-
"""A race's name and its rules, driven in a real browser (issue #11).

Needs a game on 8477 - see workflows.md - and Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_race_name.py [port]

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is stubbed, so this runs with no internet.

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
SIDS = ["sidAsta", "sidBen"]
ME = "browserseat1"


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
SETTLE = 400  # past --m-base, so a fade has finished before it is read


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: got %r want %r" % (label, got, want))
    print(("PASS " if ok else "FAIL ") + label + " -> " + repr(got))


def name(pg, where):
    return pg.evaluate("""where => {
      const el = document.querySelector('.race-name[data-where="' + where + '"]');
      if (!el) return null;
      const tip = el.querySelector('.race-rules'), chip = el.querySelector('.race-kind');
      const r = tip.getBoundingClientRect();
      return { kind: chip.firstChild.textContent.trim(),
               route: el.querySelector('.race-route').textContent,
               shown: getComputedStyle(tip).visibility === 'visible',
               expanded: chip.getAttribute('aria-expanded'),
               rules: [...tip.querySelectorAll(':scope > div')].map(g =>
                 g.querySelector('.rr-h').textContent + ': ' +
                 [...g.querySelectorAll('li')].map(li => li.firstChild.textContent +
                   (li.querySelector('.rr-pct') ? ' [' + li.querySelector('.rr-pct').textContent + ']' : '')).join(' | ')),
               right: Math.round(r.right), width: innerWidth };
    }""", where)


ka = Keepalive(SIDS + [ME])
ka.start()
for sid, who in [("sidAsta", "Asta"), ("sidBen", "Ben"), (ME, "machmar")]:
    post("/name", sid, {"name": who})

# A first race that Asta wins, so the standings hand her a handicap in the next.
post("/start_race", "sidAsta", {"start": "Chess", "target": "Neutron star", "kind": "classic"})
post("/progress", "sidAsta", {"article": "Neutron star", "clicks": 1, "path": ["Chess", "Neutron star"],
                              "times": [0, 6], "elapsed": 7})
post("/finish", "sidAsta", {"path": ["Chess", "Neutron star"], "times": [0, 6], "elapsed": 7, "clicks": 1})
post("/give_up", "sidBen", {"path": [], "times": [], "elapsed": 9, "clicks": 0})
post("/give_up", ME, {"path": [], "times": [], "elapsed": 9, "clicks": 0})

# The one on trial: every rule the game has, and I am already out of it.
post("/start_race", "sidAsta", {
    "start": "Chess", "target": "Neutron star", "kind": "advanced", "lang": "en",
    "checkpoints": ["Energy", "Star"], "checkpoint_slots": [1, 0], "mode": "clicks",
    "time_limit": 600, "allow_back": False, "allow_find": False, "ban_hubs": True,
    "show_positions": False, "allow_peek": False, "toc": 0, "handicap": True})
post("/give_up", ME, {"path": [], "times": [], "elapsed": 5, "clicks": 0})

# What made it harder is marked with what it added to the points (issue #13).
ADVANCED = [
    "Who wins: Fewest clicks wins | 10 minutes to finish [+20%]",
    "Route: Language: English | Via Energy and Star [+40%] | Energy 1st, the rest anywhere [+20%]"
    " | Hub pages off-limits [+20%]",
    "Allowed: Positions hidden [+20%] | No going back [+20%] | No find on page [+20%]"
    " | Target hidden the whole race [+20%] | Tables of links hidden [+20%] | No contents list [+20%]",
]
POINTS = "Points: Worth ×3.2: each rule marked +20% made it harder"


def handicapped(rules):
    """The handicaps depend on the standings, which other tests on the same
    game add to, so only ask that Asta's is there and said as a sentence.
    They come just before the points, which always close the list."""
    last = rules[-2] if len(rules) > 1 else ""
    return last.startswith("Handicaps: ") and "Asta started " in last and " seconds behind" in last

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
    pg.wait_for_selector('.race-name[data-where="results"]', timeout=20000)

    n = name(pg, "results")
    check("results: the mode is the chip", n["kind"], "Advanced")
    check("results: then the route", n["route"], "Chess → Neutron star")
    check("results: rules put away at rest", (n["shown"], n["expanded"]), (False, "false"))
    check("results: every rule, grouped", n["rules"][:-2], ADVANCED)
    check("results: handicaps by name", handicapped(n["rules"]), True)
    check("results: and what it was worth", n["rules"][-1], POINTS)
    check("the racing strip draws from the same list",
          pg.evaluate("() => [...document.querySelectorAll('#rules .rule')].map(x => x.textContent)"),
          ["Advanced", "fewest clicks wins", "10 min limit", "English", "via Energy (1st)", "via Star",
           "no hub pages", "positions hidden", "no going back", "no find on page", "target stays hidden",
           "handicaps on", "points ×3.2"])

    pg.click('.race-name[data-where="results"] .race-kind')
    pg.wait_for_timeout(SETTLE)
    check("pressing the mode opens the rules", name(pg, "results")["shown"], True)

    # Results is redrawn on every snapshot; the rules must not snap shut under the reader.
    pg.evaluate("() => document.querySelector('.race-name').dataset.mark = '1'")
    post("/give_up", "sidBen", {"path": [], "times": [], "elapsed": 8, "clicks": 0})
    pg.wait_for_function("() => !document.querySelector('.race-name').dataset.mark", timeout=10000)
    n = name(pg, "results")
    check("still open after the results are redrawn", (n["shown"], n["expanded"]), (True, "true"))

    pg.click('.race-name[data-where="results"] .race-kind')
    pg.wait_for_timeout(SETTLE)
    check("pressing it again puts them away", name(pg, "results")["shown"], False)

    pg.click('.race-name[data-where="results"] .race-kind')
    pg.click(".hub-h2")
    pg.wait_for_timeout(SETTLE)
    check("pressing anywhere else puts them away", name(pg, "results")["shown"], False)

    pg.click('.race-name[data-where="results"] .race-kind')
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(SETTLE)
    check("Escape puts them away", name(pg, "results")["shown"], False)

    pg.hover('.race-name[data-where="results"] .race-kind')
    pg.wait_for_timeout(SETTLE)
    check("hover peeks", name(pg, "results")["shown"], True)
    pg.mouse.move(5, 890)
    pg.wait_for_timeout(SETTLE)
    check("and moving off puts them away", name(pg, "results")["shown"], False)

    pg.click('#hub-tabs button[data-tab="replay"]')
    pg.wait_for_selector('.race-name[data-where="replay"]', timeout=10000)
    n = name(pg, "replay")
    check("replay: same name", (n["kind"], n["route"]), ("Advanced", "Chess → Neutron star"))
    pg.click('.race-name[data-where="replay"] .race-kind')
    pg.wait_for_timeout(SETTLE)
    n = name(pg, "replay")
    check("replay: same rules", (n["shown"], n["rules"][:-2], handicapped(n["rules"]), n["rules"][-1]),
          (True, ADVANCED, True, POINTS))

    # A phone: the rules hang from the whole line, so they stay on the screen.
    pg.set_viewport_size({"width": 380, "height": 800})
    pg.wait_for_timeout(400)
    n = name(pg, "replay")
    check("phone: the rules stay on the screen", n["right"] <= n["width"], True)
    pg.set_viewport_size({"width": 1280, "height": 900})

    # A lost race has no shared start to name.
    rid = pg.evaluate("() => S.snap.race.race_id")
    post("/start_race", "sidAsta", {"target": "Pulsar", "lost": True, "kind": "lost",
                                    "starts": ["Chess", "Coffee", "Vikings", "Dolphin"]})
    post("/give_up", ME, {"path": [], "times": [], "elapsed": 5, "clicks": 0})
    pg.wait_for_function("old => S.snap && S.snap.race && S.snap.race.race_id !== old", arg=rid, timeout=20000)
    pg.reload()
    pg.wait_for_selector('.race-name[data-where="results"]', timeout=20000)
    n = name(pg, "results")
    check("lost: named by where everyone was going", (n["kind"], n["route"]), ("Lost", "→ Pulsar"))
    check("lost: says everyone started somewhere different",
          "Everyone started somewhere different" in n["rules"][1], True)

    check("no page errors", errs, [])
    b.close()
ka.stop.set()
print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
