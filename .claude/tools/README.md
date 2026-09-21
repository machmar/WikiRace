# Dev scripts

Not part of the game: these drive a local copy through its own API so there's
something to look at without playing a whole race by hand.

Start a throwaway server first (see `../notes/workflows.md`), then:

    python drive_classic.py 8477     # six tangled routes from one start
    python drive_tangle.py 8477      # six starts, a checkpoint, a lot of mess
    python drive_lost.py 8477        # lost mode, and its start handout
    python drive.py 8477             # the plain four-player race

The design-language retrofit, one script per step, kept as the record of what
moved on each screen. They have all run; running one again stops on its first
anchor, which is the point:

    retrofit_rename.py      # freed .card, .panel and .row for the standard
    retrofit_shared.py      # the pieces every screen shares
    retrofit_scrim.py       # every backdrop is --scrim
    retrofit_lobby.py  retrofit_modes.py  retrofit_setup.py  retrofit_namepick.py
    retrofit_racing.py  retrofit_side.py  retrofit_peekvote.py  retrofit_results.py
    retrofit_watching.py  retrofit_replay.py  retrofit_moments.py

Test suites:

    python test_store.py             # history and SQLite (starts its own server)
    python test_names.py             # a name is a player  (starts its own server)
    python test_cp_order.py          # checkpoint order    (needs 8477 running)
