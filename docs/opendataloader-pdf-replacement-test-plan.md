# OpenDataLoader PDF 리더 엔진 교체 계획 및 테스트 계획

## 현재 구현 상태
최종 갱신일: 2026-06-07

- [x] 기본 PDF 리더를 `PDF_READER_ENGINE=auto`로 전환
- [x] OpenDataLoader PDF 우선, PyMuPDF fallback 유지
- [x] 일반 문서, 나라장터 공고문 PDF, 기준문서 PDF가 동일한 `extract_document()` reader 정책 공유
- [x] OpenDataLoader JSON/Markdown에서 table metadata와 `table_row` chunk 생성
- [x] PyMuPDF fallback page `char_start`/`char_end` 보정
- [x] OpenDataLoader JSON 중첩 text/table-cell 누락 방지
- [x] DOCX 문단과 표 cell 텍스트 추출 보강
- [x] 긴 단일 문단 기준문서 chunk overlap 보정
- [x] 기준문서 원본 파일 없음 재처리 시 기존 completed/indexed RAG 지식 보존
- [x] 기준문구 후보 승인과 Phase 3 판단 citation이 JSON basis index 건강 상태를 검증

최근 검증:
- targeted PDF/parser/table tests: `22 passed`
- 신규 API regression tests: `4 passed`
- 전체 backend tests: `134 passed`, `8 skipped`
- 인코딩 검사: `ENCODING_CHECK_OK`

## 문서 목적
현재 서비스의 PDF 리더 엔진을 PyMuPDF 중심 구조에서 `opendataloader-project/opendataloader-pdf` 중심 구조로 교체하기 위한 구현 계획과 테스트 계획을 정의합니다.

이번 계획의 목표는 단순히 PDF 텍스트 추출 라이브러리를 바꾸는 것이 아닙니다.
기준문서 RAG 품질을 높이기 위해 PDF의 표, 행, 열, 페이지, bbox, citation metadata를 서비스 데이터 구조로 가져오는 것입니다.

## 결론
교체 방향은 승인할 만합니다.

다만 운영 안정성을 위해 다음 원칙으로 진행합니다.

1. 서비스의 기본 PDF 리더 엔진을 OpenDataLoader로 전환한다.
2. PyMuPDF는 완전히 제거하지 않고 fallback 엔진으로 유지한다.
3. 기준문서 PDF는 OpenDataLoader JSON/Markdown 결과를 우선 사용한다.
4. 나라장터 공고문 PDF는 전환 후 회귀가 없을 때까지 `auto` 모드로 운영한다.
5. Java 미설치, 패키지 미설치, timeout, 변환 실패 시 PyMuPDF fallback이 반드시 작동해야 한다.

## 교체 사유
현재 PyMuPDF 기반 추출은 본문과 숫자 추출은 안정적이지만, 표가 많은 기준문서에서는 다음 문제가 있습니다.

- 표의 행/열 구조가 평문 줄 단위로 흩어짐
- `항목 / 내용 / 비고` 같은 직접생산 확인기준 표를 RAG chunk로 안정적으로 만들기 어려움
- chunk metadata에 table id, row index, column headers, bbox가 없음
- citation이 page range 수준에 머물고 표 행 단위 근거를 만들기 어려움

OpenDataLoader PDF는 Markdown/JSON 출력, table/table row/table cell 구조, page number, bounding box를 제공하므로 기준문서 RAG와 citation에 더 적합합니다.

## 외부 의존성 기준
확인한 공식 정보 기준입니다.

- 패키지: `opendataloader-pdf`
- 확인 버전: `2.4.7`
- 라이선스: Apache-2.0
- 요구사항: Java 11 이상, Python 3.10 이상
- 주요 출력: JSON, Markdown, Text, HTML, Tagged PDF
- 주요 옵션:
  - `format="markdown,json"`
  - `table_method="cluster"`
  - `reading_order="xycut"`
  - `pages`
  - `markdown_with_html`
  - `hybrid`
  - `threads`

