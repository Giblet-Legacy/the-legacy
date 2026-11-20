"""
test_legacy_v11.py — The Legacy v11 (one link: the Field's address for the browser) test suite

Function:
    Executable expression of SPEC_V13.md. Written before legacy_v11.py
    and boot_v6.py and run red first.

Functions in this file (pytest-collected):
    1. test_field_url_unchanged_without_the_variable
    2. test_field_url_public_path
    3. test_field_url_bad_values_ignored
    4. test_boot_v6_order_and_env

Helpers:
    5. _health_server — a stand-in Field that answers /api/health
    6. _field         — GET /api/field from a running Legacy v11

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V13.md 1.9.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot  # noqa: E402
import boot_v6  # noqa: E402
import legacy_v11  # noqa: E402


# 5. _health_server
@pytest.fixture
def field_url():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200 if self.path == "/api/health" else 404)
            self.end_headers()

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()
    srv.server_close()


# 6. _field
def _field():
    server = legacy_v11.make_server("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/field", timeout=30) as r:
            return json.loads(r.read())
    finally:
        server.shutdown()
        server.server_close()


# 1. test_field_url_unchanged_without_the_variable
def test_field_url_unchanged_without_the_variable(monkeypatch, field_url):
    monkeypatch.setenv("FORGE_FIELD_URL", field_url)
    monkeypatch.delenv("FORGE_FIELD_PUBLIC_URL", raising=False)
    assert _field() == {"url": field_url, "reachable": True}


# 2. test_field_url_public_path
def test_field_url_public_path(monkeypatch, field_url):
    monkeypatch.setenv("FORGE_FIELD_URL", field_url)
    monkeypatch.setenv("FORGE_FIELD_PUBLIC_URL", "/field/")
    assert _field() == {"url": "/field/", "reachable": True}
    monkeypatch.setenv("FORGE_FIELD_PUBLIC_URL", "https://example.ts.net/field/")
    assert _field()["url"] == "https://example.ts.net/field/"


# 3. test_field_url_bad_values_ignored
@pytest.mark.parametrize("bad", ["javascript:alert(1)", "ftp://x/", "field", "  ", "//evil.example/"])
def test_field_url_bad_values_ignored(monkeypatch, field_url, bad):
    monkeypatch.setenv("FORGE_FIELD_URL", field_url)
    monkeypatch.setenv("FORGE_FIELD_PUBLIC_URL", bad)
    assert _field()["url"] == field_url


# 4. test_boot_v6_order_and_env
def test_boot_v6_order_and_env(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(services)

        def start_all(self):
            raise KeyboardInterrupt  # stop straight away

        def stop(self):
            pass

    monkeypatch.setattr(boot, "Supervisor", Sup)
    monkeypatch.setattr(boot, "FIELD_SCRIPT", boot.FIELD_SCRIPT)
    monkeypatch.setattr(boot, "LEGACY_SCRIPT", boot.LEGACY_SCRIPT)
    monkeypatch.setenv("FORGE_FIELD_PUBLIC_URL", "/field/")
    assert boot_v6.main(["--port", "1", "--field-port", "2"]) == 0
    field, legacy = seen
    assert field.cmd[1].endswith(os.path.join("scp-substrate", "serve_v8.py"))
    assert field.cmd[2:] == ["--port", "2", "--quiet"]
    assert legacy.cmd[1].endswith("legacy_v11.py") and os.path.exists(legacy.cmd[1])
    assert legacy.env["FORGE_FIELD_PUBLIC_URL"] == "/field/"
    assert legacy.env["FORGE_FIELD_URL"] == "http://127.0.0.1:2/"
