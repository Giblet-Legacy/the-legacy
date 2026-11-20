"""
legacy_v2.py — The Legacy 2.0.0: one page over every consumer, in one module

Function:
    The consolidation of 1.12.0 (CONSOLIDATION_V2.md, SPEC_V2.md). 1.12.0
    ran through fourteen modules (legacy.py, legacy_v2 ... v12, v1_11,
    v1_12), a handler thirteen subclasses deep and a main that
    monkeypatched legacy_v10. This module is what that chain did, route
    by route, flattened: the same routes, answers, status codes, guard,
    buffer, caches and page, with each route's code taken from the layer
    that answered it in 1.12.0 (named in each header below). Nothing is
    added and nothing fixed. The 1.12.0 files are byte-identical in
    archive/1.12.0/ and at the tag v1.12.0.

    The Legacy never calls a model and never signs. Its one write is an
    inbox draft (through the Cockpit), and asks and ratings relayed to
    ai-gate; both pass the write guard (local host, X-Forge-Legacy, JSON),
    so on the VPS they are refused.

    python boot_v2.py         (the Field, ai-gate, then The Legacy 2.0.0)
    python legacy_v2.py [--host 127.0.0.1] [--port 8080]

Public API:
    1.  probe_layers() -> list         — /api/health (from v3: Cockpit v1.1's probes)
    2.  get_nerves() -> dict           — /api/nerves (from v3: SC-OS nerves)
    3.  get_briefing() -> dict         — /api/weaver (from v10: Weaver v1.4, cached 1 h)
    4.  voice_turn(text) -> dict       — /api/voice (from v7: the Voice, LLLM 0.1.2)
    5.  cockpit_status() -> dict       — /api/cockpit (from v7: Cockpit v1.3)
    6.  lllm_status() -> dict          — /api/lllm (from v7: Cockpit v1.3)
    7.  field_status() -> dict         — /api/field (from v4 and v11: probe, public URL)
    8.  echo_preview(fields) -> dict   — /api/echo and claim drafts (from v4: Echo v1.1)
    9.  recent_claims(limit) -> dict   — /api/claims (from v5 and v6: every filled face)
    10. chain(limit, kind) -> dict     — /api/chain (from v6)
    11. pending_drafts() -> list       — /api/inbox (from v1_11: Cockpit v1.8, in the order written)
    12. nouns() -> dict                — /api/nouns (from v12 and v1_11)
    13. buffered(key, obj) -> dict     — the last-good buffer (from v8)
    14. gate_url() -> str              — ai-gate's local API (from v1_12)
    15. make_server(host, port) -> ThreadingHTTPServer
    16. main(argv) -> int

Internal helpers:
    17. _forge_home, _db_path, _sibling, _weaver, _voice, _claim_fields,
        _face_and_text, _filled, _label, _drafts, _relay, _failed
    18. _LegacyV2Handler — the one handler

Tier:     Tier 1 — Consumer (The Connector)
Depends:  explorer-d334-forge (Cockpit forge_cli_v1_1, v1_2, v1_3, v1_8, each where 1.12.0 used it),
          the-weaver weaver_v1_4, lllm lllm_v0_1_2, the-echo echo_v1_1, sc-os nerves,
          substrate-layer substrate_v4, ai-gate ai_gate_serve.py (its HTTP API only)
Spec:     SPEC_V2.md 2.0.0
Version:  2.0.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import importlib
import json
import os
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_FIELD_URL = "http://127.0.0.1:8085/"
MAX_BODY = 8192
MAX_VOICE_INPUT = 2000
_FACES = ("FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN")
KINDS = ("claim", "seal", "proposal", "lllm.build", "record")
_LABELS = ["P1 Envelope", "P2 Sign", "P3 Freeze", "P4 Ledger", "P5 Genesis",
           "P6 Canon Verify", "P7 Record", "P8 Store", "P9 Substrate", "P10 Weight",
           "P11 Trust", "P12 Rules", "P13 DataCube", "P14 Leighton Engine", "P15 HAL"]
BUFFERED = ("/api/cockpit", "/api/claims", "/api/chain", "/api/lllm", "/api/nerves")
GET_ALLOWED = ("health", "status", "threads", "thread", "assumptions", "assumption", "known", "score")
POST_ALLOWED = ("ask", "rate")
OFFLINE = "ai-gate is not running (start it with boot_v2.py, or python ../ai-gate/ai_gate_serve.py)"

_BRIEFING_TTL = 3600.0
_BRIEFING_CACHE = {"ts": 0.0, "data": None}
_VOICE = {"session": None, "lock": threading.Lock()}
_BUFFER = {}
_LOCK = threading.Lock()
_STATIC = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript",
           ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml"}


# ---------------------------------------------------------------------------
# 17. Internal helpers
# ---------------------------------------------------------------------------
# 17a. _forge_home / _db_path — FORGE_HOME, else ~/.forge (from legacy.py)
def _forge_home():
    return os.environ.get("FORGE_HOME") or os.path.expanduser("~/.forge")


def _db_path():
    return os.path.join(_forge_home(), "forge.db")


# 17b. _sibling — import a module from a sibling repository (from v3)
def _sibling(repo, module):
    path = os.path.abspath(os.path.join(_HERE, "..", repo))
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(module)


# 17c. the sibling modules, each at the version 1.12.0 used for that route
def _weaver():
    return _sibling("the-weaver", "weaver_v1_4")


def _voice():
    return _sibling("lllm", "lllm_v0_1_2")


def _cockpit_v1_1():
    return _sibling("explorer-d334-forge", "forge_cli_v1_1")


def _cockpit_v1_2():
    return _sibling("explorer-d334-forge", "forge_cli_v1_2")


def _cockpit_v1_3():
    return _sibling("explorer-d334-forge", "forge_cli_v1_3")


def _cockpit():
    return _sibling("explorer-d334-forge", "forge_cli_v1_8")


def _echo():
    return _sibling("the-echo", "echo_v1_1")


def _p9():
    return _sibling("substrate-layer", "substrate_v4")


# ---------------------------------------------------------------------------
# 1. probe_layers (from v3)
#    Cockpit v1.1's 15 probes; if the Cockpit cannot load, 15 FAIL rows.
# ---------------------------------------------------------------------------
def probe_layers():
    try:
        return _cockpit_v1_1().probe_layers()
    except Exception as e:
        reason = f"Cockpit v1.1 unavailable: {e}"[:100]
        return [{"layer": label, "status": "FAIL", "error": reason} for label in _LABELS]


# ---------------------------------------------------------------------------
# 2. get_nerves (from v3)
# ---------------------------------------------------------------------------
def get_nerves():
    try:
        nerves = _sibling("sc-os", "nerves")
        summary = nerves.read_nerves(nerves.default_pin_path())
    except Exception as e:
        return {"available": False, "nerves": None, "error": str(e)}
    return {"available": summary is not None, "nerves": summary, "error": None}


# ---------------------------------------------------------------------------
# 3. get_briefing (from v10)
#    Weaver v1.4's compose_briefing; a good briefing is cached for an hour.
# ---------------------------------------------------------------------------
def get_briefing():
    now = time.time()
    if _BRIEFING_CACHE["data"] is not None and now - _BRIEFING_CACHE["ts"] < _BRIEFING_TTL:
        return _BRIEFING_CACHE["data"]
    result = {"briefing": None, "claims": [], "error": None}
    try:
        weaver = _weaver()
        db_path = _db_path()
        if not os.path.exists(db_path):
            result["error"] = f"database missing: {db_path}"
            return result
        claims = weaver.find_decayed_unknowns(db_path)
        if not claims:
            result["error"] = "no UNKNOWN claims to weave"
            return result
        result["claims"] = claims
        result["briefing"] = weaver.compose_briefing(claims)
    except Exception as e:
        result["error"] = f"weaver failed: {e}"
    if result["error"] is None:
        _BRIEFING_CACHE.update(ts=now, data=result)
    return result


# ---------------------------------------------------------------------------
# 4. voice_turn (from v7)
#    One Session per database, shared by every request, one turn at a time.
# ---------------------------------------------------------------------------
def voice_turn(text):
    try:
        voice = _voice()
    except Exception as e:
        return {"available": False, "reply": None, "trace": None, "trace_text": None,
                "error": f"the Voice is not installed: {e}"}
    with _VOICE["lock"]:
        db = _db_path()
        if _VOICE["session"] is None or _VOICE["session"].db_path != db:
            _VOICE["session"] = voice.Session(db)
        reply, trace = _VOICE["session"].turn(text)
    return {"available": True, "reply": reply, "trace": trace,
            "trace_text": voice.format_trace(trace), "error": None}


# ---------------------------------------------------------------------------
# 5. cockpit_status (from v7)
# ---------------------------------------------------------------------------
def cockpit_status():
    try:
        return {"available": True, "status": _cockpit_v1_3().status(), "error": None}
    except Exception as e:
        return {"available": False, "status": None, "error": str(e)}


# ---------------------------------------------------------------------------
# 6. lllm_status (from v7)
#    The installed LLLM build, and whether the ledger anchors it.
# ---------------------------------------------------------------------------
def lllm_status():
    out = {"available": False, "build_id": None, "identity": None, "warnings": [],
           "anchored": False, "error": None}
    try:
        cockpit = _cockpit_v1_3()
        prov = cockpit.lllm_provenance()
    except Exception as e:
        out["error"] = str(e)
        return out
    anchored = any((e.get("record") or {}).get("type") == "lllm.build"
                   and e["record"].get("build_json_sha256") == prov["build_json_sha256"]
                   for e in cockpit._v11._ledger_entries())
    out.update(available=True, build_id=prov["build_id"], identity=prov["identity"],
               warnings=prov["warnings"], anchored=anchored)
    return out


# ---------------------------------------------------------------------------
# 7. field_status (from v4, with v11's public URL)
#    FORGE_FIELD_URL is probed (1 s); FORGE_FIELD_PUBLIC_URL, when it is a
#    path or an http(s) URL, is the link the page is given.
# ---------------------------------------------------------------------------
def public_field_url(probed):
    value = (os.environ.get("FORGE_FIELD_PUBLIC_URL") or "").strip()
    if value.startswith("/") and not value.startswith("//"):
        return value
    if urlsplit(value).scheme in ("http", "https") and urlsplit(value).netloc:
        return value
    return probed


def field_status():
    url = os.environ.get("FORGE_FIELD_URL") or DEFAULT_FIELD_URL
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/health", timeout=1) as r:
            reachable = r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        reachable = False
    return {"url": public_field_url(url), "reachable": reachable}


# ---------------------------------------------------------------------------
# 8. echo_preview (from v4)
# ---------------------------------------------------------------------------
def _claim_fields(raw):
    fields = {k: (raw.get(k) or "").strip() for k in ("subject", "object", "face", "text")}
    fields["face"] = fields["face"].upper()
    if not fields["subject"] or not fields["object"]:
        raise ValueError("subject and object are required")
    if len(fields["subject"]) > 200 or len(fields["object"]) > 200 or len(fields["text"]) > 2000:
        raise ValueError("field too long")
    if fields["face"] not in _FACES:
        raise ValueError(f"face must be one of {_FACES}")
    return fields


def echo_preview(fields):
    db = _db_path()
    if not os.path.exists(db):
        return {"error": "no substrate yet: remember something first"}
    try:
        out = _echo().echo(db, dict(fields))
    except Exception as e:
        return {"error": f"echo failed: {e}"}
    return {k: out[k] for k in ("gate", "rules_fired", "shape", "memory")}


# ---------------------------------------------------------------------------
# 9. recent_claims (from v5, with v6's filled faces)
# ---------------------------------------------------------------------------
def _face_and_text(cap):
    face = cap.get("face") if cap.get("face") in _FACES else next(
        (f for f in _FACES if isinstance(cap.get(f), str) and cap[f]), None)
    text = cap.get(face) if face and isinstance(cap.get(face), str) else \
        f"{cap.get('subject', '')} {cap.get('object', '')}".strip()
    return face, text


def _filled(cap):
    return {f: cap[f] for f in _FACES if isinstance(cap.get(f), str) and cap[f].strip()}


def recent_claims(limit=60):
    db = _db_path()
    if not os.path.exists(db):
        return {"available": False, "claims": [], "error": "no substrate yet: remember something first"}
    try:
        sub = _cockpit_v1_2()._layer("substrate")
        out = []
        for r in sub.list_claims(db, verify=True)[::-1][:limit]:
            cap = r["capsule"] or {}
            face, text = _face_and_text(cap)
            att = sub.latest_attestation(db, r["claim_id"])
            out.append({"claim_id": r["claim_id"], "short": r["claim_id"][:12], "face": face,
                        "subject": cap.get("subject"), "object": cap.get("object"),
                        "polarity": cap.get("polarity"), "text": text, "created_at": r["created_at"],
                        "attested": bool(att and att.get("kind") == "attestation"), "verified": r["verified"]})
    except Exception as e:
        return {"available": False, "claims": [], "error": str(e)}
    try:
        sub = _cockpit_v1_2()._layer("substrate")
        faces = {r["claim_id"]: _filled(r["capsule"] or {}) for r in sub.list_claims(_db_path())}
    except Exception as e:
        return {"available": False, "claims": [], "error": str(e)}
    for claim in out:
        claim["faces"] = faces.get(claim["claim_id"], {})
    return {"available": True, "claims": out, "error": None}


# ---------------------------------------------------------------------------
# 10. chain (from v6)
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


def chain(limit=12, kind=None):
    lp = os.path.join(_forge_home(), "ledger.jsonl")
    if not os.path.exists(lp):
        return {"available": False, "entries": [], "total": 0, "matched": 0, "error": "no ledger yet"}
    with open(lp, "rb") as f:
        lines = f.read().splitlines()
    matched = []
    for line in lines[::-1]:
        try:
            e = json.loads(line)
            k, label = _label(e.get("record") if isinstance(e.get("record"), dict) else {})
            entry = {"seq": e.get("seq"), "hash": e.get("hash", ""), "prev": e.get("prev", ""),
                     "kind": k, "label": label[:200]}
        except ValueError:
            entry = {"seq": None, "hash": "", "prev": "", "kind": "record", "label": "unreadable line"}
        if kind is None or entry["kind"] == kind:
            matched.append(entry)
    return {"available": True, "entries": matched[:limit], "total": len(lines),
            "matched": len(matched), "error": None}


# ---------------------------------------------------------------------------
# 11. pending_drafts (from v1_11)
#     Cockpit v1.8's inbox, in the order written; a bad draft is shown as invalid.
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


def pending_drafts():
    return [{"id": i, **d} if d else {"id": i, "invalid": bad} for i, d, bad in _drafts()]


# ---------------------------------------------------------------------------
# 12. nouns (from v12, ordered as v1_11)
#     Registered entities and subjects (P9 v4), then drafted ones in the
#     order written. 1.12.0 listed the drafts through Cockpit v1.7 and then
#     sorted them into v1.8's order; v1.7 and v1.8 read the same inbox files
#     with the same validate_any and describe (v1.8 re-exports them), so
#     listing them through v1.8 directly gives the same answer.
# ---------------------------------------------------------------------------
def nouns():
    out = {"entities": [], "subjects": [], "error": None}
    db = _db_path()
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


# ---------------------------------------------------------------------------
# 13. buffered (from v8)
#     A good answer is kept; a failed one ("available": false) is answered
#     with the last good one, marked stale.
# ---------------------------------------------------------------------------
def _failed(obj):
    return isinstance(obj, dict) and obj.get("available") is False


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
# 14. gate_url / _relay (from v1_12)
# ---------------------------------------------------------------------------
def gate_url():
    return (os.environ.get("FORGE_AI_GATE_URL") or "http://127.0.0.1:8092").rstrip("/")


def _relay(method, path_and_query, body=None, timeout=10):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers.update({"Content-Type": "application/json", "X-Forge-Legacy": "1"})
    req = urllib.request.Request(gate_url() + path_and_query, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {"error": f"ai-gate answered {e.code}"}
    except (urllib.error.URLError, OSError, ValueError):
        return None, None


# ---------------------------------------------------------------------------
# 18. _LegacyV2Handler
#     Each route is checked in the order 1.12.0's chain reached it.
# ---------------------------------------------------------------------------
class _LegacyV2Handler(BaseHTTPRequestHandler):

    # 18a. log_message — quiet (from legacy.py)
    def log_message(self, fmt, *args):
        pass

    # 18b. _key — the buffer key for a buffered route, else None (from v8)
    def _key(self):
        parts = urlsplit(self.path)
        return parts.path + ("?" + parts.query if parts.query else "") if parts.path in BUFFERED else None

    # 18c. _write — status, JSON headers, and the body unless HEAD (v4's _send, legacy.py's _serve_json)
    def _write(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # 18d. _send — JSON with a status; buffered routes pass through the buffer on 200 (v8 over v4)
    def _send(self, status, obj):
        key = self._key()
        if key is not None and status == 200:
            obj = buffered(key, obj)
        return self._write(status, obj)

    # 18e. _serve_json — JSON, 200; buffered routes pass through the buffer (v8 over legacy.py)
    def _serve_json(self, obj):
        key = self._key()
        return self._write(200, buffered(key, obj) if key is not None else obj)

    # 18f. _serve_static — a file under static/, never outside it (from legacy.py)
    def _serve_static(self, rel):
        if not rel or ".." in rel or rel.startswith("/"):
            self.send_error(404, "Not found")
            return
        static = os.path.join(_HERE, "static")
        full = os.path.abspath(os.path.join(static, rel))
        if not full.startswith(os.path.abspath(static) + os.sep):
            self.send_error(404, "Not found")
            return
        if not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        mime = _STATIC.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # 18g. _guard — the write guard (from v4): local host, same origin, X-Forge-Legacy, JSON, size
    def _guard(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in hosts:
            return 403, "host not allowed"
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            return 403, "cross-origin request refused"
        if self.headers.get("X-Forge-Legacy") != "1":
            return 403, "missing X-Forge-Legacy header"
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            return 415, "Content-Type must be application/json"
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return 400, "Content-Length required"
        if length > MAX_BODY:
            return 413, f"body over {MAX_BODY} bytes"
        return None

    # 18h. _ai_name — the <name> of /api/ai/<name>, else None (from v1_12)
    def _ai_name(self):
        parts = urlsplit(self.path).path.split("/")
        if len(parts) == 4 and parts[1] == "api" and parts[2] == "ai":
            return parts[3]
        return None

    # 18i. do_GET — every read, in 1.12.0's order
    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path
        # the page (v1_12)
        if path in ("/", ""):
            return self._serve_static("projection_v2.html")
        # ai-gate reads, from the allowlist only (v1_12)
        if path.startswith("/api/ai/"):
            name = self._ai_name()
            if name not in GET_ALLOWED:
                return self._send(404, {"error": "not an ai-gate read"})
            status, body = _relay("GET", f"/api/{name}" + (f"?{parts.query}" if parts.query else ""))
            if status is None:
                return self._send(200, {"error": OFFLINE, "offline": True})
            return self._send(status, body)
        # drafts and nouns (v1_11)
        if path == "/api/nouns":
            return self._send(200, nouns())
        if path == "/api/inbox":
            try:
                return self._send(200, pending_drafts())
            except Exception as e:
                return self._send(200, {"error": str(e)})
        # the Field (v11)
        if path == "/api/field":
            return self._send(200, field_status())
        # the briefing (v10)
        if path == "/api/weaver":
            return self._send(200, get_briefing())
        # the Voice, the LLLM build, the Cockpit (v7)
        if path == "/api/voice":
            q = parse_qs(parts.query).get("q", [""])[0].strip()
            if not q or len(q) > MAX_VOICE_INPUT:
                return self._send(400, {"error": f"q must be 1–{MAX_VOICE_INPUT} characters"})
            return self._send(200, voice_turn(q))
        if path == "/api/lllm":
            return self._send(200, lllm_status())
        if path == "/api/cockpit":
            return self._send(200, cockpit_status())
        # claims and the chain (v6)
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
        # the Echo (v4)
        if path == "/api/echo":
            q = {k: v[0] for k, v in parse_qs(parts.query).items()}
            try:
                fields = _claim_fields(q)
            except ValueError as e:
                return self._send(400, {"error": str(e)})
            return self._send(200, echo_preview(fields))
        # health and nerves (v3)
        if path == "/api/health":
            return self._serve_json({"layers": probe_layers()})
        if path == "/api/nerves":
            return self._serve_json(get_nerves())
        # what is left (legacy.py)
        if ".." in path:
            self.send_error(400, "Bad request")
            return
        if path.startswith("/static/"):
            self._serve_static(path[len("/static/"):])
            return
        self.send_error(404, "Not found")

    # 18j. do_HEAD — a GET without the body (from legacy.py)
    def do_HEAD(self):
        self.do_GET()

    # 18k. do_POST — ai-gate asks and ratings (v1_12), an inbox draft (v1_11); else 405
    def do_POST(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/ai/"):
            name = self._ai_name()
            if name not in POST_ALLOWED:
                return self._send(404, {"error": "not an ai-gate write (seals are made in the terminal)"})
            refused = self._guard()
            if refused:
                return self._send(refused[0], {"error": refused[1]})
            try:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            except (ValueError, TypeError):
                return self._send(400, {"error": "body must be JSON"})
            status, out = _relay("POST", f"/api/{name}", body, timeout=150 if name == "ask" else 15)
            if status is None:
                return self._send(503, {"error": OFFLINE})
            return self._send(status, out)
        if path != "/api/inbox":
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
        preview = echo_preview({k: body[k] for k in ("subject", "object", "face", "text")})
        return self._send(201, {"draft_id": draft_id, "echo": preview})

    # 18l. do_PUT / do_DELETE / do_PATCH / do_OPTIONS — 405 (legacy.py, v4)
    def _not_allowed(self):
        self.send_error(405, "Method not allowed")

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _not_allowed


# ---------------------------------------------------------------------------
# 15. make_server
# ---------------------------------------------------------------------------
def make_server(host, port):
    return ThreadingHTTPServer((host, port), _LegacyV2Handler)


# ---------------------------------------------------------------------------
# 16. main (v10's flags, defaults and exit codes)
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
    print(f"The Legacy 2.0.0 on http://{host}:{port}/", flush=True)
    print("  Start it with the Field and ai-gate: python boot_v2.py (Field on 8085, ai-gate on 8092, Legacy on 8080)",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
