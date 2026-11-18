"""
test_legacy_v1_11.py — The Legacy 1.11.0 (drafts through Cockpit v1.8) test suite

Function:
    Executable expression of SPEC_V1_11.md. Written before legacy_v1_11.py,
    boot_v1_11.py and static/projection_v1_11.html, and run red first.

Functions in this file (pytest-collected):
    1. test_inbox_in_the_order_posted
    2. test_nouns_drafts_in_the_order_written
    3. test_posts_and_refusals_as_v12
    4. test_page
    5. test_boot_v1_11_order

Helpers:
    6. home    — FORGE_HOME in tmp_path
    7. server  — a running Legacy 1.11.0
    8. _get / _post

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V1_11.md 1.11.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot  # noqa: E402
import boot_v1_11  # noqa: E402
import legacy_v1_11  # noqa: E402

NOW = 1795036260.646


# 6. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    return tmp_path


# 7. server
@pytest.fixture
def server(home):
    srv = legacy_v1_11.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


# 8. _get / _post
def _url(srv, path):
    return f"http://127.0.0.1:{srv.server_address[1]}{path}"


def _get(srv, path):
    with urllib.request.urlopen(_url(srv, path), timeout=60) as r:
        return r.read().decode("utf-8")


def _post(srv, body, host=None):
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "X-Forge-Legacy": "1"}
    if host:
        headers["Host"] = host
    req = urllib.request.Request(_url(srv, "/api/inbox"), data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


# 1. test_inbox_in_the_order_posted
def test_inbox_in_the_order_posted(server, home):
    ids = []
    with patch("time.time", return_value=NOW):
        for i in range(6):
            s, b = _post(server, {"subject": "order", "object": f"o{i}", "face": "FACT", "text": f"Claim {i}."})
            assert s == 201
            ids.append(b["draft_id"])
    items = json.loads(_get(server, "/api/inbox"))
    assert [i["id"] for i in items] == ids
    assert [i["object"] for i in items] == [f"o{i}" for i in range(6)]
    stamps = [json.loads((home / "inbox" / f"{i}.json").read_text(encoding="utf-8"))["created_at"] for i in ids]
    assert all(a < b for a, b in zip(stamps, stamps[1:]))


# 2. test_nouns_drafts_in_the_order_written
def test_nouns_drafts_in_the_order_written(server):
    names = ["Zed", "Alpha", "Mid", "Beta"]
    with patch("time.time", return_value=NOW):
        for n in names:
            assert _post(server, {"kind": "entity", "name": n})[0] == 201
        assert _post(server, {"kind": "subject", "name": "S2", "entity": "Zed"})[0] == 201
        assert _post(server, {"kind": "subject", "name": "S1", "entity": "Alpha"})[0] == 201
    d = json.loads(_get(server, "/api/nouns"))
    assert d["error"] is None
    assert [e["name"] for e in d["entities"] if e["draft"]] == names
    assert [s["name"] for s in d["subjects"] if s["draft"]] == ["S2", "S1"]


# 3. test_posts_and_refusals_as_v12
def test_posts_and_refusals_as_v12(server, home):
    assert _post(server, {"kind": "entity", "name": "James Gilbert"})[0] == 201
    assert _post(server, {"kind": "subject", "name": "Nova-bot", "entity": "James Gilbert"})[0] == 201
    s, b = _post(server, {"subject": "Nova-bot", "object": "sensor", "face": "FACT", "text": "HC-SR04."})
    assert s == 201 and "echo" in b
    assert _post(server, {"kind": "place", "name": "home"})[0] == 400
    assert _post(server, {"kind": "entity", "name": "x"}, host="vmi.example.ts.net")[0] == 403
    assert len(list((home / "inbox").glob("*.json"))) == 3


# 4. test_page
def test_page(server):
    page = _get(server, "/")
    assert "Commit: <code>python forge_cli_v1_8.py inbox commit</code>" in page
    assert "Commit: <code>python forge_cli_v1_7.py" not in page  # v1.7 is named only in the header's history
    for needle in ('id="new-tabs"', 'data-new="entity"', 'id="pick-subject"', "/api/nouns"):
        assert needle in page, needle


# 5. test_boot_v1_11_order
def test_boot_v1_11_order(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(services)

        def start_all(self):
            raise KeyboardInterrupt

        def stop(self):
            pass

    monkeypatch.setattr(boot, "Supervisor", Sup)
    monkeypatch.setattr(boot, "FIELD_SCRIPT", boot.FIELD_SCRIPT)
    monkeypatch.setattr(boot, "LEGACY_SCRIPT", boot.LEGACY_SCRIPT)
    assert boot_v1_11.main(["--port", "1", "--field-port", "2"]) == 0
    field, legacy = seen
    assert field.cmd[1].endswith(os.path.join("scp-substrate", "serve_v8.py"))
    assert legacy.cmd[1].endswith("legacy_v1_11.py") and os.path.exists(legacy.cmd[1])
