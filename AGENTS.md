# 한국어 버전

## 목적
이 문서는 Codex와 향후 AI 코딩 에이전트가 `SMART 조달청 계산기` 저장소에서 일관되게 작업하도록 돕는 운영 규칙입니다.

## 저장소 규칙
- 프론트엔드와 백엔드는 반드시 분리한다.
- 설계 문서는 `docs/` 아래에 유지한다.
- 기능 작업 전 해당 기능이 어느 Phase에 속하는지 먼저 확인한다.
- 로컬 단일 PC 운영 가정을 깨는 변경은 사용자 승인 없이 도입하지 않는다.

## 언어 및 문서 규칙
- 사용자용 문서와 핵심 설계 문서는 한국어를 먼저 작성한다.
- 모든 핵심 Markdown 파일은 영어 `AI / Engineering Version (English)` 섹션을 뒤에 둔다.
- 요구사항이 모호하면 멈추지 말고 가정을 기록하고 진행한다.
- 미해결 사항은 `Questions for Product Owner` 섹션에 기록한다.

## 단계 분리 규칙
- Phase 1에서는 로그인, 크롤러, 최종 판단 엔진, 근거 조항 출력 기능을 구현하지 않는다.
- Phase 1.5의 나라장터 게시판은 공공데이터 API 기반 조회/저장/첨부 다운로드/요약까지만 허용한다.
- Phase 1.5에서는 나라장터 HTML 크롤링, 최종 자격 판단, 근거 조항 출력, 법인-공고 자동 매칭을 구현하지 않는다.
- Phase 1.6에서는 Phase 2 이전에 법인 증빙자료 업로드, 자동 추출, 자동 분류, 사용자 확인 후 법인 프로필 업데이트를 구현한다.
- Phase 1.6은 `1.6A: 사업자등록증명/사업자등록증 기반 MVP`, `1.6B: 주요 증빙자료 확장`, `1.6C: 알 수 없는 증빙자료와 운영 안정화` 순서로 나눈다.
- Phase 1.6에서는 최종 자격 판단이나 기준문서 RAG를 구현하지 않는다.
- Phase 2에서는 기준문서 업로드/청킹/인덱싱까지만 구현한다.
- Phase 3 이전에는 자격 판단 결과를 확정 기능처럼 노출하지 않는다.

## 아키텍처 가드레일
- 일반 업로드 문서와 기준문서는 반드시 분리된 도메인으로 유지한다.
- 나라장터 저장 공고는 MVP에서 프로젝트 문서와 분리된 도메인으로 유지한다.
- 모든 일반 업로드 문서는 프로젝트에 속해야 한다.
- 기준문서는 프로젝트 소속이 아닌 재사용 가능한 지식 자산이다.
- 나라장터 API 키 전체 값은 프론트엔드 응답, 로그, 문서에 노출하지 않는다.
- 파싱, OCR, 요약, 청킹, 인덱싱은 분리된 서비스/파이프라인으로 유지한다.
- Phase 1.6은 현재 Flask 백엔드 구조에서 구현하고, FastAPI 마이그레이션을 섞지 않는다.
- 백엔드와 OCR 런타임 표준은 Python 3.13.13이며 Windows에서는 `py -3.13` 또는 `C:\Python313\python.exe`를 사용한다.
- OCR은 특정 엔진에 직접 결합하지 말고 어댑터로 추상화한다.
- OCR 주 엔진은 PaddleOCR PP-OCRv5로 두고, Tesseract는 경량 fallback 후보로만 둔다.
- PaddleOCR 구현은 Python 3.13.13 런타임에서 우선 검증한다.
- OCR 엔진이 설치되지 않은 환경에서도 업로드/분석 플로우가 실패하면 안 되며 `needs_ocr_setup` 또는 `unavailable` 상태로 degrade 해야 한다.
- LLM 기반 증빙자료 분류는 API 키가 있을 때만 실행하고, 결과는 사용자 검토 후보로만 저장한다.
- 민감한 법인/개인 식별 정보는 로그에 원문으로 남기지 않는다.
- 향후 인증 추가를 위해 사용자 컨텍스트를 주입할 수 있는 구조를 유지한다.
- 향후 크롤러 확장을 위해 `source_type` 확장 가능성을 열어둔다.

