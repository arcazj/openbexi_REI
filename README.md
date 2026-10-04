# REI Research Explorer

A compact research workspace for an REI fellow developing a fellowship project: explore publications and genomic evidence, draft research questions, and export briefs for mentor review.

## Run locally

Requirements: Python 3.9 or newer, a modern browser, and internet access for live sources. The HTML frontend has no build step.

From the project folder, run these PowerShell commands:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. On macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` for installation and startup.

For browser-only operation without installing dependencies:

```powershell
py -3 serve_frontend.py
```

This serves the standalone HTML, documentation, and notices on **http://127.0.0.1:8765**. If that port is occupied or blocked, it prints an alternative; use --port 0 to let the OS choose. AI also works from this standalone page when the Python backend is running on port 8000: it connects automatically. For another backend address, use **Help → AI & connection**. Open the printed HTTP URL; double-clicking `index.html` does not enable local AI.

## Research workflow

1. Search **ovarian aging**, **PCOS**, **BRCA1**, or a GRCh38 region.
2. Review sources, evidence context, search coverage, and missing information.
3. Draft a question with population, exposure/intervention, outcome, study design, required data, and feasibility uncertainties.
4. Save references and notes. Export JSON for backup or Markdown for mentor review.

Saved research stays in this browser. Exports preserve queries, source identifiers, dates, and available AI provenance. Demonstration content is illustrative and excluded from AI evidence. Three.js views are deferred until suitable spatial data and a useful research task are available.

## Optional AI

Click **Enter API key** in the AI connection panel, then **Save key & connect**. The local backend saves the key in its private `.env` and checks model access. No restart is needed. A verified connection turns green; failures show an actionable message.

Alternatively, create `.env` from `.env.example`, set these values, and restart the backend:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6.1-sol
```

OpenAI API access is metered; your account must support the model and have generation quota. The password field clears after submission. Keep keys out of HTML source, browser storage, exports, and Git; `.env.example` is public. Browsing and manual briefs work without AI.

## Help and licences

In-app **Help** provides searchable tips and all documentation. See [Help](HELP.md), [the final implementation prompt](REI_RESEARCH_EXPLORER_PROMPT.md), [commercial-use terms](COMMERCIAL_LICENSING.md), and [third-party notices](THIRD_PARTY_NOTICES.md). The project's original-code license remains pending owner selection.

## Checks and troubleshooting

Run `python -m unittest discover -s tests -v` using the virtual environment's Python. CI checks the backend on Python 3.9 and 3.12.

Automated tests and browser checks cover live searches, saved briefs, exports, standalone backend connections, and mobile layouts. Live AI generation requires your key.

Sources stay visible while scrolling. Draft, AI suggestions, and audit export appear above completed results. For failures, inspect source coverage or the AI connection panel. Restart after manual `.env` edits. Back up research before clearing browser storage.
