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
Status:   0.1.3 (Phase 1, The Shell, on the current layers — see VERSION)

## Running

    python legacy_v3.py [--host 127.0.0.1] [--port 8080]
    python -m pytest -q

`legacy.py` is the frozen v1 shell, `legacy_v2.py` the layer over it
(SPEC_V2.md), and `legacy_v3.py` the layer over that (SPEC_V3.md:
current-layer health, Weaver v1.1, /api/nerves). Run v3.

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
