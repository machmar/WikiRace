# WikiRace

Multiplayer Wikipedia racing. Everyone gets the same start and target article;
first one there by clicking links only wins.

On a local network it needs **no server at all**: each player runs the same
script, the copies find each other, and they gossip directly — nobody hosts,
and nobody closing their laptop ends the game. Or run one copy in host mode
and everybody else just opens a browser at it, which is also how you leave it
running on a NAS or home server.

Runs on **Windows, Linux and macOS**.

## Two ways to play

They work at the same time — half your friends can install it and the other
half can just open a link, and everyone is in the same game seeing each other
as equals.

### 1. Everyone installs (no server at all)

Copy this folder to each machine, then:

**Windows** — double-click `Play WikiRace.bat`. It installs Python the first
time if the machine doesn't have it.

**Linux / macOS** — `./play.sh` in a terminal. (If it says permission denied,
run `chmod +x play.sh setup.sh` first.)

The copies find each other over the local network. Nobody hosts, nobody is
special, and one person quitting doesn't end the game.

### 2. One machine hosts, everyone else opens a link

```sh
./play.sh --host
```
```
"Play WikiRace.bat" --host
```

It prints a link like `http://192.168.1.42:8420/`. Everyone else opens that in
a browser — phone, laptop, anything — and each browser becomes its own player.
**They install nothing.** The lobby shows the link with a Copy button so you
can paste it into a group chat.

Type your name in the sidebar, and when everyone shows up hit **Set up a
race**. Everyone gets a 3-2-1 countdown together.

## Running it on a NAS or home server

Host mode is all it takes to leave the game running somewhere permanent, so
it's there whenever people fancy a race rather than only while somebody's
laptop is open.

### TrueNAS SCALE

The image is built by GitHub Actions on every push and published to this
repo's registry, so the NAS only has to pull it — nothing is built there and
you don't need the source on the box at all.

1. Make a dataset for the scoreboard, e.g. `/mnt/tank/apps/wikirace`, and note
   the UID/GID that owns it.
2. Take `docker-compose.yml` from this repo. Set `WIKIRACE_CODE` to something
   only your friends know, point the volume at that dataset, and set `user:`
   to match its owner.
3. **Apps → Discover Apps → Custom App → Install via YAML**, and paste it in.

It pulls `ghcr.io/machmar/wikirace:latest`, built for both x86 and arm.

Then everyone opens `http://your-nas:8420/?code=YOURCODE`. The code is
remembered per browser, so it's asked for once.

It also runs anywhere else Docker does:

```sh
docker compose up -d
```

To take a new version later, `docker compose pull && docker compose up -d`, or
hit **Update** on the TrueNAS app.

**Portainer** takes the same file as a stack, with one caveat: don't add a
`build:` line. Portainer runs builds with nowhere to put a Docker config, so
it fails with `mkdir /.docker: permission denied` — the compose file here has
no `build:` for exactly that reason. If you do want to build rather than pull,
do it on a machine with a shell (`docker build -t wikirace .`) and point the
stack at the tag you get.

The package is public, so the NAS pulls it without logging in to anything —
checked by fetching the manifest anonymously, which is exactly what `docker
pull` does. If you fork this and your copy comes out private, the pull fails
with `denied`; make it public under repo → **Packages** → *wikirace* →
**Package settings** → **Change visibility**, or run `docker login ghcr.io` on
the NAS with a token that can read packages.

Or without Docker at all — it's one script and one HTML file:

```sh
python3 wikirace.py --host --no-browser --no-discovery \
        --code YOURCODE --data-dir /mnt/tank/apps/wikirace
```

### Settings

Everything can come from the environment, which is how a NAS app is
configured — no command line needed:

