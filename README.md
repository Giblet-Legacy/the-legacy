# the-legacy — Tier 1: The Legacy

README.md — repository purpose and consumer contract for The Legacy.

Function:
    The final consumer. The master orchestrator. A unified web
    dashboard that surfaces the outputs of every other consumer in
    The Forge Stack. It is the projection of the self — one window
    through which the operator sees their substrate, their briefing,
    their network, and their simulations.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  All consumers (Cockpit, Substrate, Weaver, SC-OS, Echo)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   1.3.0 — v1.0.0 The Projection (legacy_v4), v1.1.0 its redesign
          (legacy_v5), v1.2.0 multi-face claims (legacy_v6); all frozen.
          legacy_v7 (SPEC_V7.md: the LLLM wired through) frozen at 1.3.0.
          legacy_v8 + boot.py (1.4.0), boot_v2 (1.5.0) and legacy_v9 +
          boot_v3 (1.6.0, the page on a phone) built, not frozen.

## Running

    python boot_v3.py                        # the Field (v7), then The Legacy (v9), kept running
    python legacy_v9.py [--host 127.0.0.1] [--port 8080]
    python ../scp-substrate/serve_v7.py      # the 3D Field alone, embedded on the page
    # LLLM engine (optional): LLLM_HOME=<engine var dir>, LLLM_CLI=<engine>/lllm/cli.py
    python -m pytest -q

Open <http://127.0.0.1:8080/>. Ctrl-C stops both.

## On the phone (Termux)

Paste this into Termux. Change the first line if the repos are cloned
somewhere other than `~/Giblets_Legacy`.

```bash
cd ~/Giblets_Legacy
for r in scp-substrate the-legacy; do (cd "$r" && git pull --ff-only && git log --oneline -1); done
(cd scp-substrate && python -m pytest -q)    # browser tests skip: Termux has no Edge or Chrome
(cd the-legacy && python -m pytest -q)
echo "LLLM_HOME=$LLLM_HOME LLLM_CLI=$LLLM_CLI"
ls "${LLLM_HOME:-$HOME/lllm/var}/models" 2>&1   # is there an LLLM engine build on this phone?
cd the-legacy && python boot_v3.py
```

Then open <http://127.0.0.1:8080/> in the phone's browser. The Claims
and Ledger tables should read as full sentences (no hash columns), and
the Field's orb names should not sit on top of each other.
`termux-wake-lock` keeps it running with the screen off; Ctrl-C stops both.

`legacy.py` is the frozen v1 shell, `legacy_v2.py` the layer over it
(SPEC_V2.md), and `legacy_v3.py` the layer over that (SPEC_V3.md:
current-layer health, Weaver v1.1, /api/nerves), and so on up to
`legacy_v9.py` (SPEC_V10.md; every layer is listed in CLAUDE.md). Run
`boot_v3.py`.

## What The Legacy shows

- **Health** — the 15-layer stack, probed live (via `forge health`).
- **The Field** — the 3D substrate (via `scp-substrate`).
- **The Voice** — the Weaver's morning briefing (via `the-weaver`).
- **The Cockpit** — a browser form to `remember` a claim (via `the-echo`
  preview, then `explorer-d334-forge` to commit).
- **The Nerves** — active peers and handshake status (via `sc-os`).

## Phase plan

- **v0.1.0** — The Shell. Dashboard with health + weaver widgets.
- **v0.2.0** — The Field. Embed `scp-substrate`.
- **v0.3.0** — The Cockpit. Form + Echo preview + commit.
- **v0.4.0** — The Nerves. Peer status from SC-OS.
- **v1.0.0** — The Projection. Full unification, frozen.

## What it is not
- Not a replacement for any other consumer.
- Not the primitives. The primitives are beneath it.
- Not finished until every consumer is surfaced.

"I wanted it. So I forged it. Now forge yours."
— James Gilbert (Giblets Forge)
