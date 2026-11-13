"""
test_legacy_v4.py — The Legacy v4 (The Projection) test suite

Function:
    Executable expression of SPEC_V4.md. Written before legacy_v4.py
    and run red first. The Cockpit writes a real substrate and ledger;
    the Legacy is exercised over HTTP.

Functions in this file (pytest-collected):
    1. test_read_routes
    2. test_lllm_and_field_states
    3. test_echo_route
    4. test_inbox_write_and_commit
    5. test_inbox_guards
    6. test_page
    10. test_briefing_from_any_directory
    11. test_voice

Fixtures and helpers:
    7.  home    — FORGE_HOME with key.pem and two claims written by the Cockpit
    8.  legacy  — a running v4 server; yields its base URL and port
    9.  _req    — HTTP request returning (status, json-or-text)

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V4.md 1.0.0
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

import subprocess
import textwrap

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "..", "explorer-d334-forge"), os.path.join(ROOT, "..", "scp-substrate")):
    if os.path.abspath(_p) not in sys.path:
        sys.path.insert(0, os.path.abspath(_p))

import legacy_v4  # noqa: E402
import forge_cli_v1_2 as cockpit  # noqa: E402

KEY = Ed25519PrivateKey.generate()


# 9. _req
def _req(url, method="GET", body=None, headers=None):
    req = urllib.request.Request(url, method=method, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status, raw, ctype = r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        status, raw, ctype = e.code, e.read(), e.headers.get("Content-Type", "")
    return status, (json.loads(raw) if "json" in ctype and raw else raw.decode("utf-8", "replace"))


# 7. home
@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    monkeypatch.delenv("LLLM_HOME", raising=False)
    monkeypatch.delenv("SSLKEYLOGFILE", raising=False)
    monkeypatch.setenv("FORGE_FIELD_URL", "http://127.0.0.1:9/")  # nothing listens on port 9
    pem = KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(b"test"))
    (tmp_path / "key.pem").write_bytes(pem)
    with patch("getpass.getpass", return_value="test"):
        assert cockpit.main(["remember", "The sky is blue", "--face", "FACT"]) == 0
        assert cockpit.main(["remember", "The tide is late", "--face", "UNKNOWN"]) == 0
        yield tmp_path


# 8. legacy
@pytest.fixture
def legacy(home):
    srv = legacy_v4.make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    yield f"http://127.0.0.1:{port}", port
    srv.shutdown()
    srv.server_close()


# 1. test_read_routes
def test_read_routes(legacy):
    base, _ = legacy
    status, body = _req(base + "/api/cockpit")
    assert status == 200 and body["available"] is True
    s = body["status"]
    assert s["claims"]["total"] == 2 and s["ledger"]["self_consistent"] is True and s["ledger"]["p8_mirror"] is True
    status, body = _req(base + "/api/health")
    assert status == 200 and len(body["layers"]) == 15
    assert _req(base + "/api/nerves")[1]["available"] is False
    assert _req(base + "/api/inbox") == (200, [])


# 2. test_lllm_and_field_states
def test_lllm_and_field_states(legacy, home, monkeypatch):
    base, _ = legacy
    body = _req(base + "/api/lllm")[1]
    assert body["available"] is False and body["error"]
    lllm_home = home / "lllm"
    (lllm_home / "models" / "abc123").mkdir(parents=True)
    (lllm_home / "models" / "abc123" / "build.json").write_text(json.dumps({"identity": {"capsule_id": "lllm@0.1.0"}}))
    monkeypatch.setenv("LLLM_HOME", str(lllm_home))
    with patch.object(cockpit, "_run_lllm", return_value="build:   abc123\n"):
        body = _req(base + "/api/lllm")[1]
    assert body["available"] is True and body["build_id"] == "abc123" and body["anchored"] is False
    assert _req(base + "/api/field")[1] == {"url": "http://127.0.0.1:9/", "reachable": False}
    import serve_v2
    field = serve_v2.make_server(str(home / "forge.db"), port=0, quiet=True)
    threading.Thread(target=field.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{field.server_address[1]}/"
        monkeypatch.setenv("FORGE_FIELD_URL", url)
        assert _req(base + "/api/field")[1] == {"url": url, "reachable": True}
    finally:
        field.shutdown()
        field.server_close()


# 3. test_echo_route
def test_echo_route(legacy):
    base, _ = legacy
    q = urllib.parse.urlencode({"subject": "sky", "object": "green", "face": "UNKNOWN"})
    status, body = _req(base + "/api/echo?" + q)
    assert status == 200 and body["gate"]["passed"] is False
    q = urllib.parse.urlencode({"subject": "tide", "object": "moon", "face": "FACT"})
    body = _req(base + "/api/echo?" + q)[1]
    assert body["gate"]["passed"] is True and len(body["shape"]["resolves"]) == 1
    assert _req(base + "/api/echo?subject=sky")[0] == 400
    assert _req(base + "/api/echo?" + urllib.parse.urlencode({"subject": "a", "object": "b", "face": "NOPE"}))[0] == 400


# 4. test_inbox_write_and_commit
def test_inbox_write_and_commit(legacy, home):
    base, port = legacy
    good = {"Content-Type": "application/json", "X-Forge-Legacy": "1",
            "Origin": f"http://127.0.0.1:{port}"}
    body = json.dumps({"subject": "sea", "object": "deep", "text": "The sea is deep", "face": "CONTEXT"}).encode()
    status, out = _req(base + "/api/inbox", "POST", body, good)
    assert status == 201 and out["echo"]["gate"]["passed"] is True
    pending = _req(base + "/api/inbox")[1]
    assert [d["id"] for d in pending] == [out["draft_id"]] and pending[0]["face"] == "CONTEXT"
    ledger_before = (home / "ledger.jsonl").read_bytes()
    with patch("getpass.getpass", return_value="test"):
        assert cockpit.main(["inbox", "commit"]) == 0
    assert len((home / "ledger.jsonl").read_bytes()) > len(ledger_before)
    assert _req(base + "/api/inbox")[1] == []
    assert _req(base + "/api/cockpit")[1]["status"]["claims"]["total"] == 3


# 5. test_inbox_guards
def test_inbox_guards(legacy, home):
    base, port = legacy
    body = json.dumps({"subject": "sea", "object": "deep", "text": "t", "face": "FACT"}).encode()
    ok = {"Content-Type": "application/json", "X-Forge-Legacy": "1"}
    cases = [
        (dict(ok, **{"X-Forge-Legacy": ""}), body, 403),
        ({"Content-Type": "application/json"}, body, 403),
        (dict(ok, Host="evil.example:80"), body, 403),
        (dict(ok, Origin="http://evil.example"), body, 403),
        (dict(ok, **{"Content-Type": "text/plain"}), body, 415),
        (ok, json.dumps({"subject": "a", "object": "b", "text": "x" * 9000, "face": "FACT"}).encode(), 413),
        (ok, json.dumps({"subject": "a", "object": "b", "text": "t", "face": "NOPE"}).encode(), 400),
        (ok, b"{not json", 400),
    ]
    for headers, data, expected in cases:
        assert _req(base + "/api/inbox", "POST", data, headers)[0] == expected, (headers, expected)
    assert _req(base + "/api/inbox", "OPTIONS")[0] == 405
    assert _req(base + "/api/inbox", "PUT", body, ok)[0] == 405
    assert _req(base + "/api/inbox")[1] == []
    assert not any(n.endswith(".json") for n in os.listdir(home / "inbox")) if (home / "inbox").exists() else True


# 6. test_page
def test_page(legacy):
    base, _ = legacy
    status, html = _req(base + "/")
    assert status == 200
    for section in ("Health", "Morning Briefing", "The Field", "The Cockpit", "Remember", "The Nerves", "LLLM",
                    "The Voice"):
        assert section in html, section
    assert "X-Forge-Legacy" in html and "&#39;" in html
    assert _req(base + "/static/index.html")[0] == 200


# 10. test_briefing_from_any_directory
def test_briefing_from_any_directory(home, tmp_path):
    work = tmp_path / "elsewhere"
    work.mkdir()
    code = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {ROOT!r})
        os.environ["FORGE_HOME"] = {str(home)!r}
        import legacy_v4
        w = legacy_v4._weaver()
        w.call_lllm = lambda prompt: "Morning."
        import weaver_v1_1; weaver_v1_1.call_lllm = w.call_lllm
        out = legacy_v4.get_briefing()
        print(out["error"], out["briefing"], len(out["claims"]))
    """)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-c", code], cwd=str(work), capture_output=True, text=True, env=env, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "None Morning. 1"


# 11. test_voice
def test_voice(legacy, home):
    base, _ = legacy
    q = urllib.parse.urlencode({"q": "is the sky blue?"})
    status, body = _req(base + "/api/voice?" + q)
    assert status == 200 and body["available"] is True
    assert body["reply"].startswith("Yes. sky is blue. [") and body["trace"]["plan"] == "answer"
    assert "--- trace ---" in body["trace_text"]
    body = _req(base + "/api/voice?" + urllib.parse.urlencode({"q": "how did you work that out?"}))[1]
    assert body["trace"]["plan"] == "trace" and "plan answer" in body["reply"]
    body = _req(base + "/api/voice?" + urllib.parse.urlencode({"q": "is the tide late?"}))[1]
    assert body["trace"]["plan"] == "unknown"  # an UNKNOWN claim has no polarity: never spoken as fact
    assert _req(base + "/api/voice")[0] == 400
    assert _req(base + "/api/voice?" + urllib.parse.urlencode({"q": "x" * 2001}))[0] == 400
