# 기준문서 RAG 추가 문제점 수정계획

## 한국어 버전

## 구현 상태
최종 업데이트: 2026-05-31

- [x] P1-1 승인/반려 규칙 후보의 수동 수정값 보존
- [x] P2-1 failed/unindexed 기준문서 규칙 후보 추출 차단
- [x] P2-2 JSON 인덱스 손상 감지와 명시적 rebuild 흐름
- [x] P2-3 `condition_text` 기반 재추출 key 제거 및 `extraction_key` 우선 매칭
- [x] P2-4 JSON 인덱스를 검색 source로 전환
- [x] 회귀 테스트 추가 및 전체 백엔드/프론트 빌드 검증

## 문서 목적
이 문서는 기준문서 RAG 추가 코드리뷰에서 파악한 문제점을 모두 보강하기 위한 수정계획입니다.

포함 범위:
- 승인/반려된 규칙 후보가 재추출 과정에서 자동 추출값으로 조용히 바뀌는 문제
- failed/unindexed 기준문서에서도 규칙 후보 추출이 실행되는 문제
- JSON 인덱스 손상이 빈 인덱스로 조용히 처리되고 덮어써질 수 있는 문제
- 수동 수정 가능한 `condition_text`가 재추출 매칭 key에 들어가는 문제
- JSON 인덱스를 운영 산출물로 유지하기 위한 관리 계획

관련 선행 문서:
- `docs/basis-rag-json-index-management-plan.md`

## 해결 원칙
1. 관리자가 검토한 값은 자동 재추출이 조용히 덮어쓰지 않는다.
2. 검색/승인/judgment에 쓸 수 없는 기준문서는 규칙 후보 추출도 차단한다.
3. JSON 인덱스는 운영 산출물이므로 손상 상태를 숨기지 않는다.
4. 자동 추출 원문 식별값과 관리자 편집 표시값을 분리한다.
5. 모든 보강은 회귀 테스트를 먼저 또는 함께 추가한다.

## P1-1. 승인/반려 후보 자동 덮어쓰기 방지

### 문제
현재 재추출에서 기존 후보와 매칭되면 다음 필드가 자동 추출값으로 갱신됩니다.

- `condition_text`
- `required_evidence_types_json`
- `related_profile_fields_json`
- `citation_candidate_id`
- `confidence`

하지만 `status`, `review_note`, `reviewed_at`, `reviewer_name`은 유지됩니다.

그 결과 관리자가 승인한 후보의 의미가 자동으로 바뀌어도 계속 `approved` 상태로 남을 수 있습니다.

### 수정 방향
후보 필드를 두 그룹으로 분리합니다.

관리자 검토 필드:
- `condition_text`
- `required_evidence_types_json`
- `related_profile_fields_json`
- `status`
- `review_note`
- `reviewed_at`
- `reviewer_name`

자동 추출 원본 필드:
- `source_condition_text`
- `source_required_evidence_types_json`
- `source_related_profile_fields_json`
- `source_confidence`
- `source_condition_hash`
- `extraction_key`

### 재추출 정책
1. `needs_review` 후보는 자동 추출값으로 갱신 가능
2. `approved` 또는 `rejected` 후보는 관리자 검토 필드를 자동으로 덮지 않음
3. 승인/반려 후보의 원문 citation 위치만 바뀐 경우:
   - 기존 `condition_text`는 유지
   - 새 `citation_candidate_id`가 기존과 같으면 상태 유지
   - 새 `citation_candidate_id`가 달라지면 `needs_review`로 내리고 재검토 사유 기록
4. 자동 추출값이 관리자 편집값과 달라진 경우:
   - `source_*` 필드만 갱신
   - `review_note`에 자동 변경 감지 메시지를 추가하거나 별도 `needs_revalidation` 플래그 사용
5. 승인 후보가 실제 기준문서에서 더 이상 매칭되지 않으면:
   - 삭제하지 않음
   - `needs_review`
   - `citation_candidate_id=''`
   - 재검토 사유 기록

### 테스트
- 승인 후보의 `condition_text`를 수동 수정한 뒤 재추출해도 `condition_text`와 `approved` 상태가 유지되는지 검증
- 승인 후보의 citation chunk가 바뀌면 `needs_review`로 내려가는지 검증
- 미검토 후보는 재추출 시 자동 값으로 갱신되는지 검증
- 반려 후보도 자동 덮어쓰기 없이 보존되는지 검증

