# 실제 기준문서 RAG 및 테이블 추출 QA 계획

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

이 문서는 사용자가 제공한 실제 기준문서 PDF를 로컬 fixture로 등록하고 RAG/표 추출 품질을 검증하기 위한 계획과 실행 기록입니다.
초기 분석 일부는 PyMuPDF 기준이지만, 현재 서비스 기본 PDF reader는 OpenDataLoader 우선 `auto` 모드입니다.

현재 기준:
- 실제 기준문서 PDF 원본은 Git에 커밋하지 않고 로컬 fixture/manifest 정책을 유지합니다.
- OpenDataLoader QA는 489쪽 기준문서 전체 변환, `auto` 변환, fallback simulation을 포함합니다.
- 기준문서 검색은 JSON basis index를 사용하며, 인덱스 손상/불일치 상태에서는 검색과 citation 사용을 차단합니다.
- DOCX 비교/분석은 문단과 표 cell 텍스트를 함께 사용합니다.
- 최신 PDF/RAG 보강 후 전체 backend 테스트 기준선은 `134 passed`, `8 skipped`입니다.
- MuPDF/PyMuPDF의 Swig 관련 warning은 알려진 내부 경고로 기록하되, 테스트 실패 조건은 아닙니다.

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

## 상세 구현계획

## 1단계. 로컬 샘플 폴더와 Git 관리 정책

수정 파일:

```text
.gitignore
backend/tests/real-basis-document-samples/README.md
backend/tests/real-basis-document-samples/manifest.example.json
```

작업 내용:
1. `backend/tests/real-basis-document-samples/` 폴더를 생성한다.
2. 폴더 안에 샘플 사용법을 설명하는 `README.md`를 만든다.
3. `.gitignore`에 다음 항목을 추가한다.

```gitignore
backend/tests/real-basis-document-samples/*.pdf
backend/tests/real-basis-document-samples/manifest.json
backend/tests/real-basis-document-samples/extraction-baseline.json
backend/tests/real-basis-document-samples/extraction-report.json
backend/tests/real-basis-document-samples/tmp/
backend/tests/real-basis-document-samples/storage/
```

4. `manifest.example.json`에는 실제 파일 없이 schema 예시만 둔다.

예상 manifest schema:

```json
{
  "schema_version": "real_basis_document_sample_v1",
  "registered_at": "2026-06-05T00:00:00+09:00",
  "source_path": "C:/Users/HOONJAE/Documents/카카오톡 받은 파일/...",
  "saved_path": "backend/tests/real-basis-document-samples/...",
  "file_name": "전체합본_(제2025-116호)...pdf",
  "file_size_bytes": 5360737,
  "sha256": "sha256:...",
  "document": {
    "title": "중소기업자간 경쟁제품 직접생산 확인기준",
    "category": "direct_production",
    "document_version": "2025-116_2025-11-19",
    "issuing_agency": "중소벤처기업부",
    "effective_date": "2025-11-19"
  }
}
```

완료 기준:
- 빈 폴더라도 Git에 남길 수 있도록 `README.md`가 존재한다.
- 원문 PDF와 분석 산출물은 Git stage 대상에서 제외된다.
- manifest schema를 보고 다른 PC 사용자가 같은 파일을 등록할 수 있다.

## 2단계. 샘플 등록 스크립트 구현

신규 파일:

```text
scripts/register-real-basis-document-sample.py
```

명령 예시:

```powershell
py -3.13 scripts/register-real-basis-document-sample.py `
  --source "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf"
```

옵션:

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--source` | 필수 | 원본 PDF 절대경로 |
| `--output-dir` | `backend/tests/real-basis-document-samples` | 복사 대상 폴더 |
| `--title` | `중소기업자간 경쟁제품 직접생산 확인기준` | 기준문서 제목 |
| `--category` | `direct_production` | 기준문서 카테고리 |
| `--document-version` | `2025-116_2025-11-19` | 기준문서 버전 |
| `--issuing-agency` | `중소벤처기업부` | 발행기관 |
| `--effective-date` | `2025-11-19` | 시행/고시일 |
| `--overwrite` | false | 기존 파일 덮어쓰기 허용 |

