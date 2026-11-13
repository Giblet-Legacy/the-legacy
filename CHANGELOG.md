# CHANGELOG — the-legacy (Tier 1: The Legacy)

CHANGELOG.md — build history for The Legacy, latest entry at top.

## [Unreleased]

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
- Built for James's "whole projection" request (2026-11-13). Not frozen (NOTES Q6).

### Bad

- The 3D Field drew no cubes in headless Edge, even with software WebGL; its data was correct (5 claims, 1 attested). Needs a look in a real browser.
- v3's /api/weaver (frozen) still uses Weaver v1.1 and fails when started outside a sibling repo. Run v4.

### Ugly

- SPEC.md §3 ("GET and HEAD only") is narrowed for one route, deliberately: drafts only, no database or ledger writes.

## [Unreleased]

### Good

- (none)

### Bad

- (none)

### Ugly

- (none)

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