주의할 점:

- `convert()` 호출마다 JVM 프로세스가 뜨므로 반복 호출은 느릴 수 있습니다.
- batch 변환과 timeout 제어를 구현해야 합니다.
- hybrid/OCR 모드는 별도 서버와 추가 의존성이 있으므로 1차 교체 범위에서 제외합니다.

## 현재 구조
현재 PDF 추출 진입점:

- `backend/app/pipelines/parser.py`
  - `extract_document()`
  - `_extract_pdf_text()`
  - PyMuPDF `page.get_text("blocks")`

기준문서 처리 흐름:

```text
process_basis_document()
  -> extract_document()
  -> run_ocr_if_needed()
  -> normalize_basis_text()
  -> split_basis_text_into_chunks()
  -> index_basis_chunks()
```

현재 약점:

- `ParsedDocument.text` 중심 구조
- parser metadata가 page/char count 중심
- table metadata 없음
- paragraph-window chunk만 존재
- JSON basis index에 table-row metadata 없음

## 목표 구조
PDF 리더를 어댑터 계층으로 분리합니다.

```text
extract_document()
  -> read_pdf_document()
       -> OpenDataLoaderPdfReader
       -> PyMuPdfPdfReader
       -> AutoPdfReader
```

기준문서 처리 흐름은 다음처럼 확장합니다.

```text
process_basis_document()
  -> extract_document()
  -> normalize_basis_text()
  -> split_basis_text_into_chunks()
  -> split_basis_tables_into_row_chunks()
  -> index_basis_chunks()
```

## 설정값
`.env` 또는 backend config에 다음 값을 추가합니다.

```text
PDF_READER_ENGINE=auto
PDF_READER_ODL_VERSION=2.4.7
PDF_READER_ODL_TABLE_METHOD=cluster
PDF_READER_ODL_READING_ORDER=xycut
PDF_READER_ODL_FORMAT=markdown,json
PDF_READER_ODL_TIMEOUT_SECONDS=180
PDF_READER_ODL_THREADS=1
PDF_READER_ODL_ENABLE_HYBRID=false
PDF_READER_ALLOW_PYMUPDF_FALLBACK=true
```

엔진 정책:

- `opendataloader`: OpenDataLoader만 사용, 실패 시 실패 처리
- `pymupdf`: 기존 PyMuPDF만 사용
- `auto`: OpenDataLoader 우선, 실패 시 PyMuPDF fallback

운영 기본값은 `auto`입니다.

## 데이터 구조 변경 계획
### ParsedDocument 확장
현재:

```python
ParsedDocument(
    text: str,
    kind: str,
    metadata: dict,
)
```

확장:

```python
ParsedDocument(
    text: str,
    kind: str,
    metadata: dict,
)
```

dataclass 필드는 유지하고 `metadata`를 확장합니다.
기존 호출부의 회귀를 막기 위해 `text/kind/metadata` 형태는 바꾸지 않습니다.

추가 metadata 예시:

```json
{
  "engine": "opendataloader-pdf",
  "engine_version": "2.4.7",
  "fallback_engine": "",
  "fallback_reason": "",
  "page_count": 489,
  "char_count": 123456,
  "markdown_char_count": 123456,
  "table_count": 1200,
  "table_row_count": 9000,
  "pages": [
    {
      "page_number": 120,
      "char_count": 1000,
      "table_count": 4,
      "bbox": [0, 0, 842, 595]
    }
  ],
  "tables": [
    {
      "table_id": "p120-t2",
      "page_number": 120,
      "bbox": [41.8, 66.9, 380.7, 424.6],
      "row_count": 7,
      "column_count": 4,
      "headers": ["항목", "내용", "비고"],
      "rows": []
    }
  ],
  "needs_ocr": false
}
```

