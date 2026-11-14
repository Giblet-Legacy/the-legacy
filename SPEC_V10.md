# SPEC V10 — the-legacy (v9: the page on a phone, boot_v3)

SPEC_V10.md — specification for legacy_v9.py, static/projection_v9.html and boot_v3.py.

Function:
    James (2026-11-14) asked for screenshots and a report, then said yes
    to fixing what they found. The report said the v8 page ran off the
    right edge of a phone; that came from the screenshot (headless Edge
    will not make a window narrower than about 500 px, so the 412 px
    shot was a 496 px page cut short). Measured in a true 412 px frame
    the cards fit, but the Claims and Ledger tables did not read: the
    hash columns (ID, Hash, Prev) never wrap, so they took the width and
    squeezed the claim and entry text to three or four letters a line
    ("appro / ve", "throu / gh"). v9 serves projection_v9.html, which
    gives the text the width on a phone; boot_v3 starts the Field v7 (SCP SPEC_V7.md, the field on a
    phone) and The Legacy v9. Where this document is silent, SPEC_V8.md
    applies. legacy.py, legacy_v2–v8, boot.py, boot_v2.py and their
    pages are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v8.py and boot.py (SPEC_V8 1.4.0), SCP Substrate serve_v7 (7.0.0)
Version:   SPEC V10 1.6.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. legacy_v9.py

v8's server; `/` serves `static/projection_v9.html`. Every route,
buffer and flag is v8's.

## 2. projection_v9.html

v8's page with:

- at 560 px and narrower: the Claims table hides its ID column and the
  Ledger table its Hash and Prev columns (all still shown on wider
  screens, and in `/api/claims` and `/api/chain`), and a long subject
  may wrap;
- grid columns that never grow past their share (`minmax(0, 1fr)`), so
  a card can never be pushed wider than the screen;
- hints that name `python boot_v3.py` and `serve_v7.py`.

## 3. boot_v3.py

`python boot_v3.py [--host H] [--port N] [--field-port N]` does exactly
what boot.py does (SPEC_V8 §2) with serve_v7.py as the Field and
legacy_v9.py as The Legacy.

## 4. Tests (test_legacy_v9.py)

- `/` serves projection_v9.html; the page names boot_v3.py and serve_v7.py.
- boot_v3 starts serve_v7.py (quiet), then legacy_v9.py.
- In a headless browser (Edge or Chrome; skipped if neither is
  installed), in a 412 × 915 frame, with claims and ledger entries
  loaded: every claim and entry text cell is at least 150 px wide, and
  no visible element ends past the right edge unless it is inside a box
  that scrolls sideways.

---

## Document control

- **SPEC V10 1.6.0** — 2026-11-14, by the VS Code AI on James's
  delegation ("take a bunch of screenshots and report", then "yes" to
  the fixes).