| | |
|---|---|
| `WIKIRACE_CODE` | required to join. **Set this.** |
| `WIKIRACE_DATA` | where the standings are kept. Mount a volume here. |
| `WIKIRACE_ROOM` | only matters if other copies run on the same network — see [Rooms](#rooms). It does *not* split the people connecting to this server. |
| `WIKIRACE_PORT` | which port to listen on (default 8420) |
| `WIKIRACE_HOST` | `1` — let browsers connect. Already set in the image. |
| `WIKIRACE_NO_BROWSER` | `1` — don't try to open a window on a headless box |
| `WIKIRACE_NO_DISCOVERY` | `1` — skip the LAN peer hunt; a server has no neighbours to find |
| `WIKIRACE_NO_INVITE` | `1` hides the lobby's invite link — the address it guesses is wrong behind a proxy, and people already have the real one |
| `WIKIRACE_NAME` | the name given to whoever opens it on the machine itself |

`GET /healthz` answers without the join code and returns player and race
counts — that's what the container's health check asks, and it's the right
thing to point a monitor at.

### Before you put it on the open internet

- **Set a code, unless something else is asking.** Without one, whoever
  reaches the port is in your game. With one, the game shows a small door and
  answers nothing else. If you're putting it behind a reverse proxy with its
  own login, drop `WIKIRACE_CODE` — two doors to the same room is just two
  things to type.
- **Terminate TLS in front of it.** This speaks plain HTTP, so on a bare port
  the code and everything else travels in the clear. TrueNAS can reverse proxy
  it behind a certificate; do that rather than forwarding 8420 directly.
- **It's a small standard-library HTTP server**, not hardened software. It
  serves exactly two things — the page and its own API — and reads no file
  paths from the request, so there's nothing to traverse. Still: keep it behind
  the reverse proxy, and it runs as UID 1000 in the image rather than root.
- **The standings are written on every finish**, not only at shutdown, so a
  yanked power cord costs at most the race in progress. A clean stop
  (`docker stop`, or the Apps page) flushes the rest.

### Behind a reverse proxy

It needs no special configuration, but two things are worth knowing, because
the whole game runs on a long-lived event stream rather than polling:

- **Buffering must be off for that stream**, or updates arrive in lumps. The
  game sends `X-Accel-Buffering: no`, which nginx — and therefore Nginx Proxy
  Manager, which most NAS boxes use — honours on its own. Traefik, Caddy and
  HAProxy don't buffer responses anyway. Nothing to configure either way.
- **Read timeouts want to be generous.** The stream is deliberately never idle
  for more than about ten seconds, so a default 60-second timeout is fine, but
  if yours is shorter than that players will see it reconnect.

No WebSocket upgrade is needed — it's plain HTTP all the way down.

## Race setup

Whoever opens **Set up race** picks the rules, and they travel with the race —
everyone plays the same game rather than each machine applying its own settings.

| Setting | |
|---|---|
| **Wikipedia edition** | 28 languages. Everyone races on the chosen one. |
| **Start / target article** | Type to search with live suggestions, or roll a pair. |
| **🎲 Random pair** | Well-known, densely-linked articles — winnable races. |
| **🌪️ Obscure** | Genuinely random. Often brutal. |
| **Show where opponents are** | Live positions on or off for everybody. |
| **Allow the Back button** | Off makes it a one-way trip. |
| **Allow find on page** | Off intercepts Ctrl+F, Cmd+F, F3 and Ctrl+G during a race. Honest limitation: a page can block the *shortcut*, not the browser's own Find menu — this discourages the reflex rather than making it impossible. |
| **Ban hub pages** | Blocks *United States*, *World War II* and two dozen other giants. Nearly every lazy route runs through one of them, so this is the setting that stops repeat games feeling identical. |
| **Handicap the leaders** | Whoever's 1st and 2nd in the standings start 10s and 5s late. Their clock runs during the wait. |
| **Who wins** | Fastest time, or fewest clicks. Whichever you don't pick still earns a bonus, so both styles of play are worth something. |
| **Checkpoints** | Up to six articles you must pass through, in any order. They show in a strip above the article and tick off as you reach them; the target won't accept you until they're all done. Enforced by the game itself, not just your browser. |
| **Table of contents** | A contents list beside the article: *Off*, *Main sections only*, *Sections and subsections*, or *Everything*. Genuinely useful for skimming a long page for the link you want — which is exactly why it's off by default and set for the whole race. |
| **Time limit** | None, 2, 5 or 10 minutes. Anyone still going is a DNF. |

**Ready check.** Everyone hits *Mark me ready* in the sidebar; the setup screen
shows who's in. **Start race** unlocks once everyone's ready, and there's a
*Start anyway* underneath for when someone wanders off.

Settings persist between races, so a rematch is one click.

## The clock is fair

The timer stops while an article is loading. What it measures is your thinking,
not your bandwidth — so a slow connection doesn't lose you the race. (Borrowed
from [wikispeedrun.org](https://wikispeedrun.org), which does the same.)

## How it looks

Top right of the bar is a round knob in a three-slot track. Slide it to pick:

| | |
|---|---|
| ☀ | light throughout |
| W | dark game, article done out like Wikipedia |
| ☾ | dark throughout (the default) |

The middle one is worth a try if the dark article is hard on your eyes but you
don't want the rest of the screen going white mid-race.

It's a per-browser choice, remembered on your own machine next to your name.
Nobody else sees your setting, and it isn't part of the race rules.

## Installing Python

There are **no packages to install** — the game is written against the Python
standard library only, deliberately, so there's nothing to pip install and
nothing to keep up to date. The only requirement is Python 3.8+ itself.

The launchers handle that for you, but you can also run it explicitly:

- Windows: `Setup.bat` (uses winget, falls back to a download from python.org)
- Linux/macOS: `./setup.sh` (uses apt, dnf, pacman, zypper, apk or Homebrew)

`setup.sh` always shows you the exact install command and asks before running
anything with `sudo`. Pass `-y` to skip the prompt for unattended installs.

## Rules

- Only links inside the article body count. File, Category, Template, Talk and
  other non-article links are struck through and dead. The list of what counts
  is read from whichever Wikipedia you're playing on, so `Soubor:` and `Datei:`
  are blocked on the Czech and German editions just like `File:` is on English.
- **Back** is free — it doesn't add a click, it just rewinds your trail. The
  host can switch it off.
- Redirects resolve, so *USA* counts as arriving at *United States*.

## Scoring

| | |
|---|---|
| 1st / 2nd / 3rd / 4th | 10 / 7 / 5 / 3 points |
| Anyone else who finishes | 2 points |
| Fewest clicks in the race | +3 bonus (shared on ties) |
| Gave up | 0 |

Standings persist in `wikirace_history.json` and are rebuilt from the shared
race history, so every player's scoreboard agrees without anyone owning it.

**Your name is your scoreboard identity.** Two players using the same name pool
their points — the sidebar warns you if that happens.

Your name is saved in your own browser, not on the host, so restarting the game
doesn't cost anyone their name — each player's browser simply reclaims it on
reconnect.

One wrinkle worth knowing: browsers file that memory under the address you
visit. As long as the game keeps the same address — which it does on a server
that stays put — your name survives restarts. If the address changes, browsers
treat it as a different site and you'll be asked again.

## Seeing each other

While a race runs, the sidebar shows everyone's current article and click count,
updating a few times a second.

**Show where opponents are** is set for the whole race in the setup screen, so
it's the same for everyone. With it off you still see click counts — you know
whether you're winning, just not where anyone is. There's also a personal
toggle in the sidebar, which can only hide more, never reveal what the race
rules hid.

Finished runs reveal the full path everyone took.

## Play-by-play

The sidebar runs a live commentary while the race is on — every move anyone
makes, newest first. When somebody lands on a page that links straight to the
target, it shouts about it:

```
Ada is one click away!
Ada → Colombia
Boris → Brazil
```

Suppressed, like everything else, when the race hides positions.

## After you finish

Finishing opens a hub with four tabs.

**Results** — finishing order with everyone's full route, plus honours: winner,
fewest clicks, scenic route, trailblazer (pages nobody else found), photo finish,
crossed paths. Underneath, the shortest route that actually existed — *"the
shortest route was 2 clicks, e.g. via Colombia. Best anyone managed was 4."*
That's checked exhaustively against every page the start links to, so "no route
in 2 clicks" is a real answer rather than a search that gave up.

**My run** — your trail with the time you reached each page. Click any step to
re-read that article. Good for finding the exact moment you went wrong.

**Watching** — everyone still going: their actual page, scrolled to where they
are on it. **Tiled** shows all at once, **Single** gives one player the full
window. Panels follow live as people click through and scroll. Links are dead so
you can't wander off. Article text never crosses the network — peers broadcast
only *which* page and *how far down*, and your copy fetches it from Wikipedia.

**Replay** — two ways to look at the same race, switchable at the top.

*Timeline* is the race as it happened: one swimlane per player on a scrubber.
Press play and watch it unfold, or scrub to the moment two people were on the
same page at the same time without knowing it. Race the same pair twice and your
previous run appears as a dashed ghost lane.

*Routes* is the shape of the race instead. Every article is one dot, shared by
everyone who saw it, so players taking the same way through run side by side; a
detour is a line that leaves the pack and rejoins it further on; and going back
to a page you'd already visited draws a dashed loop to it. Arrows show which way
each player went, start and target are pinned to either end, and a dot grows
with the number of players who passed through it.

If the race hid opponent positions, watching stays shut until everyone has
finished — otherwise finishing early would be a way to scout for whoever's still
racing next to you.

## Rooms

A room name decides which **copies of the game** pay attention to each other on
a local network. It belongs to a running copy and is chosen when it starts:

```sh
./play.sh --room friday-night
```
```
"Play WikiRace.bat" --room friday-night
```

Copies with the same name find each other and share one game. Copies with
different names ignore each other completely, even on the same wire — which is
the point, in an office or a dorm where two groups would otherwise collide.
Everyone in your group has to pass the same name.

**What it doesn't do** is divide the people connecting to one server. The room
belongs to the process, not to the connection, so everybody who opens the same
address is in the same lobby and the same race whatever it's called, and
there's no `?room=` to ask for a different one.

To run two separate games on one machine, start the game twice on two ports,
each with its own `--room` *and* its own `--data-dir` — otherwise they'd share
a scoreboard.

On a NAS this setting usually does nothing, because there's rarely another
copy on the same network to be confused with. The default is fine.

## Options

```
--name Marek          your display name
--host                let people play from a browser instead of installing
--code ABC123         require this code to join
--room friday-night   only pair up with copies using this same name (LAN only)
--port 8500           which port to listen on
--peer 192.168.1.42   add a peer by hand if broadcast is blocked
--no-invite           hide the lobby's "send them this link" card
--no-browser          don't auto-open a tab (use this on a server)
```

On Windows pass these after the .bat, e.g. `"Play WikiRace.bat" --name Marek`.

## If players can't see each other

- **Allow Python through the firewall** on *Private* networks. On Windows the
  prompt appears the first time you run it; this is the usual cause. It matters
  for hosting too — if the firewall blocks it, nobody can reach your link.
- Everyone must be on the same subnet. Guest Wi-Fi and "client isolation" on
  some routers block peer traffic entirely; a phone hotspot is a good fallback.
- VPNs can capture the traffic — disconnect them.
- Check everyone used the **same `--room`** (or none at all).
- As a last resort, tell each copy about another directly:
  `--peer <someone's IP>`. The IP is printed at startup.

## How it works

- A running copy holds a *set* of local players. Run it yourself and that set
  has one member; host for friends and it has one per connected browser. Each
  is gossiped under its own id, so the two arrangements are indistinguishable
  from the outside — which is why both modes mix freely in one game.
- Browsers are told apart by a cookie, so one person is one player no matter how
  many tabs they open. A dropped connection keeps its seat for 45 seconds, and
  the name comes back with it.
- Discovery and state sync: UDP on port **8421**, sent to multicast
  `239.255.42.99` *and* subnet broadcast, deduplicated on arrival. Known peers
  also get unicast copies, which keeps things working on switches that drop
  broadcast.
- Local UI: a small HTTP server on **8420** serving `ui.html`, pushing updates to
  the browser over server-sent events.
- Wikipedia is fetched straight from your browser via its CORS-enabled API, so
  article loads never bounce through another player's machine.
- Race results merge as a union with first-write-wins per player, so peers
  converge no matter what order packets arrive in — and each one recomputes the
  standings itself rather than trusting anyone else's tally.

## Files

| | |
|---|---|
| `wikirace.py` | the peer: discovery, gossip, scoring, local UI server |
| `ui.html` | the game interface, served straight from disk |
| `Dockerfile`, `docker-compose.yml` | for running it on a NAS or any Docker host |
| `.github/workflows/image.yml` | builds and publishes the image on every push |
| `Play WikiRace.bat` / `play.sh` | launchers (install Python if needed) |
| `Setup.bat` / `setup.sh` | explicit Python setup |
| `wikirace_history.json` | your local copy of past races (created on first finish) |
