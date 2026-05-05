# 한국어 버전

## 프로젝트 개요
`SMART 조달청 계산기`는 조달 관련 문서를 프로젝트 단위로 관리하고, AI 기반 분석 결과를 제공하는 단일 관리자용 로컬 웹 포탈입니다. 초기 MVP는 법인/프로젝트/문서 관리와 문서 요약에 집중하며, 이후 기준문서 기반 RAG와 자격 판단 엔진으로 확장합니다.

## 문제 정의
- 조달 문서는 길고 복잡해 수작업 검토 비용이 높다.
- 파일 중심 관리만으로는 프로젝트 이력과 법인 맥락을 유지하기 어렵다.
- 향후 자격 판단을 위해서는 기준문서를 구조화된 지식 자산으로 축적해야 한다.
- 일반 사용자가 문서를 직접 청킹하거나 인덱싱하는 것은 비현실적이다.

## 목표
- Phase 1에서 실사용 가능한 업로드/관리/요약 MVP 제공
- 프로젝트 중심 데이터 구조 정립
- OCR 포함 문서 파이프라인 마련
- Phase 2 기준문서 자동 청킹과 로컬 인덱싱 준비
- Phase 3 판단 엔진과 공고 수집 확장 가능 구조 확보

## 단계별 범위

### Phase 1 범위
- 단일 관리자 포탈
- 로그인 없음
- 법인 CRUD
- 프로젝트 CRUD
- 프로젝트 기반 PDF/DOCX 업로드
- 업로드 히스토리 관리
- PDF/DOCX 텍스트 추출
- 스캔 PDF OCR
- AI 요약
- 구조화 결과 저장
- 결과 캐시
- 재분석 버튼

### Phase 1 비범위
- 기준문서 RAG 검색 결과 사용
- 최종 자격 판단
- 근거 조항 출력
- 조달청 사이트 크롤링
- 인증/권한 체계

### Phase 1.5 범위: 나라장터 게시판
- 나라장터 공공데이터 API 기반 공고 검색
- 공고 리스트/상세 화면
- 기본 검색 및 상세검색
- 공고 첨부파일 목록 표시
- PDF/DOCX 첨부파일 다운로드
- 공고 1개 선택 후 `공고 상세 저장`
- 공고 상세/기초금액/면허제한/참가가능지역 API 재조회
- 공고 메타데이터 저장
- 공고 첨부 PDF/DOCX 자동 다운로드
- 기존 PyMuPDF/DOCX 파싱 파이프라인 재사용
- 공고 단위 AI 요약 및 구조화 결과 저장
- 설정 메뉴에서 나라장터 API 키 설정/연결 상태 확인

### Phase 1.5 비범위
- 최종 지원 가능/불가능 판정
- 법인-공고 요건 자동 매칭
- 기준문서 RAG 근거 검색
- HWP/HWPX 파싱
- 나라장터 HTML 크롤링

### Phase 2 범위
- 기준 PDF 관리 메뉴
- 기준문서 CRUD
- 카테고리/유형 관리
- 버전 관리
- OCR
- 자동 청킹
- 청크 메타데이터 생성
- 로컬 벡터 인덱싱
- 처리 상태 표시
- 재처리 기능

### Phase 2 비범위
- 최종 판단 엔진
- 법인 대 공고 자동 판정
- 공고 수집

### Phase 3 범위
- 조달 공고 자동 수집
- 첨부 수집
- 공고 브라우징 대시보드
- 공고 분석 저장
- 법인-요건 매칭
- 기준문서 retrieval
- 판단 결과 출력
- 근거 조항 렌더링
- 체크리스트 생성
- 준비 가이드 생성

## 가정
- 관리자 사용자 1명
- 로컬 PC 운영
- 로그인 기능은 Phase 1 제외
- HWP 제외
- 일반 업로드는 PDF/DOCX만 지원
- 기준문서는 PDF만 지원
- 프로젝트는 우선 1개 법인만 연결

