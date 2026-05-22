# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`의 Phase 1.7 기능인 `부족조건 미리보기`를 실제 운영에 가까운 수준으로 안정화하기 위한 실행 계획입니다.

Phase 1.7은 최종 지원 가능/불가능 판단 엔진이 아닙니다. 목표는 저장된 나라장터 공고의 요구조건 후보와 사용자가 관리하는 법인 프로필/증빙자료를 비교해, 현재 법인이 무엇을 준비했고 무엇이 부족할 가능성이 있는지 빠르게 확인하도록 돕는 것입니다.

## 현재 구현 기준
현재 코드 기준으로 Phase 1.7은 다음 기능까지 구현되어 있습니다.

- 저장한 나라장터 공고의 요구조건 후보를 `notice_requirement_candidates` 테이블에 저장
- 저장 공고 분석 완료 시 요구조건 후보 자동 생성
- 요구조건 후보 조회 및 재추출 API 제공
- 법인 프로필을 비교용 구조로 정규화하는 API 제공
- 공고 요구조건 후보와 법인 준비상태를 rule-based 방식으로 비교
- 비교 결과를 `notice_corporation_comparisons` 테이블에 저장
- 비교 결과 전체 이력, 상세 조회, 공고별 이력 조회 API 제공
- 요구조건 재추출 시 기존 비교 결과 무효화
- 포탈에 `부족조건 미리보기` 메뉴와 화면 추가
- 공고 선택, 법인 선택, 요구조건 후보 확인, 법인 비교 프로필 확인, 비교 실행, 최근 비교 이력 UX 제공

## 안정화 목표
Phase 1.7 안정화의 목표는 다음과 같습니다.

- 공고 요구조건 후보가 실제 나라장터 공고문에서 더 일관되게 추출되도록 한다.
- 법인 프로필과 승인된 증빙자료가 비교 엔진에 안정적으로 반영되도록 한다.
- 비교 결과가 최종 판정으로 오해되지 않도록 UX와 문구를 명확하게 한다.
- 재분석, 재추출, 삭제, 이력 조회 시 stale 데이터가 남지 않도록 한다.
- 실제 샘플 공고와 실제 법인 증빙자료 기준의 회귀 테스트 체계를 만든다.
- Phase 2 기준문서/RAG와 Phase 3 최종 판단 엔진으로 확장 가능한 구조를 유지한다.

## 이번 안정화에서 하지 않는 것
아래 항목은 Phase 1.7 안정화 범위가 아닙니다.

- 최종 `지원 가능`, `지원 불가능`, `검토 필요` 판정
- 기준문서 RAG 검색 결과를 비교 결과에 결합
- 근거 조항 citation 출력
- 체크리스트/준비 가이드의 최종 자동 생성
- 나라장터 HTML 크롤링
- 로그인/권한 기능
- HWP/HWPX 직접 파싱

## 핵심 원칙
1. 최종 판정처럼 보이지 않게 한다.
2. 불확실한 항목은 `확인 필요` 또는 `부족 가능성`으로 남긴다.
3. 법인 프로필 값보다 승인된 증빙자료를 더 신뢰한다.
4. 사용자 승인 없이 법인 정보를 자동 수정하지 않는다.
5. 요구조건 재추출이나 공고 재분석 후 기존 비교 결과는 반드시 무효화한다.
6. 기준문서 citation이 없는 결과는 향후에도 최종 판단 근거로 쓰지 않는다.

## 안정화 작업 묶음

### 1. 요구조건 후보 추출 안정화
현재 요구조건 추출은 rule-based 후보 추출 중심입니다. 실제 공고문에서 자주 나오는 표현을 더 잘 잡도록 보강합니다.

작업:
- 지역 제한 표현 보강
  - 예: `전라남도`, `전남`, `해남군`, `주된 영업소`, `소재 업체`
- 면허/업종 표현 보강
  - 예: `조경식재·시설물공사업`, `전기공사업`, `정보통신공사업`, `산림사업법인`
- 기업유형 표현 보강
  - 예: `중소기업`, `소기업`, `소상공인`, `여성기업`, `장애인기업`
