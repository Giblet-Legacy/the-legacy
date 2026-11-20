"""
test_legacy_v2_at_v2.py — test_legacy_v2.py carried into The Legacy 2.0.0 (CONSOLIDATION_V2.md §3.2, §8)

Function:
    The tests of the frozen test_legacy_v2.py that describe 1.12.0, run against
    legacy_v2 / boot_v2: the old module names are imported as aliases of
    them, and every kept test is otherwise as frozen. Tests that describe
    behaviour 1.12.0 replaced are left out; a cut inside a kept test says
    what replaced it. The original is byte-identical in
    archive/1.12.0/test_legacy_v2.py. Its own header follows.

test_legacy_v2.py — The Legacy v2 test suite

Function:
    Executable expression of SPEC_V2.md. Proves v2 matches v1 when all
    layers are healthy, captures a missing `cryptography` as FAIL rows
    where v1 raises, and serves /api/health through the v2 handler.

Tier:    Tier 1 — Consumer (The Legacy)
Spec:    SPEC_V2.md v1.0.0
Licence: MSL-1.0
"""

import sys
import json
import socket
import threading
import time
import urllib.request
import urllib.error

import pytest

import legacy_v2 as legacy
import legacy_v2


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """_isolate — reset the briefing cache and drop SSLKEYLOGFILE per test."""
    monkeypatch.setitem(legacy._BRIEFING_CACHE, "data", None)
    monkeypatch.setitem(legacy._BRIEFING_CACHE, "ts", 0.0)
    monkeypatch.delenv("SSLKEYLOGFILE", raising=False)


@pytest.fixture
def no_cryptography(monkeypatch):
    """no_cryptography — make every `cryptography` import fail for one test."""
    names = [m for m in sys.modules
             if m == "cryptography" or m.startswith("cryptography.")]
    names.append("cryptography")
    for m in set(names):
        monkeypatch.setitem(sys.modules, m, None)


@pytest.fixture
def v2_server(tmp_path, monkeypatch):
    """v2_server — run legacy_v2 on an ephemeral port; yield its base URL."""
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = legacy_v2.make_server("127.0.0.1", port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


# ── probe_layers parity ────────────────────────────────────────────────

# ── the defect (SPEC_V2 §2) ────────────────────────────────────────────


# ── re-exports ─────────────────────────────────────────────────────────

# ── HTTP server ────────────────────────────────────────────────────────
def test_v2_health_survives_missing_cryptography(v2_server, no_cryptography):
    resp = urllib.request.urlopen(v2_server + "/api/health")
    data = json.loads(resp.read().decode("utf-8"))
    assert resp.status == 200
    assert len(data["layers"]) == 15


def test_v2_index_and_weaver_inherited(v2_server):
    resp = urllib.request.urlopen(v2_server + "/")
    assert resp.status == 200
    assert "<html" in resp.read().decode("utf-8").lower()
    data = json.loads(urllib.request.urlopen(v2_server + "/api/weaver").read())
    assert {"briefing", "claims", "error"} <= set(data)


def test_v2_post_returns_405(v2_server):
    req = urllib.request.Request(v2_server + "/api/health", method="POST", data=b"x")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 405


def test_v2_head_health(v2_server):
    req = urllib.request.Request(v2_server + "/api/health", method="HEAD")
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    assert resp.read() == b""


# ── main ───────────────────────────────────────────────────────────────
def test_v2_main_rejects_bad_args():
    assert legacy_v2.main(["--bogus"]) == 2
    assert legacy_v2.main(["--port", "abc"]) == 2
