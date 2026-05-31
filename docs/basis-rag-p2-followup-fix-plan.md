# 기준문서 RAG P2 후속 이슈 수정계획

## 한국어 버전

## 문서 목적
오늘 기준문서 RAG/JSON 인덱스 보강 이후 재검토에서 발견된 P2 후속 이슈 2건을 빠르게 정리하고, 수정 범위와 테스트 기준을 명확히 하기 위한 문서입니다.

이번 이슈는 핵심 검색/재추출 로직이 다시 깨진 문제가 아니라, JSON 인덱스를 운영 검색 source로 전환하면서 주변 보조 경로 일부가 새 정책을 끝까지 반영하지 못한 문제입니다.

대상 이슈:
- 검색 평가 저장 결과의 `index_source`와 policy 문구가 예전 DB 검색 기준으로 남아 있음
- 기준문서 삭제 API가 손상된 JSON 인덱스 예외를 409 응답으로 변환하지 않아 500으로 노출될 수 있음

## 왜 이슈가 계속 나오는가
이번 변경은 단순 함수 수정이 아니라 “JSON 인덱스를 운영 산출물로 유지하고 실제 검색 source로 사용한다”는 정책 전환입니다. 따라서 실제 검색 함수뿐 아니라 다음 보조 경로까지 함께 맞아야 합니다.

- 검색 API 응답
- 검색 평가 저장 payload
- 운영/QA 리포트 문구
- 삭제/재처리/백업처럼 인덱스를 건드리는 예외 경로
- 테스트 assertion

이번에 발견된 2건은 위 보조 경로 정합성 문제입니다. 즉, 데이터 판단 로직의 새 결함이라기보다 전환 정책이 코드 전체에 끝까지 반영되는 마무리 항목입니다.

## 수정 원칙
1. JSON 인덱스가 실제 검색 source라는 사실을 모든 응답, 저장 payload, 문구에 일관되게 반영한다.
2. 손상된 JSON 인덱스는 조용히 무시하지 않고 운영자에게 rebuild 필요 상태로 반환한다.
3. 검색 평가와 삭제 API의 오류 응답 형식을 검색 API와 최대한 맞춘다.
4. 수정마다 회귀 테스트를 추가해 같은 불일치가 다시 나오지 않게 한다.

## P2-1. 검색 평가 저장 payload의 index_source 정합성 보강

### 현재 문제
`create_basis_retrieval_evaluation()`은 실제 검색에 `basis_search_results()`를 사용하고, 이 함수는 JSON 인덱스를 검색 source로 사용합니다.

하지만 저장되는 `result` payload에는 기존 DB 청크 검색 기준 값이 남아 있었습니다.

```json
{
  "policy": "검색 결과는 completed/indexed DB 청크 기준 citation 후보...",
  "index_source": "db_chunks_completed_indexed"
}
```

이 때문에 운영자나 QA 리포트가 검색 평가 결과를 볼 때 실제 검색 source를 잘못 이해할 수 있습니다.

### 수정 대상
- `backend/app/main.py`
  - `create_basis_retrieval_evaluation()`

### 수정 방향
1. `result["index_source"]`를 `json_basis_index`로 변경한다.
2. `result["policy"]` 문구를 JSON 인덱스 우선 검색 기준으로 변경한다.
3. 각 query result에 포함되는 검색 결과는 이미 `index_source: json_basis_index`를 포함하므로 그대로 둔다.
4. 향후 source 문자열 변경 가능성을 줄이기 위해 별도 상수화 후보로 남긴다.

### 테스트 계획
- `backend/tests/test_api_flows.py`
  - `test_phase25c_retrieval_evaluation_tracks_citation_coverage`에 assertion 추가

검증 항목:
- `payload["result"]["index_source"] == "json_basis_index"`
- `payload["result"]["policy"]`에 JSON 인덱스 의미가 포함됨
- 첫 query result의 `results[0]["index_source"] == "json_basis_index"`

### 완료 기준
- [x] 검색 평가 저장 결과와 검색 API 응답의 source 표기가 일치한다.
- [x] 기존 citation coverage 테스트가 유지된다.
- [x] 회귀 테스트에 source/policy assertion이 포함된다.

## P2-2. 기준문서 삭제 API의 손상 인덱스 예외 응답 정합성 보강