구현 로직:
1. `source`가 존재하는지 확인한다.
2. 확장자가 `.pdf`인지 확인한다.
3. 출력 폴더를 만든다.
4. 파일명을 안전하게 보존해 복사한다.
5. sha256을 계산한다.
6. `manifest.json`을 UTF-8로 저장한다.
7. 결과를 stdout에 JSON으로 출력한다.

예상 stdout:

```json
{
  "status": "registered",
  "saved_path": "backend/tests/real-basis-document-samples/전체합본_....pdf",
  "sha256": "sha256:...",
  "file_size_bytes": 5360737,
  "manifest_path": "backend/tests/real-basis-document-samples/manifest.json"
}
```

테스트/검증:
- source가 없으면 exit code 1
- PDF가 아니면 exit code 1
- 정상 등록 시 manifest 생성
- `--overwrite` 없을 때 기존 파일이 있으면 실패

## 3단계. PDF 추출 사전 분석 스크립트 구현

신규 파일:

```text
scripts/analyze-real-basis-document-pdf.py
```

명령 예시:

```powershell
py -3.13 scripts/analyze-real-basis-document-pdf.py
```

옵션:

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--manifest` | `backend/tests/real-basis-document-samples/manifest.json` | 샘플 manifest |
| `--output` | `backend/tests/real-basis-document-samples/extraction-report.json` | 분석 리포트 |
| `--baseline-output` | 비어 있음 | baseline 생성 시 저장 경로 |
| `--sample-lines` | `30` | table-like line 샘플 수 |
| `--low-text-threshold` | `80` | 저텍스트 페이지 기준 |

구현 로직:
1. manifest를 읽어 PDF 경로를 확인한다.
2. `fitz.open()`으로 PDF를 연다.
3. 페이지별로 다음을 추출한다.
   - `page.get_text("text")`
   - `page.get_text("blocks")`
   - `page.get_text("dict")` 기반 line/span 수
4. 정규화 텍스트를 만든다.
5. table-like line 후보를 찾는다.
6. 필수 키워드 coverage를 계산한다.
7. 리포트를 JSON으로 저장한다.

table-like line 휴리스틱:
- 한 줄에 2개 이상 연속 공백 또는 tab 유사 간격이 있다.
- 숫자/코드/품명처럼 짧은 셀이 반복된다.
- `세부품명`, `생산설비`, `검사설비`, `생산공정`, `직접생산` 같은 표 헤더 후보가 있다.
- 한 페이지에 table-like line이 일정 수 이상이면 table-like page로 본다.

예상 report schema:

```json
{
  "schema_version": "real_basis_extraction_report_v1",
  "pdf": {
    "file_name": "...pdf",
    "sha256": "sha256:...",
    "file_size_bytes": 5360737
  },
  "summary": {
    "page_count": 0,
    "text_char_count": 0,
    "normalized_text_char_count": 0,
    "pages_with_text_count": 0,
    "low_text_pages": [],
    "block_count": 0,
    "line_count": 0,
    "table_like_line_count": 0,
    "table_like_page_count": 0
  },
  "required_terms": {
    "직접생산": {"found": true, "count": 0, "pages": []}
  },
  "table_like_samples": [
    {
      "page": 1,
      "line": "세부품명 ... 생산설비 ... 검사설비",
      "score": 0.0,
      "matched_reasons": ["multi_spacing", "header_terms"]
    }
  ],
  "warnings": []
}
```

성공 기준:
- `page_count > 0`
- `normalized_text_char_count >= 10000`
- 필수 키워드 중 최소 6개 이상 발견
- table-like page 1개 이상 발견
- 저텍스트 페이지가 전체의 20% 이하이면 통과로 본다.

실패 시 분류:
- `pdf_open_failed`
- `low_text_extraction`
- `required_terms_missing`
- `table_like_lines_missing`
- `unexpected_parser_warning`

## 4단계. 실제 기준문서 RAG 테스트 fixture 구성

신규 파일:

```text
backend/tests/test_real_basis_document_rag.py
```

테스트 실행 정책:
- 샘플 PDF가 없으면 `pytest.skip()`
- `RUN_REAL_BASIS_RAG_TESTS=1`이 설정되면 더 엄격한 threshold 테스트까지 실행
- 기본 테스트에서는 시간이 오래 걸리지 않도록 핵심 테스트만 실행

테스트 환경:
- 기존 `backend/tests/test_api_flows.py`와 동일하게 임시 `SQLITE_PATH`, `STORAGE_ROOT`를 사용한다.
- OCR은 기본적으로 `OCR_ENGINE=noop`로 두어 PyMuPDF 추출 중심으로 검증한다.
- Gemini/OpenAI/Nara 키는 필요 없다.

공통 helper:

```python
def real_basis_sample_manifest() -> dict: ...
def real_basis_pdf_path() -> Path: ...
def upload_real_basis_document(client, manifest) -> dict: ...
def assert_basis_index_healthy(client) -> dict: ...
def search_basis(client, query: str, top_k: int = 5) -> dict: ...
```

## 5단계. RAG 업로드/인덱싱 테스트 케이스

테스트 이름:

```text
test_real_basis_document_upload_extracts_chunks_and_indexes
```

검증 절차:
1. manifest에서 PDF 경로를 읽는다.
2. `/api/basis-documents`에 PDF를 업로드한다.
3. 응답에서 다음을 확인한다.
   - `processing_status == completed`
   - `parse_status == completed`
   - `chunk_status == completed`
   - `index_status == completed`
   - `chunk_count > 0`
   - `vector_count == chunk_count`
4. `/api/basis-documents/{id}/chunks`로 chunk 목록을 조회한다.
5. chunk text에 핵심 키워드가 존재하는지 확인한다.
6. `/api/basis-index/status`가 valid인지 확인한다.

성공 기준:
- chunk 10개 이상
- vector_count와 chunk_count 일치
- chunk 중 하나 이상에 `직접생산` 포함
- chunk 중 하나 이상에 `세부품명` 또는 `생산설비` 포함

## 6단계. RAG 검색 테스트 케이스

테스트 이름:

```text
test_real_basis_document_search_returns_direct_production_citations
```

질의셋:

```python
RAG_QUERIES = [
    {"query": "직접생산 확인기준", "required_terms": ["직접생산", "확인기준"]},
    {"query": "중소기업자간 경쟁제품", "required_terms": ["중소기업자간", "경쟁제품"]},
    {"query": "세부품명 직접생산", "required_terms": ["세부품명", "직접생산"]},
    {"query": "생산설비 검사설비", "required_terms": ["생산설비", "검사설비"]},
    {"query": "공장등록 직접생산", "required_terms": ["공장등록", "직접생산"]},
]
```

검증 절차:
1. 기준문서를 업로드하고 인덱싱한다.
2. 각 질의로 `/api/basis-search`를 호출한다.
3. 각 응답에서 다음을 확인한다.
   - HTTP 200
   - `index_source == json_basis_index`
   - `result_count > 0`
   - 첫 결과에 `citation_candidate_id` 존재
   - 첫 결과의 document id가 업로드한 기준문서 id와 일치
4. top chunk text에 required_terms 중 하나 이상이 포함되는지 확인한다.

성공 기준:
- 질의 coverage 80% 이상
- 핵심 질의 `직접생산 확인기준`, `중소기업자간 경쟁제품`은 반드시 성공

## 7단계. 검색 평가 API 테스트 케이스

테스트 이름:

```text
test_real_basis_document_retrieval_evaluation_records_coverage
```

검증 절차:
1. 검색 테스트에서 얻은 citation id 일부를 expected citation으로 사용한다.
2. `/api/basis-retrieval-evaluations`에 query set을 저장한다.
3. 응답에서 다음을 확인한다.
   - HTTP 201
   - `result.index_source == json_basis_index`
   - `query_count >= 3`
   - `citation_coverage > 0`
   - `average_top_score > 0`

성공 기준:
- 검색 평가가 저장된다.
- 운영 QA 리포트에서 source가 JSON 인덱스로 표시된다.

## 8단계. 테이블 추출/RAG 테스트 케이스

테스트 이름:

```text
test_real_basis_document_table_like_content_is_searchable
```

입력:
- `extraction-report.json`의 `table_like_samples`
- 또는 `extraction-baseline.json`에 고정한 대표 table query

baseline schema:

```json
{
  "schema_version": "real_basis_extraction_baseline_v1",
  "table_queries": [
    {
      "name": "생산설비_검사설비_행",
      "query": "생산설비 검사설비 직접생산",
      "required_terms": ["생산설비", "검사설비"],
      "min_required_terms_in_chunk": 2
    }
  ]
}
```

검증 절차:
1. `extraction-baseline.json`이 있으면 baseline query를 사용한다.
2. 없으면 사전 분석 리포트의 table-like sample에서 query 후보를 자동 생성한다.
3. 각 table query로 `/api/basis-search` 호출.
4. top chunk에서 required_terms 동시 출현 수를 계산한다.
5. coverage를 계산한다.

성공 기준:
- table query 5개 이상일 때 80% 이상 성공
- table query가 5개 미만이면 테스트는 경고와 함께 soft pass 또는 skip
- `직접생산`, `생산설비`, `검사설비` 조합 질의는 최소 1개 이상 성공

실패 시 자동 수정계획 후보:
- 테이블 line 정규화 강화
- chunk boundary에서 table-like line 보호
- chunk metadata에 `table_like=true`, `page`, `line_index` 추가
- 검색 tokenization에 숫자/품명 코드 보존 규칙 추가

## 9단계. 문서/README 보강

수정 후보:

```text
backend/tests/real-basis-document-samples/README.md
README.md
docs/work-log.md
```

보강 내용:
- 실제 기준문서 샘플 등록 방법
- PDF 원문은 Git에 넣지 않는 이유
- RAG 실제 기준문서 테스트 실행 방법
- 테이블 추출 QA 리포트 보는 방법

README 추가 후보:

```powershell
py -3.13 scripts/register-real-basis-document-sample.py --source "<PDF 경로>"
py -3.13 scripts/analyze-real-basis-document-pdf.py
$env:RUN_REAL_BASIS_RAG_TESTS="1"
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
```

## 10단계. 실행 및 검증 명령

기본 검증:

```powershell
py -3.13 scripts/register-real-basis-document-sample.py --source "<PDF 경로>"
py -3.13 scripts/analyze-real-basis-document-pdf.py
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
py -3.13 -m pytest backend/tests -q
py -3.13 scripts/check-encoding.py
```

엄격 검증:

```powershell
$env:RUN_REAL_BASIS_RAG_TESTS="1"
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
Remove-Item Env:\RUN_REAL_BASIS_RAG_TESTS
```

프론트 확인이 필요하면:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
```

