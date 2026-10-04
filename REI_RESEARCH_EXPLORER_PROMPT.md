# Build a First Version of an REI Research Explorer

Act as an expert in reproductive endocrinology and infertility (REI), genomics, scientific visualization, and web development. Create a complete, runnable first version of the application described below.

## Purpose and audience

The user is an REI physician completing a fellowship. Their research subject is still developing. Help them explore reproductive research topics, review publications and genomic evidence, and develop candidate research questions.

Support starting from a broad interest, condition, biological process, gene, variant, or chromosome region. Example interests include ovarian aging, PCOS, endometriosis, and primary ovarian insufficiency. Keep exploration open beyond genetics when the available evidence supports other directions.

Prioritize this workflow: search a topic, inspect evidence, compare candidate questions, and save a question with references and notes.

For each saved candidate question, provide an editable research brief with population, exposure/intervention, outcome, proposed study design, required data, and feasibility uncertainties. Let the fellow optionally specify a deadline, available datasets, and mentor expertise. Mark unknown details explicitly; do not invent access, sample size, feasibility, or novelty.

## Compact, intuitive UI

- Create a calm, Apple-inspired interface with warm white backgrounds, pale gray surfaces, muted blue or sage accents, readable dark text, subtle borders, and restrained rounded corners. Keep text and controls comfortably sized.
- Use minimal navigation: **Search**, **Saved research**, and **Help**. Give the main search field visual priority.
- Offer a few example searches, recent searches, and relevant suggestions. Show an editable interpretation of the query, such as `Human · Topic: ovarian aging`.
- Put data-source selection and advanced filters in a compact **Sources & filters** popover. Use a multi-select or checkboxes, with **Recommended sources** as the default. Describe each source by its research purpose. Preserve and display user overrides.
- Group results by useful evidence types, including publications, genes, and associations. Show concise summaries with expandable evidence and source links.
- Open details in a side panel without losing the search context. Provide contextual actions such as **Save**, **Explain**, and **Compare questions**.
- Keep AI assistance contextual and collapsible. Show small connection and source-status indicators with actionable errors.
- Provide keyboard navigation, visible focus, sufficient contrast, responsive layouts, and reduced-motion support. Make tips available through keyboard focus and touch.

## Public data sources

Implement these initial sources using their current documented APIs:

