# -*- coding: utf-8 -*-
"""The list of past races behind the lobby and the Every race screen (issue #12):
everything in the archive, newest first, the right winner for each kind of race,
and the filters."""
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
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "..", "wikirace.py")
SCRATCH = tempfile.mkdtemp(prefix="wikirace-past-")
READY = re.compile(r"UI ready at http://localhost:(\d+)/")
fails = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else "   " + str(detail)))
    if not ok:
        fails.append(label)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start(data):
    """Start a copy of the game and return it with the port it says it took,
    which is not always the one it was asked for."""
    lines, said = [], threading.Event()
    env = dict(os.environ, WIKIRACE_NO_BROWSER="1", PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(free_port()), "--room", "pasttest",
                             "--no-discovery", "--data-dir", data],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, encoding="utf-8")
    port = []

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
        raise RuntimeError("server did not start: " + "".join(lines)[-1500:])
    base = "http://127.0.0.1:%d" % port[0]
    for _ in range(60):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1)
            return proc, base
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("server did not answer: " + "".join(lines)[-1500:])


def result(name, finished, clicks, elapsed, path):
    return {"name": name, "peer_id": "p" + name, "finished": finished, "clicks": clicks,
            "elapsed": elapsed, "path": path, "times": [i * 5.0 for i in range(len(path))],
            "at": 0, "guest": False}


def race(rid, created, start_page, target, results, **rules):
    r = {"race_id": rid, "start": start_page, "target": target, "lost": False, "starts": [],
         "kind": "classic", "initiator": "Kody", "created": created, "lang": "en", "mode": "time",
         "checkpoints": [], "checkpoint_slots": [], "results": {x["name"].lower(): x for x in results}}
    r.update(rules)
    return r


# ---------------------------------------------------------------- an archive bigger than the working set
now = time.time()
races = []
# Seventy plain races, an hour apart, oldest first. The game keeps only the
# newest sixty in hand, so the oldest ten are reachable only through the archive.
for i in range(70):
    races.append(race("plain%02d" % i, now - (80 - i) * 3600, "Chess", "Moon",
                      [result("Kody", True, 5, 40.0 + i * 0.1, ["Chess", "Earth", "Moon"]),
                       result("Ada", True, 4, 90.0, ["Chess", "Moon"])]))
# The cases the list has to get right, all newer than the plain ones.
races += [
    # A race for fewest clicks: Ada wins with fewer clicks although Kody was quicker.
    race("clicks", now - 9 * 3600, "Banana", "Pizza",
         [result("Kody", True, 9, 40.0, ["Banana", "Pizza"]), result("Ada", True, 3, 95.0, ["Banana", "Pizza"])],
         mode="clicks", kind="advanced", checkpoints=["Italy"], checkpoint_slots=[0]),
    # Nobody finished: listed, with no winner, and both counted as giving up.
    race("nobody", now - 8 * 3600, "Paper", "Rocket",
         [result("Kody", False, 2, 50.0, ["Paper", "Wood"]), result("BuraG", False, 0, 30.0, [])]),
    # From before modes existed: no kind, and lost, so it has to count as lost.
    race("oldlost", now - 7 * 3600, "", "Tea",
         [result("Nessa", True, 6, 70.0, ["Cat", "Tea"])], kind=None, lost=True, starts=["Cat", "Dog"]),
    # Set up but never played: no results, so not a past race at all.
    race("unplayed", now - 6 * 3600, "Fish", "Moon", []),
]

data = os.path.join(SCRATCH, "data")
os.makedirs(data)
db = sqlite3.connect(os.path.join(data, "wikirace.db"))
db.execute("CREATE TABLE races (race_id TEXT PRIMARY KEY, created REAL NOT NULL DEFAULT 0, data TEXT NOT NULL)")
db.execute("CREATE INDEX races_by_created ON races(created)")
db.execute("PRAGMA user_version = 1")
db.executemany("INSERT INTO races VALUES (?, ?, ?)", [(r["race_id"], r["created"], json.dumps(r)) for r in races])
db.commit()
db.close()

proc, BASE = start(data)


