# Working on it

## Run a copy to test against

Never touch a server the user is playing on. Use ports 8477–8479 and a
throwaway data directory:

```bash
WIKIRACE_NO_BROWSER=1 python wikirace.py --host --port 8477 --room test --no-discovery --data-dir /tmp/wrtest
```

`--no-discovery` keeps it off the LAN, so it can't disturb a real game.

## Simulate races

The scripts in `.claude/tools/` play full races through the API, which is far
quicker than clicking through Wikipedia, and gives the replay and the maps
something real to draw:

- `drive.py [port]` — four players, one start, a straightforward race.
- `drive_classic.py [port]` — seven long routes from one start that keep
  colliding at the same hubs, one photo finish, one player who gives up
  part-way, and one who gives up without clicking anything (an empty path,
  which the replay has to draw).
- `drive_lost.py [port]` — a lost race; also checks the server hands out a
  different start per player and keeps it across asks.
- `drive_tangle.py [port]` — six players, six starts, a checkpoint, long
  detours and doubling back. The messiest picture for the maps.

The browser joins any race that's still active, so a session watching a replay
can find itself racing. Give up (`post('/give_up', …)`) to get out of it.

## Test suites

- `test_store.py` — history, SQLite, the JSON migration. Starts its own server.
- `test_names.py` — a name is a player; one name races once. Starts its own.
- `test_cp_order.py` — checkpoint order rules. Needs a server on 8477 first.
- `test_reveal_tip.py` — the reveal popup, issue #18. Needs a server on 8477
  first, and Playwright (`pip install playwright && playwright install
  chromium`), because it is the one thing here that has to be watched in a
  real browser. It stubs Wikipedia, so it runs with no internet; set
  `WIKIRACE_CHROME` if Playwright's own Chromium is not where it expects.

They print PASS/FAIL per check and exit non-zero on failure.

The two that start their own server find `wikirace.py` from where the script
sits, so they run from any checkout and any folder. Each run gets a fresh temp
folder and a port the OS picks, so a copy you already have on 8477 or 8478
doesn't get in the way. If something still answers on the chosen port they stop
instead of testing it. `test_store.py` imports
`.claude/tools/fixtures/legacy_history.json`, a history file written by the
last version before SQLite. Keep it as it is: it only proves anything because
the old code wrote it.

## Editing `ui.html`

It's one file of several thousand lines, so line numbers are useless between
edits. Write a small Python patch script that asserts each anchor appears
exactly once, then apply it:

```python
def once(old, new, label):
    assert s.count(old) == 1, (label, s.count(old))
```

That catches a moved or duplicated anchor instead of silently patching the
wrong place. Keep the scripts; they double as a record of what changed.

There is no syntax check unless node is installed — a broken edit shows up as
`X is not defined` in the browser. After a risky edit, reload the page and call
something defined near it before trusting the change.

## Checking it in the browser

Prefer reading values out of the page over screenshots:

```js
({ mode: replay.mapType, players: replay.lanes.length, clock: $('rp-clock').textContent })
```

To get the browser's own player into a state without playing to it, drive the
API from the page with its `post()`, which carries the tab's sid, then reload.
A run that is already over, with a checkpoint on its trail:

```js
await post("/name", { name: "Tester" });
await post("/start_race", { target: "Pulsar", lang: "cs", kind: "classic",
  start: "Karel IV.", starts: ["Karel IV."], checkpoints: ["Praha", "Vltava"] });
await post("/progress", { article: "Praha", clicks: 1, path: ["Karel IV.", "Praha"], times: [0, 5], elapsed: 6 });
await post("/give_up", { elapsed: 8, clicks: 1, path: ["Karel IV.", "Praha"], times: [0, 5] });
```

Traps found the hard way:

- Computed styles lag for nodes the script just changed; reload rather than
  believing a screenshot taken right after a click.
