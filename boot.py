"""
boot.py — start the Field, then The Legacy, and keep both running

Function:
    SPEC_V8.md §2. Starts SCP Substrate (serve_v5.py) and waits until it
    answers, then starts The Legacy (legacy_v8.py) pointed at it and
    waits for that too. Supervises both: a child that exits is restarted
    after an exponential cool-off (1 s, 2 s, 4 s … 60 s), and the count
    resets once it has stayed up for a minute. Ctrl-C stops both.

    python boot.py [--host 127.0.0.1] [--port 8080] [--field-port 8085]

Public API:
    1. backoff(attempt, base, cap) -> float
    2. Service(name, cmd, ready, env=None)
    3. Supervisor(services, start, sleep, now, log)  — start_all, check, stop
    4. main(argv=None) -> int

Internal helpers:
    5. _http_up — any HTTP answer from a URL
    6. _tcp_up  — a port accepting connections
    7. _popen   — start a child process
    8. _log     — "[boot HH:MM:SS] …"

Tier:     Tier 1 — Consumer (The Connector)
Depends:  legacy_v8.py, ../scp-substrate/serve_v5.py; standard library
Spec:     SPEC_V8.md 1.4.0
Version:  1.4.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
FIELD_SCRIPT = os.path.abspath(os.path.join(_HERE, "..", "scp-substrate", "serve_v5.py"))
LEGACY_SCRIPT = os.path.join(_HERE, "legacy_v8.py")
READY_WAIT = 60.0
STABLE_AFTER = 60.0


# ---------------------------------------------------------------------------
# 1. backoff
#    SPEC_V8 §1: min(cap, base × 2^(attempt − 1)).
# ---------------------------------------------------------------------------
def backoff(attempt, base, cap):
    return min(cap, base * 2 ** (max(1, attempt) - 1))


# ---------------------------------------------------------------------------
# 8. _log
# ---------------------------------------------------------------------------
def _log(msg):
    print(f"[boot {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 5. _http_up / 6. _tcp_up
# ---------------------------------------------------------------------------
def _http_up(url):
    def ready():
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except urllib.error.HTTPError:
            return True  # it answered
        except (urllib.error.URLError, OSError, ValueError):
            return False
    return ready


def _tcp_up(host, port):
    def ready():
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False
    return ready


# ---------------------------------------------------------------------------
# 7. _popen
# ---------------------------------------------------------------------------
def _popen(service):
    return subprocess.Popen(service.cmd, env=service.env)


# ---------------------------------------------------------------------------
# 2. Service
# ---------------------------------------------------------------------------
class Service:
    """One child: its command, how to tell it is up, and its run state."""

    # 2a. __init__
    def __init__(self, name, cmd, ready, env=None, url=None):
        self.name, self.cmd, self.ready, self.env, self.url = name, cmd, ready, env, url
        self.proc, self.started_at, self.failures = None, 0.0, 0


# ---------------------------------------------------------------------------
# 3. Supervisor
#    SPEC_V8 §2 steps 1–5. Clock, sleep and process start are injected.
# ---------------------------------------------------------------------------
class Supervisor:
    """Starts services in order, restarts any that exit, stops them in reverse."""

    # 3a. __init__
    def __init__(self, services, start=_popen, sleep=time.sleep, now=time.monotonic, log=_log):
        self.services, self._start, self._sleep, self._now, self._log = services, start, sleep, now, log

    # 3b. _launch — start one service and wait (with cool-off) until it is up.
    def _launch(self, s):
        s.proc, s.started_at = self._start(s), self._now()
        waited, n = 0.0, 0
        while not s.ready():
            if s.proc.poll() is not None or waited >= READY_WAIT:
                self._log(f"{s.name} did not come up")
                if s.proc.poll() is None:
                    s.proc.terminate()
                return False
            n += 1
            pause = backoff(n, 0.25, 4)
            self._sleep(pause)
            waited += pause
        pid = getattr(s.proc, "pid", "?")
        self._log(f"{s.name} up" + (f" on {s.url}" if s.url else "") + f" (pid {pid})")
        return True

    # 3c. start_all — in order: each waits for the one before.
    def start_all(self):
        for s in self.services:
            self._launch(s)

    # 3d. check — restart any child that has exited, after the cool-off.
    def check(self):
        for s in self.services:
            if s.proc is None or s.proc.poll() is None:
                continue
            if self._now() - s.started_at >= STABLE_AFTER:
                s.failures = 0
            s.failures += 1
            pause = backoff(s.failures, 1, 60)
            self._log(f"{s.name} stopped (exit {s.proc.poll()}); restarting in {pause:g} s")
            self._sleep(pause)
            self._launch(s)

    # 3e. stop — in reverse order.
    def stop(self):
        for s in reversed(self.services):
            if s.proc is not None and s.proc.poll() is None:
                s.proc.terminate()
                try:
                    s.proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    s.proc.kill()
            self._log(f"{s.name} stopped")


# ---------------------------------------------------------------------------
# 4. main
# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="Start the Field, then The Legacy, and keep both running.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080, help="The Legacy's port (default 8080)")
    p.add_argument("--field-port", type=int, default=8085, help="the Field's port (default 8085)")
    args = p.parse_args(argv)
    field_url = f"http://127.0.0.1:{args.field_port}/"
    env = dict(os.environ, FORGE_FIELD_URL=field_url, PYTHONUNBUFFERED="1")
    field = Service("field", [sys.executable, FIELD_SCRIPT, "--port", str(args.field_port), "--quiet"],
                    _http_up(field_url + "api/health"), env, field_url)
    legacy = Service("legacy", [sys.executable, LEGACY_SCRIPT, "--host", args.host, "--port", str(args.port)],
                     _tcp_up(args.host, args.port), env, f"http://{args.host}:{args.port}/")
    sup = Supervisor([field, legacy])
    _log(f"FORGE_HOME={os.environ.get('FORGE_HOME') or os.path.join(os.path.expanduser('~'), '.forge')}")
    try:
        sup.start_all()
        _log(f"open {legacy.url} - Ctrl-C stops both")
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
