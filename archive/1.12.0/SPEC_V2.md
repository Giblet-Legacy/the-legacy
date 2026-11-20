# SPEC_V2 — the-legacy (Tier 1: The Legacy)

SPEC_V2.md — specification for `legacy_v2.py`, the resilient layer over
the frozen v1 shell (`legacy.py`).

Function:
    Restores SPEC.md §2.1 ("failures are captured, not raised") for
    `probe_layers()` without editing `legacy.py`. Everything else is
    inherited from v1 unchanged.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy.py (v0.1.1, frozen), SPEC.md 1.0.0
Version:  SPEC_V2 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

## 1. Relationship to v1

- `legacy.py` is frozen and is not edited (Immutable Rule).
- `legacy_v2.py` imports `legacy` and re-uses its layer loader, probe
  helpers, briefing, static serving, routing and read-only discipline.
- `python legacy_v2.py` is the entry point to run from v0.1.2 onwards.
  `python legacy.py` still works and behaves exactly as v0.1.1.

## 2. The defect v2 fixes

`legacy.probe_layers()` begins with
`from cryptography...ed25519 import Ed25519PrivateKey`, outside any
probe's `try`. That import is unused (P2 and P3 import it themselves).
If `cryptography` is absent, the function raises `ImportError` and
`GET /api/health` fails instead of returning 15 rows.

## 3. Function Contracts

### 3.1 probe_layers() -> list[dict]
Same 15 labels, same order and same checks as SPEC.md §2.1. Every
probe, including any import it needs, runs inside its own `try`.
Never raises. A missing `cryptography` yields FAIL for P2 and P3 only.

### 3.2 get_briefing() -> dict
Re-exported from v1 unchanged (SPEC.md §2.2).

### 3.3 make_server(host, port)
As v1, but with a handler that serves `/api/health` from v2's
`probe_layers()`. Every other route, method and the 405/404/400 rules
are v1's (SPEC.md §3).

### 3.4 main(argv) -> int
Same flags (`--host`, `--port`), defaults and exit codes as SPEC.md §2.3.
