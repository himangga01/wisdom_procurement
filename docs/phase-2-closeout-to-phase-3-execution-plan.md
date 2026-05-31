# 한국어 버전

## 문서 목적
이 문서는 Phase 2 종료 보강부터 Phase 2.5A-D, Phase 3A-G까지의 실제 실행 계획입니다.

현재 구현 기준선:
- Phase 2A-H 기준문서 MVP는 완료된 상태로 본다.
- Phase 2 운영 보강으로 기준문서 규칙 후보 승인/반려/수정 API와 관리 UX, 나라장터 자동 수집 실행/이력 UX, 운영 조회 인덱스, MuPDF known issue 동적 로딩을 추가했다.
- Phase 3 이전 판단 결과는 확정 자격 판정이 아니라 `부족조건`, `확인 필요`, `필요 서류`, `citation 후보` 중심으로 노출한다.
- AI/LLM 결과는 사용자 검토 후보로만 다룬다.
- 기준문서, 일반 업로드 문서, 나라장터 저장 공고는 계속 분리한다.

## Phase 2 종료 보강
목표는 Phase 2 결과물을 Phase 2.5/3 입력으로 쓰기 전에 운영 기준선을 고정하는 것입니다.

작업:
1. 테스트 기준선 API/문서화
2. 공고문 PDF 샘플 정책과 기준문서 PDF 샘플 정책 분리
3. MuPDF 내부 문법 경고 known issue 동적 로딩
4. 기본 테스트, opt-in PDF 테스트, Gemini 비교 QA 실행 방법 정리
5. 기준문서 규칙 후보 관리와 나라장터 자동 수집 관리 화면 제공

테스트:
- closeout summary API가 테스트/샘플/known issue 정책을 반환하는지 확인
- 최종 판정 문구가 포함되지 않는지 확인

## Phase 2.5A: 기준문서 규칙 후보 추출 실험
목표는 기준문서 청크에서 판단에 쓰일 수 있는 조건 후보를 뽑되 자동 확정하지 않는 것입니다.

작업:
1. `basis_rule_candidates` 테이블 추가
2. 청크 기반 rule-based 후보 추출기 추가
3. 후보 필드: 유형, 조건문, 관련 프로필 필드, 필요 증빙, citation 후보, confidence, needs_review
4. 기준문서별 후보 추출/조회 API 추가

테스트:
- 기준문서 업로드 후 규칙 후보 추출
- 후보가 basis chunk citation과 연결되는지 확인
- 후보 상태가 자동 확정이 아니라 `needs_review`인지 확인

## Phase 2.5B: 공고 요구조건 Phase 3 입력 구조화
목표는 Phase 1.7 요구조건 후보를 Phase 3 매칭 엔진이 안정적으로 읽을 수 있는 구조로 바꾸는 것입니다.

작업:
1. 기존 `notice_requirement_candidates`를 구조화 payload로 변환
2. 유형별 입력 스키마: region, license, company_type, required_document, money, date, requirement_line
3. 관련 법인 프로필 필드와 review 필요 여부 표시
4. 구조화 요구조건 API 추가

테스트:
- 저장 공고 요구조건이 Phase 3 입력 스키마로 반환되는지 확인
- unmapped/needs_review 항목이 보존되는지 확인
- 최종 판정 문구가 없는지 확인

## Phase 2.5C: 검색 품질과 citation 평가
목표는 기준문서 검색 결과가 판단 근거 후보로 쓸 수 있을 정도인지 측정하는 것입니다.

작업:
1. `basis_retrieval_evaluations` 테이블 추가
2. 질의셋 기반 검색 평가 실행 API 추가
3. top-k 결과 수, citation coverage, 평균 점수 기록
4. citation 없는 조건은 확정 판단 근거로 쓰지 않는 정책을 결과에 표시

테스트:
- 평가 실행 결과가 저장되는지 확인
- 검색 결과가 citation 후보를 포함하는지 확인
- coverage 지표가 계산되는지 확인

## Phase 2.5D: Phase 3 판단 엔진 입출력 계약 확정
목표는 판단 엔진 구현 전에 입력/출력 계약을 API와 문서로 고정하는 것입니다.

작업:
1. 판단 엔진 contract API 추가
2. 입력: 법인 snapshot, 공고 요구조건 snapshot, 기준문서 citation 후보
3. 출력: matched, missing, uncertain, needs_review, not_applicable, preparation_guide, citations, uncertainty_notes
4. contract version 관리

테스트:
- contract API가 필수 입력/출력 필드를 반환하는지 확인
- `eligible` 같은 확정 판정 용어가 나오지 않는지 확인

## Phase 3A: 판단 실행 스냅샷 모델
목표는 판단 실행 시점의 입력을 재현 가능하게 저장하는 것입니다.

작업:
1. `judgment_runs` 테이블 추가
2. notice/corporation/requirements/profile/citation snapshot 저장
3. 실행 상태, review 상태, prompt/rule version 기록

테스트:
- 판단 실행 생성 시 snapshot과 summary가 저장되는지 확인