### Basis chunk metadata 확장
기존 DB 스키마의 `metadata_json`을 우선 활용합니다.
초기 단계에서는 컬럼 추가 없이 metadata로 보존하고, 운영 안정화 후 필요한 컬럼만 추가합니다.

추가 metadata:

- `chunk_type`: `paragraph`, `table`, `table_row`, `table_context`
- `source_engine`: `opendataloader-pdf`
- `page_number`
- `logical_page`
- `bbox`
- `table_id`
- `row_index`
- `column_headers`
- `cell_texts`
- `markdown`

## 구현 단계
### ODL-1. 의존성 및 설정 추가
작업:

- `backend/requirements.txt`에 `opendataloader-pdf==2.4.7` 추가
- README에 Java 11 이상 설치 안내 추가
- backend config에 PDF reader 설정값 추가
- OpenDataLoader 사용 가능 여부 health check 추가

테스트:

- Java 설치 상태 감지
- 패키지 설치 상태 감지
- Java 미설치 시 앱 시작은 성공하고 fallback 가능 상태로 표시

### ODL-2. PDF reader adapter 분리
작업:

- `backend/app/pipelines/pdf_readers.py` 추가
- 기존 PyMuPDF 로직을 `PyMuPdfPdfReader`로 이동
- `OpenDataLoaderPdfReader` 추가
- `AutoPdfReader` 추가
- `parser.py::extract_document()`는 adapter를 호출하도록 변경

테스트:

- 기존 `test_parser.py`가 계속 통과
- `PDF_READER_ENGINE=pymupdf`에서 기존 metadata 유지
- `PDF_READER_ENGINE=opendataloader`에서 engine metadata가 ODL로 기록
- `PDF_READER_ENGINE=auto`에서 ODL 실패 시 PyMuPDF fallback

### ODL-3. OpenDataLoader JSON/Markdown 파싱
작업:

- ODL 변환 output directory를 안전한 임시 디렉터리로 생성
- `format="markdown,json"` 사용
- JSON의 `paragraph`, `heading`, `list item`, `table`, `table row`, `table cell` 추출
- Markdown을 RAG용 text 후보로 저장
- JSON table을 구조화 metadata로 변환
- 변환 완료 후 임시 파일 정리

테스트:

- synthetic PDF 변환
- table JSON fixture 파싱
- Markdown 출력 없는 경우 JSON fallback
- JSON schema가 바뀌어도 graceful failure

### ODL-4. 표 후보 필터링
작업:

- false table 제거 규칙 추가
- 1행 제목 박스 제거
- header 후보가 없는 작은 table 제거
- row/column 수, bbox 크기, cell text density 기준 적용
- `항목`, `내용`, `비고`, `연번`, `생산시설명`, `생산공정명`, `세부설명` 등 기준문서 표 header 우선 보존

테스트:

- 1행 제목 table 제거
- 직접생산 확인기준 table 보존
- 생산시설/생산공정 세부설명 table 보존
- 빈 cell이 많아도 의미 있는 row는 유지

### ODL-5. 기준문서 table-row chunk 추가
작업:

- `split_basis_tables_into_row_chunks()` 추가
- paragraph chunk와 table-row chunk를 함께 생성
- table-row chunk text 형식 표준화

예시:

```text
[표: 직접생산 확인기준] [항목: 생산시설]
내용: ① 절단기 ② 천공기 ③ 능형망기 ④ 용접기 ⑤ 검사설비
비고: 임차보유 인정하지 않음
```

테스트:

- table-row chunk 생성 수 검증
- chunk metadata에 `table_id`, `row_index`, `column_headers` 포함
- 기존 paragraph chunk 검색은 유지
- table-row query 검색 hit 검증

### ODL-6. JSON basis index 확장
작업:

- index payload metadata에 table metadata 포함
- `basis_search_results()`가 table metadata를 응답에 포함
- citation payload에 page/table/row/bbox 정보 포함

테스트:

- index checksum 검증
- rebuild 후 table metadata 유지
- 검색 결과 `index_source=json_basis_index` 유지
- citation candidate id 기존 형식 유지

### ODL-7. API/UX 반영
작업:

- 기준문서 상세 화면에 parser engine 표시
- table row chunk 검색 결과에 표/행 정보 표시
- 운영 대시보드 또는 설정 화면에 PDF reader 상태 표시
- fallback 발생 시 관리자에게 표시

테스트:

- 프론트 contract 테스트
- fallback 상태 표시 테스트
- basis search 결과 metadata 렌더링 테스트

### ODL-8. 문서 및 운영 가이드
작업:

- README 세팅 가이드 업데이트
- `docs/ai-api-setup.md`와 충돌 없이 Java/ODL 설정 분리
- `docs/basis-document-extraction-improvement-plan.md` 업데이트
- work-log 기록

테스트:

- 링크 유효성 확인
- 인코딩 체크
- 다른 PC 세팅 가이드 검토

## 테스트 계획
### 1. 단위 테스트
대상:

- `OpenDataLoaderPdfReader`
- `PyMuPdfPdfReader`
- `AutoPdfReader`
- ODL JSON parser
- table candidate filter
- table-row chunk builder

필수 케이스:

- 정상 PDF
- 빈 PDF
- 표 포함 PDF
- 2단 PDF
- 한글 텍스트 PDF
- 잘못된 JSON
- ODL timeout
- Java 미설치 simulation
- opendataloader 패키지 미설치 simulation

예상 파일:

- `backend/tests/test_pdf_readers.py`
- `backend/tests/test_basis_table_extraction.py`
- `backend/tests/test_basis_table_chunks.py`

### 2. 통합 테스트
대상:

- `extract_document()`
- `process_basis_document()`
- 기준문서 chunk/index/search
- 나라장터 저장/분석 경로

필수 케이스:

- `PDF_READER_ENGINE=pymupdf`
- `PDF_READER_ENGINE=opendataloader`
- `PDF_READER_ENGINE=auto`
- ODL 실패 후 fallback
- fallback 후 `needs_ocr` 판단 유지
- 기준문서 재처리 원자성 유지
- JSON basis index rebuild 유지

예상 파일:

- `backend/tests/test_parser.py`
- `backend/tests/test_api_flows.py`
- `backend/tests/test_real_basis_document_rag.py`

### 3. 실제 기준문서 QA
대상 PDF:

- 사용자 제공 원본:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 테스트용 repo 샘플:
  - `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`

기준 파일:

- 사용자 제공 TXT
- 사용자 제공 DOCX
- 사용자 제공 MD

사전 준비:

- 원본 PDF가 위 사용자 경로에 존재하는지 확인한다.
- `scripts/register-real-basis-document-sample.py`로 repo 테스트 샘플 폴더에 복사/등록한다.
- 기존에 등록된 동일 파일이 있으면 hash를 비교해 같은 파일인지 확인한다.
- 이후 모든 ODL 기준문서 QA는 repo 테스트 샘플 경로를 사용한다.

검증 항목:

- 전체 489쪽 변환 성공
- 논리 페이지/물리 페이지 metadata 일관성
- Markdown table row coverage
- token recall
- char 5-gram recall
- numeric recall
- table false positive 비율
- 처리 시간
- table-row 검색 hit

목표 기준:

- 전체 변환 성공
- 기준 MD 대비 `reference_table_row_coverage_in_regenerated >= 0.80`
- `regenerated_table_row_coverage_in_reference >= 0.75`
- TXT/DOCX 대비 token recall 기존 baseline 이상
- numeric recall 기존 baseline 이상
- table-row query coverage >= 0.80

필수 실행 시나리오:

1. `PDF_READER_ENGINE=opendataloader`로 이 PDF 전체 변환
2. `PDF_READER_ENGINE=auto`로 이 PDF 전체 변환
3. OpenDataLoader 실패 simulation 후 PyMuPDF fallback 확인
4. ODL Markdown/JSON 기반 재생성 MD와 사용자 제공 기준 MD 비교
5. table-row chunk 생성 후 직접생산 조건 검색 QA
6. 기준문서 재처리 실패 simulation 후 기존 chunk/index 보존 확인

### 4. 나라장터 PDF 샘플 회귀 테스트
대상:

- 이미 다운로드한 나라장터 PDF 30개 샘플
- Phase 1.7 QA PDF 샘플
- Phase 2 운영 QA PDF 샘플

검증 항목:

- 기존 PyMuPDF 대비 char count 급감 없음
- 공고명/입찰금액/기간/참가자격 키워드 추출 유지
- unsupported attachment 처리 영향 없음
- 분석 API 응답 schema 유지

목표 기준:

- 기존 샘플 테스트 전체 통과
- ODL 적용 후 공고문 분석 실패율 증가 없음
- fallback 발생 시 실패가 아니라 metadata로 기록

### 5. 실패/복구 테스트
필수 케이스:

- Java 없음
- ODL 패키지 없음
- ODL CLI/convert timeout
- ODL JSON 손상
- output directory 쓰기 실패
- PDF 암호화
- 매우 큰 PDF
- 변환 중 예외 발생

목표:

- 앱 시작 실패 없음
- 기준문서 기존 정상 chunk가 먼저 삭제되지 않음
- 재처리 실패 시 기존 index 보존
- 실패 사유가 metadata/error_message에 기록
- 관리자 UX에서 fallback/failed 상태 확인 가능

### 6. 성능 테스트
측정 항목:

- 1쪽당 평균 처리 시간
- 489쪽 기준문서 전체 처리 시간
- 나라장터 PDF 30개 전체 처리 시간
- 메모리 사용량
- 임시 파일 정리 여부

목표 기준:

- 기준문서 489쪽이 운영 허용 시간 안에 완료
- timeout 설정으로 무한 대기 없음
- 반복 호출 대신 batch 또는 per-file timeout 전략 사용
- 변환 후 temp directory 정리

### 7. UX/API 테스트
검증 항목:

- 기준문서 업로드 후 parser engine 표시
- fallback 발생 시 상태 표시
- 검색 결과에 table row citation 표시
- 관리자 설정/운영 화면에서 PDF reader 상태 확인
- 프론트가 추가 metadata를 받아도 깨지지 않음

테스트 방법:

- API contract 테스트
- Playwright 기반 UX smoke test
- monkey test는 기준문서 업로드/검색/삭제/재처리 화면 중심으로 수행

### 8. 전체 회귀 테스트
명령:

```powershell
py -3.13 -m pytest backend/tests -q
py -3.13 scripts/check-encoding.py
git diff --check
```

프론트 변경이 있을 경우:

```powershell
npm --prefix frontend run build
node scripts/ux-monkey-test.mjs
```

## 합격 기준
OpenDataLoader를 기본 PDF 리더로 전환하려면 다음 조건을 모두 만족해야 합니다.

- 전체 backend 테스트 통과
- 프론트 build 통과
- 사용자 제공 기준문서 PDF 전체 변환 성공
- 사용자 제공 기준문서 PDF를 repo 테스트 샘플로 등록한 뒤 ODL/auto/fallback 시나리오 통과
- 사용자 제공 MD 대비 table row coverage 개선
- TXT/DOCX 대비 본문/숫자 추출 회귀 없음
- 나라장터 PDF 30개 회귀 없음
- Java/ODL 실패 시 PyMuPDF fallback 정상 작동
- 기준문서 재처리 실패 시 기존 지식 보존
- JSON basis index 정합성 유지
- README와 work-log 업데이트 완료

## 실행 결과 기준선 (2026-06-05)
계획에 따라 1차 교체 구현과 테스트를 진행했습니다.

