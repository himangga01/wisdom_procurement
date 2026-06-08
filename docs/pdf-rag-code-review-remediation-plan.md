# PDF 리더 및 기준문서 RAG 코드리뷰 수정계획

## 한국어 버전

## 문서 목적
이 문서는 2026-06-07 전체 코드리뷰에서 확인한 PDF 리더와 기준문서 RAG 관련 실제 버그에 대한 수정계획입니다.

사용자 요청에 따라 다음 항목은 즉시 수정계획에서 제외하고 기록만 남깁니다.

- P1 첨부 URL 검증 DNS rebinding/shared address 보강

이번 수정계획은 위 항목을 제외한 PDF 추출, 기준문서 재처리, JSON 인덱스, 승인 후보 citation, DOCX 표 추출, 청킹 overlap 문제를 대상으로 합니다.

## 구현 상태
- [x] P1-1 기준문서 원본 파일 없음 재처리 시 기존 RAG 인덱스 보존
- [x] P1-2 승인된 기준문구 후보와 판단 엔진의 JSON 인덱스 검증 일관성 보강
- [x] P2-1 PyMuPDF fallback 기준문서 page citation offset 보정
- [x] P2-2 OpenDataLoader JSON 중첩 텍스트 및 표 셀 누락 방지
- [x] P2-3 DOCX 표 텍스트 추출 보강
- [x] P3-1 긴 단일 문단 chunk overlap 적용 오류 수정
- [x] 관련 테스트 코드 추가 및 실행
- [x] 수정 후 PDF/RAG 중심 재코드리뷰 진행

최종 업데이트: 2026-06-07

검증 결과:
- `py -3.13 -m py_compile backend/app/pipelines/pdf_readers.py backend/app/pipelines/parser.py backend/app/pipelines/basis_document.py backend/app/main.py backend/app/services/basis_rule_candidates.py backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py backend/tests/test_api_flows.py`: 통과
- `py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py -q`: `22 passed`
- 신규 API 회귀 테스트 4개: `4 passed`
- `py -3.13 -m pytest backend/tests -q`: `134 passed`, `8 skipped`

## 이번 범위에서 제외하고 기록만 하는 이슈

### P1. 첨부 URL 검증 DNS rebinding/shared address 보강
상태:
- 이번 PDF/RAG 즉시 수정계획 및 구현 범위에서는 제외
- 2026-06-07 전체 코드리뷰 후 non-global/shared address 차단과 회귀 테스트는 별도로 반영
- DNS rebinding 완화는 후속 보안 보강 이슈로 기록 유지

문제 기록:
- 현재 URL 검증은 다운로드 전 hostname을 DNS 해석해 사설망/loopback 등을 차단한다.
- 하지만 검증 시점과 실제 연결 시점의 DNS 응답이 달라지는 DNS rebinding 가능성은 완전히 제거되지 않는다.
- `100.64.0.0/10` 같은 shared address 또는 non-global 대역은 현재 `ipaddress.is_global` 기준으로 차단한다.

후속 검토 방향:
- 검증된 IP로 직접 연결하거나 custom resolver/connection 정책 도입
- redirect마다 동일 정책 재검증 유지
- DNS rebinding 완화 전략과 관련 통합 테스트 추가

## 즉시 수정계획

## P1-1. 기준문서 원본 파일 없음 재처리 시 기존 RAG 인덱스 보존

### 문제
`process_basis_document()`는 저장된 원본 PDF 파일이 없으면 문서 상태만 `failed`로 바꾸고 반환합니다.

기존에 정상 인덱싱된 기준문서를 재처리하는 상황에서 원본 파일만 사라졌다면 다음 문제가 생깁니다.

- 기존 DB chunk와 JSON 인덱스 항목은 그대로 남는다.
- 문서 상태는 `failed`가 된다.
- JSON 인덱스 검증은 completed/indexed 문서의 chunk만 DB 기준으로 보기 때문에, JSON 인덱스가 `missing_from_db` 상태가 된다.
- 결과적으로 `/api/basis-search`가 전체적으로 409가 될 수 있다.

### 수정 방향
1. 원본 파일 없음 경로에서 기존 사용 가능한 RAG 산출물이 있는지 먼저 확인한다.
2. 기존 문서가 `completed/indexed`이고 indexed chunk가 있으면 기존 검색 지식은 보존한다.
3. 이 경우 `processing_status`와 `index_status`를 `failed`로 덮지 않고, 재처리 실패 사실만 metadata 또는 `error_message`에 기록한다.
4. 신규 업로드 또는 사용 가능한 기존 chunk가 없는 문서는 기존처럼 `failed` 처리한다.
5. JSON 인덱스 검증 결과가 기존 정상 상태를 유지해야 한다.