- 제출서류 표현 보강
  - 예: `입찰참가자격 등록증`, `직접생산확인증명서`, `납세증명서`, `실적증명서`
- 공고 메타데이터와 첨부 PDF 추출 텍스트 간 중복 제거 기준 개선
- 요구조건 후보별 `source_text`를 더 설명적으로 저장
- 추출 confidence 기준과 label을 정리

완료 기준:
- 대표 샘플 공고 5건 이상에서 지역/면허/기업유형/서류 후보가 누락 없이 대부분 추출된다.
- 최종 판정 표현이 추출 결과 JSON/화면에 포함되지 않는다.
- 재추출 API를 반복 실행해도 중복 후보가 늘어나지 않는다.

### 2. 법인 비교 프로필 정규화 안정화
법인 입력값과 승인된 증빙자료를 비교 엔진이 잘 이해하도록 정규화합니다.

작업:
- 법인 기본 필드와 증빙자료 필드의 우선순위 정리
- 사업자등록증 기반 업태/종목 값을 면허/업종 비교 버킷에 안정적으로 반영
- 중소기업확인서, 직접생산확인증명서, 나라장터 등록증, 면허증 등 승인 증빙을 `required_documents` 버킷에 반영
- `certifications_json`, `preference_tags_json`, `direct_production_items_json` 파싱 기준 통일
- 지역 비교 시 주소에서 광역/기초 지자체 후보를 분리
- 같은 값이 여러 필드에 있어도 비교 프로필에서는 중복 제거

완료 기준:
- 사업자등록증만 승인된 법인도 기본 비교 프로필이 생성된다.
- 승인 증빙자료가 있는 경우 비교 결과의 `준비된 항목`으로 반영된다.
- 법인 정보가 부족한 경우 `법인 정보 없음` 또는 `확인 필요`로 안전하게 표시된다.

### 3. 비교 엔진 안전성 개선
현재 rule-based 비교 엔진을 더 조심스럽고 설명 가능한 방식으로 안정화합니다.

작업:
- 완전 일치, 부분 일치, 동의어/약어 일치 기준을 분리
- `조경식재공사업` vs `조경식재·시설물공사업`처럼 유사하지만 다른 항목의 과잉 매칭 방지
- 지역 제한은 광역/기초 단위 매칭 기준을 별도 처리
- 금액/일정/원문 요구조건은 자동 충족 판단하지 않고 `확인 필요`로 유지
- 각 비교 항목에 `reason`, `matched_value`, `source_text`를 더 명확히 제공
- 비교 엔진 출력에 `eligible`, `not eligible`, `지원 가능`, `지원 불가능` 문구가 들어가지 않도록 테스트 강화

완료 기준:
- 자동 비교 결과가 낙관적으로 과잉 매칭되지 않는다.
- 사용자가 왜 `부족 가능성`인지, 왜 `준비된 항목`인지 화면에서 이해할 수 있다.
- 비교 결과는 항상 `preview_only` 성격을 유지한다.

### 4. 포탈 UX 안정화
사용자가 결과를 잘못 해석하지 않도록 화면 흐름과 문구를 다듬습니다.

작업:
- `부족조건 미리보기` 화면 상단에 “최종 판정 아님” 안내 고정
- 비교 결과 카드 순서 개선
  - 부족 가능성
  - 확인 필요
  - 법인 정보 없음
  - 준비된 항목
- 공고 요구조건 후보와 법인 비교 프로필을 나란히 확인할 수 있게 시인성 개선
- 비교 실행 후 저장된 이력임을 명확히 표시
- 요구조건 재추출 시 기존 비교 결과가 무효화된다는 안내 추가
- 데이터가 부족한 경우 다음 행동 안내
  - 법인 증빙자료 업로드
  - 저장 공고 재분석
  - 요구조건 다시 추출
- 모바일/작은 화면에서 비교 결과 카드가 한 열로 자연스럽게 표시되는지 확인

완료 기준:
- 사용자가 화면만 보고 “이것은 최종 지원 가능 여부가 아니라 부족조건 미리보기”임을 이해할 수 있다.
- 비교 결과에서 다음에 해야 할 행동이 명확하다.
- 빈 상태, 로딩 상태, 오류 상태가 모두 친절하게 표시된다.

