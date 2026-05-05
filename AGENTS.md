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
- Phase 2에서는 기준문서 업로드/청킹/인덱싱까지만 구현한다.
- Phase 3 이전에는 자격 판단 결과를 확정 기능처럼 노출하지 않는다.

## 아키텍처 가드레일
- 일반 업로드 문서와 기준문서는 반드시 분리된 도메인으로 유지한다.
- 나라장터 저장 공고는 MVP에서 프로젝트 문서와 분리된 도메인으로 유지한다.
- 모든 일반 업로드 문서는 프로젝트에 속해야 한다.
- 기준문서는 프로젝트 소속이 아닌 재사용 가능한 지식 자산이다.
- 나라장터 API 키 전체 값은 프론트엔드 응답, 로그, 문서에 노출하지 않는다.
- 파싱, OCR, 요약, 청킹, 인덱싱은 분리된 서비스/파이프라인으로 유지한다.
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
- AI 출력은 가능하면 구조화 스키마를 우선 사용한다.

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
- phase 2 is basis ingestion/chunking/indexing only
- phase 3 introduces crawler and final judgment engine

## Architecture Guardrails
- separate project documents from basis documents
- every target document belongs to a project
- basis documents are reusable knowledge assets
- keep parsing, OCR, summarization, chunking, and indexing separated
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

## Phase 1.5 Nara Board Rules
- API-based Nara board ingestion is allowed before Phase 3.
- Do not implement HTML crawling in Phase 1.5.
- Saved Nara notices are separate from project documents unless the user explicitly asks to link them.
- Download and analyze PDF/DOCX attachments only.
- Store HWP/HWPX/XLSX as unsupported attachment metadata.
- Do not expose eligibility verdicts before the judgment engine phase.
- Nara API settings screens may show configured status and masked keys only; never return full keys to the frontend.