## 코드 구성 규칙
- 프론트엔드
  - `pages/`: 라우트 레벨 화면
  - `features/`: 사용자 액션 중심 기능
  - `entities/`: 도메인 모델 관련 UI/상태
  - `shared/`: 공통 컴포넌트, 유틸, API 클라이언트
- 백엔드
  - `api/`: 라우트
  - `models/`: ORM 엔티티
  - `schemas/`: 요청/응답 스키마
  - `services/`: 비즈니스 로직
  - `repositories/`: DB 접근
  - `pipelines/`: 파싱/OCR/요약/청킹/인덱싱 흐름

## 깨면 안 되는 가정
- Phase 1은 단일 관리자, 무인증, 단일 PC 운영이다.
- 일반 업로드 지원 포맷은 PDF와 DOCX만 허용한다.
- HWP는 구현 범위가 아니다.
- 기준문서는 PDF만 허용한다.
- 사용자가 수동으로 문서를 청킹하는 UX를 만들지 않는다.

## 기준문서 파이프라인 규칙
- 기준문서 업로드 시 자동으로 텍스트 추출 -> OCR -> 정규화 -> 청킹 -> 인덱싱을 수행한다.
- 청크에는 문서 버전, 카테고리, 페이지, 섹션 메타데이터를 남긴다.
- 재처리 시 이전 결과를 안전하게 교체해야 하며 무단 파괴하면 안 된다.
- 향후 citation 가능한 구조를 유지한다.

## 미래 확장 규칙
- 인증 추가를 막는 하드코딩 금지
- 수동 업로드와 크롤러 수집 문서가 동일한 하위 분석 파이프라인을 사용할 수 있어야 한다.
- 미래 판단 결과는 근거와 불확실성 노트를 함께 출력할 수 있어야 한다.
- 미래 판단 엔진은 `지원 가능`을 쉽게 출력하지 말고, 부족 조건/필요 인증/필요 서류/준비 가이드를 핵심 결과로 다룬다.
- 법인 프로필 입력값과 법인 증빙자료는 분리하되, 판단 시 서로 연결할 수 있어야 한다.
- 법인 등록 UX는 사업자등록증 업로드와 자동 추출을 먼저 제공하고, 사업자등록증이 없을 때만 직접 입력으로 fallback한다.
- 사업자등록증 외 증빙자료도 업로드 후 자동 분류/추출하고, 사용자가 승인한 값만 법인 프로필에 반영한다.
- 알 수 없는 증빙자료는 LLM으로 분류하되 자동 확정하지 않고 `확인 필요` 상태로 둔다.
- 기준문서 citation이 없는 조건은 확정 판단 근거로 사용하지 않는다.
- AI 출력은 가능하면 구조화 스키마를 우선 사용한다.

## 현재 구현 상태 메모
최종 갱신일: 2026-06-07

- Phase 2.5/Phase 3/Phase 4의 핵심 MVP는 현재 코드에 구현되어 있다.
- 현재 PDF reader 기본값은 OpenDataLoader 우선 `auto` 모드이며 PyMuPDF는 fallback/OCR 보조 엔진이다.
- 기준문서 검색 source는 JSON basis index 운영 산출물이다.
- 문서/계획 최신 해석은 `README.md`, `docs/technical-design.md`, `docs/technology-summary.md`, `docs/current-code-documentation-audit.md`, `docs/work-log.md`를 우선한다.
- 이 파일의 Phase guardrail은 새 기능을 추가할 때 도메인 경계를 지키기 위한 운영 규칙으로 유지한다.

## 구현 우선순위 원칙
1. 데이터 모델 정확성
2. 업로드/분석 파이프라인 안정성
3. 관리자 UX 명확성
4. 미래 확장성
5. 성능 최적화

---

# AI / Engineering Version (English)