## Questions for Product Owner
- 법인 MVP 필드에 사업자등록번호가 포함되어야 하는가
- OCR 보정 UI가 필요한가
- 프로젝트 상태 관리가 필요한가
- 분석 결과 내보내기 기능이 필요한가
- 기준문서 분류 체계를 누가 정의하는가
- 저장된 나라장터 공고를 기존 프로젝트에 즉시 연결해야 하는가
- 나라장터 게시판 1차 범위가 공사 공고만인지, 물품/용역까지 포함해야 하는가
- 나라장터 API 키를 UI에서 직접 저장/수정할지, 상태 확인만 제공할지

## 사용자 유형
- 현재: 행정사 1인 관리자
- 미래: 내부 검토자, 보조 담당자

## 사용자 여정
1. 법인 등록
2. 프로젝트 생성
3. 프로젝트에 문서 업로드
4. 파싱/OCR/요약 처리
5. 분석 결과 검토
6. 필요 시 재분석
7. Phase 2부터 기준 PDF 별도 업로드 및 재처리
8. Phase 1.5부터 나라장터 게시판에서 공고 검색
9. 공고 1개 선택 후 상세 저장 및 자동 분석

## 기능 요구사항

### 포탈
- 웹 기반 관리자 포탈
- 프로젝트 중심 탐색
- 현대적 대시보드 UI

### 법인 관리
MVP 필드 제안
- corporation_name
- business_type_or_category
- region
- certifications_or_licenses
- company_size_classification
- internal_notes
- created_at
- updated_at

### 프로젝트 관리
- 프로젝트 생성 필수
- 프로젝트는 법인 선택 포함
- 프로젝트 메모 포함
- 프로젝트별 문서 목록 제공

### 일반 문서 업로드
- 프로젝트 소속으로만 업로드 가능
- 허용 파일: PDF, DOCX
- 메타데이터 수집
  - project_name
  - selected_corporation
  - document_category_or_type
  - memo
  - revision_note
  - timestamps

### 업로드 이력 및 대시보드
- 목록
- 검색
- 필터
- 상세
- 수정
- 삭제
- 프로젝트 우선 정렬

### 문서 분석
- 파일 파싱
- 스캔 PDF OCR
- AI 기반 요약
- 구조화 출력 저장
- 결과 페이지
- 결과 캐시
- 재분석 버튼

### 나라장터 게시판
- 공공데이터 API 기반 공고 목록 조회
- 공고 검색 페이지 진입 시 최근 1개월 기본 조건으로 자동 조회
- 기본 검색과 상세검색
- 공고 상세 미리보기
- 첨부파일 목록 표시
- 지원 가능 첨부파일 다운로드
- 라디오 박스로 공고 1개 선택
- 선택 공고 저장 및 자동 분석
- 저장/다운로드/파싱/요약 진행 상태 표시
- 저장된 공고 상세 및 분석 결과 조회

### 설정/API 연동
- 나라장터 API 키 설정 여부 확인
- 마스킹된 키 표시
- 공고 API base URL 확인
- 표준 데이터 API base URL 확인
- 연결 테스트 실행
- 공고 API 테스트 실행
- 첨부 PDF 다운로드 테스트 실행
- 마지막 테스트 결과와 시각 저장

### 기준 PDF 관리
- 별도 메뉴 제공
- 업로드
- 목록
- 상세
- 메타데이터 수정
- 삭제
- 처리 상태
- 재처리 버튼

### 기준 PDF 자동 청킹
- 텍스트 추출
- OCR
- 정규화
- 자동 청킹
- 청크 메타데이터 생성
- 인덱싱
- 저장

## 비기능 요구사항
- 로컬 단일 PC에서 실행 가능해야 한다.
- 처리 상태가 명확해야 한다.
- 긴 문서도 안정적으로 처리해야 한다.
- 분석 재현성을 위해 모델명/프롬프트 버전을 기록해야 한다.
- 실패 지점을 구분해 재시도 가능해야 한다.
- 향후 인증, 크롤러, 판단 엔진 확장을 막지 않아야 한다.

## 전체 아키텍처
```text
React Admin Portal
  -> FastAPI API
    -> SQLite
    -> Local File Storage
    -> Parsing Pipeline
    -> OCR Pipeline
    -> Summarization Pipeline
    -> Future Basis Chunking Pipeline
    -> Future Vector Index
    -> Future Procurement Crawler
```