## P2-1. failed/unindexed 기준문서 규칙 후보 추출 차단

### 문제
규칙 후보 추출 API는 기준문서 존재만 확인하고 모든 청크를 대상으로 후보를 생성합니다.

검색과 승인 검증은 completed/indexed 문서만 허용하지만, 추출은 failed/unindexed 문서에서도 완료될 수 있습니다.

### 수정 방향
규칙 후보 추출 시작 전에 기준문서와 청크 상태를 검증합니다.

허용 조건:

```text
basis_documents.processing_status == completed
basis_documents.index_status == completed
대상 청크 중 vector_status == indexed and vector_id != '' 인 청크가 1개 이상
```

### API 응답 정책
조건 불만족 시:

```json
{
  "detail": "Basis document must be completed and indexed before rule candidate extraction.",
  "status": "basis_not_ready",
  "processing_status": "failed",
  "index_status": "failed"
}
```

HTTP 상태:
- `409 Conflict` 권장

operation_runs 기록:
- `status='failed'` 또는 `status='skipped'`
- `error_code='basis_not_ready'`
- 완료 operation으로 기록하지 않음

### 테스트
- failed 기준문서에서 규칙 후보 추출 요청 시 409 반환
- completed이지만 indexed chunk가 없는 문서에서 409 반환
- 실패 operation_runs에 `basis_not_ready`가 기록되는지 검증
- 정상 completed/indexed 문서는 기존처럼 후보 추출 가능

## P2-2. JSON 인덱스 손상 감지와 보호

### 문제
JSON 인덱스 로드가 실패하면 빈 인덱스를 반환합니다.

이후 저장 흐름이 실행되면 손상된 인덱스 파일이 조용히 덮어써질 수 있습니다.

JSON 인덱스를 운영 산출물로 유지하기로 했으므로, 이 동작은 위험합니다.

### 수정 방향
`load_basis_index()`를 단순 dict 반환에서 상태 포함 결과로 분리합니다.

예시:

```python
{
    "status": "ok" | "missing" | "corrupt" | "invalid_schema",
    "payload": {...},
    "error_message": "...",
    "path": "..."
}
```

### 보호 정책
1. JSON decode 실패 시 빈 인덱스로 처리하지 않음
2. 손상 파일은 `.corrupt-{timestamp}`로 복사 또는 rename
3. 일반 index update/delete 함수는 손상 상태에서 자동 저장 금지
4. 복구는 명시적인 `basis-index/rebuild`에서만 수행
5. 운영 상태 API에서 손상 상태를 표시

### 운영 API
`docs/basis-rag-json-index-management-plan.md`의 계획과 연결합니다.

- `GET /api/basis-index/status`
- `POST /api/basis-index/validate`
- `POST /api/basis-index/rebuild`

상태 예시:

```json
{
  "status": "corrupt",
  "can_search": false,
  "rebuild_required": true,
  "error_message": "Invalid JSON at line 1 column 10"
}
```

### 테스트
- 손상된 `basis-index.json`이 있으면 status API가 `corrupt`를 반환
- 손상 상태에서 일반 재처리가 파일을 조용히 덮지 않는지 검증
- rebuild API 호출 후 정상 schema/checksum으로 복구되는지 검증
- 손상 상태에서 검색을 막거나 명시적 오류를 반환하는지 검증

## P2-3. `condition_text` 기반 매칭 key 제거

### 문제
재추출 매칭 key가 사용자 편집 가능한 `condition_text`에 의존합니다.

### 수정 방향
`condition_text`는 관리자 표시/편집 필드로만 사용하고, 재추출 매칭은 `extraction_key`로 수행합니다.

필드 추가:
- `source_condition_text`
- `source_condition_hash`
- `extraction_key`

권장 key:

```text
basis:{basis_document_id}:rule:{rule_type}:chunk_hash:{chunk_hash}:source:{source_condition_hash}
```

### 마이그레이션
기존 row:
1. `source_condition_text = condition_text`
2. `source_condition_hash = hash(normalized condition_text)`
3. `extraction_key = legacy generated key`
4. 이후 재추출 1회 동안 legacy fallback 허용

### 테스트
- 수동 수정된 `condition_text`가 있어도 `extraction_key`로 기존 후보가 매칭되는지 검증
- legacy row가 첫 재추출에서 안정 key로 보강되는지 검증

## P2-4. JSON 인덱스를 검색 source로 전환

### 문제
현재 검색 source는 DB 청크입니다.

