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
- `legacy_v10.py` + `boot_v4.py` (SPEC_V11.md: the Briefing through Weaver v1.4, one engine line per question; built, not frozen) are the layer over v9. Run `python boot_v4.py`.
- `legacy_v9.py` + `boot_v3.py` (SPEC_V10.md: the page reads on a phone; the Field v7; built, not frozen) are the layer over v8. Run `python boot_v3.py`.
- `legacy_v8.py` + `boot.py` (SPEC_V8.md: boot the Field then The Legacy, exponential cool-off, self-refreshing page, last-good buffer; built, not frozen) are the layer over v7. Run `python boot.py`.
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
