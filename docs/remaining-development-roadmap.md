# 한국어 버전

## 문서 목적
이 문서는 2026-05-22 기준 `SMART 조달청 계산기`의 남은 개발 단계를 다시 정리합니다.

현재 기준선은 다음과 같습니다.

- Phase 1: 업로드/관리/요약 MVP 완료
- Phase 1.5: 나라장터 API 기반 게시판/첨부 다운로드/공고 분석 완료
- Phase 1.6: 법인 증빙자료 업로드/추출/분류/검토 기반 프로필 보강 완료
- Phase 1.7: 공고 요구조건 대 법인 부족조건 미리보기 완료 및 실제 공고 PDF QA 완료
- Phase 2A-H: 기준문서 업로드/파싱/OCR degrade/정규화/청킹/로컬 인덱싱/검색/관리 UX MVP 완료
- Phase 2 운영 보강: 기준문서 규칙 후보 승인/반려/수정 API와 관리 UX, 나라장터 자동 수집 실행/이력 UX, 운영 조회 인덱스, MuPDF known issue 동적 로딩 완료
- 공고문 PDF 테스트 공용 캐시: 나라장터 랜덤 PDF 30개 확보, opt-in 테스트 재사용 구조 완료
- Gemini 2.5 기반 PDF 텍스트 비교 QA: 대표 공고문류 PDF에서 서비스 파싱과 Gemini 추출 텍스트의 높은 본문 일치도 확인

따라서 이후 작업은 `Phase 2 기능 추가`가 아니라 `Phase 2.5 검증/구조화`와 `Phase 3 판단 엔진`으로 넘어가는 흐름입니다.

## 남은 단계 요약

| 우선순위 | 단계 | 목적 | 산출물 |
| --- | --- | --- | --- |
| 1 | Phase 2 종료 보강 | 현재 구현을 Phase 3 입력으로 쓰기 전에 정리 | 문서/테스트/샘플 기준선, 경고 목록, known issue |
| 2 | Phase 2.5A | 기준문서에서 규칙 후보 추출 실험 | 기준문서 규칙 후보 스키마와 추출기 |
| 3 | Phase 2.5B | 공고 요구조건 후보를 Phase 3 입력 구조로 고도화 | 구조화된 notice requirement schema |
| 4 | Phase 2.5C | 검색 품질과 citation 품질 평가 | 검색 평가셋, recall/coverage 지표, citation 정책 |
| 5 | Phase 2.5D | Phase 3 판단 엔진 입력/출력 계약 확정 | 판단 엔진 I/O contract 문서와 테스트 fixture |
| 6 | Phase 3A-G | 부족조건 중심 판단 엔진과 근거 출력 | 판단 결과 API/UX, citation, 준비 가이드 |
| 7 | Phase 4 | 운영 제품화 | 인증, 백업, 배포, 다중 사용자/클라우드 선택지 |

## 바로 해야 할 일: Phase 2 종료 보강
Phase 2A-H는 MVP로 완료되었지만, Phase 3로 넘어가기 전에 아래를 먼저 정리합니다.

2026-05-24 기준으로 운영 화면/API/인덱스/known issue 동적 로딩은 구현 완료되었습니다. 남은 일은 실제 기준문서 PDF 샘플 선정과 citation 품질 기준 고정입니다.

작업:
- 현재 전체 테스트 기준선을 다시 고정
- 나라장터 공고문 PDF 30개 캐시 manifest와 QA 요약 보존
- PyMuPDF 내부 문법 경고가 발생한 PDF 목록을 로컬 QA known issue JSON에서 동적으로 읽도록 유지
- 공고문 PDF와 실제 기준문서 PDF를 구분해 테스트 목적을 명확히 표시
- `temp/` 산출물은 로컬 QA 결과로만 유지하고 Git에는 포함하지 않음
- 실제 기준문서 PDF 샘플 5~10개를 제품 오너가 선정할 수 있도록 후보 목록 작성

완료 기준:
- 기본 테스트와 opt-in PDF 테스트 실행 방법이 문서화된다.
- 공고문 PDF 샘플은 파이프라인 안정성 테스트용으로, 기준문서 PDF 샘플은 검색/citation 품질 평가용으로 분리된다.
- Phase 3 전에 반드시 확인해야 할 known issue가 한 곳에 모인다.

