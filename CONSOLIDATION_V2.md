# CONSOLIDATION V2 — the-legacy 1.12.0 -> 2.0.0 (plan)

CONSOLIDATION_V2.md — the plan for flattening The Legacy's layer chain into one clean 2.0.0.

Function:
    James (2026-11-20): "freeze then plan 2.0.0 consolidation". 1.12.0 is
    frozen. This is the plan for 2.0.0 under his consolidation rule
    (2026-11-16: "consolidate what is if adding more its a new v"): one
    clean major version, identical behaviour, old layers archived
    byte-identical, nothing added and nothing fixed. Planned, not
    started; waiting for James's sign-off on §6.

Version:  plan, draft 2 (2026-11-20: decisions and Step 0)
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

## 6. Decisions (James, 2026-11-20: "yes to all 4 1 archive folder and no to s24")

1. Behaviour is what boot_v1_12 does.
2. The work is on branch `consolidate-2.0.0`, merged once at the freeze.
3. One archive folder: `archive/1.12.0/`.
4. No S24 run; the laptop is enough.

## 8. Step 0 result (2026-11-20)

**How it was run:**
- The tag `v1.12.0` was made, and the work is on branch
  `consolidate-2.0.0`.
- A scratchpad pytest plugin swapped every old `make_server` for 1.12.0's,
  every old `boot_vN.main` for `boot_v1_12.main`, and every old legacy
  `main` for 1.12.0's. legacy_v10's `main` was left alone, because 1.12.0
  runs through it.
- No file in the repository changed.

**What a pass or a fail meant:**
- A passing test counts as live only if it actually goes through 1.12.0's
  server or boot.
- A test that only calls an old helper 1.12.0 no longer reaches, or starts
  an old file in a subprocess, passes trivially. It was counted as
  replaced.
- Five failing tests mixed live and replaced checks. Their live checks
  were split out and run alone against 1.12.0, and they pass.

**The totals:** 75 old tests. **41 are live** and carried as they are, **5
are mixed** (only the live checks are carried), and **29 are replaced**.
test_legacy_v1_12's 9 tests become test_legacy_v2.py.

### Live, carried as `<suite>_at_v2.py` (41)

| Old suite | Tests |
|---|---|
| test_legacy | health_endpoint_returns_json, index_returns_html, post_returns_405, path_traversal_blocked, unknown_route_returns_404, weaver_endpoint_returns_json |
| test_legacy_v2 | v2_head_health, v2_health_survives_missing_cryptography, v2_index_and_weaver_inherited, v2_post_returns_405, v2_main_rejects_bad_args |
| test_legacy_v3 | health_runs_current_layers (v3.probe_layers is what /api/health calls), nerves_states (v3.get_nerves is what /api/nerves calls) |
| test_legacy_v4 | read_routes, echo_route, inbox_write_and_commit, inbox_guards, voice |
| test_legacy_v5 | claims_route, chain_route, v4_routes_inherited |
| test_legacy_v6 | claims_have_every_face, chain_kind_filter |
| test_legacy_v7 | voice_speaks_text_and_aspects |
| test_legacy_v8 | backoff, supervisor_order_and_restarts (boot.py's, used by boot_v1_12), server_buffer (v8.buffered is in 1.12.0's chain) |
| test_legacy_v10 | briefing_through_weaver_v1_4 |
| test_legacy_v11 | field_url_unchanged_without_the_variable, field_url_public_path, field_url_bad_values_ignored (5 cases) |
| test_legacy_v12 | inbox_lists_each_kind, nouns_empty_without_a_database, nouns_registered_and_drafted, page, post_drafts_of_each_kind, post_refusals |
| test_legacy_v1_11 | inbox_in_the_order_posted, nouns_drafts_in_the_order_written, page, posts_and_refusals_as_v12 |

### Mixed: only the live checks are carried (5)

| Test | Carried | Replaced, and by what |
|---|---|---|
| v3 test_http | health has 15 layers; nerves unavailable; POST /api/health is 405 | the briefing via `legacy_v3._weaver` (v10's Weaver v1.4) |
| v4 test_lllm_and_field_states | /api/field unreachable, then reachable | "LLLM unavailable" with no LLLM_HOME (v7's /api/lllm) |
| v6 test_older_routes_inherited | health has 15 layers; cockpit total | the Voice reply's wording (v7's Voice) |
| v7 test_briefing_and_lllm_with_engine | /api/lllm build; /api/cockpit total | the briefing's LLLM line (v10) |
| v7 test_page_and_inherited_routes | /api/claims; /api/chain?kind=claim | projection_v7.html (the 1.12 page) |

### Replaced, left in the archive (29)

| Why | Tests |
|---|---|
| Old helpers that 1.12.0 no longer reaches | legacy: probe_layers ×4, get_briefing ×3; v2: v1_raises_without_cryptography, v2_captures_missing_cryptography, v2_probe_layers_matches_v1, get_briefing_is_v1; v3: weaver_finds_real_claims; v4: briefing_from_any_directory (v4._weaver, in a subprocess) |
| Old pages | v4, v5, v6, v9 page tests, v10 test_page, v8 test_page (reads projection_v8.html), v9 phone_tables (projection_v9 in a browser) |
| Old briefing format | v7 briefing_without_engine (v10 replaced it) |
| Old boots (two services; 1.12.0 starts three) | boot_v2, boot_v5, v9 boot_v3_order, v10 boot_v4_order, v11 boot_v6_order_and_env, v12 boot_v7_order, v1_11 boot_v1_11_order. test_legacy_v1_12's boot test covers boot_v1_12. |
| Old boot.py started in a subprocess | v8 boot_end_to_end |

**One gap to note:** v8's boot_end_to_end is the only test that boots
the real processes, and it boots 1.4.0's `boot.py`. 1.12.0 has no
end-to-end test. Nothing is added in a consolidation, so the §3.3
side-by-side run stands in for it. A boot_v2 end-to-end test can come
afterwards, as 2.1.0.

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