구현 완료:
- `backend/requirements.txt`에 `opendataloader-pdf==2.4.7` 추가
- `backend/app/pipelines/pdf_readers.py` 추가
- 기본 PDF 리더를 `PDF_READER_ENGINE=auto`로 전환
- OpenDataLoader 실패 시 PyMuPDF fallback 유지
- 기준문서 table metadata와 `table_row` chunk 생성
- PDF 리더 상태 API 추가: `GET /api/settings/pdf-reader/status`
- 실제 기준문서 OpenDataLoader QA 스크립트 추가: `scripts/run-opendataloader-real-basis-qa.py`
- README, 기술 요약, work-log 업데이트

실제 기준문서 QA:
- 대상 PDF: 489쪽
- `PDF_READER_ENGINE=opendataloader`: 통과
- `PDF_READER_ENGINE=auto`: 통과
- OpenDataLoader timeout simulation 후 PyMuPDF fallback: 통과
- OpenDataLoader 추출 결과:
  - table count: 1,566
  - table row count: 10,637
  - 기준문서 table-row chunk: 9,069
  - 기준 MD 대비 service row token coverage: 1.0
  - service 대비 기준 MD row token coverage: 0.9795

주의 기준선:
- 정확 문자열 기반 table row coverage는 기준 MD와 OpenDataLoader Markdown의 셀 병합/줄바꿈/공백 차이 때문에 warning으로 남습니다.
- 현재 QA 합격 기준은 exact row coverage가 아니라 token 기반 table row coverage를 주요 기준으로 사용합니다.

## 예상 리스크와 대응
| 리스크 | 영향 | 대응 |
|---|---|---|
| Java 미설치 | PDF 변환 실패 | `auto` 모드 fallback, README 설치 안내 |
| JVM 호출 비용 | 처리 지연 | timeout, batch 변환, 기준문서 우선 적용 |
| table 과검출 | RAG 노이즈 증가 | rows/headers/bbox/cell density 필터 |
| ODL JSON schema 변화 | parser 실패 | schema guard, fixture test, graceful fallback |
| text 출력 반복 노이즈 | 검색 품질 저하 | text 출력보다 Markdown/JSON 중심 사용 |
| hybrid 의존성 증가 | 설치 난이도 증가 | 1차 범위에서 hybrid 제외 |

## 작업 순서
권장 순서:

1. ODL-1 의존성/설정 추가
2. ODL-2 reader adapter 분리
3. ODL-3 JSON/Markdown 파싱
4. ODL-4 table filter
5. ODL-5 table-row chunk
6. ODL-6 JSON basis index metadata 확장
7. ODL-7 API/UX 반영
8. ODL-8 문서/운영 가이드
9. 실제 기준문서 QA
10. 나라장터 PDF 30개 회귀 QA
11. 전체 코드 리뷰와 버그 수정

## 보류 범위
다음은 이번 교체 1차 범위에서 제외합니다.

- OpenDataLoader hybrid 서버 상시 운영
- OCR 전략을 OpenDataLoader로 전면 교체
- PDF/UA accessibility 기능
- HWP/HWPX 지원
- 공고문 분석 로직의 판단 엔진 변경

---

# AI / Engineering Version (English)

## Current Implementation Status
Last updated: 2026-06-07

- [x] Default PDF reader switched to `PDF_READER_ENGINE=auto`
- [x] OpenDataLoader first, PyMuPDF fallback retained
- [x] Target documents, Nara PDFs, and basis PDFs share the same `extract_document()` reader policy
- [x] OpenDataLoader JSON/Markdown generates table metadata and `table_row` chunks
- [x] PyMuPDF fallback page `char_start`/`char_end` offsets fixed
- [x] Nested OpenDataLoader JSON text/table-cell loss fixed
- [x] DOCX paragraph and table-cell extraction implemented
- [x] Long single-paragraph chunk overlap fixed
- [x] Missing stored basis PDF reprocessing preserves existing completed/indexed RAG knowledge
- [x] Basis rule approval and Phase 3 judgment citations validate JSON basis-index health

