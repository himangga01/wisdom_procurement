# 한국어 버전

## 문서 목적
이 문서는 2026-05-24 재리뷰에서 확인된 `P1 보강 필요`, `P2 보강 필요`, `문서 보강 필요` 항목을 실제 수정 작업으로 전환하기 위한 계획서입니다.

여기서 `P1`과 `P2`는 개발 Phase 번호가 아니라 보강 우선순위입니다.

- P1: 판단 품질, 운영 이력, citation 신뢰도에 직접 영향을 주는 즉시 보강 항목
- P2: 운영자 UX, 상태 관리, 검색/필터 사용성을 높이는 후속 보강 항목
- 문서 보강: 현재 구현과 설계 문서 사이의 불일치를 제거하는 정리 항목

## 현재 기준선
현재 구현 기준선은 다음과 같이 봅니다.

- Phase 1.7 QA와 실제 공고문 PDF 샘플 기반 테스트 흐름은 준비되어 있다.
- Phase 2A-H 기준문서 업로드, 파싱, OCR degrade, 정규화, 청킹, 로컬 인덱싱, 검색, 관리 UX MVP는 구현되어 있다.
- Phase 2 운영 보강으로 기준문서 규칙 후보 승인/반려/수정 API와 UX, 나라장터 자동 수집 실행/이력 UX, 운영 조회 인덱스, MuPDF known issue 동적 로딩이 추가되어 있다.
- 백엔드 전체 unittest, 프론트엔드 빌드, 인코딩 체크는 통과했다.
- 단, 승인된 규칙 후보가 실제 판단 엔진에 연결되는 흐름과 운영 실패 이력 UX는 아직 보강이 필요하다.

## 진행 상태
2026-05-24 1차 보강 착수 결과는 다음과 같습니다.

- `done`: P1-1 승인된 기준 규칙 후보를 judgment citation 후보로 우선 연결
- `done`: P1-2 citation 후보 승인 검증 강화
- `done`: P1-3 나라장터 수집 실패 run payload 반환과 이력 UX 새로고침 보강
- `partial`: P2-1 기준 규칙 후보 관리 UX 개선. 기준문서 선택과 citation option 선택은 반영했으며, 기준문서 상세 화면의 바로 추출 액션은 후속으로 남긴다.
- `done`: P2-2 리뷰 상태 metadata 정책 확정
- `done`: P2-3 나라장터 수집 이력 `partial_failed` 필터와 keyword 검색 범위 보강
- `done`: P2-4 검색 품질/평가 UX 보강. `/basis-retrieval-evaluations` 화면에서 coverage와 누락 citation을 확인한다.
- `done`: D-1/D-2/D-3 문서 보강. 현재 설계/UX 문서는 부족조건/준비 상태 중심으로 정리했으며, work-log의 오래된 표현은 역사 기록으로만 남긴다.
- `partial`: D-4 코드 구조 분리 실작업. `core/text.py`, `core/json_utils.py`, `core/citations.py`, `services/basis_rule_candidates.py`를 추가해 공통 helper, citation ID 검증, 기준 규칙 후보 승인/상태 전환/매칭 helper를 `main.py` 밖으로 분리했다. 이어서 `services/nara_api.py`를 추가해 나라장터 응답 파싱, 첨부 정규화, 안전 URL 검사, 첨부 다운로드 helper를 서비스 모듈로 분리했다. `pipelines/basis_document.py`도 추가해 기준문서 정규화, 청킹, 로컬 인덱싱, 재처리, 검색 후보 생성 로직을 파이프라인 모듈로 이동했다.

## 수정 범위
이번 계획의 범위는 다음 세 묶음입니다.

1. P1 보강
2. P2 보강
3. 문서 보강

이번 계획은 다음 작업을 범위 밖으로 둡니다.

- 신규 인증/로그인 기능
- HTML 크롤러
- HWP/HWPX 파싱
- 최종 자격 판정처럼 보이는 확정형 UX
- 외부 배포/백업/다중 사용자 운영 기능

## P1 보강 계획

### P1-1. 승인된 기준 규칙 후보를 판단 엔진에 연결
문제:

현재 기준문서 규칙 후보 승인/반려 UX는 존재하지만, 판단 실행 시 승인된 후보가 우선 사용되지 않는다. 이 상태에서는 관리자가 승인한 기준 규칙이 실제 판단 근거 품질을 개선하지 못한다.