### 테스트 계획
- 기존 기준문서를 업로드해 indexed chunk와 JSON 인덱스를 만든다.
- 저장된 PDF 파일을 삭제한다.
- 재처리 API를 호출한다.
- 기존 chunk와 JSON 인덱스가 유지되는지 확인한다.
- `/api/basis-index/status`가 valid/can_search 상태인지 확인한다.
- `/api/basis-search`가 기존 citation 후보를 계속 반환하는지 확인한다.
- 신규 문서의 파일 없음 실패 경로는 여전히 failed가 되는지 확인한다.

### 완료 기준
- 기존 정상 기준문서는 원본 파일이 사라진 재처리 실패로 전체 RAG 검색을 망가뜨리지 않는다.
- 기존 citation 후보와 승인 후보가 무단 삭제되거나 invalid index를 만들지 않는다.

## P1-2. 승인된 기준문구 후보와 판단 엔진의 JSON 인덱스 검증 일관성 보강

### 문제
기준문구 후보 승인 검증과 판단 엔진의 승인 후보 우선 경로는 DB 문서/청크 상태만 확인합니다.

반면 기준문서 검색은 JSON 인덱스를 운영 검색 source로 사용하고, JSON 인덱스가 손상되면 409로 막습니다.

따라서 JSON 인덱스가 손상되었거나 DB와 불일치한 상태에서 다음 불일치가 생길 수 있습니다.

- `/api/basis-search`는 막힌다.
- 기준문구 후보 승인은 DB 상태만 보고 통과할 수 있다.
- 판단 엔진은 승인 후보 citation이 있으면 일반 검색 fallback을 생략해 손상된 인덱스 상태에서도 citation을 노출할 수 있다.

### 수정 방향
1. 기준문구 후보 승인 시 `validate_basis_index()`를 확인한다.
2. JSON 인덱스가 invalid면 승인을 막고 `basis_index_unavailable`, `rebuild_required: true` 성격의 응답을 반환한다.
3. 승인 대상 chunk의 `vector_id`가 JSON 인덱스에 존재하고, `basis_document_id`, `chunk_id`, `chunk_hash`가 DB와 일치하는지 확인한다.
4. 판단 엔진에서도 승인 후보 조회 전에 JSON 인덱스 검증을 수행한다.
5. JSON 인덱스가 invalid면 승인 후보와 일반 검색 citation을 모두 사용하지 않고, uncertainty note에 인덱스 오류를 남긴다.

### 테스트 계획
- JSON 인덱스 손상 상태에서 기준문구 후보 승인 API가 승인하지 않는지 확인한다.
- JSON 인덱스에서 승인 후보의 `vector_id`만 제거한 상태에서 승인이 거절되는지 확인한다.
- 이미 승인된 후보가 있는 상태에서 JSON 인덱스를 손상시키고 판단 실행 시 승인 후보 citation이 노출되지 않는지 확인한다.
- 인덱스 rebuild 후 승인/판단 흐름이 다시 정상화되는지 확인한다.

### 완료 기준
- 검색, 승인, 판단이 모두 같은 JSON 인덱스 건강 상태를 기준으로 동작한다.
- 손상된 인덱스 상태에서 citation이 우회 노출되지 않는다.

## P2-1. PyMuPDF fallback 기준문서 page citation offset 보정

### 문제
OpenDataLoader 경로는 page metadata에 `char_start`와 `char_end`를 저장합니다.

하지만 PyMuPDF fallback 경로는 페이지별 `char_count`만 저장하고, 전체 텍스트는 페이지 사이에 `\n\n`를 넣어 합칩니다.

`basis_page_ranges()`의 `char_count` fallback은 이 separator 길이를 반영하지 않아 2페이지 이후 citation page가 밀릴 수 있습니다.

### 수정 방향
1. `PyMuPdfPdfReader`도 OpenDataLoader처럼 page별 `char_start`, `char_end`를 기록한다.
2. `basis_page_ranges()`는 명시 offset이 있으면 이를 우선 사용하도록 기존 정책을 유지한다.
3. fallback을 위해 `char_count`만 있는 metadata 처리도 separator drift가 없도록 보완한다.

### 테스트 계획
- PyMuPDF 강제 모드로 3페이지 PDF를 추출한다.
- page metadata에 `char_start`, `char_end`가 있는지 확인한다.
- 기준문서 chunk의 `page_start`, `page_end`가 실제 텍스트 위치와 맞는지 확인한다.
- OpenDataLoader page offset 테스트는 기존대로 유지한다.

