# SMART Procurement Code Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the validated operational, data-integrity and analysis defects, complete Phase 1 workflows, and deliver safe Phase 2 basis ingestion without introducing Phase 3 judgment.

**Architecture:** Keep the active Flask application and the separate React frontend. Move active database, file, analysis and ingestion responsibilities out of the monolithic entry point incrementally, using durable SQLite, request-scoped connections and persisted attempts around bounded local processing. Basis assets remain independent of projects and publish a new usable version only after the complete ingestion pipeline succeeds.

**Tech Stack:** Python 3.12, Flask, SQLite, pypdf, python-docx, local Tesseract/PDF rendering adapters, the existing OpenAI SDK, React/TypeScript/Vite/React Router and PowerShell. Proposed tests use Python unittest and Vitest/React Testing Library; Phase 2 uses embedded local Qdrant and CPU FastEmbed behind adapters. None of these changes or installations has been executed.

**Spec:** [Canonical service analysis and accepted findings R01-R28](../../service-analysis.md), [repository instructions](../../../AGENTS.md), [technical design](../../technical-design.md), [UX design](../../ux-design.md). When design claims disagree with runtime, the current review identifies the gap; this plan supplies the proposed behavior.

**Date and baseline:** 2026-10-02, Asia/Seoul. HEAD `e5ac3d10ddf22edbe1199b7736981f21d049f644` plus the reviewed existing working tree. Three reviewers completed two parallel critique rounds; the main session revalidated and narrowed their findings.

**Status:** Planning complete. Every implementation checkbox is intentionally unchecked. The user explicitly instructed the session to stop before code changes; this file is not authorization to implement.

> Publication scope, 2026-10-02: `origin/main` at `abcecdfc725e22d118d8dc67b0f2f4d4343749ff` is 20 commits newer than this plan's reviewed local baseline. Its documentation includes subsequent phases and different runtime/OCR choices. This plan is preserved as the review's baseline-specific proposal, not a current remote implementation mandate. Revalidate every affected finding and reconcile current architecture, requirements and completed work before executing it; do not overwrite the newer implementation with the old snapshot.

## Global Constraints

- Keep frontend and backend separated; keep design documentation under `docs/`.
- Verify the target Phase before implementation. Preserve local single-PC, single-administrator operation.
- Phase 1 has no login, crawler, final judgment engine or evidence-clause rendering. HWP remains excluded.
- General uploads support PDF/DOCX only and always belong to a project. Basis documents support PDF only and remain reusable assets outside projects.
- Phase 2 implements ingestion, versioning, OCR, normalization, chunking, metadata and local indexing; it does not determine qualification or match requirements to a corporation.
- Keep parsing, OCR, summarization, chunking and indexing as distinct active services/pipelines. Preserve injectable user context and extensible `source_type` seams without adding authentication or a crawler.
- Never create a manual chunking UX. Reprocessing preserves the prior usable result/index until replacement succeeds.
- Do not change application code during the current review turn. Do not restart live servers, delete stored files, call paid models or install dependencies as part of plan publication.
- Preserve pre-existing working-tree changes and historical review evidence. Stage only task-specific changes during future implementation; never use blanket `git add .`.
- Never print/store secret values. Do not reinstall Orca or its Claude/OpenCode status hooks.
- This plan and the canonical service-analysis report are English-only by explicit user instruction. Other core documentation retains the repository's Korean-first/English-section convention.

## Review Focus

- A live memory-backed instance contains the only copy of valuable metadata: preserve accessible records before any future restart; do not promise recovery of already-lost history. Preflight/T03/T15.
- Database failure or process interruption occurs between a file operation and metadata commit: recover both halves without deleting unrelated originals. T04/T15.
- Two requests or a late response target the same document, including deletion during analysis: isolate transactions, reject duplicate work, conditionally publish and bind UI output to the current identity. T03/T06/T09.
- A partially readable document or provider failure produces plausible empty output: expose coverage/failure/degradation and preserve the last usable result. T07/T08/T09.
- A pending/failed basis replacement or unfamiliar category looks authoritative: keep the published version, reject unsupported interpretation and suppress unmatched issuance assertions. T10/T12/T13.

## Delivery Milestones and Order

| Milestone | Tasks | Release gate |
| --- | --- | --- |
| A: Immediate containment | Preflight, T01, T02, T10 | Explicit offline mode, verified process ownership and no unsupported issuance assertions |
| B: Phase 1 stabilization | T03-T09, T14, T15 | Persistence, transaction/file recovery, local trust boundary, truthful extraction/attempts, provider provenance and correct UI identity all pass |
| C: Phase 1 completeness | T11, related T14/T15 checks | CRUD, dependency-aware deletion and source inspection pass |
| D: Phase 2 ingestion | T12-T13, related T14/T15 checks | Versioned automatic ingestion/index publication and failed-replacement recovery pass |

Execute T10's containment after T01/T02, before full CRUD expansion. Task numbers identify deliverables rather than impose a strict numerical order; dependencies below control execution. Complete Phase 1 acceptance before delivering the full Phase 2 milestone. Phase 3 is excluded from this plan.

## Proposed Defaults and Contracts

These are explicit planning defaults, not claims about existing behavior or previously approved product requirements. Product decisions may revise them before the corresponding task is implemented.

