# -*- coding: utf-8 -*-
"""Take the lobby's "Last race" line and its Rematch button away (issue #31).

Since #30 the lobby's Earlier races card lists the last race first, with its
mode, winner and time, and a race's own page has "Play this again". The line in
Standings said the same thing in a smaller place, and the Rematch button named
the same race a third time, so both go and the history is the one way back to a
finished race.

Kept, per workflows.md, as a record of exactly what changed.
"""
import io
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
UI = os.path.join(ROOT, "ui.html")
README = os.path.join(ROOT, "README.md")


def load(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def save(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class Patch:
    def __init__(self, text):
        self.s = text

    def once(self, old, new, label):
        assert self.s.count(old) == 1, (label, self.s.count(old))
        self.s = self.s.replace(old, new)


# ---- ui.html ----

ui = Patch(load(UI))

ui.once('''            <div id="lobby-board"><div class="empty">No races yet.</div></div>
            <div id="lobby-last" class="tiny muted" style="margin-top:var(--s-3)"></div>
''', '''            <div id="lobby-board"><div class="empty">No races yet.</div></div>
''', "standings line")

ui.once('''          <button id="lobby-start" class="primary big">Set up a race</button>
          <button id="lobby-rematch" class="big" hidden>Rematch</button>
''', '''          <button id="lobby-start" class="primary big">Set up a race</button>
''', "rematch button")

ui.once('''  renderBoard(snap.leaderboard, $("lobby-board"));

  // Offer a rematch of the most recent race, settings and all.
  const last = lastFinishedRace(snap);
  setFlag($("lobby-rematch"), "hidden", !last);
  if (last) {
    setText($("lobby-last"), "Last race: " + raceTitle(last));
    setText($("lobby-rematch"), "Rematch: " + raceTitle(last));
  } else {
    setText($("lobby-last"), "");
  }
  renderPast(snap);
}

function lastFinishedRace(snap) {
  if (!snap || !snap.races_list) return null;
  const done = snap.races_list.filter(r => r.finishers);
  done.sort((a, b) => (b.created || 0) - (a.created || 0));
  return done[0] || null;
}
''', '''  renderBoard(snap.leaderboard, $("lobby-board"));
  renderPast(snap);
}
''', "renderLobby and lastFinishedRace")

ui.once('''/* One click, and the same game again - its rules, not whatever was set up last. */
$("lobby-rematch").onclick = async () => {
  const row = lastFinishedRace(S.snap);
  const last = row && await fetchRace(row.race_id);
  if (!last) { toast("Couldn't load the last race — try again"); return; }
  const rules = rulesOf(last);
  // A lost rematch gets lost somewhere new.
  const starts = last.lost ? await lostStarts(rules.lang, last.target, rules.checkpoints, rules.ban_hubs) : [];
  if (last.lost && starts.length < 2) { toast("Couldn't reach Wikipedia"); return; }
  await post("/start_race", Object.assign(rules, {
    start: last.start, target: last.target, lost: !!last.lost, starts, kind: kindOf(last),
  }));
};
''', '', "rematch handler")

ui.once('/* Settings survive between races, so a rematch is one click. */',
        '/* Settings survive between races, so setting up the same race again is quick. */',
        "cfg comment")

save(UI, ui.s)

# ---- README.md ----

readme = Patch(load(README))
readme.once("Settings persist between races, so a rematch is one click.",
            "Settings persist between races, so setting up the same race again is quick.",
            "readme")
save(README, readme.s)

print("done")
