# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`의 Phase 2 개발 범위를 실제 구현 가능한 세부 단계로 나누고, Phase 2.5로 분리해야 할 실험/고도화 범위를 명확히 기록합니다.

Phase 2의 목표는 기준 PDF를 일반 업로드 문서와 분리된 재사용 지식 자산으로 저장하고, `텍스트 추출 -> OCR -> 정규화 -> 청킹 -> 로컬 인덱싱 -> 검색`까지 준비하는 것입니다.

Phase 2에서는 최종 자격 판단, 근거 조항 출력, 법인-공고 확정 매칭, 기준문서 기반 판정 UI를 구현하지 않습니다.

## 현재 전제
- Phase 1.7은 저장 공고 요구조건 후보와 법인 준비상태를 비교하는 `부족조건 미리보기`까지 구현한다.
- 현재 실제 백엔드는 Flask 기반이며 Phase 2에서도 FastAPI 마이그레이션을 섞지 않는다.
- 기준문서는 일반 프로젝트 문서와 다른 도메인이다.
- 기준문서는 PDF만 허용한다.
- 사용자가 직접 청크를 나누는 UX는 만들지 않는다.
- OCR 엔진이 없어도 업로드/처리 흐름은 실패하지 않고 `needs_ocr_setup` 또는 `unavailable` 상태로 degrade 해야 한다.
- 기준문서 청크는 향후 citation 가능한 구조를 가져야 한다.

## Phase 2 비범위
- 최종 자격 판정처럼 보이는 확정형 결과
- 근거 조항 citation 렌더링
- 법인 대 공고 요구조건 확정 매칭
- 기준문서 규칙 자동 확정
- 나라장터 HTML 크롤링
- HWP/HWPX 기준문서 파싱
- 로그인/권한 체계
- 클라우드 벡터 DB 의존 운영

## Phase 2A: 기준문서 도메인 골격
목표는 일반 업로드 문서, 나라장터 저장 공고, 기준문서를 DB와 파일 저장 경로에서 명확히 분리하는 것입니다.

작업:
- `basis_documents` 테이블 추가
- `basis_document_chunks` 테이블 추가
- 필요 시 `basis_document_processing_runs` 또는 처리 이력 필드 설계
- 저장 경로를 `storage/basis/`로 분리
- 기준문서 상태값 정의
  - `uploaded`
  - `parsing`
  - `ocr_processing`
  - `normalizing`
  - `chunking`
  - `indexing`
  - `completed`
  - `failed`
  - `needs_ocr_setup`
- 기준문서 메타데이터 필드 정의
  - 제목
  - 카테고리
  - 문서 버전
  - 발행기관
  - 시행일
  - 출처 URL
  - 메모
  - 파일 hash
  - 처리 상태/오류 메시지
- 기존 SQLite 스키마 보정 방식과 같은 안전한 마이그레이션 흐름 사용

완료 기준:
- 기준 PDF를 프로젝트 문서와 섞지 않고 별도 테이블/스토리지에 저장할 수 있다.
- 기존 DB 파일에서 앱 시작 시 스키마 보정이 안전하게 수행된다.
- 기준문서 상태와 오류 메시지를 API 응답으로 내려줄 수 있다.

## Phase 2B: 기준문서 CRUD/API
목표는 프론트엔드 없이도 API만으로 기준문서 생명주기를 관리할 수 있게 만드는 것입니다.

작업:
- `GET /api/basis-documents`
- `POST /api/basis-documents`
- `GET /api/basis-documents/{id}`
- `PATCH /api/basis-documents/{id}`
- `DELETE /api/basis-documents/{id}`
- `POST /api/basis-documents/{id}/reprocess`
- `GET /api/basis-documents/{id}/chunks`
- PDF 외 파일 업로드 차단
- 삭제 시 원본 파일, 청크, 인덱스 참조 정리
- 재처리 시 이전 결과를 안전하게 교체

완료 기준:
- PDF 업로드, 목록 조회, 상세 조회, 메타데이터 수정, 삭제, 재처리 요청이 API 테스트로 검증된다.
- PDF가 아닌 파일은 명확한 오류로 거절된다.
- 삭제 후 고아 청크/파일 참조가 남지 않는다.

## Phase 2C: 기준 PDF 파싱/OCR/정규화 파이프라인
목표는 기준 PDF에서 검색 가능한 텍스트를 안정적으로 확보하는 것입니다.

작업:
- 기존 `parser.py`의 PyMuPDF 추출 흐름 재사용
- 기존 `ocr.py`의 OCR 어댑터 재사용
- 텍스트 PDF는 PyMuPDF 우선 추출
- 스캔 PDF 또는 텍스트 부족 PDF는 OCR 후보로 처리
- OCR 엔진 미설치 시 업로드 자체는 성공시키고 상태를 `needs_ocr_setup`으로 저장
- 페이지별 텍스트, 문자 수, OCR 여부, 엔진명, confidence 메타데이터 저장
- 한글 깨짐, 과도한 공백, 쪽번호, 머리말/꼬리말, 목차성 라인 정규화
- 처리 중 예외 발생 시 원본 파일과 오류 상태 보존

