# -*- coding: utf-8 -*-
"""Issue #12: every finished race, reachable from the lobby.

The lobby gets a card of the newest few races. "Show older races" opens the
Every race screen: all of them, grouped by evening, with filters. Any race
opens on a page of its own - results, honours, the best route, the replay in
all five views, and everyone's steps side by side - with "Play this again" to
run the same game. Both screens have an address (#races, #race=<id>), so a race
or a filtered list can be sent to someone, and Back works.

Also mends the lobby's Rematch, which never appeared (it looked for results
the snapshot doesn't carry) and, had it appeared, would have used whatever
rules were last set up rather than the last race's.

Three other ways to do this were built as a demo and turned down; see
decisions.md.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Patch:
    def __init__(self, name):
        self.path = os.path.join(ROOT, name)
        self.s = io.open(self.path, encoding="utf-8").read()

    def once(self, old, new, label):
        assert self.s.count(old) == 1, (os.path.basename(self.path), label, self.s.count(old))
        self.s = self.s.replace(old, new)

    def save(self):
        io.open(self.path, "w", encoding="utf-8", newline="").write(self.s)


# ================================================================ server
py = Patch("wikirace.py")

py.once('''def race_checkpoints(race):''', '''def race_summary(race):
    """One line of a list of past races: enough to draw it, nothing more.

    The full record, with every path, is a second fetch from /api/race when
    somebody actually opens it."""
    fin = rank_finishers(race)
    results = (race.get("results") or {}).values()
    return {
        "race_id": race.get("race_id"), "created": race.get("created", 0),
        "kind": race.get("kind"), "lost": bool(race.get("lost")),
        "start": race.get("start"), "target": race.get("target"),
        "mode": race.get("mode", "time"), "lang": race.get("lang", "en"),
        "checkpoints": race.get("checkpoints") or [],
        "players": [r.get("name") for r in results],
        # Names only: enough for a podium and for "you came third".
        "order": [r.get("name") for r in fin],
        "quit": [r.get("name") for r in results if not r.get("finished")],
        "winner": {"name": fin[0].get("name"), "elapsed": fin[0].get("elapsed"),
                   "clicks": fin[0].get("clicks")} if fin else None,
    }


def past_races(races, player="", kind="", find=""):
    """Races somebody has a result in, newest first, narrowed the way the
    Every race screen asks: by who played, which game, and a page that was
    the start, the target or a stop."""
    who, find = norm_name(player), norm_name(find)
    out = []
    for r in races:
        if not r.get("results"):
            continue
        if who and who not in r["results"]:
            continue
        # Races from before modes existed have no kind; work it out the way
        # the browser does for the two that matter here.
        if kind and (r.get("kind") or ("lost" if r.get("lost") else "advanced")) != kind:
            continue
        if find and not any(find in norm_name(t) for t in
                            [r.get("start"), r.get("target")] + list(r.get("checkpoints") or [])):
            continue
        out.append(r)
    out.sort(key=lambda r: r.get("created", 0), reverse=True)
    return out


def race_checkpoints(race):''', "summary helpers")

py.once('''            elif path == "/api/history":''', '''            elif path == "/api/races":
                # Past races for the lobby and the Every race screen. The
                # archive has every race; the working set has the newest, and
                # wins for any race in both, because it may have moved on.
                from urllib.parse import parse_qs, urlparse
                q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                try:
                    limit = max(1, min(500, int(q.get("limit") or 20)))
                except ValueError:
                    limit = 20
                races = {r["race_id"]: r for r in (STORE.everything() if STORE is not None else [])}
                # Summarised under the lock: a live race's results change as
                # people finish.
                with state.lock:
                    races.update(state.races)
                    rows = past_races(races.values(), q.get("player", ""), q.get("kind", ""), q.get("find", ""))
                    page = [race_summary(r) for r in rows[:limit]]
                self._json({"races": page, "total": len(rows)})
            elif path == "/api/history":''', "endpoint")

py.save()


# ================================================================ browser
ui = Patch("ui.html")

# ---------------------------------------------------------------- CSS
ui.once('''  /* ---------- post-race hub ---------- */''', '''  /* ---------- past races: the lobby's list, the Every race screen, a race's page ---------- */

  .past-card { margin-top: var(--s-4); }
  /* A Row you can press: the whole line opens the race. */
  .past-row { cursor: pointer; }
  .past-row:hover .past-pair, .past-row:focus-visible .past-pair { color: var(--accent); }
  .past-row:focus-visible { outline: none; box-shadow: inset 0 0 0 2px var(--accent); border-radius: var(--r-box); }
  .past-main { flex: 1; min-width: 0; }
  .past-pair {
    font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: color var(--m-fast);
  }
  .past-new { color: var(--good); font-size: var(--t-xs); font-weight: 400; }
  .past-meta { font-size: var(--t-xs); color: var(--fg-faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .past-win { text-align: right; font-size: var(--t-sm); flex: none; }
  .past-win .past-time { display: block; font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-dim); }
  .past-none { color: var(--fg-faint); font-size: var(--t-xs); flex: none; }
  .past-day {
    font-size: var(--t-xs); color: var(--fg-dim); font-weight: 600;
    padding: var(--s-4) 0 var(--s-1); border-bottom: 1px solid var(--line-soft);
  }
  .past-day:first-child { padding-top: 0; }
  .past-more { width: 100%; margin-top: var(--s-3); }

  /* The two screens of their own: a bar like the hub's, then a column. */
  #racelist, #racepage { flex: 1; display: flex; flex-direction: column; min-height: 0; }
  #racelist-bar, #racepage-bar {
    display: flex; align-items: center; gap: var(--s-4); padding: var(--s-3) var(--s-5);
    background: var(--bg-2); border-bottom: 1px solid var(--line); flex: none;
  }
  #racelist-body, #racepage-body { flex: 1; overflow-y: auto; }

  .rl-inner { max-width: 860px; margin: 0 auto; padding: var(--s-7) var(--s-7) var(--s-9); }
  .rl-filters { display: flex; gap: var(--s-3); flex-wrap: wrap; align-items: center; margin-bottom: var(--s-6); }
  /* Wide enough for the longest "...'s races"; it is one dropdown, once. */
  .rl-who { width: 15em; }
  /* The search takes whatever the filters leave, but never less than a phrase's worth. */
  .rl-filters input[type=text] { flex: 1; min-width: 12em; width: auto; }
  #rl-list { display: flex; flex-direction: column; gap: var(--s-4); }
  .rl-eh { display: flex; align-items: baseline; gap: var(--s-3); flex-wrap: wrap; margin-bottom: var(--s-1); }
  .rl-day { font-size: var(--t-md); font-weight: 700; }
  .rl-em { font-size: var(--t-xs); color: var(--fg-dim); }
  /* Wide enough for "08:35 PM", so every pairing starts in the same place. */
  .rl-time { font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-faint); flex: none; width: 5.5em; }
  .rl-podium { display: flex; gap: var(--s-3); font-size: var(--t-xs); font-weight: 600; flex: none; }
  /* Wide enough for "you gave up", so the podiums line up down a card. */
  .rl-you { font-size: var(--t-xs); color: var(--fg-dim); flex: none; width: 7em; text-align: right; }
  .rl-you.won { color: var(--gold); font-weight: 600; }
  .rl-empty { text-align: center; padding: var(--s-8) 0; }
  @media (max-width: 760px) {
    .rl-podium span:not(:first-child), .rl-time { display: none; }
  }

  /* A race's page borrows the hub's results and replay, so it only has to
     close the gaps between them. */
  #racepage-body #results-pane { padding-bottom: 0; }
  #racepage-body #replay-pane { padding-top: 0; padding-bottom: 0; }
  #racepage-steps { max-width: 860px; margin: 0 auto; padding: var(--s-7) var(--s-7) var(--s-9); }
  .rpg-steps-card { overflow-x: auto; padding: 0; }
  table.rpg-steps { border-collapse: collapse; font-size: var(--t-xs); width: 100%; }
  .rpg-steps th {
    text-align: left; padding: var(--s-3) var(--s-4); font-size: var(--t-sm); white-space: nowrap;
    border-bottom: 2px solid; /* a border width: the player's colour, underlining their name */
  }
  .rpg-steps td { padding: var(--s-1) var(--s-4); border-bottom: 1px solid var(--line-soft); white-space: nowrap; color: var(--fg-dim); }
  .rpg-steps tr:last-child td { border-bottom: none; }
  .rpg-steps td.n { color: var(--fg-faint); font-family: var(--mono); }
  .rpg-steps td.met { color: var(--fg); font-weight: 600; background: var(--hover); }
  .rpg-steps td.tgt { color: var(--good-fg); font-weight: 600; }

  /* ---------- post-race hub ---------- */''', "css")

# ---------------------------------------------------------------- markup
ui.once('''        <div class="card lobby-card" id="share-card" style="margin-top:var(--s-4)" hidden>''',
        '''        <div id="past-slot"></div>

        <div class="card lobby-card" id="share-card" style="margin-top:var(--s-4)" hidden>''', "lobby list")

ui.once('''    <div id="toast"></div>''', '''    <!-- ---------- every finished race ---------- -->
    <div id="racelist" hidden>
      <div id="racelist-bar">
        <button id="rl-back" class="ghost">‹ Lobby</button>
        <span class="tiny muted">Every race played on this server</span>
      </div>
      <div id="racelist-body">
        <div class="rl-inner">
          <h2 class="hub-h2">Every race</h2>
          <p class="hub-sub" id="rl-sub"></p>
          <div class="rl-filters">
            <div class="seg" id="rl-kind">
              <button data-k="" class="on">Every game</button><button data-k="classic">Classic</button><button data-k="advanced">Advanced</button><button data-k="lost">Lost</button>
            </div>
            <div class="rl-who" id="rl-who"></div>
            <input type="text" id="rl-find" autocomplete="off" placeholder="Find a page: a start, a target or a stop">
          </div>
          <div id="rl-list"></div>
        </div>
      </div>
    </div>

    <!-- ---------- one finished race, on a page of its own ---------- -->
    <div id="racepage" hidden>
      <div id="racepage-bar">
        <button id="racepage-back" class="ghost">‹ Lobby</button>
        <span id="racepage-note" class="tiny muted"></span>
        <span class="hstack" style="margin-left:auto">
          <button id="racepage-link">Copy link</button>
          <button id="racepage-again" class="primary">Play this again</button>
        </span>
      </div>
      <div id="racepage-body">
        <div id="racepage-results"></div>
        <div id="racepage-replay"></div>
        <div id="racepage-steps"></div>
      </div>
    </div>

    <div id="toast"></div>''', "screens")

# ---------------------------------------------------------------- stage
ui.once('''  $("hub").hidden = mode !== "hub";
  spec.on = mode === "hub" && hubTab === "watch";''', '''  $("hub").hidden = mode !== "hub";
  $("racelist").hidden = mode !== "racelist";
  $("racepage").hidden = mode !== "racepage";
  // The results and replay a race's page borrowed go home when it closes,
  // and the address stops pointing at a screen that is no longer up.
  if (mode !== "racepage") restorePanes();
  if (mode !== "racelist" && mode !== "racepage") {
    past.race = null;
    past.from = null;
    if (/^#race/.test(location.hash)) history.replaceState(null, "", location.pathname + location.search);
  }
  spec.on = mode === "hub" && hubTab === "watch";''', "setStage")

ui.once('''  if (!snap.race && stageMode !== "lobby") setStage("lobby");''',
        '''  if (!snap.race && !["lobby", "racelist", "racepage"].includes(stageMode)) setStage("lobby");''', "fallback")

ui.once('''    if (spec.on) closeSpectate();          // a new race pulls you back to playing
    enterRace(snap.race, snap.my_run);
  }''', '''    if (spec.on) closeSpectate();          // a new race pulls you back to playing
    enterRace(snap.race, snap.my_run).then(routePending);
  } else if (!snap.race) {
    routePending();
  }''', "arrival")

ui.once('''  } else {
    setText($("lobby-last"), "");
  }
}''', '''  } else {
    setText($("lobby-last"), "");
  }
  renderPast(snap);
}''', "renderLobby")

# The snapshot's list is compact: a count of finishers, not the results.
ui.once('''  const done = snap.races_list.filter(r => Object.keys(r.results || {}).length);''',
        '''  const done = snap.races_list.filter(r => r.finishers);''', "lastFinishedRace")

ui.once('''$("lobby-rematch").onclick = async () => {
  const last = lastFinishedRace(S.snap);
  if (!last) return;
  cfg.lang = last.lang || cfg.lang;
  // A lost rematch gets lost somewhere new.
  const starts = last.lost ? await lostStarts(cfg.lang, last.target, cfg.checkpoints, cfg.ban_hubs) : [];
  if (last.lost && starts.length < 2) { toast("Couldn't reach Wikipedia"); return; }
  await post("/start_race", {
    start: last.start, target: last.target, lang: cfg.lang, lost: !!last.lost, starts,
    kind: last.kind || (last.lost ? "lost" : undefined),
    show_positions: cfg.show_positions, allow_back: cfg.allow_back,
    allow_find: cfg.allow_find, allow_peek: cfg.allow_peek,
    time_limit: cfg.time_limit, ban_hubs: cfg.ban_hubs, allow_tables: cfg.allow_tables,
    handicap: cfg.handicap, checkpoints: cfg.checkpoints, checkpoint_slots: cfg.checkpoint_slots,
    mode: cfg.mode,
    toc: cfg.toc,
  });
};''', '''/* One click, and the same game again - its rules, not whatever was set up last. */
$("lobby-rematch").onclick = async () => {
  const row = lastFinishedRace(S.snap);
  const last = row && await fetchRace(row.race_id);
  if (!last) { toast("Couldn't load the last race — try again"); return; }
  const rules = rulesOf(last);
  // A lost rematch gets lost somewhere new.
  const starts = last.lost ? await lostStarts(rules.lang, last.target, rules.checkpoints, rules.ban_hubs) : [];
  if (last.lost && starts.length < 2) { toast("Couldn't reach Wikipedia"); return; }
  await post("/start_race", Object.assign(rules, {
    start: last.start, target: last.target, lost: !!last.lost, starts, kind: kindOf(last),
  }));
};''', "rematch")

ui.once('''/* ------------------------------------------------------------------ *
 * Lobby
 * ------------------------------------------------------------------ */''', r'''/* ------------------------------------------------------------------ *
 * Past races: the lobby's list, the Every race screen, and a race's own
 * page. Both screens have an address - #races, with any filters after a
 * "?", and #race=<id> - so either can be sent to someone, and Back works.
 * ------------------------------------------------------------------ */

const LOBBY_PAST = 8;        // races the lobby shows before "Show older races"
const RACE_LIST_MAX = 500;   // the most the Every race screen loads at once
const past = {
  list: [], total: 0, sig: "",   // the lobby's newest few
  race: null,                    // the race on its own page
  from: null,                    // the list that page was opened from, to go back to
  // A link to one of the screens, held until the game has said whether
  // there is a race to drop you into first.
  pending: /^#race/.test(location.hash) ? location.hash : null,
};
const raceList = { key: null, list: [], total: 0, scroll: 0, kind: "", player: "", find: "", timer: null };

async function fetchRaces(params) { return (await fetch(apiUrlFor("/races", params))).json(); }
async function fetchRace(id) {
  try {
    const r = await (await fetch(apiUrlFor("/race", { id }))).json();
    return r && r.race_id ? r : null;
  } catch (e) { return null; }
}

/* ---- when: the time on a row, the phrase on a page, the evening a race belongs to ---- */

function daysAgo(t, shift) {
  const then = new Date((t - shift) * 1000), now = new Date(Date.now() - shift * 1000);
  return Math.round((new Date(now.toDateString()) - new Date(then.toDateString())) / 864e5);
}
const clockOf = t => new Date(t * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
function whenPlayed(t) {
  const n = daysAgo(t, 0);
  if (n === 0) return clockOf(t);
  if (n === 1) return "yesterday " + clockOf(t);
  return new Date(t * 1000).toLocaleDateString([], { weekday: "short" }) + " " + clockOf(t);
}
function playedPhrase(t) {
  const n = daysAgo(t, 0);
  if (n === 0) return "today at " + clockOf(t);
  if (n === 1) return "yesterday at " + clockOf(t);
  return "on " + new Date(t * 1000).toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" }) +
         " at " + clockOf(t);
}
/* A session that runs past midnight still belongs to the evening it began. */
function eveningOf(t) {
  const n = daysAgo(t, 6 * 3600);
  if (n === 0) return "Today";
  if (n === 1) return "Yesterday";
  return new Date(t * 1000).toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" });
}

function byEvening(list) {
  const groups = [];
  for (const s of list) {
    const day = eveningOf(s.created);
    if (!groups.length || groups[groups.length - 1].day !== day) groups.push({ day, races: [] });
    groups[groups.length - 1].races.push(s);
  }
  return groups;
}

const pairText = s => esc(startLabel(s)) + " → " + esc(s.target);

function raceMeta(s) {
  const bits = [raceKind(s), raceMode(s) === "clicks" ? "fewest clicks" : "fastest time"];
  if (raceCheckpoints(s).length) bits.push("via " + raceCheckpoints(s).join(", "));
  bits.push(s.players.length + (s.players.length === 1 ? " player" : " players"));
  return bits;
}

/* A whole Row opens its race, by pointer or by keyboard. */
function onRowPick(host, pick) {
  host.addEventListener("click", e => {
    const r = e.target.closest(".past-row");
    if (r) pick(r.dataset.race);
  });
  host.addEventListener("keydown", e => {
    const r = e.target.closest(".past-row");
    if (r && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pick(r.dataset.race); }
  });
}

/* ---- the lobby's list ---- */

function renderPast(snap) {
  // Only worth asking again when a race has been added or someone finished.
  const top = (snap.races_list || [])[0] || {};
  const sig = (snap.race_count || 0) + ":" + top.race_id + ":" + top.finishers;
  if (sig === past.sig) return;
  past.sig = sig;
  fetchRaces({ limit: LOBBY_PAST }).then(d => {
    past.list = d.races;
    past.total = d.total;
    drawPast();
  }).catch(() => { past.sig = ""; });
}

function lobbyRow(s) {
  const live = S.snap && S.snap.race && S.snap.race.race_id === s.race_id;
  const w = s.winner;
  return '<div class="row in-card past-row" role="button" tabindex="0" data-race="' + s.race_id + '">' +
    '<div class="past-main"><div class="past-pair">' + pairText(s) +
    (live ? ' <span class="past-new">· just now</span>' : "") + "</div>" +
    '<div class="past-meta">' + esc(raceMeta(s).concat(whenPlayed(s.created)).join(" · ")) + "</div></div>" +
    (w ? '<div class="past-win"><span style="color:' + colorFor(w.name) + ';font-weight:600">🥇 ' + esc(w.name) + "</span>" +
         '<span class="past-time">' + (raceMode(s) === "clicks" ? w.clicks + " clicks" : fmtTime(w.elapsed)) + "</span></div>"
       : '<div class="past-none">nobody finished</div>') + "</div>";
}

function drawPast() {
  const slot = $("past-slot");
  if (!past.list.length) { slot.innerHTML = ""; return; }
  let rows = "", day = null;
  for (const s of past.list) {
    const d = eveningOf(s.created);
    if (d !== day) { rows += '<div class="past-day">' + esc(d) + "</div>"; day = d; }
    rows += lobbyRow(s);
  }
  slot.innerHTML = '<div class="card lobby-card past-card"><h3>Earlier races <span class="muted">(' + past.total + ")</span></h3>" +
    rows + (past.total > past.list.length ? '<button class="ghost past-more" id="past-more">Show older races</button>' : "") +
    "</div>";
  if ($("past-more")) $("past-more").onclick = () => { raceList.scroll = 0; location.hash = "races"; };
}

onRowPick($("past-slot"), id => { past.from = null; location.hash = "race=" + id; });

/* ---- getting to a screen from its address ---- */

function routeFromHash() {
  const race = /^#race=([0-9a-f]+)/.exec(location.hash);
  if (race) { openRacePage(race[1]); return true; }
  if (/^#races/.test(location.hash)) { openRaceList(new URLSearchParams(location.hash.split("?")[1] || "")); return true; }
  return false;
}

/* Opening a link to one of the screens waits for the game first: if a race is
   on and you are in it, the race wins and the link is dropped. */
function routePending() {
  const want = past.pending;
  past.pending = null;
  if (!want || S.running) return;
  if (location.hash !== want) history.replaceState(null, "", location.pathname + location.search + want);
  routeFromHash();
}

window.addEventListener("hashchange", () => {
  if (S.running) return;
  if (!routeFromHash() && (stageMode === "racelist" || stageMode === "racepage")) setStage("lobby");
});

/* Back to the lobby as a step of its own, so the browser's Back returns here. */
function toLobby() {
  history.pushState(null, "", location.pathname + location.search);
  setStage("lobby");
}

/* ---- the Every race screen ---- */

/* The filters live in the address, so a filtered list is a link too. */
function raceListHash() {
  const p = new URLSearchParams();
  if (raceList.kind) p.set("kind", raceList.kind);
  if (raceList.player) p.set("player", raceList.player);
  if (raceList.find) p.set("find", raceList.find);
  const qs = p.toString();
  return "races" + (qs ? "?" + qs : "");
}

async function openRaceList(params) {
  raceList.kind = params.get("kind") || "";
  raceList.player = params.get("player") || "";
  raceList.find = params.get("find") || "";
  const arriving = stageMode !== "racelist";
  setStage("racelist");
  if (arriving) buildRaceListFilters();
  if (raceListHash() !== raceList.key) await loadRaceList();
  else drawRaceList();
  if (arriving) $("racelist-body").scrollTop = raceList.scroll;
}

function buildRaceListFilters() {
  $("rl-kind").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.k === raceList.kind));
  $("rl-find").value = raceList.find;
  const me = S.snap && S.snap.me ? S.snap.me.name : "";
  const names = [...new Set(((S.snap && S.snap.leaderboard) || []).map(e => e.name))].filter(n => norm(n) !== norm(me));
  const options = [["", "Anyone"], [me, "Races I was in"]].concat(names.map(n => [n, n + "'s races"]));
  // Someone in the address who has since left the standings still filters.
  if (raceList.player && !options.some(o => norm(o[0]) === norm(raceList.player)))
    options.push([raceList.player, raceList.player + "'s races"]);
  makeDropdown($("rl-who"), options, raceList.player, v => { raceList.player = v; refilterRaceList(); });
}

function refilterRaceList() {
  history.replaceState(null, "", location.pathname + location.search + "#" + raceListHash());
  $("racelist-body").scrollTop = 0;
  loadRaceList();
}

async function loadRaceList() {
  const key = raceListHash();
  const q = { limit: RACE_LIST_MAX };
  if (raceList.kind) q.kind = raceList.kind;
  if (raceList.player) q.player = raceList.player;
  if (raceList.find) q.find = raceList.find;
  try {
    const d = await fetchRaces(q);
    if (key !== raceListHash()) return;        // the filters moved on while this loaded
    raceList.list = d.races;
    raceList.total = d.total;
    raceList.key = key;
  } catch (e) { toast("Couldn't load the races — try again"); return; }
  drawRaceList();
}

function raceListRow(s, me) {
  const medals = ["🥇", "🥈", "🥉"];
  const podium = (s.order || []).slice(0, 3).map((n, i) =>
    '<span style="color:' + colorFor(n) + '">' + medals[i] + " " + esc(n) + "</span>").join("");
  const place = me ? (s.order || []).findIndex(n => norm(n) === norm(me)) : -1;
  const quit = !!me && (s.quit || []).some(n => norm(n) === norm(me));
  const you = place === 0 ? "you won" : place > 0 ? "you came " + ordinal(place + 1) : quit ? "you gave up" : "";
  return '<div class="row in-card past-row" role="button" tabindex="0" data-race="' + s.race_id + '">' +
    '<span class="rl-time">' + clockOf(s.created) + "</span>" +
    '<div class="past-main"><div class="past-pair">' + pairText(s) + "</div>" +
    '<div class="past-meta">' + esc(raceMeta(s).join(" · ")) + "</div></div>" +
    '<div class="rl-podium">' + (podium || '<span class="past-none">nobody finished</span>') + "</div>" +
    '<span class="rl-you' + (place === 0 ? " won" : "") + '">' + you + "</span></div>";
}

function drawRaceList() {
  const me = S.snap && S.snap.me ? S.snap.me.name : "";
  const groups = byEvening(raceList.list);
  const filtered = raceList.kind || raceList.player || raceList.find;
  const n = raceList.total;
  const evenings = groups.length + (groups.length === 1 ? " evening" : " evenings");
  let sub = !n ? "" : filtered ? (n === 1 ? "1 race matches" : n + " races match") + ", from " + evenings
                               : (n === 1 ? "1 race" : n + " races") + " over " + evenings + ", newest first";
  if (n > raceList.list.length) sub += " — showing the newest " + raceList.list.length;
  setText($("rl-sub"), sub);
  if (!raceList.list.length) {
    $("rl-list").innerHTML = '<div class="empty rl-empty">' +
      (filtered ? "No races like that. Try fewer filters." : "No races yet. They appear here once people finish.") + "</div>";
    return;
  }
  $("rl-list").innerHTML = groups.map(g => {
    const wins = new Map();
    g.races.forEach(s => s.winner && wins.set(s.winner.name, (wins.get(s.winner.name) || 0) + 1));
    const top = [...wins.entries()].sort((a, b) => b[1] - a[1])[0];
    const times = g.races.map(s => s.created);
    const bits = [g.races.length + (g.races.length === 1 ? " race" : " races")];
    bits.push(g.races.length > 1 ? clockOf(Math.min(...times)) + "–" + clockOf(Math.max(...times)) : clockOf(times[0]));
    if (top && top[1] > 1) bits.push(top[0] + " won " + top[1]);
    return '<div class="card rl-evening"><div class="rl-eh"><span class="rl-day">' + esc(g.day) + "</span>" +
      '<span class="rl-em">' + esc(bits.join(" · ")) + "</span></div>" +
      g.races.map(s => raceListRow(s, me)).join("") + "</div>";
  }).join("");
}

onRowPick($("rl-list"), id => {
  raceList.scroll = $("racelist-body").scrollTop;
  past.from = "#" + raceListHash();
  location.hash = "race=" + id;
});
$("rl-back").onclick = toLobby;
$("rl-kind").onclick = e => {
  const b = e.target.closest("button[data-k]");
  if (!b || b.dataset.k === raceList.kind) return;
  raceList.kind = b.dataset.k;
  $("rl-kind").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
  refilterRaceList();
};
$("rl-find").oninput = () => {
  clearTimeout(raceList.timer);
  raceList.timer = setTimeout(() => { raceList.find = $("rl-find").value.trim(); refilterRaceList(); }, 250);
};

/* ---- a race's own page ---- */

/* The page borrows the hub's results and replay rather than drawing its own:
   they are built around fixed ids, and one copy of each keeps them honest.
   Leaving the page sends them home (setStage). */
function restorePanes() {
  const homeR = document.querySelector('.hub-pane[data-pane="results"]');
  const homeP = document.querySelector('.hub-pane[data-pane="replay"]');
  if ($("results-pane").parentNode !== homeR) homeR.appendChild($("results-pane"));
  if ($("replay-pane").parentNode !== homeP) homeP.appendChild($("replay-pane"));
}

async function openRacePage(id) {
  if (stageMode === "racepage" && past.race && past.race.race_id === id) return;
  const race = await fetchRace(id);
  if (location.hash !== "#race=" + id) return;  // moved on while it loaded
  if (!race) {
    toast("That race isn't on this server");
    history.replaceState(null, "", location.pathname + location.search);
    setStage("lobby");
    return;
  }
  const from = past.from;
  setStage("racepage");
  past.race = race;
  past.from = from;
  $("racepage-results").appendChild($("results-pane"));
  $("racepage-replay").appendChild($("replay-pane"));
  const view = Object.assign({}, S.snap, { race });
  renderResults(view);
  renderReplay(view);
  drawSteps(race);
  setText($("racepage-note"), "Played " + playedPhrase(race.created) + (race.initiator ? ", set up by " + race.initiator : ""));
  setText($("racepage-back"), from ? "‹ Every race" : "‹ Lobby");
  $("racepage-body").scrollTop = 0;
}

/* Everyone's route side by side, a click to a row, so who met whom is
   something you can see down a column. A shared start isn't a meeting. */
function drawSteps(race) {
  const fin = rankFinishers(race);
  const runs = fin.concat(Object.values(race.results || {}).filter(r => !fin.includes(r)));
  const colors = raceColors(race);
  const seen = new Map();
  runs.forEach(r => (r.path || []).forEach((p, i) => {
    if (i === 0 && !race.lost) return;
    if (!seen.has(norm(p))) seen.set(norm(p), new Set());
    seen.get(norm(p)).add(r.name);
  }));
  const rows = Math.max(0, ...runs.map(r => (r.path || []).length));
  let html = '<div class="hub-sec"><h4>Everyone\'s steps <span class="muted">— bold pages were visited by more than one player</span></h4>' +
    '<div class="card rpg-steps-card"><table class="rpg-steps"><thead><tr><th></th>' +
    runs.map(r => { const c = ink(colors.get(r.name)); return '<th style="color:' + c + ";border-color:" + c + '">' + esc(r.name) + "</th>"; }).join("") +
    "</tr></thead><tbody>";
  for (let i = 0; i < rows; i++) {
    html += '<tr><td class="n">' + (i ? i : "start") + "</td>" + runs.map(r => {
      const path = r.path || [], p = path[i];
      if (!p) return i === path.length && !r.finished ? '<td class="n">gave up</td>' : "<td></td>";
      const others = i === 0 && !race.lost ? [] : [...(seen.get(norm(p)) || [])].filter(n => n !== r.name);
      const cls = norm(p) === norm(race.target) ? "tgt" : others.length ? "met" : "";
      return '<td class="' + cls + '"' + (others.length ? ' title="Also here: ' + esc(others.join(", ")) + '"' : "") + ">" + esc(p) + "</td>";
    }).join("") + "</tr>";
  }
  $("racepage-steps").innerHTML = html + "</tbody></table></div></div>";
}

$("racepage-back").onclick = () => { if (past.from) location.hash = past.from.slice(1); else toLobby(); };
$("racepage-again").onclick = () => playAgain(past.race);
$("racepage-link").onclick = async () => {
  try {
    await navigator.clipboard.writeText(location.href);
    toast("Link copied — anyone in the game can open this race");
  } catch (e) { toast("Couldn't copy — the link is in the address bar"); }
};

/* ---- the same game again ---- */

/* The rules a race was played under, in the shape race setup keeps them. */
function rulesOf(race) {
  return {
    lang: race.lang || "en", mode: raceMode(race),
    checkpoints: raceCheckpoints(race).slice(), checkpoint_slots: raceSlots(race).slice(),
    show_positions: race.show_positions !== false, allow_back: race.allow_back !== false,
    allow_find: race.allow_find !== false, allow_peek: race.allow_peek !== false,
    ban_hubs: !!race.ban_hubs, allow_tables: allowTables(race),
    time_limit: race.time_limit || 0, toc: raceToc(race),
    handicap: !!Object.keys(race.handicaps || {}).length,
  };
}
const kindOf = race => (MODES.find(m => m.name === raceKind(race)) || MODES[0]).id;

/* Race setup, filled in from an old race and left open to change. A lost race
   keeps its target; its starts belonged to the people who had them. */
async function playAgain(race) {
  if (!race) return;
  Object.assign(cfg, rulesOf(race));
  document.querySelectorAll(".overlay").forEach(o => o.remove());
  openConfigurator(kindOf(race));
  if ($("c-start") && !race.lost) $("c-start").value = race.start || "";
  if ($("c-target")) $("c-target").value = race.target || "";
  toast(race.lost ? "Same target — everyone gets a new place to start"
                  : "Same race, same rules — change anything you like", 3200);
}

/* ------------------------------------------------------------------ *
 * Lobby
 * ------------------------------------------------------------------ */''', "past races block")

ui.save()


# ================================================================ the standard
md = Patch("docs/DesignLanguage.md")
md.once('''A **Row inside a Card** drops its own box''', '''**A Row you can press** — a finished race in the lobby or on the Every race
screen — is the whole line, not a button tucked into it: the line is what you
are choosing. It keeps the Row's shape, takes a pointer, colours its name with
the accent on hover and focus, and has the focus ring a Control has. It is a
Row that does something, not an eighth piece.

A **Row inside a Card** drops its own box''', "pressable row")
md.save()

page = Patch("docs/design-language.html")
page.once('''  .row.in-card .nm { font-weight: 600; }''', '''  .row.in-card .nm { font-weight: 600; }
  /* A Row you can press: the whole line is the choice. */
  .row.press { cursor: pointer; }
  .row.press:hover .nm, .row.press:focus-visible .nm { color: var(--accent); }
  .row.press:focus-visible { outline: none; box-shadow: inset 0 0 0 2px var(--accent); border-radius: var(--r-box); }''',
           "pressable row style")
page.once('''      <div class="row in-card"><span class="nm">Kimmy</span><span class="num">not ready</span></div>
    </div>
  </div>''', '''      <div class="row in-card"><span class="nm">Kimmy</span><span class="num">not ready</span></div>
    </div>
    <div class="card" style="max-width: 420px; margin-top: var(--s-6)">
      <h4>Earlier races (32)</h4>
      <div class="row in-card press" role="button" tabindex="0"><span class="nm">Chess &rarr; Neutron star</span><span class="num">Kody</span></div>
      <div class="row in-card press" role="button" tabindex="0"><span class="nm">Prague &rarr; Apollo 11</span><span class="num">BuraG</span></div>
    </div>
  </div>''', "pressable row demo")
page.once('''<li>Every list in a card in the game was already drawn this way.</li></ul></div>''',
           '''<li>Every list in a card in the game was already drawn this way.</li><li>A Row you can press is the whole line, with the accent on its name for hover and focus and a Control's focus ring. Still a Row, not an eighth piece.</li></ul></div>''',
           "pressable row rule")
page.save()

print("past races added")
