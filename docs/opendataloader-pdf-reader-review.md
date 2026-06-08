# OpenDataLoader PDF 리더 전환 검토

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

이 문서는 2026-06-05의 교체 전 검토 기록입니다. 당시 결론은 “전면 교체는 아직 이르고 기준문서/table-heavy PDF 보조 엔진으로 먼저 도입”이었지만, 이후 구현과 QA를 거쳐 현재 코드는 다음 상태로 변경되었습니다.

- 기본 PDF 리더는 `PDF_READER_ENGINE=auto`입니다.
- `auto`는 OpenDataLoader PDF를 먼저 사용하고, Java/패키지/timeout/변환 실패 시 PyMuPDF fallback을 사용합니다.
- 기준문서뿐 아니라 일반 업로드 문서와 나라장터 공고문 PDF도 동일한 `extract_document()` 진입점을 통해 현재 reader 정책을 공유합니다.
- PyMuPDF는 제거되지 않았고 fallback 및 OCR 렌더링 보조 엔진으로 유지됩니다.
- 실제 기준문서 489쪽 OpenDataLoader QA와 fallback QA가 통과했고, 이후 PDF/RAG 보강 뒤 전체 backend 기준선은 `134 passed`, `8 skipped`입니다.
- 따라서 아래의 “전면 교체는 아직 이르다”는 문장은 역사적 검토 결론으로 읽고, 현재 실행 기준은 `docs/opendataloader-pdf-replacement-test-plan.md`와 `README.md`를 우선합니다.

## 검토 목적
현재 서비스의 PDF 추출기는 PyMuPDF 기반 평문 추출에 가깝습니다.
최근 실제 기준문서 PDF를 Markdown으로 재생성하고 사용자 제공 기준 MD와 비교한 결과, 본문과 숫자 추출은 안정적이지만 표 구조 보존이 RAG 품질의 핵심 병목으로 확인되었습니다.

이 문서는 `opendataloader-project/opendataloader-pdf`를 우리 PDF 리더로 교체하거나 보조 엔진으로 도입할지 검토한 결과입니다.

## 결론
전면 교체는 아직 이릅니다.

권장 방향은 다음과 같습니다.

1. `OpenDataLoader PDF`를 기준문서 전용 또는 table-heavy PDF 전용 보조 엔진으로 먼저 도입한다.
2. 기존 PyMuPDF 추출기는 공고문/단순 PDF의 빠른 fallback으로 유지한다.
3. 기준문서 파이프라인에는 OpenDataLoader JSON의 `table`, `table row`, `table cell`, `bounding box`, `page number`를 활용해 table-row chunk를 만든다.
4. 전체 전환 여부는 실제 기준문서 전체 489쪽과 나라장터 PDF 30개 샘플의 비교 리포트가 통과한 뒤 결정한다.

## 외부 라이브러리 요약
- 저장소: `https://github.com/opendataloader-project/opendataloader-pdf`
- PyPI 패키지: `opendataloader-pdf`
- 최신 확인 버전: `2.4.7`
- 라이선스: Apache-2.0
- 런타임 요구사항: Java 11 이상, Python 3.10 이상
- 출력 포맷: JSON, Markdown, HTML, Text, PDF, Tagged PDF
- 주요 옵션:
  - `--format markdown,json,text`
  - `--table-method cluster`
  - `--reading-order xycut`
  - `--pages`
  - `--markdown-with-html`
  - `--sanitize`
  - `--hybrid docling-fast`
  - `--hybrid-fallback`

## 우리 서비스 현재 상태
현재 PDF 추출 진입점은 다음입니다.

- `backend/app/pipelines/parser.py`
  - `extract_document()`
  - PDF면 `_extract_pdf_text()` 호출
  - PyMuPDF `page.get_text("blocks")`로 블록을 읽고 좌/우 컬럼 기준 정렬
  - 반환 metadata는 page count, page별 char count 정도

기준문서 RAG 파이프라인은 다음 흐름입니다.

- `backend/app/pipelines/basis_document.py`
  - `extract_document()`
  - `run_ocr_if_needed()`
  - `normalize_basis_text()`
  - `split_basis_text_into_chunks()`
  - `index_basis_chunks()`

