# Service Analysis: SMART Procurement Calculator

- Latest analysis date: 2026-10-02 (Asia/Seoul)
- Initial analysis date: 2026-10-01; its dated verification evidence is retained below.
- Repository: `wisdom_procurement`
- Reviewed Git HEAD: `e5ac3d10ddf22edbe1199b7736981f21d049f644`
- Reviewed state: the current working tree, including existing uncommitted backend, frontend, basis document, and server script changes.
- Language: English, as explicitly requested by the product owner.

> Publication scope, 2026-10-02: Git synchronization discovered that `origin/main` at `abcecdfc725e22d118d8dc67b0f2f4d4343749ff` contains 20 commits after the reviewed local HEAD. This report describes the older local working tree identified above. Its findings have not been revalidated against that newer implementation and must not be treated as current remote-runtime conclusions. Publication preserves the newer remote code and documentation; rebaseline the report and remediation plan before using them to change that implementation.

## Executive Assessment

The service is a local administration portal for a single procurement practitioner. It organizes corporations, projects, and procurement documents, then extracts qualification requirements, required documents, limitations, and dates for human review.

The current implementation is a Phase 1 prototype with some basis document summary functionality. Phase 1 is incomplete because persistent storage, OCR, and full corporation/project CRUD are missing from the active application. Phase 2 is incomplete because basis document versioning, chunking, metadata, and vector indexing are absent.

