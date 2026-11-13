"""
test_legacy_v5.py — The Legacy v5 (The Projection redesigned) test suite

Function:
    Executable expression of SPEC_V5.md. Written before legacy_v5.py
    and run red first. The Cockpit writes a real substrate and ledger;
    the v5 server is exercised over HTTP.

Functions in this file (pytest-collected):
    1. test_claims_route
    2. test_chain_route
    3. test_page
    4. test_v4_routes_inherited

Fixtures and helpers:
    5. home   — FORGE_HOME with key.pem and two claims written by the Cockpit
    6. server — a running v5 server; yields its base URL
    7. _req   — HTTP GET returning (status, json-or-text)

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V5.md 1.0.0
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

import legacy_v5  # noqa: E402
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
        assert cockpit.main(["remember", "The tide is late", "--face", "UNKNOWN"]) == 0
        yield tmp_path


# 6. server
@pytest.fixture
def server(home):
    srv = legacy_v5.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


# 1. test_claims_route
def test_claims_route(server):
    status, body = _req(server + "/api/claims")
    assert status == 200 and body["available"] is True
    claims = body["claims"]
    assert [c["face"] for c in claims] == ["UNKNOWN", "FACT"]  # newest first
    sky = claims[1]
    assert sky["subject"] == "sky" and sky["polarity"] == "affirm" and sky["text"] == "The sky is blue"
    assert sky["verified"] is True and sky["attested"] is False and sky["short"] == sky["claim_id"][:12]
    assert _req(server + "/api/claims?limit=1")[1]["claims"][0]["face"] == "UNKNOWN"
    assert _req(server + "/api/claims?limit=abc")[0] == 400


# 2. test_chain_route
def test_chain_route(server):
    status, body = _req(server + "/api/chain")
    entries = body["entries"]
    assert status == 200 and body["total"] == 2 and [e["seq"] for e in entries] == [1, 0]
    assert entries[0]["prev"] == entries[1]["hash"] and entries[1]["prev"] == "0" * 64
    assert [e["kind"] for e in entries] == ["claim", "claim"] and "tide" in entries[0]["label"]
    assert _req(server + "/api/chain?limit=1")[1]["entries"][0]["seq"] == 1
    assert _req(server + "/api/chain?limit=x")[0] == 400


# 3. test_page
def test_page(server):
    status, html = _req(server + "/")
    assert status == 200
    for section in ("Metrics", "Layers", "Claims by face", "Query", "Ledger", "Claims", "Field",
                    "New claim", "Network", "Briefing", "LLLM"):
        assert section in html, section
    assert "X-Forge-Legacy" in html and "&#39;" in html
    v4_page = _req(server + "/static/projection.html")
    assert v4_page[0] == 200 and "Claims by face" not in v4_page[1]


# 4. test_v4_routes_inherited
def test_v4_routes_inherited(server):
    assert len(_req(server + "/api/health")[1]["layers"]) == 15
    assert _req(server + "/api/cockpit")[1]["status"]["claims"]["total"] == 2
    body = _req(server + "/api/voice?" + urllib.parse.urlencode({"q": "is the sky blue?"}))[1]
    assert body["reply"].startswith("Yes. sky is blue.")
