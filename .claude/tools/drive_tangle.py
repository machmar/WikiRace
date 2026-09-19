# -*- coding: utf-8 -*-
"""A messy lost race: six players, six starts, one checkpoint, two who give up."""
import json
import sys
import urllib.request

SID = lambda name: "sid" + "".join(c for c in name if c.isalnum())
BASE = "http://127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8477")
TARGET = "Pulsar"
CHECK = "Energy"

# Long routes that keep meeting at the same few hubs, double back, and wander
# off alone for a while - the shapes the maps exist to untangle.
ROUTES = {
    "Kimmy": ["Coffee", "Caffeine", "Chemistry", "Molecule", "Atom", "Physics", "Energy", "Heat",
              "Thermodynamics", "Entropy", "Physics", "Astronomy", "Star", "Nuclear fusion", "Hydrogen",
              "Chemistry", "Periodic table", "Helium", "Sun", "Star", "Supernova", "Neutron star", "Pulsar"],
    "Kody": ["Jazz", "Music", "Sound", "Wave", "Light", "Optics", "Telescope", "Astronomy", "Galaxy",
             "Milky Way", "Star", "Energy", "Nuclear fusion", "Supernova", "Neutron star", "Pulsar"],
    "BuraG": ["Physics", "Gravity", "Isaac Newton", "Mathematics", "Geometry", "Euclid", "Ancient Greece",
              "Philosophy", "Aristotle", "Physics", "Energy", "Electricity", "Magnetism", "Electromagnetism",
              "Light", "Astronomy", "Black hole", "Neutron star", "Pulsar"],
    "machmar": ["Dolphin", "Whale", "Ocean", "Water", "Hydrogen", "Chemistry", "Chemical element",
                "Periodic table", "Dmitri Mendeleev", "Russia", "Soviet Union", "Sputnik 1", "Spaceflight",
                "Rocket", "NASA", "Hubble Space Telescope", "Astronomy", "Star", "Energy", "Supernova",
                "Neutron star", "Pulsar"],
    # Wanders a long way alone before finding the pack - the Collapsed map's +N.
    "Robin Boson": ["Mount Everest", "Himalayas", "Nepal", "Kathmandu", "Monsoon", "Rain", "Cloud",
                    "Atmosphere of Earth", "Nitrogen", "Chemical element", "Chemistry", "Physics", "Energy",
                    "Star", "Astronomy", "Cosmology", "Big Bang", "Universe", "Supernova", "Neutron star", "Pulsar"],
    # Gave up out in the cold.
    "Ada": ["Vikings", "Norway", "Scandinavia", "Baltic Sea", "Fishing", "Salmon", "River", "Water",
            "Ice", "Glacier", "Antarctica", "Penguin", "Bird", "Dinosaur"],
}
QUIT = {"Ada"}
# Seconds spent on each page: mostly a few, now and then a long read.
PAUSES = [4.5, 9.0, 3.5, 21.0, 6.5, 5.0, 12.5, 4.0, 30.0, 7.5, 3.0, 16.0, 5.5, 8.0, 4.5, 11.0, 6.0, 25.0, 3.5, 9.5]


def post(path, sid, body=None):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def times_for(name, path):
    out, t = [0.0], 0.0
    seed = sum(ord(c) for c in name)
    for i in range(1, len(path)):
        t += PAUSES[(seed + i * 7) % len(PAUSES)] * (0.8 + (seed % 5) * 0.12)
        out.append(round(t, 1))
    return out


for name in ROUTES:
    post("/api/name", SID(name), {"name": name})

race = post("/api/start_race", SID("Kimmy"), {
    "target": TARGET, "lost": True, "kind": "lost", "lang": "en",
    "starts": [p[0] for p in ROUTES.values()],
    "checkpoints": [CHECK], "mode": "time",
    "show_positions": True, "allow_back": True, "allow_find": True, "allow_peek": True,
})
print("race:", race.get("ok"), race.get("race", {}).get("race_id"))

for name, path in ROUTES.items():
    times = times_for(name, path)
    post("/api/progress", SID(name),
         {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": times})
    if name in QUIT:
        res = post("/api/give_up", SID(name), {"elapsed": times[-1] + 40, "clicks": len(path) - 1})
        print("  %-12s gave up after %5.1fs, %d clicks" % (name, times[-1] + 40, len(path) - 1))
    else:
        res = post("/api/finish", SID(name),
                   {"elapsed": times[-1], "clicks": len(path) - 1, "path": path, "times": times})
        print("  %-12s %s in %5.1fs, %d clicks" % (name, "finished" if res.get("ok") else res, times[-1], len(path) - 1))
