# SPEC V13 — the-legacy (legacy_v11 + boot_v6: one link, the Field inside it)

SPEC_V13.md — specification for legacy_v11.py and boot_v6.py.

Function:
    James (2026-11-16), on the read-only copy on the VPS: the Legacy
    page's Field section points at 127.0.0.1:8085, which only the
    server itself can reach, and the Field's own port is not reachable
    from his phone; "i would prefer just a single weblink". The Field is
    published under the Legacy's own address at /field/, and the page
    must be told that address instead of the one the server probes.
    v11 separates the two. Where this document is silent, SPEC_V12.md
    applies. legacy.py, legacy_v2–v10, boot.py and boot_v2–v5 and their
    pages are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v10.py (1.7.0), boot.py (SPEC_V8.md), ../scp-substrate/serve_v8.py
Version:   SPEC V13 1.9.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. legacy_v11.py: the Field's address for the browser

`GET /api/field` returns `{"url": U, "reachable": R}` as v4 does, with:

- **R** still from probing `FORGE_FIELD_URL` (the address the server
  itself reaches the Field at; boot sets it to `http://127.0.0.1:<field
  port>/`). Unchanged.
- **U** = `FORGE_FIELD_PUBLIC_URL` if it is set and not empty, else the
  probed URL as before. It is the address the page puts in its iframe
  and link, so on a laptop (no variable) nothing changes; on the VPS it
  is `/field/`, a path on the same link.
- `FORGE_FIELD_PUBLIC_URL` must be a path starting with `/` or an
  `http://` / `https://` URL. Anything else is ignored (the probed URL
  is used), so a bad value can never put a `javascript:` or other
  scheme in the page.

Every other route, the page, the POST guard and the flags are v10's.

## 2. boot_v6.py

`python boot_v6.py [--host H] [--port N] [--field-port N]` does exactly
what boot_v5.py does (serve_v8.py as the Field) with legacy_v11.py as
The Legacy. `FORGE_FIELD_PUBLIC_URL`, if set in boot's environment,
reaches the Legacy unchanged (boot passes its environment through).

## 3. On the VPS (roadmap VPS.md)

Tailscale Serve publishes The Legacy at `/` and the Field at `/field`
(prefix stripped) on the one tailnet address; the service sets
`FORGE_FIELD_PUBLIC_URL=/field/` and runs boot_v6.py.

## 4. Tests (test_legacy_v11.py)

- `/api/field` without the variable: the probed URL, as v10.
- With `FORGE_FIELD_PUBLIC_URL=/field/`: url `/field/`, reachable still
  from the probe (a live stand-in Field answers `/api/health`).
- A bad value (`javascript:alert(1)`, `ftp://x`, `field`) is ignored.
- boot_v6 starts serve_v8.py (quiet), then legacy_v11.py, and passes
  `FORGE_FIELD_PUBLIC_URL` through.

---

## Document control

- **SPEC V13 1.9.0** — 2026-11-16, by the VS Code AI on James's request ("just a single weblink").
