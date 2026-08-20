#!/usr/bin/env python3
"""
WikiRace LAN - serverless multiplayer Wikipedia racing.

Every player runs this script. Peers find each other on the local network with
UDP multicast + broadcast; there is no central server. Game state is gossiped
between peers and each peer derives the leaderboard independently, so nobody's
machine is special and nobody's exit ends the game.

    py wikirace.py                 # play
    py wikirace.py --name Marek    # set your display name
    py wikirace.py --peer 192.168.1.42   # manual peer if broadcast is blocked

Requires Python 3.9+. Standard library only.
"""

import argparse
import hashlib
import json
import os
import random
import re
import socket
import struct
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))

MCAST_GRP = "239.255.42.99"
DISCOVERY_PORT = 8421
DEFAULT_HTTP_PORT = 8420

HEARTBEAT_INTERVAL = 1.0      # seconds between idle presence broadcasts
RACE_TICK_INTERVAL = 0.35     # seconds between position broadcasts while racing
PEER_TIMEOUT = 12.0           # drop peers unheard from this long
DIGEST_INTERVAL = 5.0         # seconds between history digest broadcasts
MAX_RACES_KEPT = 60

POINTS_BY_RANK = [10, 7, 5, 3]
POINTS_FINISH_OTHER = 2
POINTS_FEWEST_CLICKS = 3

LIVE_PATH_STEPS = 25        # recent trail sent live; the full path ships in the result
HANDICAP_SECONDS = [10, 5]  # start delay for 1st and 2nd in the standings
LOCAL_PLAYER_GRACE = 45.0   # how long a browser keeps its seat after disconnecting

PALETTE = [
    "#f97583", "#79c0ff", "#7ee787", "#ffa657", "#d2a8ff",
    "#56d4dd", "#f2cc60", "#ff9bce", "#a5d6ff", "#b4f1b4",
]


def log(*a):
    print("[wikirace]", *a, flush=True)


def now():
    return time.time()


def norm_name(name):
    return " ".join((name or "").split()).lower()


# --------------------------------------------------------------------------
# Shared game state.  Guarded by one lock; every mutation bumps `version` so
# the HTTP layer can tell connected browsers that something changed.
# --------------------------------------------------------------------------

class Player:
    """One person playing through this process.

    Running the script yourself gives you exactly one of these. Hosting for
    friends who only have a browser gives you one per connected browser - and
    since each is gossiped under its own id, nobody else on the network can
    tell the two arrangements apart.
    """

    def __init__(self, pid, name):
        self.id = pid
        self.name = name
        self.color = PALETTE[int(hashlib.md5(pid.encode()).hexdigest(), 16) % len(PALETTE)]
        self.run = None             # clicks, path, times, started_at, finished, elapsed
        self.ready = False
        self.show_opponents = True  # personal preference; the race rule can override
        self.last_seen = now()
        self.streams = 0            # open browser connections

    def alive(self):
        # A browser that closed keeps its seat briefly, so a refresh mid-race
        # doesn't drop the player out of the game.
        return self.streams > 0 or (now() - self.last_seen) < LOCAL_PLAYER_GRACE


