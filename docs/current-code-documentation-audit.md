# 현재 코드/문서 감사 리포트

## 한국어 버전

최종 갱신일: 2026-08-21

## 문서 목적
이 문서는 현재 코드 전체 리뷰와 Markdown 문서 재검토 결과를 한곳에 정리합니다.
과거 Phase 계획서가 많아졌기 때문에, 각 문서의 과거 계획과 현재 구현 상태가 충돌하지 않도록 기준점을 제공합니다.

## 현재 코드 기준 핵심 상태
- 백엔드는 Python 3.13.13 + Flask + SQLite 기반 로컬 단일 PC 서비스입니다.
- 프론트엔드는 React + TypeScript + Vite + React Router 기반입니다.
- PDF 추출 기본값은 `PDF_READER_ENGINE=auto`입니다.
- `auto` 모드는 OpenDataLoader PDF를 먼저 사용하고, Java/패키지/timeout/변환 실패 시 PyMuPDF로 fallback합니다.
- 일반 문서, 나라장터 첨부 PDF, 기준문서 PDF는 모두 `extract_document()` 진입점을 공유합니다.
- DOCX 추출은 문단과 표 cell 텍스트를 모두 분석 입력에 포함합니다.
- 기준문서 RAG 검색은 DB chunk 직접 검색이 아니라 JSON 인덱스 운영 산출물인 `storage/basis-index/basis-index.json`을 사용합니다.
- JSON 기준문서 인덱스가 없거나 손상되었거나 DB와 불일치하면 검색, 규칙 후보 승인, 판단 엔진 citation 사용을 차단하고 rebuild를 요구합니다.
- 기준문서 재처리 실패 시 기존 정상 chunk/index를 무단 삭제하지 않도록 보강되어 있습니다.
- 나라장터 검색은 공사·용역·물품·기타와 전체 병합 검색을 지원합니다.
- 판단 엔진은 규칙 기반 결과와 Gemini 70% 가중 판단 보조를 보수적으로 병합하고, 부족 조건, 필요 서류, 준비 가이드, 근거 상태를 저장합니다.
- Phase 4 운영 기능은 운영 대시보드, 작업 이력/실패/재시도, 백업 생성/검증/복원계획 dry-run까지 포함합니다.
- 고정 ngrok 도메인 `https://smart.kang.ngrok.pro`는 프론트엔드와 same-origin `/api`를 단일 주소로 제공합니다.
- 저장 공고와 법인 정보를 기준으로 검토용 계약서 DOCX 초안을 생성합니다.
- Playwright 기반 전체 업무 흐름 시연 영상 자동화가 구현되어 있습니다.

## 코드 리뷰 결과
이번 리뷰에서 문서와 함께 확인한 핵심 코드 영역:
- `backend/app/main.py`: API 라우트, 판단 엔진, 기준문서/나라장터/백업/운영 API
- `backend/app/pipelines/parser.py`: 문서 추출 진입점
- `backend/app/pipelines/pdf_readers.py`: OpenDataLoader/PyMuPDF adapter
- `backend/app/pipelines/basis_document.py`: 기준문서 청킹, JSON 인덱스, 검색, 재처리
- `backend/app/services/basis_rule_candidates.py`: 기준문구 후보 승인/반려/수정
- `backend/app/services/backups.py`: 백업/검증/복원계획
- `backend/app/services/operations.py`: 운영 대시보드/작업 요약
- `frontend/src/app/App.tsx`, `frontend/src/app/api.ts`: 화면 라우트와 API client

현재 코드에서 즉시 문서화가 필요한 누락/불일치:
- 일부 과거 문서는 PDF 추출을 PyMuPDF 중심으로 설명했지만, 현재 기본 리더는 OpenDataLoader 우선 `auto` 모드입니다.
- 일부 과거 문서는 기준문서 검색 source를 DB chunk처럼 설명했지만, 현재 운영 검색 source는 JSON basis index입니다.
- 일부 과거 문서는 DOCX 추출을 문단 중심으로 설명했지만, 현재는 표 cell 텍스트도 포함합니다.
- 일부 과거 검증 문서는 `118 passed` 또는 `105 passed` 같은 이전 테스트 기준선을 담고 있었고, 최근 PDF/RAG 보강 후 기준선은 `134 passed`, `8 skipped`입니다.
- 실제 기준문서 샘플의 PyMuPDF 기반 재생성 MD와 report는 역사적 기준선 산출물입니다. 현재 RAG 기본 리더 품질 판단은 OpenDataLoader QA 산출물을 우선 봅니다.

