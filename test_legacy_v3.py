"""
test_legacy_v3.py — The Legacy v3 (current-layer dashboard) test suite

Function:
    Executable expression of SPEC_V3.md. Written before legacy_v3.py
    and run red first.

Functions in this file (pytest-collected):
    1. test_health_runs_current_layers
    2. test_weaver_finds_real_claims
    3. test_nerves_states
    4. test_http

Fixtures and helpers:
    5. home   — FORGE_HOME with a P9 substrate holding one dream
    6. _get   — HTTP GET/POST against a running server

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V3.md 1.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "substrate-layer"), os.path.join(ROOT, "..", "sc-os")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import legacy  # noqa: E402
import legacy_v3  # noqa: E402
import substrate_v3  # noqa: E402
import pins  # noqa: E402
import envelope_v2  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 5. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("SSLKEYLOGFILE", raising=False)
    legacy_v3._BRIEFING_CACHE.update(ts=0.0, data=None)
    legacy._BRIEFING_CACHE.update(ts=0.0, data=None)
    db = str(tmp_path / "forge.db")
    substrate_v3.init_db(db)
    substrate_v3.write_claim(db, {"subject": "tide", "object": "late",
                                  "UNKNOWN": "Why is the tide late?", "face": "UNKNOWN"}, KEY)
    return tmp_path


# 6. _get
def _get(base, path, method="GET"):
    req = urllib.request.Request(base + path, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None


# 1. test_health_runs_current_layers
def test_health_runs_current_layers():
    rows = legacy_v3.probe_layers()
    assert [r["layer"].split()[0] for r in rows] == [f"P{i}" for i in range(1, 16)]
    assert all(r["status"] == "PASS" for r in rows), [r for r in rows if r["status"] != "PASS"]


# 2. test_weaver_finds_real_claims
def test_weaver_finds_real_claims(home, monkeypatch):
    weaver_v1_1 = legacy_v3._weaver()
    monkeypatch.setattr(weaver_v1_1, "call_lllm", lambda prompt: "Morning: chase the tide.")
    out = legacy_v3.get_briefing()
    assert out["error"] is None and out["briefing"] == "Morning: chase the tide."
    assert [c["subject"] for c in out["claims"]] == ["tide"]
    assert legacy._compute_briefing()["error"] == "no UNKNOWN claims to weave"  # v1, pinned


# 3. test_nerves_states
def test_nerves_states(home):
    assert legacy_v3.get_nerves() == {"available": False, "nerves": None, "error": None}
    path = os.path.join(str(home), "sc-os", "pins.sc.json")
    os.makedirs(os.path.dirname(path))
    peer = envelope_v2.did_key_encode(Ed25519PrivateKey.generate().public_key())
    pins.PinStore(path, KEY).add(peer, "127.0.0.1:9001")
    out = legacy_v3.get_nerves()
    assert out["available"] is True and out["nerves"]["peers"] == [peer]
    data = open(path, "rb").read()
    open(path, "wb").write(data.replace(b"9001", b"9002"))
    out = legacy_v3.get_nerves()
    assert out["available"] is False and out["nerves"] is None and out["error"]


# 4. test_http
def test_http(home, monkeypatch):
    monkeypatch.setattr(legacy_v3._weaver(), "call_lllm", lambda prompt: "ok")
    srv = legacy_v3.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        status, body = _get(base, "/api/health")
        assert status == 200 and len(body["layers"]) == 15
        status, body = _get(base, "/api/weaver")
        assert status == 200 and body["briefing"] == "ok"
        status, body = _get(base, "/api/nerves")
        assert status == 200 and body["available"] is False
        assert _get(base, "/api/health", method="POST")[0] == 405
    finally:
        srv.shutdown()
        srv.server_close()
