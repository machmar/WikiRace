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

## One click away means a link you could click

The shout, and the badge beside a racer, come from the links API, which counts
every link in the article's wikitext. The game hides a lot of an article — the
tables of related links at the foot of it, category lists, maintenance boxes —
so the API said "one away" about links nobody could see. On a page like
*Finger*, whose navigation table lists every other finger and the hand and the
arm, that was most of the time.

The rare yes from the API is now checked by laying the article out the way the
race lays it out, off the side of the screen, and asking whether a link to the
target has a box on the page. Asking the page beats keeping a second list of
what is hidden, because a second list is a list that can disagree with the
stylesheet; it also picks up the rest of the hidden furniture for free.

The cost is one article fetch, and it is only ever paid on the yes, which is
rare and cached per article for the race. Rejected: doing the visibility check
on every report, which would fetch an article per player per click; and
`action=parse&prop=links`, which is the same wikitext-level answer as the
links API and would have needed the same correcting.

Whether the tables are there at all is a rule of the race (`allow_tables`,
off by default), so it is in Game settings with everything else people argue
about, and Easy turns it on.

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

## Bringing the game onto the design language

Done one screen at a time, each its own commit with a before-and-after the
owner looked at: shared pieces first, then the lobby, mode picker, race setup,
name picker, racing chrome, side panel, peek sheet and vote card, hub results,
Watching and the replay. Every patch script is kept in `.claude/tools/` as the
record of what moved. What it settled:

- **The shared pieces go first, as their own step.** The base button, fields,
  small print, standings table and dialog are on every screen; whichever
  screen got to them first would have silently changed all the others.
- **Three class names were taken, and were renamed out of the way** rather
  than prefixing the standard's pieces: the dialog was `.card` (it is a Panel,
  now `.panel`), the side panel's sections were `.panel` (now `.side-sec`), and
  a flex helper was `.row` (now `.hstack`). A class called `.card` that is
  really a dialog would have misled someone either way.
- **A Control is the element and inherits its size.** The standard first gave
  buttons a fixed 13px, but the game's buttons have always inherited; forcing
  one size would have shrunk every button in the game.
- **A Row inside a Card is a hairline, not a box** (`.row.in-card`), which is
  how every list of players was already drawn. All of them now match.
- **A toast is a Note that floats, not a Tip**: it carries a sentence and
  points at nothing. A Tip always points at something under it.
- **The spring is for something that travels and lands** - the theme knob, a
  player arriving on your page, a checkpoint, the finish - not "arrivals" in
  general, and never a dialog simply appearing. The one place the game already
  used the curve was the theme knob.
- **A log is fine print.** The play-by-play was first snapped up to body size,
  which made an insignificant log look like a feature.
- **Every backdrop is `--scrim`.** The one behind race setup hard-coded the
  dark theme's colour at 93% and turned the light theme near-black.
- **Honours and the best-route box are Cards**, though the standard first
  listed them as centred Notes.
- **A size stays where it earns it.** The finishing order stays at 15px, a size
  up from other lists, because it is what the results screen is for; it had
  inherited that size, and the Row base class nearly shrank it by accident.
- **The carve-outs grew from one to four**: the article, the maps and
  timeline, illustrations (the miniature setup screens in the mode picker),
  and the big moments (the countdown and the splashes). The interface around
  any of them, and a message shown with them, still follows the standard.

Rejected: prefixing the base classes (`ui-card` and so on). Nothing could ever
collide, but the misleading `.card` dialog would have stayed forever.

## Every issue gets a label, checked by the hook

An unlabelled issue is lost when the backlog is sorted, so filing one needs at
least one label. The check lives in `.claude/tools/guard-gh.ps1`, the hook that
already stands in front of `gh issue create`, because that is how issues get
filed here.

Rejected: enforcing it on GitHub. GitHub has no way to refuse an unlabelled
issue. Issue forms can pre-fill a label, but `gh issue create` skips them, and a
workflow can only react after the issue exists - by labelling it itself, which
defeats the point, or by nagging.

## The self-starting tests carry what they need

`test_store.py` and `test_names.py` used to name a scratch folder from an old
session of a different project. `test_store.py` read its legacy history from
that folder, so it only ran on one machine until the folder was cleaned (issue
#20). Now each run finds the game from where the script is, makes its own temp
folder, and imports a legacy history file checked in under
`.claude/tools/fixtures/`. That file is the one the old version actually wrote,
copied as it was. A file made up to match would only show that the importer
reads what we think the old format was.

Each of the two tests takes a port the OS chooses rather than a fixed one. On
the old fixed 8478 they collided with the throwaway "before" copy that
`workflows.md` suggests, and quietly tested that copy instead. They also refuse
to start if anything answers on their port first.

Rejected: an environment variable to override the port or the folder. Nothing
needs one, and it would be one more thing that could point at the wrong place.

## The reveal vote says itself out loud, and the button stays as it was

The vote to open the target has always carried its tally on the reveal button,
but the button is in the chrome and the game is played in the article, so an
ask could pass a whole table by: the only other sign was a line of `--t-xs`
fine print in the play-by-play, which on a phone is behind the drawer
(issue #18).

What it got is one thing: a Tip hanging off the reveal button, saying who
asked and how the tally stands, gone after twenty seconds. Pressing it opens
the vote card rather than casting a vote - being told a vote is open is not
being asked to rush it - and on the grant the same Tip turns green and opens
the target page, which is the job the old toast could not do because a toast
takes no clicks.

The button itself was left exactly as it was. Four things were drawn and
turned down with it: pips on the button for each racer's answer, a fourth
colour for "you have answered and they have not", the vote marks repeated in
the racer list, and a rewritten vote card naming the asker. A tally that stays
at 3/4 when the fourth says no is fine, and everything those added was
something the Tip now says in a sentence.

Also turned down, and worth keeping turned down: opening the vote card by
itself when somebody asks. The race clock does not stop, so a modal that
steals the screen because another player clicked something costs everyone who
did not ask for it real seconds, and it makes asking a weapon.

Three rules the implementation turns on:

- **It speaks to everybody, including people who have already answered.**
  "Three of us are waiting on you" is news to the three as well. It will not
  tell you about your own vote.
- **It fires on a change in the tally, not on a snapshot.** Snapshots arrive
  several times a second and mostly say the same thing, so each announcement
  is keyed by the race and the set of names that have said yes.
- **An ask made while you were still entering the race is news when you land.**
  The baseline it compares against is left where it was while the countdown
  has the screen, rather than moved on. Arriving at a vote already in progress
  after a *reload* still stays quiet, because that is not news about anybody -
  the button already says a vote is open.
