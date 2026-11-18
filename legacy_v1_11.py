"""
legacy_v1_11.py — The Legacy 1.11.0: drafts through Cockpit v1.8

Function:
    The entry point from 1.11.0 (SPEC_V1_11.md). The Legacy v12 with the
    Cockpit moved from v1.7 to v1.8 (explorer-d334-forge SPEC_V1_8.md):
    drafts are written with a created_at after every pending one, and
    /api/inbox and the drafted half of /api/nouns come in the order the
    drafts were written, not in v1.7's hash order within a millisecond.
    The page (static/projection_v1_11.html) names `forge_cli_v1_8.py inbox
    commit`. Everything else is v12's. legacy.py and v2-v12 are not edited.

    python boot_v1_11.py      (the Field v8, then The Legacy 1.11.0)
    python legacy_v1_11.py [--host 127.0.0.1] [--port 8080]

Public API:
    1. nouns() -> dict
    2. pending_drafts() -> list
    3. make_server(host, port) -> ThreadingHTTPServer
    4. main(argv) -> int

Internal helpers:
    5. _cockpit — Cockpit v1.8
    6. _drafts  — pending drafts in the order written, validated and described

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v12.py (1.10.0), legacy_v4.py (Echo), forge_cli_v1_8 (1.8.0)
Spec:     SPEC_V1_11.md 1.11.0
Version:  1.11.0 (frozen 2026-11-18)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import legacy_v3  # noqa: E402
import legacy_v4  # noqa: E402
import legacy_v10 as _v10  # noqa: E402
import legacy_v12 as _v12  # noqa: E402


# ---------------------------------------------------------------------------
# 5. _cockpit
# ---------------------------------------------------------------------------
def _cockpit():
    return legacy_v3._sibling("explorer-d334-forge", "forge_cli_v1_8")


# ---------------------------------------------------------------------------
# 6. _drafts
#    v12's _drafts over Cockpit v1.8's pending_drafts (SPEC_V1_11 §1).
# ---------------------------------------------------------------------------
def _drafts():
    cockpit, out = _cockpit(), []
    for draft_id, path in cockpit.pending_drafts():
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
# ---------------------------------------------------------------------------
def pending_drafts():
    return [{"id": i, **d} if d else {"id": i, "invalid": bad} for i, d, bad in _drafts()]


# ---------------------------------------------------------------------------
# 1. nouns
#    SPEC_V1_11 §1: v12's registered nouns, then drafted ones in the order written.
# ---------------------------------------------------------------------------
def nouns():
    out = _v12.nouns()
    if out.get("error"):
        return out
    rank = {draft_id: n for n, (draft_id, _, _) in enumerate(_drafts())}
    for key in ("entities", "subjects"):
        registered = [x for x in out[key] if not x["draft"]]
        drafted = sorted((x for x in out[key] if x["draft"]), key=lambda x: rank.get(x["id"], len(rank)))
        out[key] = registered + drafted
    return out


class _LegacyV1_11Handler(_v12._LegacyV12Handler):

    # 3.1 do_GET — the v11 page, /api/nouns and /api/inbox in v1.8 order, else v12.
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", ""):
            return self._serve_static("projection_v1_11.html")
        if path == "/api/nouns":
            return self._send(200, nouns())
        if path == "/api/inbox":
            try:
                return self._send(200, pending_drafts())
            except Exception as e:
                return self._send(200, {"error": str(e)})
        return super().do_GET()

    # 3.2 do_POST — v12's, with the draft written by Cockpit v1.8.
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
    return ThreadingHTTPServer((host, port), _LegacyV1_11Handler)


# ---------------------------------------------------------------------------
# 4. main
#    v10's flags, defaults and exit codes, with 1.11.0's server (as v12 does).
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
