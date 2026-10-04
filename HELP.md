# REI Research Explorer Help

## Quick start

Search a topic such as **ovarian aging** or **PCOS**, a human gene such as **BRCA1**, or a chromosome region such as `17:43044295-43170245`. Check the interpreted search type and change it if necessary. Open a finding to inspect its source, then start a research brief with the references you want to keep.

## Sources and coverage

**Recommended sources** selects relevant providers. Use **Sources & filters** to select providers yourself or limit the number of retrieved records.

- **PubMed:** publications and available abstracts.
- **Ensembl:** human genes, transcripts, and regions, using GRCh38.
- **GWAS Catalog:** reported trait and genetic associations.

Coverage reports the source query, match count when available, retrieved count, and failures or limits. A small result set is not proof that no research exists. Sources can use different search vocabularies; inspect their queries and original records.

## Reading evidence

Open source links to check findings. Study design, population, sample size, and human/animal context are shown when available; missing information remains unknown. Retractions, corrections, and expressions of concern are displayed when the source provides them. A reported association does not establish causation. Genome coordinates are displayed with their assembly and convention.

## Research briefs

Record a question, population, exposure/intervention, outcome, study design, required data, notes, and feasibility uncertainties. Optionally record your deadline, available datasets, and mentor expertise. Review access, sample size, methods, and time with your mentor; the application cannot establish these from publications alone.

Saved research stays in this browser on this device. Export JSON for backup and transfer. Import merges new brief IDs, preserves existing briefs, and restores supplied research constraints. Import only trusted workspace files. Export Markdown for mentor review, including references and search provenance. Clearing browser storage removes local saved work, so keep a backup.

## AI assistance

AI is optional and runs through the Python backend. Configure a local `.env` using `.env.example`, then restart the backend:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6.1-sol
```

Keys remain on the server. Never put a real key in the HTML, browser storage, exported research, or Git. OpenAI API usage is metered and requires access to the configured model.

Use **Explain**, question generation, or comparison when evidence is available. Suggestions should cite supplied records and identify uncertainty. A suggested gap or novel question is provisional. Exports preserve the evidence identifiers, model, and prompt version for review. Canceling a browser request may not stop a provider request that has already started.

## Demonstration and browser-only use

Demonstration mode is explicitly labeled and uses illustrative material. It is for learning the workflow, not research evidence or AI input. A live search failure never silently switches to demonstration mode.

The HTML works without the AI backend for sources that allow browser requests. If a source needs a proxy, start the Python backend. Browser-only mode does not enable AI. Documentation files can be opened from Help or directly beside `index.html`.

## 3D views

3D is deferred in the first version because the initial workflows do not supply validated spatial genome data or a task that benefits from 3D. A visualization extension point is reserved. Schematics must be labeled; physical structure claims need suitable spatial evidence.

## Troubleshooting

- **No findings:** inspect the search interpretation, exact source queries, and coverage; try a synonym or broader topic.
- **One source failed:** review the available results and retry later. Limits and timeouts are reported separately from empty results.
- **Backend unavailable:** check the backend URL and startup command in the README. Browse compatible sources or use the explicit demonstration.
- **AI unavailable:** check `.env`, restart the backend, and review connection/model access status. The key is never entered in the browser.
- **Saved work missing:** check the browser and device, then restore your JSON backup.

## Licences and project documentation

Read [commercial licensing notes](COMMERCIAL_LICENSING.md), [third-party notices](THIRD_PARTY_NOTICES.md), and the [NCBI copyright and disclaimer notice](https://www.ncbi.nlm.nih.gov/home/about/policies/). Publication text and datasets have source-specific reuse terms. The project's original-code license remains pending owner selection.

The [README](README.md) contains startup instructions. The [implementation prompt](REI_RESEARCH_EXPLORER_PROMPT.md) records the agreed scope and acceptance criteria.
