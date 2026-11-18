"""
boot_v1_11.py — start the Field (v8), then The Legacy (1.11.0: drafts through Cockpit v1.8), and keep both running

Function:
    boot.py (SPEC_V8.md §2) with SCP Substrate serve_v8.py as the Field
    and legacy_v1_11.py as The Legacy (SPEC_V1_11.md: drafts through Cockpit v1.8). FORGE_FIELD_PUBLIC_URL
    in the environment reaches the Legacy unchanged, so on the VPS the
    page shows the Field at /field/ on the same link. Everything else is
    boot.py's. boot.py and boot_v2–v7 are not edited; this sets boot.py's
    scripts for this process only, then runs its main.

    python boot_v1_11.py [--host 127.0.0.1] [--port 8080] [--field-port 8085]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  boot.py (SPEC_V8.md), legacy_v1_11.py, ../scp-substrate/serve_v8.py
Spec:     SPEC_V1_11.md 1.11.0
Version:  1.11.0 (frozen 2026-11-18)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import boot as _v1  # noqa: E402

FIELD_SCRIPT = os.path.abspath(os.path.join(_HERE, "..", "scp-substrate", "serve_v8.py"))
LEGACY_SCRIPT = os.path.join(_HERE, "legacy_v1_11.py")


# ---------------------------------------------------------------------------
# 1. main
# ---------------------------------------------------------------------------
def main(argv=None):
    _v1.FIELD_SCRIPT, _v1.LEGACY_SCRIPT = FIELD_SCRIPT, LEGACY_SCRIPT
    return _v1.main(argv)


if __name__ == "__main__":
    sys.exit(main())