수정 방향:

- `basis_rule_candidates.status = approved`인 후보를 판단 엔진 입력 후보로 사용할 수 있게 한다.
- 공고 요구조건과 승인된 기준 규칙 후보를 연결하는 선택 로직을 추가한다.
- 승인 후보가 있으면 일반 기준문서 검색 결과보다 우선 사용한다.
- 승인 후보가 없거나 매칭 점수가 낮으면 기존 기준문서 검색을 fallback으로 사용한다.
- judgment snapshot에 다음 정보를 남긴다.
  - 사용된 승인 규칙 후보 ID
  - fallback 검색 사용 여부
  - citation 후보 ID
  - citation 신뢰도
  - citation 임계값 통과 여부
- citation이 없는 항목은 확정 판단 근거로 쓰지 않고 `needs_review` 또는 `citation_missing`으로 표시한다.

예상 코드 변경:

- 판단 실행 로직에서 기준문서 검색 전에 승인 규칙 후보 조회 단계 추가
- 승인 후보와 공고 요구조건 간 매칭 서비스 추가
- judgment result payload에 승인 후보 provenance 필드 추가
- 필요 시 `basis_rule_candidates` 조회 repository/helper 분리

테스트 계획:

- 승인된 규칙 후보가 있는 경우 judgment item에 해당 후보가 연결되는지 검증
- 승인되지 않은 후보는 judgment evidence로 사용되지 않는지 검증
- 승인 후보가 없을 때 기존 검색 fallback이 동작하는지 검증
- citation이 임계값 미만이면 `review_evidence_ready=false` 또는 동등 상태로 남는지 검증

완료 기준:

- 승인된 기준 규칙 후보가 실제 판단 결과의 citation 후보 또는 evidence 후보로 사용된다.
- 승인되지 않은 후보는 판단 근거로 쓰이지 않는다.
- fallback 검색 사용 여부가 snapshot에 남는다.
- 최종 자격 판정 문구는 계속 노출하지 않는다.

### P1-2. citation 후보 승인 검증 강화
문제:

규칙 후보 승인 시 `citation_candidate_id`가 실제 `basis_document_id`와 `basis_chunk_id`에 대응하는지 충분히 검증하지 않는다. 프론트에서도 citation ID를 자유 입력할 수 있어 잘못된 citation을 승인할 위험이 있다.

수정 방향:

- citation ID 형식을 표준화한다.
  - 예: `basis:{basis_document_id}:chunk:{basis_chunk_id}`
- 승인 API에서 다음을 검증한다.
  - citation ID 형식이 유효한지
  - citation ID의 문서 ID가 후보의 `basis_document_id`와 같은지
  - citation ID의 청크 ID가 후보의 `basis_chunk_id`와 같은지
  - 해당 기준문서와 청크가 실제 존재하는지
- 프론트에서는 자유 입력 대신 후보 citation 선택 UI를 제공한다.
- 수정 API에서는 citation 불일치 시 400 응답과 명확한 오류 메시지를 반환한다.

예상 코드 변경:

- citation ID parser/validator helper 추가
- 기준 규칙 후보 PATCH/approve API 검증 강화
- 기준 규칙 후보 상세 payload에 선택 가능한 citation 후보 또는 현재 chunk citation preview 추가
- 프론트 citation 입력 필드를 선택/미리보기 방식으로 변경

테스트 계획:

- 올바른 citation ID 승인 성공
- 다른 기준문서 ID가 들어간 citation ID 승인 실패
- 존재하지 않는 청크 ID 승인 실패
- 빈 citation ID 승인 실패
- 프론트 타입과 API 응답 타입 정합성 빌드 검증

완료 기준:

- 승인된 규칙 후보는 항상 실제 기준문서/청크와 연결된다.
- 운영자가 임의 문자열을 citation으로 승인할 수 없다.
- 오류 메시지가 관리자에게 이해 가능한 문구로 표시된다.

### P1-3. 나라장터 자동 수집 실패 이력 UX 보강
문제:

백엔드는 API 키 미설정 같은 실패도 `nara_collection_runs`에 기록하지만, 프론트는 실패 응답을 예외로 처리해 방금 저장된 실패 이력을 즉시 보여주지 못할 수 있다.

수정 방향:

