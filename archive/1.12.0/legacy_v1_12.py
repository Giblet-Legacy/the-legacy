"""
legacy_v1_12.py — The Legacy 1.12.0: the AI on the page, through the gate

Function:
    The entry point from 1.12.0 (SPEC_V1_12.md). The Legacy 1.11.0 with
    one addition: /api/ai/* is relayed to the ai-gate local API
    (ai_gate_serve.py, FORGE_AI_GATE_URL, default http://127.0.0.1:8092),
    and the page (static/projection_v1_12.html) gains an "Ask the AI"
    card. The Legacy never calls a model: the gate is the only process
    that talks to Gemini. Reads are relayed from an allowlist only. Asks
    and ratings pass the Legacy v4 write guard first (local host,
    X-Forge-Legacy, JSON), so on the VPS they are refused. There is no
    seal relay: a HAL seal needs James's passphrase, in the terminal.
    legacy.py and v2-v12, legacy_v1_11 are not edited.

    python boot_v1_12.py      (the Field, ai-gate, then The Legacy 1.12.0)
    python legacy_v1_12.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. gate_url() -> str
    2. make_server(host, port) -> ThreadingHTTPServer
    3. main(argv) -> int

Internal helpers:
    4. _relay — one request to the gate; (status, JSON body)

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v1_11.py (1.11.0), ai-gate ai_gate_serve.py (0.1.0)
Spec:     SPEC_V1_12.md 1.12.0
Version:  1.12.0 (frozen 2026-11-20)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy_v10 as _v10  # noqa: E402
import legacy_v1_11 as _v1_11  # noqa: E402

GET_ALLOWED = ("health", "status", "threads", "thread", "assumptions", "assumption", "known", "score")
POST_ALLOWED = ("ask", "rate")
OFFLINE = "ai-gate is not running (start it with boot_v1_12.py, or python ../ai-gate/ai_gate_serve.py)"


# ---------------------------------------------------------------------------
# 1. gate_url
# ---------------------------------------------------------------------------
def gate_url():
    return (os.environ.get("FORGE_AI_GATE_URL") or "http://127.0.0.1:8092").rstrip("/")


# ---------------------------------------------------------------------------
# 4. _relay
# ---------------------------------------------------------------------------
def _relay(method, path_and_query, body=None, timeout=10):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers.update({"Content-Type": "application/json", "X-Forge-Legacy": "1"})
    req = urllib.request.Request(gate_url() + path_and_query, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {"error": f"ai-gate answered {e.code}"}
    except (urllib.error.URLError, OSError, ValueError):
        return None, None


class _LegacyV1_12Handler(_v1_11._LegacyV1_11Handler):

    def _ai_name(self):
        parts = urlsplit(self.path).path.split("/")
        if len(parts) == 4 and parts[1] == "api" and parts[2] == "ai":
            return parts[3]
        return None

    # 2.1 do_GET — the 1.12 page; /api/ai/<allowed> relayed; else 1.11.
    def do_GET(self):
        u = urlsplit(self.path)
        if u.path in ("/", ""):
            return self._serve_static("projection_v1_12.html")
        if u.path.startswith("/api/ai/"):
            name = self._ai_name()
            if name not in GET_ALLOWED:
                return self._send(404, {"error": "not an ai-gate read"})
            status, body = _relay("GET", f"/api/{name}" + (f"?{u.query}" if u.query else ""))
            if status is None:
                return self._send(200, {"error": OFFLINE, "offline": True})
            return self._send(status, body)
        return super().do_GET()

    # 2.2 do_POST — /api/ai/ask and /api/ai/rate, behind the v4 guard; else 1.11 (the inbox).
    def do_POST(self):
        if not urlsplit(self.path).path.startswith("/api/ai/"):
            return super().do_POST()
        name = self._ai_name()
        if name not in POST_ALLOWED:
            return self._send(404, {"error": "not an ai-gate write (seals are made in the terminal)"})
        refused = self._guard()
        if refused:
            return self._send(refused[0], {"error": refused[1]})
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        except (ValueError, TypeError):
            return self._send(400, {"error": "body must be JSON"})
        status, out = _relay("POST", f"/api/{name}", body, timeout=150 if name == "ask" else 15)
        if status is None:
            return self._send(503, {"error": OFFLINE})
        return self._send(status, out)


# ---------------------------------------------------------------------------
# 2. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV1_12Handler)


# ---------------------------------------------------------------------------
# 3. main
#    v10's flags, defaults and exit codes, with 1.12's server (as v12 and 1.11 do).
# ---------------------------------------------------------------------------
def main(argv):
    original = _v10.make_server
    _v10.make_server = make_server
    try:
        return _v10.main(argv)
    finally:
        _v10.make_server = original


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
