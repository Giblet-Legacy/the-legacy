"""
test_legacy_v12_at_v2.py — test_legacy_v12.py carried into The Legacy 2.0.0 (CONSOLIDATION_V2.md §3.2, §8)

Function:
    The tests of the frozen test_legacy_v12.py that describe 1.12.0, run against
    legacy_v2 / boot_v2: the old module names are imported as aliases of
    them, and every kept test is otherwise as frozen. Tests that describe
    behaviour 1.12.0 replaced are left out; a cut inside a kept test says
    what replaced it. The original is byte-identical in
    archive/1.12.0/test_legacy_v12.py. Its own header follows.

test_legacy_v12.py — The Legacy v12 (new entity, new subject, new claim) test suite

Function:
    Executable expression of SPEC_V14.md. Written before legacy_v12.py,
    boot_v7.py and static/projection_v10.html, and run red first.

Functions in this file (pytest-collected):
    1. test_nouns_empty_without_a_database
    2. test_nouns_registered_and_drafted
    3. test_post_drafts_of_each_kind
    4. test_post_refusals
    5. test_inbox_lists_each_kind
    6. test_page
    7. test_boot_v7_order

Helpers:
    8. home    — FORGE_HOME in tmp_path
    9. server  — a running Legacy v12
    10. _get / _post

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V14.md 1.10.0
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot_v2 as boot  # noqa: E402
import legacy_v2 as legacy_v12  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 8. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    return tmp_path


# 9. server
@pytest.fixture
def server(home):
    srv = legacy_v12.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


# 10. _get / _post
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


def _p9():
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "substrate-layer"))
    import substrate_v4
    return substrate_v4


# 1. test_nouns_empty_without_a_database
def test_nouns_empty_without_a_database(server):
    assert json.loads(_get(server, "/api/nouns")) == {"entities": [], "subjects": [], "error": None}


# 2. test_nouns_registered_and_drafted
def test_nouns_registered_and_drafted(server, home):
    p9, db = _p9(), str(home / "forge.db")
    p9.init_db(db)
    ent = p9.add_entity(db, "James Gilbert", KEY, kind="person")
    sub = p9.add_subject(db, "Nova-bot", KEY)
    p9.add_member(db, sub, ent, KEY)
    assert _post(server, {"kind": "entity", "name": "Giblets Forge"})[0] == 201
    assert _post(server, {"kind": "subject", "name": "LLLM", "entity": "Giblets Forge"})[0] == 201
    d = json.loads(_get(server, "/api/nouns"))
    assert d["error"] is None
    ents = {e["name"]: e for e in d["entities"]}
    subs = {s["name"]: s for s in d["subjects"]}
    assert ents["James Gilbert"]["draft"] is False and ents["James Gilbert"]["kind"] == "person"
    assert ents["Giblets Forge"]["draft"] is True
    assert subs["Nova-bot"]["entities"] == ["James Gilbert"] and subs["Nova-bot"]["draft"] is False
    assert subs["LLLM"]["entities"] == ["Giblets Forge"] and subs["LLLM"]["draft"] is True


# 3. test_post_drafts_of_each_kind
def test_post_drafts_of_each_kind(server, home):
    s, b = _post(server, {"kind": "entity", "name": "James Gilbert"})
    assert s == 201 and b["draft_id"]
    s, b = _post(server, {"kind": "subject", "name": "Nova-bot", "entity": "James Gilbert"})
    assert s == 201 and b["draft_id"]
    s, b = _post(server, {"subject": "Nova-bot", "object": "sensor", "face": "FACT", "text": "HC-SR04."})
    assert s == 201 and b["draft_id"] and "echo" in b
    files = sorted((home / "inbox").glob("*.json"))
    kinds = sorted(json.loads(p.read_text(encoding="utf-8")).get("kind", "claim") for p in files)
    assert kinds == ["claim", "entity", "subject"]


# 4. test_post_refusals
def test_post_refusals(server, home):
    assert _post(server, {"kind": "place", "name": "home"})[0] == 400
    assert _post(server, {"kind": "subject", "name": "Nova-bot"})[0] == 400
    assert _post(server, {"kind": "entity", "name": "x"}, host="vmi.example.ts.net")[0] == 403
    assert not (home / "inbox").exists() or not list((home / "inbox").glob("*.json"))


# 5. test_inbox_lists_each_kind
def test_inbox_lists_each_kind(server):
    _post(server, {"kind": "entity", "name": "James Gilbert"})
    _post(server, {"kind": "subject", "name": "Nova-bot", "entity": "James Gilbert"})
    _post(server, {"subject": "sky", "object": "colour", "face": "FACT", "text": "Blue."})
    items = json.loads(_get(server, "/api/inbox"))
    by_kind = {i["kind"]: i for i in items}
    assert by_kind["entity"]["name"] == "James Gilbert"
    assert by_kind["subject"]["entity"] == "James Gilbert"
    assert by_kind["claim"]["subject"] == "sky"


# 6. test_page
def test_page(server):
    page = _get(server, "/")
    for needle in ('id="new-tabs"', 'data-new="entity"', 'data-new="subject"', 'data-new="claim"',
                   'id="pick-entity"', 'id="pick-subject"', "forge_cli_v1_7.py inbox commit", "/api/nouns", "form.grid[hidden]"):
        assert needle in page, needle


