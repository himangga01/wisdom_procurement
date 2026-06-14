# 한국어 버전

## 문서 목적
이 문서는 `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 실제 서비스 로직 동작 테스트로 바꾸기 위한 계획이다.

영상 시연은 화면을 보여주는 목적이지만, 이 테스트는 화면 뒤의 핵심 파이프라인이 끊기지 않고 이어지는지 확인하는 목적이다.

## 결론
`3. 제품 시연 흐름`은 하나의 업무 파이프라인 회귀 테스트로 고정하는 것이 적합하다.

테스트는 다음 흐름을 한 번에 검증한다.

1. 법인 증빙자료 업로드
2. 증빙 후보 승인과 법인 프로필 반영
3. 대시보드와 운영 상태 확인
4. 나라장터 공고 저장/분석
5. 저장 공고 요구조건 후보 확인
6. 기준문서 업로드/청킹/JSON basis index 생성
7. 공고와 법인 비교
8. 부족조건 중심 판단 run 생성
9. 계약서 DOCX 초안 생성/다운로드
10. 작업 이력과 운영 요약 확인

## 테스트 계층

### 1. 빠른 파이프라인 회귀 테스트
- 위치: `backend/tests/test_api_flows.py`
- 방식: Flask test client 기반 API 테스트
- OCR: `OCR_ENGINE=noop`
- 외부 API: 사용하지 않음
- 파일: 테스트 안에서 생성한 DOCX/PDF 사용
- 목적:
  - CI 또는 로컬에서 빠르게 반복 가능
  - 실제 나라장터/LLM/OCR 네트워크 상태와 무관하게 핵심 로직 검증

### 2. 실제 PDF 운영 샘플 테스트
- 대상: `source/test_doc/`
- 방식: 별도 옵션형 테스트 또는 운영 QA 스크립트
- OCR: 로컬 PaddleOCR 사용 가능 시 실행
- 목적:
  - 실제 법인 증빙 PDF의 OCR/분류 품질 확인
  - 시간이 오래 걸리므로 기본 회귀 테스트에는 포함하지 않음

### 3. 브라우저 UX 시나리오 테스트
- 대상: 향후 Playwright 시나리오
- 목적:
  - 같은 흐름이 실제 화면에서도 클릭/입력/다운로드까지 되는지 검증
  - 영상 생성 스크립트와 공유 가능

## 이번 작업 범위

이번 반복에서는 1번 빠른 파이프라인 회귀 테스트를 우선 구현한다.

테스트 이름:

```text
test_service_rocket_pitch_demo_pipeline_flow
```

검증 기준:

- 사업자등록증 증빙 업로드 후 승인하면 새 법인이 생성된다.
- 중소기업확인서 증빙 업로드 후 승인하면 기존 법인 프로필에 인증/기업규모가 병합된다.
- 대시보드에서 법인 카운트가 증가한다.
- 나라장터 공고 저장/분석 후 요구조건 후보가 생성된다.
- 기준문서 업로드 후 청크와 JSON basis index 검색 결과가 생성된다.
- 공고-법인 비교 결과에 준비됨/부족/확인 필요 항목이 포함된다.
- 판단 run은 최종 합격 단정 없이 부족조건 중심 결과와 citation 후보를 만든다.
- 계약서 DOCX 초안 생성 후 다운로드 가능한 파일이 생성된다.
- 운영 이력에 판단 run과 계약서 생성 이력이 남는다.
- 응답 전체에 `eligible`, `지원 가능` 같은 최종 확정 표현이 노출되지 않는다.

## 반복 절차

1. 계획 문서 작성
2. 테스트 코드 추가
3. 테스트 실행
4. 실패 지점 분석
5. 버그 수정
6. 같은 테스트 재실행
7. 관련 기존 테스트 재실행
8. `docs/work-log.md`에 결과 기록

## 1차 실행 결과

### 테스트 실행
- 추가 테스트: `backend/tests/test_api_flows.py`
- 테스트명: `test_service_rocket_pitch_demo_pipeline_flow`
- 실행 흐름:
  - 법인 증빙 업로드/승인
  - 중소기업확인서 업로드/승인
  - 대시보드 확인
  - 나라장터 공고 저장/분석
  - 요구조건 후보/구조화 입력 확인
  - 기준문서 업로드/청킹/인덱싱
  - 기준문서 검색
  - 공고-법인 부족조건 미리보기
  - 판단 run 생성
  - 계약서 DOCX 미리보기/생성/다운로드
  - 작업 이력과 운영 요약 확인

### 발견된 문제

#### 문제 1. 계약서 DOCX 검증 방식이 표 텍스트를 읽지 못함
- 성격: 테스트 코드 문제
- 원인: 계약서 본문 주요 값은 DOCX 표 셀에 들어가는데, 테스트가 문단 텍스트만 검사했다.
- 수정: 문단과 표 셀 텍스트를 함께 읽도록 테스트를 수정했다.

#### 문제 2. 기준문서 최초 업로드 처리가 작업 이력에 남지 않음
- 성격: 실제 서비스 버그
- 원인: 기준문서 `reprocess`는 `basis_document_processing` 작업 이력을 남기지만, 최초 업로드 후 자동 처리 흐름은 이력을 남기지 않았다.
- 영향: 시연 흐름 마지막 단계의 운영 대시보드/작업 이력에서 기준문서 처리 이력을 확인할 수 없었다.
- 수정: 기준문서 업로드 API에서도 `record_operation_run()`을 호출해 `basis_document_processing` 이력을 남기도록 보강했다.

#### 문제 3. 최종 판정 금지어 테스트가 안내 문구까지 오탐함
- 성격: 테스트 코드 문제
- 원인: `지원 가능` 문자열 전체를 금지해 `지원 가능한 첨부`나 금지 안내 문맥까지 실패시켰다.
- 수정: 실제 verdict 필드/값 중심으로 검증을 좁혔다.

### 재테스트 결과
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v`: 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 106개 통과
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 13개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음

