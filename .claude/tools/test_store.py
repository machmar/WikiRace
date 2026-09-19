# -*- coding: utf-8 -*-
"""Exercise the SQLite history: migration, archive beyond the working set,
persistence across restarts, and the scoreboard wipe."""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

GAME = "/c/Users/marec/Desktop/WikiRace/wikirace.py"
SCRATCH = "/c/Users/marec/AppData/Local/Temp/claude/C--Users-marec-Desktop-AlchemistVST/cdb28a64-2388-4477-b63d-6ba8d0294f6f/scratchpad"
PORT = 8478
BASE = "http://127.0.0.1:%d" % PORT
fails = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else "   " + str(detail)))
    if not ok:
        fails.append(label)


def start(data):
    env = dict(os.environ, WIKIRACE_NO_BROWSER="1", PYTHONUNBUFFERED="1")
    p = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(PORT), "--room", "storetest",
                          "--no-discovery", "--data-dir", data],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, encoding="utf-8")
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/healthz", timeout=1)
            return p
        except OSError:
            if p.poll() is not None:
                break
            time.sleep(0.2)
    if p.poll() is None:
        p.kill()
    raise RuntimeError("server did not start: " + (p.communicate()[0] or "")[-1500:])


def stop(p):
    # Ask nicely, the way Docker does, so the shutdown save runs.
    p.terminate()
    try:
        out, _ = p.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
    return out


def get(path, sid="sidTester"):
    return json.loads(urllib.request.urlopen("%s%s%ssid=%s" % (BASE, path, "&" if "?" in path else "?", sid), timeout=10).read())


def post(path, sid, body):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def rows(data):
    db = sqlite3.connect(os.path.join(data, "wikirace.db"))
    n = db.execute("SELECT COUNT(*) FROM races").fetchone()[0]
    db.close()
    return n


# ---------------------------------------------------------------- 1. real legacy file
print("\n1. importing the history the old version wrote")
real = os.path.join(SCRATCH, "gdata")
legacy = json.load(open(os.path.join(real, "wikirace_history.json"), encoding="utf-8"))["races"]
p = start(real)
state = get("/api/state")
same_paths = all(get("/api/race?id=" + r["race_id"]).get("results") == r.get("results") for r in legacy)
out = stop(p)
check("old file renamed to .imported", os.path.exists(os.path.join(real, "wikirace_history.json.imported"))
      and not os.path.exists(os.path.join(real, "wikirace_history.json")))
check("every old race is in the database", rows(real) == len(legacy), (rows(real), len(legacy)))
check("the game loaded them", state["race_count"] == len(legacy), state["race_count"])
check("log says what happened", "imported %d races" % len(legacy) in out, out[-400:])
check("paths survived the move", same_paths)

# ---------------------------------------------------------------- 2. more than the working set
print("\n2. an archive bigger than the 60 races the game keeps in hand")
big = os.path.join(SCRATCH, "bigdata")
shutil.rmtree(big, ignore_errors=True)
os.makedirs(big)
many = [{"race_id": "old%03d" % i, "start": "A%d" % i, "target": "B", "created": 1000.0 + i,
         "results": {"x": {"name": "X", "finished": True, "clicks": 3, "elapsed": 10.0 + i, "path": ["A%d" % i, "M", "B"]}}}
        for i in range(75)]
json.dump({"races": many}, open(os.path.join(big, "wikirace_history.json"), "w", encoding="utf-8"))
p = start(big)
state = get("/api/state")
check("only the newest 60 are in play", state["race_count"] == 60, state["race_count"])
oldest = get("/api/race?id=old000")
check("the oldest race is still reachable for replays", oldest.get("start") == "A0", oldest)
hist = get("/api/history")
check("/api/history returns every race", len(hist["races"]) == 75, len(hist["races"]))

# a race finished now is written straight away, not at shutdown
for n in ("Ann", "Bo"):
    post("/api/name", "sid" + n, {"name": n})
    get("/api/state", "sid" + n)
r = post("/api/start_race", "sidAnn", {"start": "Cheese", "target": "Milk"})
rid = r["race"]["race_id"]
post("/api/progress", "sidAnn", {"article": "Milk", "clicks": 1, "path": ["Cheese", "Milk"], "times": [0, 2]})
post("/api/finish", "sidAnn", {"elapsed": 2.0, "clicks": 1, "path": ["Cheese", "Milk"], "times": [0, 2]})
time.sleep(0.3)
db = sqlite3.connect(os.path.join(big, "wikirace.db"))
doc = db.execute("SELECT data FROM races WHERE race_id = ?", (rid,)).fetchone()
db.close()
check("a finish is on disk immediately", doc is not None and any(r.get("name") == "Ann" for r in json.loads(doc[0])["results"].values()), doc)

# killed hard, no shutdown save: the finish must still be there
p.kill(); p.communicate()
p = start(big)
check("survives a hard kill", any(r.get("name") == "Ann" and r.get("finished") for r in get("/api/race?id=" + rid).get("results", {}).values()))
check("archive is 76 races after restart", rows(big) == 76, rows(big))

# ---------------------------------------------------------------- 3. the wipe
print("\n3. clearing the scoreboard")
# With a race in progress, the wipe keeps that one and nothing else.
r2 = post("/api/start_race", "sidAnn", {"start": "Bread", "target": "Milk"})
post("/api/reset_scores", "sidAnn", {})
kept = get("/api/state")["race_count"]
check("a race in progress survives the wipe, nothing else does", kept == 1 and rows(big) == 1, (kept, rows(big)))
stop(p)
p = start(big)
after = get("/api/state")["race_count"]
check("and the archive matches after a restart", after == 1 and rows(big) == 1, (after, rows(big)))
check("the kept race is the one in progress", get("/api/race?id=" + r2["race"]["race_id"]).get("start") == "Bread")
stop(p)

print("\n%s" % ("all checks passed" if not fails else "FAILURES: %s" % fails))
sys.exit(1 if fails else 0)