- 관리자 실행 요청 자체가 접수되었고 run이 저장된 경우에는 HTTP 200 또는 202로 run payload를 반환한다.
- 수집 결과 상태는 payload의 `status`로 표현한다.
  - `completed`
  - `partial_failed`
  - `failed`
  - `not_configured`
- 예외적인 서버 장애만 5xx로 둔다.
- 프론트는 실행 직후 성공/실패 여부와 무관하게 최신 실행 이력을 새로고침한다.
- 실패 사유, 저장 건수, 첨부 다운로드 실패 건수, 재시도 가능 여부를 상세 패널에서 확인할 수 있게 한다.

예상 코드 변경:

- 나라장터 수집 실행 API의 응답 정책 정리
- API client에서 collection run 실행 결과 타입 명시
- `NaraCollectionRunsPage`에서 실패 상태도 상세 패널에 표시
- 실행 overlay는 네트워크/서버 오류와 업무 실패 상태를 구분

테스트 계획:

- API 키 미설정 시 run이 `not_configured`로 저장되고 응답 payload에 포함되는지 검증
- 부분 실패 fixture에서 `partial_failed`가 필터/상세에 표시되는지 검증
- 프론트 빌드 검증
- 가능하면 브라우저 스모크로 실행 버튼, 상태 필터, 상세 패널 표시 확인

완료 기준:

- 관리자는 실패한 수집 실행도 즉시 이력에서 확인할 수 있다.
- 실패 사유가 API 응답과 UX 양쪽에서 보인다.
- 실패를 단순 네트워크 오류처럼만 보여주지 않는다.

## P2 보강 계획

### P2-1. 기준 규칙 후보 관리 UX 개선
문제:

현재 운영자는 기준문서 ID를 수동 입력해 후보를 추출하고, citation도 직접 문자열로 다뤄야 한다.

수정 방향:

- 기준문서 선택 드롭다운 또는 검색형 선택기를 추가한다.
- 기준문서 목록/상세에서 `규칙 후보 추출` 액션을 바로 실행할 수 있게 한다.
- 후보 상세에서 문서 제목, 버전, 카테고리, 페이지, 섹션, chunk preview를 함께 보여준다.
- citation 후보는 문자열 입력이 아니라 선택/미리보기 UI로 제공한다.
- 승인/반려/수정 버튼은 상태에 따라 활성/비활성 처리한다.

테스트 계획:

- 기준문서 선택 없이 추출 실행 시 안내 메시지 표시
- 기준문서 선택 후 추출 API 호출
- 후보 상세에서 citation preview 표시
- 프론트 빌드 검증

완료 기준:

- 운영자가 내부 ID를 몰라도 후보 추출과 승인을 진행할 수 있다.
- citation 확인 없이 승인하는 흐름을 줄인다.

### P2-2. 규칙 후보 리뷰 상태 정책 확정
문제:

승인/반려된 후보를 다시 `needs_review`로 되돌릴 때 `reviewed_at`, `reviewer_name`, `review_note`를 유지할지 초기화할지 정책이 명확하지 않다.

수정 방향:

- 상태 전환 정책을 다음처럼 고정한다.
  - `needs_review -> approved/rejected`: `reviewed_at`, `reviewer_name` 기록
  - `approved/rejected -> needs_review`: `reviewed_at`, `reviewer_name` 초기화, 이전 note는 `review_note`에 남기거나 별도 history가 없으면 보존
  - `approved/rejected -> archived`: 기존 review metadata 보존
- MVP에서는 별도 review history 테이블을 만들지 않고, 상태 전환 정책과 현재 메타데이터를 명확히 한다.
- Phase 4 운영 감사 로그에서 history 테이블을 별도 검토한다.

테스트 계획:

- 승인 시 reviewer metadata 기록
- 반려 시 reviewer metadata 기록
- 다시 검토 필요로 되돌릴 때 `reviewed_at` 정책이 기대대로 동작
- archived 전환 시 metadata 보존

완료 기준:

- 동일한 상태 전환이 항상 같은 metadata 결과를 만든다.
- 관리자 화면에서 현재 상태와 리뷰 메타데이터가 모순되지 않는다.

### P2-3. 나라장터 수집 이력 필터/검색 보강
문제:

부분 실패 상태가 UI 필터에 빠져 있고, 실행 이력을 조건별로 찾는 기능이 제한적이다.

수정 방향:

