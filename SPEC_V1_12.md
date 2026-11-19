# SPEC V1.12 — the-legacy (legacy_v1_12 + boot_v1_12: the AI on the page, through the gate)

SPEC_V1_12.md — specification for legacy_v1_12.py, boot_v1_12.py and static/projection_v1_12.html.

Function:
    James, 2026-11-19: "now lets integrate the ai into our interface".
    The Legacy 1.11.0 gains an "Ask the AI" card. The Legacy still never
    calls a model and never signs: it relays to ai-gate's local API
    (ai-gate SPEC §12), which is the only process that talks to Gemini.
    Where this document is silent, SPEC_V1_11.md applies. legacy.py,
    legacy_v2–v12, legacy_v1_11, boot.py, boot_v2–v7, boot_v1_11 and
    their pages are not edited.

Tier:      Tier 1 — Consumer (The Connector)
Depends:   legacy_v1_11.py (1.11.0), ai-gate ai_gate_serve.py (0.1.0)
Version:   SPEC V1.12 1.12.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. The relay: `/api/ai/*`

The gate is at `FORGE_AI_GATE_URL` (default `http://127.0.0.1:8092`).

- **GET `/api/ai/<name>`** for `health`, `status`, `threads`, `thread`,
  `assumptions`, `assumption` and `score` is relayed to `/api/<name>`
  with its query string. Any other name gives 404 and is never relayed.
- **POST `/api/ai/ask`** and **`/api/ai/rate`** pass the Legacy v4 write
  guard first: a local host only, the `X-Forge-Legacy` header,
  `application/json`, and the size limit. They are then relayed with
  the gate's own header. Any other POST under `/api/ai/` gives 404.
  **There is no seal relay.**
- **Gate down:** a GET answers 200 with
  `{"error": "ai-gate is not running …", "offline": true}`, so the page
  can say so; a POST answers 503.
- Everything else (the inbox, nouns, the Field, the rest) is 1.11's.

## 2. The page: `static/projection_v1_12.html`

### 2.1 Views (James: "can we do something about the gui, its very busy now and not very fluid")

The 1.11 page was 13 cards in one scroll, with 9 refreshing all the time.
1.12 shows **one view at a time**, behind a **left sidebar** (a bottom bar
on a phone). Every 1.11 card is kept, and only the arrangement changes:

| View | Cards |
|---|---|
| 1 Home | **Needs you** (new), Metrics, Briefing |
| 2 Ask | Ask the AI |
| 3 Create | New, Echo |
| 4 Claims | Query, Faces, Claims |
| 5 Ledger | Ledger |
| 6 Field | the Field, full height |
| 7 System | Layers, Network, LLLM |

- **Needs you** lists drafts waiting to be committed and assumptions
  waiting for a HAL seal, each with its terminal command. "Nothing needs
  you right now" when clear. Home, Ask and Create carry badges.
- **Only the open view refreshes.** Health, the cockpit status and the
  drafts always refresh, because they feed the pills, the metrics and
  "Needs you". The claims, ledger, network, briefing and LLLM panels
  wait while hidden. The Field's iframe loads only when the Field view
  is first opened.
- Each view has an address (`#home` … `#system`), so the back button and
  bookmarks work. Keys 1-7 switch views (not while typing). The last
  view is remembered in this browser.
- **Ask:** threads down the left (each with counts and the AI's λ).
  Clicking a thread shows its earlier answers, and clicking one opens
  it. The scope picker shows only for a new thread. Ctrl+Enter asks.

### 2.2 The AI card

The 1.11 page with one card, **Ask the AI** (`id="ai-card"`):

- a **thread** (typed, or picked from the existing ones), a **scope**
  picked from P9's committed entities and subjects (needed for a new
  thread), and the **idea**;
- **the answer**, headed **ASSUMPTION · status · thread · model · id**:
  the text, what it builds on, every conflict it reports, and its open
  questions;
- **rate 1-5:** the AI's λ and tier are updated;
- **the seal command**, to run in the terminal
  (`python ai_gate.py seal <id> approve --lambda 1.0`). The page never
  seals;
- each thread's counts (pending, approved, refused) and the AI's λ;
- if the gate is not running, the card says so and Ask is disabled.

On the VPS the card is view-only. It has no gate and no Gemini key
there, and the guard refuses writes.

## 3. `boot_v1_12.py`

boot.py's Supervisor, with three services in order:

1. the Field (serve_v8);
2. **ai-gate** (`../ai-gate/ai_gate_serve.py --port <ai-port>`, default
   8092), only when that checkout exists. Without it the Legacy starts
   alone and says so;
3. the Legacy (`legacy_v1_12.py`), with `FORGE_AI_GATE_URL` set.

`GEMINI_API_KEY` and `FORGE_GEMINI_MODEL` come from James's environment,
and only the gate uses them.

## 4. Tests (test_legacy_v1_12.py)

- Reads are relayed from the allowlist only, with path tricks refused.
- Asks and ratings are relayed with the header, and refused (403) from
  a foreign host before reaching the gate.
- Seal and other posts are not relayed.
- Gate down: a GET says offline, and a POST gives 503.
- The inbox still works.
- The page has the card.
- boot_v1_12 starts the field, then ai-gate, then the legacy, with the
  gate's URL.
- Both files are marked 1.12.0-dev until frozen.

---

## Document control

- **SPEC V1.12 1.12.0** — 2026-11-19, by the VS Code AI on James's
  instruction. Not frozen.
