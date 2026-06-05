# 실제 기준문서 RAG 및 테이블 추출 QA 계획

## 한국어 버전

## 문서 목적
사용자가 제공한 실제 기준문서 PDF를 로컬 기준문서 샘플로 보관하고, 현재 기준문서 파이프라인에서 다음 항목을 검증하기 위한 실행 계획입니다.

- PDF 원문 보관 위치와 관리 정책
- 기준문서 업로드/청킹/JSON 인덱싱/RAG 검색 동작
- 테이블이 많은 PDF에서 텍스트 추출이 충분히 정상적으로 되는지
- 추출 결과가 RAG 검색/citation 후보로 쓸 수 있는 품질인지

대상 파일:

```text
C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf
```

확인된 파일 상태:

- 파일 존재: 확인
- 파일 크기: 약 5.36MB
- 사용 목적: 기준문서 RAG 실제 샘플

## 핵심 원칙
1. 이 PDF는 일반 공고문이 아니라 재사용 기준문서 지식 자산으로 다룬다.
2. 원문 PDF는 테스트용 로컬 샘플 폴더에 보관하되, 기본적으로 Git에는 커밋하지 않는다.
3. Git에는 원문 PDF 대신 manifest, README, 테스트 코드, QA 리포트 형식만 남긴다.
4. 테스트는 파일이 없으면 skip하고, 파일이 있으면 실제 추출/RAG 품질을 검증한다.
5. 테이블 구조는 완전한 표 객체 복원이 아니더라도, 검색 가능한 핵심 행/열 의미가 보존되는지 우선 검증한다.

## 보관 폴더 계획

신규 폴더:

```text
backend/tests/real-basis-document-samples/
```

예상 구성:

```text
backend/tests/real-basis-document-samples/
  README.md
  manifest.json
  extraction-baseline.json
  extraction-report.json
  전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf
```

관리 정책:

- PDF 원문과 실행 결과 JSON은 로컬 산출물로 취급한다.
- `.gitignore`에 `backend/tests/real-basis-document-samples/*.pdf`, `extraction-report.json`, 임시 저장소를 추가한다.
- `README.md`와 `manifest.example.json` 또는 최소 manifest schema는 커밋 가능하게 둔다.
- 사용자가 명시적으로 원문 PDF 커밋을 원하면 별도로 확인 후 진행한다.

## 구현 단계 계획

## A. 샘플 등록 스크립트

목표:
- 사용자가 제공한 PDF를 정해진 샘플 폴더로 복사한다.
- 파일명, 원본 경로, 파일 크기, sha256, 등록일시를 manifest에 기록한다.

예상 파일:

```text
scripts/register-real-basis-document-sample.py
```

예상 실행:

```powershell
py -3.13 scripts/register-real-basis-document-sample.py `
  --source "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf"
