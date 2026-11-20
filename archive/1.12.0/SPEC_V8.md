# SPEC V8 — the-legacy (The Legacy v8: boot together, cool off, refresh, buffer)

SPEC_V8.md — specification for legacy_v8.py, boot.py and static/projection_v8.html, over The Legacy v7 (1.3.0).

Function:
    James (2026-11-14): "substrate is not running can we get both the
    legacy and substrate to boot one after another and have
    exponential cool off and refresh and hold a buffer". v8 adds a
    launcher that starts the Field, then The Legacy, and keeps both
    running; a server-side buffer of the last good status; and a page
    that refreshes itself, backs off exponentially while a source is
    down, and keeps showing its last good data. SPEC_V7.md remains
    authoritative for everything this document does not change.
    legacy.py and legacy_v2–v7 are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v7.py (1.3.0); SCP Substrate serve_v5 (started by boot.py)
Version:   SPEC V8 1.4.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Cool-off

`backoff(attempt, base, cap) = min(cap, base × 2^(attempt − 1))` for
attempt ≥ 1. Every retry in v8 uses it.

## 2. boot.py

`python boot.py [--host 127.0.0.1] [--port 8080] [--field-port 8085]`

1. Starts the Field: `python ../scp-substrate/serve_v5.py --port <field-port> --quiet`
   (its database is `$FORGE_HOME/forge.db`, as always).
2. Waits until `http://127.0.0.1:<field-port>/api/health` answers (any
   HTTP status), polling with `backoff(n, 0.25, 4)`, for at most 60 s.
3. Starts The Legacy: `python legacy_v8.py --host … --port …`, with
   `FORGE_FIELD_URL` set to the Field's URL, and waits for it to accept
   connections the same way.
4. Supervises both. When a child exits, it is restarted after
   `backoff(failures, 1, 60)` seconds; `failures` resets to 0 once a
   child has stayed up for 60 s. A child that never comes up within
   the wait counts as a failure.
5. Ctrl-C stops The Legacy, then the Field, and exits 0.

Lines are logged as `[boot HH:MM:SS] …`. The supervisor is a class
(`Service`, `Supervisor`) with injectable clock, sleep and process
start, so it can be tested without real waits.

## 3. Server buffer (legacy_v8.py)

For `/api/cockpit`, `/api/claims`, `/api/chain`, `/api/lllm` and
`/api/nerves`, each 200 response is buffered per path and query. A
response that failed (a dict with `available: false`) is replaced by
the last good one for the same key, with `stale: true`,
`stale_since: <ISO time of that good one>` and `stale_error: <the new
error>`. Good responses carry `fetched_at`. Every other route is v7's.
`/` serves `static/projection_v8.html`.

## 4. The page (projection_v8.html)

- Each panel refreshes itself: health 60 s, Cockpit status 15 s,
  claims 30 s, ledger 15 s, inbox 30 s, network 60 s, briefing and
  LLLM 300 s.
- A failed or stale refresh keeps the panel's last good data on
  screen, marked stale, and retries after `backoff(n, 2, 60)` seconds;
  a good one resets the count.
- The Field panel checks `/api/field` with `backoff(n, 2, 30)` while
  the Field is down, shows the iframe as soon as it is up, keeps the
  iframe while it reconnects, and reloads it when it is back; once up
  it checks every 30 s.
- Claims are fetched with `limit=500`, so the panel and the face counts
  cover every claim, not the last 60.
- Hints name `python boot.py` and `serve_v5.py`.

## 5. main (legacy_v8.py)

As v7, with the v8 page and buffer.

## 6. Tests (test_legacy_v8.py)

- backoff values and cap.
- Supervisor: starts the Field before The Legacy and waits for each;
  restarts an exited child after backoff(1), backoff(2), …; resets after
  60 s up; stops both on stop().
- The server buffer: a good response is stored; a later failure returns
  the stored one marked stale; no buffer → the failure as is.
- `/` serves the v8 page with the refresh, backoff and buffer code and
  `limit=500`.
- End to end: boot.py starts serve_v5 and legacy_v8 on free ports
  against a real FORGE_HOME, and The Legacy reports the Field reachable.

---

## Document control

- **SPEC V8 1.4.0** — 2026-11-14, by the VS Code AI on James's delegation.