class GameState:
    def __init__(self, seed_name, http_port, room="default"):
        self.lock = threading.RLock()
        self.version = 0
        self.http_port = http_port
        self.room = room
        self.seed_name = seed_name      # --name, for whoever is at this machine
        self.seed_used = False
        self.locals = {}                # session id -> Player
        self.known_names = {}           # session id -> name, survives a disconnect
        self.lan_urls = []
        self.public_url = None          # set once an internet tunnel is up
        self.join_code = None           # required to get in, when playing publicly

        # peer_id -> presence/live info
        self.peers = {}

        # race_id -> race record (the gossiped, mergeable history)
        self.races = {}

        # the race this process is currently in, if any
        self.active_race_id = None
        self.events = []            # short human-readable feed
        self.seq = 0

    # -- local players ------------------------------------------------------

    def player(self, sid, create=True, at_console=False):
        """Look up (or seat) the player behind a browser session."""
        p = self.locals.get(sid)
        if p is None and create:
            # Someone coming back after a dropped connection keeps the name
            # they chose, rather than reappearing as "Player 4".
            name = self.known_names.get(sid)
            if not name and at_console and not self.seed_used:
                # --name belongs to whoever is sitting at this machine, not to
                # the first stranger who happens to open the link.
                name = self.seed_name
                self.seed_used = True
            if not name:
                name = self.next_guest_name()
            p = Player(uuid.uuid4().hex[:12], name)
            self.locals[sid] = p
            self.add_event(f"{name} joined", "join")
            self.bump()
        if p:
            p.last_seen = now()
        return p

    def next_guest_name(self):
        taken = {norm_name(x.name) for x in self.locals.values()}
        taken |= {norm_name(n) for n in self.known_names.values()}
        for i in range(1, 100):
            candidate = f"Player {i}"
            if norm_name(candidate) not in taken:
                return candidate
        return "Player"

    def prune_locals(self):
        gone = [sid for sid, p in self.locals.items() if not p.alive()]
        for sid in gone:
            p = self.locals.pop(sid)
            self.known_names[sid] = p.name
            self.add_event(f"{p.name} left", "leave")
        if gone:
            self.bump()
        return gone

    # -- helpers (call with lock held) --------------------------------------

    def bump(self):
        self.version += 1

    def add_event(self, text, kind="info"):
        self.events.append({"t": now(), "text": text, "kind": kind})
        del self.events[:-40]

    def next_seq(self):
        self.seq += 1
        return self.seq

    def active_race(self):
        return self.races.get(self.active_race_id) if self.active_race_id else None

    def prune_peers(self):
        cutoff = now() - PEER_TIMEOUT
        gone = [pid for pid, p in self.peers.items() if p.get("last_seen", 0) < cutoff]
        for pid in gone:
            p = self.peers.pop(pid)
            self.add_event(f"{p.get('name', 'someone')} left", "leave")
        if gone:
            self.bump()

    def trim_races(self):
        if len(self.races) <= MAX_RACES_KEPT:
            return
        ordered = sorted(self.races.values(), key=lambda r: r.get("created", 0))
        for r in ordered[:len(self.races) - MAX_RACES_KEPT]:
            if r["race_id"] != self.active_race_id:
                self.races.pop(r["race_id"], None)

    # -- derived data -------------------------------------------------------

    def leaderboard(self):
        """Recomputed from scratch out of the gossiped race history.

        Because every peer merges the same set of race results, every peer
        arrives at the same table without anyone owning the truth.
        """
        tally = {}

        def slot(display):
            key = norm_name(display)
            if key not in tally:
                tally[key] = {
                    "name": display, "points": 0, "wins": 0, "races": 0,
                    "finished": 0, "clicks": 0, "best_time": None, "best_clicks": None,
                }
            return tally[key]

        for race in self.races.values():
            results = race.get("results", {})
            if not results:
                continue
            finishers = sorted(
                [r for r in results.values() if r.get("finished")],
                key=lambda r: (r.get("elapsed", 9e9), r.get("clicks", 999)),
            )
            fewest = min((r.get("clicks", 999) for r in finishers), default=None)

            for r in results.values():
                e = slot(r.get("name", "?"))
                e["races"] += 1

            for i, r in enumerate(finishers):
                e = slot(r.get("name", "?"))
                e["finished"] += 1
                e["clicks"] += r.get("clicks", 0)
                e["points"] += POINTS_BY_RANK[i] if i < len(POINTS_BY_RANK) else POINTS_FINISH_OTHER
                if fewest is not None and r.get("clicks") == fewest:
                    e["points"] += POINTS_FEWEST_CLICKS
                if i == 0:
                    e["wins"] += 1
                el = r.get("elapsed")
                if el is not None and (e["best_time"] is None or el < e["best_time"]):
                    e["best_time"] = el
                ck = r.get("clicks")
                if ck is not None and (e["best_clicks"] is None or ck < e["best_clicks"]):
                    e["best_clicks"] = ck

        rows = sorted(tally.values(), key=lambda e: (-e["points"], -e["wins"], e["name"]))
        for i, row in enumerate(rows):
            row["rank"] = i + 1
        return rows

    def compute_handicaps(self):
        """Start delays for whoever's running away with the session.

        A party game stops being fun once someone is untouchable, so the
        leaders give up a few seconds. Computed by the host from the shared
        standings and shipped with the race, so everyone agrees on it.
        """
        scored = [e for e in self.leaderboard() if e["points"] > 0]
        return {
            norm_name(e["name"]): HANDICAP_SECONDS[i]
            for i, e in enumerate(scored[:len(HANDICAP_SECONDS)])
        }

    def history_digest(self):
        """Cheap fingerprint of what we know, so peers can spot a gap."""
        parts = []
        for rid in sorted(self.races):
            names = ",".join(sorted(self.races[rid].get("results", {})))
            parts.append(f"{rid}:{names}")
        return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

    def snapshot(self, sid):
        """Everything one browser needs, in one JSON-able blob.

        Other people sharing this process look exactly like remote peers, so
        the whole UI is indifferent to how anyone happens to be connected.
        """
        with self.lock:
            me = self.player(sid)
            race = self.active_race()
            live = []

            for other_sid, q in self.locals.items():
                if other_sid == sid:
                    continue
                run = q.run or {}
                live.append({
                    "id": q.id, "name": q.name, "color": q.color,
                    "article": run.get("article"), "clicks": run.get("clicks", 0),
                    "finished": run.get("finished", False), "elapsed": run.get("elapsed"),
                    "gave_up": run.get("gave_up", False), "ready": q.ready,
                    "scroll": run.get("scroll", 0),
                    "path": (run.get("path") or [])[-LIVE_PATH_STEPS:],
                    "times": (run.get("times") or [])[-LIVE_PATH_STEPS:],
                    "race_id": run.get("race_id") or self.active_race_id,
                    "path_len": len(run.get("path", [])),
                    "in_this_race": bool(race) and (
                        run.get("race_id") == race["race_id"] or not run),
                    "local": True,
                })

            for pid, p in self.peers.items():
                live.append({
                    "id": pid, "name": p.get("name", "?"), "color": p.get("color", "#888"),
                    "article": p.get("article"), "clicks": p.get("clicks", 0),
                    "finished": p.get("finished", False), "elapsed": p.get("elapsed"),
                    "gave_up": p.get("gave_up", False), "ready": p.get("ready", False),
                    "scroll": p.get("scroll", 0),
                    "path": p.get("path", []), "times": p.get("times", []),
                    "race_id": p.get("race_id"), "path_len": p.get("path_len", 0),
                    "in_this_race": bool(race) and p.get("race_id") == race["race_id"],
                })
            live.sort(key=lambda x: x["name"].lower())

            return {
                "version": self.version,
                "room": self.room,
                "me": {"id": me.id, "name": me.name, "color": me.color},
                "peers": live,
                "race": race,
                "my_run": me.run,
                "leaderboard": self.leaderboard(),
                "events": self.events[-14:],
                "show_opponents": me.show_opponents,
                "ready": me.ready,
                "join_urls": self.lan_urls,
                "public_url": self.public_url,
                "local_players": len(self.locals),
                "race_count": len(self.races),
                # Deliberately compact - this rides every snapshot, so full
                # paths are fetched on demand from /api/race instead.
                "races_list": [
                    {"race_id": r["race_id"], "start": r.get("start"),
                     "target": r.get("target"), "created": r.get("created", 0),
                     "lang": r.get("lang", "en"),
                     "finishers": sum(1 for x in r.get("results", {}).values()
                                      if x.get("finished"))}
                    for r in sorted(self.races.values(),
                                    key=lambda x: x.get("created", 0), reverse=True)[:20]
                ],
            }