## 남은 코드 리스크
- 첨부 URL 검증의 DNS rebinding/shared address 보강은 사용자 요청에 따라 즉시 수정 범위에서 제외했고, `docs/코드리뷰 후 수정필요.md`와 `docs/pdf-rag-code-review-remediation-plan.md`에 기록-only 이슈로 유지합니다.
- `backend/tests/__init__.py`는 기본 테스트 환경에서 `PDF_READER_ENGINE=pymupdf`를 설정합니다. 전체 backend 회귀 테스트를 빠르고 안정적으로 유지하기 위한 선택이지만, 운영 기본값인 `auto` 전체 경로는 별도 OpenDataLoader QA와 targeted tests로 보완해야 합니다.
- 나라장터 PDF 샘플 manifest 중 일부는 과거 PyMuPDF 기준으로 생성된 캐시입니다. 새 분석은 현재 `extract_document()` 정책을 따르지만, 샘플 manifest 자체는 historical fixture로 봐야 합니다.
- `gpt api.txt`가 Git에 추적되어 있고 credential 패턴과 일치합니다. 값은 문서에 노출하지 않았으며, 관련 키 회전/폐기와 파일·Git 이력 정리가 필요합니다.
- 고정 ngrok 주소는 현재 무인증 단일 관리자 포탈을 외부에 공개하므로 운영 사용 전 인증·권한·접속 통제가 필요합니다.
- `scripts/manage-servers.ps1`의 보조 프로세스 탐지 조건 한 곳에 `D:\project\wisdom_procurement` 절대경로가 남아 있어 다른 설치 경로에서 오래된 프로세스 탐지가 제한될 수 있습니다.
- 일부 과거 QA 문서와 `scripts/run-opendataloader-real-basis-qa.py` 기본 경로가 기존 사용자 폴더를 참조합니다. 다른 PC에서는 `--pdf source\rag_doc\...pdf`를 명시해야 합니다.
- `backend/app.db`, `.env`, 일부 업로드/로그/캐시는 Git에 포함되지 않지만 일부 `backend/storage/`와 데모 산출물은 추적됩니다. clone만으로 기존 운영 상태가 완전히 복원되지 않습니다.
- 현재 Git pack은 약 326 MiB이며, 대용량 영상·스크린샷·스토리지 산출물의 보관 정책이 필요합니다.

## MD 문서 검토 결과
이번 업데이트에서 최신 구현 상태를 반영하거나 최신 상태 문서를 연결한 문서:
- `README.md`
- `docs/technical-design.md`
- `docs/technology-summary.md`
- `docs/ai-api-setup.md`
- `docs/basis-rag-json-index-management-plan.md`
- `docs/basis-rag-p2-followup-fix-plan.md`
- `docs/basis-rag-additional-remediation-plan.md`
- `docs/basis-document-extraction-improvement-plan.md`
- `docs/basis-document-md-regeneration-comparison-plan.md`
- `docs/real-basis-document-rag-test-plan.md`
- `docs/opendataloader-pdf-reader-review.md`
- `docs/opendataloader-pdf-replacement-test-plan.md`
- `docs/pdf-rag-code-review-remediation-plan.md`
- `docs/current-service-verification-remediation-plan.md`
- `docs/ux-design.md`
- `docs/ux-monkey-testing-plan.md`
- `docs/remaining-development-roadmap.md`
- `docs/other-pc-handoff-guide.md`
- `docs/운영 제품화 세부계획서.md`
- `docs/코드리뷰 후 수정필요.md`
- `backend/tests/real-basis-document-samples/README.md`
- `docs/work-log.md`

과거 계획/이력 성격이라 원문 전체를 새 구현 문서로 바꾸지 않은 문서:
- `docs/phase-1.6-stabilization-plan.md`
- `docs/phase-1.7-stabilization-plan.md`
- `docs/phase-2-implementation-plan.md`
- `docs/phase-2-closeout-to-phase-3-execution-plan.md`
- `docs/p1-p2-doc-remediation-plan.md`
- `docs/corporation-evidence-auto-extraction-plan.md`
- `docs/ocr-engine-implementation-plan.md`
- `docs/narajangteo-api-analysis.md`
- `docs/narajangteo-api-test-result-20260505.md`
- `docs/narajangteo-board-design.md`
- `docs/eligibility-rag-implementation-plan.md`
- `AGENTS.md`

위 문서는 과거 결정/계획의 기록으로 유지합니다. 현재 실행 기준은 README, 기술 설계서, 기술 요약, 이 감사 리포트, 작업 로그를 우선합니다.

생성 산출물로 유지한 Markdown:
- `backend/tests/real-basis-document-samples/regenerated-basis-document.md`
- `backend/tests/real-basis-document-samples/opendataloader-regenerated-basis-document.md`
- `backend/tests/real-basis-document-samples/opendataloader-regenerated-basis-document-auto.md`
- `backend/tests/real-basis-document-samples/opendataloader-regenerated-basis-document-fallback.md`

이 파일들은 테스트 fixture/QA artifact라서 사람이 읽는 설계 문서처럼 문장을 최신화하지 않습니다.

## 문서 최신화 원칙
1. 현재 실행 기준은 README와 이 감사 리포트를 우선합니다.
2. 과거 계획서는 삭제하지 않고, 상단 또는 구현 상태 섹션에 최신 구현 기준을 붙입니다.
3. PDF/RAG 관련 문서는 OpenDataLoader `auto`, JSON basis index, DOCX table cell 추출을 기준으로 해석합니다.
4. 현재 대표 기준문서 PDF는 `source/rag_doc/`에 추적되어 다른 PC에서도 사용할 수 있습니다. 비교용 TXT/DOCX/MD 원본은 별도 로컬 참조자료로 관리합니다.
5. 문서 변경은 `docs/work-log.md`에 기록합니다.
6. 다른 PC 작업 재개는 `docs/other-pc-handoff-guide.md`의 소스-only/운영 데이터 이전 구분을 따릅니다.