완료 기준:
- 텍스트 PDF와 스캔 PDF 모두 처리 상태가 재현 가능하게 기록된다.
- OCR 실패/미설치 상태에서도 수동 재처리 또는 환경 설정 후 재처리가 가능하다.
- 페이지 단위 텍스트와 메타데이터가 청킹 단계에 전달된다.

## Phase 2D: 자동 청킹
목표는 기준문서를 향후 검색과 citation에 적합한 단위로 나누는 것입니다.

작업:
- 페이지/섹션 기반 1차 분할
- 길이 기준 2차 분할
- 문서 제목/장/절/조/항 후보 추출
- 청크 메타데이터 저장
  - 기준문서 ID
  - 문서 버전
  - 카테고리
  - 페이지 번호
  - 섹션 제목 후보
  - 조항/항목 후보
  - chunk index
  - chunk hash
  - normalized text
- 같은 입력에 대해 가능한 한 동일한 청크가 생성되도록 deterministic 정책 유지
- 재처리 시 이전 청크를 무단 파괴하지 않고 처리 run 단위로 안전하게 교체

완료 기준:
- 기준문서 하나에서 청크 목록이 생성된다.
- 각 청크가 원문 문서, 버전, 페이지, 섹션 맥락을 가진다.
- 재처리 후 이전 청크/새 청크 관계가 추적 가능하다.

## Phase 2E: 로컬 벡터 인덱싱
목표는 기준문서 청크를 로컬 검색 인덱스에 연결하는 것입니다.

작업:
- Qdrant local을 1차 목표로 검토
- Chroma는 대안으로 유지
- 임베딩 provider/model 설정 구조 추가
- 청크별 인덱싱 상태 저장
  - `vector_status`
  - `vector_id`
  - `embedding_model`
  - `indexed_at`
  - `index_error_message`
- 인덱싱 실패 청크만 재시도 가능하게 설계
- 재처리 시 이전 벡터를 안전하게 삭제/교체
- 로컬 벡터 저장소가 실행되지 않는 경우 `indexing_unavailable` 또는 `failed`로 degrade

완료 기준:
- 기준문서 청크가 로컬 벡터 저장소에 인덱싱된다.
- DB 청크와 벡터 ID가 연결된다.
- 벡터 저장소가 없어도 전체 앱이 중단되지 않는다.

## Phase 2F: 기준문서 검색 API
목표는 Phase 3 판단 엔진 전에 기준문서 검색 품질을 검증할 수 있게 하는 것입니다.

작업:
- `POST /api/basis-search`
- 입력:
  - query
  - category
  - document_version
  - top_k
  - metadata filters
- 출력:
  - basis document ID/title
  - chunk ID
  - chunk text
  - page
  - section
  - score
  - citation 후보 ID
  - vector metadata
- 검색 결과는 판단 결과가 아니라 검색 후보임을 명시
- citation 가능한 식별자는 준비하되 UI에서 근거 조항처럼 확정 렌더링하지 않음

완료 기준:
- `지역제한`, `중소기업확인서`, `직접생산확인`, `입찰참가자격` 같은 질의로 관련 청크가 검색된다.
- 검색 API 결과가 Phase 3 판단 엔진 입력으로 확장 가능한 구조를 가진다.

## Phase 2G: 기준문서 관리 UX
목표는 관리자가 포탈에서 기준문서 업로드부터 처리 상태 확인까지 수행할 수 있게 하는 것입니다.

작업:
- 비활성화된 `기준문서 관리` 메뉴 활성화
- 기준 PDF 업로드 폼
- 기준문서 목록
- 카테고리/버전/시행일/메모 입력
- 처리 상태 배지
- 상세 화면
- 청크 미리보기
- 재처리 버튼
- 실패 사유 표시
- OCR/벡터 인덱스 설정 상태 안내
- 기준문서가 프로젝트 문서가 아니라 재사용 지식 자산임을 UX 문구로 명확히 표시

완료 기준:
- 사용자가 기준 PDF를 업로드하고 처리 상태를 확인할 수 있다.
- 청크 미리보기를 통해 파싱/청킹 품질을 검토할 수 있다.
- 실패 시 다음 행동이 명확히 보인다.

## Phase 2H: 안정화/회귀 테스트
목표는 Phase 3 판단 엔진으로 넘어가기 전에 기준문서 파이프라인의 신뢰도를 확보하는 것입니다.

작업:
- 기준 PDF 업로드 API 테스트
- PDF 외 파일 거절 테스트
- 텍스트 PDF 파싱 테스트
- 스캔 PDF OCR fallback 테스트
- OCR 미설치 degrade 테스트
- 청크 생성 테스트
- 재처리 시 이전 청크/벡터 안전 교체 테스트
- 검색 API 테스트
- 프론트 빌드와 스모크 테스트
- 실제 기준 PDF 3~5개 수동 QA

완료 기준:
- 기준문서 업로드 -> 추출 -> OCR -> 정규화 -> 청킹 -> 인덱싱 -> 검색이 한 흐름으로 검증된다.
- 전체 백엔드 테스트, 프론트 빌드, 스모크 테스트가 통과한다.
- 실제 기준 PDF 샘플 기준 주요 실패 케이스가 문서화된다.

## Phase 2 완료 기준
아래 조건을 만족하면 Phase 2를 완료로 봅니다.

