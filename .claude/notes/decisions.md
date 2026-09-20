# Decisions, and what they cost

Why the game is the way it is, so nobody spends an afternoon re-proposing
something that was already tried and dropped.

## A name is the player, not a device

Results, standings and handicaps are keyed by the normalised name, so the same
name on a phone and a laptop is one player. A scheme with per-device player
keys was built and then reverted: it made "Kody here" and "Kody there" two
players, which is not what anyone means by a name.

The cost is that two people picking the same name become one player, so the
name picker warns when a name is already on the scoreboard or in the game, and
suggests ones nobody has used. A name can only race once per race
(`name_in_race`): whoever joins first keeps it, and anyone else is asked to
pick another.

Guests get a name for the session and are left out of the standings.

## Rules travel with the race

Every rule lives in the race record, not in each browser's settings, so
everyone plays the same game and a peer joining late learns the rules with the
race. The server is what enforces them; the browser repeats the check only to
give a faster, friendlier message.

## Game modes are modes, not presets

Classic, Advanced and Lost change what the setup screen asks for, not just the
default values. Classic asks two questions; Advanced has the full board; Lost
has no start to pick. The rules everyone argues about anyway (back button,
find, hub pages, contents, time limit) are a single **Game settings** menu
shared by all three, with Easy/Normal/Hard presets, folded away by default.

Rejected: a list of preset buttons on one setup screen. It left everyone
scrolling past nine settings to start a two-click race.

## Lost mode hands out starts from the server

The browser setting the race up rolls a dozen well-linked pages; the server
gives each player one and keeps it on their run. That way a reload lands you
back on the same page, no two players get the same one, and everyone can see
where everyone started.

Rejected: each browser rolling its own start. Two players would sometimes get
the same page, and a refresh would move you somewhere new.

## Starts come from a curated pool, not Special:Random

Wikipedia's random endpoint mostly returns stubs, and a page nothing links to
is a page nobody can reach. The pool (`const POOL`) is hand-picked for heavy
cross-linking, and other editions are reached through language links. The
Obscure button exists for when you want the chaos anyway.

## Checkpoints: the list is the order

A pinned stop must be made at its place in the list; unpinned stops can be made
whenever. "Any order", "this one last" and "a fixed route" are then the same
rule with different pins, and moving a row is enough to change the route.

Shuffle rerolls until what the route *demands* differs from before, because
reordering stops that nobody has to make in order is not a change at all.

## One clock for the whole replay

Timeline and the four maps draw the same moment of one replay (`replay.t`, in
race seconds). Switching view mid-replay carries on from where you were.

- **Race clock pacing**: a light waits on a page as long as that player read
  it, then hops, so people finish in the order they really did. A constant
  speed along the drawn line was rejected: in Spring and Metro a line's length
  is an accident of the layout, so the same click would be quick on one map and
  slow on the next.
- **The whole race takes ~18 seconds**, whatever it really took.
- **Plays once when it comes into view**, then settles. A loop never stops
  moving beside things you are trying to read, and drains a phone.
- **Play and stop only** — no scrubber, no speed control. Stopping shows the
  whole race.
- The player boxes under the view are also how you pick whose route to follow.
- **A box always reads as a sentence.** Where there is no page to name — a
  player who gave up before clicking anything — it says "at the start", and
  "gave up at the start" once they are out. An em dash standing in for the
  missing page read as "gave up on —", which is not a thing anyone says.

## Four map layouts, kept

No single drawing of four tangled routes suits everyone, so Aligned, Metro,
Spring and Collapsed all stayed, with Timeline alongside them. The studies that
produced them, with measurements, are the "Route Layout Studies" page; the
short version is that each trades something real (a dot is a page / no line
runs backwards / an axis you can read / how much is hidden).

The maps never assume a single start page (`m.startKeys` is a set), because
lost races have one per player.

## Colours come from one place

`raceColors` assigns them and every view uses it, so the timeline, the maps and
the boxes agree on who is who. The palette is pitched for a dark screen, so the
light themes swap in darker twins of the same hue (`LIGHT_INK`) rather than
using different colours.

## The browser talks to Wikipedia directly

All article fetching goes browser → Wikipedia with `origin=*`; the server never
proxies it. Spectating broadcasts only *which* page someone is on and how far
down it they are, and each spectator fetches that page itself, so article text
never crosses the LAN.

## One HTML file, no build step

`ui.html` is the whole app. It makes the game trivial to host and to hand to a
friend, and it is why edits are made with anchored patch scripts rather than by
line number. A framework would buy less than the simplicity costs.

## History in SQLite

Races are kept in `wikirace.db` (WAL), with the old `wikirace_history.json`
imported once and renamed. A single JSON file rewritten on every change was
losing the point at which races got long.

## There is a design language, and it was measured, not invented

Colour was already a real token system; type, space, radius and motion never
got the same treatment. Measuring `ui.html` found 27 distinct font sizes across
140 declarations — 48 of them on half-pixels that were the same size written on
different days — 13 radii expressing 4 roles, and spacing at nearly every
integer from 1 to 26.

So the scales in `docs/DesignLanguage.md` are derived: each is the value that
already dominated. Two move away from current practice on purpose, and both say
so: panels go from 10px to 16px radius (today a panel is rounded *less* than
the cards inside it, which reads backwards), and four text sizes is fewer than
the game uses.

**A 4px grid was the worst-fitting scale of everything tested**, because it
moves `6px` forty times and `10px` twenty-four. The game has always had a
3-based rhythm. Anyone reaching for the usual grid out of habit will fight the
file the whole way.

Rejected: a scale fine enough to fit the game exactly. It needed 13–15 steps,
and a 13-step scale is not a system — it is the status quo with token names on
it, and "which size?" still has a dozen answers.

Rejected: **retrofitting by attrition**, each feature snapping whatever it
happened to touch. It was the first plan and it was wrong. A half-converted
interface has *more* inconsistency than an unconverted one, because two systems
run at once and "which is right, the old panel or the new one?" becomes a live
question on every screen. The game is brought over one screen at a time
instead, each its own issue, commit and before-and-after.

Two things the standard deliberately does not cover: the article, which keeps
Wikipedia's own colours and type because the reading is meant to look like the
real thing; and the route maps and timeline, which are data drawings whose
geometry means something about the race rather than about visual rhythm. The
chrome around a drawing is ordinary interface and does follow the standard.
