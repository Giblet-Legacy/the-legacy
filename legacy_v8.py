"""
legacy_v8.py — The Legacy v8: the last good status held, the page refreshes itself

Function:
    The layer over legacy_v7.py, and the entry point from v8 (SPEC_V8.md).
    Buffers the last good answer of the status routes (/api/cockpit,
    /api/claims, /api/chain, /api/lllm, /api/nerves) and serves it,
    marked stale, when a fresh read fails. `/` serves
    static/projection_v8.html, which refreshes every panel, backs off
    exponentially while a source is down and keeps its last good data.
    Start it with the Field through boot.py. legacy.py and legacy_v2–v7
    are not edited.

Public API:
    1. buffered(key, obj) -> dict
    2. make_server(host, port)
    3. main(argv) -> int

Internal helpers:
    4. _failed           — a response that should fall back to the buffer
    5. _LegacyV8Handler  — v7's handler with the v8 page and the buffer

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v7.py (1.3.0)
Spec:     SPEC_V8.md 1.4.0 (over SPEC_V7.md 1.3.0)
Version:  1.4.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy_v7 as _v7  # noqa: E402

BUFFERED = ("/api/cockpit", "/api/claims", "/api/chain", "/api/lllm", "/api/nerves")
_BUFFER = {}
_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# 4. _failed
# ---------------------------------------------------------------------------
def _failed(obj):
    return isinstance(obj, dict) and obj.get("available") is False


# ---------------------------------------------------------------------------
# 1. buffered
#    SPEC_V8 §3: store good answers; replace a failure with the last good.
# ---------------------------------------------------------------------------
def buffered(key, obj):
    if not isinstance(obj, dict):
        return obj
    with _LOCK:
        if not _failed(obj):
            good = dict(obj, fetched_at=datetime.now(timezone.utc).isoformat())
            _BUFFER[key] = good
            return good
        good = _BUFFER.get(key)
    if good is None:
        return obj
    return dict(good, stale=True, stale_since=good["fetched_at"], stale_error=obj.get("error"))


# ---------------------------------------------------------------------------
# 5. _LegacyV8Handler
# ---------------------------------------------------------------------------
class _LegacyV8Handler(_v7._LegacyV7Handler):

    # 5.1 _key — the buffer key for this request, or None.
    def _key(self):
        parts = urlsplit(self.path)
        return parts.path + ("?" + parts.query if parts.query else "") if parts.path in BUFFERED else None

    # 5.2 _send — v4's JSON sender, through the buffer.
    def _send(self, status, obj):
        key = self._key()
        if key is not None and status == 200:
            obj = buffered(key, obj)
        return super()._send(status, obj)

    # 5.3 _serve_json — v1's JSON sender, through the buffer.
    def _serve_json(self, obj):
        key = self._key()
        return super()._serve_json(buffered(key, obj) if key is not None else obj)

    # 5.4 do_GET — the v8 page, else v7.
    def do_GET(self):
        if urlsplit(self.path).path in ("/", ""):
            return self._serve_static("projection_v8.html")
        return super().do_GET()


# ---------------------------------------------------------------------------
# 2. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV8Handler)


# ---------------------------------------------------------------------------
# 3. main
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
    print(f"The Legacy (v8) on http://{host}:{port}/", flush=True)
    print("  Start it with the Field: python boot.py (Field on 8085, Legacy on 8080)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
