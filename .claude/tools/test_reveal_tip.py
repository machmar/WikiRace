# -*- coding: utf-8 -*-
"""The reveal popup, driven in a real browser (issue #18).

Needs a game on 8477 - see workflows.md - and Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_reveal_tip.py [port]

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is stubbed, so this runs with no internet: the point is the
popup, not the article behind it.

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


def post(path, sid, body=None):
    req = urllib.request.Request("%s/api%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def get(path, sid):
    return json.loads(urllib.request.urlopen("%s/api%s?sid=%s" % (BASE, path, sid), timeout=10).read())


class Keepalive(threading.Thread):
    """Players nobody asks after time out and leave, taking the tally with them."""
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


ARTICLE_BODY = """
<div class="mw-parser-output">
<p>A <b>pulsar</b> is a highly magnetized rotating <a href="/wiki/Neutron_star"
title="Neutron star">neutron star</a> that emits beams of electromagnetic
radiation out of its magnetic poles. This radiation can be observed only when a
beam of emission is pointing toward <a href="/wiki/Earth" title="Earth">Earth</a>,
much like the way a lighthouse can be seen only when the light is pointed in the
direction of an observer, and is responsible for the pulsed appearance of
emission.</p>
<p>Neutron stars are very dense and have short, regular rotational periods. This
produces a very precise interval between pulses that ranges from milliseconds to
seconds for an individual pulsar. Pulsars are one of the candidates for the
source of ultra-high-energy <a href="/wiki/Cosmic_ray" title="Cosmic ray">cosmic
rays</a>.</p>
<h2>History of observation</h2>
<p>The first pulsar was observed on 28 November 1967 by
<a href="/wiki/Jocelyn_Bell_Burnell" title="Jocelyn Bell Burnell">Jocelyn Bell
Burnell</a> and <a href="/wiki/Antony_Hewish" title="Antony Hewish">Antony
Hewish</a>. They observed pulses separated by 1.33 seconds that originated from
the same location in the sky and kept to
<a href="/wiki/Sidereal_time" title="Sidereal time">sidereal time</a>.</p>
<p>In looking for explanations for the pulses, the short period of the pulses
eliminated most astrophysical sources of radiation, such as
<a href="/wiki/Star" title="Star">stars</a>, and since the pulses followed
sidereal time, it could not be human-made radio frequency interference.</p>
<h2>Nomenclature</h2>
<p>Initially Bell Burnell and Hewish named the first pulsar LGM 1, for "little
green men". The name pulsar, a contraction of "pulsating star", first appeared
in print in 1968.</p>
<h2>Formation and lifecycle</h2>
<p>The events leading to the formation of a pulsar begin when the core of a
massive star is compressed during a
<a href="/wiki/Supernova" title="Supernova">supernova</a>, which collapses into
a neutron star. The neutron star retains most of its
<a href="/wiki/Angular_momentum" title="Angular momentum">angular momentum</a>,
and since it has only a tiny fraction of its progenitor's radius, it is formed
with very high rotation speed.</p>
</div>
"""




def stub_wikipedia(context):
    """No internet needed: the article behind the vote is not what is on trial."""
    def handler(route):
        url = route.request.url
        if "action=parse" in url:
            title = "Pulsar"
            for part in url.split("&"):
                if part.startswith("page="):
                    title = urllib.parse.unquote(part[5:]).replace("+", " ")
            body = {"parse": {"title": title, "text": {"*": ARTICLE_BODY}}}
        elif "generator=random" in url:
            body = {"query": {"pages": {}}}
        else:
            titles = "Pulsar"
            for part in url.split("&"):
                if part.startswith("titles="):
                    titles = urllib.parse.unquote(part[7:]).replace("+", " ")
            body = {"query": {"pages": {"1": {"pageid": 1, "title": titles, "length": 90000}}}}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
    context.route("**/w/api.php*", handler)


ka = Keepalive(SIDS + [ME])
ka.start()
fails = []

def check(label, got, want):
    ok = got == want
    if not ok: fails.append("%s: got %r want %r" % (label, got, want))
    print(("PASS " if ok else "FAIL ") + label + " -> " + repr(got))

def fresh_race():
    for s in SIDS + [ME]: post("/peek_vote", s, {"value": None})
    post("/start_race", "sidAsta", {"start": "Karel IV.", "target": "Pulsar", "lang": "cs",
                                    "kind": "classic", "checkpoints": []})
    for i, (name, path) in enumerate([("Asta", ["Karel IV.", "Praha", "Vltava"]),
                                      ("Ben", ["Karel IV.", "Univerzita Karlova", "Věda"]),
                                      ("Cleo", ["Karel IV.", "Rakousko-Uhersko", "Česko", "Evropa"])]):
        times = [round(j * (6.5 + i), 1) for j in range(len(path))]
        post("/progress", "sid" + name, {"article": path[-1], "clicks": len(path) - 1,
                                         "path": path, "times": times, "elapsed": times[-1] + 4})
    post("/progress", ME, {"article": "Svatá říše římská", "clicks": 1,
                                       "path": ["Karel IV.", "Svatá říše římská"],
                                       "times": [0, 9.2], "elapsed": 14.0})

def seen_new_race(pg, before):
    pg.wait_for_function("old => S.snap && S.snap.race && S.snap.race.race_id !== old",
                         arg=before, timeout=30000)


def racing(pg):
    pg.wait_for_function("() => S.running && !S.done && !document.getElementById('btn-peek').hidden",
                         timeout=30000)


def tip(pg):
    return pg.evaluate("""() => {
      const el = document.getElementById('reveal-tip');
      const b = document.getElementById('btn-peek').getBoundingClientRect();
      const r = el.getBoundingClientRect();
      return { hidden: el.hidden, open: el.classList.contains('open'),
               text: el.textContent.replace(/\\s+/g, ' ').trim(),
               btn: document.getElementById('btn-peek').className,
               cnt: (document.querySelector('#btn-peek .cnt') || {}).textContent || '',
               under: el.hidden ? null : Math.round(r.top - b.bottom),
               onbtn: el.hidden ? null : (r.left < b.left + b.width / 2 && r.right > b.left) };
    }""")

for sid in SIDS + [ME]:
    post("/name", sid, {"name": {"sidAsta": "Asta", "sidBen": "Ben", "sidCleo": "Cleo",
                                 ME: "machmar"}[sid]})
fresh_race()

with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    stub_wikipedia(ctx)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.add_init_script("localStorage.setItem('wr_sid','browserseat1');"
                       "localStorage.setItem('wr_name','machmar');"
                       "localStorage.setItem('wr_theme','dark');")
    pg.goto(BASE + "/"); pg.wait_for_timeout(3500)

    check("quiet at rest", tip(pg)["hidden"], True)

    # Ben asks.
    post("/peek_vote", "sidBen", {"value": "yes"}); pg.wait_for_timeout(1800)
    t = tip(pg)
    check("shows on an ask", t["hidden"], False)
    check("names the asker", t["text"], "Ben wants the target page opened. 1 of 4 agreed Have your say →")
    check("button untouched", t["btn"], "asked")
    check("count untouched", t["cnt"], "1/4")
    check("sits under the button", t["under"] <= 8 and t["under"] >= 0, True)
    check("caret lands on the button", t["onbtn"], True)

    # Rule 1: my own vote says nothing to me. Rule 4: answering takes it away.
    pg.evaluate("() => post('/peek_vote', { value: 'yes' })"); pg.wait_for_timeout(1800)
    t = tip(pg)
    check("answering dismisses it", t["hidden"], True)
    check("and says nothing about my own vote", t["text"].startswith("machmar"), False)

    # Rule 2: a later yes still speaks, though I have answered.
    post("/peek_vote", "sidCleo", {"value": "yes"}); pg.wait_for_timeout(1800)
    t = tip(pg)
    check("speaks again after I answered", t["hidden"], False)
    check("later wording + who is left", t["text"],
          "Cleo agreed too. 3 of 4 agreed · waiting on Asta See who →")

    # Rule 3: it must not re-fire on every snapshot.
    pg.evaluate("() => document.getElementById('reveal-tip').dataset.mark = '1'")
    pg.wait_for_timeout(2500)
    check("survives snapshots without rebuilding",
          pg.evaluate("() => document.getElementById('reveal-tip').dataset.mark"), "1")

    # Rule 4: the asker changing their mind takes it away.
    post("/peek_vote", "sidCleo", {"value": None})
    post("/peek_vote", "sidBen", {"value": None})
    pg.evaluate("() => post('/peek_vote', { value: null })")
    pg.wait_for_timeout(1800)
    check("withdrawal takes it away", tip(pg)["hidden"], True)

    # Rule 5: the grant is the green one, and it is the way in.
    for s in SIDS: post("/peek_vote", s, {"value": "yes"})
    pg.evaluate("() => post('/peek_vote', { value: 'yes' })")
    pg.wait_for_timeout(1800)
    t = tip(pg)
    check("grant shows", t["hidden"], False)
    check("grant is green", t["open"], True)
    check("grant wording", t["text"],
          "Everyone agreed — the target is open. Read it whenever you like Open it →")
    check("grant button untouched", t["btn"], "granted")
    pg.click("#reveal-tip"); pg.wait_for_timeout(2500)
    check("pressing the grant opens the target",
          pg.evaluate("() => !document.getElementById('peek-scrim').hidden"), True)
    check("and takes itself away", tip(pg)["hidden"], True)
    pg.click("#peek-close"); pg.wait_for_timeout(400)

    # Rule 7: a new race clears it.
    rid = pg.evaluate("() => S.snap.race.race_id")
    fresh_race(); seen_new_race(pg, rid); racing(pg); pg.wait_for_timeout(800)
    check("a new race clears it", tip(pg)["hidden"], True)

    # Pressing an ask opens the vote card, it does not vote.
    post("/peek_vote", "sidBen", {"value": "yes"})
    pg.wait_for_selector("#reveal-tip", state="visible", timeout=10000)
    pg.click("#reveal-tip"); pg.wait_for_timeout(600)
    check("pressing an ask opens the vote card",
          pg.evaluate("() => !document.getElementById('vote-scrim').hidden"), True)
    check("and casts no vote", pg.evaluate("() => myVote(S.snap)"), None)
    pg.click("#vote-close"); pg.wait_for_timeout(300)

    # Withdrawing and asking again is news again, not a one-off.
    post("/peek_vote", "sidBen", {"value": None}); pg.wait_for_timeout(1800)
    check("withdrawn a second time", tip(pg)["hidden"], True)
    post("/peek_vote", "sidBen", {"value": "yes"})
    pg.wait_for_selector("#reveal-tip", state="visible", timeout=10000)
    check("asking again is news again", tip(pg)["text"].startswith("Ben wants"), True)

    # A later yes speaks over the one before it, and resets the twenty seconds.
    post("/peek_vote", "sidCleo", {"value": "yes"})
    pg.wait_for_function("() => /Cleo agreed too/.test(document.getElementById('reveal-tip').textContent)",
                         timeout=10000)
    check("a later yes speaks over the first", tip(pg)["hidden"], False)

    # An ask made while you are still entering a race is news when you land,
    # rather than something you never hear about. The page has to have seen
    # the race first, or this is the reload case instead, which stays quiet.
    rid = pg.evaluate("() => S.snap.race.race_id")
    fresh_race(); seen_new_race(pg, rid)
    post("/peek_vote", "sidBen", {"value": "yes"})
    racing(pg)
    pg.wait_for_selector("#reveal-tip", state="visible", timeout=15000)
    check("an ask during your countdown still lands",
          tip(pg)["text"].startswith("Ben wants"), True)

    # And it goes on its own.
    pg.wait_for_timeout(21000)
    check("gone after twenty seconds", tip(pg)["hidden"], True)

    check("no page errors", errs, [])
    b.close()
ka.stop.set()
print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
