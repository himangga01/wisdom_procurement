# 기준문서 PDF 추출 로직 보완 계획

## 목적

현재 기준문서 RAG는 PDF를 업로드한 뒤 우리 서비스가 직접 텍스트를 추출하고, 그 결과를 청킹/인덱싱해 검색에 사용합니다.

이번 비교 테스트의 목적은 단순히 외부 TXT/DOCX/MD와 숫자상 일치율을 확인하는 것이 아니라, 실제 RAG 품질에 필요한 다음 항목을 보강하기 위한 것입니다.

- 기준문서 본문 텍스트 누락 여부 확인
- 표 형태 요구조건의 보존 여부 확인
- 세부품명, 생산시설, 검사설비, 공정 정보가 검색 가능한 단위로 남는지 확인
- 향후 citation에 필요한 페이지/표/행 메타데이터 확보

## 비교 대상

서비스 기준 추출 대상:

- `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 서비스 추출 방식: 현재 `app.pipelines.parser.extract_document()` 기반 PyMuPDF PDF 직접 파싱

외부 기준 파일:

- TXT: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).txt`
- DOCX: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx`
- MD: `중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`

## 비교 결과 요약

| 기준 파일 | 기준 문자 수 | 서비스 문자 수 | service token recall | reference token recall | service 5-gram recall | reference 5-gram recall | service line coverage | reference line coverage | numeric recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| TXT | 728,596 | 702,598 | 0.9001 | 0.7725 | 0.8103 | 0.8107 | 0.9948 | 0.9495 | 0.9880 / 0.9970 |
| DOCX | 720,588 | 702,598 | 0.9002 | 0.7721 | 0.8425 | 0.8489 | 0.9270 | 0.8992 | 0.9905 / 0.9971 |
| MD | 1,719,849 | 702,598 | 0.9073 | 0.3541 | 0.9358 | 0.3951 | 0.9955 | 0.5200 | 0.9979 / 0.3625 |

## 해석

### 1. 본문 텍스트 추출은 대체로 안정적

서비스 추출 텍스트가 TXT/DOCX/MD 기준에 들어있는 비율은 모두 약 90% 이상입니다.

이는 현재 PDF 직접 파싱 결과가 기준문서의 주요 본문, 조항, 숫자, 핵심 키워드를 상당히 잘 포함한다는 의미입니다.

### 2. TXT와 DOCX는 원문 본문 비교 기준으로 적합

TXT와 DOCX 기준은 서비스 추출 결과와 길이가 비슷합니다.

- TXT compact 문자 수: 554,696
- DOCX compact 문자 수: 550,700
- 서비스 compact 문자 수: 554,921

따라서 본문 텍스트 회수율, 숫자 회수율, 조항 검색 가능성 검증에는 TXT/DOCX가 적합합니다.

### 3. DOCX는 `python-docx`만 사용하면 비교가 왜곡됨

DOCX 기준 파일은 표가 많습니다.

- DOCX 문단 수: 3,576
- DOCX 표 수: 744
- DOCX 표 셀 수: 15,523

단순 `python-docx` 문단/표 셀 방식은 387,786자만 추출했습니다. 반면 DOCX 패키지 XML의 `w:t` 텍스트를 직접 읽으면 720,588자가 추출됩니다.

따라서 DOCX 기준 비교는 `docx-package-xml-wt` 방식이 맞습니다.

### 4. MD는 표 구조 보강 기준으로 적합

MD 기준 파일은 1,719,849자로 TXT/DOCX보다 훨씬 깁니다.

MD에는 다음 정보가 추가로 포함된 것으로 보입니다.

- Markdown 제목/설명
- Markdown 표 구분자
- 표 행/열 구조
- 표 감지 결과
- 원문 좌우 논리페이지 분리 결과

그래서 raw reference recall은 낮게 나오는 것이 자연스럽습니다.

- MD reference token recall in service: 0.3541
- MD reference 5-gram recall in service: 0.3951
- MD reference line coverage in service: 0.5200

이 수치는 우리 서비스가 본문을 못 뽑는다는 뜻이 아니라, 현재 서비스 추출 결과가 Markdown 표 구조와 행/열 표현을 보존하지 않는다는 뜻에 가깝습니다.

## 현재 추출 로직의 부족한 부분

### P1. 표 구조가 별도 산출물로 보존되지 않음

현재 서비스는 PDF 블록 텍스트를 읽고 정규화해 청킹합니다.

그러나 기준문서 RAG에서는 표가 핵심입니다.

- 세부품명
- 생산시설
- 검사설비
- 생산공정
- 기준 설명
- 예외 조건

이 정보가 표 행 단위로 보존되지 않으면 RAG 검색에서 특정 제품군의 직접생산 조건을 정확히 citation하기 어렵습니다.

### P1. 좌우 논리페이지/다단 레이아웃 처리가 충분하지 않음

MD 기준 파일 설명상 외부 추출은 PDF 내장 텍스트를 좌우 논리페이지 단위로 분리했습니다.

현재 서비스는 page block의 x/y 좌표를 기준으로 좌/우 컬럼을 정렬하지만, 기준문서처럼 한 물리 페이지 안에 두 논리 페이지가 들어가는 경우를 별도 메타데이터로 남기지는 않습니다.

### P1. 표 행과 주변 조항의 연결이 약함

RAG citation에서는 표 행만 있어도 부족하고, 해당 표가 어느 조항/제품군/페이지에 속하는지 알아야 합니다.

현재 청크 메타데이터에는 page range와 section title은 있으나, table id, row index, column labels, logical page, parent section 같은 구조화 메타데이터가 부족합니다.

### P2. Markdown 표 기준 평가가 아직 별도 지표로 분리되지 않음

현재 비교 지표는 전체 텍스트 기반입니다.

MD 기준 파일은 표 구조가 풍부하므로, 다음 지표를 별도로 계산해야 합니다.

- Markdown table row count
- table row token coverage
- numeric cell coverage
- header/column label coverage
- product-name row coverage

## 추출 로직 보완 계획

## 1단계. 비교/QA 기준선 보강

### 구현 항목

- `scripts/compare-real-basis-document-txt.py`를 기준 파일 비교 도구로 계속 사용한다.
- `.txt`, `.docx`, `.md` 기준 파일을 모두 지원한다.
- MD 기준 파일에 대해서는 raw text 비교와 table-aware 비교를 분리한다.
- 리포트에 reference type별 해석을 명확히 기록한다.

### 추가할 지표

- `markdown_table_count`
- `markdown_table_row_count`
- `markdown_table_header_count`
- `markdown_table_numeric_cell_count`
- `markdown_table_row_token_recall_in_service`
- `service_table_candidate_recall_in_markdown`

### 성공 기준

- TXT/DOCX service token recall >= 0.90 유지
- TXT/DOCX numeric recall >= 0.98 유지
- MD service token recall >= 0.90 유지
- MD table row coverage 기준선 산출

## 2단계. PDF 페이지 레이아웃 추출 보강

### 구현 항목

- `backend/app/pipelines/parser.py`에서 PDF 추출 결과를 단순 text뿐 아니라 layout metadata로 확장한다.
- PyMuPDF `page.get_text("dict")` 또는 `page.get_text("rawdict")` 기반으로 block/line/span 좌표를 수집한다.
- `page.get_text("words")` 기반 word 좌표도 보관한다.
- 물리 페이지 내 좌우 논리페이지 분리 후보를 계산한다.

### 산출 메타데이터

- `page_number`
- `logical_page_number`
- `column_index`
- `block_index`
- `line_index`
- `bbox`
- `font_size`
- `text`

### 성공 기준

- 기존 텍스트 추출 결과의 service token recall 저하 없음
- page coverage 1.0 유지
- 논리페이지 분리 결과가 MD 기준 페이지 흐름과 크게 어긋나지 않음

## 3단계. 표 감지 및 Markdown 표 변환

### 구현 항목

- PDF 선 정보와 텍스트 정렬 정보를 조합해 table candidate를 감지한다.
- PyMuPDF drawing/line 정보가 있으면 우선 사용한다.
- 선 정보가 부족한 경우 text alignment 기반 fallback을 사용한다.
- 표 후보를 Markdown table 또는 row-oriented plain text로 변환한다.
- 표 원문과 변환 결과를 모두 metadata에 보관한다.

### 표 산출물 예시

```json
{
  "table_id": "basis-2025-116-p129-t1",
  "page_number": 129,
  "logical_page_number": 258,
  "bbox": [0, 0, 0, 0],
  "headers": ["세부품명", "생산시설", "검사설비"],
  "rows": [
    {
      "row_index": 1,
      "cells": ["...", "...", "..."],
      "row_text": "세부품명 ... 생산시설 ... 검사설비 ..."
    }
  ]
}
```

### 성공 기준

- MD 기준 table row coverage 0.70 이상
- 주요 키워드 `세부품명`, `생산시설`, `검사설비`, `공정`이 포함된 표 행 검색 가능
- 숫자/면적/수량 cell recall 0.95 이상

## 4단계. 기준문서 청킹 전략 보강

### 구현 항목

현재는 paragraph-window 중심 청킹입니다.

기준문서 표 RAG를 위해 청킹을 다음 단위로 확장합니다.

- 본문 조항 청크
- 표 전체 청크
- 표 행 청크
- 표 행 + 주변 섹션 context 청크

### 청크 메타데이터

- `chunk_type`: `paragraph`, `table`, `table_row`, `table_context`
- `page_start`
- `page_end`
- `logical_page_start`
- `logical_page_end`
- `section_title`
- `table_id`
- `row_index`
- `column_headers`
- `source_bbox`

### 성공 기준

- RAG 검색에서 제품명/세부품명 질의가 표 행 청크를 반환
- citation candidate가 page + table + row 정보를 포함
- 기존 본문 검색 성능 저하 없음

## 5단계. RAG 인덱스와 citation 보강

### 구현 항목

- JSON basis index에 `chunk_type`, `table_id`, `row_index`, `logical_page` metadata를 포함한다.
- citation id는 기존 `basis:{document_id}:chunk:{chunk_id}`를 유지하되, payload에 table metadata를 추가한다.
- table row chunk는 검색 점수 계산에서 제품명/세부품명/숫자 token 가중치를 높인다.

### 성공 기준

- `/api/basis-search` 결과에서 table row citation 후보 확인 가능
- 검색 결과에 `chunk.metadata.table_id`, `row_index`, `column_headers` 포함
- MD table query coverage 0.80 이상

## 6단계. 테스트 코드 보강

### 추가 테스트

- `test_parser_pdf_layout_metadata.py`
  - PDF block/line/word 좌표 metadata 생성 검증
- `test_basis_table_extraction.py`
  - synthetic PDF table 감지 검증
  - line-based fallback 검증
- `test_real_basis_reference_compare.py`
  - TXT/DOCX/MD 기준 파일 비교 회귀 테스트
- `test_real_basis_document_rag.py`
  - table row query가 citation 후보를 반환하는지 검증

### 실제 기준문서 opt-in QA

- `RUN_REAL_BASIS_RAG_TESTS=1`
- TXT/DOCX/MD comparison reports 생성
- table-aware coverage 리포트 생성

## 우선순위

### 즉시 P1

1. MD table-aware comparison metric 추가
2. PDF layout metadata 추출 추가
3. table candidate 감지 prototype 추가
4. 표 행 청크 생성과 검색 테스트 추가

### 다음 P2

1. 논리페이지 분리 고도화
2. table row citation metadata UI 노출
3. 기준문서 검색 평가 API에 table coverage metric 추가
4. 실제 기준문서 기준 regression threshold 고정

## 현재 결론

현재 서비스의 PDF 직접 파싱은 본문 텍스트와 숫자 기준으로는 안정적입니다.

하지만 RAG 품질을 높이려면 단순 텍스트 회수율보다 표 구조 보존이 더 중요합니다. 특히 이 기준문서는 직접생산 조건이 대량의 표에 들어 있으므로, 다음 작업의 핵심은 표 행/열/논리페이지/섹션을 보존한 table-aware extraction pipeline입니다.

## 추가 확인: PDF -> MD 재생성 비교

우리 서비스 방식으로 실제 PDF를 Markdown으로 재생성하고 사용자 제공 MD와 직접 비교했습니다.

결과:

- PDF 물리 페이지 수: 489
- 재생성 논리페이지 수: 977
- 기준 MD 논리페이지 수: 977
- 재생성 Markdown 문자 수: 1,635,197
- 기준 MD 문자 수: 1,731,919
- 재생성 표 수: 3,034
- 기준 MD 표 수: 1,928
- 재생성 table row 수: 13,390
- 기준 MD table row 수: 11,351
- regenerated token recall in reference: 0.9303
- reference token recall in regenerated: 0.7931
- regenerated char 5-gram recall in reference: 0.8665
- reference char 5-gram recall in regenerated: 0.8171
- regenerated table row coverage in reference: 0.7060
- reference table row coverage in regenerated: 0.7644

추가 해석:

- 좌/우 논리페이지 분리 전략은 기준 MD와 동일한 논리페이지 수를 재현했다.
- PDF -> Markdown 재생성은 plain text 비교보다 기준 MD와 더 잘 맞는다.
- 현재 표 감지는 표 구조를 어느 정도 회수하지만, 기준 MD보다 표 수가 많아 과검출이 확인된다.
- 과검출 예시는 고시번호/제목 조각이 1행 표로 잡히는 경우가 많다.

추가 보완 우선순위:

1. 표 후보 최소 품질 조건 추가
   - 최소 row count
   - 최소 column count
   - header keyword 또는 numeric density
   - bbox 면적/텍스트 길이 기준
2. 인접 bbox 표 병합
   - 같은 논리페이지에서 연속된 작은 표 조각을 하나의 표로 병합
3. 제목/고시번호 false table 제거
   - `고시`, `일부개정`, `제20xx-` 중심의 짧은 1행 표 후보 제외
4. table row chunk 생성
   - 과검출 필터 후 행 단위 chunk를 생성
5. table-aware comparison metric 고정
   - `regenerated_table_row_coverage_in_reference >= 0.70`
   - `reference_table_row_coverage_in_regenerated >= 0.75`

---

# AI / Engineering Version (English)

## Purpose

The current basis-document RAG pipeline uploads the real basis PDF, extracts service-side text, chunks it, indexes it, and searches it.

The comparison tests are not just for text similarity. They are meant to identify extraction gaps that affect RAG quality, especially table-heavy direct-production requirements.

## References

Service source:

- `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- service extraction: PyMuPDF via `app.pipelines.parser.extract_document()`

