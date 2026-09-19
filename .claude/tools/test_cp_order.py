# -*- coding: utf-8 -*-
"""Checkpoints have to be made where the race asked for them."""
import json, sys, urllib.request
B = "http://127.0.0.1:8477"
fails = []

def post(p, sid, body=None):
    req = urllib.request.Request("%s%s?sid=%s" % (B, p, sid), data=json.dumps(body or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else "   " + str(detail)))
    if not ok: fails.append(label)

def race(slots):
    return post("/api/start_race", "sidA", {"start": "Start", "target": "End", "kind": "advanced",
                                            "checkpoints": ["Alpha", "Beta", "Gamma"],
                                            "checkpoint_slots": slots})

def run(sid, path):
    post("/api/progress", sid, {"article": path[-1], "clicks": len(path) - 1, "path": path,
                                "times": [i * 5.0 for i in range(len(path))]})
    return post("/api/finish", sid, {"elapsed": 60.0, "clicks": len(path) - 1, "path": path})

post("/api/name", "sidA", {"name": "Orderly"})
post("/api/name", "sidB", {"name": "Wrongway"})

print("\n1. any order (nothing pinned)")
race([0, 0, 0])
check("any order is fine", run("sidA", ["Start", "Gamma", "Alpha", "Beta", "End"]).get("ok") is True)

print("\n2. Gamma must be last")
race([0, 0, 3])
r = run("sidB", ["Start", "Alpha", "Gamma", "Beta", "End"])
check("Gamma in the middle is refused", r.get("error") == "checkpoints out of order", r)
check("and it says which stop", r.get("wrong") == ["Gamma"], r)
check("Gamma last is allowed", run("sidA", ["Start", "Beta", "Alpha", "Gamma", "End"]).get("ok") is True)

print("\n3. Beta second, the rest either way")
race([0, 2, 0])
check("Alpha, Beta, Gamma works", run("sidA", ["Start", "Alpha", "Beta", "Gamma", "End"]).get("ok") is True)
race([0, 2, 0])
check("Gamma, Beta, Alpha works too", run("sidA", ["Start", "Gamma", "Beta", "Alpha", "End"]).get("ok") is True)
race([0, 2, 0])
r = run("sidB", ["Start", "Beta", "Alpha", "Gamma", "End"])
check("Beta first is refused", r.get("error") == "checkpoints out of order", r)

print("\n4. all three in order")
race([1, 2, 3])
check("in order works", run("sidA", ["Start", "Alpha", "Beta", "Gamma", "End"]).get("ok") is True)
race([1, 2, 3])
r = run("sidB", ["Start", "Alpha", "Gamma", "Beta", "End"])
check("out of order is refused", r.get("error") == "checkpoints out of order", r)
check("and names both stops", sorted(r.get("wrong") or []) == ["Beta", "Gamma"], r)

print("\n5. a missed stop is still a missed stop")
race([1, 2, 3])
r = run("sidB", ["Start", "Alpha", "Beta", "End"])
check("missing beats order", r.get("error") == "checkpoints missed", r)

print("\n6. revisiting counts from the first time")
race([0, 0, 3])
r = run("sidB", ["Start", "Gamma", "Alpha", "Beta", "Gamma", "End"])
check("coming back to Gamma doesn't fix the order", r.get("error") == "checkpoints out of order", r)

print("\n%s" % ("all checks passed" if not fails else "FAILURES: %s" % fails))
sys.exit(1 if fails else 0)