### 현재 문제
기준문서 삭제 API는 삭제 중 `delete_basis_vectors()`를 호출합니다.

`delete_basis_vectors()` 내부에서는 `load_basis_index()`를 호출하고, JSON 인덱스가 손상되어 있으면 `BasisIndexError`를 발생시킵니다.

기존 삭제 라우트는 이 예외를 잡지 않아 일반 500 오류로 노출될 수 있었습니다.

### 수정 대상
- `backend/app/main.py`
  - `delete_basis_document()`

### 수정 방향
1. `delete_basis_document()`에서 `delete_basis_vectors()` 호출을 `try/except BasisIndexError`로 감싼다.
2. 예외 발생 시 검색 API와 동일한 형식으로 409를 반환한다.

권장 응답:

```json
{
  "detail": "Basis index ...",
  "status": "basis_index_unavailable",
  "rebuild_required": true
}
```

3. 삭제는 중단한다. 손상된 인덱스 상태에서 DB 문서만 삭제하면 DB/JSON 인덱스 불일치가 더 커질 수 있기 때문이다.
4. 운영자는 `POST /api/basis-index/rebuild`로 복구 후 삭제를 다시 시도한다.

### 테스트 계획
- `backend/tests/test_api_flows.py`에 신규 테스트 추가

테스트 이름:
- `test_basis_document_delete_returns_409_when_basis_index_is_corrupt`

검증 항목:
1. 기준문서 업로드
2. `basis-index.json`을 손상된 JSON으로 변경
3. `DELETE /api/basis-documents/{id}` 호출
4. HTTP 409 반환 확인
5. payload:
   - `status == "basis_index_unavailable"`
   - `rebuild_required == true`
6. DB에서 기준문서와 청크가 삭제되지 않았는지 확인
7. rebuild 후 삭제가 정상 동작하는지 확인

### 완료 기준
- [x] 손상 인덱스 상태에서 삭제 API가 500을 내지 않는다.
- [x] 삭제 중단으로 DB/JSON 불일치 확대를 막는다.
- [x] rebuild 후 정상 삭제 경로가 유지된다.

## 구현 순서
- [x] `create_basis_retrieval_evaluation()`의 `result.index_source`와 policy 문구 수정
- [x] 검색 평가 테스트 assertion 추가
- [x] `delete_basis_document()`의 `BasisIndexError` -> 409 변환 추가
- [x] 삭제 예외 경로 테스트 추가
- [x] 백엔드 전체 테스트 실행
- [x] 프론트 빌드와 인코딩 검사 실행
- [x] `docs/work-log.md`에 작업 기록

## 수정 후 추가 코드리뷰 결과
이번 계획의 2개 이슈는 구현과 테스트로 해소되었습니다. 다만 후속 코드리뷰에서 별도 리스크 1건을 추가로 확인했습니다.

추가 리스크:
- `delete_basis_vectors()`는 `load_basis_index()`만 사용하므로, `basis-index.json`이 “파일 없음” 상태이거나 DB와 불일치한 상태인지는 삭제 전에 충분히 검증하지 않습니다.
- 특히 여러 기준문서가 있는 상태에서 JSON 인덱스 파일이 없으면, 삭제 API가 빈 인덱스를 새로 저장한 뒤 대상 문서를 삭제할 수 있습니다. 이 경우 남은 기준문서의 indexed chunk가 DB에는 있는데 JSON 인덱스에는 없는 상태가 되어 검색 API가 다시 rebuild 필요 상태가 될 수 있습니다.

권장 후속 조치:
- 삭제 전에 `validate_basis_index(conn)` 기준으로 `rebuild_required` 상태를 확인한다.
- 인덱스가 missing/inconsistent/corrupt이고 DB에 indexed chunk가 있으면 삭제를 409로 막는다.
- 단일 문서 삭제처럼 결과적으로 빈 인덱스가 정상 상태가 되는 경우도, 정책을 단순하게 유지하려면 먼저 rebuild 후 삭제하도록 안내한다.

## P2-3. 기준문서 삭제 전 JSON 인덱스 정합성 검증 보강

### 현재 문제
P2-2 수정으로 손상된 JSON 파일은 409로 막지만, 삭제 전에 전체 인덱스 정합성을 검증하지는 않습니다.

따라서 다음 상태에서는 삭제가 진행될 수 있습니다.