## 프론트엔드 아키텍처
- React + TypeScript + Vite
- React Router
- TanStack Query
- React Hook Form 권장
- 페이지
  - Dashboard
  - Corporations
  - Projects
  - Project Detail
  - Analysis Detail
  - Basis Documents

## 백엔드 아키텍처
- FastAPI
- SQLAlchemy
- Pydantic
- 서비스 계층 분리
- 파이프라인 계층 분리
  - parser_service
  - ocr_service
  - summarizer_service
  - basis_chunking_service
  - indexing_service
- 초기 비동기: FastAPI background tasks
- 확장 비동기: worker queue 가능

## 추천 기술 스택과 근거
- FastAPI: Python OCR/문서 처리/AI SDK 연계에 적합
- SQLite: 단일 PC MVP에 적합
- Local filesystem: 원본 파일 관리가 단순
- React + Vite: 빠른 어드민 UI 구축에 적합
- Qdrant: 로컬 벡터 검색과 메타 필터링에 유리

## DB 스키마 제안

### corporations
- id
- name
- business_category
- region
- certifications_json
- company_size_classification
- internal_notes
- created_at
- updated_at

### projects
- id
- name
- corporation_id
- status
- notes
- created_at
- updated_at

### project_documents
- id
- project_id
- document_type
- original_file_name
- stored_file_path
- mime_type
- file_size
- memo
- revision_note
- parsing_status
- ocr_status
- analysis_status
- latest_analysis_id
- created_at
- updated_at

### analyses
- id
- project_document_id
- analysis_type
- model_provider
- model_name
- prompt_version
- input_hash
- output_json
- output_markdown
- token_usage_json
- status
- error_message
- created_at

### procurement_notices
- id
- bid_ntce_no
- bid_ntce_ord
- title
- notice_institution_name
- demand_institution_name
- bid_notice_datetime
- bid_begin_datetime
- bid_close_datetime
- opening_datetime
- estimated_price
- budget_amount
- basis_amount
- industry_limit_yn
- construction_site_region
- notice_url
- detail_url
- source_api
- raw_notice_json
- raw_enrichment_json
- save_status
- analysis_status
- latest_analysis_id
- created_at
- updated_at

### procurement_notice_attachments
- id
- notice_id
- source_field
- original_file_name
- file_url
- file_extension
- support_status
- download_status
- stored_file_path
- mime_type
- file_size
- file_hash
- parse_status
- parsed_text_path
- parser_metadata_json
- error_message
- created_at
- updated_at

### procurement_notice_analyses
- id
- notice_id
- analysis_type
- model_provider
- model_name
- prompt_version
- input_hash
- output_json
- output_markdown
- token_usage_json
- status
- error_message
- created_at

### procurement_notice_jobs
- id
- notice_id
- job_type
- status
- current_step
- progress_percent
- message
- error_message
- started_at
- finished_at
- created_at

### basis_documents
- id
- title
- category
- version_label
- original_file_name
- stored_file_path
- processing_status
- memo
- created_at
- updated_at

### basis_document_chunks
- id
- basis_document_id
- chunk_index
- chunk_text
- chunk_text_normalized
- page_start
- page_end
- section_title
- section_path
- chunk_hash
- metadata_json
- embedding_model
- vector_status
- created_at

### audit_logs
- id
- entity_type
- entity_id
- action
- actor_label
- before_json
- after_json
- created_at

## ER 개요
- corporation 1:N projects
- project 1:N project_documents
- project_document 1:N analyses
- basis_document 1:N basis_document_chunks
- procurement_notice 1:N procurement_notice_attachments
- procurement_notice 1:N procurement_notice_analyses
- procurement_notice 1:N procurement_notice_jobs

## 프로젝트/법인/파일 관계
- 프로젝트는 하나의 법인에 연결된다.
- 일반 업로드 파일은 반드시 하나의 프로젝트에 속한다.
- 분석 결과는 파일 단위로 버전 누적 저장한다.
- 기준문서는 프로젝트에 속하지 않는 별도 지식 자산이다.
- 나라장터 저장 공고는 MVP에서 프로젝트와 분리된 외부 공고 도메인으로 관리한다.
- 향후 저장 공고에서 프로젝트를 생성하거나 법인과 연결하는 확장을 열어둔다.