```

완료 기준:
- 샘플 폴더가 생성된다.
- PDF가 샘플 폴더에 복사된다.
- manifest에 sha256과 원본 경로가 기록된다.

## B. PDF 추출 품질 사전 분석

목표:
- PyMuPDF 기반 현재 파서가 실제 기준문서에서 어느 정도 텍스트를 뽑는지 측정한다.
- 테이블이 많은 페이지에서 행/열 의미가 얼마나 보존되는지 확인한다.

예상 파일:

```text
scripts/analyze-real-basis-document-pdf.py
```

측정 항목:
- page_count
- text_char_count
- normalized_text_char_count
- pages_with_text_count
- empty_or_low_text_pages
- block_count
- line_count
- table_like_line_count
- table_like_page_count
- required_terms coverage
- extraction warnings

필수 키워드 후보:
- `중소기업자간 경쟁제품`
- `직접생산`
- `확인기준`
- `세부품명`
- `생산설비`
- `검사설비`
- `생산공정`
- `공장등록`
- `중소기업확인서`

테이블 추출 확인 방식:
- 다중 공백/짧은 셀 반복/숫자 코드/품명 패턴으로 table-like line 후보를 탐지한다.
- 표의 셀이 완전한 2차원 구조로 복원되지 않더라도, 한 행의 핵심 의미가 같은 page 또는 같은 chunk 안에 남는지 확인한다.
- 사전 분석 후 실제 문서에서 자주 나오는 표 헤더와 대표 행을 baseline으로 고정한다.

완료 기준:
- `extraction-report.json` 생성
- 추출 문자 수와 page coverage 확인
- 필수 키워드 coverage 확인
- 대표 table-like page와 line 후보 확인

## C. 기준문서 업로드/인덱싱 RAG 테스트

목표:
- 실제 PDF를 `/api/basis-documents` 경로로 업로드한다.
- 자동 추출 -> OCR fallback 판단 -> 정규화 -> 청킹 -> JSON 인덱싱 흐름을 검증한다.
- JSON basis index가 valid 상태인지 확인한다.

예상 테스트:

```text
backend/tests/test_real_basis_document_rag.py
```

테스트 실행 정책:
- 기본 전체 테스트에서는 샘플 파일이 없으면 skip한다.
- 실제 검증 시에는 샘플 파일이 있으면 실행한다.
- 필요하면 `RUN_REAL_BASIS_RAG_TESTS=1` 환경변수로 명시 실행하도록 구성한다.

검증 항목:
- 업로드 응답 status: `completed` 또는 OCR 환경에 따른 허용 상태
- `parse_status == completed`
- `chunk_count > 0`
- `vector_count == chunk_count`
- `GET /api/basis-index/status` 결과 valid
- `index_source == json_basis_index`

## D. RAG 검색 질의 테스트

목표:
- 실제 기준문서에서 검색해야 할 조달 기준 문구가 RAG 검색으로 citation 후보를 반환하는지 검증한다.

초기 질의 후보:

```text
직접생산 확인기준
중소기업자간 경쟁제품
세부품명 직접생산
생산설비 검사설비
공장등록 직접생산
중소기업확인서 직접생산 확인
```

검증 항목:
- 각 질의가 `result_count > 0`
- 각 결과가 `citation_candidate_id`를 포함
- 결과의 document metadata가 실제 기준문서와 연결됨
- top result chunk에 질의 핵심어 일부가 포함됨
- 검색 평가 API `/api/basis-retrieval-evaluations`에 query set 저장 가능

완료 기준:
- 검색 질의별 result coverage 기록
- 실패 질의는 원인 분류: 추출 실패, 청킹 문제, 토큰화 문제, 테이블 flatten 문제

## E. 테이블 기반 RAG 품질 테스트

목표:
- 표 안의 행/열 기준 문구가 일반 본문처럼 검색 가능한지 확인한다.

테스트 방식:
1. 사전 분석에서 table-like page를 찾는다.
2. 대표 표 헤더/행 후보를 5~10개 선정한다.
3. 선정한 문구를 기준으로 검색 질의를 만든다.
4. RAG 검색 결과의 chunk에 같은 page 또는 같은 table-like line 정보가 포함되는지 확인한다.

초기 품질 기준:
- table-like 질의 5개 이상
- result coverage 80% 이상
- top result chunk가 빈 텍스트/깨진 텍스트가 아니어야 함
- 대표 행의 핵심 셀 단어가 chunk 안에 2개 이상 함께 존재해야 함

만약 실패하면 보강 후보:
- PyMuPDF block/line/span 기반 테이블 보존 정규화 개선
- page별 table-like line을 별도 metadata로 저장
- chunking 시 table-like block은 중간에서 과도하게 자르지 않도록 보정
- 향후 `camelot`, `tabula`, `pdfplumber` 같은 표 추출 도구 도입 검토

## F. 산출물

예상 산출물:

```text
docs/real-basis-document-rag-test-plan.md
backend/tests/real-basis-document-samples/README.md
backend/tests/real-basis-document-samples/manifest.example.json
scripts/register-real-basis-document-sample.py
scripts/analyze-real-basis-document-pdf.py
backend/tests/test_real_basis_document_rag.py
```

로컬 산출물:

```text
backend/tests/real-basis-document-samples/manifest.json
backend/tests/real-basis-document-samples/extraction-baseline.json
backend/tests/real-basis-document-samples/extraction-report.json
backend/tests/real-basis-document-samples/*.pdf
```

## 실행 순서
1. 샘플 폴더 및 `.gitignore` 정책 추가
2. PDF 등록 스크립트 작성
3. 제공된 PDF를 샘플 폴더로 복사
4. PDF 사전 분석 스크립트 작성 및 실행
5. extraction baseline 작성
6. 실제 기준문서 RAG pytest 추가
7. RAG 검색 질의셋과 검색 평가 테스트 추가
8. 테이블 기반 질의 테스트 추가
9. 실패 항목이 있으면 추출/청킹 보강계획 작성 후 수정
10. 전체 백엔드 테스트, 관련 targeted 테스트, 인코딩 검사 실행
11. `docs/work-log.md`에 결과 기록

## 이번 계획에서 아직 하지 않는 것
- 원문 PDF 복사
- 테스트 코드 작성
- RAG 테스트 실행
- 테이블 추출 알고리즘 변경

사용자 요청이 “계획부터 작성”이므로, 위 항목은 다음 단계에서 진행합니다.

## Questions for Product Owner
- 원문 PDF를 Git에 커밋하지 않는 로컬 샘플 정책으로 진행해도 되는지 확인이 필요합니다. 현재 계획은 원문 PDF를 `.gitignore` 대상으로 두고 로컬에서만 사용하는 방식입니다.

---

# AI / Engineering Version (English)

## Purpose
This plan defines how to store the provided real basis-document PDF locally and verify the current basis-document RAG pipeline and table-heavy text extraction quality.

Target file:

```text
C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf
```

Confirmed:
- file exists
- size is about 5.36MB
- intended use is real basis-document RAG QA

## Principles
1. Treat this as a reusable basis knowledge asset, not as a Nara notice PDF.
2. Store the PDF under a local test fixture directory.
3. Do not commit the raw PDF by default.
4. Commit scripts, test code, manifest schema, and documentation.
5. Skip tests when the sample file is absent, and run real QA when the sample is present or explicitly enabled.
6. For tables, first verify searchable semantic preservation rather than full 2D table reconstruction.

## Storage Plan

Local fixture directory:

```text
backend/tests/real-basis-document-samples/
```

Expected local files:

```text
README.md
manifest.json
extraction-baseline.json
extraction-report.json
*.pdf
```

Git policy:
- ignore raw PDFs and generated reports
- commit README and manifest schema/example
- ask before committing the raw PDF

## Implementation Plan

## A. Sample Registration
Add:

```text
scripts/register-real-basis-document-sample.py
```

Responsibilities:
- create fixture directory
- copy source PDF
- compute sha256
- write manifest with source path, saved path, size, hash, and timestamp

## B. Extraction Preflight Analysis
Add:

```text
scripts/analyze-real-basis-document-pdf.py
```

Metrics:
- page_count
- text_char_count
- normalized_text_char_count
- pages_with_text_count
- low_text_pages
- block_count
- line_count
- table_like_line_count
- table_like_page_count
- required term coverage
- extraction warnings

Required term candidates:
- `중소기업자간 경쟁제품`
- `직접생산`
- `확인기준`
- `세부품명`
- `생산설비`
- `검사설비`
- `생산공정`
- `공장등록`
- `중소기업확인서`

## C. Basis Upload / Index RAG Test
Add:

```text
backend/tests/test_real_basis_document_rag.py
```

Validate:
- basis upload via `/api/basis-documents`
- parse completion
- chunk_count > 0
- vector_count == chunk_count
- JSON basis index is valid
- search source is `json_basis_index`

## D. RAG Search Query Test
Initial queries:

```text
직접생산 확인기준
중소기업자간 경쟁제품
세부품명 직접생산
생산설비 검사설비
공장등록 직접생산
중소기업확인서 직접생산 확인
```

Validate:
- each query returns at least one result
- each result has a citation candidate id
- top chunks contain relevant query terms
- retrieval evaluation API can store the query set

## E. Table-Aware RAG QA
Process:
1. Detect table-like pages during preflight.
2. Select 5 to 10 representative table headers/rows.
3. Build table-oriented RAG queries.
4. Verify result coverage and chunk semantic preservation.

Initial thresholds:
- at least 5 table-like queries
- at least 80% result coverage
- top chunks are non-empty and not garbled
- at least two key cell terms from the target row are present in the same chunk

Potential fixes if table QA fails:
- improve PyMuPDF block/line/span normalization
- preserve table-like lines as metadata
- adjust chunking to avoid splitting table-like blocks too aggressively
- evaluate dedicated table extraction libraries later

## Execution Order
1. Add fixture directory and gitignore policy.
2. Add sample registration script.
3. Copy the provided PDF.
4. Add and run extraction analysis script.
5. Create extraction baseline.
6. Add real-basis RAG pytest.
7. Add retrieval query evaluation.
8. Add table-oriented QA checks.
9. If failures appear, document and fix extraction/chunking issues.
10. Run targeted tests, backend tests, and encoding checks.
11. Record results in `docs/work-log.md`.

## Out Of Scope For This Step
No PDF copy, test implementation, RAG execution, or extraction algorithm change is performed in this planning step.

## Questions for Product Owner
- Confirm that the raw PDF should remain a local ignored fixture rather than being committed to Git.