- 상태 필터에 `partial_failed`를 추가한다.
- 검색 키워드가 실행 조건, 공고명, 실패 사유, 저장 결과 요약까지 포함하도록 확장한다.
- 실행 일시 범위 필터는 Phase 3F 이후 운영량이 많아질 때 추가한다.
- 실패/부분 실패 row는 상태, 실패 사유, 저장 성공/실패 건수를 한눈에 보이게 한다.

테스트 계획:

- `partial_failed` 필터 적용
- 실패 사유 keyword 검색
- 저장 결과 summary 표시
- 프론트 빌드 검증

완료 기준:

- 관리자가 실패/부분 실패 이력을 쉽게 찾을 수 있다.
- 실패 사유가 상세 진입 전에도 요약된다.

### P2-4. 검색 품질/평가 UX 보강
문제:

검색/citation 평가 결과는 백엔드에 있으나 운영자가 평가 품질을 해석하는 UX는 아직 제한적이다.

수정 방향:

- 기준문서 검색 평가 결과 목록을 관리자 화면에서 확인할 수 있게 한다.
- `result_coverage`, `expected_citation_coverage`, `missed_expected_citation_ids`를 사람이 이해하기 쉬운 라벨로 표시한다.
- 평가 실패 항목은 재평가 또는 기준 citation 수정 후보로 이어질 수 있게 한다.

테스트 계획:

- 평가 결과 목록 API/화면 표시
- 누락 citation 목록 표시
- 평가 결과가 없는 경우 empty state 표시

완료 기준:

- citation 품질 문제를 코드 로그가 아니라 관리자 화면에서 확인할 수 있다.

## 문서 보강 계획

### D-1. 최종 판정 중심 표현 정리
문제:

일부 문서에 `eligible`, `not_eligible`, `지원 가능`, `지원 불가`처럼 최종 자격 판정처럼 읽히는 표현이 남아 있다.

수정 방향:

- 현재 정책을 문서 전반에 다시 고정한다.
  - Phase 3 전까지는 최종 자격 판단을 확정 기능처럼 노출하지 않는다.
  - Phase 3도 우선은 부족조건, 필요 인증, 필요 서류, 준비 가이드, citation 상태 중심으로 표현한다.
- 오래된 status 예시는 다음처럼 교체한다.
  - `matched`
  - `missing`
  - `uncertain`
  - `needs_review`
  - `not_applicable`
  - `citation_missing`
- 역사 기록 성격의 work-log는 무리하게 삭제하지 않고, 현재 기준을 덧붙인다.

수정 대상:

- `docs/technical-design.md`
- `docs/eligibility-rag-implementation-plan.md`
- `docs/phase-2-implementation-plan.md`
- `docs/remaining-development-roadmap.md`
- `docs/work-log.md`의 최신 기준 요약 섹션

테스트 계획:

- 금지/주의 표현 검색 스크립트 또는 `rg` 체크
- 문서 링크 깨짐 확인
- 인코딩 체크

완료 기준:

- 핵심 설계 문서에서 최종 자격 판정처럼 읽히는 표현이 현재 정책과 충돌하지 않는다.
- 문서마다 Phase guardrail이 일관된다.

### D-2. 오래된 Phase 표기 수정
문제:

일부 사용자 화면 문구와 문서에 현재 단계와 맞지 않는 Phase 표기가 남아 있다.

수정 방향:

- 사용자 화면에서 `Phase 1.6`으로 남은 공고 요구조건 후보 안내 문구를 현재 맥락에 맞게 수정한다.
- 문서 내 Phase 2 운영 보강 완료/미완료 상태를 일관되게 정리한다.
- Phase 번호를 사용자에게 직접 보여줄 필요가 없는 화면은 기능 중심 문구로 바꾼다.

테스트 계획:

- 프론트 빌드
- 관련 문구 `rg` 검색
- 공고 상세 화면 문구 확인

완료 기준:

- 관리자 화면에서 오래된 Phase 번호 때문에 혼란이 생기지 않는다.

### D-3. Questions for Product Owner 통합
문제:

미결정 질문이 여러 문서에 흩어져 있어 우선순위 결정이 어렵다.

수정 방향:

- `docs/remaining-development-roadmap.md`에 통합 `Questions for Product Owner` 섹션을 둔다.
- 각 문서의 질문은 유지하되, 핵심 질문은 통합 섹션으로 링크하거나 중복을 줄인다.
- 질문마다 상태를 붙인다.
  - `open`
  - `decided`
  - `deferred`

테스트 계획:

- 문서 내 질문 섹션 검색
- 중복 질문 정리 확인

완료 기준:

- 다음 개발 순서를 막는 질문을 한 곳에서 볼 수 있다.

### D-4. 코드 구조 보강 계획 문서화
문제:

`backend/app/main.py`와 일부 프론트 페이지 파일이 커져서 AGENTS.md의 코드 구성 규칙과 점점 멀어지고 있다.

수정 방향:

- 즉시 대규모 리팩터링을 진행하지 않고, 기능 보강과 함께 자연스럽게 분리한다.
- 백엔드는 다음 순서로 분리한다.
  - `api/`: route 함수
  - `services/`: judgment, basis rule candidate, Nara collection service
  - `repositories/`: SQLite 접근 helper
  - `schemas/`: request/response payload shape
  - `pipelines/`: PDF/OCR/chunk/index 흐름
- 프론트는 다음 순서로 분리한다.
  - pages는 route composition 위주로 축소
  - features에 액션 단위 컴포넌트 분리
  - entities에 도메인 표시 컴포넌트 분리
  - shared에 공통 UI/API 유틸 분리

테스트 계획:

- 분리 전후 백엔드 전체 unittest 동일 통과
- 프론트 빌드 동일 통과
- 핵심 API smoke 확인

완료 기준:

- 새 기능은 가능한 한 기존 초대형 파일을 더 키우지 않는다.
- P1/P2 보강 중 새 helper/service를 분리 구조로 만들기 시작한다.

## 실행 순서
권장 실행 순서는 다음과 같습니다.

1. P1-2 citation 검증 강화
2. P1-1 승인된 규칙 후보를 판단 엔진에 연결
3. P1-3 나라장터 실패 이력 UX 보강
4. P2-1 기준 규칙 후보 관리 UX 개선
5. P2-2 리뷰 상태 정책 확정
6. P2-3 나라장터 수집 이력 필터/검색 보강
7. D-1 최종 판정 중심 표현 정리
8. D-2 오래된 Phase 표기 수정
9. D-3 Questions for Product Owner 통합
10. D-4 코드 구조 보강 계획 반영
11. 전체 회귀 테스트와 코드 리뷰

이 순서를 추천하는 이유는 citation 검증이 먼저 닫혀야 승인 후보를 판단 엔진에 안전하게 연결할 수 있고, 그 다음에 운영 UX와 문서 정리를 진행해야 실제 기능과 문서가 다시 어긋나지 않기 때문입니다.

## 전체 테스트 기준선
각 보강 작업 후 최소 테스트는 다음과 같습니다.

```powershell
cd backend
py -3.13 -m unittest discover -s tests -v

cd ..\frontend
npm run build

cd ..
py -3.13 scripts\check-encoding.py
git diff --check
```

가능하면 브라우저 스모크 테스트로 다음 화면을 확인합니다.

- `/basis-rule-candidates`
- `/nara-collection-runs`
- 저장 공고 상세 화면
- judgment run 상세 화면

## 완료 기준
이번 보강 계획은 다음 상태가 되면 완료로 봅니다.

- 승인된 기준 규칙 후보가 실제 판단 입력 또는 citation 후보로 사용된다.
- citation 후보는 실제 기준문서/청크와 불일치한 상태로 승인될 수 없다.
- 나라장터 수집 실패도 관리자 이력 화면에서 즉시 확인할 수 있다.
- 기준 규칙 후보 관리 UX에서 내부 ID 수동 입력 의존도가 줄어든다.
- 부분 실패 상태와 실패 사유 검색이 운영 화면에서 가능하다.
- 핵심 문서의 최종 판정 표현과 Phase 표기가 현재 정책과 일치한다.
- 전체 테스트와 빌드가 통과한다.

## Questions for Product Owner
- 승인된 기준 규칙 후보가 여러 개 매칭될 때 운영 정책은 `가장 높은 신뢰도 1개`가 좋을까요, 아니면 `여러 citation 후보 병렬 표시`가 좋을까요?
- `approved/rejected -> needs_review` 전환 시 기존 리뷰 메모를 보존하는 것이 좋을까요, 아니면 별도 history가 생기기 전까지 초기화하는 것이 좋을까요?
- 나라장터 수집 실행 결과가 `not_configured`일 때 HTTP 200/202로 업무 실패를 반환하는 정책을 확정해도 될까요?
- 검색/citation 평가 결과 화면은 Phase 2 보강에 포함할까요, 아니면 Phase 2.5C의 운영 UX로 분리할까요?