- `requestAnimationFrame` stops while the pane is hidden, so a replay can sit
  at `t = 0` and look broken when it isn't. Step it by hand: `stepReplay(0.1)`.
- Synthetic `pointerover` doesn't trigger CSS `:hover`; use a real hover, or
  assert on the classes and styles your code sets.
- Anything that reacts to a *change* in a snapshot can't be tested with a
  sleep. Driving the API and then waiting a fixed second races the stream, and
  the test passes or fails on the machine's mood. Wait for the page to have
  seen the thing — `wait_for_function` on `S.snap.race.race_id`, or
  `wait_for_selector` on what should appear — and the same test goes green
  every run. `test_reveal_tip.py` was flaky three ways before it did this.

## Filing issues and PRs

Anything Claude opens is filed by the machine account `machmar-claude`, not by
the owner, so the history says who did what. It is a collaborator on the repo
with write access, and its login lives in its own gh config directory.

    $env:GH_CONFIG_DIR = "$env:USERPROFILE\.config\gh-claude"
    gh issue create ...

There is a `ghc` function in the user's PowerShell profile that does the same
thing in one word (`ghc issue create ...`), leaving plain `gh` as the owner's
own login. Assign work to `machmar-claude` too.

In a Claude session this is already the default: `.claude/settings.local.json`
sets `GH_CONFIG_DIR` for the session, so every `gh` call is the machine account
without anyone remembering. `.claude/settings.json` adds a hook that refuses
`gh issue create`, `gh pr create` and the other commands that stamp a name,
unless the machine account is what is being used - a backstop for a machine
where the env var is missing.

The same hook refuses `gh issue create` with no `--label` (or `-l`) on it, so
every issue Claude files has at least one label. `gh label list` shows what
there is: bug, enhancement, documentation, accessibility and question are the
ones in use. The hook only looks at `gh` where a command starts, so a note or a
commit message that merely mentions the command goes through.

To act as the owner on purpose - creating a repository under their account,
inviting a collaborator - clear it for that one command:

    $old = $env:GH_CONFIG_DIR; Remove-Item Env:GH_CONFIG_DIR
    gh repo create machmar/thing --private
    $env:GH_CONFIG_DIR = $old

The settings files are only read when a session starts, so a change to either
takes effect in the next chat, not the one that made it.

Commits keep the owner as committer but carry Claude as co-author, which is
what the trailer in the commit message is for.

## Committing

Only when asked. PowerShell here-strings mangle a message containing double
quotes, so write the message to a file and `git commit -F`. Pushing to `main`
starts the image build; `gh run watch` follows it.

## Comparing before and after

The browser pane is shared with the owner, so a change to how something looks
is best shown as two live copies side by side rather than described:

- Run the working tree on 8477, and the last commit on 8478 from an export:
  `git archive HEAD wikirace.py ui.html | tar -x -C <dir>`. The server reads
  `ui.html` from disk on every request, so re-exporting refreshes "before"
  and saving the working file refreshes "after", with no restart.
- Give both copies the same data: run the same drive script against each, and
  keep the fake players alive with a loop that polls `/api/state` for their
  sids every few seconds. Without it they time out and "leave", and the two
  lobbies stop matching.
- Open each in its own tab, set `document.title` to BEFORE and AFTER, and set
  the same fixed viewport on both.

Traps:

- A tab that has been reloaded and one that has not can show different state
  for the same race. Reload both before believing a difference. (The goal bar
  used to be the example, issue #19; a reload now draws it from the restored
  trail.)
- Messages the game re-hides on every update (the name-clash and guest notes)
  can be pinned visible for a comparison with a temporary style in the page -
  never in the source.
- A screenshot taken straight after a theme switch or a toast catches it
  half-faded. Read the computed style instead, or wait.
- When the pane is hidden, screenshots fail; read values out of the page.
- A patch script that stops on an anchor writes nothing. Check `git status`
  before trusting anything a chained command printed after it.