## Questions for Product Owner
- DNS rebinding/shared address 보강을 다음 보안 작업으로 즉시 진행할지, 운영 배포 직전 보강 항목으로 둘지 결정이 필요합니다.
- 전체 backend tests의 기본 PDF reader를 `auto`로 바꿀지, 현재처럼 빠른 PyMuPDF 기본값 + 별도 OpenDataLoader QA로 유지할지 결정이 필요합니다.
- `gpt api.txt` 관련 키를 즉시 회전하고 Git 이력까지 정리할지 결정이 필요합니다.
- 새 PC로 기존 `backend/app.db`와 `backend/storage/`를 옮길지, 빈 개발 DB로 시작할지 결정이 필요합니다.
- 대용량 생성 산출물을 Git에서 계속 관리할지 외부 artifact 저장소로 분리할지 결정이 필요합니다.

---

# AI / Engineering Version (English)

## Purpose
This document records the 2026-08-21 current-code, documentation, and cross-PC handoff audit.
It gives future agents a single source of truth when older phase plans conflict with the current implementation.

## Current Code Snapshot
- Backend: Python 3.13.13, Flask, SQLite, local filesystem.
- Frontend: React, TypeScript, Vite, React Router.
- PDF extraction default: `PDF_READER_ENGINE=auto`.
- `auto` tries OpenDataLoader PDF first and falls back to PyMuPDF on Java/package/timeout/conversion failures.
- Target documents, Nara attachments, and basis PDFs share `extract_document()`.
- DOCX extraction includes paragraphs and table cells.
- Basis retrieval uses the operational JSON artifact `storage/basis-index/basis-index.json`.
- Invalid/missing/inconsistent basis index state blocks search, rule-candidate approval, and judgment citation usage.
- Basis reprocessing preserves existing completed/indexed knowledge when the stored source file is missing.
- Nara search supports construction, service, goods, etc, and merged all-business-type search.
- Judgment runs conservatively combine deterministic comparison with Gemini 70% weighted assistance.
- Phase 4 operations include dashboard, operation runs, failures/retries, backups, validation, and restore dry-runs.
- Fixed-domain ngrok access uses `https://smart.kang.ngrok.pro` with same-origin `/api` proxying.
- Contract DOCX generation and Playwright full-workflow demo recording are implemented.

## Code Review Notes
Reviewed:
- `backend/app/main.py`
- `backend/app/pipelines/parser.py`
- `backend/app/pipelines/pdf_readers.py`
- `backend/app/pipelines/basis_document.py`
- `backend/app/services/basis_rule_candidates.py`
- `backend/app/services/backups.py`
- `backend/app/services/operations.py`
- `frontend/src/app/App.tsx`
- `frontend/src/app/api.ts`

Documentation drift fixed or recorded:
- PyMuPDF-centered descriptions were updated to OpenDataLoader `auto` plus PyMuPDF fallback.
- DB-chunk retrieval descriptions were updated to JSON basis index retrieval.
- DOCX paragraph-only descriptions were updated to include table-cell extraction.
- Previous verification baselines were updated with the latest `134 passed`, `8 skipped` backend result where relevant.
- PyMuPDF regenerated Markdown artifacts are historical baselines; current basis QA prioritizes OpenDataLoader artifacts.

## Remaining Risks
- Attachment URL DNS rebinding/shared-address hardening remains record-only per user request.
- `backend/tests/__init__.py` defaults tests to `PDF_READER_ENGINE=pymupdf`; OpenDataLoader coverage must remain covered by targeted tests and real-basis QA.
- Some Nara sample manifests are historical PyMuPDF fixtures.
- Tracked `gpt api.txt` matches a credential pattern; rotate/revoke the credential and remove the file/history through an approved security task.
- The fixed ngrok endpoint exposes the current unauthenticated portal.
- One auxiliary `manage-servers.ps1` process-discovery condition still uses `D:\project\wisdom_procurement`.
- Historical QA defaults reference the previous user's absolute source path; another PC should pass the tracked basis PDF explicitly.
- Git does not include `.env` files or `backend/app.db`, while parts of storage and demo artifacts are tracked, so a clone is not a complete runtime-state restore.
- The Git pack is about 326 MiB and needs an artifact-retention decision.

## Documentation Rule
Current operational interpretation should prefer README, the cross-PC handoff guide, technical design, technology summary, this audit, and work-log over older phase plans.

## Questions for Product Owner
- Decide when to implement DNS rebinding/shared-address hardening.
- Decide whether full backend tests should default to `auto` or keep fast PyMuPDF defaults plus targeted OpenDataLoader QA.
- Decide whether to rotate the credential and remove `gpt api.txt` from Git history now.
- Decide whether the new PC receives the existing database/storage or starts with an empty development database.
- Decide whether generated artifacts remain in Git or move to external artifact storage.
