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

- **Freeze boot_v5 at 1.8.0?** The Field v8 (SPEC_V12.md). Built and
  green on the laptop. Not yet run on the S24. Raised 2026-11-15.
  Owner: James.

- **Q1.** Health check depth. Should The Legacy run `forge health`
  as a subprocess (slow, ~2s, but isolated) or import `forge_cli`
  directly (fast, but couples The Legacy to the Cockpit's internals)?
  v0.1.x probes in-process (fast; see SPEC §4). Move to subprocess
  if probes become slow or a broken layer can take the server down —
  isolation beats speed at the UI layer.
  **2026-11-13:** v3 delegates to the Cockpit's `probe_layers()`
  (in-process, current layers, real round trips), so there is one
  health check for the whole stack.
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
- **Q5.** Freeze legacy_v3 (0.1.3)? **Resolved 2026-11-13 — James: "freeze all".** Frozen on the laptop run; confirmed on the S24 by James, 2026-11-13. Built and green on the laptop
  (26/26). Not yet run on the S24. Raised 2026-11-13. Owner: James.
- **Q7.** Freeze legacy_v5 (The Projection redesigned)? **Resolved 2026-11-13 — James: "freeze".** Frozen on the laptop run; confirmed on the S24 by James, 2026-11-13. Built and green on
  the laptop (38/38). Raised 2026-11-13. Owner: James.
- **Q6.** Freeze legacy_v4 (The Projection) at 1.0.0? **Resolved 2026-11-13 — James: "freeze".** Frozen on the laptop run; confirmed on the S24 by James, 2026-11-13. Built and green
  on the laptop (33/33). The Field's rendering still to be checked in a
  real browser. Raised 2026-11-13. Owner: James.
- **Q3 resolved 2026-11-13 (SPEC_V4):** the Field is embedded as an
  iframe of SCP Substrate on 8085; the Legacy probes its health first.
- **Q8.** Stale hint in frozen files: legacy_v4.py, legacy_v5.py (startup
  message) and static/projection_v5.html ("Field is not running") say
  `serve_v2.py`. SCP Substrate's entry point is now `serve_v3.py`
  (v2 breaks the field on any attested claim). Frozen, so not edited:
  fix in the next Legacy version. Raised 2026-11-13. Owner: James.
  **2026-11-13:** fixed in v6 (legacy_v6.py, projection_v6.html name
  `serve_v3.py`); v4 and v5 keep the old hint, frozen.
- **Q9.** Freeze legacy_v6 at 1.2.0? Built and green on the laptop (42/42).
  Raised 2026-11-13. Owner: James.
  **Resolved 2026-11-13 — James: "freeze".** Laptop run; S24 run still to be
  confirmed (v6 was unpushed when the phone was tested).
- **Q10.** Freeze legacy_v7 at 1.3.0? The LLLM wired through (SPEC_V7.md).
  Built and green on the laptop (46/46). Waits on Cockpit v1.3, Weaver v1.3
  and LLLM v0.1.2. Raised 2026-11-13. Owner: James.
- **Q11.** Freeze legacy_v8 and boot.py at 1.4.0? Boot together, cool-off,
  refresh, buffer (SPEC_V8.md). Built and green on the laptop (51/51); boot
  and restart checked live. Uses SCP Substrate v5 and Cockpit v1.4, both
  built, not frozen. Raised 2026-11-14. Owner: James.
  **Resolved 2026-11-13 — James: "freeze commmit and push".** Frozen on the laptop run; S24 run still to be confirmed.
  Correction 2026-11-14: the line above was recorded in error; VERSION never
  took 1.4.0, so v8 was not frozen then.
  **Resolved 2026-11-14 — James: "phone worked freeze please".** Frozen; tests pass on the laptop and the S24.
- **Q12.** Freeze boot_v2 at 1.5.0 (SPEC_V9.md, the Field v6)? Built and
  green on the laptop. Raised 2026-11-14. Owner: James.
  **Resolved 2026-11-14 — James: "phone worked freeze please".** Frozen; tests pass on the laptop and the S24.
- **Q13.** Freeze legacy_v9 and boot_v3 at 1.6.0 (SPEC_V10.md: the page
  reads on a phone; the Field v7)? Built and green on the laptop (55/55).
  Raised 2026-11-14. Owner: James.
  **Resolved 2026-11-14 — James: "phone worked freeze please".** Frozen; tests pass on the laptop and the S24.
- **Q14.** Freeze legacy_v10 and boot_v4 at 1.7.0 (SPEC_V11.md: the
  Briefing through Weaver v1.4)? Built and green on the laptop (58/58).
  Raised 2026-11-14. Owner: James.
  **Resolved 2026-11-14 — James: "phone worked freeze please".** Frozen; tests pass on the laptop and the S24.
- **Q15.** Freeze boot_v5 at 1.8.0 (SPEC_V12.md: the Field v8, you at the
  centre)? Built and green on the laptop. Raised 2026-11-15. Owner: James.
  **Resolved 2026-11-16 — James: "commit and push and freeze".** Frozen; 67/67 on the laptop.
- **Q16.** Freeze legacy_v11 and boot_v6 at 1.9.0 (SPEC_V13.md: one link)?
  Built and green on the laptop (67/67); running on the VPS, the Legacy
  and its Field opened from the S24 and the PC on one tailnet link.
  Raised 2026-11-16. Owner: James.
  **Resolved 2026-11-16 — James: "commit and push and freeze".** Frozen; 67/67 on the laptop.
- **Q17.** SCP Substrate serve_v8 / view_v4, which boot_v5 and boot_v6 start
  as the Field, is still 8.0.0-dev in scp-substrate. Freeze it too?
  Raised 2026-11-16. Owner: James.
- **Q18.** `test_legacy_v8.py::test_boot_end_to_end` is racy: it stops boot
  as soon as `/api/field` answers, then asserts boot has already logged
  `legacy up`, which boot writes on its own poll. On 2026-11-16 it failed
  3 of 5 runs alone (boot.py and legacy_v8 unchanged). Fix as a new test
  layer that waits for both log lines before stopping boot. Raised
  2026-11-16. Owner: James.