브라우저에서 확인:

```text
http://127.0.0.1:5199/basis-documents
http://127.0.0.1:5199/basis-retrieval-evaluations
```

## 11단계. 구현 완료 체크리스트

- [x] `.gitignore`에 실제 기준문서 샘플 산출물 제외 규칙 추가
- [x] `backend/tests/real-basis-document-samples/README.md` 작성
- [x] `manifest.example.json` 작성
- [x] `scripts/register-real-basis-document-sample.py` 작성
- [x] 제공 PDF를 샘플 폴더로 복사
- [x] `manifest.json` 생성
- [x] `scripts/analyze-real-basis-document-pdf.py` 작성
- [x] `extraction-report.json` 생성
- [x] table-like page/line 확인
- [x] `extraction-baseline.json` 생성
- [x] `backend/tests/test_real_basis_document_rag.py` 작성
- [x] 업로드/청킹/인덱싱 테스트 통과
- [x] RAG 검색 질의 테스트 통과
- [x] 검색 평가 API 테스트 통과
- [x] 테이블 기반 검색 테스트 통과
- [x] 실패 발견 시 수정계획 검토
- [x] 필요한 추출/청킹 수정 없음 확인
- [x] targeted pytest 통과
- [x] 전체 backend pytest 통과
- [x] 인코딩 검사 통과
- [x] work-log 기록

