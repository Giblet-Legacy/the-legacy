# SPEC_V4 — the-legacy (Tier 1: The Legacy, The Projection)

SPEC_V4.md — specification for `legacy_v4.py`, the layer over the v3 dashboard.

Function:
    The Projection: one page through which the operator sees and feeds
    every consumer in the stack. It delivers the README's remaining
    phases in one layer — v0.2.0 The Field, v0.3.0 The Cockpit,
    v0.4.0 The Nerves — and adds LLLM. legacy.py, legacy_v2.py and
    legacy_v3.py are not edited. Where this document is silent,
    SPEC_V3.md, SPEC_V2.md and SPEC.md apply.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  forge_cli_v1_2 (Cockpit: status, drafts, LLLM provenance),
          weaver_v1_2 (Weaver),
          echo_v1_1 (Echo), serve_v2 at 127.0.0.1:8085 (SCP Substrate),
          weaver_v1_1, sc-os nerves (via legacy_v3)
Version:  SPEC_V4 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Principles kept

- **The Legacy never signs and never sees a passphrase.** Every
  commit happens in the Cockpit, in a terminal (Cockpit SPEC.md §9).
- **It writes to no database and no ledger.** Its only write is a
  draft file in `$FORGE_HOME/inbox/`, in the Cockpit's own format
  (Cockpit SPEC_V1_2 §2), via the Cockpit's `write_draft`.
- **Localhost only.** No auth (SPEC.md §4); cross-site writes are
  blocked by §4's guards instead.

## 2. Read routes (GET, JSON)

| Route | Answer |
| --- | --- |
| `/api/health`, `/api/nerves` | v3, unchanged |
| `/api/weaver` | v3's shape and cache, through Weaver **v1.2** (v1.1 failed to import outside a sibling repo; the-weaver SPEC_V1_2.md) |
| `/api/cockpit` | `{available, status, error}` — Cockpit `status()` (no passphrase) |
| `/api/lllm` | `{available, build_id, identity, warnings, anchored, error}` — Cockpit `lllm_provenance()`; `anchored` is true when the ledger holds this build's `lllm.build` record |
| `/api/field` | `{url, reachable}` — SCP Substrate's `/api/health` probed with a 1 s timeout; `url` defaults to `http://127.0.0.1:8085/` (`FORGE_FIELD_URL` overrides) |
| `/api/echo?subject=&object=&face=[&text=]` | Echo v1.1 preview: `{gate, rules_fired, shape, memory}`; 400 on missing or invalid fields; `{error}` if there is no substrate yet |
| `/api/inbox` | pending drafts, each `{id, subject, object, face, text}` or `{id, invalid}` |
| `/` | `static/projection.html` (the v1 page stays at `/static/index.html`) |

Every read route answers 200 with an `error` field rather than failing
when a consumer is missing; a missing consumer never takes the page
down.

## 3. The one write: POST /api/inbox

Body: JSON `{subject, object, text, face}`. On success: 201 with
`{draft_id, echo}`, where `echo` is the Echo preview of the same claim,
so the operator sees at once whether the Keystone Gate will refuse it.
Validation is the Cockpit's `validate_draft` (400 with the reason).

## 4. Guards on the write

A browser on the same machine can be made to POST to localhost by any
web page. The write is accepted only if all of these hold, else 403:

1. `Host` is `127.0.0.1:<port>` or `localhost:<port>` (blocks DNS
   rebinding).
2. `Origin`, if present, is `http://` + that same host.
3. Header `X-Forge-Legacy: 1` is present. A cross-site page cannot
   send a custom header without a preflight, and the server answers no
   preflight (OPTIONS is 405).

Also: `Content-Type` must be `application/json` (415), and the body at
most 8 KiB (413). PUT, PATCH, DELETE and OPTIONS stay 405.

## 5. The page (static/projection.html)

Sections, each filled from §2: Health · Morning Briefing · The Field
(iframe of `url` when reachable, else how to start it) · The Cockpit
(claims by face, attested, ledger entries, self-consistency, P8
mirror, open proposals, inbox counts) · Remember (form → live Echo
preview → "Save draft" → `forge inbox commit` in the terminal) · The
Nerves (owner, peers) · LLLM (build, anchored, warnings). Escaping:
every interpolated value goes through `escapeHtml`, which also escapes
`'` (closing the v0.1.1 CHANGELOG "Ugly"). Colours follow the v1 page
and adapt to light mode.

## 6. Tests (test_legacy_v4.py)

- Each read route answers with live data from a substrate written by
  the Cockpit; LLLM and the Field report "unavailable" cleanly and
  "available" when present.
- POST /api/inbox: a valid draft is written in the Cockpit's format and
  returned with its Echo preview; missing header, foreign Host,
  foreign Origin → 403; wrong content type → 415; oversize → 413;
  invalid face → 400; OPTIONS/PUT → 405.
- A draft saved through the Legacy is committed by `forge inbox commit`.
- `/` serves the Projection page with every section.
- Started from a directory outside the repositories, the Legacy still
  produces a Morning Briefing (regression for the Weaver import defect).

---

## Document control

- **SPEC_V4 1.0.0** — 2026-11-13, by the VS Code AI for James's "whole
  projection" request. The inbox write is a deliberate, narrow change
  to SPEC.md §3 ("GET and HEAD only"): drafts only, no signing, no
  database or ledger writes.
