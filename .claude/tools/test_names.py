# -*- coding: utf-8 -*-
"""The name is the player: same name on any device is the same player."""
import json
import os
import shutil
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
    p = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(PORT), "--room", "names",
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
    p.kill()
    return p.communicate()[0]


def get(path, sid):
    return json.loads(urllib.request.urlopen("%s%s%ssid=%s" % (BASE, path, "&" if "?" in path else "?", sid), timeout=10).read())


def post(path, sid, body):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def finish(sid, path, secs):
    post("/api/progress", sid, {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": [0] * len(path)})
    return post("/api/finish", sid, {"elapsed": secs, "clicks": len(path) - 1, "path": path})


def board(sid):
    return {e["name"]: e for e in get("/api/state", sid)["leaderboard"]}


def kody(b):
    return next((e for n, e in b.items() if n.strip().lower() == "kody"), {})


data = os.path.join(SCRATCH, "namedata")
shutil.rmtree(data, ignore_errors=True)
os.makedirs(data)
legacy = [{"race_id": "legacy0", "start": "A", "target": "B", "created": 100.0, "mode": "time",
           "results": {"kody": {"name": "Kody", "finished": True, "clicks": 2, "elapsed": 9.0, "path": ["A", "X", "B"]}}}]
json.dump({"races": legacy}, open(os.path.join(data, "wikirace_history.json"), "w", encoding="utf-8"))
p = start(data)

print("\n1. the same name on another device is the same player")
check("the laptop plays as Kody", post("/api/name", "laptop", {"name": "Kody"}).get("ok") is True)
check("the phone can be Kody too", post("/api/name", "phone", {"name": "  kody "}).get("ok") is True)
check("a friend picks another name", post("/api/name", "friend", {"name": "Robin Boson"}).get("ok") is True)
b = board("friend")
check("Kody's old results already count", b.get("Kody", {}).get("points") == 13, b)

race = post("/api/start_race", "friend", {"start": "Cheese", "target": "Milk"})["race"]
finish("laptop", ["Cheese", "Milk"], 3.0)
finish("friend", ["Cheese", "Cow", "Milk"], 5.0)
race2 = post("/api/start_race", "friend", {"start": "Bread", "target": "Milk"})["race"]
finish("friend", ["Bread", "Milk"], 2.0)
finish("phone", ["Bread", "Cow", "Milk"], 4.0)
b = board("friend")
kodys = [n for n in b if n.lower() == "kody"]
check("one Kody on the scoreboard, not two", len(kodys) == 1, list(b))
k = b[kodys[0]] if kodys else {}
check("laptop and phone results add up", k.get("races") == 3 and k.get("points") == 13 + 13 + 7, k)
check("a result is filed under the name", "kody" in get("/api/race?id=" + race["race_id"], "friend")["results"])

print("\n2. one name races once per race")
race3 = post("/api/start_race", "friend", {"start": "Salt", "target": "Milk"})["race"]
post("/api/progress", "friend", {"article": "Salt", "clicks": 0, "path": ["Salt"]})
first = post("/api/progress", "laptop", {"article": "Salt", "clicks": 0, "path": ["Salt"]})
check("the laptop joins the race as Kody", first is None or first.get("ok") is not False, first)
second = post("/api/progress", "phone", {"article": "Salt", "clicks": 0, "path": ["Salt"]})
check("the phone can't also race as Kody", second.get("error") == "name_in_race", second)
check("a refreshed laptop is still the same runner", (post("/api/progress", "laptop", {"article": "Sea", "clicks": 1, "path": ["Salt", "Sea"]}) or {}).get("ok") is not False)
check("the phone can't finish as Kody", finish("phone", ["Salt", "Milk"], 1.0).get("error") == "name_in_race")
check("or give up as Kody", post("/api/give_up", "phone", {"elapsed": 2.0, "clicks": 0}).get("error") == "name_in_race")
check("a guest can't race as Kody either", post("/api/name", "visitor", {"name": "KODY", "guest": True}).get("error") == "name_in_race")
check("the phone can't rename into a name that's racing", post("/api/name", "phone", {"name": "Robin Boson"}).get("error") == "name_in_race")
check("the phone picks another name", post("/api/name", "phone", {"name": "Kody Mobil"}).get("ok") is True)
check("and joins the race under it", (post("/api/progress", "phone", {"article": "Salt", "clicks": 0, "path": ["Salt"]}) or {}).get("ok") is not False)
finish("laptop", ["Salt", "Sea", "Milk"], 3.0)
check("once Kody has finished, the name is still taken while the race runs",
      post("/api/name", "visitor", {"name": "Kody"}).get("error") == "name_in_race")
res = get("/api/race?id=" + race3["race_id"], "friend")["results"]
check("exactly one Kody result, and it's the laptop's win",
      [r["finished"] for r in res.values() if r["name"].lower() == "kody"] == [True], res)
finish("phone", ["Salt", "Milk"], 4.0)
post("/api/give_up", "friend", {"elapsed": 5.0, "clicks": 0})
check("when everyone's done, the phone can be Kody again", post("/api/name", "phone", {"name": "Kody"}).get("ok") is True)
b = board("friend")
check("and Kody counted that race once", kody(b)["races"] == 4, kody(b))

print("\n3. guests")
check("a guest can use any name", post("/api/name", "visitor", {"name": "Kody", "guest": True}).get("ok") is True)
race4 = post("/api/start_race", "friend", {"start": "Oil", "target": "Milk"})["race"]
finish("visitor", ["Oil", "Milk"], 1.0)
b = board("friend")
check("a guest's race doesn't touch Kody's score", kody(b)["races"] == 4, kody(b))
check("but the guest is in the race results", any(r.get("guest") for r in get("/api/race?id=" + race4["race_id"], "friend")["results"].values()))

print("\n4. renaming is becoming somebody else")
before = board("friend")["Robin Boson"]["points"]
post("/api/name", "friend", {"name": "Miloslav Nemes"})
b = board("friend")
check("the old name keeps its points", b.get("Robin Boson", {}).get("points") == before, b)
check("the new name starts fresh", "Miloslav Nemes" not in b, b)

print("\n5. restart and handicaps")
stop(p)
p = start(data)
post("/api/name", "laptop", {"name": "Kody"})
b = board("laptop")
check("standings survive a restart", b.get("Kody", {}).get("races") == 4 or b.get("kody", {}).get("races") == 4, b)
hc = post("/api/start_race", "laptop", {"start": "A", "target": "B", "handicap": True})["race"]["handicaps"]
check("handicaps are keyed by name", "kody" in hc, hc)
stop(p)

print("\n%s" % ("all checks passed" if not fails else "FAILURES: %s" % fails))
sys.exit(1 if fails else 0)