## 예상 버그 탐지 포인트

- 증빙 승인 후 법인 프로필 병합 누락
- 공고 저장/분석 비동기 작업 완료 대기 실패
- 요구조건 후보가 구조화되지 않는 문제
- basis JSON index와 DB 청크 불일치
- 판단 run에서 citation 후보가 비어 있는 문제
- 계약서 생성 시 judgment run 연결 실패
- 작업 이력 누락
- 최종 판정처럼 보이는 금지 문구 노출

## 검증 명령

```powershell
cd backend
py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v
py -3.13 -m unittest tests.test_api_flows -v
py -3.13 -m unittest tests.test_frontend_contracts -v
cd ..
npm run build
py -3.13 scripts\check-encoding.py
git diff --check
```

---

# AI / Engineering Version (English)

## Purpose
Convert the Rocket Pitch demo flow into an end-to-end service pipeline regression test.

## Scope
The first implementation is a fast backend API pipeline test using Flask test client and synthetic DOCX/PDF fixtures. It does not depend on live Nara API, LLM calls, or real OCR.

## Scenario
1. Upload corporation evidence.
2. Approve extracted candidates and create/update corporation profile.
3. Check dashboard/operations state.
4. Save and analyze a Nara notice.
5. Validate extracted notice requirements.
6. Upload/index a basis document.
7. Run notice-corporation comparison.
8. Create a gap-first judgment run.
9. Generate/download a DOCX contract draft.
10. Verify operation history.

## Regression Criteria
- The pipeline must produce persisted artifacts at each stage.
- Judgment output must remain gap-first and must not expose final eligibility wording.
- Contract generation must produce a downloadable DOCX.
- Operation history must include judgment and contract runs.

## Future Extensions
- Add an opt-in real-PDF test using `source/test_doc/`.
- Share the scenario with Playwright demo-video recording.

## First Run Result
- Added `test_service_rocket_pitch_demo_pipeline_flow`.
- Found and fixed one real service issue: initial basis-document upload processing did not create a `basis_document_processing` operation run.
- Adjusted test assertions for DOCX table text and verdict wording false positives.
- Verified with targeted pipeline test, full API flow tests, frontend contract tests, frontend build, encoding check, and whitespace check.
