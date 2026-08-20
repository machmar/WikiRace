# WikiRace

Multiplayer Wikipedia racing. Everyone gets the same start and target article;
first one there by clicking links only wins.

Play on your own network, or with anyone anywhere.

On a local network it needs **no server at all**: each player runs the same
script, the copies find each other, and they gossip directly — nobody hosts,
and nobody closing their laptop ends the game. To play with people further
away, one person hosts and everybody else just opens a link.

Runs on **Windows, Linux and macOS**.

## Three ways to play

Pick whichever suits the room. **They work at the same time** — half your
friends can install it, the other half can just open a link, and everyone is in
the same game seeing each other as equals.

### 1. Everyone installs (fully serverless)

Copy this folder to each machine, then:

**Windows** — double-click `Play WikiRace.bat`. It installs Python the first
time if the machine doesn't have it.

**Linux / macOS** — `./play.sh` in a terminal. (If it says permission denied,
run `chmod +x play.sh setup.sh` first.)

Nobody hosts, nobody is special, and one person quitting doesn't end the game.

### 2. You host, everyone else just opens a link

One machine runs it with `--host`:

```sh
./play.sh --host
```
```
"Play WikiRace.bat" --host
```

It prints a link like `http://192.168.1.42:8420/`. Everyone else opens that in a
browser — phone, laptop, anything — and each browser becomes its own player.
**They install nothing.** The lobby shows the link with a Copy button so you can
paste it into a group chat.

The trade-off: if the host closes the app, the browser-only players drop out.
Anyone running their own copy keeps playing regardless.

### 3. Play with people anywhere in the world

One machine runs it with `--internet`:

```sh
./play.sh --internet
```
```
"Play WikiRace.bat" --internet
```

After a few seconds it prints something like:

```
  PLAY OVER THE INTERNET - send this one link to anyone, anywhere:

      https://ba43815099273f.lhr.life/?code=R76PYJ
```

Send that link to anyone. They open it in a browser and they're in — no
install, no account, nothing to configure. The join code is already in the
link, so a stranger who stumbles onto the bare address can't wander in.

Under the hood it forwards your game through `ssh`, which Windows, macOS and
Linux all ship with. Nothing to install, no port forwarding, no router
settings. **The link lives only as long as that window stays open**, and you
get a fresh one each session.

Whichever way you play, type your name in the sidebar, and when everyone shows
up hit **Set up a race**. Everyone gets a 3-2-1 countdown together.

## A permanent home on GitHub Pages

The interface is a single static file (`docs/index.html`), so GitHub can host
it for free at a URL that never changes — handy when the game address is
different every session.

1. Push this repo to GitHub.
2. **Settings → Pages → Source: Deploy from a branch**, branch `main`,
   folder **`/docs`**. Save.
3. A minute later it's live at `https://YOU.github.io/REPO/`.

Friends bookmark that page. When you start a game, they open it and paste the
link you sent — or you can skip the pasting entirely:

```sh
./play.sh --internet --pages https://YOU.github.io/REPO/
```

Now the link it prints goes *through* your page, with the game address already
filled in. One click and they're playing.

The page is also where people can grab the download to host games themselves.

*What Pages can't do:* it only serves files, so it can't run the game. Somebody
still has to be hosting for there to be a game to join.

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
| **Ban hub pages** | Blocks *United States*, *World War II* and two dozen other giants. Nearly every lazy route runs through one of them, so this is the setting that stops repeat games feeling identical. |
| **Handicap the leaders** | Whoever's 1st and 2nd in the standings start 10s and 5s late. Their clock runs during the wait. |
| **Checkpoint** | An article you must pass through on the way. Reaching the target without it doesn't count. |
| **Time limit** | None, 2, 5 or 10 minutes. Anyone still going is a DNF. |

**Ready check.** Everyone hits *Mark me ready* in the sidebar; the setup screen
shows who's in. **Start race** unlocks once everyone's ready, and there's a
*Start anyway* underneath for when someone wanders off.

Settings persist between races, so a rematch is one click.

## The clock is fair

The timer stops while an article is loading. What it measures is your thinking,
not your bandwidth — so a slow connection doesn't lose you the race. (Borrowed
from [wikispeedrun.org](https://wikispeedrun.org), which does the same.)

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

**Replay** — the whole race as swimlanes, one per player, on a scrubber. Press
play and watch it unfold. Dotted links mark pages more than one player visited,
so you can see where routes converged — and scrub to the moment two people were
on the same page at the same time without knowing it. Race the same pair twice
and your previous run appears as a dashed ghost lane.

If the race hid opponent positions, watching stays shut until everyone has
finished — otherwise finishing early would be a way to scout for whoever's still
racing next to you.

## Rooms

Everyone on the network running the game lands in the same game by default.
On a shared network — an office, a dorm, a coworking space — another group
could be playing too, and you'd end up in each other's races.

Give your group a room name and you'll only see each other:

```sh
./play.sh --room friday-night          # Linux/macOS
```
```
"Play WikiRace.bat" --room friday-night
```

Everyone in your group has to pass the same name.

## Options

```
--name Marek          your display name
--host                let people on your network play from a browser
--internet            let anyone anywhere play from a browser (public link)
--pages URL           route the shared link through your GitHub Pages address
--code ABC123         require a join code (auto-generated by --internet)
--no-code             with --internet, let anyone with the link straight in
--room friday-night   only play with people using this same room name
--port 8500           different local UI port
--peer 192.168.1.42   add a peer by hand if broadcast is blocked
--no-browser          don't auto-open a tab
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
| `docs/index.html` | the game interface — served by the script, and by GitHub Pages |
| `Play WikiRace.bat` / `play.sh` | launchers (install Python if needed) |
| `Setup.bat` / `setup.sh` | explicit Python setup |
| `wikirace_history.json` | your local copy of past races (created on first finish) |
