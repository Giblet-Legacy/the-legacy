"""
test_legacy_v8_at_v2.py — test_legacy_v8.py carried into The Legacy 2.0.0 (CONSOLIDATION_V2.md §3.2, §8)

Function:
    The tests of the frozen test_legacy_v8.py that describe 1.12.0, run against
    legacy_v2 / boot_v2: the old module names are imported as aliases of
    them, and every kept test is otherwise as frozen. Tests that describe
    behaviour 1.12.0 replaced are left out; a cut inside a kept test says
    what replaced it. The original is byte-identical in
    archive/1.12.0/test_legacy_v8.py. Its own header follows.

test_legacy_v8.py — The Legacy v8 (boot together, cool off, refresh, buffer) test suite

Function:
    Executable expression of SPEC_V8.md. Written before legacy_v8.py and
    boot.py and run red first.

Functions in this file (pytest-collected):
    1. test_backoff
    2. test_supervisor_order_and_restarts
    3. test_server_buffer
    4. test_page
    5. test_boot_end_to_end

Helpers:
    6. FakeProc  — a process that is alive until told otherwise
    7. _free_port
    8. _req

Tier:     Tier 1 — Consumer (The Connector)
Spec:     SPEC_V8.md 1.4.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import boot_v2 as boot  # noqa: E402
import legacy_v2 as legacy_v8  # noqa: E402


# 6. FakeProc
class FakeProc:
    def __init__(self, name):
        self.name, self.code, self.stopped = name, None, False

    def poll(self):
        return self.code

    def terminate(self):
        self.stopped, self.code = True, 0

    def wait(self, timeout=None):
        return self.code


# 7. _free_port
def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# 8. _req
def _req(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


# 1. test_backoff
def test_backoff():
    assert [boot.backoff(n, 1, 60) for n in range(1, 9)] == [1, 2, 4, 8, 16, 32, 60, 60]
    assert boot.backoff(1, 0.25, 4) == 0.25 and boot.backoff(5, 0.25, 4) == 4


# 2. test_supervisor_order_and_restarts
def test_supervisor_order_and_restarts():
    clock = {"t": 0.0}
    started, slept = [], []
    procs = {}

    def start(service):
        p = FakeProc(service.name)
        started.append(service.name)
        procs.setdefault(service.name, []).append(p)
        return p

    sup = boot.Supervisor(
        [boot.Service("field", ["x"], lambda: True), boot.Service("legacy", ["y"], lambda: True)],
        start=start, sleep=lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)),
        now=lambda: clock["t"], log=lambda msg: None)
    sup.start_all()
    assert started == ["field", "legacy"]
    procs["legacy"][-1].code = 1            # The Legacy dies twice quickly
    sup.check()
    procs["legacy"][-1].code = 1
    sup.check()
    assert started == ["field", "legacy", "legacy", "legacy"] and slept[-2:] == [1, 2]
    clock["t"] += 61                        # up for over a minute: the count resets
    sup.check()
    procs["legacy"][-1].code = 1
    sup.check()
    assert slept[-1] == 1
    sup.stop()
    assert procs["legacy"][-1].stopped and procs["field"][-1].stopped


# 3. test_server_buffer
def test_server_buffer():
    legacy_v8._BUFFER.clear()
    good = {"available": True, "status": {"n": 1}}
    out = legacy_v8.buffered("/api/cockpit", good)
    assert out["available"] and "fetched_at" in out and "stale" not in out
    bad = {"available": False, "error": "database is locked"}
    out = legacy_v8.buffered("/api/cockpit", bad)
    assert out["status"] == {"n": 1} and out["stale"] is True and out["stale_error"] == "database is locked"
    assert out["stale_since"] == legacy_v8._BUFFER["/api/cockpit"]["fetched_at"]
    assert legacy_v8.buffered("/api/lllm", bad) == bad  # nothing buffered yet