## 기준문서 모델
- 목적: 향후 자격 판단, 근거 조항 검색, 내부 기준 관리
- 제약: PDF만 허용
- 기능: 버전 관리, 재처리, 청킹, 인덱싱

## API 설계 제안

### Corporations
- GET `/api/corporations`
- POST `/api/corporations`
- GET `/api/corporations/{id}`
- PATCH `/api/corporations/{id}`
- DELETE `/api/corporations/{id}`

### Projects
- GET `/api/projects`
- POST `/api/projects`
- GET `/api/projects/{id}`
- PATCH `/api/projects/{id}`
- DELETE `/api/projects/{id}`

### Project Documents
- GET `/api/projects/{id}/documents`
- POST `/api/projects/{id}/documents`
- GET `/api/documents/{id}`
- PATCH `/api/documents/{id}`
- DELETE `/api/documents/{id}`
- POST `/api/documents/{id}/reanalyze`

### Analyses
- GET `/api/analyses/{id}`
- GET `/api/documents/{id}/latest-analysis`

### Nara Board
- GET `/api/nara/notices/search`
- GET `/api/nara/notices/preview`
- POST `/api/nara/notices/save-and-analyze`
- GET `/api/nara/notice-jobs/{job_id}`
- GET `/api/nara/saved-notices`
- GET `/api/nara/saved-notices/{notice_id}`
- GET `/api/nara/saved-notices/{notice_id}/attachments/{attachment_id}/download`
- POST `/api/nara/saved-notices/{notice_id}/reanalyze`

### Settings / Integrations
- GET `/api/settings/integrations/nara/status`
- POST `/api/settings/integrations/nara/test`

### Basis Documents
- GET `/api/basis-documents`
- POST `/api/basis-documents`
- GET `/api/basis-documents/{id}`
- PATCH `/api/basis-documents/{id}`
- DELETE `/api/basis-documents/{id}`
- POST `/api/basis-documents/{id}/reprocess`
- GET `/api/basis-documents/{id}/chunks`

## 파일 업로드 생명주기
1. 프로젝트 선택 또는 생성
2. 메타데이터와 함께 파일 업로드
3. 원본 파일 저장
4. DB 레코드 생성
5. 파싱 수행
6. 필요 시 OCR 수행
7. 정규화 텍스트 생성
8. 캐시 조회
9. LLM 분석 수행
10. 결과 저장 및 최신 분석 연결

## 나라장터 공고 저장/분석 생명주기
1. 사용자가 `나라장터 게시판 > 공고 검색`에 진입
2. 프론트엔드가 기본 조회 조건을 구성
   - 기준 기간: 최근 1개월
   - 예: 오늘이 `2026-05-05`이면 `2026-04-05 00:00` ~ `2026-05-05 23:59`
   - 페이지 크기: 20
3. 백엔드가 `getBidPblancListInfoCnstwkPPSSrch`로 목록 조회
4. 사용자가 검색 조건을 변경하면 변경 조건으로 다시 조회
5. 사용자가 라디오 박스로 공고 1개 선택
6. 사용자가 `공고 상세 저장` 클릭
7. 백엔드가 공고 상세/기초금액/면허제한/참가가능지역 API 재조회
8. `procurement_notices`에 공고 메타데이터 upsert
9. 첨부파일 URL과 파일명을 정규화하여 `procurement_notice_attachments`에 upsert
10. PDF/DOCX 첨부만 자동 다운로드
11. 다운로드 파일을 로컬 저장소에 저장하고 해시 계산
12. 기존 PyMuPDF/python-docx 파싱 파이프라인 실행
13. 공고 메타데이터와 추출 텍스트를 결합해 요약 입력 구성
14. AI 요약 또는 fallback 요약 실행
15. `procurement_notice_analyses`에 결과 저장
16. `procurement_notice_jobs` 상태를 완료 또는 부분 실패로 갱신

