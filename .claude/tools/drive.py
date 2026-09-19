# -*- coding: utf-8 -*-
"""Play a four-player race against a local test server."""
import json
import sys
import urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else "8477"
BASE = "http://127.0.0.1:" + PORT

ROUTES = {
    "Kimmy": ["Karel IV.", "Praha", "Vltava", "Labe", "Německo", "Evropa", "Věda", "Fyzika", "Evropa", "Latina", "Řečtina", "Věda", "Filozofie", "Aristotelés", "Fyzika", "Matematika", "Isaac Newton", "Gravitace", "Fyzika", "Světlo", "Optika", "Dalekohled", "Astronomie", "Hvězda", "Vesmír", "Hvězda", "Supernova", "Neutronová hvězda", "Pulsar"],
    "Kody": ["Karel IV.", "Univerzita Karlova", "Věda", "Chemie", "Vodík", "Helium", "Jaderná fúze", "Energie", "Fyzika", "Evropa", "Česko", "Věda", "Astronomie", "Galileo Galilei", "Itálie", "Renesance", "Evropa", "Dalekohled", "Hubbleův vesmírný dalekohled", "NASA", "Vesmír", "Černá díra", "Neutronová hvězda", "Pulsar"],
    "BuraG": ["Karel IV.", "Rakousko-Uhersko", "Česko", "Evropa", "Německo", "Věda", "Fyzika", "Energie", "Teplota", "Kelvin", "Fyzika", "Astronomie", "Sluneční soustava", "Slunce", "Hvězda", "Jaderná fúze", "Vodík", "Chemie", "Věda", "Astronomie", "Mléčná dráha", "Galaxie", "Vesmír", "Kosmologie", "Supernova", "Neutronová hvězda", "Pulsar"],
    "machmar": ["Karel IV.", "Svatá říše římská", "Středověk", "Gotika", "Architektura", "Stavba", "Most", "Karlův most", "Vltava", "Řeka", "Voda", "Vodík", "Chemický prvek", "Periodická tabulka prvků", "Dmitrij Ivanovič Mendělejev", "Rusko", "Sovětský svaz", "Studená válka", "Sputnik 1", "Kosmonautika", "Raketa", "NASA", "Spojené státy americké", "Věda", "Vesmír", "Hvězda", "Supernova", "Neutronová hvězda", "Pulsar"],
}


def post(path, sid, body=None):
    req = urllib.request.Request("%s%s?sid=%s" % (BASE, path, sid),
                                 data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def get(path, sid):
    return json.loads(urllib.request.urlopen("%s%s?sid=%s" % (BASE, path, sid), timeout=10).read())


cmd = sys.argv[2] if len(sys.argv) > 2 else "race"

if cmd == "race":
    for name in ROUTES:
        post("/api/name", "sid" + name, {"name": name})
        get("/api/state", "sid" + name)
    r = post("/api/start_race", "sidKimmy", {"start": "Karel IV.", "target": "Pulsar", "lang": "cs",
                                             "checkpoints": sys.argv[3:] if len(sys.argv) > 3 else []})
    print("race:", r.get("ok"), r.get("race", {}).get("race_id"))
    for i, (name, path) in enumerate(ROUTES.items()):
        times = [round(j * (6.5 + i), 1) for j in range(len(path))]
        post("/api/progress", "sid" + name, {"article": path[-1], "clicks": len(path) - 1, "path": path, "times": times})
        res = post("/api/finish", "sid" + name, {"elapsed": times[-1], "clicks": len(path) - 1, "path": path, "times": times})
        print(name, "finished:", res.get("ok"), res.get("error", ""))

elif cmd == "state":
    s = get("/api/state", "sidKimmy")
    print("results:", sorted((s["race"] or {}).get("results", {}).keys()))
