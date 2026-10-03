# -*- coding: utf-8 -*-
"""The Give up button goes when your run is over, however it ended (issue #47).

Needs a game on 8477 - see workflows.md - and Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_giveup_button.py [port]

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is stubbed, so this runs with no internet.

The page plays each race itself: it is the page's own handling of a finish, a
give up and a time limit that is on trial, and posting to the API would skip it.

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
STARTER = "sidAsta"
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


# One link to the target, so a click on it is a finish.
ARTICLE_BODY = """
<div class="mw-parser-output">
<p>A <b>pulsar</b> is a highly magnetized rotating <a href="/wiki/Neutron_star"
title="Neutron star">neutron star</a> that emits beams of electromagnetic
radiation out of its magnetic poles.</p>
</div>
"""


def stub_wikipedia(context):
    """No internet needed: the article is not what is on trial."""
    def handler(route):
        url = route.request.url
        if "action=parse" in url:
            title = "Pulsar"
            for part in url.split("&"):
                if part.startswith("page="):
                    title = urllib.parse.unquote(part[5:]).replace("+", " ").replace("_", " ")
            body = {"parse": {"title": title, "text": {"*": ARTICLE_BODY}}}
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


def new_race(**rules):
    body = {"start": "Pulsar", "target": "Neutron star", "lang": "en", "kind": "classic", "checkpoints": []}
    body.update(rules)
    post("/start_race", STARTER, body)


def seen_new_race(pg, before):
    pg.wait_for_function("old => S.snap && S.snap.race && S.snap.race.race_id !== old",
                         arg=before, timeout=30000)


def racing(pg):
    """In the race, past the countdown, with the first article drawn."""
    pg.wait_for_function("() => S.running && !S.done && !!document.querySelector('#article a[data-page]')",
                         timeout=30000)


def over(pg):
    """The run is over and the page has moved on to the screen that says so."""
    pg.wait_for_function("() => S.done && stageMode === 'hub'", timeout=30000)


def giveup(pg):
    # Shown means drawn, not merely not marked hidden: a rule that overrides
    # the attribute would leave it on screen all the same.
    return pg.evaluate("""() => {
      const b = document.getElementById('btn-giveup'), r = b.getBoundingClientRect();
      return { marked_hidden: b.hidden, shown: getComputedStyle(b).display !== 'none' && r.width > 0 };
    }""")


def run_one(pg, label, rules, ends_it, first=False):
    """One race, from the countdown to the end of the run."""
    before = None if first else pg.evaluate("() => S.snap.race.race_id")
    new_race(**rules)
    if before:
        seen_new_race(pg, before)
    racing(pg)
    check(label + ": offered while the race is on", giveup(pg)["shown"], True)
    ends_it(pg)
    over(pg)
    check(label + ": gone once the run is over", giveup(pg), {"marked_hidden": True, "shown": False})


ka = Keepalive([STARTER, ME])
ka.start()
for sid, who in [(STARTER, "Asta"), (ME, "machmar")]:
    post("/name", sid, {"name": who})

with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    stub_wikipedia(ctx)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.add_init_script("localStorage.setItem('wr_sid','browserseat1');"
                       "localStorage.setItem('wr_name','machmar');"
                       "localStorage.setItem('wr_theme','dark');")
    pg.goto(BASE + "/")

    # Reaching the target is the way a run is meant to end, and the one this
    # was missing for.
    run_one(pg, "finishing", {},
            lambda pg: pg.click("#article a[data-page='Neutron star']"), first=True)

    # What the issue says already worked after a refresh: Results drawn from
    # the finished run, with the button put away by the other branch.
    pg.reload()
    pg.wait_for_function("() => S.done && stageMode === 'hub'", timeout=30000)
    check("finishing, then a reload: still gone", giveup(pg), {"marked_hidden": True, "shown": False})

    run_one(pg, "giving up", {}, lambda pg: pg.click("#btn-giveup"))

    # The clock only starts at GO, so three seconds is three seconds of racing.
    run_one(pg, "running out of time", {"time_limit": 3}, lambda pg: None)

    check("no page errors", errs, [])
    b.close()
ka.stop.set()
print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