## 나라장터 API 설정 확인 흐름
1. 사용자가 `설정 > API 연동 > 나라장터` 진입
2. 백엔드가 환경변수 또는 로컬 설정에서 `NARA_API_SERVICE_KEY` 존재 여부 확인
3. 프론트엔드에는 전체 키가 아니라 마스킹된 키와 설정 상태만 반환
4. 사용자가 `연결 테스트` 클릭
5. 백엔드가 최근 1개월 기본 조건으로 공고 목록 테스트 호출
6. 대표 공고가 있으면 상세 API와 첨부 PDF 다운로드 테스트를 선택 수행
7. 마지막 테스트 결과, 오류 메시지, 테스트 시각을 반환

## 나라장터 게시판 파이프라인 상태값
- `queued`
- `fetching_notice`
- `saving_notice`
- `downloading_attachments`
- `parsing_documents`
- `summarizing`
- `completed`
- `partial_failed`
- `failed`

## 나라장터 첨부파일 정책
- `.pdf`, `.docx`는 다운로드와 분석 대상이다.
- `.hwp`, `.hwpx`, `.xlsx`, `.xls`, `.zip`, 확장자 불명 파일은 메타데이터만 저장한다.
- 다운로드 검증은 HTTP 상태, Content-Type, 파일 크기, PDF `%PDF` 시그니처 또는 DOCX zip 시그니처로 수행한다.
- 일부 첨부 다운로드가 실패해도 다른 첨부 처리는 계속하고 전체 작업은 `partial_failed`가 될 수 있다.

## 파싱 파이프라인
- PDF
  - Phase 1 개선 결정: 기존 `pypdf` 중심 추출에서 `PyMuPDF` 중심 추출로 교체한다.
  - `PyMuPDF`로 페이지별 텍스트, 블록, 좌표, 읽기 순서 후보를 함께 추출한다.
  - 텍스트 레이어가 충분하면 OCR 없이 정규화와 조달문서 후처리 단계로 이동한다.
  - 텍스트 양이 부족하거나 이미지형 페이지로 판단되면 OCR fallback 경로로 전환한다.
  - 기존 `pypdf`는 필요 시 비교/백업용 후보로만 남기고, 기본 엔진으로 사용하지 않는다.
- DOCX
  - 문단/표 텍스트 추출
  - 줄바꿈 정규화
- 공통
  - 문서 해시 생성
  - 추출 텍스트 저장
  - 페이지 번호, 블록 순서, 추출 엔진, 추출 문자 수, OCR 필요 여부를 메타데이터로 남긴다.

### PDF 추출 엔진 교체 구현 계획
1. 의존성에 `PyMuPDF`를 추가한다.
2. `extract_text()`를 PDF/DOCX 분기만 처리하는 단순 함수에서 PDF 전용 추출 함수와 DOCX 추출 함수로 분리한다.
3. PDF 추출 결과는 원문 텍스트 문자열뿐 아니라 페이지별 메타데이터를 함께 생성한다.
4. 조달 공고문에서 자주 뭉개지는 표/항목을 보정하기 위해 공백, 항목 번호, 날짜/금액 주변 줄바꿈을 정규화한다.
5. 추출 문자 수가 임계값 미만이면 `ocr_status=needs_ocr` 또는 OCR fallback으로 넘긴다.
6. 기존 스모크 테스트에 실제 PDF 샘플 또는 텍스트 레이어가 있는 테스트 PDF를 추가해 회귀를 막는다.
7. 이후 PaddleOCR 연결 시 `PyMuPDF`가 페이지 이미지를 렌더링하고 OCR 엔진이 해당 이미지를 읽는 구조로 확장한다.

### 조달 PDF 샘플 기준 결정
- 사용자 제공 샘플은 4페이지이며 기존 `pypdf`로도 약 5,414자 추출 가능했다.
- 문제는 스캔 OCR이 아니라 표, 제목, 항목 번호, 본문 경계가 붙는 레이아웃 손실이다.
- 따라서 Phase 1의 첫 개선은 OCR 엔진 교체가 아니라 `PyMuPDF` 기반 레이아웃 인식 추출로 한다.
- OCR은 텍스트 레이어가 부족한 PDF에만 fallback으로 적용한다.

## OCR 파이프라인
- 대상: 스캔 PDF
- 흐름
  - 페이지 렌더링
  - 로컬 OCR
  - 페이지별 텍스트 병합
  - 품질 기준 미달 시 경고 상태 기록
