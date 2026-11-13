# SPEC_V5 — the-legacy (Tier 1: The Legacy, The Projection redesigned)

SPEC_V5.md — specification for `legacy_v5.py`, the layer over v4.

Function:
    A new page for The Projection and the two read-only routes it
    needs. Built as a layer, not an edit: legacy_v4.py, SPEC_V4.md and
    static/projection.html stay exactly as committed (v4, SPEC_V4
    1.1.0). Where this document is silent, SPEC_V4.md applies,
    including every route, the inbox guards and the Voice.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v4.py (SPEC_V4 1.1.0); P9 substrate_v3 (read-only),
          via the Cockpit's layer loader
Version:  SPEC_V5 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Why v5

James on the v4 page: "boring and uninspired"; on a first warm/serif
redraft: "still not right try modern clean and technical". v5 is a
clean technical console that also shows the two things v4 hid: what
is in memory, and the chain that keeps it honest.

## 2. Read-only routes (added over v4)

- `GET /api/claims?limit=N` (default 60, at most 500; a non-number is
  400): the newest active claims from P9 substrate_v3 (`mode=ro`,
  verify-on-read), newest first, each `{claim_id, short, face,
  subject, object, polarity, text, created_at, attested, verified}`.
  `text` is the capsule's face text, else "subject object". `attested`
  is P9 SPEC_V3 §3's latest decision being an attestation. Answers
  `{available, claims, error}`.
- `GET /api/chain?limit=N` (default 12, at most 200; a non-number is
  400): the newest ledger entries, newest first, each `{seq, hash,
  prev, kind, label}`; `kind` is `claim`, `seal`, `proposal`,
  `lllm.build` or `record`; `label` is a short description. Reads
  `ledger.jsonl` only; it never verifies or writes (P6 and
  `/api/cockpit` say whether the chain is intact). Answers
  `{available, entries, total, error}`.

## 3. The page (static/projection_v5.html, served at `/`)

Modern, clean and technical (James: "still not right try modern clean
and technical", after a first warm/serif draft): neutral greys, 1px
borders, one accent colour plus semantic green / amber / red, system
sans for text, monospace and tabular figures for data, tables for
records. System fonts only (local-first, works offline); light and
dark from `prefers-color-scheme`; no decorative motion. Every
interpolated value goes through `escapeHtml` (which escapes `'`).

Regions, in order: top bar (name, live status: layers, chain, mirror,
clock) · Metrics (claims, ledger, drafts, peers) · Layers (15-cell
status grid) and Claims by face (stacked bar + counts) · Query (the
Voice: console input, answers with citation ids, plan, trace on
request) · Ledger (table: seq, kind, label, hash, prev) and Claims
(table: face, text, id, sealed, verified) · Field (SCP Substrate
embedded) · New claim (form, Echo result, inbox) · Network (SC-OS
peers), Briefing, LLLM · footer.

The v4 page stays available at `/static/projection.html`; v1's at
`/static/index.html`.

## 4. Tests (test_legacy_v5.py)

- `/api/claims` and `/api/chain` return live data from a substrate and
  ledger written by the Cockpit, newest first, with intact `prev`
  links; bad `limit` is 400.
- `/` serves the v5 page with every section, the inbox header, and an
  escaping function that escapes `'`; the v4 page is still served.
- Every v4 route still answers through the v5 server (inherited).

---

## Document control

- **SPEC_V5 1.0.0** — 2026-11-13, by the VS Code AI after James's
  "boring and uninspired". Made a layer after James's "make sure you
  are not over writing and versioning like the claude.md requires":
  the first draft had edited v4's files in place.