# --------------------------------------------------------------------------
# UDP gossip layer
# --------------------------------------------------------------------------

class PeerNet:
    def __init__(self, state, extra_peers=None):
        self.state = state
        self.process_id = uuid.uuid4().hex[:12]
        self.on_change = lambda: None
        self.extra_peers = list(extra_peers or [])
        self.seen = {}                    # (peer_id, seq) -> ts, for dedupe
        self.unicast_targets = {}         # peer_id -> (ip, port)
        self.running = True

        self.rx = self._make_rx_socket()
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        try:
            self.tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        except OSError:
            pass

        self.bcast_addrs = self._broadcast_addresses()
        log("broadcasting to", ", ".join(self.bcast_addrs), f"+ multicast {MCAST_GRP}")

    # -- sockets ------------------------------------------------------------

    def _make_rx_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        s.bind(("", DISCOVERY_PORT))
        # Join the multicast group on every local interface we can find, so
        # several copies on one machine (and odd multi-NIC laptops) all hear it.
        for ip in self._local_ips() + ["0.0.0.0"]:
            try:
                mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(ip))
                s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except OSError:
                pass
        s.settimeout(0.5)
        return s

    def _local_ips(self):
        ips = set()
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ips.add(info[4][0])
        except OSError:
            pass
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            ips.add(probe.getsockname()[0])
            probe.close()
        except OSError:
            pass
        return [ip for ip in ips if not ip.startswith("127.")]

    def _broadcast_addresses(self):
        addrs = {"255.255.255.255"}
        for ip in self._local_ips():
            parts = ip.split(".")
            if len(parts) == 4:
                addrs.add(".".join(parts[:3] + ["255"]))   # assume /24, true for home LANs
        return sorted(addrs)

    # -- send ---------------------------------------------------------------

    def send(self, msg, to=None):
        with self.state.lock:
            # Messages about a specific player carry that player's identity;
            # anything else speaks for the process as a whole.
            if "from" not in msg:
                any_player = next(iter(self.state.locals.values()), None)
                msg["from"] = any_player.id if any_player else self.process_id
                msg.setdefault("name", any_player.name if any_player else "host")
            msg.setdefault("room", self.state.room)
            msg.setdefault("seq", self.state.next_seq())
        data = json.dumps(msg, separators=(",", ":")).encode()
        if len(data) > 60000:
            log("dropping oversized message", msg.get("type"))
            return

        if to:
            try:
                self.tx.sendto(data, to)
            except OSError:
                pass
            return

        targets = [(MCAST_GRP, DISCOVERY_PORT)]
        targets += [(a, DISCOVERY_PORT) for a in self.bcast_addrs]
        targets += [(ip, DISCOVERY_PORT) for ip in self.extra_peers]
        # Unicast to peers we already know: survives switches that eat broadcast.
        targets += list(self.unicast_targets.values())
        for t in dict.fromkeys(targets):
            try:
                self.tx.sendto(data, t)
            except OSError:
                pass

    # -- receive ------------------------------------------------------------

    def listen_loop(self):
        while self.running:
            try:
                data, addr = self.rx.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    time.sleep(0.2)
                continue
            try:
                msg = json.loads(data.decode())
            except (ValueError, UnicodeDecodeError):
                continue

            src = msg.get("from")
            # Our own multicast comes straight back to us; ignore anything we
            # said, including messages for every player we host.
            if not src or src == self.process_id:
                continue
            with self.state.lock:
                if any(p.id == src for p in self.state.locals.values()):
                    continue
            # Other groups may be playing on this same network. Without this,
            # their races would drag our players in and vice versa.
            if msg.get("room", "default") != self.state.room:
                continue
            key = (src, msg.get("seq"))
            if key in self.seen:
                continue                                  # same message via a second path
            self.seen[key] = now()
            if len(self.seen) > 4000:
                cutoff = now() - 30
                self.seen = {k: v for k, v in self.seen.items() if v > cutoff}

            self.unicast_targets[src] = (addr[0], DISCOVERY_PORT)
            try:
                self.handle(msg, addr)
            except Exception as e:                        # never let one bad packet kill the loop
                log("error handling", msg.get("type"), e)

    def handle(self, msg, addr):
        st = self.state
        kind = msg.get("type")
        src = msg["from"]
        changed = False

        with st.lock:
            # Only presence messages speak for a player. Digests and sync
            # traffic speak for a process, and seating those as players would
            # invent a phantom peer per machine.
            if kind in ("hello", "state"):
                peer = st.peers.get(src)
                if peer is None:
                    peer = {"id": src, "clicks": 0}
                    st.peers[src] = peer
                    st.add_event(f"{msg.get('name', 'someone')} joined", "join")
                    changed = True
                peer["last_seen"] = now()
                peer["name"] = msg.get("name", peer.get("name", "?"))
                peer["color"] = msg.get("color", peer.get("color", "#888"))
                peer["ip"] = addr[0]
                # A peer between races has no run to report, so its heartbeat
                # simply omits these. Without clearing them first, everyone
                # would keep showing where that player was in the last race.
                if msg.get("race_id") != peer.get("race_id"):
                    for k in ("article", "clicks", "finished", "gave_up", "elapsed",
                              "path", "times", "path_len", "scroll"):
                        peer.pop(k, None)
                for k in ("article", "clicks", "finished", "elapsed", "race_id",
                          "gave_up", "path_len", "ready", "scroll", "path", "times"):
                    if k in msg:
                        peer[k] = msg[k]
                changed = True
                if kind == "hello":
                    self.send_hello(to=(addr[0], DISCOVERY_PORT))

            elif kind == "race_start":
                changed |= self._merge_race(msg["race"], announce=True)
                race = st.races.get(msg["race"]["race_id"])
                if race and self._should_adopt(race):
                    st.active_race_id = race["race_id"]
                    for p in st.locals.values():
                        p.run = None
                        p.ready = False       # readiness is per-race, not sticky
                    st.add_event(
                        f"{msg.get('name')} started a race: {race['start']} -> {race['target']}",
                        "race",
                    )
                    changed = True

            elif kind == "result":
                rid = msg.get("race_id")
                race = st.races.get(rid)
                if race is None and msg.get("race"):
                    self._merge_race(msg["race"])
                    race = st.races.get(rid)
                if race is not None:
                    res = msg["result"]
                    key = norm_name(res.get("name", ""))
                    if key not in race.setdefault("results", {}):
                        race["results"][key] = res
                        verb = "finished" if res.get("finished") else "gave up"
                        detail = ""
                        if res.get("finished"):
                            detail = f" in {res['clicks']} clicks / {res['elapsed']:.1f}s"
                        st.add_event(f"{res.get('name')} {verb}{detail}", "finish")
                        changed = True

            elif kind == "digest":
                if msg.get("digest") != st.history_digest():
                    self.send({"type": "sync_req"}, to=(addr[0], DISCOVERY_PORT))

            elif kind == "sync_req":
                self.send_history(to=(addr[0], DISCOVERY_PORT))

            elif kind == "sync_res":
                for race in msg.get("races", []):
                    changed |= self._merge_race(race)

            if changed:
                st.bump()

        if changed:
            self.on_change()

    def _should_adopt(self, race):
        """Decide whether an announced race becomes ours.

        Nobody gets yanked out of a race they're already running, but if two
        people hit 'New race' at the same moment every peer needs to land on
        the same one - hence the deterministic (created, race_id) tie-break
        rather than simply taking whichever packet arrived last.
        """
        st = self.state
        current = st.active_race()
        if current is None:
            return True
        if current["race_id"] == race["race_id"]:
            return False
        # Nobody sharing this process gets yanked out of a run in progress.
        if any(p.run and not p.run.get("done") and p.run.get("clicks", 0) > 0
               for p in st.locals.values()):
            return False
        return (race.get("created", 0), race["race_id"]) > \
               (current.get("created", 0), current["race_id"])

    def _merge_race(self, incoming, announce=False):
        """Union-merge a race record. First result per player wins, so the
        merge is order-independent and every peer converges."""
        st = self.state
        rid = incoming.get("race_id")
        if not rid:
            return False
        existing = st.races.get(rid)
        if existing is None:
            race = {
                "race_id": rid,
                "start": incoming.get("start"),
                "target": incoming.get("target"),
                "initiator": incoming.get("initiator"),
                "created": incoming.get("created", now()),
                "results": dict(incoming.get("results", {})),
                # Rules default to the permissive classic game, so a race sent
                # by an older peer still behaves sensibly.
                "lang": incoming.get("lang", "en"),
                "show_positions": incoming.get("show_positions", True),
                "allow_back": incoming.get("allow_back", True),
                "time_limit": incoming.get("time_limit", 0),
                "ban_hubs": incoming.get("ban_hubs", False),
                "checkpoint": incoming.get("checkpoint", ""),
                "handicaps": dict(incoming.get("handicaps", {})),
            }
            st.races[rid] = race
            st.trim_races()
            return True
        touched = False
        for key, res in incoming.get("results", {}).items():
            if key not in existing.setdefault("results", {}):
                existing["results"][key] = res
                touched = True
        return touched

    # -- outbound message builders -----------------------------------------

    def send_hello(self, to=None):
        """One presence message per local player."""
        st = self.state
        with st.lock:
            msgs = []
            for p in st.locals.values():
                m = {"type": "hello", "from": p.id, "name": p.name, "color": p.color,
                     "http_port": st.http_port, "race_id": st.active_race_id,
                     "ready": p.ready}
                if p.run:
                    m.update({
                        "article": p.run.get("article"),
                        "clicks": p.run.get("clicks", 0),
                        "finished": p.run.get("finished", False),
                        "gave_up": p.run.get("gave_up", False),
                        "elapsed": p.run.get("elapsed"),
                        "path_len": len(p.run.get("path", [])),
                    })
                msgs.append(m)
        for m in msgs:
            self.send(m, to=to)

    def send_state(self):
        st = self.state
        with st.lock:
            msgs = []
            for p in st.locals.values():
                if not p.run:
                    continue
                run = p.run
                msgs.append({
                    "type": "state", "from": p.id, "name": p.name, "color": p.color,
                    "race_id": st.active_race_id,
                    "article": run.get("article"), "clicks": run.get("clicks", 0),
                    "finished": run.get("finished", False),
                    "gave_up": run.get("gave_up", False),
                    "elapsed": run.get("elapsed"), "path_len": len(run.get("path", [])),
                    "ready": p.ready,
                    # How far down the article they are, 0..1, so spectators can
                    # mirror their view rather than just naming the page.
                    "scroll": run.get("scroll", 0),
                    # Recent trail, so others can narrate the race as it happens.
                    # Trimmed to keep the datagram inside a typical MTU.
                    "path": run.get("path", [])[-LIVE_PATH_STEPS:],
                    "times": run.get("times", [])[-LIVE_PATH_STEPS:],
                })
        for m in msgs:
            self.send(m)

    def send_history(self, to=None):
        with self.state.lock:
            races = list(self.state.races.values())
        # Chunk so a long night of racing still fits in datagrams.
        for i in range(0, len(races), 12):
            self.send({"type": "sync_res", "races": races[i:i + 12]}, to=to)

    # -- periodic -----------------------------------------------------------

    def beacon_loop(self):
        last_digest = 0.0
        while self.running:
            st = self.state
            with st.lock:
                racing = any(p.run and not p.run.get("done") for p in st.locals.values())
            if racing:
                self.send_state()
                time.sleep(RACE_TICK_INTERVAL)
            else:
                self.send_hello()
                time.sleep(HEARTBEAT_INTERVAL)

            if now() - last_digest > DIGEST_INTERVAL:
                last_digest = now()
                with st.lock:
                    digest = st.history_digest()
                self.send({"type": "digest", "digest": digest})
                with st.lock:
                    st.prune_peers()
                    st.prune_locals()      # browsers that closed their tab
                self.on_change()

    def start(self):
        threading.Thread(target=self.listen_loop, daemon=True).start()
        threading.Thread(target=self.beacon_loop, daemon=True).start()
        self.send_hello()
        self.send({"type": "sync_req"})

    def stop(self):
        self.running = False


