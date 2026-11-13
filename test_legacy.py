"""
test_legacy.py — The Legacy test suite (Phase 1, v0.1.0)

Function:
    Executable expression of SPEC.md §2 and §3. Covers the layer
    probes, the briefing endpoint, the HTTP server's routes, and its
    read-only discipline.

Tier:    Tier 1 — Consumer (The Legacy)
Spec:    SPEC.md v1.0.0 (Phase 1)
Licence: MSL-1.0
"""

import os
import sys
import json
import socket
import tempfile
import threading
import time
import pytest
import urllib.request
import urllib.error
from unittest.mock import patch

# Bootstrap sibling layers for probes
ROOT = os.path.dirname(os.path.abspath(__file__))
for layer in [
    "envelope-layer", "sign-layer", "freeze-layer", "ledger-layer",
    "genesis-layer", "canon-verify-layer", "record-layer", "store-layer",
    "substrate-layer", "weight-layer", "trust-layer",
    "leighton-engine-layer", "rules-layer", "datacube-layer", "hal-layer",
]:
    p = os.path.abspath(os.path.join(ROOT, "..", layer))
    if os.path.isdir(p):
        sys.path.insert(0, p)

import legacy


@pytest.fixture
def forge_home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def test_server():
    """Start a real HTTP server on an ephemeral port, yield base_url, then shut down."""
    # Pick a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = legacy.make_server("127.0.0.1", port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Give the server a moment to bind
    time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


# ── probe_layers ───────────────────────────────────────────────────────
def test_probe_layers_returns_15():
    results = legacy.probe_layers()
    assert len(results) == 15


def test_probe_layers_shape():
    results = legacy.probe_layers()
    for r in results:
        assert "layer" in r
        assert "status" in r
        assert "error" in r
        assert r["status"] in ("PASS", "FAIL")


def test_probe_layers_names_match_expected():
    results = legacy.probe_layers()
    names = [r["layer"] for r in results]
    expected = [
        "P1 Envelope", "P2 Sign", "P3 Freeze", "P4 Ledger", "P5 Genesis",
        "P6 Canon Verify", "P7 Record", "P8 Store", "P9 Substrate",
        "P10 Weight", "P11 Trust", "P12 Rules", "P13 DataCube",
        "P14 Leighton Engine", "P15 HAL",
    ]
    assert names == expected


def test_probe_layers_all_pass_when_layers_present():
    """When all sibling layers exist (which they do in the phone env), all should PASS."""
    results = legacy.probe_layers()
    failures = [r for r in results if r["status"] == "FAIL"]
    assert failures == [], f"unexpected FAILs: {failures}"


# ── get_briefing ───────────────────────────────────────────────────────
def test_get_briefing_returns_shape(forge_home, monkeypatch):
    monkeypatch.delenv("LLLM_HOME", raising=False)
    result = legacy.get_briefing()
    assert "briefing" in result
    assert "claims" in result
    assert "error" in result


def test_get_briefing_no_db_returns_error(forge_home, monkeypatch):
    monkeypatch.setenv("LLLM_HOME", str(forge_home))
    result = legacy.get_briefing()
    assert result["briefing"] is None
    assert result["error"] is not None


def test_get_briefing_no_lllm_returns_error(forge_home, monkeypatch):
    monkeypatch.delenv("LLLM_HOME", raising=False)
    # Use a tmp FORGE_HOME with no db
    result = legacy.get_briefing()
    # Either "no db" or "no LLLM" is a valid error
    assert result["error"] is not None


# ── HTTP server tests ──────────────────────────────────────────────────
def test_index_returns_html(test_server):
    resp = urllib.request.urlopen(test_server + "/")
    body = resp.read().decode("utf-8")
    assert resp.status == 200
    assert "<!doctype html>" in body.lower() or "<html" in body.lower()


def test_health_endpoint_returns_json(test_server):
    resp = urllib.request.urlopen(test_server + "/api/health")
    body = resp.read().decode("utf-8")
    assert resp.status == 200
    data = json.loads(body)
    assert "layers" in data
    assert isinstance(data["layers"], list)
    assert len(data["layers"]) == 15


def test_weaver_endpoint_returns_json(test_server):
    resp = urllib.request.urlopen(test_server + "/api/weaver")
    body = resp.read().decode("utf-8")
    assert resp.status == 200
    data = json.loads(body)
    assert "briefing" in data
    assert "claims" in data
    assert "error" in data


def test_post_returns_405(test_server):
    req = urllib.request.Request(test_server + "/", method="POST", data=b"x")
    try:
        urllib.request.urlopen(req)
        pytest.fail("POST should not be allowed")
    except urllib.error.HTTPError as e:
        assert e.code == 405


def test_path_traversal_blocked(test_server):
    # Attempt to fetch something outside static/ via ../.
    req = urllib.request.Request(test_server + "/../etc/passwd")
    try:
        resp = urllib.request.urlopen(req)
        body = resp.read().decode("utf-8", errors="replace")
        pytest.fail(f"traversal should be blocked, got: {body[:100]}")
    except urllib.error.HTTPError as e:
        # 403 or 404 both acceptable
        assert e.code in (400, 403, 404)


def test_unknown_route_returns_404(test_server):
    try:
        urllib.request.urlopen(test_server + "/nope")
        pytest.fail("unknown route should 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404
