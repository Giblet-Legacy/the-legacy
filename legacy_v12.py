"""
legacy_v12.py — The Legacy v12: new entity, new subject, new claim

Function:
    The entry point from v12 (SPEC_V14.md). The Legacy v11, with the
    "New claim" card made "New" with three tabs (static/projection_v10.html):
    an entity stands alone, a subject is linked to an entity from a
    drop-down, a claim to a subject (or an entity) from a drop-down. Each
    is saved as a draft in the Cockpit v1.7 inbox and signed in the
    terminal by `forge_cli_v1_7.py inbox commit`; the Legacy never signs.
    /api/nouns feeds the drop-downs from P9 v4 and the pending drafts.
    legacy.py and v2-v11 behave exactly as before.

    python boot_v7.py      (the Field v8, then The Legacy v12)
    python legacy_v12.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. nouns() -> dict
    2. pending_drafts() -> list
    3. make_server(host, port) -> ThreadingHTTPServer
    4. main(argv) -> int

Internal helpers:
    5. _cockpit — Cockpit v1.7
    6. _p9      — P9 substrate_v4
    7. _drafts  — pending drafts, validated and described

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v11.py (1.9.0), legacy_v4.py (guard, Echo), forge_cli_v1_7 (1.7.0), substrate_v4 (4.0.0)
Spec:     SPEC_V14.md 1.10.0
Version:  1.10.0 (frozen 2026-11-16)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sqlite3
import sys
from contextlib import closing
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy  # noqa: E402
import legacy_v3  # noqa: E402
import legacy_v4  # noqa: E402
import legacy_v10 as _v10  # noqa: E402
import legacy_v11 as _v11  # noqa: E402


# ---------------------------------------------------------------------------
# 5. _cockpit
# ---------------------------------------------------------------------------
def _cockpit():
    return legacy_v3._sibling("explorer-d334-forge", "forge_cli_v1_7")


# ---------------------------------------------------------------------------
# 6. _p9
# ---------------------------------------------------------------------------
def _p9():
    return legacy_v3._sibling("substrate-layer", "substrate_v4")


# ---------------------------------------------------------------------------
# 7. _drafts
#    [(draft_id, described draft or None, reason or None)].
# ---------------------------------------------------------------------------
def _drafts():
    cockpit, out = _cockpit(), []
    for draft_id, path in cockpit._v12._pending_drafts():
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            cockpit.validate_any(d)
            out.append((draft_id, cockpit.describe(d), None))
        except (OSError, ValueError) as e:
            out.append((draft_id, None, str(e)))
    return out


# ---------------------------------------------------------------------------
# 2. pending_drafts
#    SPEC_V14 §2: every kind, or invalid with its reason.
# ---------------------------------------------------------------------------
def pending_drafts():
    return [{"id": i, **d} if d else {"id": i, "invalid": bad} for i, d, bad in _drafts()]


# ---------------------------------------------------------------------------
# 1. nouns
#    SPEC_V14 §2: registered (P9 v4) then drafted; read-only.
# ---------------------------------------------------------------------------
def nouns():
    out = {"entities": [], "subjects": [], "error": None}
    db = legacy._db_path()
    try:
        if os.path.exists(db):
            with closing(sqlite3.connect(f"file:{db}?mode=ro", uri=True)) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if {"entities", "subjects", "memberships"} <= tables:
                p9 = _p9()
                for r in p9.list_entities(db):
                    out["entities"].append({"id": r["id"], "name": r["name"], "kind": r["kind"], "draft": False})
                for r in p9.list_subjects(db):
                    out["subjects"].append({"id": r["id"], "name": r["name"], "kind": r["kind"], "draft": False,
                                            "entities": [m["name"] for m in p9.members(db, r["id"])]})
        for draft_id, d, _ in _drafts():
            if d and d["kind"] == "entity":
                out["entities"].append({"id": draft_id, "name": d["name"], "kind": None, "draft": True})
            elif d and d["kind"] == "subject":
                out["subjects"].append({"id": draft_id, "name": d["name"], "kind": None, "draft": True,
                                        "entities": [d["entity"]]})
    except Exception as e:
        out["error"] = f"nouns failed: {e}"
    return out


class _LegacyV12Handler(_v11._LegacyV11Handler):

    # 3.1 do_GET — the v10 page, /api/nouns and /api/inbox, else v11.
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", ""):
            return self._serve_static("projection_v10.html")
        if path == "/api/nouns":
            return self._send(200, nouns())
        if path == "/api/inbox":
            try:
                return self._send(200, pending_drafts())
            except Exception as e:
                return self._send(200, {"error": str(e)})
        return super().do_GET()

    # 3.2 do_POST — v4's guard; any kind of draft through Cockpit v1.7.
    def do_POST(self):
        if urlsplit(self.path).path != "/api/inbox":
            return self.send_error(405, "Method not allowed")
        refused = self._guard()
        if refused:
            return self._send(refused[0], {"error": refused[1]})
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            draft_id = _cockpit().write_draft_any(body)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": f"draft not saved: {e}"})
        if "kind" in body:
            return self._send(201, {"draft_id": draft_id})
        preview = legacy_v4.echo_preview({k: body[k] for k in ("subject", "object", "face", "text")})
        return self._send(201, {"draft_id": draft_id, "echo": preview})


# ---------------------------------------------------------------------------
# 3. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV12Handler)


# ---------------------------------------------------------------------------
# 4. main
#    v10's flags, defaults and exit codes, with v12's server.
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
