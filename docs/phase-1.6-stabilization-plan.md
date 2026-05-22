# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`의 Phase 1.6, 즉 `법인 증빙자료 자동 추출과 법인 프로필 보강` 기능을 Phase 2 개발 전에 안정화하기 위한 실행 계획입니다.

Phase 1.6의 목표는 최종 지원 가능성 판단이 아닙니다. 목표는 법인 증빙자료를 안정적으로 업로드하고, OCR/파싱/AI 정리를 통해 법인 프로필 후보값을 만들고, 사용자가 검토한 값만 안전하게 반영하는 것입니다.

## 현재 구현 기준
현재 코드와 작업 로그 기준으로 다음 기능은 이미 구현된 상태로 봅니다.

- 법인 증빙자료 업로드
- PDF/DOCX/JPG/JPEG/PNG 증빙자료 처리
- PaddleOCR 기반 OCR 어댑터
- 사업자등록증/사업자등록증명 기본정보 추출
- 주요 증빙자료 규칙 기반 분류/후보 추출
- 알 수 없는 증빙자료 LLM 분류 fallback
- 후보값 체크/수정/선택 반영 UX
- 법인 준비도 카드
- 사업자등록번호 + 관리 법인그룹 중복 정책
- 전역 처리중 오버레이 UX

## 진행 상태
- `2026-05-22`: 기준 상태 점검을 수행했고 백엔드 전체 테스트와 프론트엔드 빌드가 통과했다.
- `2026-05-22`: 사업자등록증 `사업의 종류` 표에서 `업태`, `종목` 라벨이 줄 단위로 깨지거나 LLM 결과에 섞이는 경우를 방어하도록 후처리 로직을 강화했다.
- `2026-05-22`: Gemini/OpenAI LLM 정리 결과도 저장 전 `business_type`, `business_item`, `business_category` 형태로 다시 검증하도록 변경했다.
- `2026-05-22`: 관련 회귀 테스트를 추가했고, 전체 백엔드 테스트 기준은 `47 passed, 1 skipped`로 갱신되었다.
- `2026-05-22`: 법인 증빙자료 화면의 개발자용 상태값을 한국어 배지 라벨로 정리해 검토/재처리 UX의 가독성을 개선했다.
- `2026-05-22`: 사용자 제공 사업자등록증 이미지로 PaddleOCR opt-in 테스트를 실행했고, OCR 이후 업태/종목 후보 정리까지 통과하는지 확인했다.
- `2026-05-22`: 서버/스크립트 한글깨짐 방지를 위해 HTTP 응답 디코딩 fallback, Flask JSON 한글 출력, PowerShell UTF-8 출력, 인코딩 체크 스크립트를 추가했다.

## 안정화 목표
Phase 1.6 안정화의 핵심 목표는 다음입니다.

- 사용자가 증빙자료 업로드 후 현재 시스템이 무엇을 처리 중인지 명확히 알 수 있어야 한다.
- OCR/파싱 결과가 틀려도 사용자가 보정하고 다시 분석할 수 있어야 한다.
- 후보값은 사용자가 선택한 경우에만 법인 프로필에 반영되어야 한다.
- OCR/AI/API 키/파일 형식 문제가 있어도 전체 플로우가 중단되지 않아야 한다.
- 실제 증빙자료 샘플을 기준으로 회귀 테스트가 가능해야 한다.
- Phase 1.7의 `공고 요구조건 대 법인 부족조건 미리보기`로 자연스럽게 이어질 데이터 품질을 확보해야 한다.

## 비범위
이번 안정화에서 하지 않는 일입니다.

- 최종 `지원 가능/지원 곤란/검토 필요` 판정
- 기준문서 RAG
- 기준 PDF 청킹/벡터 인덱싱
- HWP/HWPX 직접 파싱
- 외부 기관 진위확인 API 연동
- 대규모 사용자/권한/로그인 체계

## 안정화 작업 묶음

### 1. 기준 상태 점검과 회귀 테스트 고정
현재 기능이 어느 수준까지 정상 동작하는지 기준선을 먼저 고정합니다.

작업:
- Phase 1.6 관련 API 목록 재점검
- 프론트엔드 증빙자료 플로우 전체 클릭 경로 점검
- 현재 테스트 목록 정리
- 실패해도 되는 선택 테스트와 반드시 통과해야 하는 테스트 분리
- 실제 샘플 파일은 Git에 넣지 않고 `backend/storage/ocr-samples/` 또는 로컬 전용 경로로 관리

