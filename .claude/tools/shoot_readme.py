# -*- coding: utf-8 -*-
"""Take the pictures in README.md, from a real game, in a real browser.

    py -3.13 .claude/tools/shoot_readme.py [--only name,name] [--keep]

It starts its own copy of the game on a throwaway data folder (seeded with a few
evenings of past races so the lobby has something to say), fills the table with
five made-up players, and then plays one whole race as a sixth in a Chromium
window - the setup, the countdown, the clicks, the finish, and the Results and
Replay afterwards. Wikipedia is the real one, so this needs the internet and
Playwright with a Chromium (see workflows.md).

The pictures land in docs/img/. Run it again whenever the game looks different
enough that the README's pictures are lying; every picture is made fresh, and
the timings are written down here rather than guessed, so a rerun looks the same.

    --only a,b   keep only those pictures (the race is still played in full)
    --keep       leave the game running at the end, so you can look around in it

    WIKIRACE_RAW=<folder>   also keep every picture in full colour there, to try
                            a different squeeze without playing the race again
"""
import io
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "..", "wikirace.py")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "docs", "img"))
READY = re.compile(r"UI ready at http://localhost:(\d+)/")
CHROME = os.environ.get("WIKIRACE_CHROME") or None

ARGS = sys.argv[1:]
ONLY = set(ARGS[ARGS.index("--only") + 1].split(",")) if "--only" in ARGS else None
KEEP = "--keep" in ARGS

# The page is drawn at this size and photographed at twice it, so text stays
# sharp on a high-density screen and the README can show it smaller.
VIEW = {"width": 1280, "height": 800}
SCALE = 2

ME = "Kody"
OTHERS = ["Ada", "Boris", "Cleo", "Dev", "Eli"]
SID = lambda name: "sid" + "".join(c for c in name if c.isalnum())

START, TARGET, STOP = "Chess", "Pulsar", "Physics"

# Who goes where. Kody is played live in the browser; the others are posted to
# the game the way a browser would. Every route passes through the stop, because
# the race makes it a checkpoint. They share pages on purpose: that is what the
# maps are for.
ROUTES = {
    "Kody": [START, "Mathematics", "Science", STOP, "Astronomy", "Star", "Supernova", "Neutron star", TARGET],
    "Ada": [START, "Strategy", "Science", STOP, "Astronomy", TARGET],
    "Boris": [START, "Board game", "Game", "Play (activity)", "Child", "Human", "Brain", "Neuron",
              "Electricity", STOP, "Magnetism", "Light", "Astronomy", "Star", "Black hole", "Neutron star", TARGET],
    "Cleo": [START, "Computer chess", "Computer", "Artificial intelligence", "Mathematics", STOP,
             "Quantum mechanics", "Atom", "Nuclear physics", "Star", "Supernova", "Neutron star", TARGET],
    "Dev": [START, "Russia", "Soviet Union", "Cold War", "Space Race", "Sputnik 1", "Spaceflight", "Rocket"],
    "Eli": [START, "Chess piece", "Queen (chess)", "Monarchy", "Middle Ages", "Europe", "Renaissance",
            "Science", STOP, "Light", "Astronomy", "Telescope", "Star", "Neutron star", TARGET],
}
# Race seconds on each player's own clock when they come in. Kody's is whatever
# he really takes; the rest are made to be slower, with Ada third on time but
# fewest on clicks.
ELAPSED = {"Cleo": 97.0, "Ada": 118.0, "Boris": 133.0, "Dev": 152.0, "Eli": 141.0}
PAUSES = [5.0, 8.5, 3.0, 12.0, 6.0, 4.5, 11.0, 3.5, 9.0, 7.0, 2.5, 14.0]


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- the game
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_game(data):
    lines, said, port = [], threading.Event(), []
    env = dict(os.environ, WIKIRACE_NO_BROWSER="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    # --name keeps the machine's own user name out of the play-by-play.
    proc = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(free_port()), "--room", "readme",
                             "--no-discovery", "--no-browser", "--name", "Fran", "--data-dir", data],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, encoding="utf-8")

    def drain():
        for line in proc.stdout:
            lines.append(line)
            m = READY.search(line)
            if m and not port:
                port.append(int(m.group(1)))
                said.set()
        said.set()

    threading.Thread(target=drain, daemon=True).start()
    said.wait(15)
    if not port:
        proc.kill()
        raise RuntimeError("the game did not start: " + "".join(lines)[-1500:])
    base = "http://127.0.0.1:%d" % port[0]
    for _ in range(60):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1)
            return proc, base
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("the game did not answer: " + "".join(lines)[-1500:])


