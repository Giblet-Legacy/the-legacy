"""
test_legacy_v6.py — The Legacy v6 (multi-face claims) test suite

Function:
    Executable expression of SPEC_V6.md. Written before legacy_v6.py
    and run red first. The Cockpit writes a single-face claim, a
    multi-face cube and a sealed approval; the v6 server is exercised
    over HTTP.

Functions in this file (pytest-collected):
    1. test_claims_have_every_face
    2. test_chain_kind_filter
    3. test_page
    4. test_older_routes_inherited

Fixtures and helpers:
    5. home   — FORGE_HOME: sky (FACT), ledger-layer (FACT + CONTEXT + UNKNOWN), sky sealed
    6. server — a running v6 server; yields its base URL
    7. _req   — HTTP GET returning (status, json-or-text)

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V6.md 1.0.0
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

import legacy_v6  # noqa: E402
import forge_cli_v1_2 as cockpit  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 7. _req
def _req(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            status, raw, ctype = r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        status, raw, ctype = e.code, e.read(), e.headers.get("Content-Type", "")
    return status, (json.loads(raw) if "json" in ctype and raw else raw.decode("utf-8", "replace"))


# 5. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    monkeypatch.delenv("SSLKEYLOGFILE", raising=False)
    monkeypatch.setenv("FORGE_FIELD_URL", "http://127.0.0.1:9/")
    pem = KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(b"test"))
    (tmp_path / "key.pem").write_bytes(pem)
    with patch("getpass.getpass", return_value="test"):
        assert cockpit.main(["remember", "The sky is blue", "--face", "FACT"]) == 0
        dc = cockpit._layer("datacube")
        capsule = cockpit._asserted_capsule({"subject": "ledger-layer", "object": "P4 Ledger"}, "FACT",
                                            "The hash-chained, append-only ledger.")
        dc.set_face(capsule, "CONTEXT", "Frozen 2.0.0 (ledger_v2).")
        dc.set_face(capsule, "UNKNOWN", "Should RecursionError become False?")
        key = cockpit._v11._load_key(str(tmp_path / "key.pem"))
        cockpit._v11._commit(capsule, key)
        sky = [r for r in cockpit._layer("substrate").list_claims(str(tmp_path / "forge.db"))
               if r["capsule"]["subject"] == "sky"][0]["claim_id"]
        assert cockpit.main(["propose", sky, "--action", "publish"]) == 0
        assert cockpit.main(["approve", "2", "--key", str(tmp_path / "key.pem"), "--lambda", "1.8"]) == 0
        yield tmp_path


# 6. server
@pytest.fixture
def server(home):
    srv = legacy_v6.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


# 1. test_claims_have_every_face
def test_claims_have_every_face(server):
    status, body = _req(server + "/api/claims")
    assert status == 200 and body["available"] is True
    by_subject = {c["subject"]: c for c in body["claims"]}
    ledger = by_subject["ledger-layer"]
    assert list(ledger["faces"]) == ["FACT", "CONTEXT", "UNKNOWN"]
    assert ledger["faces"]["UNKNOWN"] == "Should RecursionError become False?"
    assert ledger["face"] == "FACT" and ledger["text"] == "The hash-chained, append-only ledger."
    assert by_subject["sky"]["faces"] == {"FACT": "The sky is blue"} and by_subject["sky"]["attested"] is True


# 2. test_chain_kind_filter
def test_chain_kind_filter(server):
    body = _req(server + "/api/chain?kind=claim&limit=5")[1]
    assert [e["kind"] for e in body["entries"]] == ["claim", "claim"]
    assert body["matched"] == 2 and body["total"] == 4
    assert [e["seq"] for e in body["entries"]] == [1, 0]  # reachable although seals are newer
    seals = _req(server + "/api/chain?kind=seal")[1]
    assert [e["kind"] for e in seals["entries"]] == ["seal"] and seals["matched"] == 1
    every = _req(server + "/api/chain")[1]
    assert [e["seq"] for e in every["entries"]] == [3, 2, 1, 0] and every["matched"] == 4
    assert _req(server + "/api/chain?kind=everything")[0] == 400


# 3. test_page
def test_page(server):
    status, html = _req(server + "/")
    assert status == 200
    for text in ("Metrics", "Layers", "Faces filled", "Query", "Ledger", "Claims", "Field", "New claim",
                 "Network", "Briefing", "LLLM", ">Subject<", 'data-kind="claim"', 'data-kind="seal"',
                 "serve_v3.py", "pinned via SC-OS"):
        assert text in html, text
    assert "serve_v2.py" not in html
    assert "X-Forge-Legacy" in html and "&#39;" in html
    assert _req(server + "/static/projection_v5.html")[0] == 200


# 4. test_older_routes_inherited
def test_older_routes_inherited(server):
    assert len(_req(server + "/api/health")[1]["layers"]) == 15
    assert _req(server + "/api/cockpit")[1]["status"]["claims"]["total"] == 2
    body = _req(server + "/api/voice?" + urllib.parse.urlencode({"q": "what is the ledger-layer?"}))[1]
    assert body["reply"].startswith("ledger-layer is P4 Ledger.")
