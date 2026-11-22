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
Status:   2.1.0 (frozen 2026-11-22) — first-time guidance and Advanced navigation
          (SPEC_V2_1.md): legacy_v2_1.py, boot_v2_1.py, static/projection_v2_1.html.
          2.0.0 (CONSOLIDATION_V2.md, SPEC_V2.md) remains unchanged.
          1.12.0 and everything before it is byte-identical in
          archive/1.12.0/ and at the tag v1.12.0.

## Running

The 2.1.0 interface keeps the 2.0.0 routes and groups Ledger and System
under Advanced. The 2.0.0 entry points remain available.

    python boot_v2_1.py                      # the Field, ai-gate, then The Legacy 2.1.0, kept running
    python legacy_v2_1.py [--host 127.0.0.1] [--port 8080]
    python ../scp-substrate/serve_v8.py      # the 3D Field alone, embedded on the page
    # the AI (optional, the gate only): GEMINI_API_KEY and FORGE_GEMINI_MODEL
    # LLLM engine (optional): LLLM_HOME=<engine var dir>, LLLM_CLI=<engine>/lllm/cli.py
    python -m pytest -q

Open <http://127.0.0.1:8080/>. Ctrl-C stops all three.

## On the phone (Termux)

Paste this into Termux. Change the first line if the repos are cloned
somewhere other than `~/Giblets_Legacy`.

```bash
cd ~/Giblets_Legacy
for r in scp-substrate the-legacy the-weaver; do (cd "$r" && git pull --ff-only && git log --oneline -1); done
(cd scp-substrate && python -m pytest -q)    # browser tests skip: Termux has no Edge or Chrome
(cd the-legacy && python -m pytest -q)
(cd the-weaver && python -m pytest -q)
echo "LLLM_HOME=$LLLM_HOME LLLM_CLI=$LLLM_CLI"
ls "${LLLM_HOME:-$HOME/lllm/var}/models" 2>&1   # is there an LLLM engine build on this phone?
cd the-legacy && python boot_v2_1.py
```

Then open <http://127.0.0.1:8080/> in the phone's browser. The Claims
and Ledger tables should read as full sentences (no hash columns), and
the Field's orb names should not sit on top of each other.
`termux-wake-lock` keeps it running with the screen off; Ctrl-C stops them all.

From 2.0.0 The Legacy is one module (`legacy_v2.py`), one boot
(`boot_v2.py`) and one page (`static/projection_v2.html`), described by
`SPEC_V2.md`. The fourteen layers it replaced (legacy.py to
legacy_v1_12.py, boot.py to boot_v1_12.py, SPEC.md to SPEC_V1_12.md) are
in `archive/1.12.0/`. They import their siblings through `../`, so to run
1.12.0 itself, check out the tag: `git worktree add ../the-legacy-1.12.0
v1.12.0`.

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
