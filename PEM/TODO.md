# PEM — deferred work / open questions

A catalogue of loose ends still in the tree as of the 2026-05 refactor: things
deliberately left for later, dormant features, small cleanups, and the
in-source `TODO`/`XXX` markers worth a decision. Each item is "implement or
abandon" — nothing here is load-bearing. Companion to `PEM_REFACTOR_PLAN.md`
(repo root), which tracks the refactor itself.

---

## 1. Refactor follow-ups

- **Split `pemlib/pyshell.py`.** `ModifiedInterpreter`, `PyShell`, and
  `main()` still share one ~2 kloc module. Splitting (e.g. `shell/interpreter.py`
  + `shell/pyshell.py` + a small `shell/app.py` for `main()`) was judged
  valuable-but-riskier and skipped. — *implement or abandon*
- **Trim `pyshell.main()`'s dead CLI parsing.** PEM always launches it as
  `pyshell.main()` with `argv = ["PEM", "-e", <file?>]`. The `-n` (no
  subprocess), `-s`/`PEMSTARTUP`/`PYTHONSTARTUP`, `-i`, `-c cmd`, `-r file`,
  and `-` (stdin) branches — plus the long `usage_msg` string — are inherited
  from IDLE and unreachable in normal use. Decide whether to keep `-n`
  (no-subprocess mode still half-works) and delete the rest, or leave it. —
  *implement or abandon*
- **`perflog.py` once the dust settles.** The `PEM_PERF`-gated latency
  harness (`pemlib/perflog.py` + `perflog.mark(...)` calls scattered through
  `pyshell.py`, `execution/run.py`, `editing/editor.py`, `editing/runscript.py`)
  exists to diagnose the startup-lag refactor. Decide: keep as a permanent
  diagnostic, gate it tighter, or strip it out (and the call sites). —
  *implement or abandon*
- **Test suite.** The IDLE-derived `pemlib/pem_test/` was removed (mostly
  broken pre-refactor, not worth fixing piecemeal). A fresh suite is to be
  written later — both for the new machinery (pre-warm spare pool,
  `restart_subprocess` promotion, `active_sink` output routing, the per-tab
  output pane) and for whatever editor behaviour is worth pinning down.
- **Dead `if __name__ == '__main__'` blocks.** ~45 modules still end with an
  `if __name__ == '__main__': ... main('pemlib.pem_test.test_X', ...)`
  (and some `from pemlib.pem_test.htest import run`) block, inherited from
  IDLE — now importing a package that no longer exists. Inert in normal use
  (only runs on `python -m pemlib.<x>`), but cruft. Strip them, or leave
  until the new test suite lands. — *implement or abandon*

## 2. Dormant / non-functional features

- **Create Executable in the frozen PEM app.** The feature works in
  pip-installed PEM (and from source); the frozen app leaves out its menu item
  and Preferences section (`pem.isFrozen()`). Running PyInstaller inside the
  frozen app fails: the app's Python modules are compiled into it, and
  PyInstaller needs them as files on disk. If revisited, options are to
  assemble the student's program from PEM's own compiled runtime (PyInstaller's
  archive reader/writer), or have PEM set up a real Python build environment on
  first use. Meanwhile PEM.app still bundles PyInstaller (and `PEM.py`'s
  `_child.py` route) only for nested builds — remove them if this stays out.
  — *implement or abandon*
- **`OnDemandOutputWindow`** in `pemlib/shell/outwin.py` — a dead class with
  a `# These classes are currently not used but might come in handy` header. —
  *abandon (delete) unless a use appears*
- **Pause-while-running.** `('_Pause', '<<pause>>')` is commented out in
  `mainmenu.py` ("functionality not yet implemented"). There is no Pause
  mechanism for a running subprocess. — *implement or abandon*
- **`codecontext` / `zoomheight`** (`pemlib/editing/`) are active, working
  features but have no menu items (the whole `('options', [...])` cascade in
  `mainmenu.py` is commented out, as is the Format cascade). Decide whether to
  surface them in a menu or leave them keyboard/preference-only. — *implement or
  abandon*
- **Turtle Demo menu item** — commented out at the bottom of `mainmenu.py`
  (`# if find_spec('turtledemo'): ...`). — *implement or abandon*

## 3. Small cleanups

