# The design language

What every part of WikiRace is meant to look like, be called, and say, so that
a new feature is a lookup rather than a judgement call and the game looks like
one thing.

This is derived from the game as it stands, not imposed on it. Each rule below
is the value that already dominated the file, so most of what is written here
you have already been doing — it just had no name. Where a rule moves away from
current practice it says so and says why.

The rules about *how the game works* — that rules travel with the race, that
the server enforces and the browser echoes, that a name is the player — live in
[.claude/notes/decisions.md](../.claude/notes/decisions.md) and are not
repeated here.

## How this gets applied

New work is built on the tokens from the start — that part is not negotiable,
and it is why the token layer landed before anything else.

The game itself is brought over **one screen at a time, deliberately**, each
screen its own issue, its own commit and its own before-and-after. An earlier
draft of this file said the retrofit would happen by attrition, each feature
snapping whatever it happened to touch. That was wrong, and the reason is worth
keeping: a half-converted interface has *more* inconsistency than an
unconverted one, because now there are two systems running at once and "which
is right, the old panel or the new one?" becomes a live question on every
screen. Attrition ends in a mixed game indefinitely; a campaign ends in a
coherent one.

The screens, as the file actually divides: lobby, mode picker, race setup, name
picker, racing chrome, side panel, peek sheet and vote card, hub results, hub
replay chrome.

Two consequences worth being explicit about:

- A literal `px` value in new CSS is a bug unless it is a border width or
  something genuinely one-off, in which case say why in a comment.
- When you edit a component, snap the whole component, not the one line you
  came for. Half-snapped components are worse than unsnapped ones.

## Colour

Unchanged. `:root` already carries a two-tier set — base colours
(`--bg`, `--fg`, `--accent`, `--good`, `--warn`, `--bad`, `--gold`) and the
tinted surfaces built from them (`--good-bg` / `--good-line` / `--good-fg` and
their siblings) — and the light and Wikipedia themes swap values rather than
hunting hex codes. Everything below is an attempt to give type, space, radius
and motion the same treatment.

Standing rules that the file used to half-follow:

- Shadows use `var(--shadow)`, never a literal `rgba`. Three places hard-code
  `rgba(0, 0, 0, .5)` today and go muddy on the light themes.
- **Every backdrop behind a Panel is `var(--scrim)`**, whatever the Panel is.
  The one behind the race setup used to hard-code the dark theme's colour at
  93%, so on the light theme it turned the whole screen near-black while the
  name picker and peek sheet used a soft grey — three dimmings for one idea.
  A blur on top is fine; a different colour is not.
- Player colours come from `raceColors` and nowhere else, with `ink()` swapping
  in the `LIGHT_INK` twins on light themes, so the timeline, the maps and the
  boxes always agree on who is who.

## Type

Four text sizes and a display tier. Twenty-seven distinct sizes were measured
across 140 declarations; forty-eight of those sat on half-pixels — 9.5, 10.5,
11.5, 12.5, 13.5, 14.5, 15.5 — scattered across unrelated components. They were
not a dense-data tier, they were the same size written on different days, and
collapsing them is most of what this scale does.

| Token | Size | What it is for |
|---|---|---|
| `--t-xs` | 11px | fine print: legends, pips, meta, captions |
| `--t-sm` | 13px | the workhorse: body, rows, pills, notes — Controls inherit instead |
| `--t-md` | 15px | emphasis: card headings, lead-ins |
| `--t-lg` | 17px | section headings |
| `--t-xl` | 22px | display |
| `--t-2xl` | 30px | display |
| `--t-3xl` | 46px | the finish |
| `--t-4xl` | 130px | the countdown |

Two-thirds of declarations move, by an average of 0.56px. Nine declarations in
the whole file move 1.5px or more.

Weights are **400** for body, **600** for emphasis, **700** for headings. The
500, 650 and 800 in use today account for six declarations between them.

## Space

