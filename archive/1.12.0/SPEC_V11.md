# SPEC V11 — the-legacy (v10: the briefing through Weaver v1.4, boot_v4)

SPEC_V11.md — specification for legacy_v10.py and boot_v4.py.

Function:
    James (2026-11-14) saw the Briefing give every question on one
    subject the same engine line. The Weaver v1.4 (the-weaver
    SPEC_V1_4.md) gives one line per question. v10 is The Legacy v9
    with its briefing from Weaver v1.4; boot_v4 starts the Field v7,
    then The Legacy v10. Where this document is silent, SPEC_V10.md
    applies. legacy.py, legacy_v2–v9, boot.py, boot_v2.py, boot_v3.py
    and their pages are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v9.py (SPEC_V10 1.6.0), the-weaver weaver_v1_4 (1.4.0)
Version:   SPEC V11 1.7.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. legacy_v10.py

v9's server and page. v10's handler serves the briefing
(`/api/weaver`) itself, with v7's shape, errors and cache rule, through
`weaver_v1_4` instead of `weaver_v1_3`. Nothing in v7 is replaced, so
legacy.py–v9 behave as before, even in the same process.

## 2. boot_v4.py

`python boot_v4.py [--host H] [--port N] [--field-port N]` does exactly
what boot.py does (SPEC_V8 §2) with serve_v7.py as the Field and
legacy_v10.py as The Legacy.

## 3. Tests (test_legacy_v10.py)

- v10's Weaver is weaver_v1_4 and v7's is still weaver_v1_3;
  `/api/weaver` on a v10 server returns v1.4's briefing: a stand-in
  engine that answers each question's object gives one different line
  per question on one subject.
- `/` serves projection_v9.html.
- boot_v4 starts serve_v7.py (quiet), then legacy_v10.py.

---

## Document control

- **SPEC V11 1.7.0** — 2026-11-14, by the VS Code AI on James's
  delegation (the repeated "Envelope-layer and P2 at." line; "yes").