External references:

- TXT reference
- DOCX reference
- MD reference

## Comparison Summary

| Reference | Reference chars | Service chars | service token recall | reference token recall | service 5-gram recall | reference 5-gram recall | service line coverage | reference line coverage | numeric recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| TXT | 728,596 | 702,598 | 0.9001 | 0.7725 | 0.8103 | 0.8107 | 0.9948 | 0.9495 | 0.9880 / 0.9970 |
| DOCX | 720,588 | 702,598 | 0.9002 | 0.7721 | 0.8425 | 0.8489 | 0.9270 | 0.8992 | 0.9905 / 0.9971 |
| MD | 1,719,849 | 702,598 | 0.9073 | 0.3541 | 0.9358 | 0.3951 | 0.9955 | 0.5200 | 0.9979 / 0.3625 |

## Interpretation

The service extraction is stable for body text and numeric content. TXT and DOCX are appropriate body-text references because their compact sizes are close to the service extraction.

The MD reference is much larger because it includes Markdown structure, table rendering, extraction notes, and logical page/table information. Low MD reference-to-service recall means the current service extraction does not preserve table structure, not that body extraction is fundamentally broken.

## Gaps

### P1. Table structure is not preserved

The service currently extracts normalized text and paragraph-window chunks. It does not preserve direct-production table rows as first-class RAG units.