## Phase 3B: 부족조건 중심 매칭 엔진
목표는 법인 정보와 공고 요구조건을 비교해 부족/확인 필요 항목을 찾는 것입니다.

작업:
1. 기존 Phase 1.7 비교 로직을 judgment item으로 확장
2. 상태: matched, missing, uncertain, needs_review, not_applicable
3. 매칭 결과는 확정 자격 판정이 아니라 준비 상태로만 표현

테스트:
- 보유 면허/지역은 matched
- 없는 면허/서류는 missing
- 금액/일정/원문 요구조건은 needs_review

## Phase 3C: 기준문서 citation 연결
목표는 각 판단 항목에 기준문서 검색 후보를 붙이는 것입니다.

작업:
1. requirement별 basis search 실행
2. citation candidates attach
3. citation 없는 항목은 `citation_status=missing`으로 표시

테스트:
- 관련 기준문서가 있으면 citation 후보가 붙는지 확인
- citation 없는 조건은 확정 근거로 쓰이지 않는지 확인

## Phase 3D: 준비 가이드 생성
목표는 사용자가 다음에 무엇을 준비해야 하는지 알 수 있게 하는 것입니다.

작업:
1. missing/needs_review 항목별 필요 액션 생성
2. 필요 서류 목록 생성
3. 불확실성 노트 생성

테스트:
- 부족 서류/면허가 preparation guide에 포함되는지 확인

## Phase 3E: 검토 워크플로
목표는 판단 결과를 사람이 검토하고 상태를 남길 수 있게 하는 것입니다.

작업:
1. judgment run review 상태 PATCH API
2. reviewer note 저장
3. 결과 payload에 review 상태 포함

테스트:
- review 상태 변경과 메모 저장 확인

## Phase 3F: 나라장터 API 자동 수집 확장
목표는 API 기반 신규 공고 모니터링/저장 구조를 준비하는 것입니다.

작업:
1. `nara_collection_runs` 테이블 추가
2. API 검색 조건과 결과 수 기록
3. 테스트에서는 외부 API 호출 없이 주입 notice 목록으로 dry-run/save 동작 검증
4. HTML 크롤링은 구현하지 않음

테스트:
- API 키가 없으면 외부 호출을 하지 않고 안전하게 실패/드라이런 처리
- 주입 notice 목록으로 collection run이 저장되는지 확인

## Phase 3G: 통합 QA와 오탐 방지
목표는 최종 판정 과신을 막는 회귀 테스트를 확보하는 것입니다.

작업:
1. 실제 흐름 기반 backend 통합 테스트 추가
2. final verdict 금지 문자열 검사
3. citation 없는 조건의 확정 근거 사용 차단 검사

테스트:
- judgment 결과 JSON에 `eligible`, `지원 가능`, `지원 불가능`이 포함되지 않는지 확인
- citation missing 항목이 final evidence처럼 표시되지 않는지 확인

## 실행 순서
1. Phase 2 종료 보강
2. Phase 2.5A
3. Phase 2.5B
4. Phase 2.5C
5. Phase 2.5D
6. Phase 3A-B
7. Phase 3C-D
8. Phase 3E-F
9. Phase 3G 통합 QA
10. 전체 코드 리뷰와 버그 수정

## Questions for Product Owner
- 실제 기준문서 PDF 샘플은 어떤 법령/예규부터 운영 기준으로 삼을까요?
- Phase 2.5 규칙 후보 승인 UX는 Phase 3 이전에 필수일까요?
- 판단 결과 화면에서 확정 자격 판정 표현을 계속 숨기고 `준비 상태`만 보여주는 정책으로 확정해도 될까요?

---

# AI / Engineering Version (English)

## Purpose
Execution plan from Phase 2 closeout hardening through Phase 2.5A-D and Phase 3A-G.

Baseline:
- Phase 2A-H MVP is complete.
- Phase 2 operations hardening now includes basis rule candidate review APIs/UX, Nara collection run management UX, operational indexes, and dynamic MuPDF known-issue loading.
- Phase 3 output remains gap-first and citation-aware, not a confident eligibility verdict.
- AI/LLM outputs are review candidates only.
- Basis documents, project uploads, and Nara notices remain separate domains.

## Planned Implementation
- Phase 2 closeout: expose/document test baseline, sample policy, and known MuPDF warnings.
- Phase 2.5A: add basis rule candidates extracted from basis chunks.
- Phase 2.5B: structure notice requirements into a Phase 3 input schema.
- Phase 2.5C: add retrieval/citation evaluation runs.
- Phase 2.5D: expose the Phase 3 judgment I/O contract.
- Phase 3A-G: add judgment runs, gap-first matching, citation candidates, preparation guide, review workflow, API-based Nara collection runs, and overconfidence regression tests.
- Operations UX: manage basis rule candidate approval/rejection/editing and Nara collection run execution/history from the admin portal.

## Guardrails
- No final eligibility wording before the product owner explicitly approves that UX.
- No uncited requirement becomes final decision evidence.
- Nara automation remains API-based; no HTML crawling is introduced.
- Missing AI/OCR dependencies must not break core flows.
