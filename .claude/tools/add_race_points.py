# -*- coding: utf-8 -*-
"""Issue #13: results say what each player was paid, and why.

The sums come from the server (`race.scoring`); this only draws them: a
points column and a line under each finisher, the multiplier beside the
finishing order, and the race's rules with what made it harder marked.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")
s = io.open(PATH, encoding="utf-8").read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


# -- CSS ----------------------------------------------------------------------

once("""  .path-line { font-size: var(--t-xs); color: var(--fg-faint); margin-left: calc(26px + var(--s-3)); word-break: break-word; line-height: 1.45; }
""", """  .path-line { font-size: var(--t-xs); color: var(--fg-faint); margin-left: calc(26px + var(--s-3)); word-break: break-word; line-height: 1.45; }
  /* What a finisher was paid and why, under the name like the path, and a
     shade stronger than it because it is the line people look for. */
  .score-line { font-size: var(--t-xs); color: var(--fg-dim); margin-left: calc(26px + var(--s-3)); line-height: 1.45; }
  .result-row .pts { min-width: 3ch; }
""", "score line css")

once("""  .race-rules ul { list-style: none; margin: 0; padding: 0; }
""", """  .race-rules ul { list-style: none; margin: 0; padding: 0; }
  /* A rule that made the race harder carries what it added to the points. */
  .race-rules li.rr-hard { display: flex; justify-content: space-between; gap: var(--s-3); }
  .race-rules .rr-pct { font-family: var(--mono); font-size: var(--t-xs); color: var(--fg-dim); white-space: nowrap; }
""", "rules mark css")

# -- the rules, marked --------------------------------------------------------

once("""  const groups = [];
  const add = (group, text, ...pills) => {
    let g = groups.find(x => x.group === group);
    if (!g) groups.push(g = { group, items: [] });
    g.items.push({ text, pills: pills.filter(Boolean) });
  };
""", """  const groups = [];
  const add = (group, text, ...pills) => {
    let g = groups.find(x => x.group === group);
    if (!g) groups.push(g = { group, items: [] });
    const item = { text, pills: pills.filter(Boolean) };
    g.items.push(item);
    return item;
  };
  // Which rules made the race harder is the server's call, made once for the
  // standings; here it is only attached to the line that names the rule.
  const scoring = race.scoring;
  const hard = (item, key) => {
    const n = scoring ? scoring.hard.filter(k => k === key).length : 0;
    if (n) item.hard = "+" + n * scoring.step + "%";
  };
""", "add returns item")

once("""    add("Who wins", min + (min === 1 ? " minute" : " minutes") + " to finish", min + " min limit");""",
     """    hard(add("Who wins", min + (min === 1 ? " minute" : " minutes") + " to finish", min + " min limit"), "time_limit");""",
     "mark limit")
once("""  if (race.lost) add("Route", "Everyone started somewhere different", "lost: everyone starts somewhere different");""",
     """  if (race.lost) hard(add("Route", "Everyone started somewhere different", "lost: everyone starts somewhere different"), "lost");""",
     "mark lost")
once("""    add("Route", "Via " + list,
        ...stops.map((c, i) => "via " + c + (slots[i] ? " (" + slotName(slots[i], stops.length) + ")" : "")));
    const order = orderPhrase(stops, slots);
    if (order) add("Route", order.charAt(0).toUpperCase() + order.slice(1));
  }
  if (race.ban_hubs) add("Route", "Hub pages off-limits", "no hub pages");
""", """    hard(add("Route", "Via " + list,
        ...stops.map((c, i) => "via " + c + (slots[i] ? " (" + slotName(slots[i], stops.length) + ")" : ""))), "checkpoint");
    const order = orderPhrase(stops, slots);
    if (order) hard(add("Route", order.charAt(0).toUpperCase() + order.slice(1)), "order");
  }
  if (race.ban_hubs) hard(add("Route", "Hub pages off-limits", "no hub pages"), "no_hubs");
""", "mark route")
once("""  add("Allowed", hidden ? "Positions hidden" : "Everyone's position shown", hidden ? "positions hidden" : "positions shown");
  add("Allowed", noBack ? "No going back" : "Back button allowed", noBack ? "no going back" : "back allowed");
  add("Allowed", race.allow_find === false ? "No find on page" : "Find on page allowed",
      race.allow_find === false && "no find on page");
  if (race.peek) add("Allowed", "Target opened by a vote", "target revealed");
  else if (race.allow_peek === false) add("Allowed", "Target hidden the whole race", "target stays hidden");
  else add("Allowed", "Target could be opened by a vote");
  add("Allowed", allowTables(race) ? "Tables of links shown" : "Tables of links hidden",
      allowTables(race) && "link tables allowed");
  const toc = raceToc(race);
  add("Allowed", toc ? "Contents: " + TOC_LABELS[toc].toLowerCase() : "No contents list",
      toc && "contents: " + TOC_LABELS[toc].toLowerCase());