### P1. Two-up/logical-page layout is weak

The external MD reference appears to split physical PDF pages into left/right logical pages. The service currently does not persist logical-page metadata.

### P1. Table rows are not connected to sections/citations

Chunks have page and section metadata, but not table id, row index, column headers, logical page, or source bbox.

### P2. Markdown table comparison needs separate metrics

Raw text metrics are not enough for the MD reference. Table-aware metrics should measure row/header/cell coverage.

## Improvement Plan

### Step 1. Strengthen comparison baselines

- Keep `scripts/compare-real-basis-document-txt.py` for TXT/DOCX/MD references.
- Add MD table-aware metrics.
- Separate raw-text comparison from table-structure comparison.

Acceptance:

- TXT/DOCX service token recall >= 0.90
- TXT/DOCX numeric recall >= 0.98
- MD service token recall >= 0.90
- table-row coverage baseline produced

### Step 2. Add PDF layout metadata extraction

- Extend `backend/app/pipelines/parser.py` to collect block/line/span/word coordinates.
- Use `page.get_text("dict")`, `page.get_text("rawdict")`, or `page.get_text("words")`.
- Detect physical-page columns/logical pages.

Metadata:

- page number
- logical page number
- column index
- block/line index
- bbox
- font size
- text

### Step 3. Add table detection and Markdown/table-row rendering

