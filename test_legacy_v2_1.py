"""Tests for the 2.1.0 dashboard layer."""

import threading
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import pytest

import boot_v2
import boot_v2_1
import legacy_v2_1


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    srv = legacy_v2_1.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()
    thread.join()


def test_new_page_and_head(server):
    with urllib.request.urlopen(server + "/") as response:
        page = response.read().decode("utf-8")
    assert "Welcome to The Legacy" in page
    assert "question and thread context" in page
    assert "saving does not sign or commit" in page.lower()
    with urllib.request.urlopen(urllib.request.Request(server + "/", method="HEAD")) as response:
        assert response.status == 200
        assert response.read() == b""

    class Navigation(HTMLParser):
        def __init__(self):
            super().__init__()
            self.depth = 0
            self.views = {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "details" and attrs.get("id") == "advanced-nav":
                self.depth += 1
            if tag == "a" and attrs.get("data-view"):
                self.views[attrs["data-view"]] = self.depth > 0

        def handle_endtag(self, tag):
            if tag == "details" and self.depth:
                self.depth -= 1

    nav = Navigation()
    nav.feed(page)
    assert nav.views == {"home": False, "ask": False, "create": False,
                         "field": False, "ledger": True, "system": True}


def test_existing_write_guard_is_preserved(server):
    request = urllib.request.Request(
        server + "/api/inbox", data=b"{}", headers={"Content-Type": "application/json"}
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request)
    assert error.value.code == 403


def test_boot_uses_new_entry_and_restores_frozen_module(monkeypatch):
    original = boot_v2.LEGACY_SCRIPT
    observed = []
    monkeypatch.setattr(boot_v2, "main", lambda argv: observed.append((boot_v2.LEGACY_SCRIPT, argv)) or 0)
    assert boot_v2_1.main(["--port", "8081"]) == 0
    assert observed[0][0].endswith("legacy_v2_1.py")
    assert observed[0][1] == ["--port", "8081"]
    assert boot_v2.LEGACY_SCRIPT == original


def test_frozen_release_is_discoverable():
    root = Path(__file__).parent
    version = [line.strip() for line in (root / "VERSION").read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.startswith("#")]
    assert version[-1] == "2.1.0"
    for name in ("boot_v2_1.py", "legacy_v2_1.py"):
        assert "Version:  2.1.0 (frozen 2026-11-22)" in (root / name).read_text(encoding="utf-8")