Latest verification:
- targeted PDF/parser/table tests: `22 passed`
- new API regression tests: `4 passed`
- full backend tests: `134 passed`, `8 skipped`
- encoding check: `ENCODING_CHECK_OK`

## Purpose
Define the implementation and test plan for replacing the current PyMuPDF-centered PDF reader with `opendataloader-project/opendataloader-pdf`.

The goal is not just replacing a text extractor. The real objective is to preserve table structure, rows, columns, pages, bounding boxes, and citation metadata for basis-document RAG.

## Decision
Proceed with replacement, but keep PyMuPDF as a fallback engine.

Default operational mode should be:

```text
PDF_READER_ENGINE=auto
```

This means:

- OpenDataLoader first
- PyMuPDF fallback on Java/package/timeout/conversion failures
- basis documents use OpenDataLoader JSON/Markdown first
- Nara notice PDFs stay protected by regression tests before full rollout

## External Dependency
Confirmed official requirements:

- package: `opendataloader-pdf`
- version checked: `2.4.7`
- license: Apache-2.0
- Java 11+
- Python 3.10+
- outputs: JSON, Markdown, Text, HTML, Tagged PDF
- useful options:
  - `format="markdown,json"`
  - `table_method="cluster"`
  - `reading_order="xycut"`
  - `pages`
  - `markdown_with_html`
  - `threads`

Important note:

- each Python `convert()` call spawns a JVM process, so avoid many repeated calls and use timeout/batch strategies.
- hybrid/OCR mode requires additional server setup and is out of scope for the first replacement phase.

## Current Architecture
Current entrypoint:

- `backend/app/pipelines/parser.py::extract_document()`
- PDF path calls `_extract_pdf_text()`
- PyMuPDF uses `page.get_text("blocks")`

Basis pipeline:

```text
process_basis_document()
  -> extract_document()
  -> run_ocr_if_needed()
  -> normalize_basis_text()
  -> split_basis_text_into_chunks()
  -> index_basis_chunks()
```

Weaknesses:

- plain text-centered parser result
- no table id / row index / column header / bbox metadata
- paragraph-window chunks only
- table-row citations are not possible yet

## Target Architecture
Introduce PDF reader adapters:

```text
extract_document()
  -> read_pdf_document()
       -> OpenDataLoaderPdfReader
       -> PyMuPdfPdfReader
       -> AutoPdfReader
```

Extend basis processing:

```text
process_basis_document()
  -> extract_document()
  -> normalize_basis_text()
  -> split_basis_text_into_chunks()
  -> split_basis_tables_into_row_chunks()
  -> index_basis_chunks()
```

## Implementation Phases
### ODL-1. Dependencies and config
- Add `opendataloader-pdf==2.4.7`.
- Add Java setup guidance.
- Add PDF reader config.
- Add reader health/status checks.

### ODL-2. Reader adapter layer
- Add `backend/app/pipelines/pdf_readers.py`.
- Move current PyMuPDF logic into `PyMuPdfPdfReader`.
- Add `OpenDataLoaderPdfReader`.
- Add `AutoPdfReader`.
- Keep `ParsedDocument.text/kind/metadata` compatible.

### ODL-3. Parse OpenDataLoader JSON/Markdown
- Run ODL in a safe temp directory.
- Use `format="markdown,json"`.
- Parse paragraphs/headings/lists/tables.
- Convert table JSON into normalized metadata.
- Clean temp outputs.

### ODL-4. Table candidate filtering
- Remove one-row title tables.
- Preserve direct-production criteria tables.
- Filter by row/column count, header tokens, bbox size, and cell text density.

### ODL-5. Table-row chunks
- Add `split_basis_tables_into_row_chunks()`.
- Generate `table_row` chunks.
- Include table id, row index, column headers, cell texts, page, and bbox.

