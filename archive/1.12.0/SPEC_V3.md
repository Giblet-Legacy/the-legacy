# SPEC_V3 — the-legacy (Tier 1: The Legacy, current-layer dashboard)

SPEC_V3.md — specification for `legacy_v3.py`, the layer over the v2 shell.

Function:
    Points The Legacy's two widgets at the current layers and opens the
    first read-only view of SC-OS. legacy.py (v1) and legacy_v2.py are
    not edited. Where this document is silent, SPEC.md and SPEC_V2.md
    apply unchanged (routes, methods, 405/404/400, static serving,
    flags, exit codes).

Tier:     Tier 1 — Consumer (The Connector)
Depends:  explorer-d334-forge `forge_cli_v1_1.probe_layers`,
          the-weaver `weaver_v1_1`, sc-os `nerves`
Version:  SPEC_V3 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Why v3

- v1/v2 health probes load the frozen **v1** module of 14 layers and
  mostly check that a function exists, so "all PASS" said nothing
  about the layers the stack now runs on.
- The Voice widget used Weaver v1.0.0, which never finds a claim in a
  real substrate (it cannot parse P9's ISO 8601 timestamps).
- SC-OS had no view at all.

## 2. GET /api/health

`{"layers": forge_cli_v1_1.probe_layers()}` — the Cockpit's own 15
round trips through the current layers, so the dashboard and
`forge health` can never disagree. If the Cockpit cannot be imported,
15 FAIL rows carry the reason. Never raises.

## 3. GET /api/weaver

Same shape and one-hour cache as SPEC.md §2.2, computed with
`weaver_v1_1` (find_decayed_unknowns, build_prompt, call_lllm). The
cache is v3's own; v1's is untouched.

## 4. GET /api/nerves (new)

`{"available": bool, "nerves": dict | null, "error": str | null}` from
`nerves.read_nerves(nerves.default_pin_path())`:
- no pin file → `available: false`, no error ("no SC-OS pins yet");
- a pin file that fails verification → `available: false` with the
  error (fail closed, nothing shown);
- otherwise the verified summary.
The dashboard page gains no widget yet; that is the v0.4.0 Nerves
phase.

## 5. Tests (test_legacy_v3.py)

- /api/health: 15 rows, all PASS, labels P1–P15 in order.
- /api/weaver: on a real P9 substrate with a mocked LLLM, the briefing
  and claims come back; v1's `_compute_briefing` on the same file
  reports "no UNKNOWN claims" (pins the reason for v3).
- /api/nerves: absent, valid and tampered pin files.
- The server answers all three over HTTP; POST is still 405.

---

## Document control

- **SPEC_V3 1.0.0** — 2026-11-13, by the VS Code AI on James's
  delegation ("fix all 11 issues").
