"""
test_legacy_v9.py — The Legacy v9 (the page on a phone, boot_v3) test suite

Function:
    Executable expression of SPEC_V10.md. Written before the v9 page's
    changes and run red first against an unmodified copy of the v8 page.

Functions in this file (pytest-collected):
    1. test_page_served
    2. test_boot_v3_order
    3. test_phone_tables

Helpers:
    4. _browser — Edge or Chrome, else None
    5. Probe    — the v9 handler with sample claims and ledger, and the
                  page shown in a 412 x 915 frame
    6. _free_port

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V10.md 1.6.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import html as _html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot  # noqa: E402
import boot_v3  # noqa: E402
import legacy_v9  # noqa: E402

TEXT = "The Voice answers only from active P9 claims, read-only, and never from OPINION or FICTION."
CLAIMS = {"available": True, "claims": [
    {"subject": "explorer-d334-forge", "face": "FACT", "text": TEXT, "polarity": "affirm",
     "faces": {"CONTEXT": "lllm SPEC.md section 12: P9 forge.db, read-only."},
     "attested": True, "verified": True, "short": "be5b74980c62"} for _ in range(6)]}
CHAIN = {"available": True, "total": 375, "matched": 375, "entries": [
    {"seq": 374 - i, "kind": "claim", "label": "FACT: " + TEXT, "hash": "3528bca0d5ce" * 5,
     "prev": "92ee01d14f6e" * 5} for i in range(6)]}
PROBE = """<script>setTimeout(function () {
  var W = innerWidth, bad = [], narrow = [];
  document.querySelectorAll("body *").forEach(function (e) {
    var r = e.getBoundingClientRect();
    if (!r.width || !r.height || r.right <= W + 1) return;
    for (var p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      var o = getComputedStyle(p).overflowX;
      if ((o === "auto" || o === "scroll") && p.getBoundingClientRect().right <= W + 1) return;
    }
    bad.push((e.id || e.className || e.tagName) + " ends at " + Math.round(r.right));
  });
  var cells = document.querySelectorAll("#claims td.t, #ledger td.t");
  cells.forEach(function (c) { narrow.push(Math.round(c.getBoundingClientRect().width)); });
  parent.postMessage(JSON.stringify({ W: W, bad: bad.slice(0, 20), cells: narrow }), "*");
}, 3000);</script>"""
PHONE = """<!doctype html><title>waiting</title><iframe src="/" style="width:412px;height:915px;border:0"></iframe>
<script>addEventListener("message", function (e) { document.title = e.data; });</script>"""


# 4. _browser
def _browser():
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return shutil.which(name)
    for path in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(path):
            return path
    return None


# 5. Probe
class Probe(legacy_v9._LegacyV9Handler):

    def log_message(self, *args):
        pass

    def _raw(self, body, ctype):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", ""):
            with open(os.path.join(ROOT, "static", "projection_v9.html"), encoding="utf-8") as f:
                return self._raw(f.read().replace("</body>", PROBE + "</body>"), "text/html; charset=utf-8")
        if path == "/phone":
            return self._raw(PHONE, "text/html; charset=utf-8")
        if path == "/api/claims":
            return self._raw(json.dumps(CLAIMS), "application/json")
        if path == "/api/chain":
            return self._raw(json.dumps(CHAIN), "application/json")
        return super().do_GET()


# 6. _free_port
def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# 1. test_page_served
def test_page_served():
    server = legacy_v9.make_server("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}/", timeout=20) as r:
            page = r.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
    with open(os.path.join(ROOT, "static", "projection_v9.html"), encoding="utf-8") as f:
        assert page == f.read()
    for needle in ("python boot_v3.py", "serve_v7.py", "function poll", "limit=500"):
        assert needle in page, needle


# 2. test_boot_v3_order
def test_boot_v3_order(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(s.cmd for s in services)

        def start_all(self):
            raise KeyboardInterrupt  # stop straight away

        def stop(self):
            pass

    monkeypatch.setattr(boot, "Supervisor", Sup)
    monkeypatch.setattr(boot, "FIELD_SCRIPT", boot.FIELD_SCRIPT)
    monkeypatch.setattr(boot, "LEGACY_SCRIPT", boot.LEGACY_SCRIPT)
    assert boot_v3.main(["--port", "1", "--field-port", "2"]) == 0
    field, legacy = seen
    assert field[1].endswith(os.path.join("scp-substrate", "serve_v7.py")) and field[2:] == ["--port", "2", "--quiet"]
    assert legacy[1].endswith("legacy_v9.py")


# 3. test_phone_tables
def test_phone_tables(monkeypatch, tmp_path):
    browser = _browser()
    if not browser:
        pytest.skip("no headless browser (Edge or Chrome) on this device")
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))  # never the real ~/.forge
    monkeypatch.delenv("LLLM_HOME", raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", _free_port()), Probe)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        r = subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                            f"--user-data-dir={tmp_path / 'profile'}", "--window-size=1000,1000",
                            "--virtual-time-budget=6000", "--dump-dom",
                            f"http://127.0.0.1:{server.server_address[1]}/phone"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150)
    finally:
        server.shutdown()
        server.server_close()
    title = re.search(r"<title>(.*?)</title>", r.stdout, re.S)
    shown = json.loads(_html.unescape(title.group(1))) if title and title.group(1) != "waiting" else None
    assert shown and shown["W"] == 412, (shown, r.stderr[-500:])
    assert len(shown["cells"]) == 12 and min(shown["cells"]) >= 150, shown
    assert shown["bad"] == [], shown