### 5. 재분석/재추출/이력 무결성
공고 분석과 요구조건 재추출은 기존 비교 결과의 신뢰도에 영향을 줍니다.

작업:
- 저장 공고 재분석 시 기존 요구조건 후보와 비교 결과 무효화 확인
- 요구조건 재추출 시 기존 비교 결과 삭제 또는 stale 처리 기준 확정
- 저장 공고 삭제 시 요구조건 후보/비교 결과 같이 삭제
- 법인 삭제 또는 법인 정보 변경 시 기존 비교 이력 표시 정책 검토
- 비교 결과 조회 시 당시 사용한 법인 프로필 snapshot 저장 필요성 검토

완료 기준:
- 오래된 요구조건 후보 기반 비교 결과가 최신 결과처럼 보이지 않는다.
- 삭제된 공고/법인과 연결된 고아 비교 데이터가 남지 않는다.
- 비교 이력은 언제 생성된 결과인지 명확히 표시된다.

### 6. 테스트 및 샘플 QA 체계
실제 나라장터 공고와 법인 증빙자료를 기준으로 회귀 테스트를 강화합니다.

작업:
- rule-based 단위 테스트 추가
  - 지역 제한
  - 면허/업종
  - 기업유형
  - 제출서류
  - 중복 제거
- API 테스트 추가
  - 요구조건 재추출
  - 비교 생성
  - 비교 이력 조회
  - stale 무효화
  - 삭제 cascade
- 프론트 빌드와 스모크 테스트 유지
- 실제 샘플 공고 PDF는 Git에 직접 커밋하지 않고 로컬 opt-in 테스트 경로로 관리
- 샘플별 기대 추출 결과를 별도 JSON fixture로 관리할지 검토

완료 기준:
- 전체 백엔드 테스트 통과
- 프론트 빌드 통과
- 스모크 테스트 통과
- 대표 샘플 공고 최소 5건에 대한 수동 QA 결과 기록

### 7. 보안/개인정보/로그 점검
법인 정보와 증빙자료에는 민감 정보가 포함될 수 있습니다.

작업:
- 비교 결과/로그에 API 키 전체값이 노출되지 않는지 점검
- 사업자등록번호, 대표자명, 주소가 오류 로그에 과도하게 남지 않는지 점검
- 프론트 응답에서 필요한 정보만 내려오는지 확인
- 저장 파일 경로가 외부로 과도하게 노출되지 않는지 확인

완료 기준:
- API 키 전체값은 어디에도 노출되지 않는다.
- 민감 정보는 필요한 화면에서만 표시된다.
- 에러 메시지는 사용자가 이해할 수 있으면서도 원문 민감 정보를 과도하게 포함하지 않는다.

## 권장 개발 순서

### Step 1. 현재 기능 기준선 고정
- 전체 테스트 실행
- 실제 공고 2~3건으로 현재 부족조건 미리보기 결과 확인
- 문제 유형 분류

완료 기준:
- 현재 실패/불편/누락 항목 목록 확보

### Step 2. 요구조건 추출 보강
- 지역/면허/기업유형/서류 토큰 확장
- source_text와 confidence 개선
- 관련 단위/API 테스트 추가

완료 기준:
- 대표 샘플에서 요구조건 후보 누락 감소

### Step 3. 법인 비교 프로필 보강
- 승인 증빙자료 반영 범위 개선
- 주소/업종/인증/우대조건 정규화 개선
- 비교 프로필 API 테스트 추가

완료 기준:
- 법인 프로필이 비교 엔진에 안정적으로 전달됨

### Step 4. 비교 엔진 과잉 매칭 방지
- 부분 일치 기준 개선
- 애매한 항목은 `확인 필요`로 보내기
- 최종 판정 금지 테스트 추가

완료 기준:
- 낙관적 오판 가능성이 줄어듦

### Step 5. UX 문구와 화면 정리
- 최종 판정 아님 안내 강화
- 부족/확인 필요 중심으로 카드 순서 재배치
- 다음 행동 CTA 추가