## Phase 2.5A: 기준문서 규칙 후보 추출 실험
목표는 기준문서 청크에서 판단에 쓸 수 있을 법한 조건 후보를 추출하되, 자동 확정하지 않는 것입니다.

작업:
- 실제 기준문서 PDF 샘플 선정
- 기준문서 청크에서 다음 후보 필드 추출
  - `rule_candidate_id`
  - `basis_document_id`
  - `chunk_id`
  - `category`
  - `condition_text`
  - `target_scope`
  - `required_evidence_types`
  - `related_profile_fields`
  - `citation_candidate_id`
  - `confidence`
  - `needs_review`
- Gemini 2.5 또는 rule-based 추출기를 실험하되 결과는 후보로만 저장
- citation 없는 규칙 후보는 판단 근거로 승격하지 않음

완료 기준:
- 기준문서 청크에서 규칙 후보를 만들 수 있다.
- 모든 후보는 citation 후보와 연결되거나 `needs_review`로 남는다.
- Phase 3 판단 엔진이 바로 확정 판단으로 쓰지 않도록 guard가 있다.

## Phase 2.5B: 공고 요구조건 구조화 고도화
목표는 Phase 1.7의 요구조건 후보를 Phase 3 매칭 엔진이 이해할 수 있는 구조로 바꾸는 것입니다.

작업:
- 요구조건 후보를 유형별로 정규화
  - 지역 제한
  - 업종/면허/등록 조건
  - 실적 조건
  - 인증/확인서 조건
  - 공동수급/컨소시엄 조건
  - 제출서류 조건
  - 입찰참가 제한/결격 조건
- 숫자/날짜/금액/기간 조건 파싱
- 법인 프로필 필드와 연결 가능한 조건 표시
- 연결 불가능한 조건은 `unmapped` 또는 `needs_review`로 유지

완료 기준:
- 공고 요구조건이 Phase 3 입력 스키마로 직렬화된다.
- 최종 자격 판정 문구는 여전히 노출하지 않는다.
- 사람이 검토해야 하는 조건이 분리된다.

## Phase 2.5C: 검색 품질과 citation 평가
목표는 기준문서 검색 결과를 판단 근거로 써도 되는지 품질 기준을 세우는 것입니다.

작업:
- 기준문서별 평가 질의셋 작성
- top-k 검색 결과가 올바른 청크를 포함하는지 측정
- citation 후보의 문서/페이지/섹션 메타데이터가 충분한지 검증
- 공고 요구조건과 기준문서 검색 결과를 연결하는 실험
- Gemini 2.5 비교 QA는 보조 검증으로 사용하되, 정답 기준은 사람이 승인한 기준문서/청크로 둠

완료 기준:
- 검색 품질 지표가 기록된다.
- citation 없는 조건은 Phase 3에서 확정 판단 근거로 쓰지 않는 정책이 테스트된다.
- 기준문서 검색 결과만 확인할 수 있는 관리자 UX 필요 여부가 결정된다.

## Phase 2.5D: Phase 3 판단 엔진 입력/출력 계약 확정
목표는 판단 엔진을 구현하기 전에 데이터 계약을 먼저 고정하는 것입니다.

작업:
- 입력 계약 정의
  - 법인 프로필 snapshot
  - 법인 증빙자료 snapshot
  - 공고 요구조건 snapshot
  - 기준문서 citation 후보
  - 사용자 검토 상태
- 출력 계약 정의
  - `matched`
  - `missing`
  - `uncertain`
  - `needs_review`
  - `not_applicable`
  - 준비 가이드
  - 필요 서류 목록
  - citation 목록
  - 불확실성 노트
- 판단 결과를 확정 판정이 아니라 준비 상태/부족 조건 중심으로 설계

완료 기준:
- Phase 3 API와 테스트 fixture가 계약 기반으로 작성될 수 있다.
- citation 없는 조건은 확정 판단 결과에 들어가지 않는다.
- 결과 표현은 확정 판정보다 `부족 조건`, `필요 인증`, `필요 서류`, `준비 가이드`를 우선한다.

## Phase 3A: 판단 도메인과 스냅샷 모델
목표는 판단 실행 시점의 데이터를 재현 가능하게 고정하는 것입니다.

