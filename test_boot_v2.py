"""
test_boot_v2.py — boot_v2 (the Field v6) test

Function:
    SPEC_V9.md: boot_v2 starts serve_v6.py (quiet), then legacy_v8.py.
    The supervisor is replaced so nothing real starts.

Functions in this file (pytest-collected):
    1. test_boot_v2_starts_field_v6_first

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V9.md 1.5.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot  # noqa: E402
import boot_v2  # noqa: E402


# 1. test_boot_v2_starts_field_v6_first
def test_boot_v2_starts_field_v6_first(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(s.cmd for s in services)

        def start_all(self):
            raise KeyboardInterrupt  # stop straight away

        def stop(self):
            pass

    monkeypatch.setattr(boot, "Supervisor", Sup)
    old = boot.FIELD_SCRIPT
    try:
        assert boot_v2.main(["--port", "1", "--field-port", "2"]) == 0
    finally:
        boot.FIELD_SCRIPT = old
    field, legacy = seen
    assert field[1].endswith(os.path.join("scp-substrate", "serve_v6.py")) and field[2:] == ["--port", "2", "--quiet"]
    assert legacy[1].endswith("legacy_v8.py")
