"""
legacy_v9.py — The Legacy v9: the page reads on a phone

Function:
    The entry point from v9 (SPEC_V10.md). v8's server (boot together,
    last good status held, self-refreshing page), serving
    static/projection_v9.html: on a phone the Claims and Ledger tables
    drop their hash columns so the text gets the width, and the hints
    name boot_v3.py and serve_v7.py. legacy.py and v2-v8 are not edited.

    python boot_v3.py      (the Field v7, then The Legacy v9)
    python legacy_v9.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. make_server(host, port) -> ThreadingHTTPServer
    2. main(argv) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v8.py (SPEC_V8.md 1.4.0)
Spec:     SPEC_V10.md 1.6.0 (over SPEC_V8.md 1.4.0)
Version:  1.6.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy_v8 as _v8  # noqa: E402


class _LegacyV9Handler(_v8._LegacyV8Handler):

    # 0.1 do_GET — the v9 page, else v8.
    def do_GET(self):
        if urlsplit(self.path).path in ("/", ""):
            return self._serve_static("projection_v9.html")
        return super().do_GET()


# ---------------------------------------------------------------------------
# 1. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV9Handler)


# ---------------------------------------------------------------------------
# 2. main
#    v8's flags, defaults and exit codes.
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
    print(f"The Legacy (v9) on http://{host}:{port}/", flush=True)
    print("  Start it with the Field: python boot_v3.py (Field on 8085, Legacy on 8080)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
