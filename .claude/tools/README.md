# Dev scripts

Not part of the game: these drive a local copy through its own API so there's
something to look at without playing a whole race by hand.

Start a throwaway server first (see `../notes/workflows.md`), then:

    python drive_classic.py 8477     # six tangled routes from one start
    python drive_tangle.py 8477      # six starts, a checkpoint, a lot of mess
    python drive_lost.py 8477        # lost mode, and its start handout
    python drive.py 8477             # the plain four-player race

The pictures in the top-level README are made from the real game, not drawn:

    py -3.13 shoot_readme.py         # starts its own server, plays a whole race in Chromium, writes docs/img/
    py -3.13 shoot_readme.py --only racing,lobby   # keep just those (the race is still played)

It needs the internet (the articles are the real Wikipedia) and Playwright. It
seeds a few evenings of past races so the lobby has a history, fills the table
with five made-up players and plays the sixth in the browser; every picture is
made fresh, so rerun it when the game looks different enough that they're lying.
Set `WIKIRACE_RAW` to a folder to also keep each picture in full colour.

The design-language retrofit, one script per step, kept as the record of what
moved on each screen. They have all run; running one again stops on its first
anchor, which is the point:

    retrofit_rename.py      # freed .card, .panel and .row for the standard
    retrofit_shared.py      # the pieces every screen shares
    retrofit_scrim.py       # every backdrop is --scrim
    retrofit_lobby.py  retrofit_modes.py  retrofit_setup.py  retrofit_namepick.py
    retrofit_racing.py  retrofit_side.py  retrofit_peekvote.py  retrofit_results.py
    retrofit_watching.py  retrofit_replay.py  retrofit_moments.py

One-off fixes, the same way:

    fix_goalbar_reload.py   # issue #19: the goal bar after a reload
    add_race_name.py        # issue #11: the mode in a race's name, and its rules
    add_past_races.py       # issue #12: past races, the Every race screen, a race's page
    add_race_points.py      # issue #13: what each player was paid, and why
    add_setup_points.py     # issue #33: what a race will pay, in race setup
    add_side_resize.py      # issue #35: a side panel you can resize, and a rules strip that scrolls
    fix_rules_peek_redraw.py  # issue #37: the rules under a race's name came back open by themselves
    fix_giveup_after_finish.py  # issue #47: Give up stayed in the top bar after you finished
    fix_typeahead_after_blur.py  # issue #50: title suggestions opening under a field you had left
    fix_typeahead_stale_answers.py  # issue #52: suggestions for a search you had moved on from

Test suites:

    python test_store.py             # history and SQLite (starts its own server)
    python test_names.py             # a name is a player  (starts its own server)
    python test_past_races.py        # the past-races list (starts its own server)
    python test_points.py            # points by how hard the race was (starts its own server)
    python test_typeahead.py         # suggestions only show the search you are waiting on (starts its own server, needs Playwright)

The ones that start their own server pick a free port and a fresh temp folder,
so they run from anywhere. `fixtures/` holds the history file the pre-SQLite
version wrote, which `test_store.py` imports.
    python test_cp_order.py          # checkpoint order    (needs 8477 running)
    python test_race_name.py         # a race's name and rules (needs 8477, Playwright)
    python test_points_ui.py         # results say why, in the page (needs 8477, Playwright)
    python test_side_panel.py        # the side panel's width and rules strip (needs 8477, Playwright)
    python test_giveup_button.py     # Give up goes when a run is over (needs 8477, Playwright)
