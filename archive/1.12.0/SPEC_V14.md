# SPEC V14 — the-legacy (legacy_v12 + boot_v7: new entity, new subject, new claim)

SPEC_V14.md — specification for legacy_v12.py, boot_v7.py and static/projection_v10.html.

Function:
    James (2026-11-16): "where we have the new claim we should have tabs
    for new entity new subject and new claim, and a way to link the
    claims we create to a subject from a drop down and subject to a
    entity from a drop down; entity does not have this option as its an
    entity". The "New claim" card becomes "New" with three tabs. Each
    saves a draft through the Cockpit v1.7 inbox (explorer-d334-forge
    SPEC_V1_7.md); the Legacy still never signs. Where this document is
    silent, SPEC_V13.md applies. legacy.py, legacy_v2–v11, boot.py,
    boot_v2–v6 and their pages are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v11.py (1.9.0), Cockpit forge_cli_v1_7 (1.7.0), P9 substrate_v4 (4.0.0)
Version:   SPEC V14 1.10.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. The card: three tabs

| Tab | Fields | Links to |
| :--- | :--- | :--- |
| **Entity** | name | nothing: an entity stands alone |
| **Subject** | name; **entity** from a drop-down | the entity it belongs to |
| **Claim** | **subject** from a drop-down; object; face; text | the subject it is about |

- The claim drop-down lists subjects, and entities in their own group
  (claims about a person, such as James's identity claims, are about an
  entity).
- Drop-downs list what P9 has registered and what is drafted but not yet
  committed, the latter marked "(draft)", so an entity, a subject in it
  and a claim about that subject can all be drafted at once; the
  Cockpit commits them in that order.
- Echo previews claims only, as before. Pending drafts show their kind.
- The commit hint names `forge_cli_v1_7.py inbox commit`.

## 2. API

- `GET /api/nouns` → `{"entities": [{id, name, kind, draft}],
  "subjects": [{id, name, kind, draft, entities: [names]}], "error"}`:
  registered ones from P9 v4 (`list_entities`, `list_subjects`,
  `members`), then pending entity and subject drafts (`draft: true`,
  `id` the draft id, a subject's `entities` its drafted entity). No
  database or no P9 v4 tables: empty lists, no error. Read-only.
- `POST /api/inbox` (v4's guard unchanged: localhost Host, same origin,
  `X-Forge-Legacy: 1`, JSON, size): a body with `kind` `entity` or
  `subject` is written with the Cockpit's `write_draft_any` and answered
  `201 {"draft_id"}`; a body without `kind` is a claim, written the same
  way and answered with the Echo preview as v4. A bad draft is `400`.
- `GET /api/inbox` → pending drafts of every kind:
  `{"id", "kind", ...fields}` or `{"id", "invalid"}`.
- `/` serves `projection_v10.html`. Everything else is v11's.

## 3. boot_v7.py

boot_v6 with legacy_v12.py as The Legacy (the Field is still serve_v8).

## 4. Tests (test_legacy_v12.py)

- `/api/nouns`: empty without a database; with a registered entity, a
  subject in it and a pending entity draft, all listed, drafts marked.
- `POST /api/inbox` writes entity, subject and claim drafts (the claim
  with an Echo preview); an unknown kind is 400; a request with a
  tailnet Host is 403 (read-only on the VPS).
- `GET /api/inbox` lists each kind.
- `/` is the v10 page: three tabs, the two drop-downs, the v1.7 commit hint.
- boot_v7 starts serve_v8, then legacy_v12.

---

## Document control

- **SPEC V14 1.10.0** — 2026-11-16, by the VS Code AI on James's request.
