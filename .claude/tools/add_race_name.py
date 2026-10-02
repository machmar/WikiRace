# -*- coding: utf-8 -*-
"""Issue #11: say which mode a race was, and what its rules were.

A race is named by its mode and its route wherever it is shown afterwards -
"Classic · Chess → Neutron star", or "Lost · → Pulsar" when there was no
shared start. On the Results and Replay headers the mode is a Pill you can
press, and what it opens is a Tip listing the rules the race was played under.

The rules come from one list, raceRules(), which the strip beside the racers
now draws from as well, so the two can never tell different stories.

Four designs were drawn for this; this is option 1. See decisions.md.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI = os.path.join(ROOT, "ui.html")

s = io.open(UI, encoding="utf-8").read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


# ---------------------------------------------------------------- CSS
once(
    "  .hub-sub { color: var(--fg-dim); font-size: var(--t-sm); margin: 0 0 var(--s-6); }\n",
    "  .hub-sub { color: var(--fg-dim); font-size: var(--t-sm); margin: 0 0 var(--s-6); }\n"
    "\n"
    "  /* A race's name: its mode, then its route. The mode is a Pill you can\n"
    "     press, and what it opens is the rules the race was played under, so a\n"
    "     race a week old still says what game it was. */\n"
    "  .race-name { position: relative; display: flex; flex-wrap: wrap; align-items: center; gap: var(--s-1) var(--s-3); }\n"
    "  button.race-kind { padding: var(--s-1) var(--s-3) var(--s-1) var(--s-4); font-weight: 600; }\n"
    "  .race-kind .caret { font-size: var(--t-xs); color: var(--fg-faint); transition: transform var(--m-fast) var(--e-out); }\n"
    "  .race-name.open .race-kind { border-color: var(--accent); }\n"
    "  .race-name.open .race-kind .caret { transform: rotate(180deg); }\n"
    "  /* What it opens is a Tip: it floats, points at the chip, and holds nothing\n"
    "     to press, so it never takes a click meant for what is under it. It\n"
    "     carries a list rather than a label, so it takes the Note's padding, as\n"
    "     the reveal popup does. It hangs from the whole line rather than the\n"
    "     chip, so on a phone it can be as wide as the line is. */\n"
    "  .race-rules {\n"
    "    position: absolute; top: 100%; left: 0; z-index: 20;\n"
    "    width: min(320px, 100%); margin-top: var(--s-3);\n"
    "    display: grid; gap: var(--s-3); padding: var(--s-3) var(--s-4); line-height: 1.45;\n"
    "    opacity: 0; visibility: hidden;\n"
    "    transition: opacity var(--m-base) var(--e-out), visibility var(--m-base);\n"
    "  }\n"
    "  .race-name.open .race-rules { opacity: 1; visibility: visible; }\n"
    "  /* Hover only peeks; a tap is what keeps it open, because a phone has no\n"
    "     hover to lose. Put away while the pointer is still on the chip, the peek\n"
    "     sits out until the pointer leaves, or putting it away would do nothing. */\n"
    "  @media (hover: hover) {\n"
    "    .race-name:not(.shut) .race-kind:hover ~ .race-rules { opacity: 1; visibility: visible; }\n"
    "  }\n"
    "  /* The caret is a square stood on its corner, taking the Tip's own border\n"
    "     and ground, and it sits over the mode's word. */\n"
    "  .race-rules::before {\n"
    "    content: \"\"; position: absolute; top: calc(var(--s-3) / -2); left: var(--s-6);\n"
    "    width: var(--s-3); height: var(--s-3); background: var(--bg-3);\n"
    "    border-left: 1px solid var(--line-strong); border-top: 1px solid var(--line-strong);\n"
    "    transform: rotate(45deg);\n"
    "  }\n"
    "  .race-rules .rr-h {\n"
    "    font-size: var(--t-xs); text-transform: uppercase; letter-spacing: .1em;\n"
    "    color: var(--fg-faint); font-weight: 700; margin-bottom: var(--s-1);\n"
    "  }\n"
    "  .race-rules ul { list-style: none; margin: 0; padding: 0; }\n"
    "  @media (prefers-reduced-motion: reduce) {\n"
    "    .race-rules, .race-kind .caret { transition: none; }\n"
    "  }\n",
    "css")


# ---------------------------------------------------------------- the rules, once
once(
    "function renderRules(race) {\n"
    "  const host = $(\"rules\");\n"
    "  if (!race) { setHTML(host, \"\"); return; }\n"
    "  const bits = [];\n"
    "  bits.push(raceKind(race));\n"
    "  bits.push((LANGS.find(l => l[0] === race.lang) || [\"\", race.lang || \"en\"])[1]);\n"
    "  bits.push(race.show_positions === false ? \"positions hidden\" : \"positions shown\");\n"
    "  bits.push(race.allow_back === false ? \"no going back\" : \"back allowed\");\n"
    "  if (race.allow_find === false) bits.push(\"no find on page\");\n"
    "  if (race.peek) bits.push(\"target revealed\");\n"
    "  else if (race.allow_peek === false) bits.push(\"target stays hidden\");\n"
    "  if (race.time_limit) bits.push(Math.round(race.time_limit / 60) + \" min limit\");\n"
    "  bits.push(raceMode(race) === \"clicks\" ? \"fewest clicks wins\" : \"fastest time wins\");\n"
    "  if (race.lost) bits.push(\"lost: everyone starts somewhere different\");\n"
    "  if (race.ban_hubs) bits.push(\"no hub pages\");\n"
    "  if (allowTables(race)) bits.push(\"link tables allowed\");\n"
    "  if (raceToc(race)) bits.push(\"contents: \" + TOC_LABELS[raceToc(race)].toLowerCase());\n"
    "  const slots = raceSlots(race), stops = raceCheckpoints(race);\n"
    "  stops.forEach((c, i) => bits.push(\"via \" + c + (slots[i] ? \" (\" + slotName(slots[i], stops.length) + \")\" : \"\")));\n"
    "  if (Object.keys(race.handicaps || {}).length) bits.push(\"handicaps on\");\n"
    "  setHTML(host, bits.map(b => '<span class=\"pill rule\">' + esc(b) + \"</span>\").join(\"\"));\n"
    "}\n",
    "/* The rules a race was played under, grouped the way a player asks about\n"
    "   them. `text` is the line under a race's name afterwards; `pills` is the\n"
    "   wording on the strip beside the racers during it, which is terser and\n"
    "   leaves out what nobody needs reminding of mid-race. One list, so the two\n"
    "   can never tell different stories about one race. */\n"
    "function raceRules(race) {\n"
    "  if (!race) return [];\n"
    "  const groups = [];\n"
    "  const add = (group, text, ...pills) => {\n"
    "    let g = groups.find(x => x.group === group);\n"
    "    if (!g) groups.push(g = { group, items: [] });\n"
    "    g.items.push({ text, pills: pills.filter(Boolean) });\n"
    "  };\n"
    "\n"
    "  const clicks = raceMode(race) === \"clicks\";\n"
    "  add(\"Who wins\", clicks ? \"Fewest clicks wins\" : \"Fastest time wins\",\n"
    "      clicks ? \"fewest clicks wins\" : \"fastest time wins\");\n"
    "  if (race.time_limit) {\n"
    "    const min = Math.round(race.time_limit / 60);\n"
    "    add(\"Who wins\", min + (min === 1 ? \" minute\" : \" minutes\") + \" to finish\", min + \" min limit\");\n"
    "  }\n"
    "\n"
    "  const lang = (LANGS.find(l => l[0] === race.lang) || [\"\", race.lang || \"en\"])[1];\n"
    "  add(\"Route\", \"Language: \" + lang, lang);\n"
    "  if (race.lost) add(\"Route\", \"Everyone started somewhere different\", \"lost: everyone starts somewhere different\");\n"
    "  const stops = raceCheckpoints(race), slots = raceSlots(race);\n"
    "  if (stops.length) {\n"
    "    const list = stops.length > 1 ? stops.slice(0, -1).join(\", \") + \" and \" + stops[stops.length - 1] : stops[0];\n"
    "    add(\"Route\", \"Via \" + list,\n"
    "        ...stops.map((c, i) => \"via \" + c + (slots[i] ? \" (\" + slotName(slots[i], stops.length) + \")\" : \"\")));\n"
    "    const order = orderPhrase(stops, slots);\n"
    "    if (order) add(\"Route\", order.charAt(0).toUpperCase() + order.slice(1));\n"
    "  }\n"
    "  if (race.ban_hubs) add(\"Route\", \"Hub pages off-limits\", \"no hub pages\");\n"
    "\n"
    "  const hidden = race.show_positions === false, noBack = race.allow_back === false;\n"
    "  add(\"Allowed\", hidden ? \"Positions hidden\" : \"Everyone's position shown\", hidden ? \"positions hidden\" : \"positions shown\");\n"
    "  add(\"Allowed\", noBack ? \"No going back\" : \"Back button allowed\", noBack ? \"no going back\" : \"back allowed\");\n"
    "  add(\"Allowed\", race.allow_find === false ? \"No find on page\" : \"Find on page allowed\",\n"
    "      race.allow_find === false && \"no find on page\");\n"
    "  if (race.peek) add(\"Allowed\", \"Target opened by a vote\", \"target revealed\");\n"
    "  else if (race.allow_peek === false) add(\"Allowed\", \"Target hidden the whole race\", \"target stays hidden\");\n"
    "  else add(\"Allowed\", \"Target could be opened by a vote\");\n"
    "  add(\"Allowed\", allowTables(race) ? \"Tables of links shown\" : \"Tables of links hidden\",\n"
    "      allowTables(race) && \"link tables allowed\");\n"
    "  const toc = raceToc(race);\n"
    "  add(\"Allowed\", toc ? \"Contents: \" + TOC_LABELS[toc].toLowerCase() : \"No contents list\",\n"
    "      toc && \"contents: \" + TOC_LABELS[toc].toLowerCase());\n"
    "\n"
    "  // Handicaps are keyed by the normalised name; the name a player sees\n"
    "  // comes from their result, or from the standings if they sat it out.\n"
    "  const known = Object.values(race.results || {}).concat((S.snap && S.snap.leaderboard) || []);\n"
    "  Object.entries(race.handicaps || {}).sort((a, b) => b[1] - a[1]).forEach(([key, secs], i) => {\n"
    "    const who = (known.find(r => norm(r.name) === key) || { name: key }).name;\n"
    "    add(\"Handicaps\", who + \" started \" + secs + (secs === 1 ? \" second\" : \" seconds\") + \" behind\",\n"
    "        i === 0 && \"handicaps on\");\n"
    "  });\n"
    "  return groups;\n"
    "}\n"
    "\n"
    "function renderRules(race) {\n"
    "  const host = $(\"rules\");\n"
    "  if (!race) { setHTML(host, \"\"); return; }\n"
    "  const bits = [raceKind(race)].concat(...raceRules(race).map(g => g.items.flatMap(it => it.pills)));\n"
    "  setHTML(host, bits.map(b => '<span class=\"pill rule\">' + esc(b) + \"</span>\").join(\"\"));\n"
    "}\n"
    "\n"
    "/* A race's name, the way a player would say it: the mode, then the route.\n"
    "   A lost race had no shared start to name, so it is just where everyone\n"
    "   was going. */\n"
    "const raceRoute = (race) => race.lost ? \"→ \" + race.target : race.start + \" → \" + race.target;\n"
    "const raceTitle = (race) => raceKind(race) + \" · \" + raceRoute(race);\n"
    "\n"
    "/* Which race name has its rules open, by where it is drawn. Results is\n"
    "   redrawn on every snapshot, so the open state lives here rather than in\n"
    "   the markup, or the rules would snap shut under the reader. */\n"
    "let raceRulesOpen = \"\";\n"
    "\n"
    "/* The name with its mode as a Pill you can press, and the rules it opens. */\n"
    "function raceNameHTML(race, where) {\n"
    "  const open = raceRulesOpen === where, id = \"race-rules-\" + where;\n"
    "  return '<div class=\"hub-sub race-name' + (open ? \" open\" : \"\") + '\" data-where=\"' + where + '\">' +\n"
    "    '<button type=\"button\" class=\"pill race-kind\" aria-expanded=\"' + open + '\" aria-controls=\"' + id + '\">' +\n"
    "    esc(raceKind(race)) + ' <span class=\"caret\" aria-hidden=\"true\">▾</span></button>' +\n"
    "    '<span class=\"race-route\">' + esc(raceRoute(race)) + \"</span>\" +\n"
    "    '<div class=\"tip race-rules\" id=\"' + id + '\" role=\"group\" aria-label=\"The rules this race was played under\">' +\n"
    "    raceRules(race).map(g => '<div><div class=\"rr-h\">' + esc(g.group) + \"</div><ul>\" +\n"
    "      g.items.map(it => \"<li>\" + esc(it.text) + \"</li>\").join(\"\") + \"</ul></div>\").join(\"\") +\n"
    "    \"</div></div>\";\n"
    "}\n"
    "\n"
    "function setRaceRulesOpen(where) {\n"
    "  raceRulesOpen = where;\n"
    "  document.querySelectorAll(\".race-name\").forEach(el => {\n"
    "    const on = el.dataset.where === where;\n"
    "    const chip = el.querySelector(\".race-kind\");\n"
    "    if (!on && el.classList.contains(\"open\") && chip.matches(\":hover\")) el.classList.add(\"shut\");\n"
    "    el.classList.toggle(\"open\", on);\n"
    "    chip.setAttribute(\"aria-expanded\", String(on));\n"
    "  });\n"
    "}\n",
    "raceRules")


# ---------------------------------------------------------------- where races are named
once(
    "    '<p class=\"hub-sub\">' + esc(startLabel(race)) + \" → \" + esc(race.target) +\n"
    "    (raceCheckpoints(race).length ? \" · via \" + raceCheckpoints(race).map(esc).join(\", \") : \"\") +\n"
    "    \" · \" + (raceMode(race) === \"clicks\" ? \"fewest clicks\" : \"fastest time\") + \"</p>\";\n",
    "    raceNameHTML(race, \"results\");\n",
    "results header")

once(
    "      '<p class=\"hub-sub\">' + esc(startLabel(race)) + \" → \" + esc(race.target) + \"</p>\" +\n",
    "      raceNameHTML(race, \"replay\") +\n",
    "replay header")

once(
    "    setText($(\"lobby-last\"), \"Last race: \" + startLabel(last) + \" → \" + last.target);\n"
    "    setText($(\"lobby-rematch\"), \"Rematch: \" + startLabel(last) + \" → \" + last.target);\n",
    "    setText($(\"lobby-last\"), \"Last race: \" + raceTitle(last));\n"
    "    setText($(\"lobby-rematch\"), \"Rematch: \" + raceTitle(last));\n",
    "lobby")


# ---------------------------------------------------------------- opening and closing
once(
    "  else if (!$(\"reveal-tip\").hidden) { hideRevealTip(); ev.preventDefault(); }\n"
    "});\n",
    "  else if (!$(\"reveal-tip\").hidden) { hideRevealTip(); ev.preventDefault(); }\n"
    "  else if (raceRulesOpen) { setRaceRulesOpen(\"\"); ev.preventDefault(); }\n"
    "});\n"
    "\n"
    "/* The rules under a race's name: pressing the mode keeps them open, and\n"
    "   pressing it again or anywhere else puts them away. Hover only peeks, and\n"
    "   that is the stylesheet's job. */\n"
    "document.addEventListener(\"click\", (ev) => {\n"
    "  const chip = ev.target.closest(\".race-kind\");\n"
    "  const where = chip ? chip.closest(\".race-name\").dataset.where : \"\";\n"
    "  const next = where && where !== raceRulesOpen ? where : \"\";\n"
    "  if (next !== raceRulesOpen) setRaceRulesOpen(next);\n"
    "});\n"
    "document.addEventListener(\"pointerout\", (ev) => {\n"
    "  const chip = ev.target.closest && ev.target.closest(\".race-kind\");\n"
    "  if (chip && !chip.contains(ev.relatedTarget)) chip.closest(\".race-name\").classList.remove(\"shut\");\n"
    "});\n",
    "handlers")

io.open(UI, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