- Use PyMuPDF drawing/line information where possible.
- Use text-alignment fallback when line graphics are absent.
- Emit table candidates as structured rows and Markdown/plain row text.

Acceptance:

- MD table row coverage >= 0.70
- table-row queries for item names/equipment/processes return matching chunks
- numeric cell recall >= 0.95

### Step 4. Improve basis chunking

Add chunk types:

- `paragraph`
- `table`
- `table_row`
- `table_context`

Metadata:

- `chunk_type`
- page/logical page
- section title
- table id
- row index
- column headers
- source bbox

### Step 5. Improve RAG index and citations

- Keep citation id format stable.
- Add table metadata to result payloads.
- Weight item-name/equipment/numeric tokens for table-row chunks.

Acceptance:

- `/api/basis-search` can return table-row citation candidates.
- result metadata includes table id, row index, and column headers.
- MD table query coverage >= 0.80.

### Step 6. Add tests

- parser layout metadata tests
- table extraction tests
- reference comparison tests
- real basis RAG table-row query tests

## Current Conclusion

The current PDF extraction is good enough for body text and numeric recall. The next important improvement is not more plain text extraction; it is table-aware extraction, chunking, indexing, and citation metadata.

## Additional Check: PDF -> Markdown Regeneration

We regenerated Markdown from the actual PDF and compared it directly against the user-provided MD reference.

Result:

- physical pages: 489
- regenerated logical pages: 977
- reference logical pages: 977
- regenerated Markdown characters: 1,635,197
- reference MD characters: 1,731,919
- regenerated tables: 3,034
- reference MD tables: 1,928
- regenerated table rows: 13,390
- reference MD table rows: 11,351
- regenerated token recall in reference: 0.9303
- reference token recall in regenerated: 0.7931
- regenerated char 5-gram recall in reference: 0.8665
- reference char 5-gram recall in regenerated: 0.8171
- regenerated table row coverage in reference: 0.7060
- reference table row coverage in regenerated: 0.7644

Interpretation:

- The left/right logical-page split matches the reference MD page count.
- Markdown regeneration aligns better with the MD reference than plain text extraction.
- Table structure is partially recovered, but PyMuPDF over-detects short title/notice fragments as tables.

Next improvements:

1. add table candidate quality filters
2. merge adjacent table bboxes
3. remove short title/notice false tables
4. create table-row chunks after filtering
5. lock table-aware comparison thresholds
