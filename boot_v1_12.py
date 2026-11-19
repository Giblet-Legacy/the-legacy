"""
boot_v1_12.py — start the Field, ai-gate's local API, then The Legacy 1.12.0, and keep them running

Function:
    SPEC_V1_12.md §3. boot.py's Supervisor with three services: the Field
    (SCP Substrate serve_v8.py), ai-gate (../ai-gate/ai_gate_serve.py,
    when that checkout exists) and The Legacy 1.12.0 (legacy_v1_12.py),
    which is told where the gate is (FORGE_AI_GATE_URL).
    FORGE_FIELD_PUBLIC_URL reaches the Legacy as before. GEMINI_API_KEY
    and FORGE_GEMINI_MODEL reach only the gate's environment, whatever
    it inherits. Without an ai-gate checkout (the VPS today), the Legacy
    starts without it, and its AI card says the gate is not running.
    boot.py and boot_v2-v7, boot_v1_11 are not edited.

    python boot_v1_12.py [--host 127.0.0.1] [--port 8080] [--field-port 8085] [--ai-port 8092]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  boot.py (SPEC_V8.md), legacy_v1_12.py, ../scp-substrate/serve_v8.py, ../ai-gate/ai_gate_serve.py
Spec:     SPEC_V1_12.md 1.12.0
Version:  1.12.0-dev
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import boot as _v1  # noqa: E402

FIELD_SCRIPT = os.path.abspath(os.path.join(_HERE, "..", "scp-substrate", "serve_v8.py"))
GATE_SCRIPT = os.path.abspath(os.path.join(_HERE, "..", "ai-gate", "ai_gate_serve.py"))
LEGACY_SCRIPT = os.path.join(_HERE, "legacy_v1_12.py")


# ---------------------------------------------------------------------------
# 1. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="Start the Field, ai-gate, then The Legacy 1.12.0, and keep them running.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080, help="The Legacy's port (default 8080)")
    p.add_argument("--field-port", type=int, default=8085, help="the Field's port (default 8085)")
    p.add_argument("--ai-port", type=int, default=8092, help="ai-gate's local API port (default 8092)")
    args = p.parse_args(argv)
    field_url = f"http://127.0.0.1:{args.field_port}/"
    gate_url = f"http://127.0.0.1:{args.ai_port}"
    env = dict(os.environ, FORGE_FIELD_URL=field_url, FORGE_AI_GATE_URL=gate_url, PYTHONUNBUFFERED="1")
    services = [_v1.Service("field", [sys.executable, FIELD_SCRIPT, "--port", str(args.field_port), "--quiet"],
                            _v1._http_up(field_url + "api/health"), env, field_url)]
    if os.path.exists(GATE_SCRIPT):
        services.append(_v1.Service("ai-gate", [sys.executable, GATE_SCRIPT, "--port", str(args.ai_port)],
                                    _v1._http_up(gate_url + "/api/health"), env, gate_url + "/"))
    else:
        _v1._log(f"no ai-gate checkout at {GATE_SCRIPT}: starting without it")
    legacy = _v1.Service("legacy", [sys.executable, LEGACY_SCRIPT, "--host", args.host, "--port", str(args.port)],
                         _v1._tcp_up(args.host, args.port), env, f"http://{args.host}:{args.port}/")
    services.append(legacy)
    sup = _v1.Supervisor(services)
    _v1._log(f"FORGE_HOME={os.environ.get('FORGE_HOME') or os.path.join(os.path.expanduser('~'), '.forge')}")
    try:
        sup.start_all()
        _v1._log(f"open {legacy.url} - Ctrl-C stops all three")
        while True:
            sup.check()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sup.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
