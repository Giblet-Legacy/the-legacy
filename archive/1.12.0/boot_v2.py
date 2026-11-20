"""
boot_v2.py — start the Field (v6), then The Legacy (v8), and keep both running

Function:
    boot.py (SPEC_V8.md §2) with SCP Substrate serve_v6.py as the Field,
    so dependency claims are drawn as your own links (SCP SPEC_V6.md).
    Everything else (order, waits, exponential cool-off, Ctrl-C) is
    boot.py's. boot.py is committed and not edited; this sets its Field
    script for this process only, then runs its main.

    python boot_v2.py [--host 127.0.0.1] [--port 8080] [--field-port 8085]

Public API:
    1. main(argv=None) -> int

Tier:     Tier 1 — Consumer (The Connector)
Depends:  boot.py (SPEC_V8.md), ../scp-substrate/serve_v6.py
Spec:     SPEC_V9.md 1.5.0
Version:  1.5.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import boot as _v1  # noqa: E402

FIELD_SCRIPT = os.path.abspath(os.path.join(_HERE, "..", "scp-substrate", "serve_v6.py"))


# ---------------------------------------------------------------------------
# 1. main
# ---------------------------------------------------------------------------
def main(argv=None):
    _v1.FIELD_SCRIPT = FIELD_SCRIPT
    return _v1.main(argv)


if __name__ == "__main__":
    sys.exit(main())
