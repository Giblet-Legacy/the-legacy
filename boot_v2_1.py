"""
boot_v2_1.py — start the Field, ai-gate and The Legacy 2.1.0

Uses the frozen 2.0.0 supervisor with the 2.1.0 entry point.
Version:  2.1.0 (frozen 2026-11-22)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

import boot_v2


def main(argv=None):
    original = boot_v2.LEGACY_SCRIPT
    boot_v2.LEGACY_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legacy_v2_1.py")
    try:
        return boot_v2.main(argv)
    finally:
        boot_v2.LEGACY_SCRIPT = original


if __name__ == "__main__":
    sys.exit(main())