The primary value is reducing document review effort while preserving project context. The 2026-10-02 two-round review additionally confirmed shared-transaction interference, unsafe process selection, file/database inconsistency, stale document results in the UI, permissive cross-origin access, and misleading failure states. Operational use requires these defects to be repaired before additional analysis features are introduced. The current accepted findings and their verification limits are recorded in the [two-round review](#two-round-code-and-service-review-2026-10-02); the [remediation plan](superpowers/plans/2026-10-02-code-remediation.md) is proposed work, not implemented behavior.

## Service Purpose and User Workflow

The intended user is one administrator working on a single local PC. Authentication is intentionally outside Phase 1 scope.

The main workflow is:

1. Register a corporation with its industry, region, certifications, size, and internal notes.
2. Create a project linked to that corporation.
3. Upload a PDF or DOCX to the project, with document type and revision notes.
4. Explicitly run document analysis.
5. Review qualification requirements, required documents, limitations, dates, and additional checkpoints.
6. Reanalyze when necessary.
7. Separately register and summarize basis PDFs for reuse across projects.

When direct production certificate terminology appears in an analysis, the frontend displays selected items from the latest basis document summary in the corresponding category.

Corporation information is stored and linked to projects, but the active summarization path does not compare it with procurement requirements. The service does not implement a final eligibility decision, procurement crawler, or scoring/calculation engine.

## Implemented Capabilities and Phase Alignment

| Capability | Current implementation | Assessment |
| --- | --- | --- |
| Dashboard | Corporation, project, and document counts | Basic Phase 1 functionality |
| Corporation management | Creation, listing, and client-side search | Active application lacks update and delete routes/UI |
| Project management | Creation, listing, corporation linkage, and client-side search | Active application lacks full CRUD and project detail workflow |
| Project documents | PDF/DOCX upload, metadata, listing, search, status filtering, and backend deletion | Core domain relationship is present; deletion UI is absent |
| Document parsing | PDF text extraction and DOCX paragraph extraction | OCR and DOCX table extraction are missing |
| Document analysis | Qualification-focused JSON and Markdown, cache, and forced reanalysis | Synthetic fallback happy path works; schema validity, factual accuracy, failures and cache identity are not assured |
| Basis documents | Separate tables and storage, local PDF path registration, summaries, and reanalysis | Partial functionality; not the required Phase 2 ingestion pipeline |
| Basis versions and retrieval | Latest document selected by category | No explicit version, effective-date, item-specific retrieval, or citation metadata |
| Chunking and indexing | No active implementation found | Required Phase 2 work remains |
| Final judgment and crawler | No active implementation found | Consistent with phase restrictions |

General documents belong to projects. Basis documents are reusable assets without project ownership. Extension allowlists restrict general documents to PDF/DOCX and basis documents to PDF; actual content, resource limits and extraction quality are not validated adequately. No manual chunking interface was found. The basis import API registers a pending source; the UI makes a separate analysis request. Only the configured startup bootstrap imports and analyzes automatically, and neither path implements the required complete Phase 2 pipeline.

## Actual Architecture

| Layer | Active implementation | Documented design |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite, React Router, manual `fetch`, and component state | Also describes TanStack Query and more domain-oriented layers |
| Backend | Flask and Flask-CORS in `backend/app/main.py` | FastAPI, SQLAlchemy, and Pydantic |
| Database | Shared in-memory SQLite connection | Persistent SQLite |
| File storage | Local filesystem under `storage/uploads` and `storage/basis` | Local filesystem |
| Parsing | `pypdf` and `python-docx` | PDF/DOCX parsing with OCR |
| AI | External OpenAI call when configured; deterministic fallback otherwise | External LLM summaries with structured output |
| Basis processing | Extract text and summarize | Extract, OCR, normalize, chunk, embed, and index |

The server manager starts the backend with `python -m app.main`. Its active Flask entry point does not import the legacy FastAPI router, ORM models, service layer, or pipeline modules. Those files exist, but their behavior is not the behavior of the running application. Current requirements also describe the Flask runtime.

API routing, SQL, parsing, summarization, caching, and basis processing are concentrated in `backend/app/main.py`. Frontend pages similarly own forms, data fetching, and presentation directly. The frontend/backend separation is intact, but the internal separation required by the architecture guardrails is incomplete.

## Findings and Recommended Priorities

### 1. Critical: Business records are not persisted

`MEMORY_DB_URI` uses SQLite memory mode. A fresh process with the same storage directory initializes an empty database. Corporation, project, document metadata, and analysis records disappear when the backend process ends, although uploaded files remain on disk.

This was reproduced in an isolated probe: counts changed from one corporation, one project, and one document to zero for all three in the fresh process. Restore persistent database storage and verify retention across restarts before treating the portal as an operational record system.

### 2. High: A tracked file contains an API credential-shaped value

`gpt api.txt` is tracked by Git and contains a project API key-shaped string. The value was not reproduced in this report, and its validity was not tested.

If it is a real credential, revoke and replace it, move credentials to environment configuration, and address the tracked file and repository history. Analysis documentation must never include credential values.

### 3. High: Extraction gaps can be reported as completed analysis

DOCX extraction reads paragraphs only. An isolated DOCX containing a unique table-cell marker lost that marker during extraction.

A blank PDF was accepted and analyzed with HTTP 200, `analysis_status=completed`, and `ocr_status=skipped`, despite having no extractable text. The legacy OCR module contains only an integration placeholder and is not used by the active Flask path.

Implement DOCX table extraction and an actual OCR path. Distinguish insufficient extraction, OCR required, processing, failure, and successful analysis so users can assess coverage.

### 4. High: Basis summaries are not matched to the applicable item or clause

The analysis screen detects direct production keywords, loads the latest basis document for a fixed category, and selects the first item from several requirement lists. It does not match detailed product names, applicable sections, versions, or effective dates.

The resulting risk of displaying requirements for another product is an inference from the selection logic; applicability accuracy was not evaluated against real procurement cases. Retain the phase boundary and implement the required versioned basis ingestion and metadata before introducing retrieval-based judgment. Current summary references should clearly express their scope and limitations.

### 5. High: Cache, version, and deletion semantics are incomplete

- Analysis cache lookup uses document ID and extracted-text hash, without prompt version or model configuration. Changing the prompt version reused an older analysis in the probe.
- Basis import identifies duplicates by original filename and category. Importing a different PDF with the same filename/category returned the original document ID and title, preventing a new version from being registered.
- Deleting a project document left its analysis records behind. Two orphan analysis rows remained in the probe, and SQLite foreign-key enforcement was disabled.

Use explicit cache identities, traceable basis versions/content identities, and deliberate database/file deletion rules. Preserve previous results safely during reprocessing.

### 6. Medium: Failure visibility and processing UX are incomplete

AI exceptions fall back to deterministic summaries without recording the exception reason. Analysis records are marked completed, with an empty error message. The analysis page labels a fallback source, but several list and form paths rely on console errors or unhandled promise rejection instead of actionable user feedback.

Analysis runs synchronously inside the request. There is no persisted processing job or stage progress, and some action buttons allow repeated requests while processing. These gaps matter even with a single administrator.

### 7. Medium: Long documents and source context are truncated

External summarization sends only the first 120,000 characters. Basis fallback processing considers at most 600 unique lines. PDF pages are flattened into a string, without retaining page/section context in analysis output.

Later requirements can be omitted, and the service cannot yet provide traceable citations. Introduce coverage reporting and the planned pipelines within the applicable phase.

### 8. Medium: Documentation and runtime behavior disagree

README and design documents describe FastAPI, persistent SQLite, OCR, and full CRUD beyond the active implementation. Legacy modules may make completed work appear more extensive than it is.

Choose and document the supported runtime, align startup instructions and dependencies, then separate API, repository, service, and pipeline responsibilities. Keep the local single-PC assumption unless the product owner explicitly approves a change.

## Verification Evidence

These checks were performed on 2026-10-01 during the preceding service analysis in this conversation. They used temporary files and an isolated Python process with external AI calls and basis bootstrap disabled. Existing servers and production data were not used.

| Check | Observed result |
| --- | --- |
| Corporation creation -> project creation -> DOCX upload -> analysis -> latest result | Passed with deterministic fallback |
| Repeated analysis of unchanged text | Reused existing analysis |
| Forced reanalysis | Created a new analysis record |
| Prompt version changed with unchanged text | Reused older cached analysis |
| DOCX table-cell extraction | Table marker absent |
| Blank PDF analysis | HTTP 200, completed, OCR skipped |
| Same filename/category basis import with different content | Existing ID and title reused |
| Document deletion after two analyses | Two orphan analysis records remained |
| SQLite foreign-key enforcement | Disabled |
| Active corporation/project PATCH endpoints | HTTP 404 |
| Fresh process with the same file storage | All dashboard record counts reset to zero; PDF files remained |
| Frontend `tsc --noEmit --incremental false` | Exit code 0 |

At this initial 2026-10-01 checkpoint, external AI calls, actual OCR, browser interaction, real procurement applicability, full frontend bundling, and concurrency behavior were not verified. The 2026-10-02 review below adds synthetic concurrency and component-source evidence. The existing smoke script checks a blank-PDF happy path; it does not establish extraction quality or restart persistence.

No application fixes were made as part of the analysis or this report publication.

## Recommended Delivery Sequence

1. Preserve any still-live in-memory records before a future restart; address the tracked credential-shaped value through its owner.
2. Establish enforceable offline test configuration and verified process ownership. Keep tests away from the live server and storage.
3. Repair durable transactions, recoverable file operations, local Origin/Host boundaries, bounded parsing, extraction coverage and truthful processing attempts. Contain unsupported basis assertions and replacement regressions early.
4. Repair model validation/cache provenance and frontend identity/error handling, then complete Phase 1 CRUD and source inspection. Retain Flask while separating active responsibilities.
5. After Phase 1 acceptance, complete Phase 2 automatic basis ingestion: extraction -> OCR -> normalization -> chunking -> metadata -> indexing, with traceable versions and safe publication.
6. Introduce crawler, corporation-to-requirement matching, final judgment and evidence rendering only within Phase 3. The detailed task dependencies and release gates are in the English remediation plan.

## Questions for Product Owner

- Is the added basis summary interface an intentional interim feature, or should delivery strictly complete Phase 1 before Phase 2 work?
- Which basis categories, detailed product identifiers, versions, and effective dates must be managed?
- What representative PDF/DOCX corpus and quality criteria should define extraction and summary acceptance?
- Is analysis export required, and what operational backup/restore workflow is expected?

These questions are unresolved product decisions, not prerequisites for saving or reusing this report. The existing local, single-administrator, no-authentication assumption remains in effect.

## Source Map

- [Repository instructions](../AGENTS.md)
- [Project overview](../README.md)
- [Technical design](technical-design.md)
- [UX design](ux-design.md)
- [Work log](work-log.md)
- [Active backend](../backend/app/main.py)
- [Backend requirements](../backend/requirements.txt)
- [Legacy analysis service](../backend/app/services/analysis_service.py)
- [Legacy OCR placeholder](../backend/app/pipelines/ocr.py)
- [Frontend routes](../frontend/src/app/App.tsx)
- [Frontend API client](../frontend/src/app/api.ts)
- [Analysis screen](../frontend/src/pages/AnalysisPage.tsx)
- [Basis document screen](../frontend/src/pages/BasisDocumentsPage.tsx)
- [Document screen](../frontend/src/pages/DocumentsPage.tsx)
- [Server manager](../scripts/manage-servers.ps1)
- [Smoke script](../scripts/smoke-test.ps1)

## Reuse and Maintenance

For future service analysis requests, read this file first as the saved baseline. Compare it with current instructions, design documents, source code, dependencies, and working-tree changes. Revalidate affected findings rather than presenting this snapshot as current truth.

Update this same English Markdown file after each analysis, recording the analysis date, reviewed revision/working-tree scope, evidence, verification limitations, priority findings, and unresolved product questions. Preserve dated historical verification evidence. Mark resolved findings with supporting evidence, and replace stale conclusions with current supported conclusions. Distinguish planned behavior from implementation and executed verification. Keep secrets and personal document content out of the report.

## Two-Round Code and Service Review: 2026-10-02

### Scope and Source Baseline

This review covers all 53 first-party application/configuration/script files in the baseline inventory below: 32 backend Python files, 11 frontend source files, two Windows scripts and eight configuration/dependency files. It also covers repository instructions, README, all five pre-existing project documents, dependency-lock metadata, tracked generated-artifact metadata and selected installed dependency implementations. Third-party dependencies were not exhaustively audited; generated assets and personal stored documents were not treated as source code or opened for content review.

The source baseline is HEAD `e5ac3d10ddf22edbe1199b7736981f21d049f644` plus the existing working tree. Before this review, uncommitted source changes already existed in `backend/app/main.py`, `frontend/src/app/{App.tsx,api.ts,types.ts}`, `frontend/src/pages/AnalysisPage.tsx`, both Windows scripts and `frontend/tsconfig.tsbuildinfo`; `frontend/src/pages/BasisDocumentsPage.tsx` and basis storage were untracked. Existing instruction/documentation changes also predated this review. Findings therefore describe the working tree, not HEAD alone. The initial SHA-256 of the active backend was `7431c342c777f14c2bb7659a26293f0daf6c05d1b47ec8cda0d115ac366a7024`; a 53-file hash manifest was captured for final change verification.

The user requested review and an English remediation plan, followed by a halt before code changes. Review work used temporary synthetic fixtures, test clients, extracted function bodies, mocked component hooks and mocked PowerShell operating-system calls. It did not execute the live server-management or smoke scripts, terminate processes, inspect real environment secrets, call an external model, contact a network share or modify application source.

### Parallel Review and Main-Session Decisions

Three subagents completed two rounds, with perspectives rotated for the second round:

| Reviewer | Round 1 | Round 2 |
| --- | --- | --- |
| `review_backend` | Backend/domain/parser/model contracts | Security, Windows operations and priority assumptions |
| `review_frontend` | Frontend behavior and administrator workflow | Backend API, transaction, file and result-publication contracts |
| `review_operations` | Startup, dependencies, security and documentation | Product interpretation, frontend integration and phase boundaries |

The main session independently checked the cited source, reran relevant synthetic probes and decided whether to accept, narrow or reject the criticisms. Repeated criticisms are consolidated into the finding groups below. Round 2 added recoverable file/database coordination, provider-upgrade and degraded-result promotion defects, and strengthened startup, phase-containment and attribution acceptance criteria.

Accepted criticisms are evidence-backed risks or explicit delivery gaps. They do not establish P0 compromise, valid credentials, real-world procurement correctness or full browser acceptance. Keeping the last successful result after failed reanalysis is desirable; hiding the failed attempt is the defect. A corrupt PDF upload returning 201 can legitimately mean that its source was stored; its subsequent unhandled processing failure is the defect. Mandatory framework migration, authentication and distributed workers were rejected as remediation prerequisites.

### Accepted Finding Ledger

P1 means a demonstrated data-integrity/operational hazard or an exposed high-impact boundary requiring repair before operational reliance. P2 means a functional/reliability defect or a separately identified roadmap gap. P3 means lower-priority usability/accessibility work. No P0 finding is established. “Synthetic” means isolated execution against generated data or mocked collaborators; “source” means a main-session code inspection rather than end-to-end acceptance.

| ID | Priority | Finding and evidence | Main verification / limit | Plan tasks |
| --- | --- | --- | --- | --- |
| R01 | P1 | Business metadata and analyses disappear on process exit. `main.py:30,117,129` uses a shared memory database. | Fresh synthetic process: all record counts zero, original files still present. | T03, T15 |
| R02 | P1, conditional | Git tracks an API credential-shaped value in `gpt api.txt`. | Earlier content inspection retained; no value reproduced or validity tested. Owner revocation depends on whether it is real. | Preflight, T15 |
| R03 | P1 | Concurrent requests share one SQLite connection/transaction. `main.py:117-123`. | Paused valid create plus invalid SQL-binding request rolled back the valid request; both failed. Exact duplicate-ID symptom from the agent was not independently reproduced. | T03, T06 |
| R04 | P1 | Server stop force-kills candidates from saved PIDs, port owners or a workspace substring. `manage-servers.ps1:133-175`. | Mocked actual functions selected stale PID, foreign listener and unrelated workspace Python. No real process killed. | T02 |
| R05 | P1 | Smoke testing replaces/stops the normal servers, writes to normal storage and can use configured bootstrap/AI. `smoke-test.ps1:38-74`. | Source inspection; script deliberately not executed. This compounds R01/R04. | T01, T02, T15 |
| R06 | P1 | Wildcard CORS and forced JSON parsing admit arbitrary-origin reads and simple text/plain mutations. `main.py:115,820,855,1014`. | Test client reflected an untrusted Origin on GET and accepted text/plain JSON POST with 201. Actual browser permission to reach localhost and DNS rebinding were not tested. | T05 |
| R07 | P1 | DOCX tables are omitted and text-empty PDFs are reported completed/OCR skipped. `main.py:237-245,534-536`. | Synthetic table marker absent; blank PDF returned 200 completed. Mixed scanned/readable real documents and OCR accuracy untested. | T07 |
| R08 | P1 | File and DB halves of upload/delete are not recoverable together. `main.py:914-941,962-967`. | Injected INSERT failure: zero rows/one file; injected DELETE failure: row retained/source removed. With FK enforcement enabled on an analyzed fixture, the natural FK error also occurred after source unlink. | T03, T04 |
| R09 | P1 | Analysis UI can attribute a previous or late result to a newer route. `AnalysisPage.tsx:110-140`. | Actual component source with mocked hooks: route document 2 retained/displayed document 1 after both failed load and late response. Real browser not exercised. | T09 |
| R10 | P1 | Installed/pinned `pypdf==5.9.0` is affected by published parser denial-of-service advisories. `requirements.txt:4`, `main.py:239`. | Installed version and reachable reader/extraction calls verified; primary advisories checked. No harmful PDF or exploit executed. | T05, T07 |
| R11 | P2 | Processing exceptions leave pending/old completed status; failed forced model calls silently promote fallback over the prior model result. `main.py:479-540,716-773`. | Corrupt PDF: non-JSON 500/pending. Failed reanalysis: old completed result. Synthetic model failure: new completed fallback became latest. | T06, T08, T09 |
| R12 | P2 | JSON object mode plus permissive normalizers accepts incomplete model output as completed. `main.py:316-349,471,593-625`. | Fake local SDK returned `{}`; API completed with normalized empty fields/lists. No real provider behavior tested. Shape validation does not prove factual accuracy. | T08 |
| R13 | P2 | Cache ignores prompt/parser/model/requested-provider changes and blocks fallback-to-model upgrade. `main.py:491-492,726-729`. | Prompt change reused old result; enabling a synthetic provider reused fallback with zero provider calls. | T08 |
| R14 | P2 | Document deletion leaves analyses, and in-flight analysis can publish after deletion. `main.py:513-536,955-967`. | Two existing orphan analyses; delayed analysis after delete created another orphan. FK alone is not a safe repair; see R08. | T04, T06 |
| R15 | P2 | Request values are not validated reliably. `main.py:818-871,891-909,1012-1027`. | Array/null/nonnumeric payloads produced non-JSON 500; empty corporation name accepted; corporation ID 1.9 truncated to 1. | T05 |
| R16 | P2 | Extensions are the main file check; size/page/time limits and pre-access local-path policy are missing. `main.py:237,552-558,891-916`. | Source confirms unrestricted resources and `Path.exists()` before suffix checks. UNC/mapped-drive network or authentication behavior not executed. | T05, T07 |
| R17 | P2 | Same filename/category hides changed basis content instead of creating a version. `main.py:562-572`. | Two different synthetic PDFs returned the original ID/title. | T10, T12 |
| R18 | P2 | A newer pending basis document masks the previously usable category result. `main.py:1055-1077`. | Category latest returned pending newest document with null analysis. | T10, T12 |
| R19 | P2 | Every free-form basis category is summarized as direct-production criteria. `main.py:664-675,700`; `BasisDocumentsPage.tsx:109-117`. | Arbitrary category synthetic fallback had the direct-production topic; model prompt is statically fixed to it. | T10, T12 |
| R20 | P2 | The issuance panel presents first-list items as applicable without item/version/effective-date matching, and hides scope/uncertainty. `AnalysisPage.tsx:177-183,310-364`. | Selection and omitted fields confirmed by source/component harness. Wrong-product applicability is a supported risk inference, not tested procurement accuracy. | T10 |
| R21 | P2 | Source coverage is lost/truncated and dated required-document lines can be omitted. `main.py:299-309,467,475,661,704,712`. | Dated submission fixture was absent from required documents; source shows 120,000-character model prefix, 600-line basis cap and flattened PDF pages. Reported input length counts unsent text. | T07, T08, T13 |
| R22 | P2 | Failed reads look empty, mutation failures lack useful feedback, repeat submits remain possible, and partial basis import is hidden after analysis failure. | Source harness confirmed dashboard zeros, uncaught reanalysis failure, two create calls and imported basis omitted from list. File state cleared while native input remained uncontrolled; visual browser symptom untested. | T09 |
| R23 | P2, delivery gap | Phase 1 edit/delete/detail/source workflows are incomplete; saved certification/notes and document attribution are inaccessible in the relevant UI. | Active routes/UI inspected; legacy CRUD is dormant. General summary and original/extracted-source inspection are missing, not proof of stored-data loss. | T11 |
| R24 | P2 | Resolver singleton returns first character; status probes wrong backend port; session overrides are discarded; startup has unbounded/weak readiness and no failure cleanup. | Mocked resolvers returned `C`; status displayed 19001 while probing default 18111. Source/installed Vite confirm missing strictPort and generic 200 check; curl has no deadline. Failure cleanup not executed live. | T01, T02 |
| R25 | P2 | Configured basis bootstrap runs analysis before listening and accumulates fresh stored copies after restarts. `main.py:230,780-795`. | Two synthetic fresh processes left two copies; actual configured model could incur latency/cost, but no paid call made. | T01, T06, T12 |
| R26 | P2 | README/design/setup claims overstate runtime, persistence, OCR and schema guarantees; absolute links and personal-path defaults are nonportable. | Active Flask runtime and current documentation compared. Uvicorn/legacy dependencies are not the supported current entry point. | T15 |
| R27 | P2 | Generated basis files and SQLite journal/WAL/SHM patterns are not adequately ignored; three journal artifacts are tracked. | Git index/ignore metadata inspected. No secret or journal content leakage established; local files must not be automatically purged. | T15 |
| R28 | P3 | Search/status controls lack explicit names, async messages lack announcement semantics, and a small-text brand color has insufficient calculated contrast against white. | CSS/source only: `#d95a8a` versus white 3.633:1; `#c64678` 4.617:1. Focus styles exist and native controls remain keyboard-capable. Rendered contrast/a11y tree untested. | T14 |

### Dependency and External Evidence

The following primary advisories affect `pypdf==5.9.0`. The newest fix floor among these three is 6.18.1; this is a floor for these known issues, not a complete vulnerability scan or a guarantee that any future chosen release is safe. Recheck advisories and compatibility when implementing the upgrade.

| Advisory | Published / fixed version | Relevant operation |
| --- | --- | --- |
| [GHSA-2rw7-x74f-jg35 / CVE-2026-27628](https://github.com/py-pdf/pypdf/security/advisories/GHSA-2rw7-x74f-jg35) | 2026-02-22 / 6.7.2 | Circular cross-reference traversal while reading a PDF |
| [GHSA-763m-79hh-57f2 / CVE-2026-84311](https://github.com/py-pdf/pypdf/security/advisories/GHSA-763m-79hh-57f2) | 2026-08-14 / 6.16.1 | Repeated XObject processing during text extraction |
| [GHSA-g9cg-prrw-2r8q / CVE-2026-102996](https://github.com/py-pdf/pypdf/security/advisories/GHSA-g9cg-prrw-2r8q) | 2026-09-11 / 6.18.1 | Excessive font-width processing during text extraction |

The installed OpenAI SDK defaults were inspected locally: 600-second request timeout, 5-second connect timeout and two retries. The active application sets no explicit total deadline. These are installed-version observations, not a timed real-provider test.

`Start-Process -UseNewEnvironment` does not inherit arbitrary caller-session overrides; explicit child configuration is necessary for offline smoke isolation. Scope defaults differ by PowerShell/runtime version, so this review does not claim every Windows User-scope variable is removed. See [Microsoft Start-Process documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process?view=powershell-7.5). The installed `python-dotenv==1.1.1` implementation has no `PYTHON_DOTENV_DISABLED` shortcut and the application calls implicit `load_dotenv()`.

Calculated normal-text contrast is compared with the 4.5:1 threshold in [WCAG 2.2 contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). This supports the color concern; it does not replace rendered gradient, disabled-state or full accessibility verification.

### Executed Verification and Limits

| Verification | Result |
| --- | --- |
| All 32 backend Python files parsed with `ast.parse` | Passed; syntax only |
| Frontend TypeScript `tsc --noEmit --incremental false` | Exit 0; no emitted build or browser acceptance |
| Isolated Flask test-client workflow | Fallback create/project/upload/analyze/cache/reanalyze path passed |
| Main synthetic DB/concurrency/extraction/API probes | Reproduced the defects described in R01/R03/R06-R19/R21/R25 |
| Actual frontend source executed with mocked hook/API collaborators | Reproduced R09 and the listed R20/R22 omissions/states |
| PowerShell AST-extracted functions with OS calls mocked | Reproduced unsafe candidate selection, singleton resolver and saved-port mismatch |
| Round 2 actual upload/delete/analysis function bodies with temporary SQLite/files/provider stubs | Reproduced DB/file failure split, FK deletion loss, fallback cache lock-in and degraded promotion |
| Local dependency/source inspection and primary advisory review | Confirmed the narrowly stated version/default/source claims |

No comprehensive automated suite exists in the reviewed repository. These checks are diagnostic probes, not a production acceptance suite. No live restart/stop, full Vite bundle, actual DOM/browser flow, real OCR, paid model, personal document corpus, HTTP-load concurrency test, destructive parser exploit, network-share access or restore test was run. Model schema and confidence notes cannot establish complete or correct procurement interpretation. The final 53-file SHA-256 comparison found zero changed application/configuration/script files. Local documentation links and English-only/secret-pattern checks passed; review additions consist of this report, the plan, README navigation and the work-log entry.

### Product and Delivery Decisions

The service is currently a document-review workbench. The name does not imply an implemented calculator, eligibility engine or authoritative certificate determination. Auth, crawling and final judgment remain intentionally excluded from Phase 1. Missing Phase 2 version/chunk/index functionality is an implementation gap, separate from the demonstrated Phase 1 defects.

Preserve the active Flask runtime during stabilization. Add per-request SQLite transactions and small active repository/service/pipeline seams without activating incompatible dormant FastAPI/ORM code. Persisted attempts can initially accompany bounded synchronous requests; a distributed queue is unnecessary. Aborting frontend fetch protects UI state but does not itself cancel backend/model work.

Preserve last usable results and published basis versions when reprocessing fails. A fallback preview needs explicit degraded provenance and must not silently replace a successful requested-provider result. Suppress the current unmatched issuance assertion early; independently labeled basis-library inspection remains possible without Phase 3 matching or judgments.

### Questions for Product Owner Added by This Review

- Which still-live records, stored originals and analysis history need preservation before the first future restart? Existing APIs do not expose all historical analysis rows; already-lost metadata cannot be recovered merely by introducing persistence.
- Are network/mapped-drive basis sources intentional? The proposed default is local-volume input, with any network exception explicitly configured by the owner before filesystem access.
- What representative Korean text/scanned/mixed PDF and DOCX fixtures, including tables and dated submission requirements, define extraction and summarization quality acceptance?
- Should a requested-model failure expose an optional fallback preview? The proposed default preserves the previous usable result and never promotes that preview silently.
- What backup retention and supported category/version/effective-date taxonomy should be adopted? The plan supplies conservative implementation defaults pending revised product decisions.

These questions do not block publication of the review or plan. Implementation remains unexecuted at the user's instruction.

### Baseline Source Inventory

```text
backend/app/ (32 .py files)
  __init__.py
  api/__init__.py, api/router.py
  api/routes/__init__.py, analyses.py, corporations.py, dashboard.py, documents.py, projects.py
  core/__init__.py, core/config.py
  db/__init__.py, db/base.py, db/init_db.py, db/session.py
  main.py
  models/__init__.py, analysis.py, corporation.py, document.py, project.py
  pipelines/__init__.py, ocr.py, parser.py, summarizer.py
  schemas/__init__.py, analysis.py, corporation.py, document.py, project.py
  services/__init__.py, analysis_service.py
frontend/src/ (11 files)
  app/App.tsx, app/api.ts, app/types.ts, main.tsx, styles.css
  pages/AnalysisPage.tsx, BasisDocumentsPage.tsx, CorporationsPage.tsx,
        DashboardPage.tsx, DocumentsPage.tsx, ProjectsPage.tsx
scripts/ (2 files)
  manage-servers.ps1, smoke-test.ps1
configuration/dependencies (8 files)
  .gitignore, backend/.env.example, backend/requirements.txt,
  frontend/.env.example, frontend/index.html, frontend/package.json,
  frontend/tsconfig.json, frontend/vite.config.ts
```
