# -*- coding: utf-8 -*-
"""The side panel can be resized, and its rules strip stops growing (issue #35).

- The panel was a fixed 330px. It is now narrower by default (270px) and has an
  edge you can pull, press an arrow key on, or double-click to put back. The
  width is a variable on #app so a drag sets one number, and it is kept on this
  machine like the theme: it is about the screen in front of you.
- The rules under Racers were a wrapping row of pills that grew with the race
  until it pushed the racers and the standings off the screen. The pills are a
  step tighter, and the strip stops at about four rows and scrolls inside
  itself.
- On a phone the panel is a drawer and has no edge to pull, so the handle is
  hidden there and the drawer keeps the width it had.

The grip sits inside the panel's own column, over its left border, rather than
straddling it: half of it would otherwise cover the article's scrollbar. Since
it takes the panel's cell in the grid, the panel is placed in that cell
explicitly - left to auto-placement it would be pushed down a row.

Run from anywhere; it asserts each anchor appears exactly once and writes
nothing if one does not.
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


# ---- the column, and the panel's place in it ----
once("""  /* minmax(0, 1fr) rather than 1fr: a plain 1fr refuses to go narrower than
     its content, and one wide Wikipedia table is enough to push the whole
     layout past the edge of a phone screen. */
  #app {
    display: grid; grid-template-columns: minmax(0, 1fr) 330px;
    grid-template-rows: auto 1fr; height: 100%;
  }""",
"""  /* minmax(0, 1fr) rather than 1fr: a plain 1fr refuses to go narrower than
     its content, and one wide Wikipedia table is enough to push the whole
     layout past the edge of a phone screen.

     The side panel's width is a variable so that a drag only has to set one
     number. The clamp is here as well as in the script because a width saved in
     a wide window has to stay sane in a narrow one: the article keeps at least
     half the screen. These are layout widths, which the type and space scales
     do not cover. */
  #app {
    --side-w: 270px;
    display: grid; grid-template-columns: minmax(0, 1fr) clamp(220px, var(--side-w), 50vw);
    grid-template-rows: auto 1fr; height: 100%;
  }""", "app grid")

once("""  #side {
    border-left: 1px solid var(--line); background: var(--bg-2);
    overflow-y: auto; overflow-x: hidden;
  }
""",
"""  /* Placed by hand because the grip below shares its cell: left to auto-placement
     the panel would be pushed down a row. */
  #side {
    grid-column: 2; grid-row: 2;
    border-left: 1px solid var(--line); background: var(--bg-2);
    overflow-y: auto; overflow-x: hidden;
  }
  /* The edge you pull to resize it. It lives inside the panel's column, over
     its border, so it never covers the article's scrollbar. */
  #side-grip {
    grid-column: 2; grid-row: 2; justify-self: start;
    position: relative; z-index: 2; width: var(--s-2);
    cursor: col-resize; touch-action: none;
  }
  /* A line, like a border, so it is a width rather than a space. */
  #side-grip::after {
    content: ""; position: absolute; inset: 0 auto 0 0; width: 2px;
    background: transparent; transition: background var(--m-fast);
  }
  #side-grip:hover::after, #side-grip:focus-visible::after, #side-grip.drag::after { background: var(--accent); }
  #side-grip:focus-visible { outline: none; }
  /* While pulling, the pointer is often off the edge, over the article. */
  body.resizing { cursor: col-resize; user-select: none; }
""", "side + grip css")

# ---- the rules strip ----
once("""  #rules { display: flex; flex-wrap: wrap; gap: var(--s-2); margin-bottom: var(--s-3); }
  #rules:empty { margin: 0; }
  /* A Pill, compact: a race can carry half a dozen rules. */
  .rule { font-size: var(--t-xs); padding: var(--s-1) var(--s-3); color: var(--fg-dim); }""",
"""  /* A race can carry a dozen rules, and the panel has racers and standings to
     show as well, so the strip stops at four rows and a bit of a fifth - the
     bit being what says it scrolls - and scrolls inside itself. */
  #rules {
    display: flex; flex-wrap: wrap; gap: var(--s-1); margin-bottom: var(--s-3);
    max-height: 110px; overflow-y: auto; scrollbar-width: thin;
  }
  #rules:empty { margin: 0; }
  /* A Pill, compact: a race can carry half a dozen rules. */
  .rule { font-size: var(--t-xs); line-height: 1.3; padding: var(--s-1) var(--s-2); color: var(--fg-dim); }""", "rules css")

# ---- a phone has a drawer, not an edge ----
once("""    /* The sidebar slides in over the article instead of stealing space. */
    #side {""",