# --------------------------------------------------------------------------
# Persistence - local only; the network is the real source of truth.
# --------------------------------------------------------------------------

def save_path():
    return os.path.join(HERE, "wikirace_history.json")


def load_history(state):
    try:
        with open(save_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    with state.lock:
        for race in data.get("races", []):
            if race.get("race_id"):
                state.races[race["race_id"]] = race
        state.trim_races()
        state.bump()
    log(f"loaded {len(state.races)} past races")


def save_history(state):
    with state.lock:
        data = {"races": list(state.races.values())}
    tmp = save_path() + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, save_path())
    except OSError as e:
        log("could not save history:", e)


# --------------------------------------------------------------------------
# Local HTTP server: serves the UI and bridges the browser to the peer net.
# --------------------------------------------------------------------------

class Subscriber:
    """One connected browser tab. Hashable by identity, unlike a bare tuple."""

    __slots__ = ("sid", "dirty", "cv")

    def __init__(self, sid):
        self.sid = sid
        self.dirty = False
        self.cv = threading.Condition()

    def wait_for_change(self, timeout):
        """True when something moved, False if we merely timed out."""
        with self.cv:
            if not self.dirty:
                self.cv.wait(timeout=timeout)
            was = self.dirty
            self.dirty = False
            return was

    def poke(self):
        with self.cv:
            self.dirty = True
            self.cv.notify()


