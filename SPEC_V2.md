# SPEC V2 — the-legacy 2.0.0 (legacy_v2 + boot_v2: the consolidation of 1.12.0)

SPEC_V2.md — specification for legacy_v2.py, boot_v2.py and static/projection_v2.html.

Function:
    James, 2026-11-20: "freeze then plan 2.0.0 consolidation", then "go
    ahead". The plan is CONSOLIDATION_V2.md. 2.0.0 is The Legacy 1.12.0
    with its fourteen-module chain flattened into one module, one boot
    and one page. Behaviour is 1.12.0's: the same routes, answers, status
    codes, guard, buffer, caches, page and boot. Nothing is added and
    nothing is fixed. The specs this one gathers, SPEC.md to
    SPEC_V1_12.md, are byte-identical in archive/1.12.0/. Where this
    document is silent, they apply, read through the layer named for each
    route in §1.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   Cockpit forge_cli_v1_1, v1_2, v1_3 and v1_8; Weaver v1.4;
           LLLM Voice 0.1.2; Echo v1.1; SC-OS nerves; P9 substrate_v4;
           the Field (scp-substrate serve_v8); ai-gate's local API (0.1.0)
Version:   SPEC V2 2.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Routes (legacy_v2.py)

Each route does exactly what the 1.12.0 layer that answered it did.

| Route | Answer | From |
|---|---|---|
| `GET /` | static/projection_v2.html | v1_12 (SPEC_V1_12 §2) |
| `GET /api/ai/<name>` | relayed to ai-gate for `health status threads thread assumptions assumption known score`; any other name gets 404; with the gate down, 200 `{"error", "offline": true}` | v1_12 (SPEC_V1_12 §1) |
| `POST /api/ai/ask`, `/api/ai/rate` | relayed behind the guard (§2); body not JSON: 400; gate down: 503; any other name: 404 (seals are made in the terminal) | v1_12 |
| `GET /api/nouns` | registered entities and subjects (P9 v4), then drafted ones in the order written | v12 and v1_11 (SPEC_V14, SPEC_V1_11) |
| `GET /api/inbox` | pending drafts through Cockpit v1.8, in the order written | v1_11 |
| `POST /api/inbox` | a draft through Cockpit v1.8 behind the guard: 201 `{"draft_id"}`, plus the Echo preview for a claim | v1_11 |
| `GET /api/field` | the Field probed at FORGE_FIELD_URL (1 s); FORGE_FIELD_PUBLIC_URL, when it is a path or an http(s) URL, is the link given | v4 and v11 (SPEC_V13) |
| `GET /api/weaver` | Weaver v1.4's briefing, a good one cached for an hour | v10 (SPEC_V11) |
| `GET /api/voice?q=` | one turn of the Voice (LLLM 0.1.2), with q 1–2000 characters, else 400 | v7 (SPEC_V7) |
| `GET /api/lllm`, `/api/cockpit` | the LLLM build and its anchoring; the Cockpit's status (both Cockpit v1.3) | v7 |
| `GET /api/claims?limit=`, `/api/chain?limit=&kind=` | recent claims with every filled face; the ledger, filtered by kind | v5 and v6 (SPEC_V5, SPEC_V6) |
| `GET /api/echo?subject=&object=&face=&text=` | the Echo's preview (Echo v1.1) | v4 (SPEC_V4) |
| `GET /api/health`, `/api/nerves` | Cockpit v1.1's 15 probes; SC-OS nerves | v3 (SPEC_V3) |
| anything else | a path with `..` gets 400; `/static/<file>` is served from static/ only; otherwise 404 | legacy.py (SPEC.md) |

- **Order:** routes are checked in the order 1.12.0's chain reached them.
- **HEAD** is a GET without the body.
- **Other methods:** POST to any other path, and PUT, DELETE, PATCH and
  OPTIONS, get 405.
- **The buffer (v8, SPEC_V8):** `/api/cockpit`, `/api/claims`,
  `/api/chain`, `/api/lllm` and `/api/nerves` keep their last good
  answer. A failed one (`"available": false`) is answered with the last
  good one, marked `stale`.

## 2. The write guard (v4, SPEC_V4)

A write must meet all of these:

- the host is `127.0.0.1:<port>` or `localhost:<port>`;
- any Origin is the same host;
- the request carries `X-Forge-Legacy: 1`;
- the content type is JSON;
- it has a Content-Length of at most 8192 bytes.

Otherwise it gets 403, 415, 400 or 413. On the VPS every write is
refused, because the host differs.

## 3. boot_v2.py

boot.py's supervisor (SPEC_V8):

- start in order, each waiting for the one before;
- an exponential cool-off;
- restart a child that exits;
- stop in reverse order.

It runs boot_v1_12's three services (SPEC_V1_12 §3):

1. **The Field:** `../scp-substrate/serve_v8.py`.
2. **ai-gate:** `../ai-gate/ai_gate_serve.py`, only when that checkout
   exists.
3. **The Legacy:** `legacy_v2.py`, with FORGE_FIELD_URL and
   FORGE_AI_GATE_URL set.

The flags are `--host`, `--port` (8080), `--field-port` (8085) and
`--ai-port` (8092). `python legacy_v2.py [--host] [--port]` keeps v10's
flags and exit codes: 2 on a bad argument.

## 4. The only differences from 1.12.0

Both are text that names the files to run, which the consolidation
renamed:

- **The startup banner** says `The Legacy 2.0.0` and `python boot_v2.py`.
  1.12.0 said `The Legacy (v10)` and `boot_v4.py`.
- **The "ai-gate is not running" message** names `boot_v2.py`, not
  `boot_v1_12.py`.

**Not changed:** the page keeps 1.12.0's text byte for byte, including
its Field hint naming `boot_v3.py` and `serve_v7.py`. That hint was
already stale in 1.12.0, and fixing it is not a consolidation's job
(NOTES).

## 5. The page: static/projection_v2.html

It is projection_v1_12.html with two header lines added at the top of
its comment. Nothing else changes. SPEC_V1_12 §2 describes it.

## 6. Tests

- **test_legacy_v2.py** is 1.12.0's suite (9 tests), pointed at
  legacy_v2 and boot_v2. The version check is `2.0.0-dev` until the
  freeze.
- **The twelve test_\*_at_v2.py suites** hold the 46 older tests that
  still describe 1.12.0 (CONSOLIDATION_V2 §8):
  - the old module names are imported as aliases of legacy_v2 or boot_v2;
  - every kept test is otherwise as frozen;
  - six of them had replaced checks cut, each cut marked with what
    replaced it.
- **The gate (CONSOLIDATION_V2 §3.3):**
  - 59 of 59 tests pass;
  - 1.12.0, run from a worktree of the tag v1.12.0, and 2.0.0 were run
    side by side against a copy of the real ~/.forge: 51 checks, 0
    differences. The only things set aside were λ and claim ages, which
    move with the time of the request, the buffer's `fetched_at`, and the
    §4 message;
  - boot_v2 started all three services, and they answered through the
    Legacy.

---

## Document control

- **SPEC V2 2.0.0**: 2026-11-20, by the VS Code AI on James's "go
  ahead" (CONSOLIDATION_V2.md). Not frozen.
