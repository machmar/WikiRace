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

They print PASS/FAIL per check and exit non-zero on failure.

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

Traps found the hard way:

- Computed styles lag for nodes the script just changed; reload rather than
  believing a screenshot taken right after a click.
- `requestAnimationFrame` stops while the pane is hidden, so a replay can sit
  at `t = 0` and look broken when it isn't. Step it by hand: `stepReplay(0.1)`.
- Synthetic `pointerover` doesn't trigger CSS `:hover`; use a real hover, or
  assert on the classes and styles your code sets.

## Committing

Only when asked. PowerShell here-strings mangle a message containing double
quotes, so write the message to a file and `git commit -F`. Pushing to `main`
starts the image build; `gh run watch` follows it.
