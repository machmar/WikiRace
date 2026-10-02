# -*- coding: utf-8 -*-
"""Points reflect how hard the race was, issue #13.

The rules are checked straight off the functions, because a race dict is all
they need; then once through a server, to see the standings and both places a
browser reads a race from carry the same sums.
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
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
GAME = os.path.join(ROOT, "wikirace.py")
sys.path.insert(0, ROOT)
import wikirace  # noqa: E402

fails = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else "   " + str(detail)))
    if not ok:
        fails.append(label)


EASY = {"show_positions": True, "allow_back": True, "allow_find": True, "allow_peek": True,
        "ban_hubs": False, "allow_tables": True, "toc": 3, "time_limit": 0}
NORMAL = dict(EASY, allow_back=False, allow_find=False, allow_tables=False, toc=1)
HARD = dict(NORMAL, show_positions=False, allow_peek=False, ban_hubs=True, toc=0, time_limit=600)


def hard(race):
    return sorted(wikirace.race_difficulty(race))


def run(name, secs, clicks, finished=True, guest=False):
    return {"name": name, "finished": finished, "gave_up": not finished, "elapsed": secs,
            "clicks": clicks, "guest": guest}


def with_results(rules, *runs, **extra):
    race = dict(rules, **extra)
    race["results"] = {r["name"].lower(): r for r in runs}
    return race


print("\n1. what counts as harder")
check("an easy race has nothing", hard(dict(EASY)) == [], hard(dict(EASY)))
check("the normal preset: no back, no find, no link tables",
      hard(dict(NORMAL)) == ["no_back", "no_find", "no_tables"], hard(dict(NORMAL)))
check("contents cut to main sections is not off", "no_contents" not in hard(dict(EASY, toc=1)))
check("contents off counts", hard(dict(EASY, toc=0)) == ["no_contents"], hard(dict(EASY, toc=0)))
check("the hard preset counts eight",
      hard(dict(HARD)) == ["hidden", "no_back", "no_contents", "no_find", "no_hubs", "no_reveal",
                           "no_tables", "time_limit"], hard(dict(HARD)))
check("a ten-minute limit counts", hard(dict(EASY, time_limit=600)) == ["time_limit"])
check("a half-hour limit doesn't", hard(dict(EASY, time_limit=1800)) == [])
check("a lost race counts", hard(dict(EASY, lost=True)) == ["lost"])
check("every checkpoint counts",
      hard(dict(EASY, checkpoints=["A", "B", "C"])) == ["checkpoint"] * 3, hard(dict(EASY, checkpoints=["A", "B", "C"])))
check("a pinned order counts once more",
      hard(dict(EASY, checkpoints=["A", "B", "C"], checkpoint_slots=[1, 2, 3])) == ["checkpoint"] * 3 + ["order"])
check("pinning one of two is an order too",
      hard(dict(EASY, checkpoints=["A", "B"], checkpoint_slots=[0, 2])) == ["checkpoint"] * 2 + ["order"])
check("pinning a lone stop is no order at all",
      hard(dict(EASY, checkpoints=["A"], checkpoint_slots=[1])) == ["checkpoint"])
check("a handicap isn't the race being harder", hard(dict(EASY, handicaps={"kody": 10})) == [])
check("the target being revealed doesn't matter, only the rule", hard(dict(EASY, peek=True)) == [])
check("an old race reads its missing rules the way the rules list does",
      hard({"start": "A", "target": "B"}) == ["no_contents", "no_tables"], hard({"start": "A", "target": "B"}))

print("\n2. the sums")
s = wikirace.race_scoring(dict(EASY, results={}))
check("an easy race pays the usual points", s["multiplier"] == 1 and s["step"] == 20, s)
s = wikirace.race_scoring(dict(HARD))
check("eight hard things make it x2.6", s["multiplier"] == 2.6, s)
s = wikirace.race_scoring(dict(HARD, lost=True, checkpoints=["A", "B", "C"], checkpoint_slots=[1, 2, 3]))
check("hard and lost through three stops in order is x3.6", s["multiplier"] == 3.6, s)

race = with_results(NORMAL, run("Ada", 30, 6), run("Bo", 40, 3), run("Cy", 50, 9), run("Di", 9, 1, finished=False))
p = wikirace.race_scoring(race)["players"]
check("the winner's 10, times 1.6", p["Ada"] == {"place": 1, "place_points": 10, "bonus": 0, "points": 16}, p.get("Ada"))
check("second with the fewest clicks: 7 + 3, times 1.6",
      p["Bo"] == {"place": 2, "place_points": 7, "bonus": 3, "points": 16}, p.get("Bo"))
check("third: 5 times 1.6", p["Cy"]["points"] == 8, p.get("Cy"))
check("giving up is worth nothing", "Di" not in p, p)

race = with_results(HARD, run("Ada", 30, 6), run("Bo", 40, 7), run("Cy", 50, 8), run("Ed", 60, 9), run("Fy", 70, 9))
p = wikirace.race_scoring(race)["players"]
check("rounded to the nearest point: 7 x 2.6 is 18", p["Bo"]["points"] == 18, p.get("Bo"))
check("and 3 x 2.6 is 8", p["Ed"]["points"] == 8, p.get("Ed"))
check("fifth and later still get 2, scaled to 5", p["Fy"] == {"place": 5, "place_points": 2, "bonus": 0, "points": 5}, p.get("Fy"))
check("the winner can take the bonus too", p["Ada"]["bonus"] == 3 and p["Ada"]["points"] == 34, p.get("Ada"))

p = wikirace.race_scoring(with_results(EASY, run("Ada", 30, 6)))["players"]
check("finishing alone has nobody to beat for fewest clicks", p["Ada"]["bonus"] == 0 and p["Ada"]["points"] == 10, p)
p = wikirace.race_scoring(with_results(EASY, run("Ada", 30, 6), run("Bo", 30, 2), run("Cy", 40, 2)))["players"]
check("a tie for fewest clicks pays both", p["Bo"]["bonus"] == 3 and p["Cy"]["bonus"] == 3, p)
p = wikirace.race_scoring(with_results(dict(EASY, mode="clicks"), run("Ada", 50, 2), run("Bo", 20, 4)))["players"]
check("a clicks race gives the bonus for the fastest time", p["Bo"]["bonus"] == 3 and p["Ada"]["bonus"] == 0, p)
p = wikirace.race_scoring(with_results(EASY, run("Gus", 10, 1, guest=True), run("Ada", 30, 6)))["players"]
check("a guest takes their place but collects nothing", "Gus" not in p and p["Ada"]["place"] == 2
      and p["Ada"]["points"] == 7, p)

# -- through a server ---------------------------------------------------------

SCRATCH = tempfile.mkdtemp(prefix="wikirace-points-")
READY = re.compile(r"UI ready at http://localhost:(\d+)/")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


lines, said = [], threading.Event()
proc = subprocess.Popen([sys.executable, GAME, "--host", "--port", str(free_port()), "--room", "points",
                         "--no-discovery", "--data-dir", SCRATCH],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                        env=dict(os.environ, WIKIRACE_NO_BROWSER="1", PYTHONUNBUFFERED="1"))
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
    sys.exit("server did not start: " + "".join(lines)[-1500:])
BASE = "http://127.0.0.1:%d" % port[0]


def get(path, sid):
    return json.loads(urllib.request.urlopen("%s%s%ssid=%s" % (BASE, path, "&" if "?" in path else "?", sid), timeout=10).read())


def post(path, sid, body):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def finish(sid, path, secs):
    post("/api/progress", sid, {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": [0] * len(path)})
    return post("/api/finish", sid, {"elapsed": secs, "clicks": len(path) - 1, "path": path})


try:
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/healthz", timeout=1)
            break
        except OSError:
            time.sleep(0.2)

    print("\n3. the standings and the race carry the same sums")
    post("/api/name", "a", {"name": "Ada"})
    post("/api/name", "b", {"name": "Bo"})
    race = post("/api/start_race", "a", dict(NORMAL, start="Cheese", target="Milk"))["race"]
    finish("a", ["Cheese", "Cow", "Grass", "Milk"], 3.0)
    finish("b", ["Cheese", "Milk"], 5.0)
    board = {e["name"]: e["points"] for e in get("/api/state", "a")["leaderboard"]}
    check("the standings pay a normal race x1.6", board == {"Ada": 16, "Bo": 16}, board)
    live = get("/api/state", "a")["race"]
    check("the race on screen says why", live.get("scoring", {}).get("players", {}).get("Bo", {}).get("bonus") == 3,
          live.get("scoring"))
    old = get("/api/race?id=" + race["race_id"], "a")
    check("so does a past race", old.get("scoring", {}).get("multiplier") == 1.6, old.get("scoring"))
    check("and the reasons are named", sorted(old["scoring"]["hard"]) == ["no_back", "no_find", "no_tables"],
          old.get("scoring"))

    print("\n4. race setup asks what a race would pay before it starts")

    def draft(body):
        try:
            return post("/api/score_rules", "a", body)
        except urllib.error.HTTPError as e:
            return {"error": e.code}

    d = draft(dict(NORMAL))
    check("a normal draft counts three", sorted(d.get("hard", [])) == ["no_back", "no_find", "no_tables"] and d.get("step") == 20, d)
    d = draft(dict(EASY, lost=True, checkpoints=["Energy", "  ", "Star"], checkpoint_slots=[1, 0, 2]))
    check("a draft is read the way a race would be: blank stops dropped, lost and order counted",
          sorted(d.get("hard", [])) == ["checkpoint", "checkpoint", "lost", "order"], d)
    check("the same rules a started race would be scored on",
          sorted(draft(dict(HARD)).get("hard", [])) == hard(dict(HARD)))
    check("asking starts nothing", get("/api/state", "a")["race"]["race_id"] == race["race_id"])
finally:
    proc.kill()
    proc.wait()
    shutil.rmtree(SCRATCH, ignore_errors=True)

print("\n%s" % ("all checks passed" if not fails else "FAILURES: %s" % fails))
sys.exit(1 if fails else 0)