- 권장
  - Phase 1 기본 fallback 후보: PaddleOCR
  - 경량 대안: Tesseract `kor+eng`
  - Stirling PDF: 메인 추출 엔진이 아니라 향후 PDF 전처리/OCR 보조 서버로 선택 연동 가능

## AI / API 요구사항 설계

### 추천 제공자 및 모델
- Primary: OpenAI `GPT-5.1`
- Secondary cheaper model: `GPT-5 mini`

### 한국어 조달 문서에 적합한 이유
- 긴 문서 요약과 구조화 출력이 강함
- 한국어 장문 컨텍스트 처리에 적합
- 후속 판단 프롬프트로 같은 제공자 내 확장 가능

### PDF/DOCX 입력 처리
- MVP는 파일 원본 자체보다 파싱/정규화된 텍스트를 주 입력으로 사용
- 필요 시 파일 입력 지원은 별도 실험 가능
- PDF 텍스트 추출 기본 엔진은 `PyMuPDF`로 한다.
- DOCX는 `python-docx`를 유지한다.

### OCR 전략
- 스캔 PDF는 로컬 OCR 우선
- OCR 결과를 정규화 텍스트로 저장
- 원본 추출 텍스트와 OCR 텍스트를 구분 보관
- OCR은 모든 PDF에 무조건 적용하지 않고, `PyMuPDF` 추출 결과가 부족한 경우에만 fallback으로 적용한다.

### 요약 프롬프트 전략
- 역할: 조달문서 분석 보조관
- 지시
  - 문서에 없는 내용 추정 금지
  - 불명확 항목은 `확인 필요`로 표기
  - JSON 스키마 준수
- 출력
  - 구조화 JSON
  - 사용자용 마크다운 요약

### 구조화 출력 전략
```json
{
  "document_summary": "",
  "key_dates": [],
  "requirements": [],
  "required_documents": [],
  "risks": [],
  "questions_to_check": [],
  "confidence_note": ""
}
```

### 환각 완화 전략
- 사실과 추론을 필드로 분리
- 문서 밖 정보 생성 금지
- 불명확 시 `확인 필요`
- 향후 근거 조항 단계에서 citation id 강제

### 캐시 전략
- input_hash + prompt_version + model_name 조합 사용
- 동일 입력/프롬프트/모델이면 재사용
- 프롬프트 변경 시 새 분석 생성

### 재분석 전략
- 수동 버튼으로 강제 재실행
- 이전 결과는 이력으로 유지
- latest_analysis_id만 갱신

### 미래 판단 프롬프트 설계
- 입력: 법인 프로필 + 공고 요약 + retrieval 근거
- 출력: eligible / not_eligible / review_required
- 각 결과에 사유, 부족 항목, 근거 citation 포함

### 미래 근거 조항 retrieval 설계
- 기준문서에서 semantic + metadata filter 검색
- 반환: 문서명, 버전, 페이지, 섹션, 인용 텍스트
- 판단 엔진은 근거를 구조화해 출력

## 요약 파이프라인
1. 추출/정규화 텍스트 수집
2. 길이 점검
3. 필요 시 분할 요약
4. LLM 호출
5. JSON 검증
6. 마크다운 생성
7. 결과 저장

## 기준 PDF 자동 청킹 파이프라인
1. 기준 PDF 업로드
2. 파일 저장
3. 텍스트 추출
4. OCR
5. 정규화
6. 섹션/페이지 단위 1차 분할
7. 토큰 길이 기준 2차 청킹
8. 청크 메타데이터 생성
9. 임베딩 생성
10. 로컬 벡터 저장소 인덱싱
11. 처리 상태 갱신

## 청크 전략
- 사용자 수동 청킹 금지
- 1차 분할 기준
  - 페이지
  - 제목/조항 패턴
- 2차 분할 기준
  - 500~900 토큰 수준
  - 80~150 토큰 오버랩

## 청크 메타데이터 설계
- chunk_id
- basis_document_id
- category
- version_label
- page_start
- page_end
- section_title
- section_path
- chunk_index
- chunk_hash
- source_text_length
- normalized_text_length
- created_at

## 로컬 인덱싱 설계
- 권장: Qdrant
- 대안: Chroma
- 선택 기준
  - 메타 필터링 필요성이 높으면 Qdrant
  - 단순 프로토타입이면 Chroma