- [PubMed through NCBI E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/): relevant publications and available abstracts.
- [Ensembl REST](https://rest.ensembl.org/documentation/info/overlap_region): gene lookup and genomic features, including transcripts and locations where available.
- [GWAS Catalog](https://www.ebi.ac.uk/gwas/docs/programmatic-access/rest-api/): reported genetic associations, study information, and trait context.

Use a small source-adapter interface so additional sources can be added easily. Consider [UCSC](https://genome.ucsc.edu/goldenpath/help/api.html) for sequence and genomic tracks, and [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/intro/) for submitted variant classifications, as later extensions. Only offer implemented sources as selectable integrations.

Choose relevant sources for each search and explain those choices briefly. Show partial results when a source is unavailable. Distinguish failed retrieval from a successful search with no matches. Include input validation, request limits, timeouts, basic caching, and sensible retry behavior.

Show which sources were searched, the exact query used for each, total matches where available, retrieved counts, limits, and whether coverage is partial. A limited search must not support a claim that no published research exists on a topic.

## Scientific accuracy and evidence

Start human genomic exploration with GRCh38. Display organism, assembly, coordinate convention, source/version when available, and retrieval date. Normalize coordinates correctly and identify assembly mismatches before combining genomic records.

Keep publication findings, reported associations, variant classifications, and AI interpretations clearly identifiable. Preserve conflicting evidence and relevant study context. Make supporting citations accessible beside each finding.

Display study design, human versus animal evidence, population, and sample size when available. Distinguish association from causation and flag available corrections, retractions, and expressions of concern using PubMed's linked notices. Mark missing information as unknown.

## Optional Three.js 3D views

Use ordinary tables and 2D views for routine browsing. Implement a Three.js view when a named research task benefits from spatial exploration and suitable data is available. Otherwise, defer 3D while preserving an extension point. When implemented, provide rotation, zoom, selection, tooltips, and a clear return to results.

Load Three.js when the view is opened. Label schematic layouts explicitly; representations of physical genome structure require appropriate spatial data. Provide an equivalent readable view if 3D rendering is unavailable.

## Python backend and OpenAI integration

Provide a small Python backend, preferably FastAPI, for AI assistance and API proxying where required.

- Integrate the requested **GPT-6.1 Sol** model through the OpenAI Responses API and official Python SDK. Set `OPENAI_MODEL=gpt-6.1-sol` by default and make it configurable. Follow the [official model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol). Report unavailable-model errors clearly and require an explicit configuration change before using another model.
- Read `OPENAI_API_KEY` from a server environment variable or a local, Git-ignored `.env` file. Provide `.env.example` with placeholders. Keep keys out of HTML, browser storage, responses, logs, and committed files, following [official authentication guidance](https://developers.openai.com/api/reference/overview#authentication).
- Provide compact AI status and connection-check controls accessible from Help/settings. Explain missing credentials, insufficient API access, rate limits, and connectivity errors in plain language.
- Support **Explain this finding**, evidence summaries, and comparison of saved candidate questions. Suggest questions with a rationale, supporting references, uncertainties, and the data and methods needed to investigate them.
- Ground responses in retrieved evidence and cite actual source records. Treat novelty and research-gap claims as provisional until verified. Clearly identify when only abstracts or limited metadata were available.
- Make AI requests user-initiated, with progress feedback, cancellation, and bounded request sizes. Preserve ordinary browsing and saved work when AI is unavailable.

## Standalone frontend and saved research

Deliver one HTML frontend containing its CSS and JavaScript, with no build step, served over local HTTP. Document and pin external library versions. Explain internet requirements and any CDN dependencies.

Keep Python optional for AI. Browser-only mode must support sources verified to allow direct browser access; clearly indicate sources that need a backend proxy. Handle CORS requirements explicitly. Provide clearly labeled example data for trying the interface when live services are unavailable.

Persist saved questions, references, and notes locally across reloads. Support editing, deletion, and export/import of the research workspace in JSON, plus a concise Markdown export for review with a fellowship mentor.

Preserve an audit trail with original queries, filters, exact source queries, identifiers, retrieval dates, source versions when available, and the evidence supplied to AI. Record model and prompt versions alongside generated advice and exported briefs. Keep stored content within applicable reuse permissions.

## Help, README, and deliverables

Keep documentation concise and task-focused. Make all documentation reachable through a searchable **Help** panel, including a quick start, examples, source descriptions, glossary, AI setup, 3D guidance, troubleshooting, and technical reference. Use short, dismissible contextual tips for unfamiliar features.

Deliver the complete frontend, Python backend, dependency file, `.env.example`, appropriate `.gitignore`, and a concise but explicit `README.md`.

The README should include prerequisites, tested installation/startup commands, the local URL, browser-only operation, backend setup, API-key and model configuration, a short usage example, and common fixes. Explain OpenAI API access and metered usage. Link to Help for longer explanations. Aim for roughly 400 words, without omitting necessary setup steps.

## Commercial use and licensing

Design for potential commercial use. Follow [the commercial licensing notes](COMMERCIAL_LICENSING.md), verify the licenses of pinned dependencies and bundled assets, and record source-specific data terms. Preserve required license texts, copyright notices, attribution, and modification notices in `THIRD_PARTY_NOTICES.md` and distributions.

Use the owner's selected license for original project code; until selected, clearly mark project licensing as pending. Third-party permissions do not establish the project's own license. OpenAI API use has separate service terms and usage charges.

Make licensing documentation available through **Help → Licences**. Make the NCBI copyright and disclaimer notice evident in source details and Help for PubMed and other NCBI integrations. Include source terms and attribution in relevant exports. Check permissions for caching, AI processing, display, and redistribution; public API access alone does not establish those rights. Do not classify all PubMed content as public domain or all GWAS data as CC0.

## Verification and completion

Verify a topic search, a gene search such as BRCA1, source inspection, the optional 3D view, saving and restoring a research question, export/import, and an AI explanation with citations when credentials are available.

For the core acceptance example, start with ovarian aging, produce or manually draft a source-supported candidate question, identify its feasibility uncertainties, and export a brief for mentor review. Verify that the application does not invent supporting references, study feasibility, or novelty. Test a 3D view only if the research-use criterion justified implementing one.

Check keyboard use, a narrow screen, empty results, one failed source, missing credentials, and unavailable backend behavior. Run checks appropriate to the implementation and report what was verified, what needs live credentials, and any remaining limitations. Label example data and untested integrations clearly.

A first-time REI fellow should be able to search, understand the supporting evidence, and save a candidate research question without reading documentation.

Provide working code and clear startup instructions. Keep the first version focused on this complete research workflow.