완료 기준:
- `py -3.13 -m unittest discover -s tests -v` 통과
- `npm run build` 통과
- `scripts/smoke-test.ps1` 통과
- OCR 선택 테스트의 skip/pass 조건이 문서화됨

### 2. OCR/파싱 안정화
사업자등록증 이미지처럼 레이아웃이 있는 문서에서 OCR 결과가 줄 단위로 깨지는 문제를 줄입니다.

작업:
- PaddleOCR 결과를 단순 문자열이 아니라 좌표/라인 그룹 기준으로 후처리
- 사업자등록증의 `사업의 종류`, `업태`, `종목` 영역 전용 정리 로직 강화
- OCR confidence가 낮은 줄은 후보값으로 자동 확정하지 않음
- 한글 경로, 공백 포함 경로, 긴 파일명 처리 재검증
- OCR 엔진 미설치 시 `OCR 설정 필요` 상태와 수동 보정 UX 유지

완료 기준:
- 사용자 제공 사업자등록증 이미지에서 법인명, 사업자등록번호, 대표자명, 주소, 업태/종목 후보가 분리되어 표시됨
- 업태/종목이 한 줄로 뭉치거나 엉뚱한 필드에 들어가는 케이스가 줄어듦
- OCR 실패 시 파일은 저장되고 사용자가 수동 보정할 수 있음

### 3. AI 정리 단계 안정화
OCR이 텍스트를 대략 읽더라도 업태/종목, 면허, 증빙 종류는 사람이 읽기 좋은 구조로 다시 정리해야 합니다.

작업:
- 사업자등록증 OCR 결과를 LLM으로 정리하는 프롬프트와 JSON 스키마 고정
- LLM 결과 검증 로직 강화
- 지원하지 않는 필드명, 빈 값, 과도한 추론값은 저장하지 않음
- Gemini/OpenAI 모두 동일 스키마로 동작하는지 확인
- API 키가 없거나 호출 실패 시 규칙 기반 후보 + 수동 보정으로 degrade

완료 기준:
- `business_type`, `business_item`, `business_category` 후보가 명확히 구분됨
- LLM 결과는 항상 후보값이며 자동 확정되지 않음
- API 오류가 사용자 작업 전체를 실패시키지 않음

### 4. 후보값 반영 안전성 강화
가장 중요한 안정화 축입니다. 잘못된 OCR 후보가 기존 법인 정보를 덮어쓰면 안 됩니다.

작업:
- 선택한 후보만 반영되는지 재검증
- 선택하지 않은 후보의 상태와 이력을 보존
- 기존값과 추출값이 다를 때 충돌 배지 표시
- 핵심 식별 필드 보호
  - 법인명
  - 사업자등록번호
  - 대표자명
  - 주소
- 보조 증빙자료가 핵심 식별 필드를 덮어쓰지 않도록 UX/백엔드 가드 추가

완료 기준:
- `candidate_ids: []`가 전체 승인으로 처리되지 않음
- 사용자가 체크한 후보만 법인 프로필에 반영됨
- 수정 입력값이 원본 추출값보다 우선 적용됨
- 충돌 후보는 사용자가 명시적으로 선택해야만 반영됨

### 5. 증빙자료 상태와 재처리 UX 정리
사용자가 업로드 이후에도 증빙자료를 관리할 수 있어야 합니다.

작업:
- 상태값 표준화
  - `uploaded`
  - `extracting`
  - `ocr_processing`
  - `needs_review`
  - `ai_suggested`
  - `approved`
  - `failed`
  - `ocr_setup_required`
- 재처리 버튼의 동작 명확화
- 보정 텍스트 재분석 결과가 기존 pending 후보를 어떻게 대체하는지 정책 고정
- 삭제 시 원본 파일, 추출 텍스트, 후보값 정리 범위 점검

완료 기준:
- 사용자가 상태만 보고 다음 행동을 알 수 있음
- 재처리 후 오래된 후보와 새 후보가 혼동되지 않음
- 삭제 후 고아 파일/고아 후보가 남지 않음

### 6. UX 사용성 안정화
증빙자료 기능은 비전문 사용자가 쓰기 때문에 `지금 뭘 해야 하는지`가 아주 중요합니다.

작업:
- 업로드 전 안내 문구 개선
- 처리중 오버레이 문구를 실제 단계와 맞춤
- OCR 실패/AI 키 없음/지원 제외 파일에 대한 친절한 안내 추가
- `사업자등록증 없음` 수동 입력 fallback 흐름 점검
- 후보 검토 화면에서 `기존값`, `추출값`, `수정값`, `반영 여부`를 더 명확히 표시

