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
py -3 serve_frontend.py --port 8000
```

This serves only the frontend, documentation, and notices. Some sources require the backend proxy; browser-only mode supports compatible sources and the explicit demonstration.

## Research workflow

1. Search **ovarian aging**, **PCOS**, **BRCA1**, or a GRCh38 region.
2. Review sources, evidence context, search coverage, and missing information.
3. Draft a question with population, exposure/intervention, outcome, study design, required data, and feasibility uncertainties.
4. Save references and notes. Export JSON for backup or Markdown for mentor review.

Saved research stays in this browser. Exports preserve queries, source identifiers, dates, and available AI provenance. Demonstration content is illustrative and excluded from AI evidence. Three.js views are deferred until suitable spatial data and a useful research task are available.

## Optional AI

Create a local `.env` from `.env.example`, set these server-side values, and restart the backend:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6.1-sol
```

Use Help/settings to check the connection. OpenAI API access is metered; your account must support the configured model. Never put a key in HTML, browser storage, exports, or Git. Basic browsing and manual briefs work without AI.

## Help and licences

In-app **Help** provides searchable tips and all documentation. See [Help](HELP.md), [the final implementation prompt](REI_RESEARCH_EXPLORER_PROMPT.md), [commercial-use terms](COMMERCIAL_LICENSING.md), and [third-party notices](THIRD_PARTY_NOTICES.md). The project's original-code license remains pending owner selection.

## Checks and troubleshooting

Run `python -m unittest discover -s tests -v` using the virtual environment's Python. CI checks the backend on Python 3.9 and 3.12.

Verified with 30 automated tests and browser checks of live searches, saved briefs, exports, and mobile layouts. Live AI generation requires your key.

If a source fails, inspect its coverage status and retry; an empty result is different from failed retrieval. If AI fails, check `.env`, model access, and connection status. Restart the backend after configuration changes. Back up saved work before clearing browser storage.
