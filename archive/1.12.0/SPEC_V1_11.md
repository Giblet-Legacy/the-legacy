# SPEC V1.11 — the-legacy (legacy_v1_11 + boot_v1_11: drafts through Cockpit v1.8)

SPEC_V1_11.md — specification for legacy_v1_11.py, boot_v1_11.py and static/projection_v1_11.html.

Function:
    James (2026-11-18): "yes do the legacy layer v1.8". Cockpit v1.8
    (explorer-d334-forge SPEC_V1_8.md) lists and commits drafts in the
    order they were written; v1.7, which the Legacy v12 uses, ordered
    drafts written in the same millisecond by hash. 1.11.0 is v12 with the
    Cockpit moved to v1.8 everywhere the Legacy touches drafts. Nothing
    else changes. Where this document is silent, SPEC_V14.md applies.
    legacy.py, legacy_v2–v12, boot.py, boot_v2–v7 and their pages are
    not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v12.py (1.10.0), Cockpit forge_cli_v1_8 (1.8.0), P9 substrate_v4 (4.0.0)
Version:   SPEC V1.11 1.11.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Drafts through Cockpit v1.8

- **POST /api/inbox** saves any kind of draft with v1.8's
  `write_draft_any`. Each new draft's `created_at` comes after every
  pending draft's. The guard, the status codes and the Echo preview for
  claims are v12's.
- **GET /api/inbox** lists pending drafts in v1.8's `pending_drafts()`
  order (the order written), each validated and described as in v12.
- **GET /api/nouns**: registered nouns as in v12, then drafted ones in
  the order written.

## 2. The page

`static/projection_v1_11.html` is projection_v10.html with the commit hint
changed to `python forge_cli_v1_8.py inbox commit`, and its header
updated. Nothing else changes.

## 3. boot_v1_11.py

boot_v7.py with `legacy_v1_11.py` as The Legacy. The Field is still
serve_v8.

## 4. Tests (test_legacy_v1_11.py)

- Drafts posted while the clock is frozen are listed by /api/inbox in
  the order posted, and their `created_at` values strictly increase.
- Drafted entities and subjects in /api/nouns come in the order written.
- Every kind still posts (201) and is refused as in v12 (400, 403).
- The page shows the v1.8 commit hint and not v1.7's.
- boot_v1_11 starts serve_v8, then legacy_v1_11.

---

## Document control

- **SPEC V1.11 1.11.0** — 2026-11-18, by the VS Code AI on James's "yes
  do the legacy layer v1.8". Frozen 2026-11-18 (James: "freeze").
