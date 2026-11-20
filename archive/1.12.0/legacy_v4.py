"""
legacy_v4.py — The Legacy v4, The Projection

Function:
    The layer over legacy_v3.py, and the entry point to run from v4 on.
    One page through which the operator sees and feeds every consumer:
    health, the Weaver's briefing, the 3D Field (SCP Substrate), the
    Cockpit's status, a Remember form with a live Echo preview, the
    Nerves (SC-OS), LLLM's build, and the Voice: questions answered
    from your claims by LLLM, with a trace (SPEC_V4.md). Its only write is a
    draft in the Cockpit's inbox; it never signs and never sees a
    passphrase. legacy.py, legacy_v2.py and legacy_v3.py are not edited.

Public API:
    1. cockpit_status() -> dict
    2. lllm_status() -> dict
    3. field_status() -> dict
    4. echo_preview(fields) -> dict
    5. pending_drafts() -> list
    12. get_briefing() -> dict   (Weaver v1.2)
    14. voice_turn(text) -> dict (LLLM, the Voice)
    6. make_server(host, port)
    7. main(argv) -> int

Internal helpers (numbered below):
    8.  _cockpit   — Cockpit v1.2 module
    9.  _echo      — Echo v1.1 module
    10. _claim_fields — validate echo query fields
    11. _LegacyV4Handler — routes, guards, the one write
    13. _weaver   — Weaver v1.2 module (imports from any working directory)

Tier:     Tier 1 — Consumer (The Connector)
Depends:  forge_cli_v1_2, echo_v1_1, weaver_v1_2, lllm (the Voice), SCP Substrate serve_v2 (HTTP), legacy_v3
Spec:     SPEC_V4.md 1.1.0 (over SPEC_V3.md, SPEC_V2.md, SPEC.md)
Version:  1.0.0 (The Projection; on James's sign-off)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v3  # noqa: E402

DEFAULT_FIELD_URL = "http://127.0.0.1:8085/"
MAX_BODY = 8192
_FACES = ("FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN")
_BRIEFING_CACHE = {"ts": 0.0, "data": None}
_VOICE = {"session": None, "lock": threading.Lock()}
MAX_VOICE_INPUT = 2000


# ---------------------------------------------------------------------------
# 14. voice_turn
#     SPEC_V4 §2a: one LLLM Voice session per server (single operator), so
#     "how did you work that out?" refers to the previous turn. The Voice
#     reads forge.db only, read-only; LLLM's own opinions (lllm.db) are
#     not spoken as fact.
# ---------------------------------------------------------------------------
def voice_turn(text):
    try:
        voice = legacy_v3._sibling("lllm", "lllm")
    except Exception as e:
        return {"available": False, "reply": None, "trace": None, "trace_text": None,
                "error": f"the Voice is not installed: {e}"}
    with _VOICE["lock"]:
        db = legacy._db_path()
        if _VOICE["session"] is None or _VOICE["session"].db_path != db:
            _VOICE["session"] = voice.Session(db)
        reply, trace = _VOICE["session"].turn(text)
    return {"available": True, "reply": reply, "trace": trace,
            "trace_text": voice.format_trace(trace), "error": None}


# ---------------------------------------------------------------------------
# 8. _cockpit
# ---------------------------------------------------------------------------
def _cockpit():
    return legacy_v3._sibling("explorer-d334-forge", "forge_cli_v1_2")


# ---------------------------------------------------------------------------
# 9. _echo
# ---------------------------------------------------------------------------
def _echo():
    return legacy_v3._sibling("the-echo", "echo_v1_1")


# ---------------------------------------------------------------------------
# 1. cockpit_status
# ---------------------------------------------------------------------------
def cockpit_status():
    try:
        return {"available": True, "status": _cockpit().status(), "error": None}
    except Exception as e:
        return {"available": False, "status": None, "error": str(e)}


# ---------------------------------------------------------------------------
# 2. lllm_status
#    The build LLLM reports now, and whether the ledger has anchored it.
# ---------------------------------------------------------------------------
def lllm_status():
    out = {"available": False, "build_id": None, "identity": None, "warnings": [],
           "anchored": False, "error": None}
    try:
        cockpit = _cockpit()
        prov = cockpit.lllm_provenance()
    except Exception as e:
        out["error"] = str(e)
        return out
    anchored = any((e.get("record") or {}).get("type") == "lllm.build"
                   and e["record"].get("build_json_sha256") == prov["build_json_sha256"]
                   for e in cockpit._v11._ledger_entries())
    out.update(available=True, build_id=prov["build_id"], identity=prov["identity"],
               warnings=prov["warnings"], anchored=anchored)
    return out


# ---------------------------------------------------------------------------
# 3. field_status
#    SCP Substrate is its own server; probe its health, 1 s timeout.
# ---------------------------------------------------------------------------
def field_status():
    url = os.environ.get("FORGE_FIELD_URL") or DEFAULT_FIELD_URL
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/health", timeout=1) as r:
            reachable = r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        reachable = False
    return {"url": url, "reachable": reachable}


# ---------------------------------------------------------------------------
# 10. _claim_fields
# ---------------------------------------------------------------------------
def _claim_fields(raw):
    fields = {k: (raw.get(k) or "").strip() for k in ("subject", "object", "face", "text")}
    fields["face"] = fields["face"].upper()
    if not fields["subject"] or not fields["object"]:
        raise ValueError("subject and object are required")
    if len(fields["subject"]) > 200 or len(fields["object"]) > 200 or len(fields["text"]) > 2000:
        raise ValueError("field too long")
    if fields["face"] not in _FACES:
        raise ValueError(f"face must be one of {_FACES}")
    return fields


# ---------------------------------------------------------------------------
# 4. echo_preview
#    Echo v1.1 on the operator's substrate. Read-only.
# ---------------------------------------------------------------------------
def echo_preview(fields):
    db = legacy._db_path()
    if not os.path.exists(db):
        return {"error": "no substrate yet: remember something first"}
    try:
        out = _echo().echo(db, dict(fields))
    except Exception as e:
        return {"error": f"echo failed: {e}"}
    return {k: out[k] for k in ("gate", "rules_fired", "shape", "memory")}


# ---------------------------------------------------------------------------
# 5. pending_drafts
# ---------------------------------------------------------------------------
def pending_drafts():
    cockpit = _cockpit()
    shown = []
    for draft_id, path in cockpit._pending_drafts():
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            cockpit.validate_draft(d)
            shown.append({"id": draft_id, **{k: d[k] for k in ("subject", "object", "face", "text")}})
        except (OSError, ValueError) as e:
            shown.append({"id": draft_id, "invalid": str(e)})
    return shown


# ---------------------------------------------------------------------------
# 13. _weaver
#     Weaver v1.2: v1.1 failed to import outside a sibling repo (the-weaver
#     SPEC_V1_2.md), which broke v3's Morning Briefing when the Legacy
#     was started from the parent directory.
# ---------------------------------------------------------------------------
def _weaver():
    return legacy_v3._sibling("the-weaver", "weaver_v1_2")


# ---------------------------------------------------------------------------
# 12. get_briefing
#     SPEC_V3 §3's shape and one-hour cache, through Weaver v1.2.
# ---------------------------------------------------------------------------
def get_briefing():
    import time
    now = time.time()
    if _BRIEFING_CACHE["data"] is not None and now - _BRIEFING_CACHE["ts"] < legacy_v3._BRIEFING_TTL:
        return _BRIEFING_CACHE["data"]
    result = {"briefing": None, "claims": [], "error": None}
    try:
        weaver = _weaver()
        db_path = legacy._db_path()
        if not os.path.exists(db_path):
            result["error"] = f"database missing: {db_path}"
            return result
        claims = weaver.find_decayed_unknowns(db_path)
        if not claims:
            result["error"] = "no UNKNOWN claims to weave"
            return result
        result["claims"] = claims
        result["briefing"] = weaver.call_lllm(weaver.build_prompt(claims))
    except RuntimeError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"weaver failed: {e}"
    if result["error"] is None:
        _BRIEFING_CACHE.update(ts=now, data=result)
    return result


# ---------------------------------------------------------------------------
# 11. _LegacyV4Handler
# ---------------------------------------------------------------------------
class _LegacyV4Handler(legacy_v3._LegacyV3Handler):

    # 11.1 _send — JSON with a status code (v1's _serve_json is always 200).
    def _send(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # 11.2 do_GET — SPEC_V4 §2, else v3 / v2 / v1.
    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path
        if path in ("/", ""):
            return self._serve_static("projection.html")
        if path == "/api/weaver":
            return self._send(200, get_briefing())
        if path == "/api/voice":
            q = parse_qs(parts.query).get("q", [""])[0].strip()
            if not q or len(q) > MAX_VOICE_INPUT:
                return self._send(400, {"error": f"q must be 1–{MAX_VOICE_INPUT} characters"})
            return self._send(200, voice_turn(q))
        if path == "/api/cockpit":
            return self._send(200, cockpit_status())
        if path == "/api/lllm":
            return self._send(200, lllm_status())
        if path == "/api/field":
            return self._send(200, field_status())
        if path == "/api/inbox":
            try:
                return self._send(200, pending_drafts())
            except Exception as e:
                return self._send(200, {"error": str(e)})
        if path == "/api/echo":
            q = {k: v[0] for k, v in parse_qs(parts.query).items()}
            try:
                fields = _claim_fields(q)
            except ValueError as e:
                return self._send(400, {"error": str(e)})
            return self._send(200, echo_preview(fields))
        return super().do_GET()

    # 11.3 _guard — SPEC_V4 §4. Returns (status, reason) or None.
    def _guard(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in hosts:
            return 403, "host not allowed"
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            return 403, "cross-origin request refused"
        if self.headers.get("X-Forge-Legacy") != "1":
            return 403, "missing X-Forge-Legacy header"
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            return 415, "Content-Type must be application/json"
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return 400, "Content-Length required"
        if length > MAX_BODY:
            return 413, f"body over {MAX_BODY} bytes"
        return None

    # 11.4 do_POST — SPEC_V4 §3: the one write, a draft in the inbox.
    def do_POST(self):
        if urlsplit(self.path).path != "/api/inbox":
            return self.send_error(405, "Method not allowed")
        refused = self._guard()
        if refused:
            return self._send(refused[0], {"error": refused[1]})
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            draft_id = _cockpit().write_draft(body)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": f"draft not saved: {e}"})
        preview = echo_preview({k: body[k] for k in ("subject", "object", "face", "text")})
        return self._send(201, {"draft_id": draft_id, "echo": preview})

    # 11.5 do_OPTIONS — no preflight is ever answered (SPEC_V4 §4.3).
    def do_OPTIONS(self):
        self.send_error(405, "Method not allowed")


# ---------------------------------------------------------------------------
# 6. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV4Handler)


# ---------------------------------------------------------------------------
# 7. main
#    Same flags, defaults and exit codes as SPEC.md §2.3.
# ---------------------------------------------------------------------------
def main(argv):
    host, port, i = "127.0.0.1", 8080, 0
    while i < len(argv):
        if argv[i] == "--host" and i + 1 < len(argv):
            host, i = argv[i + 1], i + 2
        elif argv[i] == "--port" and i + 1 < len(argv):
            try:
                port = int(argv[i + 1])
            except ValueError:
                print(f"invalid port: {argv[i + 1]}", file=sys.stderr)
                return 2
            i += 2
        else:
            print(f"unknown argument: {argv[i]}", file=sys.stderr)
            return 2
    server = make_server(host, port)
    print(f"The Legacy (v4, The Projection) on http://{host}:{port}/")
    print("  Field: run ../scp-substrate/serve_v2.py for the 3D view (port 8085)")
    print("  Drafts saved here are committed with: python ../explorer-d334-forge/forge_cli_v1_2.py inbox commit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