"""    /* The drawer is one width, so there is no edge to pull. */
    #side-grip { display: none; }

    /* The sidebar slides in over the article instead of stealing space. */
    #side {""", "mobile grip")

# ---- the handle ----
once("""      <div id="feed"><div class="empty">Nothing yet.</div></div>
    </div>
  </div>
</div>
""",
"""      <div id="feed"><div class="empty">Nothing yet.</div></div>
    </div>
  </div>

  <!-- The edge of the side panel: pull it to change how wide the panel is. -->
  <div id="side-grip" role="separator" aria-orientation="vertical" aria-label="Side panel width"
       aria-valuemin="220" aria-valuemax="480" tabindex="0"
       title="Drag to resize, double-click to reset"></div>
</div>
""", "grip markup")

# ---- what the handle does ----
once("""$("lobby-start").onclick = openModePicker;
""",
"""/* The side panel's edge is a handle: drag it, press an arrow key on it, or
   double-click it to put the width back. The width is a preference about the
   screen in front of you, so like the theme it stays on this machine. The
   stylesheet clamps it to half the window as well, which is why a width saved
   in a big window is safe in a small one - and why it is not rewritten when
   the window shrinks. */
const SIDE_W = { min: 220, max: 480, step: 15 };

(function sideResize() {
  const grip = $("side-grip"), app = $("app");
  const limit = () => Math.min(SIDE_W.max, Math.floor(window.innerWidth / 2));
  const clamp = (w) => Math.max(SIDE_W.min, Math.min(limit(), Math.round(w)));
  const shown = () => Math.round($("side").getBoundingClientRect().width);
  const sync = () => grip.setAttribute("aria-valuenow", String(shown()));
  const remember = (w) => {
    try {
      if (w === null) localStorage.removeItem("wr_side");
      else localStorage.setItem("wr_side", String(w));
    } catch (e) { /* storage blocked - it just won't be remembered */ }
  };
  // null puts back the stylesheet's own width.
  const set = (w, keep) => {
    if (w === null) app.style.removeProperty("--side-w");
    else app.style.setProperty("--side-w", w + "px");
    if (keep !== false) remember(w);
    sync();
  };

  grip.addEventListener("pointerdown", (ev) => {
    if (ev.button !== 0) return;
    ev.preventDefault();
    const from = ev.clientX, start = shown();
    let now = start;
    grip.setPointerCapture(ev.pointerId);
    grip.classList.add("drag");
    document.body.classList.add("resizing");
    // The panel is on the right, so pulling left makes it wider.
    const move = (e) => { now = clamp(start + from - e.clientX); set(now, false); };
    const done = () => {
      grip.classList.remove("drag");
      document.body.classList.remove("resizing");
      grip.removeEventListener("pointermove", move);
      grip.removeEventListener("pointerup", done);
      grip.removeEventListener("pointercancel", done);
      if (now !== start) remember(now);
    };
    grip.addEventListener("pointermove", move);
    grip.addEventListener("pointerup", done);
    grip.addEventListener("pointercancel", done);
  });
  grip.addEventListener("keydown", (ev) => {
    const dir = ev.key === "ArrowLeft" ? 1 : ev.key === "ArrowRight" ? -1 : 0;
    if (!dir) return;
    ev.preventDefault();
    set(clamp(shown() + dir * SIDE_W.step));
  });
  grip.addEventListener("dblclick", () => set(null));
  window.addEventListener("resize", sync);

  try {
    const saved = parseInt(localStorage.getItem("wr_side"), 10);
    if (saved) set(clamp(saved), false);
  } catch (e) { /* ignore */ }
  sync();
})();

$("lobby-start").onclick = openModePicker;
""", "script")

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("ok")
