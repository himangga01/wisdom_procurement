# 기준문서 RAG P2 수정계획: 안정 매칭 키와 JSON 인덱스 운영 관리

## 한국어 버전

## 구현 상태
최종 업데이트: 2026-05-31

- [x] JSON 인덱스 schema v2와 checksum 필드 도입
- [x] `GET /api/basis-index/status`, `POST /api/basis-index/validate`, `POST /api/basis-index/rebuild` 추가
- [x] 검색 API를 JSON 인덱스 우선 source로 전환
- [x] 손상/불일치 인덱스에서 DB fallback 없이 409로 차단
- [x] 백업 manifest와 검증에 `basis-index.json` checksum 포함
- [x] 운영 대시보드 health에 기준문서 인덱스 상태 표시

## 문서 목적
이 문서는 기준문서 RAG 코드리뷰 이후 남은 P2 리스크 2개를 보강하기 위한 수정계획입니다.

대상 리스크:
- 관리자가 수동 수정한 `condition_text`가 재추출 매칭 key에 포함되어, 같은 원문 후보도 재추출 후 다른 후보로 인식될 수 있음
- JSON 인덱스를 생성/삭제하고 있지만 실제 검색 source는 DB 청크라서, JSON 인덱스의 운영 역할과 정합성 관리 기준이 불명확함

## 결정 사항
JSON 인덱스는 제거하지 않고 운영 산출물로 유지합니다.

역할 분리:
- SQLite DB: 기준문서, 청크, 규칙 후보, 리뷰 상태의 원본 저장소
- JSON 인덱스: 로컬 RAG 검색에 사용할 운영 인덱스 산출물
- 검색 API: 최종적으로 JSON 인덱스를 우선 사용하되, DB와 정합성이 깨진 경우 검색을 중단하거나 관리자에게 재빌드를 요구

## 수정계획 A: 규칙 후보 재추출 안정 key 도입

### 현재 문제
현재 재추출 매칭 key는 `rule_type + condition_text 정규화 값 + target_scope`입니다.

하지만 `condition_text`는 관리자가 UX에서 수정할 수 있는 값입니다. 관리자가 승인 후보 문구를 사람이 읽기 좋게 고치면, 다음 재추출 때 같은 원문 후보라도 기존 후보와 매칭되지 않을 수 있습니다.

### 목표
사용자 편집값과 시스템 재추출 식별값을 분리합니다.

### DB 보강
`basis_rule_candidates`에 다음 필드를 추가합니다.

| 필드 | 목적 |
|---|---|
| `source_condition_text` | 자동 추출 당시 원문 문구 |
| `source_condition_hash` | 원문 문구 정규화 hash |
| `extraction_key` | 재추출 매칭용 안정 key |

`condition_text`는 관리자 편집용 표시/판단 문구로 유지합니다.

### extraction_key 구성
권장 구성:

```text
basis:{basis_document_id}:rule:{rule_type}:chunk_hash:{chunk_hash}:source:{source_condition_hash}
```

이유:
- `condition_text` 수동 수정과 무관하게 같은 원문 후보를 찾을 수 있음
- chunk id가 재처리마다 바뀌어도 `chunk_hash`와 원문 hash가 같으면 연결 가능
- 기준문서가 실제로 바뀌면 hash가 달라져 재검토 대상으로 분리 가능

### 재추출 정책
1. 새 후보 생성 시 `source_condition_text`, `source_condition_hash`, `extraction_key`를 함께 만든다.
2. 기존 후보와 매칭할 때는 `extraction_key`를 우선 사용한다.
3. 기존 후보가 `extraction_key`가 없는 과거 데이터라면 1회에 한해 기존 key 방식으로 fallback 매칭한다.
4. 매칭된 후보는 `basis_chunk_id`, `citation_candidate_id`, `source_condition_text`, `source_condition_hash`만 갱신한다.
5. `condition_text`, `status`, `review_note`, `reviewed_at`, `reviewer_name`은 관리자 검토 이력이므로 보존한다.
6. 매칭되지 않은 승인/반려 후보는 삭제하지 않고 `needs_review`로 내리고 citation을 비운다.
7. 매칭되지 않은 미검토 후보만 삭제하거나 archived 처리한다.

### 테스트
- 승인 후보의 `condition_text`를 수동 수정한 뒤 재추출해도 승인 상태가 유지되는지 검증
- chunk id가 바뀌는 재처리 후에도 같은 `chunk_hash + source_condition_hash`면 기존 후보가 유지되는지 검증
- 실제 원문이 바뀌면 기존 승인 후보가 `needs_review`로 내려가는지 검증

## 수정계획 B: JSON 인덱스 운영 산출물 관리