- `basis-index.json` 파일이 없음
- DB에는 indexed chunk가 남아 있음
- JSON 인덱스에는 일부 vector가 빠져 있거나 DB에 없는 vector가 남아 있음

특히 여러 기준문서가 있는 상태에서 JSON 인덱스 파일이 없으면, 삭제 API가 빈 인덱스를 새로 저장한 뒤 대상 문서를 삭제할 수 있습니다. 그러면 남은 기준문서의 chunk가 DB에는 있지만 JSON 인덱스에는 없는 상태가 됩니다.

### 수정 대상
- `backend/app/main.py`
  - `delete_basis_document()`
- `backend/tests/test_api_flows.py`
  - 기준문서 삭제 회귀 테스트

### 수정 방향
1. `delete_basis_document()`에서 `delete_basis_vectors()` 호출 전에 `validate_basis_index(conn)`를 호출한다.
2. `validation["rebuild_required"]`가 true이면 삭제를 진행하지 않는다.
3. 검색 API와 같은 계열의 409 응답을 반환한다.

권장 응답:

```json
{
  "detail": "basis-index.json is missing while DB has indexed chunks.",
  "status": "basis_index_unavailable",
  "index_status": "missing",
  "rebuild_required": true
}
```

4. 정상 인덱스일 때만 `delete_basis_vectors()`와 DB 삭제를 이어간다.
5. 운영자는 `POST /api/basis-index/rebuild` 후 삭제를 재시도한다.

### 테스트 계획
- `test_basis_document_delete_returns_409_when_basis_index_is_missing`
  - 기준문서 2개 업로드
  - `basis-index.json` 삭제
  - 삭제 API 호출
  - 409, `index_status: missing`, `rebuild_required: true` 확인
  - 두 기준문서와 청크가 DB에 남아 있는지 확인
  - rebuild 후 삭제가 정상 동작하는지 확인
- `test_basis_document_delete_returns_409_when_basis_index_is_inconsistent`
  - 기준문서 2개 업로드
  - JSON 인덱스에서 일부 vector를 제거한 뒤 checksum을 다시 맞춰 저장
  - 삭제 API 호출
  - 409, `index_status: inconsistent`, `rebuild_required: true` 확인
  - 문서/청크가 삭제되지 않았는지 확인

### 완료 기준
- [x] missing 인덱스 상태에서 삭제 API가 DB/파일을 건드리지 않고 409를 반환한다.
- [x] inconsistent 인덱스 상태에서 삭제 API가 DB/파일을 건드리지 않고 409를 반환한다.
- [x] rebuild 후 정상 삭제 경로는 유지된다.
- [x] 전체 백엔드 테스트와 인코딩 검사를 통과한다.

## Questions for Product Owner
- 없음. 이번 3건은 이미 승인된 JSON 인덱스 운영 정책에 맞춘 정합성 수정입니다.
- 추가로 제품 판단이 필요한 항목은 없습니다.

---

# AI / Engineering Version (English)

## Purpose
This document defines the follow-up fix plan for two P2 issues found after today's basis RAG / JSON index remediation review.

These are not core retrieval or re-extraction failures. They are second-order consistency gaps after promoting the JSON index to an operational retrieval artifact.

Target issues:
- retrieval evaluation result metadata still says `db_chunks_completed_indexed`
- basis document deletion can surface a generic 500 when `basis-index.json` is corrupt

## Why These Issues Appeared
The change was a policy-level transition: the JSON index is now the operational retrieval source. That means not only search itself, but also evaluation metadata, QA wording, delete/reprocess/backup paths, and tests must reflect that policy.

The two findings are remaining consistency gaps around metadata and exception handling.

## Fix Principles
1. Make every response and persisted payload reflect JSON-index-first retrieval.
2. Never silently ignore a corrupt JSON index.
3. Use consistent API error shapes for index-unavailable states.
4. Add regression tests for every fixed path.

## P2-1. Fix Retrieval Evaluation `index_source`

### Problem
`create_basis_retrieval_evaluation()` uses `basis_search_results()`, which now searches the JSON index. However, the stored evaluation result still contained DB-chunk-based metadata.

### Target
- `backend/app/main.py`
  - `create_basis_retrieval_evaluation()`