A 3-based rhythm. This is the part most likely to surprise someone arriving
with habits: **a 4px grid is the worst-fitting scale of everything measured**,
because it moves `6px` forty times and `10px` twenty-four times. The game has
always had a 3-based rhythm; it just never said so.

| Token | Size | Where it lands |
|---|---|---|
| `--s-1` | 3px | hairline gaps, pill padding |
| `--s-2` | 6px | tight: icon gaps, chip innards |
| `--s-3` | 9px | default: row gaps, small box padding |
| `--s-4` | 12px | comfortable: control padding, list gaps |
| `--s-5` | 15px | generous: card innards |
| `--s-6` | 20px | panel padding |
| `--s-7` | 26px | dialog padding |
| `--s-8` | 40px | section separation |
| `--s-9` | 60px | page rhythm |

Sibling groups are laid out with flex or grid and `gap`, not with per-element
margins that collapse or double.

## Radius

Four roles. Thirteen values were in use to express them, and `--radius: 10px` —
the only radius token that existed — was used three times and was already
overloaded across two of the four.

| Token | Size | Role |
|---|---|---|
| `--r-pill` | 999px | a standalone token you read |
| `--r-box` | 8px | controls and small boxes |
| `--r-card` | 12px | a grouped thing among its siblings |
| `--r-panel` | 16px | the container the rest sits inside |

`--r-panel` moves panels from 10px to 16px. Today a panel is rounded *less*
than the cards inside it, which reads backwards — the container should be the
softer shape.

## Motion

Three durations and two easings.

| Token | Value | For |
|---|---|---|
| `--m-fast` | .12s | state flicks: hover, press, toggle |
| `--m-base` | .2s | the default: folds, fades, slides |
| `--m-slow` | .6s | celebratory: splashes, fanfare |
| `--e-out` | ease | everything |
| `--e-spring` | cubic-bezier(.4, 1.3, .5, 1) | arrivals only |

`--e-spring` is for a checkpoint splash or the finish — something that has
arrived. It is never for a hover. It appears once in the file today and should
stay rare.

Everything obeys `prefers-reduced-motion`.

## Elevation

Three levels, and a shadow is what says "this is floating above the page", so
it is spent only on things that are.

| Token | Value | For |
|---|---|---|
| `--el-ring` | `inset 0 0 0 2px <colour>` | selection and focus |
| `--el-lift` | `0 8px 26px var(--shadow)` | toasts, tooltips, popovers |
| `--el-float` | `0 20px 60px var(--shadow)` | dialogs, sheets |

## The seven pieces

Every surface in the game is one of these. **A new piece of UI is one of the
seven, or you have found an eighth — and an eighth goes in this file before it
goes in `ui.html`.**

| Piece | In the markup | What it is | Radius | Padding |
|---|---|---|---|---|
| **Pill** | `.pill` | a standalone token you read, not a surface things sit on | `--r-pill` | `--s-1 --s-4` |
| **Control** | `button`, `input`, `select` | something you operate | `--r-box` | `--s-2 --s-4` |
| **Row** | `.row`, or `.row.in-card` | one repeated line in a list | `--r-box` | `--s-3 --s-4` |
| **Note** | `.note` + `.good` `.warn` `.bad` `.info` | a tinted message saying how things stand | `--r-box` | `--s-3 --s-4` |
| **Tip** | `.tip` | something floating that points at what is under it | `--r-box` | `--s-1 --s-3`, `--el-lift` |
| **Card** | `.card` | a grouped thing among its siblings | `--r-card` | `--s-5`, or `--s-6` roomy |
| **Panel** | `.panel` | the container the rest sits inside | `--r-panel` | `--s-7` |

A **Control** is the element itself — a plain `button`, text field or `select`
is already one, with no class. Its text takes the size of wherever it sits:
fifteen pixels on an open screen, less in the side panel. An earlier draft of
this file gave Controls a fixed `--t-sm`, but the game has always let buttons
inherit, and forcing one size on every button would have been a restyle rather
than a snap. `.primary`, `.ghost`, `.danger` and `.big` are its variants.

