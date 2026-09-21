# How the game is put together

Line numbers move; the anchors below are search strings that don't.

## The server, `wikirace.py`

One `State` guarded by a single `RLock`; every mutation calls `bump()` so the
HTTP layer can tell browsers something changed (SSE). Copies of the game find
each other over UDP and gossip races and player positions, so any peer can
carry on if another drops.

| Thing | Anchor |
|---|---|
| Race record, every rule that travels with it | `def act_start_race` |
| Where a player begins (lost mode hands out one each) | `def act_start_page`, `def lost_start` |
| Progress reports from the browser | `def act_progress` |
| Finishing and giving up, and every rule check | `def _record_result` |
| Checkpoints: which are missed, and which are out of place | `def missing_checkpoints`, `def checkpoints_out_of_order`, `def checkpoint_slots` |
| One name races once | `def name_in_race` |
| Snapshot the browser polls/streams | `"my_run": me.run` |
| Peer gossip merge | `def _merge_race` |
| History in SQLite, and the old JSON import | `class Store` |

A race is a dict, and its rules are part of it: `start`, `target`, `lost`,
`starts`, `kind`, `checkpoints`, `checkpoint_slots`, `mode` (time/clicks),
`toc`, `time_limit`, `ban_hubs`, `allow_back`, `allow_find`, `allow_peek`,
`allow_tables`, `show_positions`, `handicaps`, `peek`. Older races may lack
newer fields, so read them through the helpers rather than directly.

Players are identified by **name**, not by device: the same name on a phone and
a laptop is one player, and results, standings and handicaps are keyed by the
normalised name. Guests are excluded from standings.

## The browser, `ui.html`

Roughly in order down the file:

| Area | Anchor |
|---|---|
| Theme and design tokens, then every component's CSS | `:root {`, `body[data-theme="light"]` |
| The seven pieces' base classes (see `docs/DesignLanguage.md`) | `---------- the seven pieces` |
| Wikipedia access (all calls go browser → Wikipedia) | `async function wiki(`, `const POOL = [` |
| Racing: navigating, clicks, checkpoints, winning | `async function navigate(`, `async function win(` |
| What counts as a link, and who is one click away | `function linkIsPlayable`, `async function isOneAway`, `async function linkIsOnScreen` |
| Game modes and the setup dialog | `const MODES = [`, `function openModePicker`, `function openConfigurator` |
| Settings menu, presets, the fold | `const PRESETS = [`, `const syncSettings` |
| Checkpoints: the list, pinning, shuffle | `function renderCheckpointChips`, `function shuffleCheckpoints` |
| Replay: one clock for every view | `const replay = {`, `function drawReplayView`, `function stepReplay` |
| Timeline view (hover highlight, lanes) | `function timelineStage`, `function drawTimeline` |
| Route maps (four layouts, pan/zoom, lights) | `const RouteMap = (() =>` |
| Player colours, light-theme twins | `function colorFor`, `const LIGHT_INK` |
| Splashes for checkpoints and the finish | `function celebrateCheckpoint` |
| Name picker and the name generator | `function openNamePicker`, `const NameGen` |

### Game modes

`Classic`, `Advanced` and `Lost` (`const MODES`). The mode decides what the
setup screen asks for, not just its defaults:

- Classic: start and target, fastest time, no stops on the way.
- Advanced: everything — who wins, checkpoints and their order.
- Lost: target only; everyone wakes up on a different random page. The browser
  that sets the race up rolls a dozen well-linked pages (`lostStarts`) and the
  server hands each player one of their own, kept on their run so a reload
  lands back on it.

The **Game settings** menu (opponents, back, find, reveal vote, hub ban, the
tables of links at the foot of an article, handicap, contents, time limit) is
the same in every mode, folded behind a button with Easy/Normal/Hard presets.
The race carries its `kind`, and races from before modes existed work theirs
out from their rules (`raceKind`).

### Checkpoints

The list is the order. A pinned stop must be made at its place in the list
(`checkpoint_slots[i] === i + 1`), and unpinned stops can be made whenever, so
"any order", "this one last" and "a fixed route" are the same rule with
different pins. Moving a row moves its pin with it.

### Replay

One clock — `replay.t`, in race seconds — drives every view: Timeline, Aligned,
Metro, Spring, Collapsed. It plays itself once when the tab comes into view, on
the race clock (a light waits on a page as long as that player read it, then
hops), and the whole race takes `REPLAY_SECONDS`. Stopping shows everything.
The player boxes under the view are also how you pick whose route to follow.
A player who gave up without ever reporting a page has an empty `path`, so their
lane has no steps at all: every view has to cope with that, and the box says
"at the start" rather than naming a page.

The maps don't assume one start page: `m.startKeys` is a set, so lost races
fan out from several. Colours come from `raceColors` so the timeline, the maps
and the boxes agree, and `ink()` swaps in darker twins on the light themes.
