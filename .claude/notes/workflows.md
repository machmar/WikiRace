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
- `test_past_races.py` — the list behind the lobby and the Every race screen:
  the archive beyond the working set, winners by mode, the filters, and the race
  going on now. Starts its own, on a database it seeds.
- `test_points.py` — what makes a race harder and what each place pays, issues
  #13 and #34. Imports `wikirace.py` for the rules, then starts its own server
  to see the standings and both places a browser reads a race from agree.
- `test_cp_order.py` — checkpoint order rules. Needs a server on 8477 first.
- `test_reveal_tip.py` — the reveal popup, issue #18. Needs a server on 8477
  first, and Playwright (`pip install playwright && playwright install
  chromium`), because it is the one thing here that has to be watched in a
  real browser. It stubs Wikipedia, so it runs with no internet; set
  `WIKIRACE_CHROME` if Playwright's own Chromium is not where it expects.
- `test_points_ui.py` — Results and a race's page say what each player was
  paid and why, the rules Tip marks what made the race harder, and race setup
  marks it before the race starts. The same needs as `test_reveal_tip.py`.
- `test_race_name.py` — a race's name and the rules under it, issue #11. The
  same needs as `test_reveal_tip.py`. It reads the rules after each press or
  hover only once the fade is over: visibility is part of the transition, so
  reading it straight away catches the old state. After putting the rules away
  it also waits for the page to have rebuilt Results (`redrawn`) before it
  reads again, because the rebuild is what used to bring them back (issue #37).
- `test_side_panel.py` — the side panel's edge and its rules strip, issue #35:
  dragging, the arrow keys, double-click, the limits, what survives a reload,
  a window too small for the saved width, a phone, and the strip stopping at
  its cap. The same needs as `test_reveal_tip.py`.

They print PASS/FAIL per check and exit non-zero on failure.

### On Windows

- `python` on the PATH here is an MSYS build (3.11) with **no pip**, and the
  `pip` on the PATH belongs to a different Python than it. The real interpreter
  is `py -3.13`, so say it every time: `py -3.13 wikirace.py ...`,
  `py -3.13 -m pip install playwright`, `py -3.13 -m playwright install
  chromium` (about 300 MB), `py -3.13 .claude/tools/test_side_panel.py`.
- A binary pipe in PowerShell corrupts it, so `git archive HEAD ... | tar -x`
  fails with "Unrecognized archive format". Write the tar file and unpack it:
  `git archive main wikirace.py ui.html -o before.tar; tar -xf before.tar`.
- The browser suites share the one server on 8477, and so does anything else
  you ran against it. `test_reveal_tip.py` failed once straight after a
  screenshot script that had left two seats named like its own, and passed on
  every run after a clean restart. When a UI suite fails for no reason you can
  see, restart the throwaway server on a fresh data folder before debugging.

The ones that start their own server find `wikirace.py` from where the script
sits, so they run from any checkout and any folder. Each run gets a fresh temp
folder, and every start gets a port the OS picks, so a copy you already have on
8477 or 8478 doesn't get in the way. The game takes the next port along when
the one it was asked for is taken, and that includes one still cooling off after
the server a test has just stopped (on Linux; Windows is more forgiving), so
the tests talk to the port the game printed on its `UI ready at` line, never
the one they asked for. `test_store.py` imports
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
- Results and the Replay are rebuilt about once a second, so anything the page
  remembers as a class on an element is gone within a second. Keep it in a
  variable and draw it into the markup, as `raceRulesOpen` and `raceRulesShut`
  do. A test that reads a fixed time after an action then sees the page just
  before or just after a rebuild, depending on where that falls in the second,
  and passes or fails on the same code (this was #37). Make the page right,
  then wait for a rebuild (`redrawn` in `test_race_name.py` marks the element
  and waits for the mark to go) rather than for a guessed time.
- A check that passes can be passing by accident. `hover peeks` only ever
  passed when a rebuild had dropped the class that was meant to stop it. When a
  flaky test goes both ways, ask what each direction depends on before
  adding a wait.

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
