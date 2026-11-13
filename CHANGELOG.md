# CHANGELOG — the-legacy (Tier 1: The Legacy)

CHANGELOG.md — build history for The Legacy, latest entry at top.

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