## 구현 결과

구현 완료 파일:

- `.gitignore`
- `backend/tests/real-basis-document-samples/README.md`
- `backend/tests/real-basis-document-samples/manifest.example.json`
- `scripts/register-real-basis-document-sample.py`
- `scripts/analyze-real-basis-document-pdf.py`
- `backend/tests/test_real_basis_document_rag.py`

로컬 ignored 산출물:

- `backend/tests/real-basis-document-samples/manifest.json`
- `backend/tests/real-basis-document-samples/extraction-report.json`
- `backend/tests/real-basis-document-samples/extraction-baseline.json`
- `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`

실제 기준문서 추출 분석 결과:

- PDF 크기: 5,360,737 bytes
- PDF 페이지 수: 489
- 추출 문자 수: 702,598
- page coverage: 1.0
- 청크 수: 495
- table-like line 후보 수: 80
- 필수 키워드 coverage: `직접생산`, `확인기준`, `중소기업자간`, `경쟁제품`, `세부품명`, `생산시설`, `검사설비` 모두 확인

테스트 결과:

- `py -3.13 -m py_compile scripts/register-real-basis-document-sample.py scripts/analyze-real-basis-document-pdf.py backend/tests/test_real_basis_document_rag.py`: 통과
- `py -3.13 scripts/analyze-real-basis-document-pdf.py --strict`: 통과
- `$env:RUN_REAL_BASIS_RAG_TESTS='1'; py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q`: `5 passed, 10 subtests passed`
- `py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q`: `5 skipped`
- `py -3.13 -m pytest backend/tests -q`: `102 passed, 8 skipped`
- `py -3.13 scripts/check-encoding.py`: 통과

