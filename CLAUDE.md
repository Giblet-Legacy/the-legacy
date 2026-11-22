# Forge Stack Context — The Legacy

CLAUDE.md — Context briefing for AI assistants working in this repository.

## What this repo is
The final consumer. Tier 1. The master orchestrator. It is the
projection of the self — a unified dashboard that surfaces the
outputs of every other consumer (Cockpit, Substrate, Weaver, SC-OS,
Echo) in one place. It is the operator's window into The Legacy.

## The Immutable Rule
Never rewrite a primitive. Add a layer. The Legacy consumes other
consumers. It does not rewrite them.

## What it is NOT
- Not a replacement for `explorer-d334-forge` (the CLI).
- Not a replacement for `scp-substrate` (the 3D viewer).
- Not a replacement for `the-weaver` (the morning voice).
- Not a replacement for `sc-os` (the network).
- Not a replacement for `the-echo` (the mirror).
- It is the **glue** — a web dashboard that surfaces all of them.

## Architecture
- **2.1.0 (frozen 2026-11-22):** `boot_v2_1.py` + `legacy_v2_1.py` + `static/projection_v2_1.html` (SPEC_V2_1.md). First-time guidance and Advanced navigation over the 2.0.0 routes and guard. Run `python boot_v2_1.py`.
- **2.0.0 (frozen 2026-11-20, tag `v2.0.0`):** `boot_v2.py` + `legacy_v2.py` + `static/projection_v2.html` (SPEC_V2.md; CONSOLIDATION_V2.md). 1.12.0's fourteen-layer chain flattened into one module, one handler, one boot: the same behaviour, route by route (SPEC_V2 §1 names the 1.12.0 layer each route comes from). Run `python boot_v2.py`. Tests: `test_legacy_v2.py` plus the carried `test_*_at_v2.py` suites (aliases of the old module names; never add new behaviour to a consolidation, it is a new version).
- Everything below is 1.12.0 and earlier, byte-identical in `archive/1.12.0/` (pytest.ini never collects it) and at the tag `v1.12.0`. The archived files import siblings via `../`, so run them from a worktree of the tag, not from the archive.
- `boot_v1_12.py` + `legacy_v1_12.py` (SPEC_V1_12.md: the "Ask the AI" card; /api/ai/* relayed to ai-gate's local API, POSTs behind the v4 guard, no seal relay; the Legacy never calls a model; frozen 1.12.0, 2026-11-20). Run `python boot_v1_12.py` (with GEMINI_API_KEY and FORGE_GEMINI_MODEL set for asks).
- `boot_v1_11.py` + `legacy_v1_11.py` (SPEC_V1_11.md: drafts through Cockpit v1.8, listed and committed in the order written; page projection_v1_11.html; frozen 1.11.0; files named for their version, roadmap NAMING.md). Run `python boot_v1_11.py`.
- `boot_v7.py` + `legacy_v12.py` (SPEC_V14.md: New entity / subject / claim tabs with drop-downs; drafts for Cockpit 1.7.0; frozen 1.10.0). Run `python boot_v7.py`.
- `boot_v6.py` + `legacy_v11.py` (SPEC_V13.md: one link — the page is told `FORGE_FIELD_PUBLIC_URL` for the Field, e.g. `/field/` on the VPS; frozen 1.9.0). Run `python boot_v6.py`.
- `boot_v5.py` (SPEC_V12.md: the Field v8, you at the centre; frozen 1.8.0) is boot_v4 with serve_v8. Run `python boot_v5.py`.
- `legacy_v10.py` + `boot_v4.py` (SPEC_V11.md: the Briefing through Weaver v1.4, one engine line per question; frozen 1.7.0) are the layer over v9. Run `python boot_v4.py`.
- `legacy_v9.py` + `boot_v3.py` (SPEC_V10.md: the page reads on a phone; the Field v7; frozen 1.6.0) are the layer over v8. Run `python boot_v3.py`.
- `legacy_v8.py` + `boot.py` (SPEC_V8.md: boot the Field then The Legacy, exponential cool-off, self-refreshing page, last-good buffer; frozen 1.4.0; boot_v2 frozen 1.5.0) are the layer over v7. Run `python boot.py`.
- `legacy_v7.py` (SPEC_V7.md: the LLLM wired through — Voice v0.1.2, Weaver v1.3, Cockpit v1.3; frozen 1.3.0) is the entry point from v7, over v6.
- Entry point: `legacy_v6.py` (SPEC_V6.md: every filled face, ledger kind filter, Subject column; frozen 1.2.0) over `legacy_v5.py` (SPEC_V5.md, the redesigned page and /api/claims, /api/chain) over `legacy_v4.py` (SPEC_V4.md, The Projection: one page, the inbox draft is its only write) over `legacy_v3.py` (SPEC_V3.md) over `legacy_v2.py` over frozen `legacy.py`. Health comes from the Cockpit's `probe_layers`; the Morning Briefing from `weaver_v1_2`; the Voice (chat) from LLLM, `../lllm`; Nerves from SC-OS `nerves`.
- Python `http.server` (standard library only).
- HTML/JS/CSS frontend (vanilla, no build step).
- Calls other consumers via subprocess or direct SQLite read.
- Read-mostly. All writes still route through the Cockpit.

## Versioning (James, 2026-11-13)
- Never overwrite a committed layer, page or spec. A change is a new
  layer (`legacy_vN.py`, `SPEC_VN.md`, `static/projection_vN.html`) over
  the last one. Signed-off specs are never edited.

## Constraints
- Standard library only (except `pytest` for dev).
- British English (-ise, artefact).
- Header discipline on every file and function.
- LF-only. No CRLF.