## Purpose
Guide Codex and future AI coding agents to preserve phase-correct architecture, documentation rules, and extensibility.

## Repository Conventions
- keep `frontend/` and `backend/` separated
- keep design docs under `docs/`
- verify target phase before implementation
- do not break local single-PC assumptions without approval

## Language / Documentation Rules
- stakeholder-facing markdown starts in Korean
- then add `AI / Engineering Version (English)`
- proceed with assumptions when ambiguous
- log unresolved items under `Questions for Product Owner`

## Phase Guardrails
- no auth, crawler, final judgment, or evidence rendering in phase 1
- phase 1.6 introduces corporation evidence upload, extraction, classification, and reviewed profile enrichment before phase 2
- phase 1.6 must be delivered as 1.6A business-registration evidence MVP, 1.6B core evidence expansion, and 1.6C unknown evidence / operational hardening
- phase 1.6 must not implement final eligibility judgment or basis-document RAG
- phase 2 is basis ingestion/chunking/indexing only
- phase 3 introduces crawler and final judgment engine

## Architecture Guardrails
- separate project documents from basis documents
- every target document belongs to a project
- basis documents are reusable knowledge assets
- keep parsing, OCR, summarization, chunking, and indexing separated
- implement phase 1.6 on the current Flask backend and do not mix it with a FastAPI migration
- standardize backend and OCR runtime on Python 3.13.13; on Windows use `py -3.13` or `C:\Python313\python.exe`
- keep OCR behind an adapter
- use PaddleOCR PP-OCRv5 as the primary OCR engine and keep Tesseract as a lightweight fallback candidate
- validate PaddleOCR first on the Python 3.13.13 runtime
- missing OCR dependencies must not break upload/analysis flows; return `needs_ocr_setup` or `unavailable`
- run LLM evidence classification only when an API key is configured, and save output as review candidates only
- do not log sensitive corporation or personal identifiers in raw form
- preserve future `source_type` extensibility

## Do-Not-Break Assumptions
- single admin only in phase 1
- no auth in phase 1
- PDF/DOCX only for target documents
- PDF only for basis documents
- no manual chunking UX

## Basis Pipeline Rules
- basis ingestion must auto-run extract -> OCR -> normalize -> chunk -> index
- chunk metadata must contain version/category/page/section context
- reprocessing should replace safely with traceability

## Future Extensibility Rules
- keep auth-ready seams
- keep manual and crawler ingestion compatible downstream
- future judgment must support evidence citations and uncertainty notes
- future judgment must focus on missing requirements, required certifications/documents, and preparation guidance rather than optimistic eligibility
- corporation profile fields and corporation evidence documents must remain separate but linkable
- corporation onboarding should start with business registration certificate upload and automatic extraction, falling back to manual entry only when the certificate is unavailable
- non-registration evidence documents should also be uploaded, classified, extracted, and applied only after user review
- unknown evidence documents may use LLM classification, but must remain `needs_review` until confirmed
- requirements without basis-document citations must not be used as final decision evidence

## Phase 1.5 Nara Board Rules
- API-based Nara board ingestion is allowed before Phase 3.
- Do not implement HTML crawling in Phase 1.5.
- Saved Nara notices are separate from project documents unless the user explicitly asks to link them.
- Download and analyze PDF/DOCX attachments only.
- Store HWP/HWPX/XLSX as unsupported attachment metadata.
- Do not expose eligibility verdicts before the judgment engine phase.
- Nara API settings screens may show configured status and masked keys only; never return full keys to the frontend.

## Current Implementation Note
Last updated: 2026-06-07

- Core Phase 2.5, Phase 3, and Phase 4 MVP scope is implemented in the current code.
- Default PDF reader is OpenDataLoader-first `auto` mode; PyMuPDF remains fallback/OCR helper.
- Basis retrieval source is the operational JSON basis index.
- Prefer `README.md`, `docs/technical-design.md`, `docs/technology-summary.md`, `docs/current-code-documentation-audit.md`, and `docs/work-log.md` for current interpretation.
- The phase guardrails in this file remain architecture rules for future changes.