class Hub:
    """Fan-out for server-sent events to any browser tabs we have open.

    Each tab renders its own snapshot, because with several people sharing one
    process 'me' differs per connection - so this signals rather than ships.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.subs = set()

    def subscribe(self, sid):
        sub = Subscriber(sid)
        with self.lock:
            self.subs.add(sub)
        return sub

    def unsubscribe(self, sub):
        with self.lock:
            self.subs.discard(sub)

    def publish(self):
        with self.lock:
            subs = list(self.subs)
        for sub in subs:
            sub.poke()


QUIET_ACTIONS = {"/api/scroll"}

GATE_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WikiRace — join</title><style>
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;
background:#0d1117;color:#e6edf3;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.b{background:#141b24;border:1px solid #26303d;border-radius:14px;padding:30px;max-width:340px;width:90%%;text-align:center}
h1{font-size:22px;margin:0 0 6px}p{color:#9aa7b4;font-size:14px;margin:0 0 18px}
input{font:inherit;width:100%%;padding:10px;border-radius:7px;border:1px solid #26303d;
background:#0d1117;color:#e6edf3;text-align:center;letter-spacing:2px;margin-bottom:12px}
input:focus{outline:none;border-color:#58a6ff}
button{font:inherit;width:100%%;padding:10px;border-radius:7px;border:1px solid #2f7ff5;
background:#1f6feb;color:#fff;font-weight:600;cursor:pointer}
.e{color:#f85149;font-size:13px;margin-bottom:10px}
</style></head><body><div class="b">
<div style="font-size:38px">&#127937;</div><h1>WikiRace</h1>
<p>Enter the code you were given.</p>
%(error)s
<form method="get" action="/">
<input name="code" autofocus autocomplete="off" placeholder="code" aria-label="join code">
<button type="submit">Join</button></form>
</div></body></html>"""


def open_tunnel(port, on_url):
    """Give the game a public HTTPS address using ssh, which is already on
    every modern Windows, macOS and Linux box - no account, no install."""
    cmd = ["ssh",
           "-o", "StrictHostKeyChecking=accept-new",
           "-o", "UserKnownHostsFile=" + os.devnull,
           "-o", "ServerAliveInterval=30",
           "-o", "ExitOnForwardFailure=yes",
           "-R", f"80:localhost:{port}", "nokey@localhost.run"]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, text=True, bufsize=1,
            encoding="utf-8", errors="replace")
    except OSError as e:
        log("could not start ssh, so no public link:", e)
        log("install ssh, or forward port %d on your router yourself." % port)
        return None

    def watch():
        pattern = re.compile(r"https://[a-z0-9-]+\.lhr\.life")
        found = False
        for line in proc.stdout:
            m = pattern.search(line)
            if m and not found:
                found = True
                on_url(m.group(0))
        if not found:
            log("the tunnel closed without giving us a link.")
        else:
            log("public link closed.")

    threading.Thread(target=watch, daemon=True).start()
    return proc