### ODL-6. JSON basis index metadata
- Include table metadata in index payloads.
- Keep citation ids stable.
- Expose table metadata through search results.

### ODL-7. API/UX
- Show parser engine.
- Show fallback status.
- Show table-row citation metadata.
- Add PDF reader status to settings/operations UX if needed.

### ODL-8. Docs and rollout
- Update README.
- Update extraction/RAG docs.
- Log all work in work-log.

## Test Plan
### Unit tests
- reader adapters
- ODL JSON parser
- table filter
- table-row chunk builder
- Java/package/timeout failure simulation

### Integration tests
- `PDF_READER_ENGINE=pymupdf`
- `PDF_READER_ENGINE=opendataloader`
- `PDF_READER_ENGINE=auto`
- fallback path
- basis document processing/indexing/search
- Nara notice analysis paths

### Real basis QA
- fixed source PDF:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- repo test sample:
  - `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- full 489-page basis PDF conversion
- compare against user TXT/DOCX/MD references
- table-row coverage
- token recall
- numeric recall
- table-row query hit rate
- required scenarios:
  - full conversion with `PDF_READER_ENGINE=opendataloader`
  - full conversion with `PDF_READER_ENGINE=auto`
  - fallback simulation after OpenDataLoader failure
  - regenerated Markdown comparison against the user-provided MD
  - table-row chunk search QA
  - failed reprocessing simulation that preserves existing chunks/index

### Nara PDF regression
- already downloaded 30 PDF samples
- phase 1.7 and phase 2 QA samples
- no analysis failure increase
- no major char-count regression

### Failure/recovery tests
- Java missing
- package missing
- timeout
- corrupt JSON
- encrypted PDF
- temp directory failure
- conversion exception

### Performance tests
- time per page
- full basis conversion time
- 30 Nara PDF batch time
- temp file cleanup

### UX/API tests
- parser engine visible
- fallback state visible
- table-row citations rendered
- API contract does not break frontend

## Implementation Result Baseline (2026-06-05)
The first replacement pass has been implemented and tested.

Implemented:
- added `opendataloader-pdf==2.4.7`
- added `backend/app/pipelines/pdf_readers.py`
- switched the default PDF reader mode to `PDF_READER_ENGINE=auto`
- kept PyMuPDF fallback for OpenDataLoader failures
- added basis-document table metadata and `table_row` chunks
- added PDF reader status API: `GET /api/settings/pdf-reader/status`
- added real basis QA script: `scripts/run-opendataloader-real-basis-qa.py`
- updated README, technology summary, and work-log

Real basis QA:
- fixed basis PDF: 489 pages
- `PDF_READER_ENGINE=opendataloader`: passed
- `PDF_READER_ENGINE=auto`: passed
- timeout simulation with PyMuPDF fallback: passed
- OpenDataLoader extraction:
  - table count: 1,566
  - table row count: 10,637
  - basis table-row chunks: 9,069
  - service row token coverage against reference MD: 1.0
  - reference MD row token coverage against service: 0.9795

Known baseline warning:
- exact string-based table-row coverage remains a warning because the reference MD and OpenDataLoader Markdown differ in cell merging, line breaks, and whitespace.
- QA acceptance uses token-based table-row coverage as the main table preservation metric.

## Acceptance Criteria
The replacement can become default only when:

- all backend tests pass
- frontend build passes if touched
- full conversion succeeds for the fixed user-provided basis PDF
- the fixed basis PDF passes OpenDataLoader, auto, and fallback scenarios after being registered as the repo test sample
- MD table-row coverage improves from the current baseline
- TXT/DOCX text and numeric recall do not regress
- 30 Nara PDFs do not regress
- Java/ODL failure falls back to PyMuPDF
- failed basis reprocessing preserves existing knowledge
- JSON basis index remains consistent
- README and work-log are updated
