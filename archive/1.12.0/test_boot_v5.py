"""
test_boot_v5.py — The Legacy boot_v5 (the Field v8) test suite

Function:
    Executable expression of SPEC_V12.md. Written before boot_v5.py and
    run red first.

Functions in this file (pytest-collected):
    1. test_boot_v5_order

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V12.md 1.8.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot  # noqa: E402
import boot_v5  # noqa: E402


# 1. test_boot_v5_order
def test_boot_v5_order(monkeypatch):
    seen = []

    class Sup:
        def __init__(self, services):
            seen.extend(s.cmd for s in services)

        def start_all(self):
            raise KeyboardInterrupt  # stop straight away

        def stop(self):
            pass

    monkeypatch.setattr(boot, "Supervisor", Sup)
    monkeypatch.setattr(boot, "FIELD_SCRIPT", boot.FIELD_SCRIPT)
    monkeypatch.setattr(boot, "LEGACY_SCRIPT", boot.LEGACY_SCRIPT)
    assert boot_v5.main(["--port", "1", "--field-port", "2"]) == 0
    field, legacy = seen
    assert field[1].endswith(os.path.join("scp-substrate", "serve_v8.py")) and field[2:] == ["--port", "2", "--quiet"]
    assert os.path.exists(field[1])
    assert legacy[1].endswith("legacy_v10.py")
