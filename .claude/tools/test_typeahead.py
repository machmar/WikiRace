# -*- coding: utf-8 -*-
"""Title suggestions only ever show the answer to the search you are waiting on
(issues #50 and #52).

The search is asynchronous, so an answer can land at the wrong time:

  - after you have left the field (#50): the blur that closes the list has
    already happened, and a list opened then has nothing left to close it;
  - for a search you have since replaced (#52): an older answer landing after a
    newer one, under a box you have emptied, or after you picked a title.

The test holds Wikipedia's answers back, does what a player does in the
meantime, and only then lets them through, in the order that goes wrong.

Starts its own game on a free port and a fresh data folder, so it runs from any
checkout. Needs Playwright with a Chromium:

    pip install playwright && playwright install chromium
    python .claude/tools/test_typeahead.py

Set WIKIRACE_CHROME to a Chromium binary if Playwright's own is not where it
expects. Wikipedia is never reached.

Prints PASS/FAIL per check and exits non-zero on failure.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "..", "wikirace.py")
CHROME = os.environ.get("WIKIRACE_CHROME") or None
SCRATCH = tempfile.mkdtemp(prefix="wikirace-typeahead-")
READY = re.compile(r"UI ready at http://localhost:(\d+)/")
ME = "typeaheadseat1"

# The list closes itself 120ms after a blur. Waiting longer than that, with the
# answer still held back, is what makes the answer "late". Too short a wait
# would let the blur's own timer close a list that opened early, and an
# unfixed page would pass; too long costs only time.
BLUR_GRACE_MS = 400

# The three boxes that share the typeahead: where each one's list is.
FIELDS = [("start", "#c-start", "#c-start-list"),
          ("target", "#c-target", "#c-target-list"),
          ("checkpoint", "#c-check", "#c-check-list")]

fails = []


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: got %r want %r" % (label, got, want))
    print(("PASS " if ok else "FAIL ") + label + " -> " + repr(got))


def answer_for(search):
    """What the stub says Wikipedia suggests for a search. Both titles carry the
    search text, so a test can tell whose answer it is looking at."""
    return [search + " one", search + " two"]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


lines, said, port = [], threading.Event(), []
proc = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(free_port()), "--room", "typeahead",
                         "--no-discovery", "--data-dir", SCRATCH],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                        env=dict(os.environ, WIKIRACE_NO_BROWSER="1", PYTHONUNBUFFERED="1"))


def drain():
    for line in proc.stdout:
        lines.append(line)
        m = READY.search(line)
        if m and not port:
            port.append(int(m.group(1)))
            said.set()
    said.set()


threading.Thread(target=drain, daemon=True).start()
said.wait(12)
if not port:
    proc.kill()
    sys.exit("server did not start: " + "".join(lines)[-1500:])
BASE = "http://127.0.0.1:%d" % port[0]


def post(path, body):
    req = urllib.request.Request("%s/api%s?sid=%s" % (BASE, path, ME), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


try:
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/healthz", timeout=1)
            break
        except OSError:
            time.sleep(0.2)
    post("/name", {"name": "Tester"})

    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
        pg.add_init_script("localStorage.setItem('wr_sid','%s');"
                           "localStorage.setItem('wr_name','Tester');"
                           "localStorage.setItem('wr_theme','dark');" % ME)

        # Wikipedia's answer to a search is held until the test lets it go; the
        # check that a typed title is a real article is answered at once.
        pending = []                  # (the search text, its route), in the order they went out

        def wikipedia(route):
            url = route.request.url
            if "action=opensearch" in url:
                search = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["search"][0]
                pending.append((search, route))
                return
            title = "Physics"
            for part in url.split("&"):
                if part.startswith("titles="):
                    title = urllib.parse.unquote(part[7:]).replace("+", " ")
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"query": {"pages": {"1": {"pageid": 1, "title": title}}}}))

        ctx.route("**/w/api.php*", wikipedia)

        pg.goto(BASE + "/")
        pg.wait_for_function("() => S.snap", timeout=30000)
        # The page counts the searches it has finished with, so the test can
        # wait for the answer to have been handled rather than guess how long
        # that takes. A counted search has already drawn, or chosen not to.
        pg.evaluate("""() => {
          window.__searched = 0;
          const real = suggestTitles;
          window.suggestTitles = async (...a) => {
            try { return await real(...a); } finally { window.__searched++; }
          };
        }""")

        pg.click("#btn-new")
        pg.click("button.mode[data-mode=advanced]")
        pg.wait_for_selector("#config-overlay #c-check")

        def searched():
            return pg.evaluate("() => window.__searched")

        def wait_pending(n=1):
            for _ in range(200):
                if len(pending) >= n:
                    return
                pg.wait_for_timeout(25)
            raise SystemExit("the search for suggestions never went out")

        def land(search, broken=False):
            """Let one held search through and wait until the page has dealt with
            it. A broken answer is not JSON, which is how a search fails here
            without the browser logging an error of its own."""
            for i, (text, route) in enumerate(pending):
                if text == search:
                    del pending[i]
                    break
            else:
                raise SystemExit("no search for %r is waiting: %r" % (search, [t for t, _ in pending]))
            before = searched()
            route.fulfill(status=200, content_type="application/json",
                          body="<html>not json" if broken else json.dumps([search, answer_for(search), [], []]))
            pg.wait_for_function("n => window.__searched > n", arg=before, timeout=10000)

        def list_state(sel):
            return pg.evaluate("""sel => {
              const el = document.querySelector(sel);
              return { hidden: el.hidden, items: [...el.querySelectorAll('.ta-item')].map(e => e.textContent) };
            }""", sel)

        def opened(search):
            return {"hidden": False, "items": answer_for(search)}

        def type_and_hold(field, text="Physics"):
            """Type into a field and wait until its search is out, unanswered."""
            assert not pending, pending
            pg.focus(field)
            pg.fill(field, "")
            pg.fill(field, text)
            wait_pending(1)

        def two_searches_out(field):
            """Type "Ph" and then "Phy" with neither search answered."""
            assert not pending, pending
            pg.focus(field)
            pg.fill(field, "")
            pg.fill(field, "Ph")
            wait_pending(1)
            pg.fill(field, "Phy")
            wait_pending(2)

        def leave_field(how, field):
            if how == "tab away":
                pg.press(field, "Tab")
            elif how == "click elsewhere":
                pg.click("#config-overlay .lede")
            elif how == "press Add":
                pg.click("#c-check-add")

        # ---- the ordinary case still works, so the rest is not passing because nothing ever opens ----
        for name, field, lst in FIELDS:
            type_and_hold(field)
            land("Physics")
            check(name + ": suggestions open while you are still in the field",
                  list_state(lst), opened("Physics"))
            pg.press(field, "Escape")
            check(name + ": and Escape puts them away", list_state(lst)["hidden"], True)

        # ---- #50: the answer arrives after you have left ----
        for name, field, lst in FIELDS:
            hows = ["tab away", "click elsewhere"] + (["press Add"] if name == "checkpoint" else [])
            for how in hows:
                type_and_hold(field)
                leave_field(how, field)
                pg.wait_for_timeout(BLUR_GRACE_MS)
                land("Physics")
                check(name + ": an answer that lands after you " + how + " stays shut",
                      list_state(lst)["hidden"], True)

        # ---- but it is the focus when the answer lands that counts, not that you were ever away ----
        for name, field, lst in FIELDS:
            type_and_hold(field)
            pg.press(field, "Tab")
            pg.wait_for_timeout(BLUR_GRACE_MS)
            pg.focus(field)
            land("Physics")
            check(name + ": an answer that lands after you have come back still opens",
                  list_state(lst), opened("Physics"))
            pg.press(field, "Escape")

        # ---- #52: the field is still yours, but the answer is for a search you have moved on from ----
        for name, field, lst in FIELDS:
            two_searches_out(field)
            land("Phy")
            check(name + ": the newer search's answer opens", list_state(lst), opened("Phy"))
            land("Ph")
            check(name + ": an older answer landing after it does not replace it",
                  list_state(lst), opened("Phy"))
            pg.press(field, "Escape")

            assert not pending, pending
            pg.fill(field, "")
            pg.fill(field, "Phys")
            wait_pending(1)
            pg.fill(field, "")
            land("Phys")
            check(name + ": an answer landing under a box you have emptied stays shut",
                  [pg.input_value(field), list_state(lst)["hidden"]], ["", True])

            two_searches_out(field)
            land("Phy")
            pg.click(lst + " .ta-item >> nth=0")
            check(name + ": picking a title fills the box and puts the list away",
                  [pg.input_value(field), list_state(lst)["hidden"]], ["Phy one", True])
            land("Ph")
            check(name + ": an older answer landing after you picked does not bring it back",
                  [pg.input_value(field), list_state(lst)["hidden"]], ["Phy one", True])

            assert not pending, pending
            pg.fill(field, "")
            pg.fill(field, "Ph")
            wait_pending(1)
            land("Ph")
            pg.fill(field, "Phy")
            wait_pending(1)
            pg.press(field, "Escape")
            check(name + ": Escape puts the list away", list_state(lst)["hidden"], True)
            land("Phy")
            check(name + ": and the answer still out for what you were typing does not bring it back",
                  list_state(lst)["hidden"], True)

            two_searches_out(field)
            land("Phy")
            land("Ph", broken=True)
            check(name + ": an older search that fails does not close the newer one's list",
                  list_state(lst), opened("Phy"))
            pg.press(field, "Escape")

        check("no page errors", errs, [])
        b.close()
finally:
    proc.kill()
    proc.wait()
    shutil.rmtree(SCRATCH, ignore_errors=True)

print("\n" + ("ALL PASS" if not fails else "FAILURES:\n" + "\n".join(fails)))
sys.exit(1 if fails else 0)