def races_api(**q):
    url = BASE + "/api/races" + ("?" + urllib.parse.urlencode(q) if q else "")
    return json.loads(urllib.request.urlopen(url, timeout=10).read())


def post(path, sid, body):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


try:
    print("\n1. everything played, newest first")
    d = races_api(limit=500)
    ids = [r["race_id"] for r in d["races"]]
    check("every race with a result is listed, archive included", d["total"] == 73, d["total"])
    check("the oldest race, outside the working set, is there", "plain00" in ids)
    check("a race nobody played is not", "unplayed" not in ids)
    check("newest first", [r["created"] for r in d["races"]] == sorted((r["created"] for r in d["races"]), reverse=True))
    check("the newest is first", ids[0] == "oldlost", ids[:3])

    print("\n2. a page at a time")
    d = races_api(limit=8)
    check("limit is honoured", len(d["races"]) == 8, len(d["races"]))
    check("the total still counts everything", d["total"] == 73, d["total"])
    check("nonsense in limit falls back to a page", len(races_api(limit="lots")["races"]) == 20)
    check("no more than 500 at once", len(races_api(limit=100000)["races"]) == 73)

    print("\n3. the right winner, and who came where")
    by = {r["race_id"]: r for r in races_api(limit=500)["races"]}
    c = by["clicks"]
    check("fewest clicks wins a clicks race", c["winner"]["name"] == "Ada", c["winner"])
    check("finishing order follows the race's rule", c["order"] == ["Ada", "Kody"], c["order"])
    check("the summary carries its stops", c["checkpoints"] == ["Italy"], c["checkpoints"])
    n = by["nobody"]
    check("nobody finished: no winner", n["winner"] is None, n["winner"])
    check("nobody finished: both gave up", sorted(n["quit"]) == ["BuraG", "Kody"], n["quit"])
    check("players are everyone with a result", sorted(n["players"]) == ["BuraG", "Kody"], n["players"])
    check("the fastest wins a time race", by["plain69"]["winner"]["name"] == "Kody", by["plain69"]["winner"])
    check("no paths in a summary", "results" not in c and "path" not in json.dumps(c))

    print("\n4. filters")
    check("by player, whatever the case", races_api(player="nessa", limit=500)["total"] == 1)
    check("by player, races they were in only", races_api(player="BuraG", limit=500)["total"] == 1)
    check("by game", [r["race_id"] for r in races_api(kind="advanced")["races"]] == ["clicks"])
    check("a race from before modes counts as lost", [r["race_id"] for r in races_api(kind="lost")["races"]] == ["oldlost"])
    check("a page that was the target", races_api(find="pizza")["total"] == 1)
    check("a page that was a stop", [r["race_id"] for r in races_api(find="ital")["races"]] == ["clicks"])
    check("a page that was the start", races_api(find="CHESS", limit=500)["total"] == 70)
    check("filters together", races_api(player="Kody", find="rocket")["total"] == 1)
    check("nothing matches", races_api(find="no such page")["total"] == 0)

    print("\n5. the race going on now")
    post("/api/name", "sidKimmy", {"name": "Kimmy"})
    post("/api/start_race", "sidKimmy", {"start": "Prague", "target": "Vltava", "kind": "classic"})
    check("a race with no results yet is not listed", races_api()["races"][0]["race_id"] == "oldlost")
    post("/api/progress", "sidKimmy", {"article": "Vltava", "clicks": 1, "path": ["Prague", "Vltava"], "times": [0, 4]})
    post("/api/finish", "sidKimmy", {"elapsed": 4.0, "clicks": 1, "path": ["Prague", "Vltava"], "times": [0, 4]})
    top = races_api()["races"][0]
    check("listed first once somebody finishes", top["target"] == "Vltava", top)
    check("with its winner", top["winner"] and top["winner"]["name"] == "Kimmy", top["winner"])
    check("and the total grows", races_api()["total"] == 74)
finally:
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()

print("\n%s" % ("ALL PASS" if not fails else "%d FAILED: %s" % (len(fails), ", ".join(fails))))
sys.exit(1 if fails else 0)
