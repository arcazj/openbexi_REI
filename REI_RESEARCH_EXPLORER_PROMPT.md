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
- Keep the implemented data sources always visible as a compact, sticky row of labeled checkboxes. Use soft source-specific colors, a per-source result limit, and a reset control. Describe each source in Help and preserve user choices. Display the draft, AI suggestion, and audit-export buttons above completed results; keep them visible below the source row while scrolling.
- Group results by useful evidence types, including publications, genes, and associations. Show concise summaries with expandable evidence and source links.
- Open details in a side panel without losing the search context. Provide contextual actions such as **Save**, **Explain**, and **Compare questions**.
- Keep AI assistance contextual and collapsible. Make connection status prominent in the header and a compact panel. Show connected status only after a successful key/model-access check; prompt for a key when missing and provide actionable errors. Use restrained silver highlights with soft sage, blue, and lavender accents while preserving readable contrast.
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
- Read `OPENAI_API_KEY` from a server environment variable or a local, Git-ignored `.env` file. Provide `.env.example` with placeholders. Allow key entry in a password field that sends it only to the local backend, clears immediately after submission or dialog dismissal, and saves it in ignored `.env` without a restart. Restrict key configuration to loopback network clients and approved local HTTP origins. Never embed keys in HTML source or retain them in browser storage, responses, logs, exports, or committed files, following [official authentication guidance](https://developers.openai.com/api/reference/overview#authentication).
- Provide prominent AI status and key-entry controls, plus connection help. Automatically verify configured key/model access without sending research evidence or generating text. Distinguish this check from generation permissions and quota. Explain missing credentials, insufficient API access, rate limits, and connectivity errors in plain language.
- Support **Explain this finding**, evidence summaries, and comparison of saved candidate questions. Suggest questions with a rationale, supporting references, uncertainties, and the data and methods needed to investigate them.
- Ground responses in retrieved evidence and cite actual source records. Treat novelty and research-gap claims as provisional until verified. Clearly identify when only abstracts or limited metadata were available.
- Generate compact contextual guidance after user-initiated completed live searches when AI is verified, with progress feedback, cancellation, and bounded request sizes. Allow automatic guidance to be turned off in AI settings. Longer Explain, Suggest research directions, and Compare analyses remain explicitly initiated. Preserve ordinary browsing and saved work when AI is unavailable.

## V1.0 compact redesign and intelligent guidance

- Remove the full-width AI connection banner and its repeated heading/subtitle. Keep one compact header status labeled **AI connected to GPT-6.1 Sol · key verified.** only after actual key/model-access verification. Place **AI settings** on the right. When disconnected, show an actionable Connect AI status. On mobile, shorten the label and reveal full model details on tap.
- Move selectable sources above search and retain their sticky visibility. Use soft silver, sage, blue, and lavender with readable contrast; reduce padding, repeated labels, and oversized panels. Keep longer explanations in searchable Help.
- Show one primary research action per stage: Search initially and Suggest research directions after results. Put draft and export actions in More actions. Keep controls usable with keyboard, touch, and narrow screens.
- Under **Make the next step useful** and **Tip**, use the configured GPT-6.1 Sol model for one next step and one tip, each at most two short sentences. Ground them in the current query, selected-source coverage, retrieved evidence, research constraints, and stage inferred from up to three saved questions.
- Make guidance actionable: apply a refined query, review/save a proposed research question, and add a next-step note to a saved or new brief. Provide **Why this suggestion?** with supporting source links and model/date. Preserve the evidence and generation audit with saved suggestions.
- Generate guidance after a completed live search, reuse it until the research context changes, and provide Refresh suggestions. Do not send a request for every keystroke. Discard stale/canceled responses. Reserve compact guidance space during loading, report failures with labeled fallback guidance, and preserve search results and saved work. Never treat illustrative examples as AI evidence.
- Release **V1.0**, using frontend/backend version `1.0.0` and Git tag `v1.0.0`. Update the concise README, Help, changelog, and GitHub Pages demo. Publish reviewed release notes and downloadable browser/local packages that exclude credentials and private workspace files.

## Standalone frontend and saved research

Deliver one HTML frontend containing its CSS and JavaScript, with no build step, served over local HTTP. Document and pin external library versions. Explain internet requirements and any CDN dependencies.

Keep Python optional for basic browsing; AI uses the Python backend. The standalone HTML, served over local HTTP, should automatically connect to the local backend on port 8000 and use its server-side key. Allow a custom backend URL in Help, preserving it without automatic fallback. Support the standalone launcher's alternate HTTP loopback ports; exclude remote and file/null origins from local backend access. Browser-only mode must support sources verified to allow direct browser access; clearly indicate sources that need a backend proxy. Provide clearly labeled example data for trying the interface when live services are unavailable.

Publish a GitHub Pages browser demo linked prominently from the README. Deploy an explicit allowlist of HTML, help documents, and licence notices. Hosted mode must avoid backend/localhost probes and key entry, explain that AI/GWAS require the local version, and load documentation correctly under the repository URL prefix. Publish updates automatically from `master`.

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