- 기준 PDF가 일반 프로젝트 문서와 분리된 도메인으로 저장된다.
- 기준문서 CRUD/API/UX가 동작한다.
- 기준 PDF 텍스트 추출과 OCR fallback이 상태 기반으로 동작한다.
- 기준문서 청크가 자동 생성되고 메타데이터를 가진다.
- 청크가 로컬 벡터 인덱스에 연결된다.
- 기준문서 검색 API로 관련 청크를 조회할 수 있다.
- 재처리 시 이전 청크/벡터가 안전하게 교체된다.
- 최종 판단/근거 조항 렌더링은 여전히 노출되지 않는다.

## Phase 2 권장 개발 순서
1. Phase 2A: 기준문서 도메인/DB
2. Phase 2B: 기준문서 CRUD/API
3. Phase 2C: 파싱/OCR/정규화 파이프라인
4. Phase 2D: 자동 청킹
5. Phase 2E: 로컬 벡터 인덱싱
6. Phase 2F: 기준문서 검색 API
7. Phase 2G: 기준문서 관리 UX
8. Phase 2H: 안정화/회귀 테스트

## Phase 2A-H 구현 기록 (2026-05-22)
이번 개발에서 Phase 2A부터 Phase 2H까지 기준문서 MVP를 구현했다.

구현 내용:
- Phase 2A: `basis_documents`, `basis_document_chunks` 테이블과 `storage/basis/`, `storage/basis-index/` 저장 경로를 추가했다.
- Phase 2B: 기준문서 업로드/목록/상세/수정/삭제/재처리/청크 조회 API를 추가했다.
- Phase 2C: 기존 PyMuPDF 파서와 OCR 어댑터를 재사용해 기준 PDF 처리 파이프라인을 연결했다.
- Phase 2D: 정규화된 텍스트를 자동 청킹하고 페이지/섹션/해시/토큰 메타데이터를 저장했다.
- Phase 2E: 외부 벡터 DB 의존 없이 `local-token-v1` 로컬 JSON 인덱스를 우선 구현했다.
- Phase 2F: `POST /api/basis-search` 검색 API를 추가하고, 검색 결과를 판단이 아닌 citation 후보 청크로만 반환한다.
- Phase 2G: 포탈의 `기준문서 관리` 메뉴를 활성화하고 업로드, 목록, 상세, 메타데이터 편집, 재처리, 청크 미리보기, 검색 UI를 추가했다.
- Phase 2H: 단계별 테스트와 전체 회귀 테스트를 수행했다.