### Plan
1. Change `result["index_source"]` to `json_basis_index`.
2. Update the policy copy to describe JSON-index-first retrieval.
3. Keep per-result `index_source` values as returned by `basis_search_results()`.
4. Consider a shared constant for index-source strings.

### Tests
Update `test_phase25c_retrieval_evaluation_tracks_citation_coverage`:
- assert `payload["result"]["index_source"] == "json_basis_index"`
- assert policy mentions JSON index semantics
- assert per-result `index_source == "json_basis_index"`

### Completion
- [x] Stored retrieval evaluation source metadata matches the search API source.
- [x] Existing citation coverage behavior remains covered.
- [x] Regression assertions cover source and policy metadata.

## P2-2. Return 409 For Delete With Corrupt Basis Index

### Problem
`delete_basis_document()` calls `delete_basis_vectors()`, which calls `load_basis_index()`. If the JSON index is corrupt, `BasisIndexError` could escape as a generic 500.

### Target
- `backend/app/main.py`
  - `delete_basis_document()`

### Plan
1. Wrap `delete_basis_vectors()` in `try/except BasisIndexError`.
2. Return HTTP 409 with:

```json
{
  "detail": "...",
  "status": "basis_index_unavailable",
  "rebuild_required": true
}
```

3. Abort deletion when the index is corrupt to avoid making DB/index inconsistency worse.
4. Operator should rebuild via `POST /api/basis-index/rebuild`, then retry deletion.

### Tests
Add `test_basis_document_delete_returns_409_when_basis_index_is_corrupt`:
1. Upload a basis document.
2. Corrupt `basis-index.json`.
3. Call `DELETE /api/basis-documents/{id}`.
4. Assert HTTP 409 and index-unavailable payload.
5. Assert DB document/chunks remain.
6. Rebuild and assert normal deletion works afterward.

### Completion
- [x] Delete API no longer returns generic 500 for corrupt indexes.
- [x] Delete aborts instead of expanding DB/JSON inconsistency.
- [x] Rebuild then delete remains functional.

## Implementation Status
- [x] Fixed retrieval evaluation metadata.
- [x] Added retrieval evaluation assertions.
- [x] Fixed delete route error mapping.
- [x] Added corrupt-index delete test.
- [x] Ran backend tests.
- [x] Ran frontend build and encoding check.
- [x] Recorded work in `docs/work-log.md`.

## Post-Fix Review Finding
The planned two issues are fixed and covered by tests. One separate follow-up risk remains:

- `delete_basis_vectors()` calls `load_basis_index()` rather than validating DB/index consistency with `validate_basis_index(conn)`.
- If `basis-index.json` is missing while DB still has indexed chunks for multiple basis documents, deleting one document can save an empty JSON index and leave remaining DB chunks missing from the JSON index.
- Recommended follow-up: validate index consistency before deletion and return 409 for missing/inconsistent/corrupt index states when DB indexed chunks exist.

## P2-3. Validate JSON Index Consistency Before Basis Document Deletion

### Problem
P2-2 blocks corrupt JSON files, but the delete route still does not validate full DB/index consistency before deletion.

Deletion can proceed when:
- `basis-index.json` is missing
- DB still has indexed chunks
- the JSON index is valid JSON but inconsistent with DB vector rows

With multiple basis documents, a missing index can lead deletion to save an empty index and remove one document while leaving other indexed DB chunks missing from the JSON index.

### Target
- `backend/app/main.py`
  - `delete_basis_document()`
- `backend/tests/test_api_flows.py`
  - deletion regression tests

### Plan
1. Call `validate_basis_index(conn)` before `delete_basis_vectors()`.
2. If `validation["rebuild_required"]` is true, abort deletion.
3. Return HTTP 409 with `basis_index_unavailable`, `index_status`, and `rebuild_required: true`.
4. Continue with `delete_basis_vectors()` and DB deletion only when the index is valid.
5. Operator should rebuild via `POST /api/basis-index/rebuild`, then retry deletion.

### Tests
- `test_basis_document_delete_returns_409_when_basis_index_is_missing`
- `test_basis_document_delete_returns_409_when_basis_index_is_inconsistent`

### Completion
- [x] Missing index states abort deletion and return 409.
- [x] Inconsistent index states abort deletion and return 409.
- [x] Rebuild then delete remains functional.
- [x] Backend tests and encoding checks pass.

## Questions for Product Owner
None. All three fixes follow the approved JSON index operational policy.
