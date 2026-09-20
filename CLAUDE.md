# WikiRace

A LAN party game: everyone races through Wikipedia from one article to another.
Two files do all the work, and there is no build step.

- `wikirace.py` — the server. Python standard library only: HTTP, SSE, a UDP
  gossip protocol between copies of the game, and SQLite for history.
- `ui.html` — the whole browser app in one file. No framework, no bundler; open
  it and it runs.

Push to `main` and GitHub Actions builds the ghcr.io image the NAS runs.

Notes for working on it live in `.claude/notes/`:

- [architecture.md](.claude/notes/architecture.md) — how the game is put
  together and where to find each part.
- [workflows.md](.claude/notes/workflows.md) — running it locally, simulating
  races, the test suites, and the traps.
- [decisions.md](.claude/notes/decisions.md) — why the game works the way it
  does, and what was tried and dropped. Read it before proposing a rework.

`.claude/tools/` holds the scripts that drive fake races and the test suites.

## Design

**Read [docs/DesignLanguage.md](docs/DesignLanguage.md) before writing any CSS
or any words a player will see.** It is short, and it is binding: every value
in it was measured off this game rather than imposed on it, so following it is
mostly a matter of not inventing a new number.
[docs/design-language.html](docs/design-language.html) is the same thing as a
page you can open, with every piece rendered live.

The short version, which is not a substitute for reading it:

- **Never write a bare `px`.** The scales are `--t-*` type, `--s-*` space,
  `--r-*` radius, `--m-*`/`--e-*` motion, `--el-*` elevation, all in `:root`
  beside the colour tokens. A literal is a bug unless it is a border width or
  genuinely one-off, and then it gets a comment saying why.
- Space is a **3-based** rhythm: 3, 6, 9, 12, 15, 20, 26, 40, 60. Not a 4px
  grid — that was measured and it fits this game worst of everything tried.
- Type is four text sizes and four display sizes. No half-pixels.
- **Every surface is one of seven pieces** — Pill, Control, Row, Note, Tip,
  Card, Panel. A new piece of UI is one of the seven, or you have found an
  eighth, and an eighth goes in the standard before it goes in `ui.html`.
- New components take a **base class plus the feature namespace**:
  `class="card lobby-card"`. The base class carries the shape; the namespaced
  one carries only what is particular to that area.
- Shadows are built from `--shadow`, never a literal `rgba` — a literal goes
  muddy on the light themes.

Two things the standard deliberately does **not** cover, so don't "fix" them
to match: the Wikipedia article itself, which keeps Wikipedia's own colours and
type because the reading is meant to look like the real thing; and the route
maps and timeline, which are data drawings whose spacing is computed for
legibility of the race, not for visual rhythm.

## House style

- Comments say **why**, not what. Full sentences, no shouting, no decoration.
- Anything a player can see gets plain English: "everyone starts somewhere
  different", not "lost mode enabled".
- Rules travel with the race, so every player plays the same game; the server
  enforces them, and the browser only repeats the check for a faster message.
- `ui.html` is one long file: edit it with anchored patch scripts that assert
  the anchor appears exactly once, rather than by line number.
- Don't commit unless asked.

## One feature, one chat

Work on a feature lives on its own branch (`feature/<slug>`) and merges into
`main` through a pull request, because pushing to `main` builds the image the
NAS runs — an unfinished feature on `main` is an unfinished feature in the
game.

Start a chat by reading the issue it belongs to, and this file. End it by:

1. leaving the working tree clean, on a branch, with a PR open;
2. writing down anything durable you learnt in `.claude/notes/`, and anything
   you decided (and rejected) in `decisions.md`;
3. filing anything you noticed but didn't do as its own issue, rather than
   leaving it in the chat.

Anything discovered mid-feature that isn't part of it is a new issue, not more
scope.
