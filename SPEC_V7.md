# SPEC V7 — the-legacy (The Legacy v7: the LLLM wired through)

SPEC_V7.md — specification for legacy_v7.py, the layer above The Legacy v6 (1.2.0).

Function:
    Points The Legacy at the layers that make LLLM work end to end:
    Cockpit v1.3 (finds the engine, refuses a refusal, P13 v3 gate),
    Weaver v1.3 (briefing from claims, engine as an aside) and the
    Voice v0.1.2 (speaks a claim's signed text, aspects). SPEC_V6.md
    remains authoritative for everything this document does not change.
    legacy.py and legacy_v2–v6 are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v6.py (1.2.0), forge_cli_v1_3, weaver_v1_3, lllm_v0_1_2
Version:   SPEC V7 1.3.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Why v7

Checked 2026-11-13: nothing using LLLM worked end to end. The engine
was unreachable from Python (installed as a shell function), the
briefing sent a chat prompt to an n-gram model, and the Voice answered
"ledger-layer is status." about the repo cubes.

## 2. Routes

v7 answers these itself; every other route is v6's (and below).

| Route | v7 |
|---|---|
| `/` | `static/projection_v7.html` |
| `/api/voice?q=` | as v4 (same limits and shape), through `lllm_v0_1_2.Session` |
| `/api/weaver` | `{briefing, claims, error}`: briefing from Weaver v1.3 `compose_briefing`, so it is present whenever there are UNKNOWN claims, engine or not; v4's one-hour cache |
| `/api/lllm` | v4's shape, through Cockpit v1.3 `lllm_provenance` |
| `/api/cockpit` | v4's shape, through Cockpit v1.3 `status` |

The Voice session is one per server and per database, as v4.

## 3. Page

`projection_v7.html` is v6's page with: Voice replies keep their line
breaks (aspects are one per line); the commit hint names
`forge_cli_v1_3.py inbox commit`; the Field hint names `serve_v4.py`.

## 4. main

As v6; the printed hints name `forge_cli_v1_3.py` and `serve_v4.py`.

## 5. Tests (test_legacy_v7.py)

- `/api/voice` speaks a cube's FACT text and answers a subject's
  aspects one per line; OPINION text never appears.
- `/api/weaver` gives a briefing from the UNKNOWN faces with no engine
  installed, and an `LLLM:` line from a stand-in engine (LLLM_CLI).
- `/api/lllm` reports the stand-in engine's build.
- `/` serves the v7 page with the new hints; v6 routes still answer.

---

## Document control

- **SPEC V7 1.3.0** — 2026-11-13, by the VS Code AI on James's
  delegation ("make sure [the LLLM] is properly wired in"; "all of it").