현재 chunk metadata에는 `page_start`, `page_end`, `section_title`은 있으나 표 ID, 행 번호, 열 제목, bbox, 논리 페이지 같은 정보가 없습니다.

## PoC 실행 결과
로컬 환경 확인:

- Java: OpenJDK 25
- Python: 3.13
- 설치: 임시 venv `temp/opendataloader-venv`에 `opendataloader-pdf==2.4.7`

### 기준문서 앞 6쪽
명령 요약:

```powershell
opendataloader-pdf temp/opendataloader-basis-first6.pdf `
  -o temp/opendataloader-out `
  -f markdown,json,text `
  --table-method cluster
```

결과:

- 실행 시간: 약 0.92초
- JSON: 69,729 bytes
- Markdown: 22,054 bytes
- Text: 5,015 bytes
- 요소 타입: paragraph, list item, heading 중심
- 앞쪽은 고시 개정 이력/목차 성격이라 표 검증에는 적합하지 않았음

주의:

- text 출력은 일부 반복/들여쓰기 노이즈가 있었음
- Markdown/JSON 출력이 RAG 입력으로 더 적합함

### 기준문서 120-125쪽
명령 요약:

```powershell
opendataloader-pdf "<기준문서 PDF>" `
  -o temp/opendataloader-out-pages120 `
  -f markdown,json,text `
  --table-method cluster `
  --pages "120-125"
```

결과:

- 실행 시간: 약 9.37초
- JSON: 351,311 bytes
- Markdown: 19,569 bytes
- Text: 23,084 bytes
- JSON type count:
  - paragraph: 426
  - table cell: 407
  - table row: 136
  - list item: 95
  - list: 43
  - table: 27
  - heading: 6
  - caption: 4
- 2행 이상 table: 21개

품질 관찰:

- `직접생산 확인기준` 표가 Markdown table로 재구성됨
- JSON에 `table`, `table row`, `table cell`, `page number`, `bounding box`, row/column/span 정보가 들어 있음
- 기존 PyMuPDF 평문 추출은 같은 구간에서 표 셀이 줄 단위로 흩어짐
- ODL은 `항목 / 내용 / 비고`, `생산공장`, `생산시설`, `생산인력`, `생산공정`, `기타` 같은 조건 테이블을 훨씬 RAG 친화적으로 보존함
- 다만 페이지 상단의 경쟁제품 제목 박스처럼 1행 제목 영역도 table로 잡히므로 false table filtering은 필요함

## 장점
1. 표 구조 보존
   - 기준문서 RAG의 핵심인 직접생산 확인기준 표를 Markdown/JSON으로 유지할 수 있습니다.

2. citation 품질 개선
   - JSON 요소마다 page number와 bounding box가 있으므로 향후 “근거 위치 하이라이트” UX에 유리합니다.

3. 다단 PDF 읽기 순서
   - XY-Cut 기반 reading order 옵션이 있어 현재 수동 좌/우 컬럼 정렬보다 확장성이 좋습니다.

4. 라이선스 적합성
   - Apache-2.0이라 현재 서비스에 도입 부담이 낮습니다.

5. Python API/CLI 둘 다 가능
   - 현재 Python 백엔드에서 adapter로 감싸기 쉽습니다.

## 리스크
1. Java 의존성
   - 사용자가 다른 PC에서 테스트할 때 Java 11 이상 설치가 필요합니다.
   - README와 세팅 가이드에 Java 설치 확인을 추가해야 합니다.

2. 성능
   - 각 변환 호출이 JVM 프로세스를 띄우므로 작은 파일을 반복 처리하면 느릴 수 있습니다.
   - 대량 공고문 PDF는 batch 처리 또는 기존 PyMuPDF fallback이 필요합니다.

3. 표 과검출
   - 제목 박스, 고시번호 박스 같은 1행짜리 table도 잡힙니다.
   - `rows >= 2`, `cells >= 4`, header token, numeric density, bbox 크기 등으로 필터링해야 합니다.

4. text 출력 품질
   - PoC에서 text 출력은 일부 반복 노이즈가 있었습니다.
   - RAG용 기본 입력은 text가 아니라 Markdown/JSON으로 잡아야 합니다.

5. Hybrid/OCR 범위
   - hybrid/OCR은 별도 서버와 추가 의존성이 필요합니다.
   - 기존 OCR 가드레일에 따라 ODL hybrid는 선택 기능으로 두고, OCR 주 엔진 정책과 충돌하지 않게 해야 합니다.

## 권장 아키텍처
PDF 추출을 단일 함수가 아니라 엔진 어댑터로 분리합니다.

```text
extract_document()
  -> PdfReaderAdapter
       -> PyMuPdfPdfReader
       -> OpenDataLoaderPdfReader
       -> AutoPdfReader