작업:
- `judgment_runs` 또는 동등한 판단 실행 기록 추가
- 공고/법인/증빙자료/기준문서 검색 결과 snapshot 저장
- 판단 실행 상태와 오류 상태 정의
- 민감정보 로그 마스킹 유지

## Phase 3B: 법인 대 공고 요구조건 매칭 엔진
목표는 구조화된 공고 요구조건과 법인 프로필/증빙자료를 비교해 부족 조건을 찾는 것입니다.

작업:
- 조건 유형별 matcher 구현
- 매칭 결과를 `matched/missing/uncertain/needs_review/not_applicable`로 분리
- 사용자 승인 전 AI 결과를 자동 확정하지 않음
- 부족 조건과 필요한 추가 서류를 우선 출력

## Phase 3C: 기준문서 citation 연결
목표는 판단 결과에 근거 후보를 연결하되, citation 없는 결과를 확정 근거로 쓰지 않는 것입니다.

작업:
- 조건별 관련 기준문서 청크 검색
- citation 후보 attach
- citation confidence와 needs_review 표시
- 근거 조항 렌더링은 후보/검토 상태로 시작

## Phase 3D: 준비 가이드 생성
목표는 사용자가 무엇을 준비해야 하는지 실행 가능한 형태로 보여주는 것입니다.

작업:
- 부족 조건별 필요 서류/인증/등록 안내 생성
- 사용자 보유 증빙자료와 부족 서류 비교
- 법인 프로필 업데이트 후보 제안
- 불확실성 노트 표시

## Phase 3E: 판단 결과 UX와 검토 워크플로
목표는 관리자가 결과를 검토하고 수정할 수 있는 화면을 만드는 것입니다.

작업:
- 판단 실행 화면
- 결과 상세 화면
- 부족 조건 중심 UI
- citation 확인 UI
- 사용자 확인/보류/수동 수정 workflow
- PDF/문서 export는 별도 하위 단계로 분리 가능

## Phase 3F: 나라장터 수집 자동화 확장
목표는 Phase 1.5의 API 기반 조회/저장 구조를 운영 자동화로 확장하는 것입니다.

작업:
- API 기반 신규 공고 모니터링
- 중복 수집 방지
- 첨부 다운로드 정책
- 실패 재시도와 수집 로그
- HTML 크롤링은 API로 부족한 경우에만 별도 승인 후 검토

## Phase 3G: 통합 QA와 오탐 방지
목표는 실제 공고/법인/기준문서 조합에서 판단 결과가 과신되지 않도록 막는 것입니다.

작업:
- 실제 공고 PDF, 실제 기준문서 PDF, 샘플 법인 프로필 조합 테스트
- false positive 방지 테스트
- citation 없는 조건의 확정 판단 차단 테스트
- Gemini 2.5 등 LLM 결과가 사용자 검토 없이 확정되지 않는지 확인

## Phase 4: 운영 제품화
Phase 4는 판단 엔진이 동작한 뒤의 운영 안정화 단계입니다.

후보 작업:
- 인증/사용자 컨텍스트 추가
- 백업/복구
- 로컬 단일 PC 외 배포 선택지 검토
- 성능 최적화
- 감사 로그
- 권한 모델
- 장기적으로 HWP/HWPX 지원 여부 재검토

## 추천 작업 순서
가장 좋은 다음 순서는 다음입니다.

1. Phase 2 종료 보강
2. 실제 기준문서 PDF 샘플 선정
3. Phase 2.5A 기준문서 규칙 후보 추출 실험
4. Phase 2.5C 검색/citation 평가셋 구축
5. Phase 2.5B 공고 요구조건 구조화 고도화
6. Phase 2.5D Phase 3 입력/출력 계약 확정
7. Phase 3A 판단 스냅샷 모델 구현

이 순서가 좋은 이유는 판단 엔진을 먼저 만들면 citation 품질이 낮은 상태에서 결과를 과신할 위험이 있기 때문입니다. 지금은 먼저 기준문서와 요구조건을 `검증 가능한 입력`으로 만드는 것이 더 중요합니다.

