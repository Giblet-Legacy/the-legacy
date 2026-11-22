"""
legacy_v2_1.py — The Legacy 2.1.0: a clearer first experience

Serves the 2.1 page over the frozen 2.0.0 routes and write guard.
Version:  2.1.0 (frozen 2026-11-22)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

import legacy_v2


class _LegacyV2_1Handler(legacy_v2._LegacyV2Handler):
    def do_GET(self):
        if urlsplit(self.path).path in ("/", ""):
            return self._serve_static("projection_v2_1.html")
        return super().do_GET()


def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV2_1Handler)


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
    print(f"The Legacy 2.1.0 on http://{host}:{port}/", flush=True)
    print("  Start it with the Field and ai-gate: python boot_v2_1.py", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
