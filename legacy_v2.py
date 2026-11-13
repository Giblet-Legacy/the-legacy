"""
legacy_v2.py — The Legacy v2, resilient layer over the frozen v1 shell

Function:
    The entry point to run instead of legacy.py. It fixes one defect in
    v1: legacy.probe_layers() imports `cryptography` before any probe
    runs, so a missing dependency raises out of the function and turns
    GET /api/health into a 500, breaking SPEC.md §2.1 ("failures are
    captured, not raised"). v2 re-composes the same 15 probes from v1's
    own helpers so every failure becomes a FAIL row (SPEC_V2.md §2).

    legacy.py is not edited (Immutable Rule). This file is the
    "add a layer" half of that rule. Briefing, static serving, routing
    and the read-only discipline are all inherited from v1 unchanged.

Public API (same names and numbering as v1):
    1. probe_layers()   — v1 probes, every failure captured as a FAIL row
    2. get_briefing()   — re-exported from v1 unchanged
    3. make_server()    — HTTP server factory using the v2 handler
    4. main(argv)       — CLI entry point (same flags as v1)

Internal (not exported):
    5. _LegacyV2Handler — v1 handler with /api/health routed to v2 probes

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy.py (v0.1.1, frozen)
Spec:     SPEC_V2.md
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

import legacy

get_briefing = legacy.get_briefing


# ---------------------------------------------------------------------------
# probe_layers
#    Same 15 labels, same order, same checks as v1 — each built from v1's
#    helpers. The only change: nothing runs outside the per-probe
#    try/except, so a missing dependency is a FAIL row, never a raise.
# ---------------------------------------------------------------------------
def probe_layers():
    """probe_layers — 15 dicts {layer, status, error}; never raises."""
    L = legacy._layer
    has = legacy._hasattr
    table = [
        ("P1 Envelope",         lambda: L("envelope").canonicalise({"a": 1})),
        ("P2 Sign",             legacy._sign_probe),
        ("P3 Freeze",           legacy._freeze_probe),
        ("P4 Ledger",           lambda: has(L("ledger"), "append_entry")),
        ("P5 Genesis",          lambda: has(L("genesis"), "mint_genesis")),
        ("P6 Canon Verify",     lambda: has(L("canon-verify"), "verify_ledger")),
        ("P7 Record",           lambda: has(L("record"), "load_private_key")),
        ("P8 Store",            lambda: has(L("store"), "init_db")),
        ("P9 Substrate",        lambda: has(L("substrate"), "write_claim")),
        ("P10 Weight",          legacy._weight_probe),
        ("P11 Trust",           lambda: has(L("trust"), "calculate_lambda")),
        ("P12 Rules",           lambda: L("rules").create_engine().list_rules() == []),
        ("P13 DataCube",        legacy._datacube_probe),
        ("P14 Leighton Engine", legacy._leighton_probe),
        ("P15 HAL",             lambda: L("hal").tier_for_lambda(2.0) == "AUTHORITY"),
    ]

    checks = []
    for label, fn in table:
        try:
            fn()
            checks.append({"layer": label, "status": "PASS", "error": ""})
        except Exception as e:
            checks.append({"layer": label, "status": "FAIL", "error": str(e)[:100]})
    return checks


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class _LegacyV2Handler(legacy._LegacyHandler):
    """_LegacyV2Handler — v1 handler; only /api/health is rerouted to v2."""

    def do_GET(self):
        """do_GET — serve /api/health from v2 probes, else defer to v1."""
        path = urlsplit(self.path).path
        if path == "/api/health":
            self._serve_json({"layers": probe_layers()})
            return
        super().do_GET()


def make_server(host, port):
    """make_server — build the threaded HTTP server with the v2 handler."""
    return ThreadingHTTPServer((host, port), _LegacyV2Handler)


# ---------------------------------------------------------------------------
# main
#    Same flags, defaults and exit codes as v1 (SPEC.md §2.3).
# ---------------------------------------------------------------------------
def main(argv):
    """main — parse --host/--port, serve until Ctrl+C; 2 on bad arguments."""
    host = "127.0.0.1"
    port = 8080

    i = 0
    while i < len(argv):
        if argv[i] == "--host" and i + 1 < len(argv):
            host = argv[i + 1]
            i += 2
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
    print(f"The Legacy (v2) serving on http://{host}:{port}/")
    print(f"  Health:  /api/health")
    print(f"  Weaver:  /api/weaver")
    print(f"  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