---

# AI / Engineering Version (English)

## Purpose
This document converts the latest review findings into an actionable remediation plan for priority P1, priority P2, and documentation gaps. Here, P1/P2 are priority levels, not product phase numbers.

## Baseline
- Phase 1.7 QA and real Nara notice PDF sample testing are available.
- Phase 2A-H basis document ingestion, parsing, OCR degradation, normalization, chunking, local indexing, search, and management UX are implemented.
- Phase 2 operations hardening added basis rule candidate review APIs/UX, Nara collection run execution/history UX, operational indexes, and dynamic MuPDF known-issue loading.
- Backend unittest, frontend build, encoding check, and whitespace checks pass.
- Remaining gaps are mostly around wiring approved rule candidates into judgment, strengthening citation validation, and making failed collection runs visible in the admin UX.

## Progress Status
As of the first remediation pass on 2026-05-24:

- `done`: P1-1 approved basis rule candidates are preferred as judgment citation candidates.
- `done`: P1-2 citation approval validation is strengthened.
- `done`: P1-3 Nara collection business failures return saved run payloads and the UX refreshes history.
- `partial`: P2-1 basis document selection and citation option selection are implemented; extraction actions from basis document detail/list remain follow-up work.
- `done`: P2-2 review metadata transition policy is implemented.
- `done`: P2-3 `partial_failed` filter and broader keyword search are implemented.
- `done`: P2-4 retrieval/citation evaluation UX. `/basis-retrieval-evaluations` shows coverage and missed citations.
- `done`: D-1/D-2/D-3 documentation cleanup. Current design/UX docs are gap/readiness-first; stale terms remain only in historical work-log or explicit forbidden-string checks.
- `partial`: D-4 code structure split implementation. Added `core/text.py`, `core/json_utils.py`, `core/citations.py`, and `services/basis_rule_candidates.py` to move shared helpers, citation ID validation, and basis rule candidate approval/status/matching helpers out of `main.py`. Added `services/nara_api.py` to move Nara response parsing, attachment normalization, safe URL checks, and attachment download helpers into a service module. Added `pipelines/basis_document.py` to move basis document normalization, chunking, local indexing, reprocessing, and search candidate generation into the pipeline layer.

## Scope
In scope:
- P1 remediation
- P2 remediation
- documentation cleanup

Out of scope:
- authentication
- HTML crawling
- HWP/HWPX parsing
- final eligibility verdict UX
- deployment, backups, or multi-user operations

## P1 Remediation

### P1-1. Wire Approved Basis Rule Candidates Into Judgment
Problem:
Approved basis rule candidates are managed in the admin UI but are not yet consumed by the judgment engine.

Plan:
- Query `basis_rule_candidates` with `status = approved` before generic basis search.
- Match approved candidates against structured notice requirements.
- Prefer approved candidates over generic search results when they pass matching and citation thresholds.
- Fall back to generic basis search when no approved candidate is available or reliable.
- Store provenance in the judgment snapshot:
  - approved rule candidate ID
  - fallback search usage
  - citation candidate ID
  - citation score
  - citation threshold status
- Keep uncited items as `needs_review` or `citation_missing`, not final evidence.

Tests:
- Approved candidates attach to judgment items.
- Unapproved candidates are ignored as evidence.
- Generic search fallback still works.
- Low-scoring citation candidates do not become review-ready evidence.

Acceptance Criteria:
- Approved candidates can affect judgment evidence candidates.
- Unapproved candidates cannot become evidence.
- Fallback usage is visible in snapshots.
- No final eligibility wording is introduced.

### P1-2. Strengthen Citation Candidate Validation
Problem:
Approval currently does not strongly prove that `citation_candidate_id` belongs to the candidate's basis document and chunk.

Plan:
- Standardize citation IDs, for example `basis:{basis_document_id}:chunk:{basis_chunk_id}`.
- Validate citation format, basis document ID, basis chunk ID, and actual row existence on approve/PATCH.
- Replace free-text citation editing in the UI with citation selection and preview.

Tests:
- Valid citation approval succeeds.
- Wrong basis document ID fails.
- Missing chunk fails.
- Empty citation fails.
- Frontend types/build remain valid.

Acceptance Criteria:
- Approved rule candidates always point to real basis document chunks.
- Admins cannot approve arbitrary citation strings.