완료 기준:
- 사용자가 비교 결과를 보고 바로 다음 행동을 알 수 있음

### Step 6. 이력/재실행 안정화
- 재분석/재추출/삭제 시 데이터 무결성 테스트 추가
- stale 결과 표시 정책 확정

완료 기준:
- 오래된 비교 결과가 최신처럼 보이지 않음

### Step 7. 최종 코드리뷰 및 회귀 테스트
- 백엔드 전체 테스트
- 프론트 빌드
- 스모크 테스트
- 인코딩 검사
- 브라우저 화면 확인

완료 기준:
- Phase 1.7 안정화 완료 판정 가능

## 테스트 명령
```powershell
cd D:\project\wisdom_procurement\backend
py -3.13 -m unittest discover -s tests -v
```

```powershell
cd D:\project\wisdom_procurement\frontend
npm run build
```

```powershell
cd D:\project\wisdom_procurement
py -3.13 scripts\check-encoding.py
powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1
git diff --check
```

## Phase 1.7 안정화 완료 기준
아래 조건을 만족하면 Phase 1.7 안정화를 완료로 봅니다.

- 실제 공고 샘플 기준 요구조건 후보 추출 품질이 수동 QA를 통과한다.
- 법인 증빙자료와 프로필 값이 비교 프로필에 안정적으로 반영된다.
- 비교 결과가 최종 지원 가능/불가능으로 오해되지 않는다.
- stale 비교 결과가 남지 않는다.
- 전체 백엔드 테스트, 프론트 빌드, 스모크 테스트가 통과한다.
- 작업 로그에 테스트 결과와 남은 이슈가 기록된다.

## Product Owner 확인 질문
- 실제 QA에 사용할 대표 나라장터 공고 샘플은 어떤 유형을 우선할까요?
- 비교 결과에서 가장 먼저 보여줄 항목은 `부족 가능성`이 맞을까요?
- 비교 결과를 PDF/Excel로 내보내는 기능은 Phase 1.8로 넘겨도 될까요?
- 법인 정보 변경 시 과거 비교 이력을 snapshot으로 유지할까요, 아니면 최신 법인 정보 기준으로만 다시 비교할까요?

---

# AI / Engineering Version (English)

## Purpose
This document defines the stabilization plan for Phase 1.7 `Gap Preview` in `SMART Procurement Calculator`.

Phase 1.7 is not the final eligibility judgment engine. It compares saved Nara notice requirement candidates against corporation profile/evidence readiness and helps the administrator identify likely missing conditions.

## Current Baseline
Implemented capabilities:

- persisted saved-notice requirement candidates in `notice_requirement_candidates`
- auto-generated candidates after saved-notice analysis
- requirement read/re-extract APIs
- corporation comparison-profile normalization API
- rule-based comparison between notice candidates and corporation readiness profile
- persisted comparison results in `notice_corporation_comparisons`
- global/detail/notice-specific comparison history APIs
- stale comparison invalidation on requirement re-extraction
- portal `Gap Preview` page and navigation

## Stabilization Goals
- improve consistency of requirement candidate extraction from real Nara notices
- make corporation profile/evidence normalization stable and explainable
- keep UX language clearly non-final and non-verdict-like
- prevent stale comparison data after re-analysis/re-extraction/deletion
- establish sample-driven regression QA before Phase 2/3 expansion

## Non-Scope
- final `eligible`, `not eligible`, or `review required` verdicts
- basis-document RAG retrieval
- evidence clause citations
- final checklist/preparation guide generation
- Nara HTML crawling
- login/auth
- HWP/HWPX parsing

## Principles
1. Do not present final eligibility decisions.
2. Keep uncertain items as `needs_review` or `possibly_missing`.
3. Prefer approved evidence over raw corporation profile fields.
4. Never mutate corporation data without user approval.
5. Invalidate comparisons after requirement re-extraction or notice re-analysis.
6. Do not use uncited requirements as final judgment evidence in future phases.

## Workstreams

### 1. Requirement Candidate Extraction
Tasks:
- expand region/license/company-type/document tokens
- improve de-duplication between metadata and parsed attachment text
- store more useful `source_text`
- normalize candidate labels and confidence
- add tests for extraction coverage and verdict-language absence

