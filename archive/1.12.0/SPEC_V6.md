# SPEC_V6 — the-legacy (Tier 1: The Legacy, multi-face claims)

SPEC_V6.md — specification for `legacy_v6.py`, the layer over v5.

Function:
    Makes the page tell the truth about cubes with several faces, and
    makes the ledger readable when seals outnumber claims. legacy_v5.py,
    SPEC_V5.md and static/projection_v5.html are frozen (1.1.0) and not
    edited. Where this document is silent, SPEC_V5.md applies.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v5.py (SPEC_V5 1.0.0); P9 substrate_v3 via the Cockpit
Version:  SPEC_V6 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Why v6

Seen by James on the live page with one multi-face cube per repo:

1. "Claims by face" counted only each claim's main face (FACT 24,
   everything else 0), hiding 24 CONTEXT faces and the COUNTER and
   UNKNOWN faces.
2. The Claims table did not say which subject (repo) a claim is about.
3. The Ledger panel showed only seal/proposal pairs; claims fell out of
   view.
4. Query suggestions were built mechanically ("is the roadmap the
   map?").
5. "LLLM opinions" sat under Peers.
6. The "Field not running" hint named `serve_v2.py` (NOTES Q8); the
   Field's entry point is `serve_v3.py`.

## 2. Routes (changed over v5, read-only)

- `GET /api/claims?limit=N`: as SPEC_V5 §2, and each claim also has
  `faces`: every filled face of the cube, `{FACE: text}`, in the six-
  face order. A face is filled when its value is a non-empty string.
- `GET /api/chain?limit=N&kind=K`: as SPEC_V5 §2, plus an optional
  `kind` filter (`claim`, `seal`, `proposal`, `lllm.build`, `record`;
  anything else is 400). The newest N entries **of that kind** are
  returned, so claims are reachable however many seals follow them.
  The answer adds `matched` (how many entries of that kind exist);
  `total` stays the whole ledger.

## 3. The page (static/projection_v6.html, served at `/`)

v5's design, with:
- **Faces filled** (renamed from Claims by face): the stacked bar and
  counts count every filled face across all claims; a note gives the
  main-face split.
- **Claims** table: Subject, Face, Claim, ID; a claim's other filled
  faces are listed under it.
- **Ledger** with filter tabs: All, Claims, Seals, Proposals.
- **Query** suggestions: "what is the <subject>?" for the two newest
  polarised claims with different subjects, then "how did you work
  that out?".
- **Metrics:** LLLM opinions under Claims; Peers says "pinned via
  SC-OS".
- The Field hint and the startup message name `serve_v3.py`.

The v5 page stays at `/static/projection_v5.html`.

## 4. Tests (test_legacy_v6.py)

- `/api/claims` returns every filled face of a multi-face cube.
- `/api/chain?kind=claim` returns only claims, even when seals are
  newer; `kind=seal` only seals; `matched` and `total` are right; a
  bad kind is 400.
- `/` serves the v6 page: the new sections, the Subject column, the
  ledger filters, `serve_v3.py` and not `serve_v2.py`; v5's page is
  still served.
- v5 and v4 routes still answer through the v6 server.

---

## Document control

- **SPEC_V6 1.0.0** — 2026-11-13, by the VS Code AI after James
  reviewed the live page ("yes" to the six fixes).