### P1-3. Improve Nara Collection Failure History UX
Problem:
The backend records failed runs, but the frontend can treat the API response as a thrown request failure and fail to refresh the newly saved run.

Plan:
- Return a run payload with HTTP 200/202 when the admin execution request is accepted and a run row is saved.
- Represent business outcome through `status`: `completed`, `partial_failed`, `failed`, `not_configured`.
- Reserve 5xx responses for unexpected server errors.
- Refresh the run list after every execution attempt.
- Show failure reason, saved counts, attachment failures, and retryability in the detail panel.

Tests:
- Missing API key returns a saved `not_configured` run payload.
- Partial failures appear in filters and detail.
- Frontend build passes.
- Browser smoke test covers execution, filters, and detail panel when available.

Acceptance Criteria:
- Admins can immediately see failed collection runs.
- Failure reasons are visible in both API and UX.

## P2 Remediation

### P2-1. Improve Basis Rule Candidate UX
Plan:
- Add basis document selector/search.
- Add rule extraction action from basis document list/detail.
- Show document title, version, category, page, section, and chunk preview.
- Replace citation free text with picker/preview.
- Disable invalid actions based on status.

### P2-2. Define Review Status Metadata Policy
Plan:
- `needs_review -> approved/rejected`: set reviewer metadata.
- `approved/rejected -> needs_review`: clear `reviewed_at` and `reviewer_name`; preserve or explicitly reset note based on product decision.
- `approved/rejected -> archived`: preserve existing review metadata.
- Defer full review history table to a later operations/audit phase.

### P2-3. Improve Nara Collection Filters/Search
Plan:
- Add `partial_failed` status filter.
- Search across query conditions, notice names, failure reasons, and result summaries.
- Improve failed/partial row summaries.

### P2-4. Improve Retrieval Evaluation UX
Plan:
- Add an admin view for retrieval evaluation results.
- Show `result_coverage`, `expected_citation_coverage`, and `missed_expected_citation_ids` with user-friendly labels.
- Use failed evaluation rows to drive citation review.

## Documentation Remediation

### D-1. Remove Final Verdict-Centric Wording
Plan:
- Replace stale `eligible` / `not_eligible` examples with gap-first states:
  - `matched`
  - `missing`
  - `uncertain`
  - `needs_review`
  - `not_applicable`
  - `citation_missing`
- Preserve work-log history where appropriate, but add current-policy notes.

### D-2. Fix Stale Phase Labels
Plan:
- Remove stale Phase 1.6 wording from user-facing requirement candidate copy.
- Make Phase 2 hardening completion status consistent across docs.
- Prefer feature-oriented UI copy over raw phase labels.

### D-3. Consolidate Product Owner Questions
Plan:
- Add a consolidated `Questions for Product Owner` section to the remaining roadmap.
- Mark questions as `open`, `decided`, or `deferred`.
- Reduce duplicate questions across docs.

### D-4. Document Code Structure Hardening
Plan:
- Avoid growing oversized files further.
- Gradually split backend routes, services, repositories, schemas, and pipelines.
- Gradually split frontend pages into route composition, features, entities, and shared modules.

## Recommended Order
1. Strengthen citation validation.
2. Wire approved rule candidates into judgment.
3. Improve Nara collection failure history UX.
4. Improve basis rule candidate UX.
5. Define review status metadata policy.
6. Improve Nara collection filters/search.
7. Remove final verdict-centric documentation.
8. Fix stale phase labels.
9. Consolidate Product Owner questions.
10. Apply code structure hardening incrementally.
11. Run full regression tests and code review.

## Test Baseline
```powershell
cd backend
py -3.13 -m unittest discover -s tests -v

cd ..\frontend
npm run build

cd ..
py -3.13 scripts\check-encoding.py
git diff --check
```

Optional browser smoke targets:
- `/basis-rule-candidates`
- `/nara-collection-runs`
- saved notice detail
- judgment run detail

## Questions for Product Owner
- When multiple approved rule candidates match, should judgment use the highest-confidence candidate only or show multiple parallel citation candidates?
- When reopening an approved/rejected rule candidate, should the previous review note be preserved until a review history table exists?
- Can the collection API return HTTP 200/202 for accepted-but-failed business outcomes such as `not_configured`?
- Should retrieval/citation evaluation UX be part of this hardening pass or Phase 2.5C operations UX?