JSON 인덱스는 생성되지만 검색에 직접 사용되지 않습니다.

### 수정 방향
단계적으로 JSON-index-first 검색으로 전환합니다.

1단계:
- 과거 계획은 DB source 노출이었지만, 현재 구현은 `index_source: json_basis_index`를 사용한다.
- status/validate/rebuild API 추가

2단계:
- JSON 인덱스가 정상일 때 JSON token vector로 검색
- DB는 `chunk_id` 기반 상세 payload 조립에 사용
- JSON 인덱스가 손상/불일치이면 검색 중단

3단계:
- 운영 대시보드에 basis-index 상태 표시
- 백업/복원 검증에 basis-index checksum 포함

### 테스트
- 정상 JSON 인덱스 검색 결과가 기존 DB 검색 결과와 동등한지 검증
- JSON 인덱스 손상 시 DB fallback 없이 오류/재빌드 요구 반환
- DB에는 없고 JSON에만 있는 chunk id가 있으면 validate 실패
- DB에는 있는데 JSON에 없는 indexed chunk가 있으면 validate 실패

## 구현 순서
1. DB migration: `basis_rule_candidates` source/extraction key 필드 추가
2. 후보 payload/API/프론트 타입에 source 필드 추가
3. 재추출 로직에서 승인/반려 후보 자동 덮어쓰기 방지
4. failed/unindexed 기준문서 후보 추출 차단
5. 관련 회귀 테스트 추가
6. JSON index load result/status 구조 도입
7. 손상 인덱스 보호와 rebuild API 추가
8. basis-index status/validate/rebuild 테스트 추가
9. 검색을 JSON-index-first로 전환
10. 백업/복원/운영 대시보드에 index 상태 연결

## 완료 기준
- 승인/반려 후보는 자동 재추출로 검토된 의미가 조용히 바뀌지 않는다.
- failed/unindexed 기준문서는 후보 추출이 차단된다.
- 손상된 JSON 인덱스는 조용히 빈 인덱스로 덮이지 않는다.
- JSON 인덱스 상태를 API와 운영 화면에서 확인할 수 있다.
- 검색이 JSON 인덱스를 운영 source로 사용하거나, 최소한 JSON 인덱스 불일치를 명시적으로 보고한다.

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

- 이 문서의 주요 RAG 보강 항목은 구현 완료 상태로 유지됩니다.
- 안정적인 `extraction_key` 기반 재추출 매칭이 적용되어 관리자가 수정한 `condition_text`가 매칭 key를 흔들지 않습니다.
- JSON basis index는 운영 검색 산출물이며, 검색/승인/판단 citation은 인덱스 유효성을 요구합니다.
- OpenDataLoader 전환 이후 기준문서 table metadata와 `table_row` chunk가 추가되었습니다.
- 추가 PDF/RAG 보강으로 PyMuPDF fallback page offset, OpenDataLoader nested text, DOCX 표 cell 추출, 긴 문단 overlap이 수정되었습니다.
- 최신 전체 backend 기준선은 `134 passed`, `8 skipped`입니다.

## Questions for Product Owner
- 승인 후보의 citation 위치만 바뀐 경우 즉시 `needs_review`로 내리는 정책이 맞는가?
- JSON 인덱스 손상 시 검색을 완전히 막을지, 운영 경고와 함께 DB fallback을 허용할지 최종 결정이 필요하다.
- 재추출로 stale 후보가 생겼을 때 관리자에게 배지, 알림, 작업 큐 중 어떤 UX로 보여줄지 결정이 필요하다.

---

# AI / Engineering Version (English)

## Implementation Status
Last updated: 2026-06-07

- [x] Preserve manually reviewed rule-candidate fields during re-extraction.
- [x] Block rule-candidate extraction for failed/unindexed basis documents.
- [x] Detect corrupt JSON indexes and require explicit rebuild.
- [x] Prefer stable `extraction_key` matching instead of editable `condition_text`.
- [x] Use the JSON basis index as the retrieval source.
- [x] Add regression tests and verify backend/frontend builds.
- [x] Add OpenDataLoader table metadata and `table_row` chunks.
- [x] Fix PyMuPDF fallback page offsets.
- [x] Preserve nested OpenDataLoader text/table-cell content.
- [x] Include DOCX table-cell text in extraction.
- [x] Fix long single-paragraph chunk overlap.

## Purpose
This document defines the remediation plan for all remaining basis-document RAG issues identified in the additional code review.