| Setting/policy | Proposed default |
| --- | --- |
| Runtime | Flask, loopback bind, one PC; no framework migration |
| Database | Existing `SQLITE_PATH`, default `backend/storage/app.db`; schema migrations tracked in SQLite |
| File/DB safety | Immutable stored originals; staged ingest and recoverable tombstone/trash deletion; no automatic purge of disconnected existing files |
| SQLite | Independent connection per request/worker operation, FK enforcement, 5-second busy timeout, short explicit transactions; WAL on local disk with supported backup API |
| Work admission | One active attempt per document/revision, at most two local processing slots; reserve/commit before processing, publish using a revision/attempt conditional update |
| Attempts | `pending`, `processing`, `succeeded`, `degraded`, `insufficient_text`, `failed`, `interrupted`, `superseded`; latest attempt separate from last usable result |
| Result quality | `usable` or `degraded`; `cache_hit` is retrieval provenance, not quality/status |
| Limits | 50 MiB upload, 500 PDF pages, 120-second extraction/OCR deadline, 512 MiB parser worker budget, 60-second total model deadline including at most one retry |
| Partial coverage | Empty or omitted pages/regions and truncated text explicitly reported; do not return an unqualified successful result for incomplete coverage |
| Model failure | Preserve prior usable result; optional fallback preview is a separately identified degraded result and does not promote itself over requested-model success |
| Network paths | Reject UNC/device/network-mapped sources before filesystem access by default; operator-approved exceptions require explicit policy/configuration |
| Corporation/project deletion | Return 409 while dependents exist; offer no implicit recursive cascade. Documents are removed individually through the recoverable deletion workflow |
| Basis categories | Initially process only `direct_production_certificate`; reject other analysis categories with a clear validation error until category-specific schemas exist |
| Basis publication | Explicit operator version/effective-date metadata; pending/failed candidates cannot replace the last published usable version |
| Backup | Consistent DB backup plus immutable original/derivative manifest, checksums, seven retained snapshots; no secret files in backups |

### Active File Boundaries

`backend/app/main.py` becomes a thin `create_app(config: RuntimeConfig | None = None) -> Flask` factory and CLI entry point. New `backend/app/runtime_config.py` owns validated configuration and explicit dotenv loading. New `backend/app/db/sqlite_runtime.py` owns connections/migrations/recovery. New `backend/app/models/runtime_records.py` defines typed records; new `backend/app/schemas/runtime_contracts.py` owns API/model validation; new `backend/app/api/flask_routes.py` registers active routes.

New repositories live in `backend/app/repositories/`: `corporations.py`, `projects.py`, `documents.py`, `analyses.py`, `basis.py`. New active services are `file_store.py`, `analysis_orchestrator.py`, `basis_ingestion.py`, `backup_service.py`. New pipelines are `extraction.py`, `ocr_adapter.py`, `normalization.py`, `summarization.py`, `chunking.py`, `embedding.py`, `indexing.py`. Existing dormant FastAPI/ORM files remain explicitly dormant until a separate retirement decision; do not import them just because they contain similarly named behavior.

Frontend shared infrastructure moves to `frontend/src/shared/api/client.ts` and `frontend/src/shared/ui/RequestState.tsx`; typed domain contracts stay in `frontend/src/app/types.ts`. Route-level pages stay under `pages/`; new mutation/analysis hooks live under `features/`, and document identity/coverage presentation under `entities/documents/`. Move only responsibilities touched by each task.

### Shared Backend Record Shapes

Define these dataclasses/validated DTOs in T01/T06/T07/T08 before callers use them:

- `RuntimeConfig`: environment, DB/storage/temp roots, allowed frontend origins/hosts, run identity, offline/bootstrap flags and the stated limits. Explicit injected config wins over dotenv; test/offline mode does not load project `.env`.
- `AttemptRecord`: id, domain, document_id, revision_id, requested_mode, status, stage, error_code, safe_error_message, started_at, finished_at.
- `ResultRecord`: id, attempt_id, document/revision identity, quality, actual_provider, model, parser/OCR/schema/prompt versions, content_hash, cache_key, structured_output, coverage, created_at.
- `AnalysisState`: document_id, revision_id, `latest_attempt: AttemptRecord | None`, `last_usable_result: ResultRecord | None`, `fallback_preview: ResultRecord | None`, cache_hit. Preserve legacy latest routes with compatible fields plus explicit state until the frontend transition is complete.
- `ExtractionResult`: ordered text blocks with page/section/region references, extracted_text, content_hash, parser/OCR versions, page coverage, warnings and omitted/truncated content.
- `BasisVersion`: asset_id, version_id, category, version_label, effective_from/to, source hash/type, processing attempt and published index_generation.
- API errors: `{ "detail": "safe message", "code": "stable_code", "request_id": "..." }`. Validate request and result types at both boundaries; do not treat a TypeScript cast as runtime validation.

## Preflight: Preserve the Reviewed Work and Any Live Data

**Addresses:** R01/R02/R05/R27. This is a future execution prerequisite, not an action performed by this review.

- [ ] Record HEAD, working-tree status and first-party source hashes; isolate task edits without overwriting the existing source changes.
- [ ] Inspect server status without starting/stopping it. If a valuable memory-backed instance is still alive, export accessible corporation/project/document/basis records and available analysis results by read-only API, and copy originals with an identity/checksum manifest to a protected local backup.
- [ ] Verify the export contains the known IDs/counts and source checksums. Record that current APIs do not expose every historical result; do not claim a complete memory snapshot or restart until required retention is addressed. Already-lost metadata requires explicit reconstruction review.
- [ ] Inform the credential owner of the tracked credential-shaped file without showing its content or testing it. If real, the owner revokes/replaces it. Removing a current tracked file and rewriting published history are separate actions; never perform a history rewrite or remote force-push implicitly.
- [ ] Preserve existing orphan/disconnected originals and basis copies. Inventory them for reconciliation; do not equate “unreferenced by the new DB” with safe to delete.