Done when:
- at least 5 representative sample notices extract usable region/license/company/document candidates
- repeated extraction is idempotent
- output contains no final-verdict language

### 2. Corporation Comparison Profile
Tasks:
- define priority between manual profile fields and approved evidence
- map approved evidence types into comparison buckets
- normalize JSON list fields consistently
- derive region candidates from addresses
- de-duplicate profile values

Done when:
- a corporation with only business-registration evidence still has a usable comparison profile
- approved evidence contributes to `prepared` matches
- missing data is safely represented as `not_found` or `needs_review`

### 3. Comparison Engine Safety
Tasks:
- separate exact, partial, synonym, and abbreviation matching
- avoid over-matching similar but different license names
- handle region granularity separately
- keep money/date/raw requirement lines as `needs_review`
- improve `reason`, `matched_value`, and `source_text`
- test that no final-verdict language appears in comparison output

Done when:
- matching is conservative
- each item is understandable to the administrator
- comparison output remains `preview_only`

### 4. Portal UX
Tasks:
- pin “not a final verdict” guidance at the top of the page
- prioritize cards by risk: possibly missing, needs review, not found, prepared
- improve side-by-side visibility of notice requirements and corporation profile
- explain that re-extraction invalidates old comparisons
- add next-action CTAs for uploading evidence, re-analyzing notice, and re-extracting requirements
- verify responsive layout

Done when:
- users understand this is a gap preview, not an eligibility verdict
- the next action is clear from the result page
- empty/loading/error states are helpful

### 5. Re-analysis / Re-extraction / History Integrity
Tasks:
- verify stale invalidation on notice re-analysis and requirement re-extraction
- delete linked candidates/comparisons when saved notices are deleted
- review behavior when corporation data changes or is deleted
- evaluate whether comparison-time corporation profile snapshots are needed

Done when:
- stale comparisons are not shown as current
- no orphan comparison data remains
- comparison history clearly shows when it was generated

### 6. Testing / Sample QA
Tasks:
- add rule-based extraction tests
- add API tests for extraction, comparison creation, history, stale invalidation, and delete cascade
- keep frontend build and smoke tests passing
- manage real sample PDFs as local opt-in test assets, not committed sensitive files
- consider JSON fixtures for expected sample extraction results

Done when:
- backend tests pass
- frontend build passes
- smoke test passes
- manual QA notes exist for at least 5 representative notices

### 7. Security / Privacy / Logging
Tasks:
- verify full API keys are never exposed
- avoid raw sensitive corporation identifiers in logs
- minimize response payloads where practical
- review local file path exposure

Done when:
- full secrets are never exposed
- sensitive fields appear only where required
- error messages are useful but not overly revealing

## Recommended Execution Order
1. Freeze current baseline and collect sample QA issues.
2. Improve requirement extraction.
3. Improve corporation comparison profile normalization.
4. Make comparison matching more conservative.
5. Refine UX copy and result ordering.
6. Harden history/re-execution integrity.
7. Run final code review and regression tests.

## Test Commands
```powershell
cd D:\project\wisdom_procurement\backend
py -3.13 -m unittest discover -s tests -v
```

```powershell
cd D:\project\wisdom_procurement\frontend
npm run build
```

```powershell
cd D:\project\wisdom_procurement
py -3.13 scripts\check-encoding.py
powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1
git diff --check
```

## Completion Criteria
Phase 1.7 stabilization is complete when:

- representative real notice samples pass manual QA
- corporation evidence/profile data feeds comparison profiles reliably
- comparison results cannot be mistaken for final eligibility verdicts
- stale comparisons are invalidated safely
- backend tests, frontend build, smoke test, and encoding check pass
- work log records test results and remaining issues

## Questions for Product Owner
- Which Nara notice categories should be prioritized for sample QA?
- Should `possibly_missing` be the first result group shown to users?
- Can PDF/Excel export move to Phase 1.8?
- Should historical comparisons keep a profile snapshot, or should comparisons always be regenerated from the latest corporation profile?