Scope:
- approved/rejected rule candidates can be silently overwritten by automatic re-extraction
- rule-candidate extraction can run against failed/unindexed basis documents
- corrupt JSON indexes are treated as empty indexes and can be overwritten silently
- editable `condition_text` is part of the re-extraction matching key
- JSON index must be retained as an operational artifact

## Principles
1. Do not silently overwrite admin-reviewed values.
2. Do not extract rule candidates from basis documents that cannot be used for search/approval/judgment.
3. Treat JSON index corruption as an operational state, not as an empty index.
4. Separate immutable extraction identity from editable display/review text.
5. Add regression tests with every hardening change.

## P1-1: Prevent Silent Overwrite Of Reviewed Candidates

Split candidate fields into admin-reviewed fields and source extraction fields.

Admin-reviewed:
- `condition_text`
- `required_evidence_types_json`
- `related_profile_fields_json`
- `status`
- `review_note`
- `reviewed_at`
- `reviewer_name`

Source extraction:
- `source_condition_text`
- `source_required_evidence_types_json`
- `source_related_profile_fields_json`
- `source_confidence`
- `source_condition_hash`
- `extraction_key`

Policy:
- `needs_review` candidates may be updated from extraction.
- `approved`/`rejected` candidates must not have reviewed semantic fields overwritten.
- If citation location changes for reviewed candidates, move them back to `needs_review`.
- If a reviewed candidate no longer matches extraction, keep it but clear citation and mark `needs_review`.

## P2-1: Block Extraction For Failed/Unindexed Basis Documents

Extraction should require:

```text
basis_documents.processing_status == completed
basis_documents.index_status == completed
at least one chunk with vector_status == indexed and vector_id != ''
```

Return `409 Conflict` with:

```json
{
  "status": "basis_not_ready",
  "detail": "Basis document must be completed and indexed before rule candidate extraction."
}
```

Record operation runs as `failed` or `skipped`, not completed.

## P2-2: Detect And Protect Corrupt JSON Indexes

Change JSON index loading from plain dict return to status result:

```python
{
    "status": "ok" | "missing" | "corrupt" | "invalid_schema",
    "payload": {...},
    "error_message": "...",
    "path": "..."
}
```

Policy:
- Do not treat JSON decode failure as an empty index.
- Preserve/rename corrupt files.
- Block normal save/delete index updates while index is corrupt.
- Rebuild only through explicit `basis-index/rebuild`.

## P2-3: Remove Editable `condition_text` From Matching Key

Add:
- `source_condition_text`
- `source_condition_hash`
- `extraction_key`

Recommended key:

```text
basis:{basis_document_id}:rule:{rule_type}:chunk_hash:{chunk_hash}:source:{source_condition_hash}
```

Legacy migration:
- initialize source fields from current `condition_text`
- allow one-time legacy fallback matching
- write stable extraction keys during re-extraction

## P2-4: Move Search To JSON-Index-First

Stage 1:
- historical plan was to keep DB source and expose `index_source`; current implementation uses `index_source: json_basis_index`
- add status/validate/rebuild APIs

Stage 2:
- search JSON token vectors first
- hydrate chunk/citation payloads from DB by `chunk_id`
- fail search if JSON index is corrupt or inconsistent

Stage 3:
- show basis-index health in operations dashboard
- include index checksum in backup/restore validation

## Implementation Order
1. Add source/extraction-key columns to `basis_rule_candidates`.
2. Expose source fields in payload/API/frontend types.
3. Prevent reviewed candidate overwrite during re-extraction.
4. Block extraction for failed/unindexed basis documents.
5. Add regression tests.
6. Introduce structured JSON index load status.
7. Add corrupt index protection and rebuild API.
8. Add status/validate/rebuild tests.
9. Switch retrieval to JSON-index-first.
10. Wire index status into backup/restore and operations dashboard.

## Definition Of Done
- Reviewed candidates cannot silently change meaning through automatic re-extraction.
- Failed/unindexed basis documents cannot produce completed extraction runs.
- Corrupt JSON index files are not silently overwritten.
- JSON index status is visible through API and operations UI.
- Retrieval either uses JSON index as source or explicitly reports index inconsistency.

## Questions for Product Owner
- Should a reviewed candidate be moved to `needs_review` whenever its citation location changes?
- Should corrupt JSON index block search completely, or should DB fallback be allowed with a warning?
- Should stale candidates be surfaced through badges, notifications, or an operations queue?