검증 결과:
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2a_2b_basis_document_crud_and_pdf_guard -v`: 통과
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2c_2d_basis_processing_extracts_normalizes_and_chunks tests.test_api_flows.ApiFlowTests.test_phase2c_basis_blank_pdf_degrades_when_ocr_is_unavailable -v`: 통과
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2e_2f_basis_index_and_search_returns_candidates_only -v`: 통과
- `py -3.13 -m unittest discover -s tests -v`: 58개 테스트 중 56개 통과, 2개 opt-in 테스트 skip
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인
- `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`

남은 운영 QA:
- 실제 기준 PDF 3~5개 수동 QA는 문서 샘플 선정이 필요하다.
- 한글 텍스트가 이미지로만 들어 있는 기준 PDF는 OCR 엔진 설치 후 재처리 품질을 별도 확인해야 한다.

## Phase 2 운영 QA 기록 - 나라장터 랜덤 공고문 PDF 10개 (2026-05-22)
사용자 요청에 따라 나라장터 API에서 공고문 PDF 10개를 랜덤 순서로 내려받아 Phase 2 기준문서 파이프라인 운영 QA를 수행했다.

QA 설계:
- 신규 스크립트 `scripts/fetch-nara-phase2-basis-qa-samples.py`를 추가했다.
- 샘플 저장 경로는 `backend/tests/nara-phase2-basis-qa-samples/`이며 Git에는 포함하지 않는다.
- 나라장터 공고문 PDF는 제품 데이터로 저장하지 않고, QA 전용 샘플로만 사용한다.
- 각 PDF를 Phase 2 기준문서 API에 업로드해 `추출 -> OCR 확인 -> 정규화 -> 청킹 -> local-token-v1 인덱싱 -> 검색`을 검증했다.
- 검색 결과는 최종 판단이 아니라 citation 후보 청크인지 확인했다.
- `RUN_NARA_PHASE2_QA=1`일 때만 실행되는 opt-in 테스트 `backend/tests/test_nara_phase2_basis_qa_samples.py`를 추가했다.

실행 명령:
```powershell
py -3.13 scripts\fetch-nara-phase2-basis-qa-samples.py --date-from 20260501 --date-to 20260522 --target-count 10 --num-of-rows 100 --max-pages-per-window 6 --window-days 7 --min-text-chars 300
$env:RUN_NARA_PHASE2_QA='1'; py -3.13 -m unittest discover -s tests -p 'test_nara_phase2_basis_qa_samples.py' -v; Remove-Item Env:\RUN_NARA_PHASE2_QA
```

수집 결과:
- 기간: `20260501` ~ `20260522`
- 랜덤 시드: `20260522203720`
- 샘플 수: 10개 / 10개
- skip: 6개
- 모든 샘플에서 `processing_status=completed`, `index_status=completed`, 검색 결과 1개 이상을 확인했다.

샘플:
- `R26BK01501003-000`: 2026년도 사방댐설치사업(상주 남장 산88-4), 13,840자, 10청크, 10벡터
- `R26BK01501098-001`: 비인면 구복리 개거수로 정비공사, 7,342자, 6청크, 6벡터
- `R26BK01501018-000`: 2026년도 계류보전사업(성주 초전 용봉), 13,841자, 10청크, 10벡터
- `R26BK01501129-000`: 지방하천 만덕천 재해복구사업, 7,948자, 6청크, 6벡터
- `R26BK01501000-000`: 2026년도 계류보전사업(상주 공성 도곡), 13,969자, 10청크, 10벡터
- `R26BK01501008-000`: 2026년도 사방댐설치사업(상주 외서 백전), 13,967자, 10청크, 10벡터
- `R26BK01501131-000`: 마산면 마명리 배수로 공사, 7,336자, 6청크, 6벡터
- `R26BK01501012-000`: 2026년도 계류보전사업(고령 덕곡 예), 13,839자, 10청크, 10벡터
- `R26BK01501088-000`: 문곡지구 소규모 배수개선사업(2차), 7,344자, 6청크, 6벡터
- `R26BK01500999-001`: 2026년도 계류보전사업(김천 지례 울곡), 13,970자, 10청크, 10벡터

검증 결과:
- `py -3.13 -m py_compile scripts\fetch-nara-phase2-basis-qa-samples.py backend\tests\test_nara_phase2_basis_qa_samples.py`: 통과
- opt-in Phase 2 QA 테스트: 2개 테스트 통과

남은 QA 메모:
- 이번 QA는 실제 나라장터 공고문 PDF를 사용한 파이프라인 운영 검증이다.
- 법령/예규 같은 진짜 기준문서 PDF의 검색 품질 평가는 별도 샘플 선정 후 추가로 수행할 수 있다.

## 공고문 PDF 테스트 공용 캐시 정책 (2026-05-22)
공고문 PDF 관련 테스트는 앞으로 나라장터 API를 매번 호출하지 않고, 이미 다운로드한 로컬 PDF 샘플을 우선 사용한다.

구성:
- 공용 샘플 경로: `backend/tests/nara-notice-pdf-samples/`
- 공용 manifest: `backend/tests/nara-notice-pdf-samples/manifest.json`
- 공용 유틸: `backend/tests/nara_pdf_sample_cache.py`
- 수집 스크립트: `scripts/fetch-nara-notice-pdf-samples.py`

우선순위:
1. Phase별 manifest 환경변수
   - `NARA_PHASE17_SAMPLE_MANIFEST`
   - `NARA_PHASE2_SAMPLE_MANIFEST`
2. 공용 manifest 환경변수
   - `NARA_NOTICE_PDF_SAMPLE_MANIFEST`
3. 공용 캐시 manifest
   - `backend/tests/nara-notice-pdf-samples/manifest.json`
4. 기존 Phase별 샘플 폴더 fallback
   - `backend/tests/nara-pdf-samples/manifest.json`
   - `backend/tests/nara-phase2-basis-qa-samples/manifest.json`

신규 수집 결과:
- 나라장터 API로 테스트용 공고문 PDF 30개를 랜덤 다운로드했다.
- 기간: `20260401` ~ `20260522`
- 랜덤 시드: `20260522204523`
- 샘플 수: 30개 / 30개
- 모든 샘플은 PDF 형식, 텍스트 추출, 요구조건 후보 추출, 최종판단 문구 부재 검증을 통과했다.

검증:
- Phase 1.7/Phase 2 opt-in 테스트가 공용 30개 샘플을 재사용하는 것을 확인했다.
- 기본 테스트 실행에서는 opt-in PDF 테스트가 skip되어 네트워크와 로컬 샘플에 의존하지 않는다.

## Phase 2.5로 분리하는 이유
Phase 2.5는 Phase 2와 Phase 3 사이의 완충 단계입니다.

Phase 2는 기준문서를 검색 가능한 지식 자산으로 만드는 단계이고, Phase 3는 그 지식 자산을 사용해 법인/공고 요구조건과 연결하는 판단 엔진 단계입니다. 두 단계를 바로 이어 붙이면 RAG 검색 결과를 과신하거나 citation 없는 조건을 판단 근거로 사용하는 위험이 있습니다.

따라서 Phase 2.5에서는 `판단 엔진`을 만들기 전에 기준문서 규칙 추출, 공고 요구조건 구조화, citation 품질 평가를 실험합니다.

## Phase 2.5A: 기준문서 규칙 추출 실험
목표는 기준문서 청크에서 판단에 쓸 수 있을 법한 조건 후보를 구조화해 보는 것입니다.

작업:
- 기준문서 청크에서 규칙 후보 추출
- `basis_rules` 또는 실험용 rule candidate 테이블 설계
- 규칙 유형 분류
  - 지역 제한
  - 면허/업종
  - 기업유형
  - 제출서류
  - 금액/실적
  - 예외/주의사항
- 각 규칙에 원문 chunk ID와 page/section 연결
- LLM 출력은 JSON schema 검증 후 후보로만 저장
- 확정 규칙처럼 자동 사용하지 않음

완료 기준:
- 기준문서 일부에서 구조화 규칙 후보를 생성할 수 있다.
- 모든 규칙 후보가 원문 청크와 연결된다.
- citation 없는 규칙 후보는 판단 입력으로 승격되지 않는다.

## Phase 2.5B: 공고 요구조건 구조화 고도화
목표는 Phase 1.7의 rule-based 요구조건 후보를 Phase 3 판단 입력에 가까운 구조로 다듬는 것입니다.

작업:
- 저장 공고 요구조건 후보 스키마 개선
- 요구조건 유형별 confidence 기준 정리
- 면허/업종/기업유형/제출서류 표현 사전 확장
- 금액/기간/실적 조건은 자동 충족 판단하지 않고 `needs_review` 계열로 유지
- 공고 원문/첨부 텍스트 source span 저장 검토
- 재추출 시 기존 비교 이력 무효화 정책 유지

완료 기준:
- 대표 공고 샘플에서 요구조건 후보 누락과 오탐이 줄어든다.
- Phase 3 매칭 엔진이 사용할 수 있는 입력 스키마가 정리된다.

## Phase 2.5C: 검색 품질과 citation 평가
목표는 검색 결과가 향후 근거로 사용할 만큼 원문 연결성이 좋은지 평가하는 것입니다.

작업:
- 대표 질문 세트 작성
  - `중소기업 확인서가 필요한 조건`
  - `직접생산확인증명서 제출 조건`
  - `지역 제한`
  - `입찰참가자격 등록`
- 검색 top_k 결과 수동 평가
- chunk/page/section citation 후보의 정확도 점검
- 너무 긴 청크, 너무 짧은 청크, 중복 청크 튜닝
- category/version 필터 품질 확인

완료 기준:
- 대표 질문 세트에서 관련 청크가 상위 결과에 나온다.
- citation 후보가 사람이 원문을 확인하기에 충분하다.
- Phase 3에서 citation 없는 조건을 확정 판단 근거로 쓰지 않는 정책이 테스트 가능하다.

## Phase 2.5D: Phase 3 판단 엔진 입력 계약 확정
목표는 Phase 3에서 사용할 입력/출력 계약을 미리 고정하는 것입니다.

작업:
- 공고 요구조건 후보 스키마 확정
- 법인 비교 프로필 스키마 보강 필요점 정리
- 기준문서 검색 결과 스키마 확정
- 판단 엔진 입력 payload 초안 작성
- 판단 엔진 출력 상태 초안 작성
  - `matched`
  - `missing`
  - `uncertain`
  - `needs_review`
  - `not_applicable`
  - `citation_missing`
- 확정형 자격 판정 문구는 제품 오너 승인 전까지 사용하지 않음
- 준비 가이드/부족 조건 중심 출력 원칙 유지

완료 기준:
- Phase 3 판단 엔진이 어떤 데이터를 받아야 하는지 문서화된다.
- 확정 판단 전 반드시 citation과 불확실성 노트를 요구하는 계약이 명확해진다.

## Phase 2.5 비범위
- 최종 자격 판정 UI
- 자동 확정 판정 출력
- 근거 조항 최종 렌더링
- 법인 정보 자동 수정
- 외부 기관 진위확인 API 연동
- 나라장터 HTML 크롤링

## Phase 2.5 완료 기준
아래 조건을 만족하면 Phase 2.5를 완료로 봅니다.

- 기준문서 규칙 후보 추출 실험 결과가 문서화된다.
- 공고 요구조건 후보 스키마가 Phase 3 입력에 맞게 정리된다.
- 기준문서 검색 결과와 citation 후보 품질을 대표 질문 세트로 평가했다.
- Phase 3 판단 엔진의 입력/출력 계약 초안이 확정된다.
- citation 없는 조건은 확정 판단에 사용하지 않는 정책이 유지된다.

## Questions for Product Owner
- 기준문서 카테고리와 우선순위는 누가 관리할까요?
- Phase 2 기준 PDF 샘플은 어떤 문서 3~5개를 우선 등록할까요?
- 기준문서 버전 충돌 시 최신본만 사용할까요, 과거 버전도 검색 가능하게 둘까요?
- 로컬 Qdrant 실행을 기본 설치에 포함할까요, 선택 설치로 둘까요?
- Phase 2.5 규칙 후보를 관리자가 승인하는 UX가 필요한가요?
- Phase 3 전에 기준문서 검색 결과만 따로 확인하는 운영 화면이 필요한가요?

## 현재 코드 기준 메모
최종 갱신일: 2026-06-07

- Phase 2 기준문서 업로드/추출/OCR degrade/청킹/JSON basis index/RAG 검색/규칙 후보 관리 흐름은 구현되어 있습니다.
- PDF reader 기본값은 OpenDataLoader 우선 `auto` 모드이며 PyMuPDF는 fallback입니다.
- 기준문서 검색 source는 `storage/basis-index/basis-index.json`입니다.
- 손상/누락/불일치 JSON 인덱스는 검색, 규칙 후보 승인, 판단 citation 사용을 차단합니다.
- 기준문서 재처리 실패 시 기존 completed/indexed 지식을 보존하는 보강이 적용되어 있습니다.

---

# AI / Engineering Version (English)

## Current Code Note
Last updated: 2026-06-07

- Phase 2 basis upload/extraction/OCR degrade/chunking/JSON basis index/RAG search/rule-candidate management flow is implemented.
- Default PDF reader is OpenDataLoader-first `auto`; PyMuPDF is fallback.
- Basis retrieval source is `storage/basis-index/basis-index.json`.
- Missing/corrupt/inconsistent JSON index state blocks search, rule approval, and judgment citation usage.
- Basis reprocessing hardening preserves existing completed/indexed knowledge on failure.

## Purpose
This document breaks Phase 2 into implementation-ready milestones and separates Phase 2.5 as an experimental bridge before the final judgment engine.

Phase 2 turns basis PDFs into reusable knowledge assets through `extract -> OCR -> normalize -> chunk -> local index -> search`.

Phase 2 must not implement final eligibility decisions, evidence citation rendering, final corporation-notice matching, or judgment UI.

## Baseline Assumptions
- Phase 1.7 provides gap preview only.
- The current backend is Flask; Phase 2 must not mix in a FastAPI migration.
- Basis documents are separate from project documents and saved Nara notices.
- Basis documents accept PDF only.
- There is no manual chunking UX.
- Missing OCR dependencies must degrade to `needs_ocr_setup` or `unavailable`.
- Basis chunks must be citation-ready for future phases.

## Phase 2 Non-Scope
- Final verdict-style decisioning
- Final evidence citation rendering
- Final corporation-vs-notice matching
- Automatically confirmed basis rules
- Nara HTML crawling
- HWP/HWPX parsing
- Auth/permissions
- Cloud vector DB dependency

## Phase 2A: Basis Domain Skeleton
Goal: keep basis documents separate in database and storage.

Tasks:
- Add `basis_documents`.
- Add `basis_document_chunks`.
- Optionally add `basis_document_processing_runs` or equivalent processing history.
- Store files under `storage/basis/`.
- Define statuses: `uploaded`, `parsing`, `ocr_processing`, `normalizing`, `chunking`, `indexing`, `completed`, `failed`, `needs_ocr_setup`.
- Define metadata: title, category, version, issuing agency, effective date, source URL, memo, file hash, status, error message.
- Use the current safe SQLite schema repair style.

Done:
- Basis PDFs can be stored separately from project documents.
- Existing SQLite files can be safely upgraded.
- Status and error metadata are exposed through APIs.

## Phase 2B: Basis CRUD/API
Goal: manage basis document lifecycle through APIs.

Tasks:
- `GET /api/basis-documents`
- `POST /api/basis-documents`
- `GET /api/basis-documents/{id}`
- `PATCH /api/basis-documents/{id}`
- `DELETE /api/basis-documents/{id}`
- `POST /api/basis-documents/{id}/reprocess`
- `GET /api/basis-documents/{id}/chunks`
- Reject non-PDF uploads.
- Clean source files, chunks, and index references on delete.
- Safely replace previous processing results on reprocess.

Done:
- Upload/list/detail/update/delete/reprocess flows are API-tested.
- Non-PDF files are rejected clearly.
- Delete leaves no orphan chunks or file references.

## Phase 2C: PDF Parsing/OCR/Normalization
Goal: obtain reliable searchable text from basis PDFs.

Tasks:
- Reuse `parser.py` and PyMuPDF extraction.
- Reuse `ocr.py` and OCR adapters.
- Prefer text extraction for text PDFs.
- Use OCR fallback for scanned or text-poor PDFs.
- Preserve upload success when OCR is missing and set `needs_ocr_setup`.
- Store page text and metadata: char count, OCR status, engine, confidence.
- Normalize Korean text, spacing, page numbers, headers/footers, and TOC-like lines.
- Preserve source file and error state on processing exceptions.

Done:
- Text PDFs and scanned PDFs produce reproducible processing status.
- OCR failures remain reprocessable.
- Page text and metadata are passed to chunking.

## Phase 2D: Automatic Chunking
Goal: split basis documents into searchable and citation-ready chunks.

Tasks:
- First split by page/section.
- Second split by length.
- Detect title/chapter/article/paragraph candidates.
- Store chunk metadata: document ID, version, category, page, section, article candidate, chunk index, hash, normalized text.
- Keep deterministic chunking where practical.
- Safely replace previous chunks during reprocessing with traceability.

Done:
- Basis documents produce chunk lists.
- Each chunk keeps source document, version, page, and section context.
- Reprocessing remains traceable.

## Phase 2E: Local Vector Indexing
Goal: connect basis chunks to a local vector index.

Tasks:
- Prefer Qdrant local.
- Keep Chroma as an alternative.
- Add embedding provider/model settings.
- Store `vector_status`, `vector_id`, `embedding_model`, `indexed_at`, and `index_error_message`.
- Retry failed chunks only.
- Safely delete/replace old vectors on reprocess.
- Degrade if the local vector store is unavailable.

Done:
- Chunks are indexed in a local vector store.
- DB chunks link to vector IDs.
- Missing vector store does not crash the app.

## Phase 2F: Basis Search API
Goal: validate retrieval quality before Phase 3 judgment.

Tasks:
- Add `POST /api/basis-search`.
- Inputs: query, category, document version, top_k, metadata filters.
- Outputs: document ID/title, chunk ID, chunk text, page, section, score, citation candidate ID, vector metadata.
- Mark results as retrieval candidates, not decisions.
- Prepare citation IDs without final citation rendering.

Done:
- Queries such as `region restriction`, `SME confirmation`, `direct production confirmation`, and `bid participation qualification` return relevant chunks.
- API output is usable as future Phase 3 input.

## Phase 2G: Basis Management UX
Goal: allow administrators to upload and monitor basis documents in the portal.

Tasks:
- Enable the disabled `Basis Documents` menu.
- Add upload form.
- Add list/detail views.
- Add category/version/effective date/memo inputs.
- Show processing badges.
- Add chunk preview.
- Add reprocess button.
- Show failure reasons.
- Show OCR/vector index setup status.
- Explain that basis documents are reusable knowledge assets, not project documents.

Done:
- Users can upload basis PDFs and inspect processing status.
- Users can preview chunks.
- Failures show clear next actions.

## Phase 2H: Stabilization/Regression
Goal: harden the basis pipeline before Phase 3.

Tasks:
- Basis upload API tests.
- Non-PDF rejection tests.
- Text PDF parsing tests.
- Scanned PDF OCR fallback tests.
- Missing OCR degradation tests.
- Chunk generation tests.
- Safe reprocess replacement tests for chunks and vectors.
- Search API tests.
- Frontend build and smoke test.
- Manual QA with 3-5 real basis PDFs.

Done:
- Upload -> extraction -> OCR -> normalization -> chunking -> indexing -> search is tested end-to-end.
- Backend tests, frontend build, and smoke tests pass.
- Major sample PDF failure cases are documented.

## Phase 2 Done Criteria
Phase 2 is complete when:
- Basis PDFs are stored in a separate domain.
- Basis CRUD/API/UX works.
- PDF extraction and OCR fallback are status-driven.
- Chunks are generated with metadata.
- Chunks are linked to a local vector index.
- Search API returns relevant chunks.
- Reprocessing safely replaces chunks/vectors.
- Final judgment and final citation rendering remain hidden.

## Recommended Phase 2 Order
1. Phase 2A: domain and DB
2. Phase 2B: CRUD/API
3. Phase 2C: parsing/OCR/normalization
4. Phase 2D: automatic chunking
5. Phase 2E: local vector indexing
6. Phase 2F: basis search API
7. Phase 2G: management UX
8. Phase 2H: stabilization/regression

## Phase 2A-H Implementation Record (2026-05-22)
This development pass implemented the Phase 2 basis-document MVP from Phase 2A through Phase 2H.

Implemented:
- Phase 2A: added `basis_documents`, `basis_document_chunks`, `storage/basis/`, and `storage/basis-index/`.
- Phase 2B: added upload/list/detail/update/delete/reprocess/chunk APIs.
- Phase 2C: wired the current PyMuPDF parser and OCR adapter into basis processing.
- Phase 2D: normalized text, generated chunks, and stored page/section/hash/token metadata.
- Phase 2E: implemented a local `local-token-v1` JSON index without requiring an external vector DB.
- Phase 2F: added `POST /api/basis-search`; results are retrieval/citation candidates only, not decisions.
- Phase 2G: enabled the portal basis-document menu and added upload, list, detail, metadata edit, reprocess, chunk preview, and search UX.
- Phase 2H: added phase-focused tests and ran full regression verification.

Verification:
- Phase 2A-B focused test: passed
- Phase 2C-D focused tests: passed
- Phase 2E-F focused test: passed
- `py -3.13 -m unittest discover -s tests -v`: 56 passed, 2 opt-in skipped
- `npm run build`: passed
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: no whitespace errors, Windows CRLF warnings only
- `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`

Remaining operational QA:
- Manual QA with 3-5 real basis PDFs still needs product-owner sample selection.
- Image-only Korean basis PDFs should be rechecked after OCR engine setup.

## Phase 2 Operational QA Record - 10 Random Nara Notice PDFs (2026-05-22)
At the user's request, downloaded 10 random Nara notice PDFs through the Nara API and ran Phase 2 basis-pipeline operational QA.

QA design:
- Added `scripts/fetch-nara-phase2-basis-qa-samples.py`.
- Stored samples under `backend/tests/nara-phase2-basis-qa-samples/`, excluded from Git.
- Nara notice PDFs are used only as QA samples, not promoted to product basis documents.
- Each PDF is uploaded through the Phase 2 basis API and verified through extract, OCR check, normalize, chunk, local-token-v1 index, and search.
- Search results are verified as citation candidate chunks, not final decisions.
- Added opt-in test `backend/tests/test_nara_phase2_basis_qa_samples.py`, enabled only with `RUN_NARA_PHASE2_QA=1`.

Results:
- Date range: `20260501` to `20260522`
- Random seed: `20260522203720`
- Sample count: 10/10
- Skipped candidates: 6
- Every sample completed processing, completed indexing, and returned at least one search result.

Verification:
- `py -3.13 -m py_compile scripts\fetch-nara-phase2-basis-qa-samples.py backend\tests\test_nara_phase2_basis_qa_samples.py`: passed
- opt-in Phase 2 QA tests: 2 passed

Remaining QA note:
- This validates the Phase 2 pipeline with real Nara notice PDFs.
- Retrieval quality against official law/regulation basis PDFs can still be evaluated after sample selection.

## Shared Notice PDF Test Cache Policy (2026-05-22)
Notice-PDF-related tests now prefer already downloaded local PDF samples instead of calling the Nara API every time.

Configuration:
- Shared sample path: `backend/tests/nara-notice-pdf-samples/`
- Shared manifest: `backend/tests/nara-notice-pdf-samples/manifest.json`
- Shared helper: `backend/tests/nara_pdf_sample_cache.py`
- Collection script: `scripts/fetch-nara-notice-pdf-samples.py`

Resolution order:
1. Phase-specific manifest env vars: `NARA_PHASE17_SAMPLE_MANIFEST`, `NARA_PHASE2_SAMPLE_MANIFEST`
2. Shared manifest env var: `NARA_NOTICE_PDF_SAMPLE_MANIFEST`
3. Shared cache manifest
4. Legacy phase-specific sample folders

New sample set:
- Downloaded 30 random Nara notice PDFs for testing.
- Date range: `20260401` to `20260522`
- Random seed: `20260522204523`
- Sample count: 30/30
- All samples passed PDF, text extraction, requirement-candidate, and no-final-decision wording checks.

Verification:
- Confirmed Phase 1.7 and Phase 2 opt-in tests reuse the shared 30-sample cache.
- Default test discovery still skips opt-in PDF tests, so it does not depend on network or local samples.

## Why Phase 2.5 Exists
Phase 2.5 is a bridge between retrieval-ready basis documents and the final Phase 3 judgment engine.

Phase 2 prepares searchable knowledge assets. Phase 3 uses those assets for decision support. Jumping directly from Phase 2 to Phase 3 risks over-trusting RAG output or using uncited conditions as decision evidence.

Phase 2.5 therefore experiments with basis rule extraction, notice requirement structuring, and citation quality evaluation before the final matcher.

## Phase 2.5A: Basis Rule Extraction Experiment
Goal: extract structured rule candidates from basis chunks.

Tasks:
- Extract rule candidates from chunks.
- Design `basis_rules` or experimental rule candidate tables.
- Classify rule types: region, license/business type, company type, required documents, amount/performance, exceptions/notes.
- Link every rule to source chunk/page/section.
- Save LLM output only after JSON schema validation.
- Do not automatically promote candidates to confirmed rules.

Done:
- Rule candidates can be generated from sample basis documents.
- Every candidate links to source chunks.
- Uncited candidates are not promoted to judgment input.

## Phase 2.5B: Notice Requirement Structuring
Goal: refine Phase 1.7 rule-based notice candidates into Phase 3-ready input.

Tasks:
- Improve saved notice requirement schema.
- Define confidence by requirement type.
- Extend dictionaries for licenses, company types, and documents.
- Keep money/date/performance requirements as `needs_review`-style conditions.
- Evaluate source spans for notice text and attachment text.
- Preserve invalidation rules on re-extraction.

Done:
- Sample notices show fewer misses and false positives.
- Phase 3 matcher input schema is clearer.

## Phase 2.5C: Retrieval And Citation Evaluation
Goal: verify that retrieved chunks are accurate enough for future evidence use.

Tasks:
- Build representative question set.
- Manually evaluate top_k search results.
- Check chunk/page/section citation candidates.
- Tune overly long, overly short, or duplicate chunks.
- Validate category/version filters.

Done:
- Relevant chunks appear in top results.
- Citation candidates are sufficient for human source verification.
- The no-citation-no-final-decision policy is testable.

## Phase 2.5D: Phase 3 Input Contract
Goal: lock the draft input/output contract for the final judgment engine.

Tasks:
- Finalize notice requirement candidate schema.
- Identify corporation comparison profile gaps.
- Finalize basis retrieval result schema.
- Draft judgment engine input payload.
- Draft output states: `matched`, `missing`, `uncertain`, `needs_review`, `not_applicable`, `citation_missing`.
- Do not use final-verdict wording until the product owner explicitly approves it.
- Preserve missing-requirement and preparation-guide-first output principles.

Done:
- Phase 3 input expectations are documented.
- Citation and uncertainty notes are required before final decisions.

## Phase 2.5 Non-Scope
- Final eligibility UI
- Automatic final verdict output
- Final citation rendering
- Automatic corporation profile mutation
- External verification APIs
- Nara HTML crawling

## Phase 2.5 Done Criteria
Phase 2.5 is complete when:
- Basis rule extraction experiment results are documented.
- Notice requirement schema is Phase 3-ready.
- Retrieval/citation quality has been evaluated with representative questions.
- Phase 3 input/output contract draft is accepted.
- The no-citation-no-final-decision policy is preserved.

## Questions for Product Owner
- Who owns basis document categories and priority?
- Which 3-5 basis PDF samples should be registered first?
- Should old basis document versions remain searchable?
- Should local Qdrant be part of the default setup or optional setup?
- Do administrators need a UX to approve rule candidates in Phase 2.5?
- Is a standalone basis search screen needed before Phase 3?
