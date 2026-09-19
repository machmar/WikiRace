# Dev scripts

Not part of the game: these drive a local copy through its own API so there's
something to look at without playing a whole race by hand.

Start a throwaway server first (see `../notes/workflows.md`), then:

    python drive_classic.py 8477     # six tangled routes from one start
    python drive_tangle.py 8477      # six starts, a checkpoint, a lot of mess
    python drive_lost.py 8477        # lost mode, and its start handout
    python drive.py 8477             # the plain four-player race

Test suites:

    python test_store.py             # history and SQLite (starts its own server)
    python test_names.py             # a name is a player  (starts its own server)
    python test_cp_order.py          # checkpoint order    (needs 8477 running)