def api(base, path, sid, body=None):
    req = urllib.request.Request("%s/api%s?sid=%s" % (base, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def api_get(base, path, sid):
    return json.loads(urllib.request.urlopen("%s/api%s?sid=%s" % (base, path, sid), timeout=10).read())


class Keepalive(threading.Thread):
    """Players nobody asks after time out and leave, so somebody has to ask."""
    daemon = True

    def __init__(self, base, sids):
        super().__init__()
        self.base, self.sids, self.stop = base, sids, threading.Event()

    def run(self):
        while not self.stop.wait(3):
            for s in self.sids:
                try:
                    api_get(self.base, "/state", s)
                except Exception:
                    pass


# ---------------------------------------------------------------- the past
EASY = dict(show_positions=True, allow_back=True, allow_find=True, allow_peek=True, allow_tables=True,
            toc=3, ban_hubs=False, time_limit=0)
NORMAL = dict(EASY, allow_back=False, allow_find=False, allow_tables=False, toc=1)
HARD = dict(NORMAL, show_positions=False, allow_peek=False, toc=0, ban_hubs=True, time_limit=600)


def made(who, finished, elapsed, path, created):
    """One result, with the times worked out from the length of the route."""
    seed = sum(ord(c) for c in who)
    gaps = [PAUSES[(seed + i * 5) % len(PAUSES)] for i in range(1, len(path))]
    scale = elapsed / sum(gaps) if gaps and sum(gaps) else 1
    times, t = [0.0], 0.0
    for g in gaps:
        t += g * scale
        times.append(round(t, 1))
    return {"name": who, "peer_id": "p" + who, "finished": finished, "clicks": max(0, len(path) - 1),
            "elapsed": elapsed, "path": path, "times": times, "at": created + elapsed, "guest": False}


def old_race(rid, ago_hours, kind, start, target, rows, **rules):
    created = time.time() - ago_hours * 3600
    base = dict(EASY)
    base.update(rules)
    results = [made(who, ok, secs, route, created) for who, ok, secs, route in rows]
    return {"race_id": rid, "start": start, "target": target, "lost": kind == "lost", "starts": [],
            "kind": kind, "initiator": rows[0][0], "created": created, "lang": "en", "mode": "time",
            "checkpoints": [], "checkpoint_slots": [], "handicaps": {}, "peek": False,
            "results": {r["name"].lower(): r for r in results}, **base}


def seed_history(data):
    r = []
    # Three evenings, oldest first.
    r.append(old_race("a1", 74, "classic", "Banana", "Eiffel Tower", [
        ("Kody", True, 48.2, ["Banana", "Fruit", "France", "Paris", "Eiffel Tower"]),
        ("Boris", True, 66.0, ["Banana", "Fruit", "Europe", "France", "Paris", "Eiffel Tower"]),
        ("Ada", True, 71.5, ["Banana", "India", "Colonialism", "France", "Paris", "Eiffel Tower"]),
        ("Cleo", False, 90.0, ["Banana", "Plant"])]))
    r.append(old_race("a2", 73.5, "classic", "Lego", "Mount Everest", [
        ("Ada", True, 52.0, ["Lego", "Denmark", "Europe", "Himalayas", "Mount Everest"]),
        ("Kody", True, 61.4, ["Lego", "Toy", "Asia", "Himalayas", "Mount Everest"]),
        ("Dev", True, 88.0, ["Lego", "Plastic", "Oil", "Nepal", "Mount Everest"])]))
    r.append(old_race("a3", 73, "advanced", "Pizza", "Roman Empire", [
        ("Cleo", True, 80.0, ["Pizza", "Italy", "Rome", "Roman Empire"]),
        ("Kody", True, 92.3, ["Pizza", "Cheese", "Italy", "Rome", "Roman Empire"]),
        ("Eli", True, 104.0, ["Pizza", "Naples", "Italy", "Rome", "Roman Empire"])], **dict(NORMAL))
    )
    r.append(old_race("b1", 50, "lost", "", "Pulsar", [
        ("Boris", True, 118.0, ["Dolphin", "Mammal", "Earth", "Sun", "Star", "Pulsar"]),
        ("Eli", True, 133.0, ["Coffee", "Africa", "Astronomy", "Star", "Pulsar"]),
        ("Kody", True, 141.0, ["Vikings", "Europe", "Science", "Physics", "Neutron star", "Pulsar"]),
        ("Ada", False, 160.0, ["Physics", "Light"])], **dict(NORMAL)))
    r.append(old_race("b2", 49, "classic", "Moon", "Chocolate", [
        ("Dev", True, 39.0, ["Moon", "Earth", "Mars", "Cocoa bean", "Chocolate"][:3] + ["Chocolate"]),
        ("Kody", True, 58.0, ["Moon", "Earth", "Plant", "Cocoa bean", "Chocolate"]),
        ("Ada", True, 77.0, ["Moon", "Cheese", "Milk", "Chocolate"])]))
    r.append(old_race("b3", 48.5, "advanced", "Titanic", "Volcano", [
        ("Ada", True, 97.0, ["Titanic", "Ship", "Iceland", "Volcano"]),
        ("Boris", True, 118.0, ["Titanic", "Atlantic Ocean", "Iceland", "Volcano"]),
        ("Cleo", True, 121.0, ["Titanic", "Ocean", "Earth", "Plate tectonics", "Volcano"]),
        ("Kody", False, 125.0, ["Titanic", "Film"])], **dict(HARD)))
    r.append(old_race("c1", 26, "classic", "Jazz", "Mathematics", [
        ("Kody", True, 44.0, ["Jazz", "Music", "Mathematics"]),
        ("Eli", True, 49.0, ["Jazz", "Music", "Mathematics"]),
        ("Boris", True, 63.0, ["Jazz", "United States", "Science", "Mathematics"])], **dict(NORMAL)))
    r.append(old_race("c2", 25.5, "classic", "Octopus", "Isaac Newton", [
        ("Cleo", True, 70.0, ["Octopus", "Ocean", "Science", "Isaac Newton"]),
        ("Ada", True, 83.0, ["Octopus", "Mollusc", "Aristotle", "Physics", "Isaac Newton"]),
        ("Kody", True, 91.0, ["Octopus", "Intelligence", "Science", "Isaac Newton"]),
        ("Dev", False, 120.0, ["Octopus", "Japan"])]))
    os.makedirs(data, exist_ok=True)
    db = sqlite3.connect(os.path.join(data, "wikirace.db"))
    db.execute("CREATE TABLE races (race_id TEXT PRIMARY KEY, created REAL NOT NULL DEFAULT 0, data TEXT NOT NULL)")
    db.execute("CREATE INDEX races_by_created ON races(created)")
    db.execute("PRAGMA user_version = 1")
    db.executemany("INSERT INTO races VALUES (?, ?, ?)", [(x["race_id"], x["created"], json.dumps(x)) for x in r])
    db.commit()
    db.close()


# ---------------------------------------------------------------- the pictures
os.makedirs(OUT, exist_ok=True)
made_pictures = []


def wanted(name):
    return ONLY is None or name in ONLY


def keep(name, png, quantize=True, size=None, maxw=1920):
    """Save a picture, smaller than a raw screenshot, as a 256-colour palette.
    The squeeze matters: median cut (Pillow's default) posterizes the photographs
    in an article and drops the small saturated areas, such as the players' colour
    bars, to the nearest grey or teal; max coverage keeps those but speckles the
    photographs; an octree keeps both. Nothing is kept wider than the README can
    show on a high-density screen."""
    if not wanted(name):
        return
    im = (png if isinstance(png, Image.Image) else Image.open(io.BytesIO(png))).convert("RGB")
    if size:
        im = im.resize(size, Image.LANCZOS)
    if im.size[0] > maxw:
        im = im.resize((maxw, round(im.size[1] * maxw / im.size[0])), Image.LANCZOS)
    if os.environ.get("WIKIRACE_RAW"):
        # Full-colour originals, for trying a different squeeze without playing the race again.
        os.makedirs(os.environ["WIKIRACE_RAW"], exist_ok=True)
        im.save(os.path.join(os.environ["WIKIRACE_RAW"], name + ".png"))
    if quantize:
        im = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
    path = os.path.join(OUT, name + ".png")
    im.save(path, optimize=True)
    made_pictures.append((name, os.path.getsize(path), im.size))
    log("   saved %s.png  %dx%d  %d KB" % (name, im.size[0], im.size[1], os.path.getsize(path) // 1024))


def shot(pg, **kw):
    return pg.screenshot(**kw)


def region(pg, selector, pad=0, **kw):
    box = pg.locator(selector).first.bounding_box()
    clip = {"x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
            "width": box["width"] + 2 * pad, "height": box["height"] + 2 * pad}
    return pg.screenshot(clip=clip, **kw)


# ---------------------------------------------------------------- driving the page
def route_times(name):
    path = ROUTES[name]
    seed = sum(ord(c) for c in name)
    gaps = [PAUSES[(seed + i * 5) % len(PAUSES)] for i in range(1, len(path))]
    total = ELAPSED.get(name) or sum(gaps)
    scale = total / sum(gaps)
    out, t = [0.0], 0.0
    for g in gaps:
        t += g * scale
        out.append(round(t, 1))
    return out


def move(base, name, steps, scroll=None):
    """Put somebody `steps` clicks along their route, as their browser would."""
    path = ROUTES[name][:steps + 1]
    times = route_times(name)[:steps + 1]
    api(base, "/progress", SID(name), {"article": path[-1], "clicks": steps, "path": path,
                                        "times": times, "elapsed": times[-1] + 2.0})
    if scroll is not None:
        api(base, "/scroll", SID(name), {"value": scroll})


def settle(pg, ms=700):
    pg.wait_for_timeout(ms)


def theme(pg, which):
    pg.click('#theme button[data-theme="%s"]' % which)
    settle(pg, 900)


def go_to(pg, title):
    """What clicking a link in the article does, without needing that link to be
    on this week's version of the page."""
    pg.wait_for_function("() => !S.loading", timeout=30000)
    pg.evaluate("t => navigate(t, true)", title)
    pg.wait_for_function("t => !S.loading && S.current && S.current.toLowerCase() === t.toLowerCase()", arg=title,
                         timeout=30000)
    settle(pg, 500)


def main():
    scratch = tempfile.mkdtemp(prefix="wikirace-readme-")
    data = os.path.join(scratch, "data")
    seed_history(data)
    proc, base = start_game(data)
    log("game on " + base)
    ka = None
    try:
        for n in OTHERS:
            api(base, "/name", SID(n), {"name": n})
        ka = Keepalive(base, [SID(n) for n in OTHERS])
        ka.start()
        for n in ["Ada", "Boris", "Cleo"]:
            api(base, "/ready", SID(n), {"value": True})

        with sync_playwright() as p:
            browser = p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
            ctx = browser.new_context(viewport=VIEW, device_scale_factor=SCALE)
            pg = ctx.new_page()
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
            pg.add_init_script("localStorage.setItem('wr_theme','dark');")

            # ---- 1. first visit: the game asks for a name
            log("1. name picker")
            pg.goto(base + "/")
            pg.wait_for_function("() => document.getElementById('np-name') && document.getElementById('np-name').value.length > 2",
                                 timeout=20000)
            settle(pg, 900)
            keep("name-picker", region(pg, ".panel:has(#np-title)", pad=24))
            pg.fill("#np-name", ME)
            pg.click("#np-play")
            pg.wait_for_function("() => S.snap && S.snap.me && S.snap.me.name === 'Kody'", timeout=15000)
            settle(pg, 1200)

            # ---- 2. the lobby
            log("2. lobby")
            pg.wait_for_function("() => document.querySelectorAll('#lobby-players .row').length >= 6", timeout=15000)
            # The "You're Kody" toast is up for a few seconds; a picture of the lobby is without it.
            settle(pg, 5000)
            pg.set_viewport_size({"width": VIEW["width"], "height": 940})
            settle(pg, 800)
            keep("lobby", shot(pg))
            pg.set_viewport_size(VIEW)
            # Now everybody else gets ready, so that Start race is open when setup is.
            for n in ["Dev", "Eli"]:
                api(base, "/ready", SID(n), {"value": True})
            pg.evaluate("() => post('/ready', { value: true })")
            settle(pg, 800)

            # ---- 3. the three games, and the setup for one of them
            log("3. modes and setup")
            pg.click("#btn-new")
            pg.wait_for_selector("#mode-overlay .mode", timeout=5000)
            settle(pg, 900)
            keep("modes", region(pg, "#mode-overlay .panel", pad=30))
            pg.click('.mode[data-mode="advanced"]')
            pg.wait_for_selector("#config-overlay #c-start", timeout=5000)
            pg.fill("#c-start", START)
            pg.fill("#c-target", TARGET)
            pg.fill("#c-check", STOP)
            pg.click("#c-check-add")
            pg.wait_for_function("() => document.querySelectorAll('#c-chips .cp-row, #c-chips .chip').length >= 1", timeout=15000)
            # Before #54 a suggestion list opened when its search came back, even for a field you had
            # left, and then covered the controls below. Let the searches land and leave each field,
            # which is harmless now and still needed on a checkout from before that fix.
            settle(pg, 2500)
            for field in ["#c-start", "#c-target", "#c-check"]:
                pg.focus(field)
                pg.click("#config-overlay h2")
            settle(pg, 600)
            pg.click("#c-settings-btn")
            settle(pg, 500)
            pg.click('#c-preset button[data-preset="easy"]')
            pg.click("#c-hubs")
            settle(pg, 1500)
            # The dialog scrolls inside itself on a short window, so give it room.
            pg.set_viewport_size({"width": VIEW["width"], "height": 1150})
            settle(pg, 800)
            pg.evaluate("() => { document.querySelector('#config-overlay .panel').scrollTop = 0;"
                        " document.getElementById('config-overlay').scrollTop = 0; }")
            settle(pg, 400)
            keep("setup", region(pg, "#config-overlay .panel", pad=30))
            pg.set_viewport_size(VIEW)
            settle(pg, 500)

            # ---- 4. the race itself
            log("4. racing")
            pg.click("#c-go")
            try:
                pg.wait_for_function("() => S.snap && S.snap.race && S.snap.race.target === 'Pulsar'", timeout=45000)
            except Exception:
                log("   the race did not start: " + json.dumps(pg.evaluate("""() => ({
                    go: (document.getElementById('c-go') || {}).textContent,
                    toast: document.getElementById('toast').textContent,
                    race: S.snap && S.snap.race && [S.snap.race.start, S.snap.race.target],
                    peers: (S.snap.peers || []).map(p => [p.name, p.ready]) })""")))
                raise
            for n in OTHERS:
                move(base, n, 0)
            try:
                pg.wait_for_function("() => S.running && !S.done", timeout=60000)
                pg.wait_for_function("() => !S.loading && S.current", timeout=60000)
            except Exception:
                log("   the race did not get going: " + json.dumps(pg.evaluate("""() => ({
                    running: S.running, done: S.done, loading: S.loading, current: S.current, stage: stageMode,
                    countdown: (document.getElementById('countdown') || {}).textContent,
                    toast: document.getElementById('toast').textContent })""")))
                raise
            settle(pg, 800)

            # Kody and Ada both land on Astronomy, so the pill that says so shows.
            plan = [("Kody", 1), ("Ada", 1), ("Boris", 1), ("Cleo", 1), ("Eli", 1), ("Dev", 1),
                    ("Kody", 2), ("Ada", 2), ("Cleo", 2), ("Boris", 2), ("Eli", 2), ("Dev", 2),
                    ("Kody", 3), ("Ada", 3), ("Boris", 3), ("Cleo", 3), ("Dev", 3), ("Eli", 3),
                    ("Kody", 4), ("Ada", 4), ("Boris", 4), ("Cleo", 4), ("Eli", 4)]
            # Boris is in the long way round, so he is behind everyone.
            for who, step in plan:
                if who == "Kody":
                    go_to(pg, ROUTES["Kody"][step])
                    settle(pg, 700)
                else:
                    move(base, who, step)
                    settle(pg, 350)
            # Boris has barely moved; leave him trailing, and Dev stuck.
            move(base, "Ada", 4)
            settle(pg, 2500)       # the checkpoint splash is on screen for a couple of seconds
            pg.wait_for_function("() => !document.getElementById('company').hidden", timeout=15000)
            pg.evaluate("() => { document.getElementById('article-wrap').scrollTop = 0; }")
            settle(pg, 1200)
            keep("racing", shot(pg))

            # ---- 5. the same race, three ways to look at it
            log("5. themes")
            tiles = []
            for which in ["light", "wiki", "dark"]:
                theme(pg, which)
                tiles.append(Image.open(io.BytesIO(shot(pg))).convert("RGB"))
            theme(pg, "dark")
            if wanted("themes"):
                # One page, cut into thirds, each third in a different look: the same words at a
                # size you can read, instead of three small pages side by side.
                w, h = tiles[0].size
                top = int(h * 0.72)
                cuts = [0, w // 3, 2 * w // 3, w]
                sheet = Image.new("RGB", (w, top))
                for i, t in enumerate(tiles):
                    sheet.paste(t.crop((cuts[i], 0, cuts[i + 1], top)), (cuts[i], 0))
                line = ImageDraw.Draw(sheet)
                for x in cuts[1:3]:
                    line.line([(x, 0), (x, top)], fill=(130, 140, 150), width=4)
                keep("themes", sheet)

            # ---- 6. somebody wants to see the target
            log("6. reveal vote")
            api(base, "/peek_vote", SID("Dev"), {"value": "yes"})
            pg.wait_for_selector("#reveal-tip:not([hidden])", timeout=15000)
            settle(pg, 1200)
            keep("reveal-ask", pg.screenshot(clip={"x": VIEW["width"] - 640, "y": 0, "width": 640, "height": 190}))
            for n in ["Ada", "Boris", "Cleo", "Eli"]:
                api(base, "/peek_vote", SID(n), {"value": "yes"})
            pg.evaluate("() => post('/peek_vote', { value: 'yes' })")
            pg.wait_for_function("() => /target is open/.test((document.getElementById('reveal-tip')||{}).textContent||'')",
                                 timeout=15000)
            pg.click("#reveal-tip")
            pg.wait_for_selector("#peek-scrim:not([hidden])", timeout=8000)
            pg.wait_for_function("() => document.querySelector('#peek-body') && document.querySelector('#peek-body').textContent.length > 400",
                                 timeout=30000)
            settle(pg, 1800)
            keep("reveal-open", shot(pg))
            pg.click("#peek-close")
            settle(pg, 600)

            # ---- 7. the finish line
            log("7. finish")
            for step in range(5, len(ROUTES["Kody"]) - 1):
                go_to(pg, ROUTES["Kody"][step])
            pg.evaluate("t => navigate(t, true)", TARGET)
            pg.wait_for_function("() => S.done", timeout=30000)
            log("   Kody took %.1fs and %d clicks" % (pg.evaluate("() => S.finalElapsed"), pg.evaluate("() => S.clicks")))
            settle(pg, 1100)
            keep("finish", shot(pg))
            settle(pg, 4500)

            # Dev and Eli are still going while the others come in.
            for n, steps in [("Ada", len(ROUTES["Ada"]) - 1)]:
                move(base, n, steps)
                times = route_times(n)
                api(base, "/finish", SID(n), {"elapsed": ELAPSED[n], "clicks": steps, "path": ROUTES[n], "times": times})
            for n in ["Cleo", "Boris"]:
                steps = len(ROUTES[n]) - 1
                times = route_times(n)
                api(base, "/progress", SID(n), {"article": TARGET, "clicks": steps, "path": ROUTES[n],
                                                 "times": times, "elapsed": times[-1]})
                api(base, "/finish", SID(n), {"elapsed": ELAPSED[n], "clicks": steps, "path": ROUTES[n], "times": times})
            move(base, "Eli", 9, scroll=0.35)
            move(base, "Dev", 7, scroll=0.18)

            # ---- 8. watching the ones who are still going
            log("8. watching")
            pg.click('#hub-tabs button[data-tab="watch"]')
            pg.wait_for_function("() => document.querySelectorAll('#spec-body .spec-view').length >= 2", timeout=20000)
            settle(pg, 4000)
            keep("watching", shot(pg))

            # ---- 9. everyone's in: results and the replay
            log("9. results and replay")
            times = route_times("Eli")
            api(base, "/finish", SID("Eli"), {"elapsed": ELAPSED["Eli"], "clicks": len(ROUTES["Eli"]) - 1,
                                               "path": ROUTES["Eli"], "times": times})
            api(base, "/give_up", SID("Dev"), {"elapsed": ELAPSED["Dev"], "clicks": len(ROUTES["Dev"]) - 1,
                                                "path": ROUTES["Dev"], "times": route_times("Dev")})
            pg.click('#hub-tabs button[data-tab="results"]')
            settle(pg, 3500)
            pg.wait_for_function("() => document.querySelectorAll('#results-pane .row, #results-pane .res-row').length >= 4",
                                 timeout=20000)
            # Results is taller than the window; photograph all of it.
            pg.set_viewport_size({"width": VIEW["width"], "height": 1500})
            settle(pg, 3500)
            box = pg.locator("#results-pane").first.bounding_box()
            # The pane has padding below its last card; cut at the last thing in it.
            last = pg.evaluate("""() => Math.max(...[...document.querySelectorAll('#results-pane *')]
                .map(e => e.getBoundingClientRect().bottom))""")
            keep("results", pg.screenshot(clip={"x": box["x"], "y": box["y"], "width": box["width"],
                                                 "height": last - box["y"] + 28}))
            pg.set_viewport_size(VIEW)
            settle(pg, 600)

            # The replay plays itself the first time the tab is on screen; let it finish, and then
            # every view shows the whole race.
            log("   replay")
            pg.click('#hub-tabs button[data-tab="replay"]')
            pg.wait_for_function("() => replay.playing", timeout=15000)
            pg.wait_for_function("() => !replay.playing && replay.linger <= 0", timeout=60000)
            settle(pg, 800)
            tiles = {}
            for view in ["Timeline", "Aligned", "Metro", "Spring"]:
                pg.click('#rp-type button:has-text("%s")' % view)
                settle(pg, 1800)
                tiles[view] = Image.open(io.BytesIO(region(pg, "#rp-frame", pad=0))).convert("RGB")
            if wanted("replay"):
                tw, th = tiles["Timeline"].size
                gap = 40
                sheet = Image.new("RGB", (tw * 2 + gap, th * 2 + gap), (13, 17, 23))
                for i, view in enumerate(["Timeline", "Aligned", "Metro", "Spring"]):
                    sheet.paste(tiles[view].resize((tw, th)), ((i % 2) * (tw + gap), (i // 2) * (th + gap)))
                keep("replay", sheet, size=(sheet.size[0] // 2, sheet.size[1] // 2))

            log("   every race")
            pg.evaluate("() => openRaceList(new URLSearchParams())")
            pg.wait_for_selector("#racelist:not([hidden]) #rl-list > *", timeout=15000)
            settle(pg, 1500)
            pg.set_viewport_size({"width": VIEW["width"], "height": 1000})
            settle(pg, 800)
            keep("every-race", shot(pg))
            pg.set_viewport_size(VIEW)

            keep_errors = errors[:]
            browser.close()
        log("page errors: %s" % (keep_errors or "none"))
        log("\n".join("%-14s %4d KB  %dx%d" % (n, s // 1024, w, h) for n, s, (w, h) in made_pictures))
        if KEEP:
            log("still running on %s - Ctrl+C to stop" % base)
            while True:
                time.sleep(60)
    finally:
        if ka:
            ka.stop.set()
        if not KEEP:
            proc.kill()


if __name__ == "__main__":
    main()