### 완료 기준
- OpenDataLoader와 PyMuPDF fallback 모두 page citation offset을 안정적으로 제공한다.

## P2-2. OpenDataLoader JSON 중첩 텍스트 및 표 셀 누락 방지

### 문제
OpenDataLoader JSON 변환에서 일부 node가 `content`를 비워 두고 children에 실제 텍스트를 담을 수 있습니다.

현재 `_collect_page_parts()`는 `paragraph`, `heading`, `caption`, `list item` node를 만나면 `content`가 비어 있어도 children을 보지 않고 return합니다.

또 `_cell_text()`도 dict에 `content` key가 있으면 내용이 비어도 children 탐색을 멈춥니다.

그 결과 본문 텍스트나 표 셀 텍스트가 누락될 수 있습니다.

### 수정 방향
1. paragraph/heading/list item/caption의 `content`가 비어 있으면 children을 계속 탐색한다.
2. `_cell_text()`는 빈 content일 때 children 탐색을 계속한다.
3. table row의 `cells` 값이 문자열인 경우도 안전하게 처리한다.
4. 기존 정상 JSON schema의 동작은 유지한다.

### 테스트 계획
- content가 비어 있고 kids에 paragraph text가 있는 본문 fixture를 추가한다.
- content가 비어 있고 kids에 paragraph text가 있는 table cell fixture를 추가한다.
- table row cells가 문자열 배열인 fixture를 추가한다.
- Markdown 표와 table metadata에 누락 없이 반영되는지 검증한다.

### 완료 기준
- OpenDataLoader JSON schema 변형에도 본문과 표 셀 텍스트가 누락되지 않는다.

## P2-3. DOCX 표 텍스트 추출 보강

### 문제
DOCX 추출은 `doc.paragraphs`만 읽고 `doc.tables`를 읽지 않습니다.

나라장터 DOCX 첨부나 사용자 업로드 DOCX가 표 중심이면 핵심 요구조건이 요약/분석 입력에서 빠질 수 있습니다.

### 수정 방향
1. `_extract_docx_text()`에서 문단 텍스트와 table cell 텍스트를 함께 추출한다.
2. 표는 행 단위로 읽고 cell 값을 구분 가능한 텍스트로 직렬화한다.
3. 기존 문단-only DOCX 테스트가 깨지지 않도록 정규화 정책을 유지한다.

### 테스트 계획
- 표가 포함된 DOCX fixture를 생성한다.
- 문단 텍스트와 표 cell 텍스트가 모두 추출되는지 확인한다.
- 빈 cell, 중복 공백, 줄바꿈 정규화가 안정적인지 확인한다.

### 완료 기준
- DOCX 표에 있는 요구조건/금액/면허/서류명이 분석 입력 텍스트에 포함된다.

## P3-1. 긴 단일 문단 chunk overlap 적용 오류 수정

### 문제
긴 단일 문단을 chunk로 쪼갤 때 `flush()`가 overlap을 만들지만, 다음 loop에서 `current_parts`를 새 slice로 덮어써 overlap이 실제 chunk에 반영되지 않습니다.

긴 조항이나 표가 문단 하나로 들어오는 경우 경계 문맥이 사라져 검색 recall과 citation 품질이 떨어질 수 있습니다.

### 수정 방향
1. 긴 문단 분할은 `flush()`의 side effect에 의존하지 않고 slice 단위 chunk를 직접 생성한다.
2. `BASIS_CHUNK_OVERLAP_CHARS`만큼 이전 slice 끝부분이 다음 slice에 포함되도록 보장한다.
3. `char_start`, `char_end`, page metadata가 실제 slice 위치와 일치하도록 유지한다.

### 테스트 계획
- `BASIS_MAX_CHUNK_CHARS`보다 긴 단일 문단을 입력한다.
- 연속 chunk 사이에 overlap 텍스트가 실제 포함되는지 확인한다.
- `char_start`가 overlap만큼 되감기는지 확인한다.
- page_start/page_end가 깨지지 않는지 확인한다.

### 완료 기준
- 긴 단일 문단에서도 chunk 경계 문맥이 보존된다.

## 권장 작업 순서
1. P1-1 기준문서 원본 파일 없음 재처리 보존
2. P1-2 승인 후보/판단 엔진 JSON 인덱스 검증
3. P2-1 PyMuPDF page offset 보정
4. P2-2 OpenDataLoader 중첩 텍스트/표 셀 보강
5. P2-3 DOCX 표 추출 보강
6. P3-1 긴 문단 overlap 수정
7. targeted backend tests 실행
8. PDF/RAG 중심 재코드리뷰

