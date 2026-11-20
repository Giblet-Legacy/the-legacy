# SPEC V9 — the-legacy (boot_v2: the Field v6)

SPEC_V9.md — specification for boot_v2.py, over boot.py (SPEC_V8.md).

Function:
    `python boot_v2.py` does exactly what boot.py does (SPEC_V8 §2), with
    SCP Substrate serve_v6.py as the Field, so "depends on" claims are
    drawn as the owner's own links (SCP SPEC_V6.md). boot.py, legacy_v8
    and every earlier file are not edited; boot_v2 sets boot.py's Field
    script for its own process, then calls boot.main.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   boot.py (SPEC_V8 1.4.0), SCP Substrate serve_v6 (6.0.0)
Version:   SPEC V9 1.5.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## Tests (test_boot_v2.py)

- boot_v2 starts serve_v6.py (quiet) before legacy_v8.py.

## Document control

- **SPEC V9 1.5.0** — 2026-11-14, by the VS Code AI on James's delegation
  ("links together are weak").
