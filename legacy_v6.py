"""
legacy_v6.py — The Legacy v6, multi-face claims and a filterable ledger

Function:
    The layer over legacy_v5.py, and the entry point to run from v6 on.
    `/api/claims` also returns every filled face of each cube; `/api/chain`
    takes a `kind` filter so claims stay reachable when seals outnumber
    them; `/` serves static/projection_v6.html (SPEC_V6.md). Every other
    route is v5's (and below). legacy.py, legacy_v2–v5 are not edited.

Public API:
    1. recent_claims(limit=60) -> dict
    2. chain(limit=12, kind=None) -> dict
    3. make_server(host, port)
    4. main(argv) -> int

Internal helpers:
    5. _filled           — a capsule's filled faces, in face order
    6. _LegacyV6Handler  — v5's handler with the v6 page and routes

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v5.py (SPEC_V5 1.0.0); P9 substrate_v3 via the Cockpit
Spec:     SPEC_V6.md 1.0.0 (over SPEC_V5.md 1.0.0)
Version:  1.2.0 (frozen 2026-11-13)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v5 as _v5  # noqa: E402

_FACES = _v5._FACES
KINDS = ("claim", "seal", "proposal", "lllm.build", "record")


# ---------------------------------------------------------------------------
# 5. _filled
#    SPEC_V6 §2: a face is filled when its value is a non-empty string.
# ---------------------------------------------------------------------------
def _filled(cap):
    return {f: cap[f] for f in _FACES if isinstance(cap.get(f), str) and cap[f].strip()}


# ---------------------------------------------------------------------------
# 1. recent_claims
#    v5's rows plus `faces`, joined by claim_id from the same read-only
#    P9 listing.
# ---------------------------------------------------------------------------
def recent_claims(limit=60):
    out = _v5.recent_claims(limit)
    if not out["available"]:
        return out
    try:
        sub = _v5._v4._cockpit()._layer("substrate")
        faces = {r["claim_id"]: _filled(r["capsule"] or {}) for r in sub.list_claims(legacy._db_path())}
    except Exception as e:
        return {"available": False, "claims": [], "error": str(e)}
    for claim in out["claims"]:
        claim["faces"] = faces.get(claim["claim_id"], {})
    return out


# ---------------------------------------------------------------------------
# 2. chain
#    SPEC_V6 §2: the newest `limit` entries of `kind` (all kinds if None).
#    Labels come from v5's _label; the file is only read.
# ---------------------------------------------------------------------------
def chain(limit=12, kind=None):
    lp = os.path.join(legacy._forge_home(), "ledger.jsonl")
    if not os.path.exists(lp):
        return {"available": False, "entries": [], "total": 0, "matched": 0, "error": "no ledger yet"}
    with open(lp, "rb") as f:
        lines = f.read().splitlines()
    matched = []
    for line in lines[::-1]:
        try:
            e = json.loads(line)
            k, label = _v5._label(e.get("record") if isinstance(e.get("record"), dict) else {})
            entry = {"seq": e.get("seq"), "hash": e.get("hash", ""), "prev": e.get("prev", ""),
                     "kind": k, "label": label[:200]}
        except ValueError:
            entry = {"seq": None, "hash": "", "prev": "", "kind": "record", "label": "unreadable line"}
        if kind is None or entry["kind"] == kind:
            matched.append(entry)
    return {"available": True, "entries": matched[:limit], "total": len(lines),
            "matched": len(matched), "error": None}


# ---------------------------------------------------------------------------
# 6. _LegacyV6Handler
# ---------------------------------------------------------------------------
class _LegacyV6Handler(_v5._LegacyV5Handler):

    # 6.1 do_GET — the v6 page and routes, else v5 (and below).
    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path
        if path in ("/", ""):
            return self._serve_static("projection_v6.html")
        if path in ("/api/claims", "/api/chain"):
            q = parse_qs(parts.query)
            cap, default = (500, 60) if path == "/api/claims" else (200, 12)
            try:
                raw = q.get("limit", [""])[0]
                limit = min(cap, max(1, int(raw))) if raw else default
            except ValueError:
                return self._send(400, {"error": "limit must be a whole number"})
            if path == "/api/claims":
                return self._send(200, recent_claims(limit))
            kind = q.get("kind", [""])[0] or None
            if kind is not None and kind not in KINDS:
                return self._send(400, {"error": f"kind must be one of {', '.join(KINDS)}"})
            return self._send(200, chain(limit, kind))
        return super().do_GET()


# ---------------------------------------------------------------------------
# 3. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV6Handler)


# ---------------------------------------------------------------------------
# 4. main
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
    print(f"The Legacy (v6) on http://{host}:{port}/")
    print("  Field: run ../scp-substrate/serve_v3.py for the 3D view (port 8085)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