완료 기준:
- 업로드 후 사용자가 기다려야 하는지, 수정해야 하는지, 반영해야 하는지 바로 이해 가능
- 에러 메시지가 개발자용 문구가 아니라 업무용 문구로 표시됨
- 수동 fallback으로도 법인 등록이 가능함

### 7. 데이터 무결성/보안 안정화
로컬 단일 PC라도 사업자등록번호, 대표자명, 주소는 민감 정보로 봐야 합니다.

작업:
- 로그에 민감 정보 원문이 찍히지 않는지 점검
- 프론트 목록에서 사업자등록번호 마스킹 정책 검토
- DB 마이그레이션/스키마 보정 로직 재실행 안전성 확인
- 같은 사업자등록번호 + 같은 관리그룹 중복 차단 재검증
- 같은 사업자등록번호 + 다른 관리그룹 warning 재검증

완료 기준:
- 중복 정책이 수동 등록, 수정, 증빙 승인 생성 흐름에 모두 동일 적용됨
- 민감 정보가 불필요하게 로그/오류 메시지에 노출되지 않음
- 기존 SQLite 파일에서도 스키마 보정이 안전하게 실행됨

### 8. 샘플 기반 품질 튜닝
지금부터는 실제 샘플이 품질을 결정합니다.

권장 샘플:
- 사업자등록증 이미지
- 사업자등록증명 PDF
- 중소기업확인서 PDF
- 여성기업확인서 PDF
- 직접생산확인증명서 PDF
- 나라장터 경쟁입찰참가자격 등록증 PDF
- 면허/등록증 PDF
- 납세증명서 PDF
- 실적증명서 PDF

샘플 관리 원칙:
- 민감 파일은 Git에 커밋하지 않음
- 테스트용 익명화 샘플은 별도 fixture로 제작 가능
- 실제 샘플 테스트는 환경변수로 opt-in 실행

완료 기준:
- 최소 5종 이상 증빙자료에 대한 회귀 테스트 또는 수동 QA 체크리스트 확보
- 사업자등록증 이미지는 실제 OCR 테스트 경로로 재현 가능
- 주요 추출 실패 케이스가 문서화됨

## 권장 개발 순서

### Step 1. 안정화 기준선 확정
- 테스트 전체 실행
- 현재 증빙자료 플로우 수동 점검
- 실패/불편/불명확 지점 목록화

### Step 2. 사업자등록증 OCR + LLM 정리 개선
- 업태/종목 분리 개선
- 사업자등록증 전용 후처리 강화
- LLM JSON 검증 강화
- 테스트 추가

### Step 3. 후보 반영/충돌/이력 안정화
- 선택 후보만 반영 보장
- 충돌 표시와 핵심 필드 보호 강화
- 재처리 시 후보 교체 정책 정리

### Step 4. UX 문구와 상태 표시 정리
- 오버레이 단계 문구 정리
- 실패/수동 fallback 안내 정리
- 증빙자료 목록 상태 배지 정리

### Step 5. 샘플 기반 회귀 테스트 확장
- 실제 샘플 opt-in 테스트
- mock 기반 필수 단위 테스트
- 스모크 테스트에 증빙자료 핵심 경로 추가 검토

### Step 6. Phase 1.6 종료 리뷰
- 코드 리뷰
- 테스트 결과 정리
- 남은 이슈를 Phase 1.7 또는 Phase 2로 이관

## Phase 1.6 안정화 완료 기준
아래 항목이 충족되면 Phase 1.6 안정화를 완료로 봅니다.

- 사업자등록증 이미지/PDF 업로드 후 법인 기본정보 후보가 생성된다.
- 업태/종목 후보가 사용자가 이해할 수 있는 형태로 정리된다.
- 후보값은 체크/수정/선택 반영을 거쳐야만 법인 프로필에 반영된다.
- OCR 또는 LLM 실패 시에도 수동 보정/수동 입력 흐름이 제공된다.
- 증빙자료 목록, 상세, 재처리, 삭제가 안정적으로 동작한다.
- 중복 법인 정책이 모든 생성/수정 경로에서 동일하게 적용된다.
- 민감 정보가 로그와 화면에 과도하게 노출되지 않는다.
- 백엔드 테스트, 프론트 빌드, 스모크 테스트가 통과한다.

## 테스트 계획

### 백엔드 테스트
- 사업자등록증 필드 추출
- 업태/종목 분리
- 빈 텍스트에서 후보 생성 금지
- LLM 분류 mock
- 후보 선택 반영
- 후보 수정값 우선 반영
- 중복 법인 차단/warning
- 증빙자료 재처리
- 증빙자료 삭제
- OCR 미설치 fallback