- **`Icons/` vs `icons/` directory case duplication.** `pemlib/` has both
  `Icons/` (app icons, read by `help_about.py` and `pyshell.main()`) and
  `icons/` (toolbar glyphs, read by `editing/editor.py`). On a
  case-insensitive filesystem these collide; consolidate to one. — *implement or
  abandon*
- **About dialog still half-IDLE.** `pemlib/help_about.py` shows
  "Python's Integrated Development and Learning Environment", a `discuss.python.org`
  link, and a `docs.python.org/.../pem.html` link (no such page). The
  Readme/News/Credits buttons read `pemlib/README.txt` / `News3.txt` /
  `CREDITS.txt`, which are still the IDLE-derived files. Rewrite the dialog and
  those three text files for PEM, or trim the dialog down. — *implement or
  abandon*
- **Error-message strings that point at IDLE docs.** `ModifiedInterpreter`'s
  `display_no_subprocess_error` / `display_port_binding_error` reference
  `docs.python.org/3/library/pem.html` and "Run PEM with the -n command
  line switch ... Help/PEM Help 'Running without a subprocess'". Reword or
  point somewhere real. — *implement or abandon*
- **`config/configdialog.py:82`** — `# XXX Decide whether to keep or delete
  these key bindings.` (an inherited IDLE marker, but a real decision). —
  *implement or abandon*

## 4. In-source `TODO` / `XXX` markers

### PEM-authored or PEM-relevant

- `pemlib/mainmenu.py:19` — `# TODO: Make this more robust` (the
  `macosx.overrideRootMenu` mutates `menudefs` in place; fragile).
- `pemlib/mainmenu.py:75` — `('_Pause', ...)` — see §2.
- `pemlib/mainmenu.py` §60-69, §92-98 — commented-out Format and Options
  cascades — see §2.
- `pemlib/shell/sidebar.py:42` — `# TODO: use also in codecontext.py`
  (the line-number gutter width logic could be shared).
- `pemlib/shell/sidebar.py:100` — `"""Placeholder for color synchronization
  in subclasses."""` — `update_colors` base method is a no-op.
- `pemlib/util.py:9-13` — the module docstring's `TODO:` list (consolidate
  more cross-module shared bits — Python/tk version strings, std streams,
  warnings helpers — into `util.py`). Inherited from idlelib but still applies.

### Inherited from idlelib (low priority — present in upstream too)

These came in with the IDLE fork and aren't PEM-specific; listed for
completeness, almost certainly *abandon* unless touching that code anyway:

- `pemlib/pyshell.py:72` — `PORT = 0  # someday pass in host, port for
  remote debug capability`.
- `pemlib/pyshell.py:1084` — `# XXX KBK 27Dec07 use text viewer someday, but
  must work w/o subproc` (paging `help()` output).
- `pemlib/config/config.py` — ~12 `# TODO`/`XXX` markers (lines 26, 55, 160,
  212, 308, 441, 471, 548, 584, 603, 872, 878) — config-system robustness and
  test-coverage notes from 2014.
- `pemlib/searching/search.py:68` — `# TODO - why is this here and not in a
  create_command_buttons?`.
- `pemlib/searching/replace.py:150` — `# XXX ought to replace circular
  instead of top-to-bottom when wrapping`.
- `pemlib/execution/rpc.py:301,522,621` — `# XXX Check for other types`,
  a stray `## cgt xxx`, and `# XXX KBK 09Sep03 We need a proper unit test`.
- `pemlib/text/format.py:119,137,152,171` — paragraph-reformatting niceties.
- `pemlib/text/percolator.py:8,57` — Delegator inheritance / API musings.
- `pemlib/text/parenmatch.py:28`, `pemlib/text/undo.py:94` — minor notes.
- `pemlib/editing/tree.py` (header `# XXX TO DO:` plus lines 194, 201, 233,
  237, 420) and `pemlib/editing/browser.py` (header `XXX TO DO:`) — the
  module/class browser widgets; geometry constants, leaked bindings, missing
  icons.
- `pemlib/dialogs/query.py:202` — `# XXX Ought to insert current file's
  directory in front of path.` (the "run with args" path-entry dialog).
- `pemlib/shell/outwin.py:135` — `# XXX Should use PemPrefs.ColorPrefs`
  (inside the dead `OnDemandOutputWindow` — moot if that's deleted).
