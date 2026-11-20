"""
test_legacy_v2.py — The Legacy 2.0.0 test suite (the consolidation of 1.12.0)

Function:
    1.12.0's own suite (archive/1.12.0/test_legacy_v1_12.py), pointed at
    legacy_v2.py, boot_v2.py and static/projection_v2.html
    (CONSOLIDATION_V2.md §3.2). Behaviour is 1.12.0's; only the names
    change. The older suites that still describe 1.12.0 are carried as
    test_*_at_v2.py. Written before legacy_v2 and boot_v2, and run red
    first. ai-gate is a stub HTTP server here: no key, no model, no
    network.

Functions in this file (pytest-collected):
    1. test_get_relayed_from_the_allowlist_only
    2. test_post_ask_and_rate_relayed_with_the_guard
    3. test_seal_and_other_posts_not_relayed
    4. test_gate_down
    5. test_inbox_still_works
    6. test_page_has_the_ai_card
    7. test_boot_v2_starts_field_gate_legacy
    8. test_frozen_at_2_0_0

Helpers:
    9. gate (stub ai-gate), server, _get, _post

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V2.md 2.0.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot_v2  # noqa: E402
import legacy_v2  # noqa: E402


# 9. helpers
@pytest.fixture
def gate(monkeypatch):
    seen = []

    class Stub(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _reply(self, code, obj):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            seen.append(("GET", self.path, None, dict(self.headers)))
            self._reply(200, {"stub": True, "path": self.path})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(("POST", self.path, body, dict(self.headers)))
            self._reply(201, {"id": "abc", "status": "pending", "standing": "assumption"})

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("FORGE_AI_GATE_URL", f"http://127.0.0.1:{srv.server_address[1]}")
    yield seen
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    srv = legacy_v2.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _url(srv, path):
    return f"http://127.0.0.1:{srv.server_address[1]}{path}"


def _get(srv, path):
    try:
        with urllib.request.urlopen(_url(srv, path), timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def _post(srv, path, body, host=None):
    h = {"Content-Type": "application/json", "X-Forge-Legacy": "1"}
    if host:
        h["Host"] = host
    req = urllib.request.Request(_url(srv, path), data=json.dumps(body).encode(), method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except ValueError:
            return e.code, {}


# 1
def test_get_relayed_from_the_allowlist_only(server, gate):
    s, body = _get(server, "/api/ai/threads")
    assert s == 200 and json.loads(body) == {"stub": True, "path": "/api/threads"}
    s, body = _get(server, "/api/ai/thread?topic=noir")
    assert json.loads(body)["path"] == "/api/thread?topic=noir"
    for p in ("status", "assumptions", "assumption", "known", "score", "health"):
        assert json.loads(_get(server, f"/api/ai/{p}")[1])["path"] == f"/api/{p}"
    n = len(gate)
    assert _get(server, "/api/ai/../../etc")[0] == 404 and _get(server, "/api/ai/secrets")[0] == 404
    assert len(gate) == n


# 2
def test_post_ask_and_rate_relayed_with_the_guard(server, gate):
    s, d = _post(server, "/api/ai/ask", {"idea": "dawn?", "topic": "noir", "about": ["Noir"]})
    assert s == 201 and d["standing"] == "assumption"
    method, path, body, headers = gate[-1]
    assert (method, path, body["idea"]) == ("POST", "/api/ask", "dawn?") and headers.get("X-Forge-Legacy") == "1"
    assert _post(server, "/api/ai/rate", {"id": "abc", "rating": 4})[0] == 201 and gate[-1][1] == "/api/rate"
    n = len(gate)
    assert _post(server, "/api/ai/ask", {"idea": "x", "topic": "noir"}, host="vmi.example.ts.net")[0] == 403
    assert len(gate) == n  # refused before it reached the gate


# 3
def test_seal_and_other_posts_not_relayed(server, gate):
    n = len(gate)
    assert _post(server, "/api/ai/seal", {"id": "abc", "decision": "approve"})[0] in (404, 405)
    assert _post(server, "/api/ai/../ask", {"idea": "x"})[0] in (404, 405)
    assert len(gate) == n


# 4
def test_gate_down(server, monkeypatch):
    monkeypatch.setenv("FORGE_AI_GATE_URL", "http://127.0.0.1:1")
    s, body = _get(server, "/api/ai/threads")
    assert s == 200 and json.loads(body)["offline"] is True and "not running" in json.loads(body)["error"]
    s, d = _post(server, "/api/ai/ask", {"idea": "x", "topic": "noir"})
    assert s == 503 and "not running" in d["error"]


# 5
def test_inbox_still_works(server, gate):
    s, d = _post(server, "/api/inbox", {"kind": "entity", "name": "James Gilbert"})
    assert s == 201 and d["draft_id"]


# 6
def test_page_has_the_ai_card(server):
    page = _get(server, "/")[1]
    for needle in ('id="ai-card"', "Ask the AI", "/api/ai/ask", "/api/ai/rate", "/api/ai/threads",
                   "seal_command", "ASSUMPTION", 'id="ai-about"', "Commit: <code>python forge_cli_v1_8.py inbox commit",
                   # one place for knowledge: local Ask, the AI only on demand (SPEC_V1_12 §2.2)
                   'id="ai-local"', 'data-answer="assumption"', 'data-answer="report"', "/api/ai/known", "/api/voice",
                   'id="browse"', 'aria-labelledby="claims-h"', "Download .md"):
        assert needle in page, needle
    ask = page[page.index('id="view-ask"'):page.index('id="view-create"')]
    assert 'aria-labelledby="claims-h"' in ask and 'aria-labelledby="faces-h"' in ask


# 6b
def test_page_is_seven_views_behind_a_sidebar(server):
    """SPEC_V1_12 §2.1 (James: "its very busy now and not very fluid"): one view at a time."""
    import re
    page = _get(server, "/")[1]
    views = re.findall(r'class="view" id="view-([a-z]+)" data-view="\1"', page)
    assert views == ["home", "ask", "create", "ledger", "field", "system"]  # Claims merged into Ask
    for v in views:
        assert f'href="#{v}" data-view="{v}"' in page, v
    assert 'id="needs"' in page and page.index('id="needs"') < page.index('id="metrics"')  # Home leads with it
    for b in ("badge-home", "badge-ask", "badge-create"):
        assert f'id="{b}"' in page
    assert page.count('<section class="card') == 13  # the 1.11 cards, Query folded into Ask, plus Needs you
    for card in ("metrics-h", "layers-h", "faces-h", "claims-h", "ledger-h", "field-h", "new-h",
                 "echo-h", "ai-h", "net-h", "brief-h", "lllm-h", "needs-h"):
        assert f'aria-labelledby="{card}"' in page, card
    assert "if (!shown(name))" in page and 'window.__legacyView !== "field"' in page  # hidden views wait
    assert page.index("legacy.view") < page.index("function poll(")  # the view is known before panels poll


# 7
def test_boot_v2_starts_field_gate_legacy(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(services)

        def start_all(self):
            raise KeyboardInterrupt

        def stop(self):
            pass

    monkeypatch.setattr(boot_v2, "Supervisor", Sup)
    assert boot_v2.main(["--port", "1", "--field-port", "2", "--ai-port", "3"]) == 0
    names = [s.name for s in seen]
    assert names == ["field", "ai-gate", "legacy"]
    field, gate_, legacy = seen
    assert field.cmd[1].endswith(os.path.join("scp-substrate", "serve_v8.py"))
    assert gate_.cmd[1].endswith(os.path.join("ai-gate", "ai_gate_serve.py")) and "3" in gate_.cmd
    assert legacy.cmd[1].endswith("legacy_v2.py") and legacy.env["FORGE_AI_GATE_URL"] == "http://127.0.0.1:3"


# 8
def test_frozen_at_2_0_0():
    for name in ("legacy_v2.py", "boot_v2.py"):
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            assert "Version:  2.0.0 (frozen 2026-11-20)" in f.read(), name