```

환경변수 예시:

```text
PDF_READER_ENGINE=pymupdf|opendataloader|auto
PDF_READER_ODL_TABLE_METHOD=cluster
PDF_READER_ODL_FORMAT=markdown,json
PDF_READER_ODL_TIMEOUT_SECONDS=120
PDF_READER_ODL_USE_HYBRID=false
```

기준문서 업로드는 기본적으로 `auto`를 사용합니다.

- 표 밀도가 높거나 기준문서 PDF면 OpenDataLoader 우선
- OpenDataLoader 실패 또는 Java 미설치면 PyMuPDF fallback
- fallback 발생 시 metadata에 `reader_fallback_reason` 기록

나라장터 공고문 PDF는 우선 PyMuPDF를 유지합니다.

- 공고문은 본문 요구조건 추출이 우선이고, 빠른 처리와 안정성이 중요함
- 표가 많은 공고문만 추후 auto mode로 ODL을 시도

## 구현 단계 제안
### 1단계: 검증용 어댑터 추가
- `backend/app/pipelines/pdf_readers.py` 추가
- `PdfReadResult` 데이터 구조 정의
- PyMuPDF reader를 기존 로직에서 분리
- OpenDataLoader reader는 선택 의존성으로 구현
- Java 미설치, 패키지 미설치, timeout 실패 시 명확한 error metadata 반환

### 2단계: 기준문서 비교 스크립트 확장
- 기존 `scripts/regenerate-real-basis-document-md.py`에 `--engine pymupdf|opendataloader` 추가
- 전체 기준문서에 대해 다음 metric 비교
  - token recall
  - char n-gram recall
  - Markdown table row coverage
  - table count
  - false table 후보 수
  - 처리 시간

### 3단계: table row chunk 도입
- ODL JSON table을 DB chunk로 변환
- chunk metadata 추가:
  - `chunk_type=table_row`
  - `source_engine=opendataloader-pdf`
  - `page_number`
  - `bbox`
  - `table_id`
  - `row_index`
  - `column_headers`
  - `cell_texts`
- 기존 citation id는 유지하고 payload metadata만 확장

### 4단계: 기준문서 RAG QA
- 사용자 제공 기준 MD와 전체 489쪽 비교
- 나라장터 PDF 30개 샘플 회귀 테스트
- 검색 평가 API에서 table-row query coverage 확인

### 5단계: 운영 적용
- 기준문서 업로드 기본 엔진을 `auto`로 전환
- 설정 화면에 PDF reader 상태 표시
- README에 Java 설치와 ODL 사용 조건 추가

## 전환 판단 기준
OpenDataLoader를 기준문서 기본 엔진으로 올리려면 다음 조건을 만족해야 합니다.

- 전체 기준문서 처리 성공
- 기준 MD 대비 reference table row coverage가 현재 0.7644보다 개선
- false table 비율이 필터링 후 운영 허용 범위
- 기존 `backend/tests` 전체 통과
- Java 미설치 환경에서 PyMuPDF fallback 정상 작동
- 나라장터 공고문 QA에서 기존보다 심각한 추출 회귀 없음

## 최종 판단
OpenDataLoader PDF는 우리 서비스의 “기준문서 RAG + 표 기반 직접생산 조건 추출”에는 좋은 후보입니다.

하지만 공고문 PDF까지 전부 즉시 교체하면 Java 의존성, 처리 시간, 출력 차이 때문에 회귀 위험이 큽니다.

따라서 지금은 다음 순서가 가장 안전합니다.

1. 기준문서 전용 OpenDataLoader adapter 도입
2. 기존 PyMuPDF fallback 유지
3. 전체 기준문서 MD 비교 metric으로 품질 검증
4. table-row chunk와 citation metadata 보강
5. 이후 공고문 PDF까지 auto mode 확대 검토

---

# AI / Engineering Version (English)

## Purpose
Evaluate whether `opendataloader-project/opendataloader-pdf` should replace the current PyMuPDF-based PDF reader.

## Recommendation
Do not fully replace PyMuPDF immediately.

Introduce OpenDataLoader PDF as an optional adapter for basis documents and table-heavy PDFs, while keeping PyMuPDF as the fast fallback for simple Nara notice PDFs.

## Current Code Update
Last updated: 2026-06-07

This document is the pre-replacement review from 2026-06-05. Its original conclusion recommended introducing OpenDataLoader first as a basis/table-heavy helper rather than fully replacing PyMuPDF. The implementation has since moved to:

- default `PDF_READER_ENGINE=auto`
- OpenDataLoader PDF first
- PyMuPDF fallback on Java/package/timeout/conversion failures
- shared `extract_document()` entrypoint for target documents, Nara PDFs, and basis PDFs
- PyMuPDF retained as fallback and OCR rendering helper
- latest backend baseline after PDF/RAG hardening: `134 passed`, `8 skipped`

Treat the earlier conservative recommendation as historical context. Use `docs/opendataloader-pdf-replacement-test-plan.md` and `README.md` as the current operational references.

## Historical System Before Replacement
- Current entrypoint: `backend/app/pipelines/parser.py::extract_document()`
- Current PDF engine: PyMuPDF `page.get_text("blocks")`
- Current basis RAG pipeline chunks normalized plain text into paragraph-window chunks.
- Current metadata lacks table id, row index, column headers, bbox, and logical page metadata.

## PoC Results
Runtime:
- Java: OpenJDK 25
- Python: 3.13
- Package: `opendataloader-pdf==2.4.7`

First 6 pages:
- elapsed: 0.92s
- output: JSON, Markdown, Text
- mostly paragraphs/list items/headings
- not table-heavy enough for table QA

Pages 120-125:
- elapsed: 9.37s
- JSON size: 351,311 bytes
- Markdown size: 19,569 bytes
- detected typed JSON elements:
  - paragraph: 426
  - table cell: 407
  - table row: 136
  - list item: 95
  - list: 43
  - table: 27
  - heading: 6
  - caption: 4
- tables with at least two rows: 21

Quality:
- ODL preserves direct-production criteria tables much better than current plain PyMuPDF text extraction.
- JSON includes page number, bounding box, table rows, cells, row/column spans.
- False-positive one-row title tables still require filtering.
- Use Markdown/JSON as RAG input, not plain text output.

## Proposed Architecture
Add PDF reader adapters:

```text
extract_document()
  -> PdfReaderAdapter
       -> PyMuPdfPdfReader
       -> OpenDataLoaderPdfReader
       -> AutoPdfReader
```

Suggested environment variables:

```text
PDF_READER_ENGINE=pymupdf|opendataloader|auto
PDF_READER_ODL_TABLE_METHOD=cluster
PDF_READER_ODL_FORMAT=markdown,json
PDF_READER_ODL_TIMEOUT_SECONDS=120
PDF_READER_ODL_USE_HYBRID=false
```

## Implementation Plan
1. Add `backend/app/pipelines/pdf_readers.py`.
2. Move the current PyMuPDF logic into `PyMuPdfPdfReader`.
3. Add `OpenDataLoaderPdfReader` as an optional dependency wrapper.
4. Extend the real basis Markdown regeneration script with `--engine`.
5. Compare full 489-page basis PDF against the user-provided MD reference.
6. Add table-row chunks from ODL JSON with bbox/cell metadata.
7. Keep PyMuPDF fallback for Java/package/timeout failures.
8. Update README with Java and ODL setup guidance.

## Go / No-Go Criteria
Promote ODL to the default basis-document engine only if:

- full real basis PDF conversion succeeds
- table-row coverage improves over the current 0.7644 reference baseline
- false table rate is controlled by filters
- all backend tests pass
- Java-missing fallback works
- Nara notice PDF QA does not regress