### 프론트엔드 확인
- 증빙자료 업로드 오버레이 표시
- 업로드 후 검토 탭 이동
- 후보 체크/해제/수정
- 재처리 버튼
- 보정 텍스트 재분석
- 삭제 확인
- 수동 등록 fallback
- 에러 상태 메시지

### 통합/스모크 테스트
- 법인 증빙자료 업로드 -> 후보 생성 -> 선택 반영 -> 법인 준비도 갱신
- OCR 미설치 상태 -> 파일 저장 -> 수동 보정 가능
- AI 키 없음 상태 -> 규칙 기반 후보 또는 확인 필요 상태 유지

## 위험과 대응
- OCR 품질이 샘플마다 크게 다를 수 있음
  - 대응: OCR 후처리 + LLM 정리 + 수동 보정 UX를 함께 유지
- LLM이 없는 정보를 추론할 수 있음
  - 대응: 스키마 검증, 지원 필드 whitelist, 자동 반영 금지
- 보조 증빙자료가 핵심 법인정보를 덮어쓸 수 있음
  - 대응: 핵심 필드 충돌 가드와 명시 선택 반영
- 실제 샘플에 개인정보가 많음
  - 대응: Git 제외, opt-in 테스트, 로그 마스킹
- Phase 2/RAG 욕심으로 안정화 범위가 커질 수 있음
  - 대응: 최종 판단과 기준문서 RAG는 Phase 1.6 안정화 비범위로 유지

## Questions for Product Owner
- 사업자등록증 `업태/종목`은 원문 그대로 저장할지, AI가 정리한 대표 업종/키워드도 별도 저장할지?
- 증빙자료 후보 중 법인명/대표자/주소처럼 민감한 핵심 필드는 기본 선택 상태로 둘지, 항상 사용자가 직접 체크하게 할지?
- 실제 증빙자료 샘플을 몇 종까지 확보한 뒤 Phase 1.6을 종료로 볼지?
- OCR 품질이 부족한 이미지에 외부 Vision API 사용을 허용할지?
- 스모크 테스트에 실제 OCR 경로를 포함할지, opt-in 선택 테스트로만 둘지?

---

# AI / Engineering Version (English)

## Purpose
This document defines the stabilization plan for Phase 1.6: corporation evidence auto-extraction and corporation profile enrichment.

The goal is not final eligibility judgment. The goal is to make evidence upload, OCR/parsing, AI cleanup, candidate review, and safe profile updates reliable enough before Phase 2 basis-document/RAG work starts.

## Current Implementation Baseline
The following capabilities are considered implemented and subject to stabilization:

- corporation evidence upload
- PDF/DOCX/JPG/JPEG/PNG evidence handling
- PaddleOCR-based OCR adapter
- business registration proof/certificate extraction
- rule-based evidence classification and candidate extraction
- unknown evidence LLM fallback classification
- checkbox/edit/apply candidate review UX
- corporation readiness cards
- duplicate policy using `business_registration_number + management_group_name`
- global blocking processing overlay

## Progress
- `2026-05-22`: Established the regression baseline; backend tests and frontend build passed.
- `2026-05-22`: Hardened business-registration `business kind` cleanup when OCR splits table labels or suffixes across lines.
- `2026-05-22`: Added a sanitization layer for Gemini/OpenAI business-kind cleanup output before it becomes review candidates.
- `2026-05-22`: Added regression coverage; backend baseline is now `47 passed, 1 skipped`.
- `2026-05-22`: Replaced raw developer-facing evidence statuses with Korean badge labels in the corporation evidence UI.
- `2026-05-22`: Ran the user-provided business-registration sample image through the opt-in PaddleOCR test and verified post-OCR business type/item extraction.
- `2026-05-22`: Added encoding hardening: HTTP decode fallback, non-ASCII Flask JSON output, PowerShell UTF-8 output setup, and a repository encoding check script.

## Stabilization Goals
- Processing state must be clear to the user.
- OCR/parser errors must be recoverable through manual correction and re-analysis.
- Only selected candidates may update the corporation profile.
- OCR/AI/API/file-format failures must not break the whole flow.
- Real evidence samples should drive regression testing.
- Data quality should be sufficient to support Phase 1.7 gap-preview work.

## Non-Scope
- final eligibility judgment
- basis-document RAG
- basis PDF chunking/vector indexing
- HWP/HWPX direct parsing
- external official verification APIs
- multi-user auth/permission system

