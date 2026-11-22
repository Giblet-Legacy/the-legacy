# The Legacy 2.1.0

A layer over 2.0.0. `legacy_v2_1.py` serves
`static/projection_v2_1.html` at `/` and inherits the existing routes
and write guard. `boot_v2_1.py` uses the 2.0.0 supervisor to start the
new entry point. The frozen 2.0.0 files remain unchanged.

The page introduces the dashboard and its main views in plain English.
Home, Ask, Create and Field remain visible; Ledger and System are in
the Advanced navigation. Claim and face details remain accessible in a
collapsed Advanced section on Ask. Existing view links and keyboard
shortcuts continue to work. Ask explains that the local action stays
local, while Explain with AI and Report send the question and context
to Gemini. Drafts are not signed or committed by saving them.

## Document control

- **2.1.0:** frozen 2026-11-22 on James's instruction.
