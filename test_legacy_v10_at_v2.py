"""
test_legacy_v10_at_v2.py — test_legacy_v10.py carried into The Legacy 2.0.0 (CONSOLIDATION_V2.md §3.2, §8)

Function:
    The tests of the frozen test_legacy_v10.py that describe 1.12.0, run against
    legacy_v2 / boot_v2: the old module names are imported as aliases of
    them, and every kept test is otherwise as frozen. Tests that describe
    behaviour 1.12.0 replaced are left out; a cut inside a kept test says
    what replaced it. The original is byte-identical in
    archive/1.12.0/test_legacy_v10.py. Its own header follows.

test_legacy_v10.py — The Legacy v10 (the briefing through Weaver v1.4, boot_v4) test suite

Function:
    Executable expression of SPEC_V11.md. Written before legacy_v10.py
    and boot_v4.py and run red first.

Functions in this file (pytest-collected):
    1. test_briefing_through_weaver_v1_4
    2. test_page
    3. test_boot_v4_order

Helpers:
    4. ENGINE — a stand-in engine cli.py that answers objects only
    5. _get   — GET a path from a running server

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V11.md 1.7.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.request

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot_v2 as boot  # noqa: E402
import legacy_v2 as legacy_v7  # noqa: E402
import legacy_v2 as legacy_v10  # noqa: E402

# 4. ENGINE — `cli.py gen <seed>`: a line for a bare object, a refusal otherwise
ENGINE = '''import sys
seed = sys.argv[2]
if seed in ("status", "design"):
    print("The envelope " + seed + " line.")
else:
    print("(nothing: the model refused to continue this seed)")
'''


# 5. _get
def _get(server, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}{path}", timeout=120) as r:
        return r.read().decode("utf-8")


# 1. test_briefing_through_weaver_v1_4
def test_briefing_through_weaver_v1_4(tmp_path, monkeypatch):
    assert legacy_v10._weaver().__name__ == "weaver_v1_4"
    # left with the archive: that frozen legacy_v7 still used weaver_v1_3 (CONSOLIDATION_V2 §8)
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "substrate-layer"))
    import substrate_v3
    key = Ed25519PrivateKey.generate()
    db = str(tmp_path / "forge.db")
    substrate_v3.init_db(db)
    for obj in ("status", "design"):
        substrate_v3.write_claim(db, {"subject": "envelope-layer", "object": obj, "FACT": "Frozen.",
                                      "UNKNOWN": f"What about the {obj}?", "face": "FACT", "polarity": "affirm"}, key)
    cli = tmp_path / "cli.py"
    cli.write_text(ENGINE, encoding="utf-8")
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.setenv("LLLM_HOME", str(tmp_path))
    monkeypatch.setenv("LLLM_CLI", str(cli))
    legacy_v10._BRIEFING_CACHE.update(ts=0, data=None)
    server = legacy_v10.make_server("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        d = json.loads(_get(server, "/api/weaver"))
    finally:
        server.shutdown()
        server.server_close()
        legacy_v10._BRIEFING_CACHE.update(ts=0, data=None)
    briefing = d.get("briefing") or ""
    lines = sorted(ln.strip() for ln in briefing.splitlines() if ln.strip().startswith("LLLM:"))
    assert lines == ["LLLM: The envelope design line.", "LLLM: The envelope status line."], d



