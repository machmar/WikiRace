# -*- coding: utf-8 -*-
"""A tangled classic race: one start, one target, six long routes, one photo finish."""
import json
import sys
import urllib.request

SID = lambda name: "sid" + "".join(c for c in name if c.isalnum())
BASE = "http://127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8477")
START, TARGET = "Chess", "Neutron star"

# Everyone leaves from the same page and nobody agrees on a direction. They
# collide at Physics, Astronomy and Star over and over, and three of them
# double back through pages they'd already seen.
ROUTES = {
    "Kimmy": [START, "Strategy", "War", "History", "Science", "Physics", "Energy", "Heat",
              "Thermodynamics", "Entropy", "Information theory", "Mathematics", "Science", "Astronomy",
              "Star", "Nuclear fusion", "Hydrogen", "Chemistry", "Periodic table", "Helium", "Sun",
              "Star", "Supernova", "Neutron star"],
    "Kody": [START, "India", "Asia", "Europe", "Science", "Mathematics", "Geometry", "Euclid",
             "Ancient Greece", "Philosophy", "Aristotle", "Physics", "Astronomy", "Telescope",
             "Galileo Galilei", "Star", "Supernova", "Neutron star"],
    "BuraG": [START, "Board game", "Game", "Play (activity)", "Child", "Human", "Brain", "Neuron",
              "Electricity", "Physics", "Magnetism", "Electromagnetism", "Light", "Optics", "Telescope",
              "Astronomy", "Galaxy", "Milky Way", "Star", "Black hole", "Neutron star"],
    "machmar": [START, "Computer chess", "Computer", "Artificial intelligence", "Algorithm",
                "Mathematics", "Physics", "Quantum mechanics", "Atom", "Electron", "Particle physics",
                "Nuclear physics", "Nuclear fusion", "Star", "Astronomy", "Cosmology", "Big Bang",
                "Universe", "Supernova", "Neutron star"],
    # The long way round: a detour nobody else takes, then a sprint at the end.
    "Robin Boson": [START, "Russia", "Soviet Union", "Cold War", "Space Race", "Sputnik 1",
                    "Spaceflight", "Rocket", "NASA", "Hubble Space Telescope", "Telescope", "Astronomy",
                    "Star", "Stellar evolution", "Supernova", "Neutron star"],
    # Got lost in the history of the game itself.
    "Ada": [START, "Chess piece", "Queen (chess)", "Monarchy", "Middle Ages", "Feudalism", "Europe",
            "Renaissance", "Art", "Painting", "Colour", "Light"],
    # Joined, looked at the start page and walked off. No route at all, which
    # is a real result with an empty path, and the replay has to say something
    # about it.
    "Nessa": [],
}
QUIT = {"Ada", "Nessa"}
PAUSES = [5.0, 8.5, 3.0, 18.0, 6.0, 4.5, 11.0, 3.5, 26.0, 7.0, 2.5, 14.0, 5.0, 9.0, 4.0, 12.0, 6.5, 22.0, 3.0, 8.0]
# Kody and BuraG cross the line within a second of each other.
PACE = {"Kimmy": 1.08, "Kody": 0.82, "BuraG": 0.955, "machmar": 1.0, "Robin Boson": 1.14, "Ada": 1.0}


def post(path, sid, body=None):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def times_for(name, path):
    out, t = [0.0], 0.0
    seed = sum(ord(c) for c in name)
    for i in range(1, len(path)):
        t += PAUSES[(seed + i * 5) % len(PAUSES)] * PACE.get(name, 1.0)
        out.append(round(t, 1))
    return out


for name in ROUTES:
    post("/api/name", SID(name), {"name": name})

race = post("/api/start_race", SID("Kody"), {
    "start": START, "target": TARGET, "kind": "classic", "lang": "en", "lost": False,
    "mode": "time", "checkpoints": [],
    "show_positions": True, "allow_back": True, "allow_find": True, "allow_peek": True,
})
print("race:", race.get("ok"), START, "->", TARGET)

for name, path in ROUTES.items():
    if not path:
        post("/api/give_up", SID(name), {"elapsed": 41.0, "clicks": 0})
        print("  %-12s gave up without clicking anything" % name)
        continue
    times = times_for(name, path)
    post("/api/progress", SID(name),
         {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": times})
    if name in QUIT:
        post("/api/give_up", SID(name), {"elapsed": times[-1] + 55, "clicks": len(path) - 1})
        print("  %-12s gave up after %5.1fs, %d clicks" % (name, times[-1] + 55, len(path) - 1))
    else:
        res = post("/api/finish", SID(name),
                   {"elapsed": times[-1], "clicks": len(path) - 1, "path": path, "times": times})
        print("  %-12s %s in %5.1fs, %d clicks" % (name, "finished" if res.get("ok") else res, times[-1], len(path) - 1))
