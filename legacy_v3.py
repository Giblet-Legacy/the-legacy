"""
legacy_v3.py — The Legacy v3, the dashboard on the current layers

Function:
    The layer over legacy_v2.py (itself over the frozen legacy.py), and
    the entry point to run from v3 on. /api/health shows the Cockpit's
    own round trips through the current layers, /api/weaver uses Weaver
    v1.1 (which can read a real substrate), and the new /api/nerves
    gives a verified, read-only view of SC-OS's pins (SPEC_V3.md).
    Every other route, method rule and flag is v1's / v2's.

    legacy.py and legacy_v2.py are not edited.

Public API:
    1. probe_layers() -> list[dict]
    2. get_briefing() -> dict
    3. get_nerves() -> dict
    4. make_server(host, port)
    5. main(argv) -> int

Internal helpers (not exported):
    6. _sibling — import a module from a sibling repository
    7. _weaver  — the Weaver v1.1 module
    8. _LegacyV3Handler — v2 handler with the three v3 routes

Tier:     Tier 1 — Consumer (The Connector)
Depends:  forge_cli_v1_1 (Cockpit), weaver_v1_1 (Weaver), nerves (SC-OS)
Spec:     SPEC_V3.md 1.0.0 (over SPEC_V2.md, SPEC.md)
Version:  0.1.3 (frozen 2026-11-13)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import importlib
import os
import sys
import time
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v2  # noqa: E402

_LABELS = ["P1 Envelope", "P2 Sign", "P3 Freeze", "P4 Ledger", "P5 Genesis",
           "P6 Canon Verify", "P7 Record", "P8 Store", "P9 Substrate", "P10 Weight",
           "P11 Trust", "P12 Rules", "P13 DataCube", "P14 Leighton Engine", "P15 HAL"]
_BRIEFING_CACHE = {"ts": 0.0, "data": None}
_BRIEFING_TTL = legacy._BRIEFING_TTL


# ---------------------------------------------------------------------------
# 6. _sibling
# ---------------------------------------------------------------------------
def _sibling(repo, module):
    path = os.path.abspath(os.path.join(_HERE, "..", repo))
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(module)


# ---------------------------------------------------------------------------
# 7. _weaver
# ---------------------------------------------------------------------------
def _weaver():
    return _sibling("the-weaver", "weaver_v1_1")


# ---------------------------------------------------------------------------
# 1. probe_layers
#    SPEC_V3 §2. Never raises.
# ---------------------------------------------------------------------------
def probe_layers():
    try:
        return _sibling("explorer-d334-forge", "forge_cli_v1_1").probe_layers()
    except Exception as e:
        reason = f"Cockpit v1.1 unavailable: {e}"[:100]
        return [{"layer": label, "status": "FAIL", "error": reason} for label in _LABELS]


# ---------------------------------------------------------------------------
# 2. get_briefing
#    SPEC_V3 §3. v1's shape and TTL, Weaver v1.1, v3's own cache.
# ---------------------------------------------------------------------------
def get_briefing():
    now = time.time()
    if _BRIEFING_CACHE["data"] is not None and now - _BRIEFING_CACHE["ts"] < _BRIEFING_TTL:
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
# 3. get_nerves
#    SPEC_V3 §4. Fails closed: an unverifiable pin file shows nothing.
# ---------------------------------------------------------------------------
def get_nerves():
    try:
        nerves = _sibling("sc-os", "nerves")
        summary = nerves.read_nerves(nerves.default_pin_path())
    except Exception as e:
        return {"available": False, "nerves": None, "error": str(e)}
    return {"available": summary is not None, "nerves": summary, "error": None}


# ---------------------------------------------------------------------------
# 8. _LegacyV3Handler
# ---------------------------------------------------------------------------
class _LegacyV3Handler(legacy_v2._LegacyV2Handler):

    # 8.1 do_GET — the three v3 routes, else v2 / v1.
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self._serve_json({"layers": probe_layers()})
        if path == "/api/weaver":
            return self._serve_json(get_briefing())
        if path == "/api/nerves":
            return self._serve_json(get_nerves())
        return super().do_GET()


# ---------------------------------------------------------------------------
# 4. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV3Handler)


# ---------------------------------------------------------------------------
# 5. main
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
    print(f"The Legacy (v3) serving on http://{host}:{port}/")
    print("  Health: /api/health   Weaver: /api/weaver   Nerves: /api/nerves")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
