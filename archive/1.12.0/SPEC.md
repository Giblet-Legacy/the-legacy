# SPEC — the-legacy (Tier 1: The Legacy)

SPEC.md — specification for The Legacy, Phase 1 (v0.1.0, The Shell).

Function:
    The master orchestrator's first phase. A web dashboard that
    surfaces the state of the 15-layer stack and the Weaver's
    morning voice, from one page at http://127.0.0.1:8080/.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  P1–P15 (via probes), the-weaver (via subprocess or import)
Version:  SPEC 1.0.0 (Phase 1 scope only)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

## 1. What v0.1.0 delivers

A single Python `http.server` on port 8080, with three endpoints:

- `GET /` — serves `static/index.html` (the dashboard).
- `GET /api/health` — returns the 15-layer status as JSON.
- `GET /api/weaver` — returns the Weaver's briefing as JSON.

Everything else (Field, Cockpit, Nerves) is deferred to v0.2.0+.

## 2. Function Contracts

### 2.1 probe_layers() -> list[dict]
Returns a list of 15 dicts:
    {"layer": "P1 Envelope", "status": "PASS" | "FAIL", "error": str}

Each probe imports its layer and runs a minimal sanity check (see
Cockpit's `_cmd_health` for the canonical probes). Failures are
captured, not raised — a failed layer becomes a FAIL row, not a
500.

### 2.2 get_briefing() -> dict
Returns:
    {"briefing": str | None, "claims": list[dict], "error": str | None}

Delegates to `the-weaver`'s `find_decayed_unknowns` and `call_lllm`.
If LLLM is unavailable, `briefing` is None and `error` is a string.

### 2.3 main(argv) -> int
CLI entry point. Accepts `--host` (default 127.0.0.1) and
`--port` (default 8080). Runs the HTTP server until interrupted.

## 3. Server Rules

- `GET` and `HEAD` only. All other methods → 405.
- Path traversal blocked: no serving outside `static/`.
- Read-only: The Legacy does not write to any database or ledger.
- Static file serving: `static/*` served as-is.
- MIME type inferred from extension. No external library.

## 4. Known Limitations (v0.1.0)

- Only health and weaver widgets. Field, Cockpit, Nerves are v0.2.0+.
- Weaver runs on every page load; cached for 1 hour to avoid hammering
  LLLM. Cache lives in memory.
- Health probes run in-process (fast). If they become slow, they'll
  move to subprocess in a future version.
- Single-operator, localhost only. No auth. No TLS.
- No JavaScript framework. Vanilla JS + CSS.