## 미래 RAG 설계
- 일반 업로드 문서는 분석 대상
- 기준문서는 근거 검색용 지식 자산
- retrieval은 metadata filter + semantic search 병행
- 결과는 citation과 함께 반환

## 미래 판단 엔진 설계
- 입력
  - corporation profile
  - notice analysis
  - retrieved basis chunks
- 출력
  - eligible
  - not_eligible
  - review_required
- 부가 출력
  - evidence clauses
  - missing requirements
  - uncertainty notes

## 미래 조달 크롤러 설계
- 별도 수집 모듈
- source_type=`crawler`
- 기존 분석 파이프라인 재사용
- robots/legal 검토 필요

## 보안/개인정보 고려사항
- API 키는 환경 변수 관리
- 나라장터 API 키 전체 값은 프론트엔드에 반환하지 않는다.
- 설정 화면에는 마스킹된 키와 연결 상태만 표시한다.
- 로컬 저장소 접근 최소화
- 삭제 시 원본/파생 데이터 함께 삭제
- 외부 API 전송 텍스트 최소화

## 로컬 단일 PC 배포 전략
- React dev/prod build + FastAPI를 동일 PC에서 실행
- SQLite와 storage 디렉터리를 로컬 디스크에 저장
- 향후 Windows 서비스 또는 데스크탑 패키징 가능

## 로깅/감사 전략
- 업로드/수정/삭제
- 분석 시작/완료/실패
- 기준문서 처리 시작/완료/실패
- 재분석/재처리

## 오류 처리 전략
- 상태값 예시
  - uploaded
  - parsing_failed
  - ocr_failed
  - analysis_failed
  - ready
- 실패 지점별 사용자 메시지 제공
- 재시도 버튼 제공

## 권장 저장소 구조
```text
wisdom_procurement/
  frontend/
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      repositories/
      pipelines/
      workers/
    storage/
      uploads/
      basis/
      nara_notices/
      cache/
  docs/
    technical-design.md
    ux-design.md
    narajangteo-board-design.md
  README.md
  AGENTS.md
```

---

# AI / Engineering Version (English)

## Summary
Local-first admin portal for one administrator to manage corporations, projects, procurement documents, Nara Marketplace notice browsing, OCR, AI summarization, and later basis-document RAG and eligibility judgment.

## Assumptions
- single admin only in phase 1
- no authentication in phase 1
- PDF/DOCX only for target uploads
- PDF only for basis documents
- project maps to one corporation in MVP

## Architecture
- Frontend: React, TypeScript, Vite, TanStack Query
- Backend: FastAPI, SQLAlchemy, Pydantic
- DB: SQLite
- Storage: local filesystem
- OCR: local OCR
- LLM: GPT-5.1 primary, GPT-5 mini secondary
- Future vector store: Qdrant preferred

## Key Entities
- Corporation
- Project
- ProjectDocument
- Analysis
- ProcurementNotice
- ProcurementNoticeAttachment
- ProcurementNoticeAnalysis
- ProcurementNoticeJob
- BasisDocument
- BasisDocumentChunk
- AuditLog

## Key Pipelines
- target document pipeline: upload -> parse -> OCR if needed -> summarize -> cache -> persist
- Nara notice pipeline: API search -> select notice -> detail/enrichment lookup -> upsert notice -> download PDF/DOCX attachments -> parse -> summarize -> persist
- settings pipeline: read local env/config -> return masked integration status -> run Nara connection tests on demand
- basis pipeline: upload -> parse -> OCR -> normalize -> chunk -> embed -> index

## Open Questions
- required corporation fields for MVP
- OCR correction UI necessity
- project status taxonomy
- export requirements
- basis taxonomy ownership
- whether saved Nara notices should immediately link to projects
- whether the first Nara board release should include goods/services notices or construction only
- whether the Nara API key should be editable in the UI or status-check only

## References
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
- PDF Files Guide: [https://platform.openai.com/docs/guides/pdf-files](https://platform.openai.com/docs/guides/pdf-files)
- Qdrant Vectors: [https://qdrant.tech/documentation/concepts/vectors/](https://qdrant.tech/documentation/concepts/vectors/)