## Questions for Product Owner
- `open`: 실제 기준문서 PDF 샘플은 어떤 문서부터 넣을까요?
- `decided`: 기준문서 규칙 후보는 관리자 승인/반려/수정 UX를 제공한다.
- `open`: 판단 결과를 처음 공개할 때 확정형 자격 판정 표현을 완전히 숨기고 `준비 상태` 중심으로만 보여줘도 될까요?
- `decided`: 나라장터 자동 수집은 API 기반 모니터링부터 시작하고, HTML 크롤링은 승인 전까지 도입하지 않는다.
- `open`: 승인된 기준 규칙 후보가 여러 개 매칭될 때 최고 신뢰도 1개만 쓸지, 여러 citation 후보를 병렬 표시할지 결정이 필요하다.
- `deferred`: 리뷰 이력 전체 history 테이블은 Phase 4 운영 감사 로그 단계에서 다시 검토한다.

---

# AI / Engineering Version (English)

## Purpose
This document restates the remaining roadmap as of 2026-05-22.

The current baseline is:

- Phase 1 MVP is complete.
- Phase 1.5 Nara API board and attachment analysis are complete.
- Phase 1.6 corporation evidence extraction/review/profile enrichment is complete.
- Phase 1.7 gap preview is complete and has real notice PDF QA.
- Phase 2A-H basis-document upload, parse/OCR-degrade, normalize, chunk, local index, search, and admin UX MVP are complete.
- Phase 2 operations hardening is complete: basis rule candidate approve/reject/edit APIs and UX, Nara collection run execution/history UX, operational indexes, and dynamic MuPDF known-issue loading.
- A shared local cache of 30 Nara notice PDFs exists for opt-in PDF tests.
- Gemini 2.5 PDF comparison QA shows high text overlap for representative notice PDFs.

The remaining work is not more Phase 2 feature work. It is Phase 2.5 validation/structuring followed by Phase 3 judgment.

## Remaining Roadmap

| Priority | Stage | Goal | Output |
| --- | --- | --- | --- |
| 1 | Phase 2 closeout hardening | Make the current implementation ready as Phase 3 input | Test baseline, sample policy, warnings, known issues |
| 2 | Phase 2.5A | Experiment with basis rule extraction | Rule candidate schema and extractor |
| 3 | Phase 2.5B | Structure notice requirements for matching | Phase 3-ready requirement schema |
| 4 | Phase 2.5C | Evaluate retrieval and citation quality | Evaluation set, recall/coverage metrics, citation policy |
| 5 | Phase 2.5D | Lock Phase 3 input/output contracts | Judgment I/O contract and fixtures |
| 6 | Phase 3A-G | Implement gap-first judgment with evidence citations | Judgment API/UX, citations, preparation guide |
| 7 | Phase 4 | Product operations | Auth, backup, deployment, multi-user/cloud options |

## Recommended Next Step
Start with Phase 2 closeout hardening, then select real official basis PDFs and begin Phase 2.5A and Phase 2.5C.

This order avoids building a judgment engine before retrieval and citation quality are measurable.

## Phase 2.5 Scope
- Extract basis rule candidates without auto-confirming them.
- Refine notice requirement candidates into typed, structured inputs.
- Evaluate basis search and citation coverage.
- Define the Phase 3 judgment input/output contract.

## Phase 3 Scope
- Persist judgment runs and input snapshots.
- Match corporation profile/evidence against notice requirements.
- Attach basis-document citation candidates.
- Generate missing requirements, required documents, and preparation guidance.
- Provide a human review workflow.
- Extend Nara API collection into operational monitoring.

## Non-Negotiable Guards
- Do not expose final eligibility as a confident verdict before Phase 3.
- Do not use uncited requirements as final decision evidence.
- Keep AI/LLM outputs as review candidates unless the user confirms them.
- Keep basis documents separate from project documents.
- Keep Nara notice PDFs separate from official basis-document samples.

## Questions for Product Owner
- `open`: Which official basis PDFs should be selected first?
- `decided`: Basis rule candidates have admin approve/reject/edit UX.
- `open`: Should the first judgment UI avoid final-verdict language and show readiness/gaps only?
- `decided`: Nara automation starts with API monitoring; HTML crawling is not introduced before explicit approval.
- `open`: When multiple approved rule candidates match, should the engine use only the top-confidence one or show multiple citation candidates?
- `deferred`: A full review-history table is deferred to the Phase 4 audit-log scope.
