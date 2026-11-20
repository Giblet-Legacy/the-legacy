# CONSOLIDATION V2 — the-legacy 1.12.0 -> 2.0.0 (plan)

CONSOLIDATION_V2.md — the plan for flattening The Legacy's layer chain into one clean 2.0.0.

Function:
    James (2026-11-20): "freeze then plan 2.0.0 consolidation". 1.12.0 is
    frozen. This is the plan for 2.0.0 under his consolidation rule
    (2026-11-16: "consolidate what is if adding more its a new v"): one
    clean major version, identical behaviour, old layers archived
    byte-identical, nothing added and nothing fixed. Planned, not
    started; waiting for James's sign-off on §6.

Version:  plan, draft 1 (2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)

---

## 1. Why now

- **The chain is too deep.** Running 1.12.0 runs 14 module layers:
  legacy -> v2 -> ... -> v12 -> v1_11 -> v1_12. The handler is a class
  13 subclasses deep. `main` gets through by monkeypatching
  `legacy_v10.make_server`. The trigger was "5+ layers deep, or a layer
  patches the one below"; the Legacy passes both.
- **The names don't say their version.** `legacy_v2.py` to `legacy_v12.py`,
  `boot_v2.py` to `boot_v7.py` and `SPEC_V2.md` to `SPEC_V14.md` are old
  counter names (roadmap NAMING.md). 2.0.0 is where the Legacy comes into
  line.
- **The size of it today:**
  - 14 legacy modules (about 2,900 lines);
  - 9 boot files;
  - 16 SPECs;
  - 10 pages (about 5,000 lines);
  - 16 test files with 88 tests.

## 2. What 2.0.0 is

**The behaviour of 2.0.0 is exactly what `python boot_v1_12.py` does
today.** That means:

- the same endpoints;
- the same answers;
- the same guard;
- the same page;
- the same boot order (the Field, ai-gate, the Legacy);
- the same flags and exit codes.

What 2.0.0 does **not** keep is behaviour that only an older entry point
had and 1.12.0 has replaced, such as legacy.py's v1 page at `/`. Those
stay runnable from `archive/1.12.0/`.

| 2.0.0 file | Made from |
|---|---|
| `legacy_v2.py` | The 1.12.0 chain, flattened into one module and one handler class. Only the code 1.12.0 actually reaches is kept; no monkeypatching. |
| `boot_v2.py` | `boot.py` plus `boot_v1_12.py`, as one file. |
| `static/projection_v2.html` | `projection_v1_12.html`, byte for byte, apart from its header comment. |
| `SPEC_V2.md` | One spec describing 2.0.0 as it is, gathered from SPEC.md to SPEC_V1_12.md. It cites them and does not re-decide anything. |
| `test_legacy_v2.py` (plus `_at_v2` suites) | The contract (§3). |

**What it still depends on stays the same:**

- Cockpit forge_cli_v1_8;
- Weaver v1.4;
- the LLLM Voice (`../lllm`);
- SC-OS nerves;
- P9 substrate_v4;
- the Field, serve_v8 (`../scp-substrate`);
- ai-gate's local API.

Each of those is pinned at the version 1.12.0 uses.

## 3. The contract: which tests carry forward

Many old tests describe behaviour that 1.12.0 has since replaced, so
they can't all simply be pointed at v2. The contract is found by
running them, not by guessing:

1. **Step 0, before any new code:**
   - Run each of the 16 old suites with its server and `main` swapped for
     1.12.0's. That's a throwaway harness in the scratchpad; no file in the
     repository changes.
   - A test that passes against 1.12.0 describes live behaviour. A test that
     fails describes behaviour 1.12.0 replaced.
   - Write the result into this plan, one row per test, for James to see.
