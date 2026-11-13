# NOTES — the-legacy (Tier 1: The Legacy)

NOTES.md — open questions and decisions for The Legacy.

## Decisions

- **The Legacy is glue, not a rewrite.** It surfaces other consumers;
  it does not reimplement them. Every widget in the dashboard calls
  into an existing consumer (subprocess or direct import). If a widget
  needs new behaviour, that behaviour belongs in the consumer, not
  in The Legacy.
- **Read-mostly.** Writes route through `explorer-d334-forge` (the
  Cockpit). The Legacy's dashboard is for viewing, not for mutating
  state directly.
- **Phased delivery.** v1.0.0 is the full projection; we freeze v0.1.0
  first (the Shell), then layer in the Field, Cockpit, and Nerves.
- **Standard library only** for the server. No Flask, no FastAPI, no
  Node.js. The dashboard is `http.server` + vanilla HTML/JS/CSS.
- **Ports.** The Legacy uses port 8080. `scp-substrate` uses 8085.
  `explorer-d334-forge` uses no port (CLI only). This avoids
  collisions when both are running.

## Open questions

- **Q1.** Health check depth. Should The Legacy run `forge health`
  as a subprocess (slow, ~2s, but isolated) or import `forge_cli`
  directly (fast, but couples The Legacy to the Cockpit's internals)?
  v1.0.0 uses subprocess — isolation beats speed at the UI layer.
- **Q2.** Weaver freshness. Should the Weaver widget re-run
  `the-weaver` on every page load (fresh briefing, slow), or cache
  the last briefing and offer a "refresh" button? v1.0.0 runs on
  load, caches for 1 hour.
- **Q3.** Field embedding. `scp-substrate` runs on 8085. Options:
  (a) iframe embed of 8085, (b) proxy `/field/*` from 8080 to 8085,
  (c) share the same server and drop scp-substrate's own port.
  v0.2.0 decision deferred.
- **Q4.** Authentication. Single-operator, localhost only. No auth
  in v1.0.0. If remote access becomes a requirement, that's a v2
  concern.