## Workstreams

### 1. Baseline And Regression Tests
- Review all Phase 1.6 APIs and frontend paths.
- Separate mandatory tests from optional OCR tests.
- Keep real sensitive samples outside Git.
- Ensure backend tests, frontend build, and smoke test pass.

### 2. OCR / Parsing Reliability
- Post-process PaddleOCR output by line grouping and coordinates.
- Harden business registration table cleanup, especially `business_type` and `business_item`.
- Do not auto-confirm low-confidence OCR lines.
- Recheck Korean paths, spaces, and long file names.
- Preserve manual fallback when OCR is unavailable.

### 3. AI Cleanup Reliability
- Stabilize prompts and JSON schema for business-registration OCR cleanup.
- Validate Gemini/OpenAI outputs through one schema.
- Reject unsupported fields, empty values, and over-inferred data.
- Degrade to rule-based candidates and manual correction when API calls fail.

### 4. Candidate Application Safety
- Reconfirm selected-candidates-only behavior.
- Preserve unselected candidates as pending.
- Show conflicts for changed core fields.
- Protect core identity fields from accidental overwrite.

### 5. Evidence Status And Reprocessing UX
- Standardize statuses: `uploaded`, `extracting`, `ocr_processing`, `needs_review`, `ai_suggested`, `approved`, `failed`, `ocr_setup_required`.
- Clarify reprocess behavior.
- Define how corrected-text reanalysis replaces pending candidates.
- Check cleanup behavior on deletion.

### 6. UX Stabilization
- Improve pre-upload guidance.
- Match overlay step labels to real backend stages.
- Improve errors for OCR missing, AI key missing, and unsupported files.
- Recheck manual fallback flow.
- Make existing/extracted/edited/applied values easy to distinguish.

### 7. Data Integrity And Privacy
- Mask or avoid raw sensitive values in logs.
- Review business registration number masking in UI.
- Ensure schema migration helpers are idempotent.
- Revalidate same-group duplicate block and other-group duplicate warning.

### 8. Sample-Based Tuning
Recommended samples:
- business registration image
- business registration proof PDF
- SME confirmation
- women-owned business confirmation
- direct production confirmation
- Nara bidding participant registration
- license/registration certificate
- tax payment certificate
- performance certificate

Sample rules:
- never commit sensitive original samples
- use anonymized fixtures where possible
- run real samples only through opt-in tests

## Recommended Implementation Order
1. Establish the current regression baseline.
2. Improve business-registration OCR and LLM cleanup, especially business type/item extraction.
3. Harden candidate application, conflict handling, and reprocessing behavior.
4. Improve status labels, overlay copy, and fallback UX.
5. Expand sample-based regression tests.
6. Run a Phase 1.6 closeout review and move remaining items to Phase 1.7 or Phase 2.

## Done Criteria
- Business registration image/PDF upload creates usable corporation profile candidates.
- Business type/item candidates are human-readable and separated.
- Profile updates require explicit checkbox/edit/apply review.
- OCR or LLM failure still allows manual correction/manual fallback.
- Evidence list/detail/reprocess/delete work reliably.
- Duplicate policy applies consistently to all create/update paths.
- Sensitive values are not overexposed in logs or UI.
- Backend tests, frontend build, and smoke test pass.

## Test Plan

Backend:
- business registration field extraction
- business type/item splitting
- empty-text candidate guard
- LLM classification mock
- selected candidate application
- edited value precedence
- duplicate block/warning
- evidence reprocess
- evidence delete
- OCR unavailable fallback

Frontend:
- evidence upload overlay
- review-tab transition
- candidate select/unselect/edit
- reprocess action
- corrected-text reanalysis
- delete action
- manual fallback
- error-state copy

Integration:
- evidence upload -> candidates -> selected apply -> readiness refresh
- OCR unavailable -> stored evidence -> manual correction
- missing AI key -> rule-based/needs-review flow remains usable

## Risks
- OCR quality varies by sample.
- LLM may infer unsupported facts.
- supplemental evidence can accidentally overwrite core profile fields.
- real evidence samples contain sensitive information.
- Phase 2/RAG scope can creep into stabilization.

## Questions for Product Owner
- Should business type/items store both original text and AI-cleaned representative keywords?
- Should sensitive core fields be selected by default or require explicit user selection?
- How many real evidence sample categories are required before Phase 1.6 can close?
- Is external Vision API allowed if local OCR quality is insufficient?
- Should real OCR be part of smoke tests or remain opt-in only?
