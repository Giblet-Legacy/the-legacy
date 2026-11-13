"""
legacy.py — The Legacy primitive layer (Phase 1: The Shell)

Function:
    The master orchestrator's first phase. A web dashboard on port
    8080 that surfaces the state of the 15-layer stack and the
    Weaver's morning voice. Read-only. Calls sibling consumers; does
    not reimplement them.

Public API:
    1. probe_layers()   — 15 layer probes, PASS/FAIL per layer.
    2. get_briefing()   — Weaver's briefing, cached on success.
    3. make_server()    — HTTP server factory (for tests and CLI).
    4. main(argv)       — CLI entry point.

Tier:     Tier 1 — Consumer (The Connector)
Depends:  P1–P15 (via probes), the-weaver (via import)
Version:  1.0.0 (on freeze; 0.0.0-dev until then)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import json
import time
import importlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


_LAYER_CACHE = {}
_BRIEFING_CACHE = {"ts": 0.0, "data": None}
_BRIEFING_TTL = 3600.0

_LAYER_MAP = {
    "envelope":         ("envelope-layer",         "envelope_v2"),
    "sign":             ("sign-layer",             "sign"),
    "freeze":           ("freeze-layer",           "freeze"),
    "ledger":           ("ledger-layer",           "ledger"),
    "genesis":          ("genesis-layer",          "genesis"),
    "canon-verify":     ("canon-verify-layer",     "canon_verify"),
    "record":           ("record-layer",           "record"),
    "store":            ("store-layer",            "store"),
    "substrate":        ("substrate-layer",        "substrate"),
    "weight":           ("weight-layer",           "weight"),
    "trust":            ("trust-layer",            "trust"),
    "leighton-engine":  ("leighton-engine-layer",  "leighton_engine"),
    "rules":            ("rules-layer",            "rules"),
    "datacube":         ("datacube-layer",         "datacube"),
    "hal":              ("hal-layer",              "hal"),
}


def _layer(name):
    if name in _LAYER_CACHE:
        return _LAYER_CACHE[name]
    here = os.path.dirname(os.path.abspath(__file__))
    dirname, modname = _LAYER_MAP[name]
    p = os.path.abspath(os.path.join(here, "..", dirname))
    if not os.path.isdir(p):
        raise RuntimeError(f"layer '{name}' not found at {p}")
    if p not in sys.path:
        sys.path.insert(0, p)
    mod = importlib.import_module(modname)
    _LAYER_CACHE[name] = mod
    return mod


def _forge_home():
    home = os.environ.get("FORGE_HOME")
    if not home:
        home = os.path.expanduser("~/.forge")
    return home


def _db_path():
    return os.path.join(_forge_home(), "forge.db")


# ---------------------------------------------------------------------------
# probe_layers
#    Returns 15 dicts: {layer, status, error}. Failures are captured,
#    not raised — a broken layer becomes a FAIL row.
# ---------------------------------------------------------------------------
def probe_layers():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    checks = []

    def probe(label, fn):
        try:
            fn()
            checks.append({"layer": label, "status": "PASS", "error": ""})
        except Exception as e:
            checks.append({"layer": label, "status": "FAIL", "error": str(e)[:100]})

    probe("P1 Envelope", lambda: _layer("envelope").canonicalise({"a": 1}))
    probe("P2 Sign", lambda: _sign_probe())
    probe("P3 Freeze", lambda: _freeze_probe())
    probe("P4 Ledger", lambda: _hasattr(_layer("ledger"), "append_entry"))
    probe("P5 Genesis", lambda: _hasattr(_layer("genesis"), "mint_genesis"))
    probe("P6 Canon Verify", lambda: _hasattr(_layer("canon-verify"), "verify_ledger"))
    probe("P7 Record", lambda: _hasattr(_layer("record"), "load_private_key"))
    probe("P8 Store", lambda: _hasattr(_layer("store"), "init_db"))
    probe("P9 Substrate", lambda: _hasattr(_layer("substrate"), "write_claim"))
    probe("P10 Weight", lambda: _weight_probe())
    probe("P11 Trust", lambda: _hasattr(_layer("trust"), "calculate_lambda"))
    probe("P12 Rules", lambda: _layer("rules").create_engine().list_rules() == [])
    probe("P13 DataCube", lambda: _datacube_probe())
    probe("P14 Leighton Engine", lambda: _leighton_probe())
    probe("P15 HAL", lambda: _layer("hal").tier_for_lambda(2.0) == "AUTHORITY")

    return checks


def _hasattr(mod, name):
    if not hasattr(mod, name):
        raise RuntimeError(f"missing {name}")
    return True


def _sign_probe():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    sign_mod = _layer("sign")
    key = Ed25519PrivateKey.generate()
    signed = sign_mod.sign_capsule({"test": True}, key)
    if not sign_mod.verify_capsule(signed, key.public_key()):
        raise RuntimeError("verify_capsule returned False")
    return True


def _freeze_probe():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    fr = _layer("freeze")
    key = Ed25519PrivateKey.generate()
    out = fr.freeze_capsule({"content": "x"}, key)
    if "document_sha256" not in out:
        raise RuntimeError("freeze_capsule did not populate document_sha256")
    return True


def _weight_probe():
    w = _layer("weight")
    val = w.leighton_weight(1.0, 0.0, 0.1)
    if val != 1.0:
        raise RuntimeError(f"leighton_weight(1.0, 0.0, 0.1) = {val}, expected 1.0")
    return True


def _datacube_probe():
    dc = _layer("datacube")
    cube = dc.create_cube({"subject": "x", "object": "y"})
    if dc.count_faces(cube) != 0:
        raise RuntimeError("empty cube should have 0 faces")
    return True


def _leighton_probe():
    le = _layer("leighton-engine")
    result = le.compute_lambda(
        [{"timestamp": 0.0, "value": 1.5}],
        k=0.1, reference_time=0.0, computed_at=0.0,
    )
    if "lambda" not in result:
        raise RuntimeError("compute_lambda returned no lambda")
    return True


# ---------------------------------------------------------------------------
# get_briefing
#    Delegates to the-weaver. Caches successful briefings for 1 hour.
#    Errors are retried every load (not cached) so a transient failure
#    does not stick.
# ---------------------------------------------------------------------------
def get_briefing():
    now = time.time()
    if (_BRIEFING_CACHE["data"] is not None
            and (now - _BRIEFING_CACHE["ts"]) < _BRIEFING_TTL):
        return _BRIEFING_CACHE["data"]

    result = _compute_briefing()

    if result.get("error") is None:
        _BRIEFING_CACHE["data"] = result
        _BRIEFING_CACHE["ts"] = now

    return result


def _compute_briefing():
    result = {"briefing": None, "claims": [], "error": None}

    try:
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.abspath(os.path.join(here, "..", "the-weaver"))
        if p not in sys.path:
            sys.path.insert(0, p)
        weaver = importlib.import_module("weaver")
    except Exception as e:
        result["error"] = f"weaver not available: {e}"
        return result

    db_path = _db_path()
    if not os.path.exists(db_path):
        result["error"] = f"database missing: {db_path}"
        return result

    try:
        claims = weaver.find_decayed_unknowns(db_path)
    except Exception as e:
        result["error"] = f"weaver query failed: {e}"
        return result

    if not claims:
        result["error"] = "no UNKNOWN claims to weave"
        return result

    result["claims"] = claims

    try:
        prompt = weaver.build_prompt(claims)
        briefing = weaver.call_lllm(prompt)
        result["briefing"] = briefing
    except RuntimeError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"weaver failed: {e}"

    return result


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
def _static_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class _LegacyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

        if ".." in path:
            self.send_error(400, "Bad request")
            return

        if path == "/api/health":
            self._serve_json({"layers": probe_layers()})
            return

        if path == "/api/weaver":
            self._serve_json(get_briefing())
            return

        if path == "/" or path == "":
            self._serve_static("index.html")
            return

        if path.startswith("/static/"):
            self._serve_static(path[len("/static/"):])
            return

        self.send_error(404, "Not found")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        self.send_error(405, "Method not allowed")

    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST

    def _serve_json(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _serve_static(self, rel):
        if not rel or ".." in rel or rel.startswith("/"):
            self.send_error(404, "Not found")
            return
        full = os.path.abspath(os.path.join(_static_dir(), rel))
        if not full.startswith(os.path.abspath(_static_dir()) + os.sep):
            self.send_error(404, "Not found")
            return
        if not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full)[1].lower()
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css":  "text/css; charset=utf-8",
            ".js":   "application/javascript",
            ".json": "application/json",
            ".png":  "image/png",
            ".svg":  "image/svg+xml",
        }.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyHandler)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv):
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
    print(f"The Legacy serving on http://{host}:{port}/")
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
