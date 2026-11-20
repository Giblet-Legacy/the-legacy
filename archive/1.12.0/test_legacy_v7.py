"""
test_legacy_v7.py — The Legacy v7 (the LLLM wired through) test suite

Function:
    Executable expression of SPEC_V7.md. Written before legacy_v7.py and
    run red first. A real FORGE_HOME is built through Cockpit v1.3; the
    engine is a stand-in cli.py reached through LLLM_CLI.

Functions in this file (pytest-collected):
    1. test_voice_speaks_text_and_aspects
    2. test_briefing_without_engine
    3. test_briefing_and_lllm_with_engine
    4. test_page_and_inherited_routes

Fixtures and helpers:
    5. home   — FORGE_HOME with two ledger-layer cubes (one with UNKNOWN)
    6. server — a running v7 server
    7. _req   — GET → (status, JSON or text)
    8. ENGINE — a stand-in engine cli.py

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V7.md 1.3.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "explorer-d334-forge")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import legacy_v7  # noqa: E402
import forge_cli_v1_3 as cockpit  # noqa: E402

KEY = Ed25519PrivateKey.generate()
STATUS = "ledger_v2 is frozen at 2.0.0; 18/18 tests pass."
PURPOSE = "ChronoSCRIBE: the hash-chained, append-only ledger."

# 8. ENGINE
ENGINE = '''import sys
if sys.argv[1] == "info":
    print("build:   abc123def456")
else:
    print(sys.argv[2] + " keeps every entry in order")
'''


# 7. _req
def _req(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            status, raw, ctype = r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        status, raw, ctype = e.code, e.read(), e.headers.get("Content-Type", "")
    return status, (json.loads(raw) if "json" in ctype and raw else raw.decode("utf-8", "replace"))


# 5. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    forge = tmp_path / "forge"
    forge.mkdir()
    monkeypatch.setenv("FORGE_HOME", str(forge))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    monkeypatch.delenv("LLLM_CLI", raising=False)
    monkeypatch.delenv("SSLKEYLOGFILE", raising=False)
    monkeypatch.setenv("FORGE_FIELD_URL", "http://127.0.0.1:9/")
    pem = KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(b"test"))
    (forge / "key.pem").write_bytes(pem)
    cockpit.commit_cube("ledger-layer", "status", {"FACT": STATUS, "OPINION": "a private opinion",
                                                   "UNKNOWN": "How large can it grow?"}, KEY)
    cockpit.commit_cube("ledger-layer", "P4 Ledger", {"FACT": PURPOSE}, KEY)
    legacy_v7._BRIEFING_CACHE.update(ts=0.0, data=None)
    yield tmp_path


# 6. server
@pytest.fixture
def server(home):
    srv = legacy_v7.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


# 1. test_voice_speaks_text_and_aspects
def test_voice_speaks_text_and_aspects(server):
    q = lambda text: _req(server + "/api/voice?" + urllib.parse.urlencode({"q": text}))[1]  # noqa: E731
    d = q("what is the status of the ledger-layer?")
    assert d["available"] and d["reply"].startswith(f"ledger-layer (status): {STATUS} [")
    d = q("what is the ledger-layer?")
    lines = d["reply"].split("\n")
    assert len(lines) == 2 and all(line.startswith("ledger-layer (") for line in lines)
    assert "private opinion" not in d["reply"] and "How large" not in d["reply"]


# 2. test_briefing_without_engine
def test_briefing_without_engine(server):
    status, d = _req(server + "/api/weaver")
    assert status == 200 and d["error"] is None
    assert "1. ledger-layer / status" in d["briefing"] and "How large can it grow?" in d["briefing"]
    assert "(LLLM unavailable: " in d["briefing"] and len(d["claims"]) == 1


# 3. test_briefing_and_lllm_with_engine
def test_briefing_and_lllm_with_engine(home, monkeypatch):
    engine_home = home / "lllm"
    (engine_home / "models" / "abc123def456").mkdir(parents=True)
    (engine_home / "models" / "abc123def456" / "build.json").write_text(json.dumps({"identity": {"code": {}}}))
    cli_py = home / "cli.py"
    cli_py.write_text(ENGINE)
    monkeypatch.setenv("LLLM_HOME", str(engine_home))
    monkeypatch.setenv("LLLM_CLI", str(cli_py))
    srv = legacy_v7.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        _, d = _req(base + "/api/weaver")
        assert "LLLM: ledger-layer keeps every entry in order" in d["briefing"]
        _, d = _req(base + "/api/lllm")
        assert d["available"] and d["build_id"] == "abc123def456" and d["anchored"] is False
        _, d = _req(base + "/api/cockpit")
        assert d["available"] and d["status"]["claims"]["total"] == 2
    finally:
        srv.shutdown()
        srv.server_close()


# 4. test_page_and_inherited_routes
def test_page_and_inherited_routes(server):
    status, page = _req(server + "/")
    assert status == 200 and "projection_v7.html" in page
    assert "forge_cli_v1_3.py inbox commit" in page and "serve_v4.py" in page and "pre-line" in page
    status, d = _req(server + "/api/claims")
    assert status == 200 and d["available"] and len(d["claims"]) == 2
    assert _req(server + "/api/chain?kind=claim")[1]["matched"] == 2
