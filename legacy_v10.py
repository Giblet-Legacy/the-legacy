"""
legacy_v10.py — The Legacy v10: the briefing through Weaver v1.4

Function:
    The entry point from v10 (SPEC_V11.md). The Legacy v9 (the page
    reads on a phone), with the Morning Briefing from the Weaver v1.4,
    which gives each open question its own engine line instead of one
    line per subject. v10's handler serves /api/weaver itself, as v7
    does, with v1.4 as the Weaver; nothing in v7 is replaced, so
    legacy.py and v2-v9 behave exactly as before.

    python boot_v4.py      (the Field v7, then The Legacy v10)
    python legacy_v10.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. _weaver() -> module   — weaver_v1_4
    2. get_briefing() -> dict — v7's shape and cache rule, through v1.4
    3. make_server(host, port) -> ThreadingHTTPServer
    4. main(argv) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v9.py (SPEC_V10.md 1.6.0), the-weaver weaver_v1_4 (1.4.0)
Spec:     SPEC_V11.md 1.7.0 (over SPEC_V10.md 1.6.0)
Version:  1.7.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import time
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v3  # noqa: E402
import legacy_v9 as _v9  # noqa: E402


_BRIEFING_CACHE = {"ts": 0.0, "data": None}


# ---------------------------------------------------------------------------
# 1. _weaver
#    SPEC_V11 §1: the Weaver v1.4.
# ---------------------------------------------------------------------------
def _weaver():
    return legacy_v3._sibling("the-weaver", "weaver_v1_4")


# ---------------------------------------------------------------------------
# 2. get_briefing
#    v7's get_briefing (shape, errors, cache for legacy_v3._BRIEFING_TTL),
#    through the Weaver v1.4.
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


class _LegacyV10Handler(_v9._LegacyV9Handler):

    # 2.1 do_GET — v10's briefing, else v9.
    def do_GET(self):
        if urlsplit(self.path).path == "/api/weaver":
            return self._send(200, get_briefing())
        return super().do_GET()


# ---------------------------------------------------------------------------
# 3. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV10Handler)


# ---------------------------------------------------------------------------
# 4. main
#    v9's flags, defaults and exit codes.
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
    print(f"The Legacy (v10) on http://{host}:{port}/", flush=True)
    print("  Start it with the Field: python boot_v4.py (Field on 8085, Legacy on 8080)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
