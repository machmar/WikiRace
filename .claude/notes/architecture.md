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
| Past races for the lobby and the Every race screen | `def past_races`, `def race_summary`, `"/api/races"` |
| Points: what made a race harder, and what each finisher was paid | `def race_difficulty`, `def race_scoring` |
| A race's rules read from a request, shared by starting one and pricing a draft | `def rules_from`, `def act_score_rules` |
| Standings, rebuilt from the races every time | `def leaderboard` |

A race is a dict, and its rules are part of it: `start`, `target`, `lost`,
`starts`, `kind`, `checkpoints`, `checkpoint_slots`, `mode` (time/clicks),
`toc`, `time_limit`, `ban_hubs`, `allow_back`, `allow_find`, `allow_peek`,
`allow_tables`, `show_positions`, `handicaps`, `peek`. Older races may lack
newer fields, so read them through the helpers rather than directly.

Players are identified by **name**, not by device: the same name on a phone and
a laptop is one player, and results, standings and handicaps are keyed by the
normalised name. Guests are excluded from standings.

A race's points are worked out from the race, never stored with it:
`with_scoring` hands the browser a copy with a `scoring` field (what made it
harder, the multiplier, and each finisher's place points, bonus and total) on
the snapshot's race and on `/api/race`. The standings add up the same totals,
so the sum a player is shown on Results is the sum in the standings. The
browser draws `scoring` and never works it out itself.

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
| A race's name, and the rules it was played under | `function raceRules`, `const raceTitle`, `function raceNameHTML` |
| Settings menu, presets, the fold | `const PRESETS = [`, `const syncSettings` |
| What setup's rules add to the points | `async function markSetupPoints` |
| Checkpoints: the list, pinning, shuffle | `function renderCheckpointChips`, `function shuffleCheckpoints` |
| Replay: one clock for every view | `const replay = {`, `function drawReplayView`, `function stepReplay` |
| Timeline view (hover highlight, lanes) | `function timelineStage`, `function drawTimeline` |
| Route maps (four layouts, pan/zoom, lights) | `const RouteMap = (() =>` |
| Player colours, light-theme twins | `function colorFor`, `const LIGHT_INK` |
| Splashes for checkpoints and the finish | `function celebrateCheckpoint` |
| Name picker and the name generator | `function openNamePicker`, `const NameGen` |
| Past races: lobby list, Every race screen, a race's page | `const past = {`, `function openRaceList`, `function openRacePage` |
| The same game again: Rematch and Play this again | `function rulesOf`, `function playAgain` |

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

A race is named by its mode and its route wherever it is shown afterwards
(`raceTitle`): `Classic · Chess → Neutron star`, or `Lost · → Pulsar`. On
Results and Replay the mode is a chip that opens the rules (`raceNameHTML`).
Those rules and the strip beside the racers both come from `raceRules`, so a
new rule is added there once and shows up in both.

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

### Past races

Every race anyone has a result in is reachable from the lobby (issue #12).
The lobby shows the newest eight; "Show older races" opens the **Every race**
screen, grouped by evening and filtered by game, player and a page that was a
start, target or stop. A race opens on **a page of its own**.

Both are stages beside lobby, race and hub (`racelist`, `racepage`), and both
have an address: `#races?kind=…&player=…&find=…` and `#race=<id>`. A link
opened from cold waits for the first snapshot (`past.pending`,
`routePending`): if a race is on and you're in it, the race wins and the link
is dropped. Leaving either screen for any other stage clears the address.

The list comes from `/api/races`, which reads the whole archive plus the
working set (the working set wins for a race in both) and sends a summary per
race - the finishing order as names, never paths. The full record is the
existing `/api/race?id=` when one is opened.

A race's page draws nothing of its own for results and replay: it **moves
the hub's `#results-pane` and `#replay-pane` into itself** and renders them
with a snapshot whose `race` is the old one, and `setStage` moves them home
(`restorePanes`). Both are built around fixed ids, so a second copy would
fight the first. The steps table under them is the page's own
(`drawSteps`).

`rulesOf(race)` is the one place that turns a race back into setup's rules.
Rematch posts them straight away (one click, as before); "Play this again"
opens race setup filled in with them. A lost race keeps only its target.
