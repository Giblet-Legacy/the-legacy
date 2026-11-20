"""
legacy_v11.py — The Legacy v11: one link, the Field's address for the browser

Function:
    The entry point from v11 (SPEC_V13.md). The Legacy v10, with
    /api/field telling the page FORGE_FIELD_PUBLIC_URL (when set and
    safe) as the Field's address, while the health probe still uses
    FORGE_FIELD_URL. On the VPS the Field is published under the
    Legacy's own address at /field/, so the page's iframe and link
    work from any device on the tailnet. On a laptop, with no variable,
    nothing changes. legacy.py and v2-v10 behave exactly as before.

    python boot_v6.py      (the Field v8, then The Legacy v11)
    python legacy_v11.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. public_field_url(probed) -> str
    2. field_status() -> dict
    3. make_server(host, port) -> ThreadingHTTPServer
    4. main(argv) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v10.py (SPEC_V11.md 1.7.0), legacy_v4.py (field_status)
Spec:     SPEC_V13.md 1.9.0
Version:  1.9.0 (frozen 2026-11-16)
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

import legacy_v4  # noqa: E402
import legacy_v10 as _v10  # noqa: E402


# ---------------------------------------------------------------------------
# 1. public_field_url
#    SPEC_V13 §1: a path starting with "/" (not "//") or an http(s) URL;
#    anything else falls back to the probed URL.
# ---------------------------------------------------------------------------
def public_field_url(probed):
    value = (os.environ.get("FORGE_FIELD_PUBLIC_URL") or "").strip()
    if value.startswith("/") and not value.startswith("//"):
        return value
    if urlsplit(value).scheme in ("http", "https") and urlsplit(value).netloc:
        return value
    return probed


# ---------------------------------------------------------------------------
# 2. field_status
#    v4's probe and shape; only the url the page is given changes.
# ---------------------------------------------------------------------------
def field_status():
    status = legacy_v4.field_status()
    status["url"] = public_field_url(status["url"])
    return status


class _LegacyV11Handler(_v10._LegacyV10Handler):

    # 2.1 do_GET — v11's /api/field, else v10.
    def do_GET(self):
        if urlsplit(self.path).path == "/api/field":
            return self._send(200, field_status())
        return super().do_GET()


# ---------------------------------------------------------------------------
# 3. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV11Handler)


# ---------------------------------------------------------------------------
# 4. main
#    v10's flags, defaults and exit codes, with v11's server.
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