## Task T01: Explicit Runtime Factory and Enforceable Offline Configuration

**Dependencies:** Preflight preservation decision. **Addresses:** R05/R24/R25.

**Files:** Modify `backend/app/main.py`, `backend/.env.example`; create `backend/app/runtime_config.py`, `backend/app/models/runtime_records.py`, `backend/tests/__init__.py`, `backend/tests/test_runtime_config.py`.

**Interfaces:** Produce `RuntimeConfig.from_environment(*, load_project_env: bool) -> RuntimeConfig` and `create_app(config: RuntimeConfig | None = None) -> Flask`. Health returns application name, run ID, schema version and readiness. Test mode forbids external model calls and bootstrap regardless of project `.env`.

- [ ] Add `test_offline_config_skips_dotenv_bootstrap_and_network` with a dotenv reader, bootstrap function and provider stub that each fail if called; assert an injected temp config wins, `/health` identifies the requested run and no normal storage is created.
- [ ] Run `python -m unittest tests.test_runtime_config -v` from `backend/`; expect the current implicit dotenv/startup behavior to fail the new test.
- [ ] Implement the factory/config loader; move directory creation/DB initialization out of import side effects. Preserve `python -m app.main`; disable startup basis analysis by default and require explicit operator action through the processing service.
- [ ] Run the same tests; expect all pass. Run the existing TypeScript check only if API types changed. Review and commit only this task's files in a future implementation branch.

## Task T02: Owned Process Lifecycle and Bounded Identity Readiness

**Dependencies:** T01. **Addresses:** R04/R24/R25.

**Files:** Modify `scripts/manage-servers.ps1`, `frontend/vite.config.ts`; create `scripts/server-manager.psm1`, `scripts/tests/test-server-manager.ps1`.

**Interfaces:** Produce `Start-ManagedServers -Config <PSCustomObject>`, `Stop-ManagedServers -State <PSCustomObject>` and `Get-ManagedStatus -StatePath <string>`. State records run ID, root, PID, creation time, executable, exact launch identity, listener/child ownership, ports, URLs and log paths. A port owner or command-line substring is conflict evidence, never kill authority.

- [ ] Add deterministic mocked-function assertions: stale/reused PID and foreign port owner survive stop; unrelated workspace Python survives; one resolver candidate returns the complete path; status probes saved URLs; launch failure cleans only its own children; a hanging probe stops at the elapsed deadline; mismatched service/run fails readiness.
- [ ] Run `powershell -NoProfile -File scripts/tests/test-server-manager.ps1`; expect assertions to fail against existing behavior. No test may call real `Stop-Process` or project start commands.
- [ ] Implement immediate pre-stop ownership validation and an owned Windows child/job lifecycle. Make `start` idempotent; require `restart` for replacement. Resolve prerequisites/ports before any stop, inherit environment intentionally and pass explicit config into children. Keep hidden windows. Enforce `--strictPort`, connect/response probe timeouts and a 30-second overall readiness deadline; verify run/application identity and listener ownership. On failed start, clean only the new owned launch and retain diagnostics.
- [ ] Run the mocked tests; expect pass. After milestone B, verify start/status/stop only against a temporary offline instance; unrelated mock/real sentinel process must survive. Review and commit task files only.

## Task T03: Durable SQLite and Independent Transactions

**Dependencies:** T01; no live restart before Preflight. **Addresses:** R01/R03.

**Files:** Modify `backend/app/main.py`; create `backend/app/db/sqlite_runtime.py`, `backend/app/db/migrations/001_runtime.sql`, `backend/app/repositories/__init__.py`, `backend/app/repositories/corporations.py`, `backend/app/repositories/projects.py`, `backend/tests/test_sqlite_runtime.py`.

**Interfaces:** Produce `connect_db(config: RuntimeConfig) -> sqlite3.Connection`, `migrate_db(conn) -> None`, `transaction(conn)` context manager, and `get_request_db() -> sqlite3.Connection`. Each worker operation opens its own connection. Repository creates return the cursor-owned inserted ID, not a shared connection's later identity.

- [ ] Add `test_restart_retains_records`, `test_failed_request_does_not_rollback_other_request` and `test_request_connections_close`. Assert persistent counts/results after a fresh process, independent failure/commit outcomes and no global shared connection.
- [ ] Run `python -m unittest tests.test_sqlite_runtime -v`; expect loss/interference under the current runtime.
- [ ] Implement durable schema migration, short transaction ownership and close/rollback teardown. Use local-disk WAL and busy timeout. Land FK enforcement together with T04's deliberate deletion/retention rules; do not enable it alone against the old unlink-first route. Import any preserved export through a separately validated, idempotent reconciliation path; never initialize by dropping existing tables.
- [ ] Rerun tests with two real connections/isolated concurrent requests; expect pass. Verify migration twice preserves rows. Review and commit with T04 if necessary to keep the FK/deletion transition safe.

## Task T04: Recoverable File Ingestion, Deletion and Restart Reconciliation

**Dependencies:** T03; FK rules land atomically with this deliverable. **Addresses:** R08/R14/R27.

**Files:** Modify active upload/delete routes; create `backend/app/services/file_store.py`, `backend/app/repositories/documents.py`, `backend/app/db/migrations/002_file_operations.sql`, `backend/tests/test_file_store.py`.