외부 TXT 기준 텍스트 비교 결과:

- 기준 TXT: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).txt`
- 비교 스크립트: `scripts/compare-real-basis-document-txt.py`
- 리포트: `backend/tests/real-basis-document-samples/text-comparison-report.json`
- TXT 인코딩: `utf-8-sig`
- 서비스 파싱 텍스트: 702,598자
- TXT 기준 텍스트: 728,596자
- compact 기준 문자 수: 서비스 554,921자, TXT 554,696자
- service token multiset recall in TXT: 0.9001
- TXT token multiset recall in service: 0.7725
- service char 5-gram recall in TXT: 0.8103
- TXT char 5-gram recall in service: 0.8107
- service line coverage in TXT: 0.9948
- TXT line coverage in service: 0.9495
- numeric recall: service -> TXT 0.9880, TXT -> service 0.9970
- 필수 키워드 coverage: `직접생산`, `확인기준`, `중소기업자간`, `경쟁제품`, `세부품명`, `생산시설`, `검사설비` 모두 양쪽에서 확인
- strict 비교 기준 통과

외부 DOCX 기준 텍스트 비교 결과:

- 기준 DOCX: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx`
- 비교 스크립트: `scripts/compare-real-basis-document-txt.py`
- 리포트: `backend/tests/real-basis-document-samples/docx-comparison-report.json`
- DOCX 기준 추출 방식: `docx-package-xml-wt`
- DOCX 문단 수: 3,576
- DOCX 표 수: 744
- DOCX 표 셀 수: 15,523
- `python-docx` 문단/표 방식 추출 문자 수: 387,786
- DOCX XML 텍스트 추출 문자 수: 720,588
- 서비스 파싱 텍스트: 702,598자
- compact 기준 문자 수: 서비스 554,921자, DOCX 550,700자
- service token multiset recall in DOCX: 0.9002
- DOCX token multiset recall in service: 0.7721
- service char 5-gram recall in DOCX: 0.8425
- DOCX char 5-gram recall in service: 0.8489
- service line coverage in DOCX: 0.9270
- DOCX line coverage in service: 0.8992
- numeric recall: service -> DOCX 0.9905, DOCX -> service 0.9971
- strict 비교 기준 통과
- 회귀 테스트 코드: `backend/tests/test_real_basis_reference_compare.py`
- 회귀 테스트 결과: `3 passed`
- 당시 전체 backend pytest 결과: `105 passed, 8 skipped`
- 현재 최신 전체 backend 기준선: `134 passed`, `8 skipped`
- 비고: 이 문서는 `python-docx`의 문단/표 셀 방식만 사용하면 기준 텍스트가 약 38.8만 자에 그쳐 비교가 왜곡되므로, DOCX 패키지 XML의 `w:t` 텍스트를 직접 읽는 방식을 사용한다.

외부 MD 기준 텍스트 비교 결과:

- 기준 MD: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`
- 비교 스크립트: `scripts/compare-real-basis-document-txt.py`
- 리포트: `backend/tests/real-basis-document-samples/md-comparison-report.json`
- 서비스 파싱 텍스트: 702,598자
- MD 기준 텍스트: 1,719,849자
- compact 기준 문자 수: 서비스 554,921자, MD 1,314,511자
- service token multiset recall in MD: 0.9073
- MD token multiset recall in service: 0.3541
- service char 5-gram recall in MD: 0.9358
- MD char 5-gram recall in service: 0.3951
- service line coverage in MD: 0.9955
- MD line coverage in service: 0.5200
- numeric recall: service -> MD 0.9979, MD -> service 0.3625
- strict 비교 기준 통과
- 비고: MD 기준 파일은 Markdown 표/설명/논리페이지/표 변환 결과를 포함해 TXT/DOCX보다 훨씬 길다. 따라서 MD 기준은 본문 텍스트 비교보다 표 구조 보존 여부를 판단하는 기준으로 사용해야 한다.

추출 로직 보완 계획:

- `docs/basis-document-extraction-improvement-plan.md`

비고:

- 실제 PDF와 `manifest.json`, 추출 리포트 산출물은 `.gitignore` 대상이므로 Git에 커밋하지 않는다.
- 이번 구현에서는 파서/청킹 알고리즘 자체 변경 없이 현재 파이프라인의 실제 기준문서 처리 가능성을 검증했다.
- MuPDF/PyMuPDF의 `SwigPyPacked`, `SwigPyObject`, `swigvarlink` 관련 DeprecationWarning이 pytest에서 출력되지만 테스트 실패는 아니다.

## Questions for Product Owner
- 원문 PDF를 Git에 커밋하지 않는 로컬 샘플 정책으로 진행해도 되는지 확인이 필요합니다. 현재 계획은 원문 PDF를 `.gitignore` 대상으로 두고 로컬에서만 사용하는 방식입니다.

---

# AI / Engineering Version (English)

## Current Code Update
Last updated: 2026-06-07

This document records the plan and execution history for the user-provided real basis PDF fixture and RAG/table extraction QA.
Some initial analysis used PyMuPDF, but the current default PDF reader is OpenDataLoader-first `auto` mode.

Current baseline:
- The real basis PDF stays out of Git and is managed as a local fixture/manifest.
- OpenDataLoader QA covers full 489-page conversion, `auto` conversion, and fallback simulation.
- Basis retrieval uses the JSON basis index and blocks search/citation usage when the index is missing/corrupt/inconsistent.
- DOCX comparison/parsing includes paragraphs and table cells.
- Latest PDF/RAG backend baseline: `134 passed`, `8 skipped`.
- MuPDF/PyMuPDF Swig warnings remain known internal warnings, not test failures.

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

## Detailed Implementation Plan

## Step 1. Fixture Directory And Git Policy

Files:

```text
.gitignore
backend/tests/real-basis-document-samples/README.md
backend/tests/real-basis-document-samples/manifest.example.json
```

Actions:
1. Create `backend/tests/real-basis-document-samples/`.
2. Add a README explaining sample registration and local-only artifacts.
3. Ignore raw PDFs and generated reports.
4. Commit only docs, scripts, tests, and manifest examples by default.

Ignore rules:

```gitignore
backend/tests/real-basis-document-samples/*.pdf
backend/tests/real-basis-document-samples/manifest.json
backend/tests/real-basis-document-samples/extraction-baseline.json
backend/tests/real-basis-document-samples/extraction-report.json
backend/tests/real-basis-document-samples/tmp/
backend/tests/real-basis-document-samples/storage/
```

## Step 2. Sample Registration Script

File:

```text
scripts/register-real-basis-document-sample.py
```

Inputs:
- `--source`
- `--output-dir`
- `--title`
- `--category`
- `--document-version`
- `--issuing-agency`
- `--effective-date`
- `--overwrite`

Responsibilities:
- validate source existence and `.pdf` suffix
- create output directory
- copy the PDF
- compute sha256
- write `manifest.json`
- print a JSON summary

## Step 3. Extraction Analysis Script

File:

```text
scripts/analyze-real-basis-document-pdf.py
```

Inputs:
- `--manifest`
- `--output`
- `--baseline-output`
- `--sample-lines`
- `--low-text-threshold`

Responsibilities:
- open the PDF with PyMuPDF
- extract page text, blocks, lines, spans
- normalize text
- detect table-like lines/pages
- calculate required-term coverage
- write `extraction-report.json`

Success thresholds:
- `page_count > 0`
- `normalized_text_char_count >= 10000`
- at least 6 required terms found
- at least 1 table-like page found
- low-text pages are no more than 20% of total pages

## Step 4. Real Basis RAG Test Module

File:

```text
backend/tests/test_real_basis_document_rag.py
```

Execution policy:
- skip when the fixture PDF is missing
- use temporary SQLite/storage roots
- default OCR engine should be `noop`
- API keys are not required
- `RUN_REAL_BASIS_RAG_TESTS=1` enables stricter thresholds

Helpers:
- `real_basis_sample_manifest()`
- `real_basis_pdf_path()`
- `upload_real_basis_document(client, manifest)`
- `assert_basis_index_healthy(client)`
- `search_basis(client, query, top_k=5)`

## Step 5. Upload / Chunk / Index Test

Test:

```text
test_real_basis_document_upload_extracts_chunks_and_indexes
```

Validate:
- upload through `/api/basis-documents`
- `processing_status == completed`
- `parse_status == completed`
- `chunk_status == completed`
- `index_status == completed`
- `chunk_count > 0`
- `vector_count == chunk_count`
- JSON basis index is valid

Success thresholds:
- at least 10 chunks
- at least one chunk includes `직접생산`
- at least one chunk includes `세부품명` or `생산설비`

## Step 6. RAG Search Test

Test:

```text
test_real_basis_document_search_returns_direct_production_citations
```

Queries:
- `직접생산 확인기준`
- `중소기업자간 경쟁제품`
- `세부품명 직접생산`
- `생산설비 검사설비`
- `공장등록 직접생산`

Validate:
- HTTP 200
- `index_source == json_basis_index`
- `result_count > 0`
- citation candidate id exists
- result document id matches the uploaded basis document
- top chunk contains at least one required term

Success threshold:
- query coverage at least 80%
- direct production and competitive products queries must pass

## Step 7. Retrieval Evaluation API Test

Test:

```text
test_real_basis_document_retrieval_evaluation_records_coverage
```

Validate:
- `/api/basis-retrieval-evaluations` stores the query set
- `result.index_source == json_basis_index`
- `query_count >= 3`
- `citation_coverage > 0`
- `average_top_score > 0`

## Step 8. Table-Aware RAG Test

Test:

```text
test_real_basis_document_table_like_content_is_searchable
```

Inputs:
- `extraction-report.json`
- optionally `extraction-baseline.json`

Validate:
- table-oriented queries return results
- top chunks are non-empty and not garbled
- required table terms co-occur in the same chunk

Success threshold:
- at least 5 table queries when available
- at least 80% coverage
- at least one query involving `직접생산`, `생산설비`, and `검사설비` passes

## Step 9. Documentation

Update:

```text
backend/tests/real-basis-document-samples/README.md
README.md
docs/work-log.md
```

Document:
- how to register the PDF
- why the raw PDF is ignored
- how to run real-basis RAG tests
- how to read extraction reports

## Step 10. Verification Commands

Basic:

```powershell
py -3.13 scripts/register-real-basis-document-sample.py --source "<PDF path>"
py -3.13 scripts/analyze-real-basis-document-pdf.py
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
py -3.13 -m pytest backend/tests -q
py -3.13 scripts/check-encoding.py
```

Strict:

```powershell
$env:RUN_REAL_BASIS_RAG_TESTS="1"
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
Remove-Item Env:\RUN_REAL_BASIS_RAG_TESTS
```

Manual frontend check:

```text
http://127.0.0.1:5199/basis-documents
http://127.0.0.1:5199/basis-retrieval-evaluations
```

## Completion Checklist

- [x] gitignore rules added
- [x] sample README added
- [x] manifest example added
- [x] registration script added
- [x] PDF copied locally
- [x] manifest generated
- [x] extraction analysis script added
- [x] extraction report generated
- [x] table-like pages/lines reviewed
- [x] extraction baseline generated
- [x] real-basis RAG pytest added
- [x] upload/chunk/index test passes
- [x] RAG query test passes
- [x] retrieval evaluation API test passes
- [x] table-oriented test passes
- [x] remediation plan considered for failures
- [x] extraction/chunking fixes not needed
- [x] targeted pytest passes
- [x] full backend pytest passes
- [x] encoding check passes
- [x] work-log updated

## Implementation Result

Implemented files:

- `.gitignore`
- `backend/tests/real-basis-document-samples/README.md`
- `backend/tests/real-basis-document-samples/manifest.example.json`
- `scripts/register-real-basis-document-sample.py`
- `scripts/analyze-real-basis-document-pdf.py`
- `backend/tests/test_real_basis_document_rag.py`

Local ignored artifacts:

- `backend/tests/real-basis-document-samples/manifest.json`
- `backend/tests/real-basis-document-samples/extraction-report.json`
- `backend/tests/real-basis-document-samples/extraction-baseline.json`
- copied real PDF sample

Extraction QA result:

- file size: 5,360,737 bytes
- page count: 489
- extracted characters: 702,598
- page coverage: 1.0
- chunk count: 495
- table-like line candidates: 80
- all required terms were found

Verification:

- Python compile check passed
- strict extraction analyzer passed
- opt-in real RAG pytest passed with 5 tests and 10 subtests
- default real RAG pytest skips 5 tests when the env var is absent
- full backend pytest passed with 102 passed and 8 skipped
- encoding check passed

External TXT comparison result:

- reference TXT: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).txt`
- comparison script: `scripts/compare-real-basis-document-txt.py`
- report: `backend/tests/real-basis-document-samples/text-comparison-report.json`
- TXT encoding: `utf-8-sig`
- service text: 702,598 characters
- reference TXT: 728,596 characters
- compact characters: service 554,921, TXT 554,696
- service token multiset recall in TXT: 0.9001
- TXT token multiset recall in service: 0.7725
- service char 5-gram recall in TXT: 0.8103
- TXT char 5-gram recall in service: 0.8107
- service line coverage in TXT: 0.9948
- TXT line coverage in service: 0.9495
- numeric recall: service -> TXT 0.9880, TXT -> service 0.9970
- all required terms were found in both texts
- strict comparison thresholds passed

External DOCX comparison result:

- reference DOCX: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx`
- comparison script: `scripts/compare-real-basis-document-txt.py`
- report: `backend/tests/real-basis-document-samples/docx-comparison-report.json`
- DOCX extraction engine: `docx-package-xml-wt`
- DOCX paragraphs: 3,576
- DOCX tables: 744
- DOCX table cells: 15,523
- `python-docx` paragraph/table extraction: 387,786 characters
- DOCX XML text extraction: 720,588 characters
- service text: 702,598 characters
- compact characters: service 554,921, DOCX 550,700
- service token multiset recall in DOCX: 0.9002
- DOCX token multiset recall in service: 0.7721
- service char 5-gram recall in DOCX: 0.8425
- DOCX char 5-gram recall in service: 0.8489
- service line coverage in DOCX: 0.9270
- DOCX line coverage in service: 0.8992
- numeric recall: service -> DOCX 0.9905, DOCX -> service 0.9971
- strict comparison thresholds passed
- regression test code: `backend/tests/test_real_basis_reference_compare.py`
- regression test result: `3 passed`
- historical full backend pytest result: `105 passed, 8 skipped`
- current full backend baseline: `134 passed`, `8 skipped`
- Note: plain `python-docx` paragraph/table-cell extraction produced only about 387k characters, so this comparison uses raw DOCX package XML `w:t` text.

External MD comparison result:

- reference MD: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`
- comparison script: `scripts/compare-real-basis-document-txt.py`
- report: `backend/tests/real-basis-document-samples/md-comparison-report.json`
- service text: 702,598 characters
- MD reference text: 1,719,849 characters
- compact characters: service 554,921, MD 1,314,511
- service token multiset recall in MD: 0.9073
- MD token multiset recall in service: 0.3541
- service char 5-gram recall in MD: 0.9358
- MD char 5-gram recall in service: 0.3951
- service line coverage in MD: 0.9955
- MD line coverage in service: 0.5200
- numeric recall: service -> MD 0.9979, MD -> service 0.3625
- strict comparison thresholds passed
- Note: the MD reference is much larger because it includes Markdown tables, notes, logical page handling, and table conversion outputs. Use it as a table-structure reference, not a plain body-text reference.

Extraction improvement plan:

- `docs/basis-document-extraction-improvement-plan.md`

Note:

- The raw PDF and generated QA outputs are local ignored artifacts.
- No parser or chunking algorithm change was required in this implementation.
- PyMuPDF emits Swig-related deprecation warnings during pytest, but they do not fail the test run.

## Questions for Product Owner
- Confirm that the raw PDF should remain a local ignored fixture rather than being committed to Git.