def make_handler(state, net, hub):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        # -- who is this request from? -------------------------------------

        def at_console(self):
            """True only for a browser on the machine actually running this.

            The peer address alone can't tell you: an ssh tunnel terminates
            locally, so somebody on the other side of the world also arrives
            from 127.0.0.1. The Host header still says which door they used.
            """
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return False
            host = (self.headers.get("Host") or "").split(":")[0].strip("[]").lower()
            return host in ("localhost", "127.0.0.1", "::1")

        def session_id(self):
            """Identify the browser behind this request.

            A cookie keeps each browser to one seat, and it rides along on
            EventSource too, which cannot send custom headers. An explicit
            ?sid= wins, so two people can share one machine if they want.
            """
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            if q.get("sid"):
                return q["sid"][0][:64]
            for part in (self.headers.get("Cookie") or "").split(";"):
                name, _, value = part.strip().partition("=")
                if name == "wr_sid" and value:
                    return value[:64]
            # No cookie yet (curl, or the very first page load). Everyone
            # unidentified shares one seat rather than spawning new players.
            return "local"

        def new_session_cookie(self):
            if self.session_id() != "local":
                return None
            return uuid.uuid4().hex[:24]

        # -- join code (only when playing over the internet) ----------------

        def code_ok(self):
            if not state.join_code:
                return True
            from urllib.parse import parse_qs, urlparse
            given = (parse_qs(urlparse(self.path).query).get("code") or [""])[0]
            if given == state.join_code:
                return True
            for part in (self.headers.get("Cookie") or "").split(";"):
                name, _, value = part.strip().partition("=")
                if name == "wr_code" and value == state.join_code:
                    return True
            return False

        def send_gate(self, tried):
            err = '<div class="e">That code didn\'t work.</div>' if tried else ""
            body = (GATE_PAGE % {"error": err}).encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")

        # -- plumbing -------------------------------------------------------

        def _cors(self):
            # Wide open on purpose: the front-end may be served from GitHub
            # Pages while the game runs on someone's laptop. There are no
            # credentials to leak - the session id travels in the query string
            # precisely so no cookie has to cross origins.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

        def _send(self, code, body=b"", ctype="application/json", cookies=()):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._cors()
            for name, value in cookies:
                self.send_header(
                    "Set-Cookie",
                    f"{name}={value}; Path=/; Max-Age=86400; SameSite=Lax")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj).encode())

        def _read_json(self):
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode())
            except ValueError:
                return {}

        # -- routes ---------------------------------------------------------

        def do_GET(self):
            path = self.path.split("?")[0]
            if not self.code_ok():
                if path in ("/", "/index.html"):
                    self.send_gate(tried="code=" in self.path)
                else:
                    self._send(403, b"join code required", "text/plain")
                return
            if path in ("/", "/index.html"):
                try:
                    with open(os.path.join(HERE, "ui.html"), "rb") as f:
                        body = f.read()
                except OSError:
                    self._send(500, b"ui.html missing next to wikirace.py", "text/plain")
                    return
                # Hand a fresh browser its own seat at the table, and remember
                # the join code so the link only has to carry it once.
                jar = []
                sid = self.new_session_cookie()
                if sid:
                    jar.append(("wr_sid", sid))
                if state.join_code:
                    jar.append(("wr_code", state.join_code))
                self._send(200, body, "text/html; charset=utf-8", cookies=jar)
            elif path == "/api/state":
                # Seat the player here too - this and the event stream race to
                # be first, and only one of them knowing the origin is enough
                # to hand out the wrong name.
                sid = self.session_id()
                with state.lock:
                    state.player(sid, at_console=self.at_console())
                self._json(state.snapshot(sid))
            elif path == "/api/race":
                # Full record including every path, for replays.
                from urllib.parse import parse_qs, urlparse
                rid = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
                with state.lock:
                    race = state.races.get(rid)
                    self._json(dict(race) if race else {"error": "no such race"})
            elif path == "/api/stream":
                self.stream()
            else:
                self._send(404, b"not found", "text/plain")

        def do_OPTIONS(self):
            # Preflight for cross-origin POSTs from a Pages-hosted front-end.
            self.send_response(204)
            self._cors()
            self.send_header("Content-Length", "0")
            self.send_header("Access-Control-Max-Age", "86400")
            self.end_headers()

        def do_POST(self):
            if not self.code_ok():
                self._send(403, b"join code required", "text/plain")
                return
            path = self.path.split("?")[0]
            body = self._read_json()
            handlers = {
                "/api/name": self.act_name,
                "/api/start_race": self.act_start_race,
                "/api/progress": self.act_progress,
                "/api/finish": self.act_finish,
                "/api/give_up": self.act_give_up,
                "/api/toggle_opponents": self.act_toggle,
                "/api/ready": self.act_ready,
                "/api/scroll": self.act_scroll,
                "/api/reset_scores": self.act_reset,
            }
            fn = handlers.get(path)
            if not fn:
                self._send(404, b"not found", "text/plain")
                return
            sid = self.session_id()
            with state.lock:
                me = state.player(sid, at_console=self.at_console())
            try:
                result = fn(body, me) or {"ok": True}
            except Exception as e:
                log("action error", path, e)
                self._json({"ok": False, "error": str(e)}, 500)
                return
            # Scroll arrives several times a second and only matters to other
            # peers, so it skips the local fan-out that redraws the whole UI.
            if path not in QUIET_ACTIONS:
                hub.publish()
            self._json(result)

        def stream(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            # An HTTP/1.1 body needs explicit framing, and a stream has no
            # length up front - so chunk it, or the browser drops the socket.
            self.send_header("Transfer-Encoding", "chunked")
            self._cors()
            self.end_headers()
            sid = self.session_id()
            sub = hub.subscribe(sid)
            with state.lock:
                me = state.player(sid, at_console=self.at_console())
                me.streams += 1
            try:
                self._emit(state.snapshot(sid))
                while True:
                    changed = sub.wait_for_change(timeout=10.0)
                    with state.lock:
                        p = state.locals.get(sid)
                        if p:
                            p.last_seen = now()
                    if changed:
                        self._emit(state.snapshot(sid))
                    else:
                        self._chunk(b": ping\n\n")          # keep the socket warm
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                hub.unsubscribe(sub)
                with state.lock:
                    p = state.locals.get(sid)
                    if p:
                        p.streams = max(0, p.streams - 1)
                        p.last_seen = now()
                try:
                    self.wfile.write(b"0\r\n\r\n")
                except OSError:
                    pass

        def _chunk(self, data):
            self.wfile.write(b"%x\r\n" % len(data) + data + b"\r\n")
            self.wfile.flush()

        def _emit(self, payload):
            self._chunk(b"data: " + json.dumps(payload).encode() + b"\n\n")

        # -- actions --------------------------------------------------------
        # Every one of these acts on `me`, the player behind this browser.

        def act_name(self, body, me):
            name = (body.get("name") or "").strip()[:24]
            if name:
                with state.lock:
                    me.name = name
                    state.known_names[self.session_id()] = name
                    state.bump()
                net.send_hello()

        def act_start_race(self, body, me):
            start = (body.get("start") or "").strip()
            target = (body.get("target") or "").strip()
            if not start or not target:
                raise ValueError("need both a start and a target article")
            limit = body.get("time_limit")
            race = {
                "race_id": uuid.uuid4().hex[:12],
                "start": start,
                "target": target,
                "initiator": me.name,
                "created": now(),
                "results": {},
                # Rules travel with the race so everyone plays the same game,
                # rather than each client applying its own local preferences.
                "lang": (body.get("lang") or "en").strip()[:12],
                "show_positions": bool(body.get("show_positions", True)),
                "allow_back": bool(body.get("allow_back", True)),
                "time_limit": int(limit) if limit else 0,
                "ban_hubs": bool(body.get("ban_hubs", False)),
                "checkpoint": (body.get("checkpoint") or "").strip(),
                "handicaps": {},
            }
            with state.lock:
                if body.get("handicap"):
                    race["handicaps"] = state.compute_handicaps()
                state.races[race["race_id"]] = race
                state.active_race_id = race["race_id"]
                for p in state.locals.values():
                    p.run = None
                    p.ready = False
                state.add_event(f"{me.name} started a race: {start} -> {target}", "race")
                state.bump()
            net.send({"type": "race_start", "race": race,
                      "from": me.id, "name": me.name, "color": me.color})
            return {"ok": True, "race": race}

        def act_progress(self, body, me):
            """Browser reports where it is; we relay it to the LAN."""
            with state.lock:
                race = state.active_race()
                if not race:
                    return {"ok": False, "error": "no active race"}
                run = me.run
                if run is None or run.get("race_id") != race["race_id"]:
                    run = {"race_id": race["race_id"], "clicks": 0, "path": [],
                           "times": [], "started_at": now(), "finished": False,
                           "gave_up": False, "done": False, "elapsed": None}
                    me.run = run
                run["article"] = body.get("article")
                run["clicks"] = int(body.get("clicks") or 0)
                path = body.get("path")
                if isinstance(path, list):
                    run["path"] = path[-60:]
                # When each step happened, on the same fair clock as `elapsed`.
                # Without this a race can be drawn but never replayed.
                times = body.get("times")
                if isinstance(times, list):
                    run["times"] = [round(float(t or 0), 1) for t in times][-60:]
                run["elapsed"] = float(body.get("elapsed") or 0.0)
                state.bump()
            net.send_state()

        def act_finish(self, body, me):
            return self._record_result(body, me, finished=True)

        def act_give_up(self, body, me):
            return self._record_result(body, me, finished=False)

        def _record_result(self, body, me, finished):
            with state.lock:
                race = state.active_race()
                if not race:
                    return {"ok": False, "error": "no active race"}
                run = me.run or {"clicks": 0, "path": [], "times": [],
                                 "race_id": race["race_id"]}
                run["finished"] = finished
                run["gave_up"] = not finished
                run["done"] = True
                run["elapsed"] = float(body.get("elapsed") or run.get("elapsed") or 0.0)
                run["clicks"] = int(body.get("clicks") or run.get("clicks") or 0)
                if isinstance(body.get("path"), list):
                    run["path"] = body["path"][-60:]
                if isinstance(body.get("times"), list):
                    run["times"] = [round(float(t or 0), 1) for t in body["times"]][-60:]
                me.run = run

                result = {
                    "name": me.name,
                    "peer_id": me.id,
                    "finished": finished,
                    "clicks": run["clicks"],
                    "elapsed": run["elapsed"],
                    "path": run.get("path", []),
                    "times": run.get("times", []),
                    "at": now(),
                }
                race.setdefault("results", {})[norm_name(me.name)] = result
                verb = "finished" if finished else "gave up"
                extra = f" in {result['clicks']} clicks / {result['elapsed']:.1f}s" if finished else ""
                state.add_event(f"{me.name} {verb}{extra}", "finish")
                state.bump()

            net.send({"type": "result", "race_id": race["race_id"],
                      "result": result, "race": race,
                      "from": me.id, "name": me.name})
            net.send_state()
            save_history(state)
            return {"ok": True, "result": result}

        def act_toggle(self, body, me):
            with state.lock:
                me.show_opponents = bool(body.get("value"))
                state.bump()

        def act_scroll(self, body, me):
            try:
                value = float(body.get("value") or 0.0)
            except (TypeError, ValueError):
                return {"ok": False}
            with state.lock:
                if me.run:
                    me.run["scroll"] = min(1.0, max(0.0, value))
            return {"ok": True}

        def act_ready(self, body, me):
            with state.lock:
                me.ready = bool(body.get("value"))
                state.bump()
            net.send_hello()      # tell the lobby straight away, don't wait a tick

        def act_reset(self, body, me):
            """Local wipe only - peers keep their copies unless they wipe too."""
            with state.lock:
                state.races = {rid: r for rid, r in state.races.items()
                               if rid == state.active_race_id}
                state.add_event("Local scoreboard cleared", "info")
                state.bump()
            save_history(state)

    return Handler


# --------------------------------------------------------------------------

def pick_http_port(preferred):
    # Deliberately no SO_REUSEADDR: on Windows it lets you bind a port another
    # process is already serving, so a second instance would silently steal
    # requests from the first instead of moving to the next port.
    # Probe the same address the real server binds. Testing 127.0.0.1 while
    # serving on 0.0.0.0 can pass here and then fail at bind time.
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise SystemExit("no free port for the local UI")


class GameServer(ThreadingHTTPServer):
    # Same reason as above - HTTPServer sets this to 1 by default.
    allow_reuse_address = False
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser(description="WikiRace LAN - serverless multiplayer Wikipedia racing")
    ap.add_argument("--name", default=None, help="your display name")
    ap.add_argument("--port", type=int, default=DEFAULT_HTTP_PORT, help="local UI port")
    ap.add_argument("--room", default="default",
                    help="only play with people using the same room name, "
                         "so separate groups on one network don't collide")
    ap.add_argument("--peer", action="append", default=[],
                    help="manually add a peer IP (repeatable) if broadcast is blocked")
    ap.add_argument("--host", action="store_true",
                    help="host for people who haven't installed anything: they just "
                         "open the printed link in a browser and each becomes a player")
    ap.add_argument("--internet", action="store_true",
                    help="play with people anywhere: opens a public HTTPS link over "
                         "ssh. Implies --host, and adds a join code to the link.")
    ap.add_argument("--code", default=None,
                    help="join code required to enter (auto-generated for --internet)")
    ap.add_argument("--no-code", action="store_true",
                    help="with --internet, let anyone who has the link straight in")
    ap.add_argument("--no-browser", action="store_true", help="don't open a browser window")
    args = ap.parse_args()

    # USERNAME on Windows, USER on Linux/macOS. Without both, everyone on the
    # non-matching platform would fall back to the same name and pool scores.
    account = os.environ.get("USERNAME") or os.environ.get("USER")
    name = args.name or account or socket.gethostname() or "Player"
    name = name.strip()[:24]

    port = pick_http_port(args.port)
    state = GameState(name, port, room=args.room.strip() or "default")

    if args.internet:
        args.host = True
        if args.code:
            state.join_code = args.code.strip()
        elif not args.no_code:
            # A public link that anybody could stumble onto deserves a lock.
            # It rides in the URL, so friends still only get sent one thing.
            state.join_code = "".join(
                random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    elif args.code:
        state.join_code = args.code.strip()

    load_history(state)

    hub = Hub()
    net = PeerNet(state, extra_peers=args.peer)
    net.on_change = hub.publish
    with state.lock:
        state.lan_urls = [f"http://{ip}:{port}/" for ip in net._local_ips()]
    net.start()

    server = GameServer(("0.0.0.0", port), make_handler(state, net, hub))

    url = f"http://localhost:{port}/"
    log(f"you are '{name}' in room '{state.room}'")
    log(f"UI ready at {url}")

    tunnel = None
    if args.internet:
        log("")
        log("  Opening a public link (this takes a few seconds)...")

        def announce(public):
            link = public + ("/?code=" + state.join_code if state.join_code else "/")
            with state.lock:
                state.public_url = link
                state.bump()
            hub.publish()
            log("")
            log("  ==================================================================")
            log("  PLAY OVER THE INTERNET - send this one link to anyone, anywhere:")
            log("")
            log(f"      {link}")
            log("")
            if state.join_code:
                log(f"  (the code {state.join_code} is already in the link)")
            log("  It stays up while this window is open.")
            log("  ==================================================================")
            log("")

        tunnel = open_tunnel(port, announce)

    if args.host and not args.internet:
        log("")
        log("  HOSTING - anyone on this network can just open a browser at:")
        for u in state.lan_urls:
            log(f"      {u}")
        log("  They need nothing installed. Each browser becomes its own player.")
        log("  Friends who ran this script themselves still join the same game.")
        log("  (use --internet instead to play with people outside your network)")
        log("")
    elif not args.host:
        if state.lan_urls:
            log("this machine on the LAN:", ", ".join(net._local_ips()))
        log("waiting for peers... (everyone just runs this script)")
        log("tip: --host shares a link on your network, --internet shares one anywhere")

    if not args.no_browser:
        local = url + ("?code=" + state.join_code if state.join_code else "")
        threading.Timer(0.6, lambda: webbrowser.open(local)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("shutting down")
    finally:
        net.stop()
        if tunnel:
            tunnel.terminate()
        save_history(state)


if __name__ == "__main__":
    main()