**Interfaces:** Produce `ingest_source(stream, *, domain: str, owner_id: int | None, metadata: dict) -> DocumentRecord`, `delete_document(document_id: int) -> DeletionRecord`, `reconcile_file_operations() -> RecoveryReport`, and `resolve_stored_source(document_id: int) -> Path`. Files stay inside configured storage after path/reparse containment checks.

- [ ] Add `test_insert_failure_removes_only_staged_upload`, `test_delete_failure_restores_source`, `test_interrupted_operation_recovers`, `test_analyzed_document_fk_delete_policy` and `test_unrelated_orphan_is_not_purged`. Inject failure before/after each DB commit/file rename boundary and assert metadata/source consistency.
- [ ] Run `python -m unittest tests.test_file_store -v`; expect current save/unlink ordering to fail.
- [ ] Implement a persisted operation journal, UUID staging and immutable final originals. Ingest commits pending metadata, atomically moves the local file and finalizes readiness; startup reconciles incomplete transitions. Delete first commits a tombstone/invalidates active attempts, moves sources/derivatives to same-volume trash, then removes dependent analysis rows and document metadata in one DB transaction. Roll back/restoratively recover on failure; a cleanup-pending state is explicit, never reported as a completed hard delete. Do not purge trash until a verified backup/retention policy permits it.
- [ ] Run fault-boundary and fresh-process recovery tests with FK enabled; expect pass and no new orphan analysis. Review and commit the coordinated T03/T04 transition.

## Task T05: Local Trust Boundary, Request/File Validation and Parser Containment

**Dependencies:** T01/T03/T04. **Addresses:** R06/R10/R15/R16.

**Files:** Modify `backend/app/main.py`, `backend/requirements.txt`, `backend/.env.example`; create `backend/app/api/flask_routes.py`, `backend/app/schemas/runtime_contracts.py`, `backend/app/services/path_policy.py`, `backend/app/pipelines/worker_limits.py`, `backend/tests/test_api_boundary.py`, `backend/tests/test_ingest_validation.py`.

**Interfaces:** Produce `register_routes(app: Flask) -> None`, `validate_local_source(raw_path: str, config: RuntimeConfig) -> Path`, `validate_upload(stream, filename: str, domain: str) -> ValidatedUpload`, and `run_bounded_worker(command: list[str], *, timeout_seconds: int, memory_bytes: int) -> WorkerOutcome`.