A **Row inside a Card** drops its own box and is divided from the next by a
hairline instead: `.row.in-card`. A box inside a box is heavy, and every list
in a card in this game — the lobby's players, the standings, the racers — was
already drawn that way before there was a standard to say so.

**Row and Note are the same shape**, and differ in what they are for: a Row is
one of many and neutral — a checkpoint in the list, a player in the ready list,
a finishing place. A Note is one of one and tinted, and it is there because
something happened.

So that the difference is visible and not only a matter of colour, **a Note is
centred**, with one carve-out: a Note that belongs to one control stays
left-aligned at that control's edge, because centring it detaches it from the
field it is about. The name picker's error and hint are the left-aligned case;
the race warning, the awards and the facts are the centred case.

A **left stripe** (`inset 3px 0 0 <colour>`) marks a Row as significant — a
start, a checkpoint, a target. It belongs to Rows, so Notes do not use it.

### Base class, then the feature namespace

The CSS is namespaced by area — `rm-` route map, `rp-` replay, `cp-`
checkpoints, `np-` name picker, `mp-` mode picker, `ff-` fanfare — and that
stays, because it is how anything gets found in a file this long. What was
missing is a shared layer underneath it, which is why `.card`, `.lobby-card`
and `.np-card` were three unrelated implementations of one idea.

The base class sits alongside the namespaced one:

```html
<div class="card lobby-card">
<div class="row in-card lp">
```

`.card` carries the radius, padding and surface; `.lobby-card` carries only
what is genuinely particular to the lobby. The lobby is built exactly this way,
and is the example to copy.

Three of these names used to mean something else in `ui.html`, and were renamed
out of the way before the base classes went in: the dialog was `.card` (it is a
Panel, and is now `.panel`), the side panel's sections were `.panel` (now
`.side-sec`), and a flex layout helper was `.row` (now `.hstack`). `.hstack`
is a helper for laying things out in a line, not one of the seven — it has no
surface of its own.

## Words

Anything a player can see is plain English. These are transcribed from lines
that already ship, not invented.

1. **Name things the way a player would.** "Everyone started somewhere
   different", never "lost mode enabled". Nobody out there knows the game has
   modes with names.
2. **A failure says what happened, then what to do.** "Couldn't find a pair in
   that language — try again". No `Error:` prefix, no apology, no stack-trace
   vocabulary.
3. **A refusal says why, in the same breath.** "Only article links count —
   that one's off-limits". Being told no without being told why is what makes
   people think the game is broken.
4. **A setting gets a qualifying line, not a definition.** "A real help — and
   arguably a cheat". The table is deciding whether to allow it, so say what
   allowing it means, not what the toggle does.
5. **A limit is advice.** "Six checkpoints is plenty", not "Maximum 6
   checkpoints".
6. **Sentence case, and no shouting.** Full stops where a sentence ends;
   labels and buttons do not get one.
7. **The server's message and the browser's say the same thing.** The browser
   check exists only to be faster. If the two ever disagree, a player is being
   told two different stories about one rule.

## What this does not cover

**The article itself.** Wikipedia's own colours and type apply inside
`#article-wrap` and the other reading surfaces on the `wiki` theme, because the
reading is meant to look like the real thing. The game around it follows this
file; the article does not.

**The route maps and the timeline.** These are data drawings, not interface.
Lane heights, node radii and the distance between hops are computed so that a
race can be read at a glance, and a number in that geometry means something
about the race rather than something about visual rhythm. Forcing `--s-3` into
a lane height would break a picture to satisfy a rule that was never about
pictures.

The chrome *around* a drawing — the replay controls, the player boxes, the view
switcher, the info panel — is ordinary interface and does follow this file. The
line is the drawing surface itself.