## 검증 명령 후보
```powershell
py -3.13 -m py_compile backend/app/pipelines/pdf_readers.py backend/app/pipelines/parser.py backend/app/pipelines/basis_document.py backend/app/main.py backend/app/services/basis_rule_candidates.py
py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py -q
py -3.13 -m pytest backend/tests/test_api_flows.py -q
py -3.13 scripts/check-encoding.py
git diff --check
```

## Questions for Product Owner
- 없음. DNS rebinding 보안 보강은 이번 즉시 수정 범위에서 제외하고 후속 이슈로만 기록한다.

---

# AI / Engineering Version (English)

## Purpose
This document records the remediation plan for concrete PDF reader and basis-document RAG bugs found in the 2026-06-07 code review.

Per the user request, the DNS rebinding/shared-address attachment URL issue is excluded from the immediate fix plan and recorded only as a follow-up security issue.

## Implementation Status
- [x] P1-1 Preserve existing RAG index when a reprocess fails because the stored basis PDF is missing
- [x] P1-2 Make approved rule-candidate citations and judgment use the same JSON index health contract as search
- [x] P2-1 Fix page citation offsets for PyMuPDF fallback basis PDFs
- [x] P2-2 Avoid dropping nested OpenDataLoader JSON text and table-cell content
- [x] P2-3 Extract DOCX table text
- [x] P3-1 Fix overlap for long single-paragraph basis chunks
- [x] Add and run targeted tests
- [x] Re-review PDF/RAG code after fixes

Final update: 2026-06-07

Verification:
- py_compile passed
- PDF/parser/table chunk targeted tests: `22 passed`
- New API regression tests: `4 passed`
- Full backend tests: `134 passed`, `8 skipped`

## Record-Only Excluded Issue

### P1. Attachment URL DNS Rebinding / Shared Address Hardening
Status:
- Excluded from this immediate PDF/RAG remediation plan
- As of 2026-06-07, non-global/shared address blocking and regression tests are implemented separately
- DNS rebinding mitigation remains a follow-up security hardening item

Follow-up direction:
- Avoid DNS rebinding by binding the validated address to the connection path or using a controlled resolver/connector
- Keep redirect validation
- Add DNS rebinding integration tests once the mitigation strategy is chosen

## Immediate Fix Plan

### P1-1. Missing Stored Basis PDF During Reprocess
Keep existing completed/indexed chunks and JSON index valid when a previously indexed basis document cannot be reprocessed because its stored PDF is missing.

Tests:
- Upload and index a basis document
- Delete the stored PDF
- Reprocess
- Assert old chunks/index remain valid and search still works
- Assert a new/non-indexed missing-file document still fails

### P1-2. Approved Rule Candidates Must Respect JSON Index Health
Approval and judgment should not bypass JSON basis-index validation.

Tests:
- Corrupt/remove JSON index and verify approval is blocked
- Remove one candidate vector from JSON and verify approval is blocked
- With an already approved candidate, corrupt JSON index and verify judgment does not emit approved citation
- Rebuild index and verify normal approval/judgment resumes

### P2-1. PyMuPDF Fallback Page Offsets
Add `char_start` and `char_end` metadata to PyMuPDF page metadata and keep char-count fallback drift-free.

Tests:
- Force PyMuPDF mode on a multi-page PDF
- Assert page offsets exist and chunk page_start/page_end are correct

### P2-2. OpenDataLoader Nested Text / Table Cells
Continue walking children when content is blank and support string cells in table rows.

Tests:
- Nested blank-content paragraph fixture
- Nested blank-content table cell fixture
- String-cell table row fixture

### P2-3. DOCX Tables
Extract DOCX table cells in addition to paragraphs.

Tests:
- DOCX with paragraphs and tables
- Assert table cell values appear in extracted text

### P3-1. Long Paragraph Overlap
Fix long paragraph chunking so overlap is actually present between adjacent chunks.

Tests:
- Long single paragraph over max chunk size
- Assert overlap text and char offsets are correct

## Suggested Verification
```powershell
py -3.13 -m py_compile backend/app/pipelines/pdf_readers.py backend/app/pipelines/parser.py backend/app/pipelines/basis_document.py backend/app/main.py backend/app/services/basis_rule_candidates.py
py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py -q
py -3.13 -m pytest backend/tests/test_api_flows.py -q
py -3.13 scripts/check-encoding.py
git diff --check
```