- [ ] Add boundary cases for arbitrary Origin, missing/non-JSON mutation content type, bad Host, JSON array/null, blank name, boolean/fractional/negative IDs, unsupported category/type, renamed invalid file, 50 MiB + 1 byte, 501 pages and lexical UNC/device/network paths. Assert safe JSON errors, correct 400/403/413/415/422 codes and no mutation/filesystem network access; trusted loopback UI requests remain accepted.
- [ ] Run `python -m unittest tests.test_api_boundary tests.test_ingest_validation -v`; expect current permissive paths to fail.
- [ ] Implement configured exact frontend Origin/Host validation before parsing or mutation; remove forced text/plain JSON acceptance and wildcard CORS. Allow trusted non-browser local requests under an explicit policy, without adding login. Validate strict positive integer IDs and bounded field schemas. Check file signatures/regular-file identity, path namespace/drive type/reparse target before access; enforce local roots/network policy and input budgets. Use Windows job limits for parser subprocesses with deadlines and owned-tree cleanup.
- [ ] Upgrade/recheck/pin a compatible pypdf release at least 6.18.1 for the three [reviewed upstream advisories](../../service-analysis.md#dependency-and-external-evidence); run harmless malformed-input and extraction fixtures. This floor is not a full vulnerability clearance. Rerun all boundary tests and existing happy path; expect pass. Commit task files only.

## Task T06: Persisted Attempts and Conditional Result Publication

**Dependencies:** T03/T04/T05. **Addresses:** R03/R11/R14/R25.

**Files:** Modify active analysis routes; create `backend/app/repositories/analyses.py`, `backend/app/services/analysis_orchestrator.py`, `backend/app/db/migrations/003_attempts.sql`, `backend/tests/test_analysis_attempts.py`; extend runtime records/contracts.

**Interfaces:** Produce `start_attempt(domain: str, document_id: int, revision_id: int, requested_mode: str) -> AttemptRecord`, `publish_result(attempt_id: int, result: ResultRecord) -> bool`, `get_analysis_state(domain: str, document_id: int) -> AnalysisState`, `recover_interrupted_attempts() -> int`. Initially use bounded synchronous requests; no Redis/Celery requirement.

- [ ] Add `test_duplicate_attempt_is_rejected`, `test_delete_blocks_late_publication`, `test_failed_reanalysis_preserves_last_usable`, `test_restart_marks_interrupted` and `test_missing_document_differs_from_not_analyzed`. Assert one active lease, no late orphan, recorded failed stage/error, unchanged last usable identity and explicit interrupted status after restart.
- [ ] Run `python -m unittest tests.test_analysis_attempts -v`; expect current direct request/status updates to fail.
- [ ] Reserve/commit an attempt, release the write transaction, process outside SQLite transactions and conditionally publish only while document/revision/attempt are still current and nondeleted. Enforce the two-slot local admission limit and expire interrupted leases safely. Record parser/OCR/provider failures separately from previous success. Keep explicit import/processing outside readiness startup; do not retry paid interrupted work automatically.
- [ ] Rerun tests and the isolated concurrency/delete probes; expect pass. Confirm cache retrieval does not create misleading success attempts. Commit task files only.

## Task T07: Complete Extraction, Real OCR and Observable Coverage

**Dependencies:** T05/T06. **Addresses:** R07/R16/R21.

**Files:** Create `backend/app/pipelines/extraction.py`, `backend/app/pipelines/ocr_adapter.py`, `backend/app/pipelines/normalization.py`, `backend/tests/test_extraction.py`, synthetic fixtures under `backend/tests/fixtures/`; modify active orchestrator, requirements and environment example.

**Interfaces:** Produce `extract_document(path: Path, kind: str, *, limits: ProcessingLimits) -> ExtractionResult`, `ocr_regions(regions: list[ImageRegion], *, languages: str, deadline: float) -> list[TextBlock]`, `normalize_blocks(blocks: list[TextBlock]) -> list[TextBlock]`. Persist ordered blocks and coverage without adding Phase 3 citation rendering.

- [ ] Add `test_docx_table_header_footer_retained`, `test_blank_pdf_is_insufficient`, `test_mixed_pdf_reports_unreadable_regions`, `test_scanned_pdf_uses_ocr`, `test_parser_worker_timeout` and `test_dated_required_document_survives`. Assert unique markers, page/region counts, explicit partial coverage and no unqualified success for unreadable/empty input.
- [ ] Run `python -m unittest tests.test_extraction -v`; expect current paragraph-only/no-OCR behavior to fail.
- [ ] Implement per-page PDF extraction and paragraph/table/header/footer DOCX traversal with deterministic ordering. Use a local PDF rendering adapter and Tesseract `kor+eng` for detected image/low-text regions; missing OCR capability yields an explicit failed/insufficient stage. Retain region/page context, coverage and normalization provenance, and enforce stated limits through T05's worker. Remove the heuristic that drops a required-document line merely because it contains a date. Preserve its schedule information too.
- [ ] Rerun synthetic tests. Separately execute an approved anonymized Korean scanned/mixed/table corpus; record observed accuracy and unresolved omissions before claiming real OCR acceptance. Unit fakes alone are insufficient. Commit task files only.

## Task T08: Strict Model Contracts, Bounded Calls and Provenance-Aware Cache

**Dependencies:** T06/T07. **Addresses:** R11/R12/R13/R21.

**Files:** Create `backend/app/pipelines/summarization.py`, `backend/app/services/cache_identity.py`, `backend/tests/test_summarization.py`, `backend/tests/test_analysis_cache.py`; extend `runtime_contracts.py`, runtime records and analysis repository.

**Interfaces:** Produce `summarize(extraction: ExtractionResult, request: SummaryRequest) -> SummaryOutcome`, `validate_summary(payload: object, schema_version: str) -> SummaryOutput`, `make_cache_key(context: AnalysisContext) -> str`. Cache identity includes document/version/content, category, parser/OCR/options, schema/prompt, requested mode/provider, effective provider and model configuration.

- [ ] Add schema cases `{}`, missing keys, wrong types, refusal and incomplete response; assert no usable publication. Add prompt/model/parser/category changes and fallback-to-model recovery; assert recomputation. Add forced provider failure after usable model success; assert preserved last usable ID, failed attempt and separately labeled optional fallback preview. Verify sent-character/coverage values exclude unsent suffixes.
- [ ] Run `python -m unittest tests.test_summarization tests.test_analysis_cache -v`; expect current permissive output/cache/promotion behavior to fail. Use injected local provider stubs only.
- [ ] Validate complete output shape without silently normalizing required fields away. Bound total model execution at 60 seconds including one retry, and retain safe failure codes. Keep offline fallback explicitly degraded; never store it as successful requested-provider output or satisfy a later requested-model cache lookup with it. Reuse only matching usable results. Replace silent prefix truncation with coverage-aware bounded multi-part processing or an explicit partial/insufficient outcome under the deadline; empty lists do not certify that the original has no requirements.
- [ ] Rerun tests and integrated attempt tests; expect pass. A future authorized real-model check must separately assess Korean factual accuracy, not just JSON shape. Commit task files only.

## Task T09: Route Identity, Request State and Mutation Feedback

**Dependencies:** T06/T08; independent UI containment may begin earlier. **Addresses:** R09/R11/R22.

**Files:** Modify `frontend/package.json`, lockfile, `src/app/api.ts`, `src/app/types.ts`, all six current pages; create `src/shared/api/client.ts`, `src/shared/ui/RequestState.tsx`, `src/features/analysis/useDocumentAnalysis.ts`, `src/features/documents/useDocumentMutations.ts`, `src/pages/__tests__/request-state.test.tsx`.

**Interfaces:** Produce `request<T>(path, { signal, ...init }?) -> Promise<T>` with validated error envelopes; `useDocumentAnalysis(documentId: number)` returns identity-bound state/result/latestAttempt/reload; mutation hooks expose pending/error/success per action. AbortController prevents obsolete UI publication but does not claim cancellation of backend/model work.

- [ ] Add actual rendered-component tests: route 1 -> 2 with failed/late response never displays document 1 under route 2; reanalysis rejection shows failed attempt and dated last result; duplicate submit yields one request; native file control clears after success; imported basis remains listed after processing failure; failed dashboard/list fetch shows an error instead of zero/onboarding; filter miss differs from no records.
- [ ] Add Vitest/Testing Library/jsdom versions compatible with the existing Vite/React major versions, locking them without unrelated upgrades. Run `npm run test -- --run src/pages/__tests__/request-state.test.tsx`; expect the new regression cases to fail before fixes.
- [ ] Reset identity-bound state on navigation, abort/ignore obsolete responses and verify returned document/revision IDs. Add catch/finally and user-visible retryable feedback for each async path; guard mutation buttons until completion. Reset the real file input via ref/form reset, refresh registered basis candidates even after analysis failure, and separate loading/error/empty/no-match/never-analyzed/processing/degraded/previous-result states.
- [ ] Rerun rendered tests and `node node_modules/typescript/bin/tsc --noEmit --incremental false`; expect pass. Exercise navigation/upload/error recovery in a real browser against the isolated instance before UX acceptance. Commit task files only.

## Task T10: Early Basis Interpretation and Replacement Containment

**Dependencies:** T01; execute after T02, before full CRUD; integrate T06/T09 contracts when available. **Addresses:** R17/R18/R19/R20.

**Files:** Modify `backend/app/main.py`, `frontend/src/pages/AnalysisPage.tsx`, `frontend/src/pages/BasisDocumentsPage.tsx`, API/types; create `backend/tests/test_basis_containment.py`, `frontend/src/pages/__tests__/basis-containment.test.tsx`.

**Interfaces:** Category reads distinguish `latest_candidate` from `published_usable`; processing accepts only supported category. Different content is a new candidate even if the original filename repeats. The analysis page consumes no basis result as an applicable issuance determination.

- [ ] Add `test_pending_basis_does_not_mask_usable`, `test_same_filename_changed_content_is_candidate`, `test_unsupported_category_rejected` and a UI assertion that unmatched first-list basis items never render as issuance requirements for the analyzed document. Raw labeled library metadata may remain visible.
- [ ] Run the backend module and frontend basis-containment test; expect current behavior to fail.
- [ ] Remove/suppress the current asserted issuance panel; do not replace it with premature item matching. Restrict category analysis, preserve successful basis selection when a candidate is pending/failed, and register changed content distinctly. Label remaining independent basis inspection with its own title/category/version/scope/provenance, without implying project applicability. This is containment, not full Phase 2 implementation.
- [ ] Rerun the tests; expect pass. Revalidate the same containment after T12's version schema migration. Commit task files only.

## Task T11: Phase 1 CRUD, Attribution and Safe Source Inspection

**Dependencies:** Milestone B, T04/T06/T07/T09. **Addresses:** R23; related R15/R22.

**Files:** Extend `api/flask_routes.py`, corporation/project/document repositories and `runtime_contracts.py`; create `backend/tests/test_phase1_workflows.py`; modify frontend API/types/routes and existing pages; create `frontend/src/pages/CorporationDetailPage.tsx`, `ProjectDetailPage.tsx`, `frontend/src/entities/documents/DocumentIdentity.tsx`, `DocumentSourceView.tsx`, and `frontend/src/pages/__tests__/phase1-workflows.test.tsx`.

**Interfaces:** Add validated corporation/project GET/PATCH/DELETE by ID; dependent deletion returns 409 with dependent counts. Add document source download and extraction/coverage reads by verified document ID, not arbitrary local path. UI attribution includes filename, project, corporation, document revision, result time and actual provider/quality.

- [ ] Add round-trip view/edit tests for every saved corporation field, especially certifications/internal notes; dependent-delete rejection; project inspection; recoverable document deletion; source-download containment; original/extracted-text comparison; route/result attribution. Assert malicious text is escaped and untrusted Markdown/HTML cannot execute.
- [ ] Run `python -m unittest tests.test_phase1_workflows -v` and corresponding frontend test file; expect missing routes/views to fail.
- [ ] Implement minimal Phase 1 CRUD/detail and document deletion UI using existing relationships and T04 recovery. Serve originals as downloads with safe filenames/content disposition; expose retained extraction/coverage in a read-only comparison view. Show general document summary and all relevant extraction warnings; keep human interpretation separate from model structure. Preserve React text escaping or sanitize any added Markdown renderer.
- [ ] Rerun tests, TypeScript and isolated browser edit/view/delete/source flows; expect pass. Do not claim calculator, corporation matching or eligibility behavior. Commit task files only.

## Task T12: Versioned Basis Assets, Library CRUD and Safe Publication

**Dependencies:** Phase 1 acceptance, T10/T04/T06/T07. **Addresses:** R17/R18/R19/R23/R25; Phase 2 delivery gap.

**Files:** Create `backend/app/repositories/basis.py`, `backend/app/services/basis_ingestion.py`, `backend/app/db/migrations/004_basis_versions.sql`, `backend/tests/test_basis_versions.py`; extend active routes/contracts; modify `BasisDocumentsPage.tsx` and create `frontend/src/pages/BasisDocumentDetailPage.tsx`, related API/types/tests.

**Interfaces:** Produce `register_basis_version(source: ValidatedUpload, metadata: BasisMetadata) -> BasisVersion`, `get_published_basis(category: str) -> BasisVersion | None`, `publish_basis_generation(version_id: int, generation_id: str) -> bool`, and basis detail/update/delete/reprocess endpoints. Native PDF upload replaces hardcoded personal-path UI defaults; any retained local-import adapter obeys T05's policy.

- [ ] Add `test_same_name_different_version`, `test_duplicate_source_is_idempotent`, `test_failed_candidate_keeps_published`, `test_effective_metadata_roundtrip`, `test_basis_has_no_project_owner` and `test_restart_does_not_duplicate_bootstrap_copies`. Validate source hash plus explicit version/category/effective dates, never filename alone.
- [ ] Run `python -m unittest tests.test_basis_versions -v` plus library detail tests; expect current schemas/publication/import workflow to fail.
- [ ] Separate reusable asset identity from immutable source versions and processing generations. Migrate existing rows as explicitly unverified legacy versions without inventing effective dates. Store required operator metadata, candidate errors and published identity; edit metadata through traceable updates and deletion through T04. Reprocess stages a new generation while keeping the last usable one available. PDF registration automatically starts the Phase 2 pipeline when T13 is available; no manual chunking.
- [ ] Rerun backend/frontend tests and T10 containment tests; expect pass. Unknown applicability stays unknown; no eligibility or issuance guidance. Commit task files only.

## Task T13: Automatic Phase 2 Chunking and Local Index Generations

**Dependencies:** T12 and Phase 1 acceptance. **Addresses:** R21 and missing Phase 2 pipeline.

**Files:** Create `backend/app/pipelines/chunking.py`, `embedding.py`, `indexing.py`, `backend/tests/test_basis_ingestion.py`, `backend/tests/test_basis_index.py`; extend `basis_ingestion.py`, requirements/config, basis chunk/generation migration and library processing UI.

**Interfaces:** Produce `chunk_blocks(extraction: ExtractionResult, metadata: BasisMetadata) -> list[BasisChunk]`, `embed_chunks(chunks: list[BasisChunk], model: str) -> EmbeddingBatch`, `build_generation(version: BasisVersion, batch: EmbeddingBatch) -> IndexGeneration`, `ingest_basis(version_id: int) -> AttemptRecord`. Stages are extract -> OCR -> normalize -> chunk -> embed -> index -> conditional publish.

- [ ] Add metadata/coverage tests and failures at every stage: version/category/page/section/chunk hash retained; a failed extraction/embedding/index build leaves the old published generation intact; restart recovers staging; identical source/options are idempotent; a newer attempt/deletion blocks publication. Assert no manual chunk controls and no project-qualification endpoint.
- [ ] Run `python -m unittest tests.test_basis_ingestion tests.test_basis_index -v`; use deterministic fake vectors for fault tests and expect missing pipeline behavior to fail.
- [ ] Implement embedded persistent Qdrant on this PC, without Docker/cloud infrastructure. Use the CPU FastEmbed-supported `intfloat/multilingual-e5-large` as the explicit initial model (1024 dimensions, cosine), provision model files in a separate operator-visible step, and use cached assets only during normal ingestion. Use its tokenizer to create at most 384-token chunks with 48-token overlap and retained source boundaries; avoid silent embedding truncation. Pin compatible packages/model revision/checksums when this task executes. [Qdrant local-mode reference](https://github.com/qdrant/qdrant-client#local-mode), [FastEmbed supported models](https://qdrant.github.io/fastembed/examples/Supported_Models/).
- [ ] Store one staging collection per generation; verify count/checksums, then transactionally publish its generation ID in SQLite. Treat the DB pointer as canonical so a crash between vector build and DB commit cannot replace the old version. Reconcile staged collections on restart; retain old generations until backup/retention cleanup. Bound Phase 2 work to one local ingestion at a time, 30-minute total duration and a separately configured 4 GiB embedding-worker budget; emit explicit resource failure if unavailable. Use a local background worker only where needed for the long pipeline, never a distributed queue.
- [ ] Run fault/restart tests and a provisioned-model Korean sample on the actual PC. Verify vectors/dimensions/counts and measured resource use; indexing success does not prove retrieval/applicability accuracy. Publish no Phase 3 retrieval judgments. Review and commit task files only.

## Task T14: Accessibility and Unambiguous Workflow States

**Dependencies:** T09/T11; repeat for Phase 2 views. **Addresses:** R28 and R22 filter ambiguity.

**Files:** Modify `frontend/src/styles.css`, page/shared UI components; create `frontend/src/pages/__tests__/accessibility.test.tsx`.

**Interfaces:** Search/filter controls have persistent accessible names; loading/success use polite status messages; actionable errors use appropriate alerts. Native keyboard behavior and existing focus indicators remain intact.

- [ ] Add rendered tests using accessible roles/names: corporation/project/document search and status selector are discoverable; processing/error messages are announced; no-match copy differs from empty collection. Test keyboard activation and focus after mutation failure.
- [ ] Run the accessibility test file; expect the current unnamed/announcement cases to fail.
- [ ] Add explicit labels and status semantics. Adjust normal-text/white-button combinations to at least 4.5:1 across the actual rendered gradient/background, including hover/focus states; preserve visual hierarchy and verify disabled states separately. The source calculation was 3.633:1 for the current bright brand color, not a complete rendered audit. [WCAG contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- [ ] Rerun component tests, TypeScript and a real browser accessibility-name/keyboard/contrast check. Record scope rather than claiming universal WCAG compliance. Commit task files only.

## Task T15: Isolated Acceptance, Backup/Restore and Honest Documentation

**Dependencies:** T01-T11/T14 for Phase 1; extend after T12/T13 for Phase 2. **Addresses:** R01/R02/R05/R24/R26/R27.

**Files:** Modify `scripts/smoke-test.ps1`, `.gitignore`, README, `docs/technical-design.md`, `docs/ux-design.md`, `docs/ai-api-setup.md`, `docs/work-log.md`, `docs/service-analysis.md`; create `backend/app/services/backup_service.py`, `backend/tests/test_backup_restore.py`, `scripts/tests/test-smoke-isolation.ps1` and synthetic text-bearing PDF/DOCX fixtures.

**Interfaces:** Produce `create_backup(destination: Path) -> BackupManifest`, `restore_backup(manifest: BackupManifest, target_config: RuntimeConfig) -> RestoreReport`. Smoke accepts explicit temp root, DB/storage/status/log roots, private ports and offline config; it cleans only its own owned processes and resolved temp workspace.

- [ ] Add acceptance tests for restart retention, corrupt/blank/mixed documents, malformed requests, file/DB recovery, duplicate/delete races, cache/provider recovery, route identity and FK integrity. Use text-bearing fixtures with expected required-document/date markers; completed status alone is not an assertion of extraction quality. Assert smoke never reads real `.env`, bootstraps personal basis files, calls external providers or touches normal ports/storage/status.
- [ ] Run `python -m unittest tests.test_backup_restore -v` and both script test files. Expect existing smoke isolation/backup behavior to fail; keep all OS/process tests mocked until the owned temporary-instance gate is met.
- [ ] Build consistent backups using SQLite's backup API and an operation/admission lock around the immutable source/derivative manifest, not a raw copy of a live WAL database. Include Phase 2 generations when present; exclude credentials and logs containing document text. Restore to a separate empty location, verify hashes/row references/index generation and only then treat the backup as usable. Retain seven snapshots with explicit safe cleanup boundaries.
- [ ] Rewrite smoke to launch only a dedicated offline instance, enforce native command exit codes/HTTP deadlines/schema assertions, restart it to verify persistence and always clean its own owned process tree. Before recursive temp deletion, resolve/verify the absolute path remains inside the test root; use native PowerShell literal-path operations end to end. Do not run the old live lifecycle as acceptance.
- [ ] Add ignore patterns for basis originals/derivatives, model/index caches and SQLite journal/WAL/SHM artifacts. Untrack generated artifacts without deleting needed local files. Resolve credential handling through the owner; do not rewrite published history in this task without separate authorization.
- [ ] Align documentation with actual Flask launch/dependencies, implemented OCR/cache/error behavior and acceptance evidence. Replace portable-project links, explain remaining legacy code and distinguish Phase 1, Phase 2 and deferred Phase 3. Preserve historical dated evidence and the canonical report path in AGENTS.md. Do not mark a planned task implemented merely because its tests were drafted.
- [ ] Run the final gates below on the isolated instance. Update actual test results/limits in the work log/report, review the complete diff and commit only completed task files. No production acceptance claim follows solely from syntax/type checks.

## Final Acceptance Gates for Future Execution

From `backend/`, use the configured project Python environment:

```powershell
python -m unittest discover -s tests -v
```

From `frontend/`, after the proposed test tooling exists:

```powershell
npm run test -- --run
node node_modules/typescript/bin/tsc --noEmit --incremental false
npm run build
```

From the repository root, run only the rewritten/mocked script tests and isolated smoke:

```powershell
powershell -NoProfile -File scripts/tests/test-server-manager.ps1
powershell -NoProfile -File scripts/tests/test-smoke-isolation.ps1
powershell -NoProfile -File scripts/smoke-test.ps1 -Offline -TestRoot <verified-temporary-directory>
git diff --check
```

Operational rollout remains gated on all of the following, irrespective of task execution order:

- [ ] Pre-restart preservation is accounted for; persistent rows/results survive fresh processes and a verified backup restore.
- [ ] Foreign/unrelated processes survive lifecycle tests; strict port/run readiness and failed-launch cleanup pass.
- [ ] Cross-origin/text/plain mutation and untrusted Host requests fail safely while the intended local UI works.
- [ ] No shared transaction interference, orphan late analysis or file/DB half-operation remains in fault/restart tests.
- [ ] Empty/corrupt/mixed/scanned/table documents have truthful outcomes; real approved OCR corpus limits are recorded.
- [ ] Requested provider, actual provider, model/schema/parser versions, analyzed coverage and cache provenance remain inspectable; failed reanalysis preserves dated prior results.
- [ ] Real browser navigation/error/retry/upload/detail/delete flows cannot display another document's result or invent empty collections after an error.
- [ ] Phase 2 acceptance separately proves complete metadata/index publication and failed replacement preservation; no Phase 3 interpretation is exposed.
- [ ] Documentation names the actual executed checks and remaining limits; any credential-owner/history actions are tracked separately.

## Questions for Product Owner

The plan proceeds using the stated conservative defaults. These questions inform later implementation/acceptance decisions and do not justify changing code during the present review:

- Which live records/history must be preserved before the first restart, and which exposed credential owner should complete revocation if the tracked value is real?
- Are mapped/network-drive basis sources required? The default remains local-volume input until an explicit network policy is adopted.
- Which supported basis categories, product identifiers and version/effective-date fields are mandatory? Unknown values remain unknown; analysis must not invent them.
- Which anonymized Korean procurement documents and accuracy criteria constitute OCR/model acceptance? Resource limits and the initial embedding choice must be measured on this PC before operational delivery.
- Is an optional degraded fallback preview wanted after requested-model failure, and should backup retention differ from seven snapshots?

## Plan Self-Review and Handoff

The plan maps all accepted finding groups to tasks; separates defect containment, Phase 1 completion and Phase 2 delivery; defines failure/promotion/deletion policy; and keeps Source/Attempt/Result/BasisVersion identities consistent across API, storage and frontend. The five review-focus conditions have owning tests. No framework migration, authentication, crawler, corporation matching, final judgment or manual chunking is proposed.

The preceding service report records what was inspected and executed. This plan records only future work; none of its implementation, installation, migration, restart or acceptance steps has run. At the user's instruction, stop here and wait before code modification.
