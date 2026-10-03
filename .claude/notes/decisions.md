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
`workflows.md` suggests, and quietly tested that copy instead.

That was not the whole of it (issue #25). Both tests stop the server and start
a second one on the same data folder, to prove the archive survives a restart,
and on Linux the port the first one used is still in `TIME_WAIT`. The game is
right to refuse it, because `pick_http_port` deliberately has no
`SO_REUSEADDR`, so the second server moved to the next port and said so. The
tests had picked one port at load and polled it for twelve seconds, then killed
a healthy server. Now every start asks the OS for a fresh port, and `start()`
reads the port out of the game's own `UI ready at` line and polls that. The
second half is the one that matters: the test no longer assumes something about
the game that is the game's to decide, and it also covers somebody running a
copy on the port it was handed.

The old check that refused to start if anything already answered on the
requested port went with it. It looked at the port the game was *asked* for,
which is exactly the one it may not take, and the new `start()` only ever
talks to a port its own child announced, which nothing else can hold.

Rejected: an environment variable to override the port or the folder. Nothing
needs one, and it would be one more thing that could point at the wrong place.

Rejected: fixing it in the game, with `SO_REUSEADDR` or a retry on the same
port. The comment on `pick_http_port` is about Windows silently handing one
player's requests to another copy, and that matters far more than a test being
tidy.

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

## A race is named by its mode, and the mode opens its rules

The Replay and Results only said `Chess → Neutron star`, so a week later there
was no telling whether that was Classic, Advanced or Lost, or what the rules
were (issue #11). A race is now named by its mode and its route wherever it is
shown afterwards - `Classic · Chess → Neutron star`, or `Lost · → Pulsar`,
since a lost race had no shared start to name - and on Results and Replay the
mode is a Pill you can press, which opens a Tip listing every rule the race
was played under: who wins, the limit, the language, the checkpoints and their
order, hubs, what was allowed, and each handicap by name.

Four designs were drawn side by side, with the game's own tokens, before any
of it was built. Turned down:

- **A fold under the name that brings back the rule strip.** Nothing floats,
  but there is no peek, opening it pushes the replay down, and a race with
  every rule on becomes a wall of pills that has no good way to name a
  handicapped player.
- **Showing only the rules that differ from the Normal preset**, with the rest
  behind a chip. It answers the question without a tap, but "unusual" is a new
  idea that has to stay in step with the presets, and what counts is a
  judgement call every time a setting is added. It can still go beside the
  chip later without undoing anything.
- **A rules card on Results, shared with the finished-games list** (#12). It
  has the most room, but the Replay has none, so it needed a chip there anyway,
  and it would have settled part of #12's design early.

Three rules the implementation turns on:

- **One list of rules.** `raceRules` is what the strip beside the racers draws
  from as well, so the two can never disagree. The strip's order changed with
  it - grouped as the Tip groups them - and its wording did not.
- **The open state lives outside the markup.** Results is redrawn on every
  snapshot, so a Tip whose openness was only a class would snap shut under
  whoever was reading it.
- **Putting it away means away.** Pressing the chip again, or Escape, while
  the pointer is still on it would leave the hover peek holding it open, so
  the peek sits out until the pointer leaves. That memory is `raceRulesShut`,
  beside the open state, and not a class on the element: it was a class first,
  and the next rebuild of Results made a new element without it, so the rules
  came back open by themselves under a pointer that had not moved (#37).
  Turned down: waiting longer in `test_race_name.py`. The test was flaky
  because the page was wrong, and a wait would only have hidden it.

## Finished races open on a page of their own, and the long list on a screen of its own

The history was all in SQLite and none of it reachable unless it happened to be
the active race (issue #12). Four ways to reach it were built as a working demo
on a seeded history of three evenings, and the owner played each:

1. **The hub, pointed backwards** - a lobby card, and clicking a race opens
   the post-race screen on it. The cheapest, but the hub then means two
   things, and only a line of small print says which race you are looking at.
2. **A page per race** - chosen. Results, honours, best route, the replay and
   a table of everyone's steps on one scrolling page, with an address. It
   reads like a report, a race can be sent to someone, and the hub stays
   about the race going on now.
3. **A history browser** - a two-pane dialog with filters. Good for finding
   last week's race, overkill for one evening.
4. **Flip through** - arrows on the hub bar stepping race to race. Fun for
   "the one before", hopeless for a race from yesterday without a list.

The owner then asked for "Show older races" to open a dedicated screen
rather than lengthen the lobby's list, which is the Every race screen: grouped
by evening with a line about each, the podium and where you came on every
row, and filters that live in the address.

What it settled:

- **The steps table is the answer to "who met whom".** The honours name one
  pair; a column per player, a click per row, with shared pages in bold, shows
  every meeting at once. A shared start doesn't count as one.
- **The Every race screen loads everything that matches, up to 500, at once**
  rather than a page at a time. Evening summaries ("Kody won 5") are only
  true if the whole evening is there, and a LAN party's history is hundreds of
  races, not millions. Past 500 it says it is showing the newest.
- **The page borrows the hub's results and replay** rather than drawing
  copies; see architecture.md.
- **Rematch stays one click**, and now uses the race's own rules. It never
  appeared before: it looked for `results` in the snapshot's compact list,
  which carries a count. "Play this again" is the considered version, and
  opens setup instead. (The lobby's Rematch button has since gone; see "The
  lobby points at the history, not at the last race".)
- **A Row you can press** went into the design standard: the whole line is
  the choice, so it is not a button inside a Row.

Rejected with the designs above: paging the lobby's list in place (the first
version of design 2) - a lobby that grows downward forever buries the buttons
that start the next race.

## Points follow how hard the race was

Every race used to pay the same, so an Easy Classic win with the back button
and find was worth a Hard Lost win through three stops in order (issue #13).
Now every rule that made a race harder adds **20%** to everything that race
pays: no going back, no find, link tables hidden, contents off, hubs banned,
the target never revealable, positions hidden, a time limit of ten minutes or
less, a lost start, each checkpoint, and a pinned order (once, and only with
two or more stops). Place points and the bonus are scaled together and rounded
once. Easy Classic is x1, Normal Classic x1.6, Hard Classic x2.6, and Hard Lost
through three stops in order x3.6; the most there can be is x4.2.

- **Equal weights, deliberately.** No going back is harder than hidden
  positions, but "+30% for this, +10% for that" is the formula nobody at the
  table can follow. "Count the hard things, a fifth more each" can be counted
  on fingers.
- **By the rule, not by what happened.** A race where the vote was allowed
  but nobody used it was as hard as one where it wasn't allowed, but it is
  scored as the easier one. Scoring on what happened would make voting to
  reveal cost everyone points - an interesting tension, but a second thing to
  explain, and the multiplier would no longer be known when the race starts.
- **An older race is read the way the rules list reads it.** A missing
  `allow_tables` or `toc` means hidden or off there, so it counts as harder
  here: the race is paid for the rules it says it was played under. Old
  standings went up by that, never down.
- **The handicap is not difficulty, and doesn't change points.** It holds
  the leaders back so the session stays close; paying them extra for beating
  it would undo what it is for, and it applies to one player, not the race.
- **The fewest-clicks bonus needs somebody to beat.** It was +3 (and is +2
  now, see "The fewest-clicks bonus is worth a place") to whoever is best at
  the measure the race isn't scored on, the winner and ties included, but
  finishing alone no longer collects it.
- **Giving up, or running out of time, is still worth nothing.** Credit per
  checkpoint was considered and dropped: it rewards banking a stop and then
  quitting, and in a party game finishing is what scores.
- **The server does the sums.** The browser only draws `scoring`, so the
  rules Tip, the line under each finisher and the standings can't disagree.
  A copy of the game on an older version would still disagree about the
  standings until it is updated, because every copy rebuilds them itself.

Race setup says it before the race starts (issue #33). Each setting carries a
faint "+20%" at the end of its row while it is making the race harder, the
checkpoints label carries theirs ("+60%" for two stops in order), and the Game
settings header carries the total ("points +220%"), where it stays in sight
with the settings folded away. Setup speaks in a sum of percentages because it
is built up one rule at a time; Results speaks in the multiplier because it
explains a sum. Both are the same number, and the rules Tip's "+20%" marks
join them.

- **Setup asks the server** (`/api/score_rules`) rather than repeating the
  check, on every change, dropping any answer that comes back after a newer
  question. Starting a race and asking what one would pay read the rules
  through the same `rules_from`, so what setup promises is what is paid.
- **Turned down: showing the marks only on hover**, with just the total
  always there. On Hard the marks line up into a column of "+20%"s, but they
  are faint, and a phone has no hover; the owner chose to keep them.

## Points follow how many players you beat

The place points were 10 / 7 / 5 / 3, then 2, whatever the size of the field, so
winning against one other player paid what winning against seven did (issue
#34). It only shows when a few people race while the rest are away from the
table, but then it paid a duel as much as a full house. The owner's view was
that paying more for beating more players is good, so a finisher is now paid
**2 for finishing and 2 for every player they beat**: 4 for winning against one
other player, 10 against four, 16 against seven, and 2 for a race on your own.
The fewest-clicks bonus and the difficulty multiplier are as they were, and
everything is still rounded once.

- **Beating includes the players who gave up or ran out of time**, and guests
  behind you. They started the race and you finished it; and a guest has always
  taken a place without taking points, so beating one is still beating somebody.
  A guest ahead of you is not beaten. Turned down: counting only players who
  finished, which stops someone padding a field by joining and quitting but
  makes the winner of a race everyone else abandoned worth only 2.
- **There is no ceiling.** Turned down: cutting today's list from the top for a
  small field (a duel starts lower down it and a field of five or more pays as it
  always did). It keeps whole numbers and leaves a full table alone, but beating
  seven would pay what beating four does, and the owner wanted more.
  Turned down: leaving it as it was, and counting a race for the standings only
  once it has two players who aren't guests.
- **A full table moves a little.** Five players pay 10 / 8 / 6 / 4 / 2 where it
  was 10 / 7 / 5 / 3 / 2. Standings are rebuilt from the last 60 races, so races
  with three players or fewer are worth less than they were and larger ones are
  worth more, the way #13 moved them.
- **The points are provisional while a race is on.** Results are recorded when
  someone finishes or gives up, so a player still on the course has not been
  beaten yet. A winner's total grows as the others come in and is settled when
  the last one is. Counting everyone still racing would pay for beating players
  who might yet win.
- **The fewest-clicks bonus now outweighed the gap between neighbouring places.**
  A place was worth 2 more than the one below it, and the bonus was 3, so second
  place with the fewest clicks outscored a first place without it by one point
  (5 against 4 in a duel, 11 against 10 in a field of five). Before, they tied.
  Left alone here because the bonus is a different question, and settled in #41
  (next section).

## The fewest-clicks bonus is worth a place

Once a place was worth 2 more than the one below, the bonus of 3 meant the
runner-up could outscore the winner, which neither the old tie nor the new flip
had been designed to do (issue #41). The bonus is now **2**, the gap between
neighbouring places, so it can lift a player level with the one above and no
higher. The owner chose it on the issue; the multiplier from #13 scales both
sides alike, so it does not change who is ahead.

- **Level, not ahead.** Second with the fewest clicks now ties first without it
  (4 against 4 in a duel, 10 against 10 in a field of five), and a tie in points
  is a tie in the standings. That is the point of the bonus: the other style of
  play is worth a place, not a win.
- **The standings dip a little.** Every bonus pays 1 less before the multiplier,
  and standings are rebuilt from the last 60 races, so totals fall by about that
  much per bonus won. Nothing stored changes.
- **Kept as a number, not tied to the per-player 2.** `POINTS_FEWEST_CLICKS` is
  its own constant, with a comment that says what it must not exceed. Turned
  down: defining it as `POINTS_PER_PLAYER_BEATEN`, which would have changed the
  bonus silently the day someone changes what a beaten player pays.
- **Turned down: leaving it at 3**, which keeps the flip, and **making it 1**,
  which would also have stopped it but with the bonus worth half a place. The
  issue offered all three and the owner picked 2.
- `test_points.py` pins it: in fields of two to eight, second with the fewest
  clicks must come out level with the winner, not past.

## The lobby points at the history, not at the last race

Since #12 the lobby's Earlier races card lists the newest race first, with its
mode, winner and time, and "just now" while it is the one on. Two more things
named that same race: a "Last race: …" line at the foot of Standings, and a
Rematch button saying it a third time (issue #31). Both are gone. Standings
ends with the standings, and a finished race is reached the one way, through
its row in Earlier races.

- **The Rematch button went with the line**, at the owner's call: the history
  already handles it. What it costs is the one-click rematch. The way back is
  now the race's row, its page, "Play this again" (setup filled in with the
  race's rules, free to change), then Start - three presses, not one.
- **Setup still remembers the last settings** (`cfg`), so Set up a race and
  Start is the quick route when nothing is to change.
- **Turned down: keeping the line but making it say something the history
  doesn't**, such as what the last race paid each player. It is a feature of
  its own and not what the repeat was about; it was not built.

## The side panel has an edge you pull, and a rules strip that stops

The panel was a fixed 330px, and the rules under Racers grew with the race: a
Hard Advanced race is a dozen pills and six rows, enough to push the racers
and the standings off the screen (issue #35).

It is now 270px by default, between 220 and 480 and never more than half the
window. The edge is pulled with a pointer, moved with the arrow keys (15px a
press) or put back by double-click. The rules strip is a step tighter and
stops at about four rows, with a bit of a fifth showing so that it reads as
scrollable, then scrolls inside itself.

- **The width stays on this machine** (`wr_side`), like the theme. A rule
  travels with the race so that everyone plays one game; a width is about the
  screen in front of you, and a phone and a laptop want different ones. It is
  never sent to the server.
- **Only a person's change is written.** A width the window is too small for
  is clamped by the stylesheet, and is neither rewritten nor forgotten, so
  coming back to a big window finds it again.
- **The grip is inside the panel's column, not astride its border.** Half of a
  grip on the border would sit on the article's scrollbar. Because it shares
  the panel's cell in the grid, the panel is placed there by hand as well;
  otherwise whichever came second is pushed down a row.
- **It is not an eighth piece.** The seven are surfaces; an edge you pull is
  an affordance on one, so `docs/DesignLanguage.md` is unchanged. The widths
  and the 110px cap are literals, with a comment, because the scales cover
  type, space and radius and not layout.
- **No phone version.** Under 760px the panel is a drawer of one width and the
  grip is hidden.
- **Known and filed rather than fixed:** at the 220px minimum the Lost race's
  longest pill wraps to two lines (#38, since fixed: see the next section), and
  `test_race_name.py` was flaky on Windows on unchanged code (#37, since fixed:
  the page lost a class when it rebuilt Results, see the race name's rules
  above).

## A pill says what is not beside it, and wraps like a box

At the panel's 220px minimum the rules strip is 179px wide, and the Lost race's
pill, "lost: everyone starts somewhere different", is 213px of words (issue
#38). Two things were wrong, and both are fixed.

- **The wording.** The strip's first pill already says "Lost", so the prefix
  repeated what sat beside it. It is now "different starts". Cutting only the
  prefix was not enough: "everyone starts somewhere different" is 190px, which
  still wraps in 179. The Tip's line, the countdown's and the best-route
  caption are written for other places and keep the full sentence.
- **The wrapping.** Other pills wrap at that width too (a contents label such
  as "contents: sections and subsections", a checkpoint with a long name), so a
  shorter phrase for one rule was never going to settle it. A Pill that will
  not fit now breaks its words evenly (`text-wrap: balance`) and keeps the
  corner a one-line Pill has, half a line plus the padding and the border, so
  it becomes a rounded box with the same curve as its neighbours instead of a
  stretched capsule whose ends cut into the words. The rule is on the base
  `.pill`, and every variant was measured to be still a capsule when it fits on
  one line: the goal-line chips and checkpoints, the strip's pills, the mode
  Pill with its caret, and the phone's racer list. The company pill sets its own
  radius and is not touched.
- **Guarded with `@supports (height: 1lh)`.** A `calc()` with a variable in it
  is valid when the stylesheet is read and only fails when it is used, so a
  browser without the `lh` unit would not fall back to the capsule above it; it
  would draw square pills. Behind the guard it keeps the capsule.
- **Turned down: an ellipsis.** It keeps every pill to one line but hides the
  rule with no way to read it in the panel, and "nothing is cut off" is what
  made the wrap tolerable in the first place.
- **Tried and dropped: `max-width: 100%`.** The strip is a flex row, so a pill
  can already shrink, and removing it changed nothing in the tests.
- **`overflow-wrap: anywhere`** is what lets a word with no break in it (a
  long checkpoint name is enough) shrink to the strip instead of pushing it
  sideways, which turns on a horizontal scrollbar.

## Each feature chat works in a worktree of its own

Chats that work on a feature each started in the one checkout, and a branch
switch in one moved the branch for all of them (issue #44, found while working
#38). A chat's branch was cut from another chat's commit instead of from
`main`; uncommitted edits were carried along by a switch into a chat that
hadn't made them; and a throwaway server went on serving a `wikirace.py` that
had changed under it. Only the first was caught, by reading the reflog.

So a feature chat now starts in `.claude/worktrees/<slug>`, cut from
`origin/main`, and the main checkout is for reading. The recipe is in
CLAUDE.md and the traps are in `workflows.md`.

- **Turned down: only saying "fetch, then cut the branch from `origin/main`".**
  It fixes the wrong base and nothing else. Chats would still share a working
  tree, so the carried-along edits and the stale server would happen as often
  as before. A worktree fixes all three, and `readme-refresh` already showed
  the convention working.
- **`--no-track`.** `git worktree add ... origin/main` makes the new branch
  track `origin/main`, which makes a bare `git push` look like it is aimed at
  `main`. The first push is `git push -u origin feature/<slug>`.
- **What it costs.** Ignored files don't follow, which is how
  `settings.local.json` got into the recipe: the `gh` hook reads
  `GH_CONFIG_DIR` from it, and a worktree without it can't open an issue or a
  PR. Every worktree is a full copy of the tree, which is small here. Ports
  8477–8479 are still shared by all of them.
- **`.claude/worktrees/` is in `.gitignore`.** It had only been hidden by one
  machine's `.git/info/exclude`.

## Give up goes when a win does, and after the game has accepted it

A run ends in the page three ways, and `giveUp()` and `outOfTime()` each put
the Give up button away while `win()` did not (issue #47), so it sat in the top
bar over Results until a reload, which goes through the branch of `enterRace()`
that hides it. `S.done` is set in exactly four places, those three and that
branch, so `win()` was the only gap.

- **It goes after the game's answer, not with `S.done`.** `win()` sets `S.done`
  first and then asks the game, and a refusal (a name clash, a missed
  checkpoint the page didn't catch) sets it back and returns you to the race.
  Hiding the button with `S.done` would leave a player in a race with nothing to
  give up with. `giveUp()` and `outOfTime()` also hide it after their post.
- **Turned down: drawing the button from state.** `btn-peek` is shown by a
  function of `S.running` and `S.done`, which cannot go stale, while Give up is
  switched by hand in five places, which is how one was missed. Moving it to
  state is the tidier shape, but it touches every branch of `enterRace()` and
  is more than a bug that one line closes. If a sixth place ever needs to
  switch it, do that then.
- **Not covered: a refused win keeping the button.** `test_giveup_button.py`
  checks the four endings; making the game refuse a win from the page needs a
  name clash or a checkpoint race the page's own check lets through, and that
  was more setup than the one line it would guard.
