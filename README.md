# REI Research Explorer · V1.0.1

A compact workspace for an REI fellow developing a research project: explore evidence, shape questions, and prepare briefs for mentor review.

**[Open the live demo →](https://arcazj.github.io/openbexi_REI/)**

[Download V1.0.1](https://github.com/arcazj/openbexi_REI/releases/tag/v1.0.1) · [Release notes](CHANGELOG.md)

The demo needs no installation or key. Search PubMed/Ensembl, try the labeled example workspace, and save/export manual briefs. AI and GWAS Catalog require the local Python version.

## Install on Windows

**[Download the Windows installer](https://github.com/arcazj/openbexi_REI/releases/download/v1.0.1/REIResearchExplorer-1.0.1-Windows-x64-Setup.exe)** for Windows 10/11, 64-bit. Run Setup, then launch **REI Research Explorer** from the Start menu or desktop. Python and dependencies are included; administrator access is not required. The app opens in your default browser. Use its tray menu to reopen or quit it. Enter your own API key through **Connect AI** when needed.

Private settings survive updates/uninstall. This installer is unsigned; Windows may show an unknown-publisher warning. See [Windows installation help](WINDOWS_INSTALLATION.md) for troubleshooting, private-data locations, and build instructions.

## Run locally

Requirements: Python 3.9+, a modern browser, and internet for live sources. The HTML has no build step.

From the project folder in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` for installation/startup.

Browser-only alternative: `py -3 serve_frontend.py`. Open the printed HTTP URL, normally **http://127.0.0.1:8765**. The launcher selects another port if needed; `--port 0` requests an available port. This standalone page automatically connects to a running backend on port 8000. Set another address in **Help → AI & connection**. Double-clicking `index.html` does not enable local AI.

## Research workflow

1. Select sources above search. Try **ovarian aging**, **PCOS**, **BRCA1**, or a GRCh38 region.
2. Inspect findings, original sources, and search coverage.
3. Use **Suggest research directions**, or **More actions → Draft a research question**.
4. Review feasibility with your mentor. Save a brief; export JSON for backup or Markdown for review.

Saved work stays in this browser. Exports preserve search and AI provenance. Illustrative examples are excluded from scientific evidence and AI input. Three.js views remain deferred until a useful spatial task and suitable data are available.

## Connect AI

Click **Connect AI**, then **Save key & connect**. The backend saves the key in ignored `.env` and verifies model access without restarting. The compact status shows the verified model; **AI settings** is on the right.

Alternatively, copy `.env.example` to `.env`, configure the following, and restart:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6.1-sol
```

After a completed live search, AI supplies one next step and one tip from retrieved evidence, constraints, and up to three saved questions. **Why this suggestion?** shows supporting sources. Apply a refined query, review/save a proposed question, or add a next step to a brief. Guidance is reused for the same context; **Refresh suggestions** requests new text. Turn automatic guidance off in **AI settings** for manual refresh.

API usage is metered and needs model access and generation quota. Keys stay on the backend; keep them out of HTML, browser storage, exports, and Git. `.env.example` is public. AI failures show labeled fallback guidance and preserve saved work.

## Help, licences, and checks

Searchable **Help** includes all documentation. See [Help](HELP.md), [implementation prompt](REI_RESEARCH_EXPLORER_PROMPT.md), [commercial terms](COMMERCIAL_LICENSING.md), and [third-party notices](THIRD_PARTY_NOTICES.md). Original-code licensing remains pending owner selection.

Run `python -m unittest discover -s tests -v` with the virtual environment. Optional browser checks: `npm ci`, `npx playwright install chromium`, then `npm run test:ui`. These development tools are not needed to run the HTML. CI checks Python 3.9/3.12 and desktop/mobile behavior. For failures, inspect coverage or AI settings. Back up research before clearing browser storage.