### 현재 문제
JSON 인덱스 파일은 생성/삭제되지만 검색은 DB 청크에서 토큰 벡터를 재계산합니다.

이 상태에서는:
- JSON 인덱스 파일이 손상되어도 검색이 계속 성공할 수 있음
- 운영자가 `index_status=completed`를 신뢰하기 어려움
- 백업/복원 후 JSON 인덱스와 DB 상태가 어긋나도 감지하기 어려움

### 목표
JSON 인덱스를 운영 산출물로 유지하고, 검색/검증/복구 기준을 명확히 합니다.

### JSON 인덱스 역할
JSON 인덱스는 로컬 단일 PC 운영 기준의 RAG 검색 인덱스입니다.

단기 목표:
- DB 청크와 JSON 인덱스의 정합성을 검증할 수 있게 한다.
- 검색 응답에 현재 사용한 인덱스 source를 명시한다.
- 인덱스 손상/누락 시 운영자가 재빌드할 수 있게 한다.

중기 목표:
- `basis_search_results()`가 JSON 인덱스를 우선 검색 source로 사용한다.
- DB는 citation 상세 조회와 원문 chunk payload 조립에 사용한다.

### JSON 인덱스 스키마
현재 `basis-index.json`을 다음 구조로 버전 관리합니다.

```json
{
  "schema_version": "basis-index-v2",
  "model": "local-token-v1",
  "created_at": "2026-05-31T12:00:00+09:00",
  "updated_at": "2026-05-31T12:00:00+09:00",
  "source": "sqlite:basis_document_chunks",
  "chunk_count": 120,
  "checksum": "sha256:...",
  "chunks": {
    "basis-1-10-abcdef123456": {
      "basis_document_id": 1,
      "chunk_id": 10,
      "chunk_hash": "abcdef...",
      "processing_run_id": "20260531120000-...",
      "tokens": {
        "license": 2,
        "certificate": 1
      },
      "metadata": {
        "page_start": 1,
        "page_end": 2,
        "section_title": "입찰참가자격"
      }
    }
  }
}
```

### 정합성 규칙
JSON 인덱스의 chunk 항목은 DB의 다음 조건과 일치해야 합니다.

```sql
basis_documents.processing_status = 'completed'
basis_documents.index_status = 'completed'
basis_document_chunks.vector_status = 'indexed'
basis_document_chunks.vector_id <> ''
basis_document_chunks.chunk_hash = index.chunks[*].chunk_hash
```

### 운영 API 계획
다음 API를 추가합니다.

| API | 목적 |
|---|---|
| `GET /api/basis-index/status` | JSON 인덱스 파일 존재, schema_version, chunk_count, checksum, DB 정합성 요약 |
| `POST /api/basis-index/validate` | DB와 JSON 인덱스 정합성 상세 검증 |
| `POST /api/basis-index/rebuild` | DB의 completed/indexed chunk 기준으로 JSON 인덱스 전체 재생성 |

### 검색 정책
Phase 1 보강:
- 현재처럼 DB 검색을 유지하되 `index_source: db_chunks_completed_indexed`를 명시한다.
- 동시에 `basis-index/status`와 `validate`를 제공해 운영자가 JSON 인덱스 상태를 확인한다.

Phase 2 보강:
- `basis_search_results()`가 JSON 인덱스를 먼저 로드한다.
- JSON 인덱스가 유효하면 JSON token vector로 검색한다.
- 검색 결과의 chunk 상세는 DB에서 `chunk_id`로 조회한다.
- JSON 인덱스가 없거나 손상되면 검색 결과를 반환하지 않고 `index_unavailable` 또는 `index_invalid`를 반환한다.
- 사용자는 `basis-index/rebuild`로 복구한다.

### 백업/복원 정책
- 백업에는 `storage/basis-index/basis-index.json`을 포함한다.
- 복원 dry-run에서는 JSON 인덱스 manifest/checksum을 검증한다.
- 복원 후 DB와 JSON 인덱스 checksum이 맞지 않으면 `basis-index/rebuild_required` 상태를 표시한다.

### 테스트
- JSON 인덱스 status API가 파일 없음/정상/손상 상태를 구분하는지 검증
- DB chunk 수와 JSON index chunk 수가 다를 때 validate가 실패하는지 검증
- rebuild 후 DB completed/indexed chunk 수와 JSON index chunk 수가 일치하는지 검증
- JSON 인덱스 손상 시 검색이 조용히 DB fallback하지 않는지 검증
- 백업 검증에서 basis-index manifest/checksum이 확인되는지 검증

