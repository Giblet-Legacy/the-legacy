# CHANGELOG — the-legacy (Tier 1: The Legacy)

CHANGELOG.md — build history for The Legacy, latest entry at top.

## [Unreleased]

### Frozen 2026-11-20 (James: "freeze then plan 2.0.0 consolidation")

- legacy_v1_12.py + boot_v1_12.py 1.12.0 (SPEC_V1_12.md), with
  static/projection_v1_12.html. VERSION 1.11.0 -> 1.12.0. The names already say
  the version (roadmap NAMING.md): `_v1_12` is 1.12.0, as the Cockpit's
  `forge_cli_v1_8` is 1.8.0.
- test_unfrozen_is_marked_dev became test_frozen_at_1_12_0.
- Bad: frozen before James has seen a real Gemini answer through the page; the
  relay is tested against a stub gate and smoke-tested without a key.
- Bad: it depends on ai-gate 0.1.0, which is still 0.1.0-dev. The relay pins
  only the gate's HTTP paths (/api/<allowed>), so ai-gate can freeze later.
- Next: the 2.0.0 consolidation (CONSOLIDATION_V2.md, planned, not started).

### Built 2026-11-19 (James: "now lets integrate the ai into our interface")

- legacy_v1_12.py + boot_v1_12.py + static/projection_v1_12.html (SPEC_V1_12.md,
  1.12.0-dev): an "Ask the AI" card.
  - The Legacy relays /api/ai/* to ai-gate's local API (ai_gate_serve.py): reads
    from an allowlist only; asks and ratings behind the v4 guard; no seal relay.
  - Every answer is shown as an ASSUMPTION with its status, conflicts and open
    questions, a 1-5 rating, the AI's λ, and the terminal seal command.
  - boot_v1_12 starts the Field, ai-gate and the Legacy.
  - test_legacy_v1_12.py: 8 tests, red first.
  - Smoke-tested on spare ports against the real forge.db: the relay works, and an
    ask without GEMINI_API_KEY is refused with that message.
- The page as seven views behind a sidebar (SPEC_V1_12 §2.1; James: "its very busy now
  and not very fluid"):
  - Home leads with "Needs you", with badges on Home, Ask and Create;
  - only the open view refreshes, and the Field loads when first opened;
  - keys 1-7, addresses #home … #system, and the last view remembered;
  - Ask has threads on the left and its history.
  Every 1.11 card is kept. Checked in headless Edge at desktop and phone widths (no
  horizontal overflow). test_legacy_v1_12.py: 9 tests.
- Claims merged into Ask (James: "should ask and claim be the same thing … pull claims and generate
  reports"; he chose the AI on demand only, and the thread's scope only).
  - One question box: Ask (local: the scope's signed claims via ai-gate /api/known, plus the
    Voice); Explain with AI and Report (through the gate, as assumptions; reports have cited
    sections and a Download .md button).
  - Faces and the claims table sit under "Browse all claims". Six views, keys 1-6.
  - Checked live on spare ports against the real forge.db: scope James Gilbert gave 84 signed
    claims, ranked, and the Voice answered, with no key and nothing sent.
- Bad: no real Gemini answer has been seen yet. That needs James's key and model id.

### Frozen 2026-11-18 (James: "freeze")

- legacy_v1_11.py + boot_v1_11.py 1.11.0 (SPEC_V1_11.md), with Cockpit
  forge_cli_v1_8.py 1.8.0. VERSION 1.10.0 -> 1.11.0. Named for the
  version they ship (roadmap NAMING.md; James: "we need consistency"):
  built as legacy_v13 / boot_v8 / SPEC_V15 / test_legacy_v13 /
  projection_v11, renamed before the freeze. The entry below uses the new
  names. The frozen legacy_v2-v12, boot_v2-v7 and SPEC_V2-V14 keep their
  counter names until the 2.0.0 consolidation.
- The VPS's run-latest picked "highest boot_vN with a plain number", so
  it would never see boot_v1_11.py. run_latest_v2 (forge-vps) picks by
  the header Version instead.

### Built 2026-11-18 (James: "yes do the legacy layer v1.8")

- legacy_v1_11.py + boot_v1_11.py + static/projection_v1_11.html (SPEC_V1_11.md,
  1.11.0): the Legacy v12 with the Cockpit moved from v1.7 to v1.8
  (explorer-d334-forge 1.8.0). New drafts get a created_at after every
  pending one; /api/inbox and the drafted half of /api/nouns come in the
  order written; the page's commit hint names forge_cli_v1_8.py. Fixes
  v1.7's hash order for drafts written in the same millisecond (shown
  against v12: six drafts posted with the clock frozen came back out of
  order). test_legacy_v1_11.py, 5 tests, run red first.

### Docs 2026-11-18 (no code change)

- `docs/ancestor-the-full-stack.md` and `docs/ancestor/the-full-stack-README.md`:
  the-full-stack kept as the Legacy's ancestor, reference only (James:
  "the forge stack was for reference only and not meant to be a layer
  involved in the legacy program … a doc created or the readme used and
  stored in docs as an ancestor"). The README is byte-identical to
  JamesTheGiblet/the-full-stack at 387220b (sha256 33e81191…2a2ac2).

### Frozen 2026-11-16 (James: "freeze all")

- legacy_v12.py + boot_v7.py 1.10.0 (SPEC_V14.md), with Cockpit
  forge_cli_v1_7.py 1.7.0. VERSION 1.9.0 -> 1.10.0. 73/74 on the laptop:
  the failure is `test_legacy_v8.py::test_boot_end_to_end` (NOTES Q18,
  the known race), which passed when re-run alone. All 7 v12 tests pass.
  The VPS's run-latest picks boot_v7 up at its next refresh (within the
  hour), so the tabs reach the tailnet page without a step on the VPS.

### Good

- `legacy_v12.py`, `boot_v7.py`, `static/projection_v10.html`, `SPEC_V14.md`,
  `test_legacy_v12.py` (7 tests, run red first): the "New claim" card is "New",
  with tabs for an Entity (a name), a Subject (a name, its entity from a
  drop-down) and a Claim (its subject, or an entity, from a drop-down). The
  drop-downs come from `GET /api/nouns` (P9 v4 plus pending drafts, marked
  "(draft)"); every tab saves a draft for `forge_cli_v1_7.py inbox commit`.
  Checked in headless Edge on demo data: one form per tab, drop-downs filled.
  73/74 (Q18's race the only failure). James, 2026-11-16.

### Ugly

- The first render showed all three forms at once: `form.grid` set
  `display: grid` and beat the `hidden` attribute. Fixed with
  `form.grid[hidden] { display: none; }`, and the page test checks for it.

### Frozen 2026-11-16 (James: "commit and push and freeze")

- boot_v5.py 1.8.0 (SPEC_V12.md) and legacy_v11.py + boot_v6.py 1.9.0
  (SPEC_V13.md). VERSION 1.7.0 -> 1.9.0. 67/67 on the laptop; v11 in use on
  the VPS from the S24 and the PC. The Field they start (scp-substrate
  serve_v8) is not frozen yet (NOTES Q17).
- At the freeze, 66/67: `test_legacy_v8.py::test_boot_end_to_end` fails
  intermittently (3 of 5 runs alone), a race in that test, not in the
  frozen layers; it touches only boot.py and legacy_v8 (NOTES Q18). All
  8 v11 tests pass.

### Good

- `legacy_v11.py`, `boot_v6.py`, `SPEC_V13.md`, `test_legacy_v11.py`
  (8 tests, run red first): one link (James, 2026-11-16: "i would
  prefer just a single weblink"). `/api/field` gives the page
  `FORGE_FIELD_PUBLIC_URL` (a `/` path or an http(s) URL; anything else
  ignored) while the health probe still uses `FORGE_FIELD_URL`, so on
  the VPS the embedded Field is `/field/` on the Legacy's own tailnet
  address. No variable, no change: a laptop behaves as v10. 67/67.
  Not frozen.
- `boot_v5.py`, `SPEC_V12.md`, `test_boot_v5.py` (1 test, run red
  first): boot_v4 with the Field v8 (scp-substrate SPEC_V8.md), so
  James is the centre of the embedded Field and his projects orbit him.
  boot_v4 untouched. Built on James's delegation. Not frozen (NOTES).

### Bad

- `test_legacy_v8.py::test_boot_end_to_end` failed once in a full run
  (2026-11-16) and passed alone and on rerun: it waits on real child
  processes, so it is timing-sensitive. Flaky, not broken.
- `test_legacy_v8.py::test_boot_end_to_end` (frozen v1.4.0, real servers
  on real ports) failed in 2 of 4 full runs on the laptop on 2026-11-15
  and passed in the other two; boot_v5 does not touch it. Flaky on
  timing, not fixed here.

### Ugly

- (none)

## [v1.7.0 (with v1.4.0, v1.5.0 and v1.6.0)] — 2026-11-14 — FROZEN

### Good

- `legacy_v10.py`, `boot_v4.py`, `SPEC_V11.md`, `test_legacy_v10.py`
  (3 tests, run red first): the Briefing through the Weaver v1.4, so
  each open question gets its own engine line. v10's handler serves
  /api/weaver itself; v7 is not replaced (a first try that swapped v7's
  Weaver at import also changed the frozen v7 tests' Weaver in the same
  run, and was replaced). `python boot_v4.py` starts the Field v7 then
  The Legacy v10. Checked live on James's data. 58/58 pass. Not frozen
  (NOTES Q14).
- `legacy_v9.py`, `static/projection_v9.html`, `boot_v3.py`,
  `SPEC_V10.md`, `test_legacy_v9.py` (3 tests, run red first against a
  plain copy of the v8 page): on a phone the Claims and Ledger tables
  drop their ID/Hash/Prev columns, so the text gets the width (v8
  squeezed it to three or four letters a line); grid columns never grow
  past their share; hints name boot_v3 and serve_v7. `python boot_v3.py`
  starts the Field v7 then The Legacy v9. 55/55 pass. Built on James's
  delegation ("take a bunch of screenshots and report", "yes"). Not
  frozen (NOTES Q13).
- `boot_v2.py`, `SPEC_V9.md`, `test_boot_v2.py`: boot.py with SCP
  Substrate serve_v6 as the Field. Run `python boot_v2.py`. Built, not
  frozen (NOTES Q12).
- `boot.py`: starts the Field (serve_v5, quiet), waits until it answers,
  then starts The Legacy (v8) pointed at it, and keeps both running; a
  child that stops is restarted after 1 s, 2 s, 4 s ... 60 s, and the
  count resets after a minute up. Ctrl-C stops both. Checked live: the
  Field killed at 11:22:08 was back at 11:22:10.
- `legacy_v8.py`, `static/projection_v8.html`, `SPEC_V8.md`,
  `test_legacy_v8.py` (5 tests, run red first, one end to end through
  boot.py): the status routes keep their last good answer and serve it
  marked stale when a fresh read fails; every panel on the page
  refreshes itself, backs off exponentially while a source is down and
  keeps its last good data; the Field panel waits for the Field and
  loads it as soon as it is up; claims are fetched with limit=500, so
  the panel and the face counts cover every claim (v7 showed 60 of 117).
- 51/51 pass. legacy.py and v2-v7 untouched. Built on James's delegation
  ("boot one after another and have exponential cool off and refresh
  and hold a buffer"). Not frozen (NOTES Q11).

### Bad

- My screenshot report said the page ran off a phone's right edge.
  Wrong: headless Edge will not make a window narrower than about 500
  px, so the "412 px" shot was a 496 px page cut short. Measured in a
  true 412 px frame the cards fit; the real fault was the squeezed text.
- On Windows, killing boot.py itself (not Ctrl-C) leaves its two
  children running; Ctrl-C in the console stops all three.

### Ugly

- projection_v8.html is v7's page with its loaders rewritten through one
  `poll` helper; the rest of the page is copied.

## [v1.3.0] — 2026-11-13 — FROZEN

### Good

- `SPEC_V7.md`, `test_legacy_v7.py` (4 tests, run red first),
  `legacy_v7.py` and `static/projection_v7.html`: the LLLM wired through.
  The Voice panel uses LLLM v0.1.2 (a claim's signed text; a subject's
  aspects one per line), the Morning Briefing uses Weaver v1.3 (present
  whenever there are UNKNOWN claims, engine or not), and `/api/lllm`
  and `/api/cockpit` use Cockpit v1.3 (engine via LLLM_CLI or PATH).
  Hints name forge_cli_v1_3 and serve_v4.
- 46/46 pass. legacy.py and v2-v6 untouched. Built on James's
  delegation ("make sure [the LLLM] is properly wired in"). Frozen at 1.3.0 (James: "freeze commmit and push", 2026-11-13); laptop run, S24 run
  still to be confirmed.

### Bad

- v7 depends on four layers built the same day: Cockpit v1.3, Weaver
  v1.3, LLLM v0.1.2 and (for the hint) SCP Substrate v4; all frozen with
  it, on the laptop run only.

### Ugly

- projection_v7.html is a copy of v6's page with three changes, so the
  page is not shared between versions.

## [v1.2.0] — 2026-11-13 — FROZEN

### Good

- `SPEC_V6.md`, `test_legacy_v6.py` (4 tests, run red first), `legacy_v6.py` and `static/projection_v6.html`: the six fixes James agreed after seeing one multi-face cube per repo. Faces filled counts every filled face (69 on 24 cubes, not "FACT 24"); the Claims table has a Subject column and lists each cube's other faces; the Ledger has All / Claims / Seals / Proposals filters (`/api/chain?kind=`); suggestions ask "what is the <subject>?"; LLLM opinions moved under Claims; the Field hint names `serve_v3.py` (closes NOTES Q8 for v6). Claims and Ledger are full width. 42/42 pass.
- Built as a layer: v5's files are exactly as committed (checked byte for byte); the v6 page started as a copy of v5's.
- Frozen at 1.2.0 (James: "freeze", 2026-11-13).

### Bad

- Frozen on the laptop run alone (2026-11-13). v6 was not yet pushed when James
  tested on the phone, so its S24 run is still to be confirmed.

### Ugly

- `/api/claims` reads the P9 claim list twice per request (v5's rows, then the faces). Fine at this size.

## [v1.1.0] — 2026-11-13 — FROZEN

### Good

- `SPEC_V5.md`, `test_legacy_v5.py` (4 tests, run red first), `legacy_v5.py` and `static/projection_v5.html`: The Projection redesigned after James's "boring and uninspired" and "still not right try modern clean and technical": a clean technical console (status bar, metrics, layer grid, claims by face, Query for the Voice, Ledger and Claims tables, Field, New claim with the Echo result, Network, Briefing, LLLM). Two read-only routes, `/api/claims` and `/api/chain`. 38/38 pass (v1–v5).
- Built as a layer: v4 (`legacy_v4.py`, `SPEC_V4.md`, `static/projection.html`) is exactly as committed and still served at `/static/projection.html`.
- Frozen at 1.1.0 (James: "freeze", 2026-11-13).

### Bad

- Frozen on the laptop run alone (2026-11-13); confirmed on the S24 by James, 2026-11-13.
- (none)

### Ugly

- The redesign was first written into v4's files in place. Undone before commit at James's request ("make sure you are not over writing and versioning like the claude.md requires") and rebuilt as v5.

## [v1.0.0] — 2026-11-13 — FROZEN

### Good

- SPEC_V4 1.1.0 (before freeze): The Voice. `GET /api/voice?q=` runs a
  turn of LLLM (sibling `../lllm`), one session per server; the page
  gains a Voice panel (ask, reply, trace on request) and the Cockpit
  panel counts LLLM opinions. James: "lllm commands go via the
  legacy". 34/34 pass.
- `SPEC_V4.md`, `test_legacy_v4.py` (7 tests, run red first), `legacy_v4.py` and `static/projection.html`: The Projection. One page with Health, the Morning Briefing, The Field (SCP Substrate embedded from 8085), The Cockpit (status), Remember (live Echo preview, then a draft for `forge inbox commit`), The Nerves and LLLM. Delivers the README's v0.2.0 Field, v0.3.0 Cockpit and v0.4.0 Nerves phases. 33/33 pass.
- The Legacy still never signs and never sees a passphrase. Its one write is a draft file in the Cockpit's inbox, guarded against cross-site requests (Host check, Origin check, required X-Forge-Legacy header, no preflight, JSON only, 8 KiB cap).
- `escapeHtml` now escapes `'` (closes the v0.1.2 Ugly). The page adapts to light mode and narrow screens (checked in headless Edge at 1200 and 520 px).
- Morning Briefing goes through Weaver v1.2; a regression test runs it from outside the repositories.
- Frozen at 1.0.0 (James: "freeze", 2026-11-13).

### Bad

- Frozen on the laptop run alone (2026-11-13); confirmed on the S24 by James, 2026-11-13.
- The 3D Field drew no cubes in headless Edge, even with software WebGL; its data was correct (5 claims, 1 attested). Needs a look in a real browser.
- v3's /api/weaver (frozen) still uses Weaver v1.1 and fails when started outside a sibling repo. Run v4.

### Ugly

- SPEC.md §3 ("GET and HEAD only") is narrowed for one route, deliberately: drafts only, no database or ledger writes.

## [v0.1.3] — 2026-11-13 — FROZEN

### Good

- `SPEC_V3.md`, `test_legacy_v3.py` (4 tests, run red first) and `legacy_v3.py`: /api/health now shows the Cockpit v1.1's own 15 round trips through the current layers (`forge_cli_v1_1.probe_layers`), so the dashboard and `forge health` cannot disagree; /api/weaver uses Weaver v1.1; new /api/nerves gives a verified, read-only view of SC-OS's pins (fails closed). 26/26 pass.
- Built on James's delegation ("fix all 11 issues"). Frozen at 0.1.3 on James's sign-off ("freeze all", 2026-11-13).

### Bad

- Frozen on the laptop run alone (2026-11-13); confirmed on the S24 by James, 2026-11-13.
- v1/v2 health probes loaded the frozen v1 module of 14 layers and mostly checked that a function existed, so "all PASS" said nothing about the layers in use.
- The Voice widget could never show a briefing from a real substrate: Weaver v1.0.0 cannot parse P9's ISO 8601 timestamps (the-weaver CHANGELOG). v0.1.1's note that the Weaver "works end-to-end against the real P9 database" was not true of the code.

### Ugly

- The page has no Nerves widget yet; /api/nerves is ready for the v0.4.0 phase.

## [v0.1.2] — 2026-11-13 — v2 layer (resilient health probes)

### Good
- `legacy_v2.py` added as a layer over the frozen `legacy.py`
  (Immutable Rule: `legacy.py` is not edited). It re-composes v1's 15
  probes from v1's own helpers so a missing `cryptography` yields FAIL
  rows for P2/P3 (SPEC.md §2.1) instead of an `ImportError` and a 500
  on `/api/health`. Everything else is inherited from v1.
- `SPEC_V2.md` and `test_legacy_v2.py` (9 tests) added; one test pins
  the v1 defect so the reason for v2 stays on record.
- `test_legacy.py`: an autouse fixture resets the in-memory briefing
  cache (a cached success could mask the error-path tests) and drops
  `SSLKEYLOGFILE`, which made all 6 HTTP tests fail with
  `PermissionError` when set to an unwritable path. Test-only; v1 code
  untouched.
- Docs aligned: README status and run instructions, NOTES Q1
  (in-process probes, matching SPEC §4).
- 22/22 pytest tests pass (13 v1 + 9 v2).

### Bad
- Run `python legacy_v2.py`, not `legacy.py`, to get the fix.

### Ugly
- Cache-busting for mobile browsers still outstanding (v0.2.0).
- `legacy.py`'s header still reads "Version: 1.0.0 (on freeze;
  0.0.0-dev until then)" and some v1 functions lack headers. Left
  as-is because v1 is frozen.
- `escapeHtml()` in `static/index.html` does not escape `'`. Harmless
  today (data only lands in text nodes); deferred to v0.2.0 UI work.

## [v0.1.1] — 2026-11-13 — Phase 1 UI patch

### Good
- `static/index.html` rewritten with defensive flexbox layout.
- Status labels use explicit `flex: 1` on the name and `margin-left:
  auto` on the status, so `PASS`/`FAIL` always renders on the right
  regardless of browser quirks.
- HTML escaped via `escapeHtml()` in all interpolated data.
- Weaver integration now works end-to-end against the real P9
  database (ISO 8601 timestamps), proving the earlier v1.0.1 Weaver
  fix lands correctly.
- 13/13 pytest tests still pass.

### Bad
- (none)

### Ugly
- Mobile Chrome cached the old `index.html` and needed a hard
  refresh (or a browser switch) to render the fixed layout. DuckDuckGo
  browser saw the new HTML immediately. Static asset caching on
  mobile browsers is aggressive; a future v0.2.0 should add
  cache-busting headers or a `?v=N` query string.

## [v0.1.0] — 2026-11-13 — Phase 1 (The Shell)

### Good
- Repository scaffolded as Tier 1 Consumer (The Connector).
- `legacy.py` implemented to SPEC v1.0.0 (Phase 1 scope).
- 13/13 pytest tests pass.
- Dashboard at http://127.0.0.1:8080/ with two live widgets:
  - Health: 15-layer probes (all PASS on current stack).
  - Morning Briefing: Weaver output, cached 1 hour.
- API endpoints: GET /api/health, GET /api/weaver.
- Read-only. GET/HEAD only, 405 on writes, path traversal blocked.
- Standard library only. No Flask, no FastAPI, no Node.js.

### Bad
- Weaver widget only renders if LLLM is configured. On a device
  without LLLM, shows "Briefing unavailable" rather than a fallback.

### Ugly
- (none)

## Phase plan

- v0.1.0 — The Shell (health + weaver). FROZEN.
- v0.2.0 — The Field (embed scp-substrate 3D viewer).
- v0.3.0 — The Cockpit (remember form + Echo preview + commit).
- v0.4.0 — The Nerves (SC-OS peer status).
- v1.0.0 — The Projection (full unification).
