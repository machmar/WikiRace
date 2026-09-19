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
