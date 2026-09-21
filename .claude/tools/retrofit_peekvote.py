# -*- coding: utf-8 -*-
"""Bring the peek sheet and the vote card onto the design language.

These are the two Panels the standard had in mind when it moved panels from
10px to 16px: both were rounded by the old --radius, less than the cards and
controls inside them.

- The vote card is a dialog like the others, so it takes .panel: the dialogs'
  surface instead of the page's, their padding and their corners. Its rows of
  votes are Rows in a Card, like every other list of people in the game.
- The peek sheet holds a Wikipedia article, so it stays a flush sheet on the
  page's own ground and does not take .panel's padding or surface; it takes
  the Panel's corners and shadow. Its body - where the article is drawn - is
  the reading surface, and like the race's own article view it is the
  standard's carve-out and keeps its padding.
"""
import io
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ui.html")

with io.open(PATH, encoding="utf-8", newline="") as f:
    s = f.read()


def once(old, new, label):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    s = s.replace(old, new)


once("""    display: flex; align-items: center; justify-content: center; padding: 20px;
  }
  #peek-sheet {
    display: flex; flex-direction: column; width: min(900px, 100%); height: 100%;
    background: var(--bg); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: 0 20px 60px var(--shadow);
    overflow: hidden;
  }
  #peek-head {
    display: flex; align-items: center; gap: 12px; flex: none;
    padding: 12px 16px; border-bottom: 1px solid var(--line); background: var(--bg-2);
  }
  #peek-head .who { flex: 1; min-width: 0; }
  #peek-head .who b { font-size: 15px; }
  #peek-head .who div { font-size: 11.5px; color: var(--fg-faint); margin-top: 2px; }""",
     """    display: flex; align-items: center; justify-content: center; padding: var(--s-6);
  }
  /* A Panel that holds an article: flush, and on the page's own ground rather
     than the dialogs', so the reading looks like the reading. */
  #peek-sheet {
    display: flex; flex-direction: column; width: min(900px, 100%); height: 100%;
    background: var(--bg); border: 1px solid var(--line);
    border-radius: var(--r-panel); box-shadow: var(--el-float);
    overflow: hidden;
  }
  #peek-head {
    display: flex; align-items: center; gap: var(--s-4); flex: none;
    padding: var(--s-4) var(--s-5); border-bottom: 1px solid var(--line); background: var(--bg-2);
  }
  #peek-head .who { flex: 1; min-width: 0; }
  #peek-head .who b { font-size: var(--t-md); }
  #peek-head .who div { font-size: var(--t-xs); color: var(--fg-faint); margin-top: var(--s-1); }""",
     "peek sheet")

once("""  #vote-card {
    width: min(430px, 100%); background: var(--bg); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: 0 20px 60px var(--shadow); padding: 20px;
  }
  #vote-card h3 { margin: 0 0 8px; font-size: 17px; }
  #vote-card .why { font-size: 13px; color: var(--fg-dim); line-height: 1.55; margin-bottom: 14px; }
  #vote-tally { margin-bottom: 16px; }
  .vote-row {
    display: flex; align-items: center; gap: 9px; padding: 6px 0;
    border-bottom: 1px solid var(--line-soft); font-size: 13.5px;
  }
  .vote-row:last-child { border-bottom: none; }
  .vote-row .nm { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .vote-row .st { font-size: 12px; color: var(--fg-faint); }""",
     """  /* A Panel; what is its own is the width. */
  #vote-card { width: min(430px, 100%); }
  #vote-card h3 { margin: 0 0 var(--s-3); font-size: var(--t-lg); }
  #vote-card .why { font-size: var(--t-sm); color: var(--fg-dim); line-height: 1.55; margin-bottom: var(--s-5); }
  #vote-tally { margin-bottom: var(--s-5); }
  .vote-row .nm { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .vote-row .st { font-size: var(--t-xs); color: var(--fg-faint); }""",
     "vote card")

once("""    <div id="vote-card">""",
     """    <div id="vote-card" class="panel">""",
     "vote card markup")
once("""<button id="vote-close" class="ghost" style="width:100%;margin-top:8px">Decide later</button>""",
     """<button id="vote-close" class="ghost" style="width:100%;margin-top:var(--s-3)">Decide later</button>""",
     "decide later")
once("""        return '<div class="vote-row ' + cls + '"><span class="st">'""",
     """        return '<div class="row in-card vote-row ' + cls + '"><span class="st">'""",
     "vote row markup")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print("peek sheet and vote card retrofitted")
