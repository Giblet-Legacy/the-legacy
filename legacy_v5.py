"""
legacy_v5.py — The Legacy v5, The Projection redesigned

Function:
    The layer over legacy_v4.py, and the entry point to run from v5 on.
    Serves the redesigned page (static/projection_v5.html) at `/` and
    adds two read-only routes it needs: the newest claims (P9, verified
    on read) and the newest ledger entries (SPEC_V5.md). Every v4 route,
    guard and the Voice are inherited unchanged. legacy.py, legacy_v2.py,
    legacy_v3.py and legacy_v4.py are not edited.

Public API:
    1. recent_claims(limit=60) -> dict
    2. chain(limit=12) -> dict
    3. make_server(host, port)
    4. main(argv) -> int

Internal helpers:
    5. _face_and_text — a capsule's face and its readable text
    6. _label         — one ledger record as (kind, label)
    7. _LegacyV5Handler — the v4 handler plus the v5 routes and page

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v4.py (SPEC_V4 1.1.0); P9 substrate_v3 via the Cockpit
Spec:     SPEC_V5.md 1.0.0 (over SPEC_V4.md 1.1.0)
Version:  1.1.0 (frozen 2026-11-13)
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
import legacy_v4 as _v4  # noqa: E402

_FACES = _v4._FACES
_GENESIS = "0" * 64


# ---------------------------------------------------------------------------
# 5. _face_and_text
# ---------------------------------------------------------------------------
def _face_and_text(cap):
    face = cap.get("face") if cap.get("face") in _FACES else next(
        (f for f in _FACES if isinstance(cap.get(f), str) and cap[f]), None)
    text = cap.get(face) if face and isinstance(cap.get(face), str) else \
        f"{cap.get('subject', '')} {cap.get('object', '')}".strip()
    return face, text


# ---------------------------------------------------------------------------
# 1. recent_claims
#    SPEC_V5 §2. Newest active claims, verified on read, read-only.
# ---------------------------------------------------------------------------
def recent_claims(limit=60):
    db = legacy._db_path()
    if not os.path.exists(db):
        return {"available": False, "claims": [], "error": "no substrate yet: remember something first"}
    try:
        sub = _v4._cockpit()._layer("substrate")
        out = []
        for r in sub.list_claims(db, verify=True)[::-1][:limit]:
            cap = r["capsule"] or {}
            face, text = _face_and_text(cap)
            att = sub.latest_attestation(db, r["claim_id"])
            out.append({"claim_id": r["claim_id"], "short": r["claim_id"][:12], "face": face,
                        "subject": cap.get("subject"), "object": cap.get("object"),
                        "polarity": cap.get("polarity"), "text": text, "created_at": r["created_at"],
                        "attested": bool(att and att.get("kind") == "attestation"), "verified": r["verified"]})
        return {"available": True, "claims": out, "error": None}
    except Exception as e:
        return {"available": False, "claims": [], "error": str(e)}


# ---------------------------------------------------------------------------
# 6. _label
# ---------------------------------------------------------------------------
def _label(rec):
    if rec.get("type") == "lllm.build":
        return "lllm.build", f"LLLM build {rec.get('build_id', '?')} anchored"
    if "decision" in rec and "seal_version" in rec:
        return "seal", f"{rec.get('decision')}: {rec.get('action_type')} — {rec.get('rationale', '')}"
    if rec.get("pending_hal") is True:
        return "proposal", f"proposal: {rec.get('action_type')} for {str(rec.get('subject_id', ''))[:12]}"
    if rec.get("face") in _FACES or "subject" in rec:
        face, text = _face_and_text(rec)
        return "claim", f"{face or 'claim'}: {text}"
    return "record", "record"


# ---------------------------------------------------------------------------
# 2. chain
#    SPEC_V5 §2. Newest ledger entries with a label. Reads the file
#    only; integrity is P6's job (/api/cockpit).
# ---------------------------------------------------------------------------
def chain(limit=12):
    lp = os.path.join(legacy._forge_home(), "ledger.jsonl")
    if not os.path.exists(lp):
        return {"available": False, "entries": [], "total": 0, "error": "no ledger yet"}
    with open(lp, "rb") as f:
        lines = f.read().splitlines()
    entries = []
    for line in lines[::-1][:limit]:
        try:
            e = json.loads(line)
        except ValueError:
            entries.append({"seq": None, "hash": "", "prev": "", "kind": "record", "label": "unreadable line"})
            continue
        kind, label = _label(e.get("record") if isinstance(e.get("record"), dict) else {})
        entries.append({"seq": e.get("seq"), "hash": e.get("hash", ""), "prev": e.get("prev", ""),
                        "kind": kind, "label": label[:200]})
    return {"available": True, "entries": entries, "total": len(lines), "error": None}


# ---------------------------------------------------------------------------
# 7. _LegacyV5Handler
# ---------------------------------------------------------------------------
class _LegacyV5Handler(_v4._LegacyV4Handler):

    # 7.1 do_GET — the v5 page and routes, else v4 (and below).
    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path
        if path in ("/", ""):
            return self._serve_static("projection_v5.html")
        if path in ("/api/claims", "/api/chain"):
            q = parse_qs(parts.query).get("limit", [""])[0]
            cap, default = (500, 60) if path == "/api/claims" else (200, 12)
            try:
                limit = min(cap, max(1, int(q))) if q else default
            except ValueError:
                return self._send(400, {"error": "limit must be a whole number"})
            return self._send(200, recent_claims(limit) if path == "/api/claims" else chain(limit))
        return super().do_GET()


# ---------------------------------------------------------------------------
# 3. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV5Handler)


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
    print(f"The Legacy (v5, The Projection) on http://{host}:{port}/")
    print("  Field: run ../scp-substrate/serve_v2.py for the 3D view (port 8085)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