2. **Every live test is carried forward against v2:**
   - Suites carried with a change become `<suite>_at_v2.py`, per NAMING.md
     (e.g. `test_legacy_v4_at_v2.py`).
   - test_legacy_v1_12 becomes `test_legacy_v2.py`.
   - Nothing is added; a known flake (Q18's race) stays a known flake.
3. **The 2.0.0 gate:**
   - every carried test passes against v2;
   - the same tests pass against 1.12.0 in the archive;
   - a side-by-side run (1.12.0 and 2.0.0 on spare ports, against a copy of
     the real forge.db) gives identical JSON from every GET endpoint, and
     an identical page apart from its header comment.

## 4. The order of work

1. **Tag `v1.12.0`** on the frozen commit. There are no tags yet; the
   archive and the tag both point at the same bytes.
2. **Branch `consolidate-2.0.0`.** main stays on 1.12.0 throughout, so
   the VPS keeps serving it (§5).
3. **Step 0 (§3.1), then the table goes to James.**
4. **Move the old files into `archive/1.12.0/` with `git mv`.** They stay
   byte-identical. That covers every legacy*.py, boot*.py, SPEC*.md,
   test_*.py and static/*.html, and `pytest.ini` keeps archive/ out of
   collection (as the Cockpit's does). The archive runs on its own, since
   its files import their siblings.
5. **Write the contract tests (§3.2) first and run them red.** Then
   write legacy_v2, boot_v2, projection_v2 and SPEC_V2 until they're
   green.
6. **Run the gate (§3.3)** on the laptop, with an S24 run if James wants
   one.
7. **Update the documents:**
   - README, CLAUDE.md and NOTES;
   - CHANGELOG (Good/Bad/Ugly);
   - NAMING.md: the-legacy leaves the old-names table;
   - roadmap STATUS and VPS.md.
   - The agent's naming and archive checks should then pass with no
     Legacy warnings.
8. **Freeze on James's word:**
   - every header says `2.0.0`;
   - VERSION goes to 2.0.0;
   - merge to main in **one** commit;
   - tag `v2.0.0`.

## 5. The VPS

- run-latest v2 picks the root `boot*.py` with the highest header
  Version that isn't -dev and isn't above VERSION. If no boot qualifies,
  it falls back to `boot.py`.
- **Moving the old boots into archive/ on main before 2.0.0 is frozen
  would leave the VPS with nothing to run.** The work stays on the
  branch, and the archive move, the new files and VERSION 2.0.0 land on
  main together.
- After the merge, `sudo legacy-refresh` should log `run-latest:
  boot_v2.py`. If it doesn't, `git revert` of the merge puts 1.12.0 back.
- Before 2.0.0 starts, 1.12.0 reaches the VPS on its next refresh,
  because VERSION is now 1.12.0. It will start ai-gate only if
  `/srv/legacy/src/ai-gate` exists. Either way, asks are refused there
  (no key, view-only guard).

## 6. Decisions for James

1. **Is "behaviour = what boot_v1_12 does" right?** The alternative,
   keeping every old entry point's behaviour in v2, would rebuild the
   pile.
2. **Is the branch, merged at freeze, OK?** It's the only way to keep
   the VPS running throughout.
3. **Archive layout:** one `archive/1.12.0/` holding everything (simple,
   and runnable as-is), or one folder per old version (closer to the
   history, but it won't run as-is). The recommendation is the first.
4. **The S24:** should 2.0.0 also be confirmed on the S24 before the
   freeze?

## 7. Left out on purpose

- **The Field (scp-substrate serve_v8)** and **the Cockpit** are due
  their own consolidations. Not this one.
- **docs/ancestor-the-full-stack.md** is a the-full-stack tie (reference
  only, 2026-11-18). It needs its own decision to remove it, not this
  consolidation.
- **Text that names old files stays as it is.** That includes frozen
  files elsewhere (Cockpit v1.1's `legacy_v3.py` hint) and seed claims
  ("legacy_v6 is frozen at 1.2.0"). Those are history, and they're still
  true of the archive.
- **ai-gate stays 0.1.0-dev.** The Legacy relays only to its HTTP
  paths, so 2.0.0 doesn't need it frozen.
