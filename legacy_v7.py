"""
legacy_v7.py — The Legacy v7, with the LLLM wired through end to end

Function:
    The layer over legacy_v6.py, and the entry point to run from v7 on
    (SPEC_V7.md). The Voice is LLLM v0.1.2 (speaks a claim's signed
    text; a subject's aspects one per line), the Morning Briefing is
    Weaver v1.3 (built from the claims, the engine adds a line when it
    can), and the engine's build and the Cockpit's status come through
    Cockpit v1.3 (finds the engine via LLLM_CLI or PATH). Every other
    route is v6's (and below). legacy.py and legacy_v2–v6 are not edited.

Public API:
    1. voice_turn(text) -> dict
    2. get_briefing() -> dict
    3. lllm_status() -> dict
    4. cockpit_status() -> dict
    5. make_server(host, port)
    6. main(argv) -> int

Internal helpers:
    7. _cockpit, _weaver, _voice — the v7 siblings
    8. _LegacyV7Handler           — v6's handler with the v7 page and routes

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v6.py (1.2.0), forge_cli_v1_3, weaver_v1_3, lllm_v0_1_2
Spec:     SPEC_V7.md 1.3.0 (over SPEC_V6.md 1.0.0)
Version:  1.3.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v3  # noqa: E402
import legacy_v4 as _v4  # noqa: E402
import legacy_v6 as _v6  # noqa: E402

_BRIEFING_CACHE = {"ts": 0.0, "data": None}
_VOICE = {"session": None, "lock": threading.Lock()}


# ---------------------------------------------------------------------------
# 7. _cockpit, _weaver, _voice
# ---------------------------------------------------------------------------
def _cockpit():
    return legacy_v3._sibling("explorer-d334-forge", "forge_cli_v1_3")


def _weaver():
    return legacy_v3._sibling("the-weaver", "weaver_v1_3")


def _voice():
    return legacy_v3._sibling("lllm", "lllm_v0_1_2")


# ---------------------------------------------------------------------------
# 1. voice_turn
#    v4's shape and session rule, through the Voice v0.1.2.
# ---------------------------------------------------------------------------
def voice_turn(text):
    try:
        voice = _voice()
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
# 2. get_briefing
#    SPEC_V7 §2: Weaver v1.3 compose_briefing; v4's one-hour cache.
# ---------------------------------------------------------------------------
def get_briefing():
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
        result["briefing"] = weaver.compose_briefing(claims)
    except Exception as e:
        result["error"] = f"weaver failed: {e}"
    if result["error"] is None:
        _BRIEFING_CACHE.update(ts=now, data=result)
    return result


# ---------------------------------------------------------------------------
# 3. lllm_status
#    v4's shape, through Cockpit v1.3.
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
# 4. cockpit_status
# ---------------------------------------------------------------------------
def cockpit_status():
    try:
        return {"available": True, "status": _cockpit().status(), "error": None}
    except Exception as e:
        return {"available": False, "status": None, "error": str(e)}


# ---------------------------------------------------------------------------
# 8. _LegacyV7Handler
# ---------------------------------------------------------------------------
class _LegacyV7Handler(_v6._LegacyV6Handler):

    # 8.1 do_GET — the v7 page and routes, else v6 (and below).
    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path
        if path in ("/", ""):
            return self._serve_static("projection_v7.html")
        if path == "/api/voice":
            q = parse_qs(parts.query).get("q", [""])[0].strip()
            if not q or len(q) > _v4.MAX_VOICE_INPUT:
                return self._send(400, {"error": f"q must be 1–{_v4.MAX_VOICE_INPUT} characters"})
            return self._send(200, voice_turn(q))
        if path == "/api/weaver":
            return self._send(200, get_briefing())
        if path == "/api/lllm":
            return self._send(200, lllm_status())
        if path == "/api/cockpit":
            return self._send(200, cockpit_status())
        return super().do_GET()


# ---------------------------------------------------------------------------
# 5. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV7Handler)


# ---------------------------------------------------------------------------
# 6. main
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
    print(f"The Legacy (v7) on http://{host}:{port}/")
    print("  Field: run ../scp-substrate/serve_v4.py for the 3D view (port 8085)")
    print("  Drafts saved here are committed with: python ../explorer-d334-forge/forge_cli_v1_3.py inbox commit")
    print("  LLLM engine: set LLLM_HOME, and LLLM_CLI to the engine's lllm/cli.py (or put lllm on PATH)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