""", """  hard(add("Allowed", hidden ? "Positions hidden" : "Everyone's position shown", hidden ? "positions hidden" : "positions shown"), "hidden");
  hard(add("Allowed", noBack ? "No going back" : "Back button allowed", noBack ? "no going back" : "back allowed"), "no_back");
  hard(add("Allowed", race.allow_find === false ? "No find on page" : "Find on page allowed",
      race.allow_find === false && "no find on page"), "no_find");
  if (race.peek) add("Allowed", "Target opened by a vote", "target revealed");
  else if (race.allow_peek === false) hard(add("Allowed", "Target hidden the whole race", "target stays hidden"), "no_reveal");
  else add("Allowed", "Target could be opened by a vote");
  hard(add("Allowed", allowTables(race) ? "Tables of links shown" : "Tables of links hidden",
      allowTables(race) && "link tables allowed"), "no_tables");
  const toc = raceToc(race);
  hard(add("Allowed", toc ? "Contents: " + TOC_LABELS[toc].toLowerCase() : "No contents list",
      toc && "contents: " + TOC_LABELS[toc].toLowerCase()), "no_contents");
""", "mark allowed")

once("""        i === 0 && "handicaps on");
  });
  return groups;
}
""", """        i === 0 && "handicaps on");
  });

  // Last, because it follows from everything above it.
  if (scoring) {
    const m = scoring.multiplier;
    add("Points", m > 1 ? "Worth ×" + m + ": each rule marked +" + scoring.step + "% made it harder"
                        : "The usual points: nothing made it harder",
        m > 1 && "points ×" + m);
  }
  return groups;
}
""", "points group")

once("""      g.items.map(it => "<li>" + esc(it.text) + "</li>").join("") + "</ul></div>").join("") +""",
     """      g.items.map(it => it.hard
        ? '<li class="rr-hard">' + esc(it.text) + '<span class="rr-pct">' + esc(it.hard) + "</span></li>"
        : "<li>" + esc(it.text) + "</li>").join("") + "</ul></div>").join("") +""",
     "tip marks")

# -- results ------------------------------------------------------------------

once("""  html += '<div class="hub-sec"><h4>Finishing order — ' +
    (raceMode(race) === "clicks" ? "fewest clicks wins" : "fastest time wins") + "</h4>";
  html += fin.map((r, i) =>
    '<div class="row in-card result-row"><span class="medal">' + (medals[i] || (i + 1) + ".") + "</span>" +
    '<span class="rn" style="color:' + colorFor(r.name) + '">' + esc(r.name) + "</span>" +
    '<span class="rs">' + fmtTime(r.elapsed) + " · " + r.clicks + "c</span></div>" +
    ((r.path || []).length ? '<div class="path-line">' + r.path.map(esc).join(" › ") + "</div>" : "")
  ).join("");
  html += out.map(r =>
    '<div class="row in-card result-row"><span class="medal">—</span>' +
    '<span class="rn muted">' + esc(r.name) + '</span><span class="rs">gave up</span></div>').join("");
""", """  // The sums are the server's, so what a player reads here is what the
  // standings added up. A race from an older server has none to show.
  const scoring = race.scoring;
  const mult = scoring ? scoring.multiplier : 1;
  const steps = scoring ? scoring.hard.length : 0;
  const bonusFor = raceMode(race) === "clicks" ? "fastest time" : "fewest clicks";
  const paid = r => {
    if (!scoring) return { pts: "", why: "" };
    const p = scoring.players[r.name];
    if (!p) return { pts: "–", why: "A guest takes the place, not the points" };
    return { pts: String(p.points),
             why: p.place_points + " for " + ordinal(p.place) +
                  (p.bonus ? " + " + p.bonus + " for " + bonusFor : "") + (mult > 1 ? ", ×" + mult : "") };
  };

  html += '<div class="hub-sec"><h4>Finishing order — ' +
    (raceMode(race) === "clicks" ? "fewest clicks wins" : "fastest time wins") +
    (mult > 1 ? '<span class="muted"> · points ×' + mult + " for " + steps +
                (steps === 1 ? " thing that" : " things that") + " made it harder</span>" : "") + "</h4>";
  html += fin.map((r, i) => {
    const pay = paid(r);
    return '<div class="row in-card result-row"><span class="medal">' + (medals[i] || (i + 1) + ".") + "</span>" +
      '<span class="rn" style="color:' + colorFor(r.name) + '">' + esc(r.name) + "</span>" +
      '<span class="rs">' + fmtTime(r.elapsed) + " · " + r.clicks + "c</span>" +
      (scoring ? '<span class="pts">' + pay.pts + "</span>" : "") + "</div>" +
      (pay.why ? '<div class="score-line">' + esc(pay.why) + "</div>" : "") +
      ((r.path || []).length ? '<div class="path-line">' + r.path.map(esc).join(" › ") + "</div>" : "");
  }).join("");
  html += out.map(r =>
    '<div class="row in-card result-row"><span class="medal">—</span>' +
    '<span class="rn muted">' + esc(r.name) + '</span><span class="rs">gave up</span>' +
    (scoring ? '<span class="pts">0</span>' : "") + "</div>").join("");
""", "results rows")

io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
