# -*- coding: utf-8 -*-
"""Play a lost race against a local test server: four players, four starts."""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8477")
STARTS = ["Physics", "Coffee", "Vikings", "Dolphin", "Jazz", "Mount Everest"]
TARGET = "Pulsar"
# Each player's route from wherever they land, all meeting near the target.
TAILS = {
    "Kimmy": ["Science", "Astronomy", "Star", "Supernova", "Neutron star", "Pulsar"],
    "Kody": ["Chemistry", "Energy", "Star", "Black hole", "Neutron star", "Pulsar"],
    "BuraG": ["History", "Science", "Astronomy", "Galaxy", "Supernova", "Neutron star", "Pulsar"],
    "machmar": ["Music", "Sound", "Wave", "Light", "Astronomy", "Star", "Neutron star", "Pulsar"],
}


def post(path, sid, body=None):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


for name in TAILS:
    post("/api/name", "sid" + name, {"name": name})

race = post("/api/start_race", "sidKimmy",
            {"target": TARGET, "lost": True, "starts": STARTS, "lang": "en"})
print("race:", race.get("ok"), race.get("race", {}).get("race_id"), "lost:", race.get("race", {}).get("lost"))

mine = {}
for name in TAILS:
    got = post("/api/start_page", "sid" + name)
    mine[name] = got.get("start")
    print(" ", name, "starts at", got.get("start"), "|", got)
    # Asking twice gives the same page.
    again = post("/api/start_page", "sid" + name).get("start")
    assert again == mine[name], (name, again, mine[name])
assert len(set(mine.values())) == len(mine), mine
print("four different starts, stable on a second ask")

for i, (name, tail) in enumerate(TAILS.items()):
    path = [mine[name]] + tail
    times = [round(j * (5.0 + i), 1) for j in range(len(path))]
    post("/api/progress", "sid" + name,
         {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": times})
    res = post("/api/finish", "sid" + name,
               {"elapsed": times[-1], "clicks": len(path) - 1, "path": path, "times": times})
    print(" ", name, "finished:", res.get("ok"), res.get("error", ""))