## 구현 순서
1. `basis_rule_candidates` 안정 key 필드 추가
2. 규칙 후보 추출/재추출 로직에서 `extraction_key` 우선 매칭 적용
3. 수동 수정 후 재추출 회귀 테스트 추가
4. JSON 인덱스 schema v2와 checksum helper 추가
5. `basis-index/status`, `validate`, `rebuild` API 추가
6. JSON 인덱스 정합성 테스트 추가
7. 검색을 JSON 인덱스 우선으로 전환
8. 백업/복원 검증에 JSON 인덱스 정합성 항목 추가
9. 운영 대시보드에 basis-index 상태 표시

## Questions for Product Owner
- JSON 인덱스 손상 시 검색을 완전히 막을지, 경고와 함께 DB fallback을 허용할지 결정이 필요합니다. 운영 산출물로 유지한다면 검색 차단이 더 안전합니다.
- 관리자가 편집한 `condition_text`를 판단 엔진에 우선 사용할지, 원문 `source_condition_text`를 우선 사용할지 UX 정책 확인이 필요합니다.
- 오래된 승인 후보가 `needs_review`로 내려갈 때 관리자에게 어떤 알림/배지를 보여줄지 결정이 필요합니다.

---

# AI / Engineering Version (English)

## Implementation Status
Last updated: 2026-05-31

- [x] Introduce JSON index schema v2 and checksum fields.
- [x] Add `GET /api/basis-index/status`, `POST /api/basis-index/validate`, and `POST /api/basis-index/rebuild`.
- [x] Prefer the JSON index as the basis retrieval source.
- [x] Block retrieval with HTTP 409 when the JSON index is corrupt or inconsistent; no DB fallback.
- [x] Include `basis-index.json` checksum in backup manifests and validation.
- [x] Expose basis-index health in the operations dashboard.

## Purpose
This document defines the remediation plan for two remaining P2 risks in the basis-document RAG flow:
- manually edited `condition_text` is currently part of the re-extraction matching key
- the JSON index is generated and deleted, but DB chunks are currently the actual retrieval source

## Decision
Keep the JSON index as an operational artifact.

Separation of responsibilities:
- SQLite DB: source of truth for basis documents, chunks, rule candidates, and review state
- JSON index: local RAG retrieval index artifact
- Search API: eventually prefer the JSON index; if index/DB consistency fails, stop retrieval or require operator rebuild

## Plan A: Stable Rule-Candidate Matching Key

Current matching key:

```text
rule_type + normalized condition_text + target_scope
```

Problem: `condition_text` is editable by admins, so re-extraction can lose linkage to the original extracted candidate.

Add columns to `basis_rule_candidates`:
- `source_condition_text`
- `source_condition_hash`
- `extraction_key`

Recommended `extraction_key`:

```text
basis:{basis_document_id}:rule:{rule_type}:chunk_hash:{chunk_hash}:source:{source_condition_hash}
```

Re-extraction policy:
1. Generate source text/hash/key for every candidate.
2. Match existing candidates by `extraction_key` first.
3. For legacy rows without `extraction_key`, use the old key once as fallback.
4. Update source/citation fields for matched rows.
5. Preserve admin-edited `condition_text`, status, review note, reviewed timestamp, and reviewer name.
6. Move unmatched approved/rejected candidates to `needs_review` with citation cleared.
7. Delete or archive only unmatched unreviewed candidates.

## Plan B: JSON Index Operational Management

The JSON index remains the local RAG retrieval artifact.

Short-term:
- add status/validation/rebuild APIs
- make index source explicit
- detect missing/corrupt/inconsistent JSON index states

Mid-term:
- make `basis_search_results()` prefer JSON index retrieval
- use DB only for citation detail and chunk payload hydration
- do not silently fall back to DB retrieval if the JSON index is invalid

New APIs:
- `GET /api/basis-index/status`
- `POST /api/basis-index/validate`
- `POST /api/basis-index/rebuild`

JSON index validity rules:
- basis document must be `processing_status='completed'`
- basis document must be `index_status='completed'`
- chunk must be `vector_status='indexed'`
- chunk must have a non-empty `vector_id`
- indexed `chunk_hash` must match the DB chunk hash

## Implementation Order
1. Add stable key fields to `basis_rule_candidates`.
2. Update extraction/re-extraction to match by `extraction_key`.
3. Add regression tests for manual `condition_text` edits.
4. Add JSON index schema v2 and checksum helpers.
5. Add basis-index status/validate/rebuild APIs.
6. Add JSON index consistency tests.
7. Switch search to JSON-index-first retrieval.
8. Add basis-index checks to backup/restore validation.
9. Show basis-index health in the operations dashboard.

## Questions for Product Owner
- If the JSON index is invalid, should retrieval be blocked or should DB fallback be allowed with a warning?
- Should judgment prefer admin-edited `condition_text` or immutable `source_condition_text`?
- What UX should notify admins when approved candidates are moved back to `needs_review`?
