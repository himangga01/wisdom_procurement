# 판단 검토 UX 전면 개선 제안서

## 한국어 버전

## 1. 문제 정의

`판단 검토` 메뉴는 이 서비스의 핵심 화면입니다. 사용자는 이 화면에서 “이 공고에 지금 지원 준비가 되어 있는지”, “무엇이 부족한지”, “다음에 어떤 서류를 준비해야 하는지”를 빠르게 이해해야 합니다.

현재 화면은 판단 엔진의 내부 상태를 그대로 노출하는 비중이 높아, 실제 업무 판단 화면으로 보기 어렵습니다.

현재 확인된 문제는 다음과 같습니다.

- `실행 이력`을 클릭해도 선택된 실행 결과가 바뀌었다는 시각 피드백이 약합니다.
- 클릭 후 상세 결과 영역으로 이동하지 않아 사용자가 아무 반응이 없다고 느낄 수 있습니다.
- `citation candidate_found`처럼 개발자/엔진용 상태값이 사용자 화면에 그대로 보입니다.
- `보유 정보와 일치하는 후보가 있습니다. 기준문서 citation과 원문을 검토해 확정하세요.` 같은 문장은 실제 업무자가 무엇을 해야 하는지 바로 이해하기 어렵습니다.
- `필요 서류 후보`, `면허/등록/허가증`이 따로 떨어져 보여, 어떤 조건 때문에 어떤 서류가 필요한지 연결이 약합니다.
- `준비 확인`, `확인 필요` 같은 상태가 한 화면에서 무엇을 의미하는지 명확하지 않습니다.
- Gemini API를 써야 할 “사람이 읽기 쉬운 요약, 부족 사유 정리, 다음 액션 정리”가 현재 판단 검토 화면에는 충분히 반영되어 있지 않습니다.

## 2. UX 목표

판단 검토 화면은 사용자가 10초 안에 다음 질문에 답할 수 있어야 합니다.

1. 이 공고는 현재 법인 기준으로 바로 준비 가능한가?
2. 부족한 조건은 몇 개이고, 가장 중요한 부족 항목은 무엇인가?
3. 어떤 서류를 준비하거나 업로드해야 하는가?
4. 기준문서 근거는 충분한가, 아니면 사람이 확인해야 하는가?
5. 검토 완료로 저장하려면 무엇을 확인해야 하는가?

## 3. 새 화면 구조 제안

### 3.1 상단 실행 영역

상단은 새 판단 실행에만 집중합니다.

구성:

- 저장 공고 선택
- 법인 선택
- `판단 검토 실행` 버튼
- 마지막 실행 시각
- 기준문서 상태 요약

권장 문구:

```text
공고와 법인을 선택하면 부족 조건, 필요한 증빙자료, 기준문서 근거를 한 번에 정리합니다.
```

기존의 “확정 판정이 아닙니다” 문구는 남기되, 화면 전체를 위축시키는 안내가 아니라 작은 보조 설명으로 배치합니다.

### 3.2 판단 요약 카드

실행 결과의 첫 화면은 숫자보다 결론 요약이 먼저 나와야 합니다.

구성:

- 큰 상태 라벨
  - `보강 필요`
  - `확인 필요`
  - `대체로 준비됨`
  - `검토 불가`
- 한 줄 요약
  - 예: `현재 법인 정보 기준으로 3개 조건은 보강이 필요하고, 2개 조건은 기준문서 근거 확인이 필요합니다.`
- 핵심 숫자
  - 준비 확인
  - 보강 필요
  - 사람 확인 필요
  - 기준문서 근거 확인률
- Gemini 요약
  - 사용자가 바로 읽을 수 있는 3~5문장 요약
  - 엔진 내부 용어 사용 금지

예시:

```text
판단 요약
보강 필요

현재 법인 정보에서는 공고 참가에 필요한 면허/등록 증빙이 충분히 확인되지 않았습니다.
직접생산, 인증, 제출서류 조건은 일부 근거가 있으나 기준문서 원문 확인이 필요합니다.
먼저 면허/등록/허가증과 관련 인증서를 업로드하고, 추출 후보를 승인하세요.
```

### 3.3 우선 준비 항목

사용자가 가장 먼저 볼 영역입니다. “부족한 조건”을 업무 행동으로 바꿔 보여줍니다.

그룹:

- 면허/등록/허가
- 인증/기업유형
- 직접생산/제품·기술 조건
- 제출서류
- 법인 기본정보 보강
- 기준문서 근거 확인

각 항목 표시:

```text
[보강 필요] 면허/등록/허가증
왜 필요한가: 공고 요구조건에 면허 또는 등록 확인이 포함되어 있습니다.
현재 상태: 승인된 법인 증빙에서 해당 면허를 찾지 못했습니다.
다음 행동: 증빙 업로드 메뉴에서 면허/등록/허가증 PDF를 업로드하고 추출 후보를 승인하세요.
관련 조건: 공고 참가자격 / 면허 조건
```

### 3.4 부족조건 상세

현재의 4열 카드 그리드는 조건이 많아질수록 읽기 어렵습니다. 상세 영역은 목록형 카드로 바꾸는 것이 좋습니다.

카드 구성:

- 상태 배지
  - `보강 필요`
  - `사람 확인 필요`
  - `준비 확인`
  - `적용 제외`
- 조건명
- 공고 요구 내용
- 현재 보유 정보
- 부족한 점
- 다음 행동
- 필요한 서류
- 기준문서 근거 요약
- 원문 보기 버튼

예시:

```text
[보강 필요] 면허/등록/허가 조건

공고 요구 내용
입찰 참가자는 관련 법령에 따른 면허 또는 등록을 보유해야 합니다.

현재 보유 정보
승인된 법인 증빙에서 해당 면허/등록 정보를 찾지 못했습니다.

다음 행동
면허증, 등록증, 허가증 중 해당 서류를 업로드하고 자동 추출 후보를 승인하세요.

기준문서 근거
검토 가능한 근거가 2건 있습니다. 가장 높은 근거는 기준문서 125쪽의 직접생산 확인 기준입니다.
```

### 3.5 기준문서 근거 영역

기준문서 근거는 중요하지만, 첫 화면에 내부 ID와 점수를 그대로 노출하면 이해가 어렵습니다.

기본은 접은 상태로 두고, 사용자가 필요할 때 펼치게 합니다.

상태 문구 매핑:

| 현재 내부값 | 사용자 화면 문구 |
|---|---|
| `candidate_found` | `검토 가능한 근거 있음` |
| `weak_candidate` | `근거 신뢰 낮음` |
| `missing` | `기준문서 근거 없음` |
| `approved_rule_candidate` | `승인된 기준문구 근거` |
| `basis_search` | `검색된 기준문서 근거` |

근거 표시 예시:

```text
검토 가능한 근거 있음
기준문서: 중소기업자간 경쟁제품 직접생산 확인기준
위치: 125쪽 / 제3장 직접생산 확인 기준
요약: 해당 제품군은 직접생산 확인 기준과 생산설비 요건을 함께 검토해야 합니다.
[원문 펼치기]
```

금지할 화면 문구:

- `citation candidate_found`
- `weak_candidate`
- `basis_search_fallback_used`
- `review_ready`
- `candidate_found`
- `matched`, `missing`, `needs_review` 원문

### 3.6 실행 이력

현재 `실행 이력`은 클릭해도 반응이 약합니다. 실행 이력은 “선택 가능한 리스트”임을 명확히 보여야 합니다.

개선안:

- 선택된 이력에 `선택됨` 배지와 좌측 강조선 표시
- 클릭 시 상세 결과 영역으로 자동 스크롤
- 클릭 시 상단 제목이 해당 공고/법인으로 즉시 변경
- 이력 카드에 날짜, 법인, 보강 필요 수, 확인 필요 수 표시
- 상태 필터 제공
  - 전체
  - 보강 필요
  - 확인 필요
  - 검토 완료

이력 카드 예시:

```text
[선택됨] 2026-06-14 15:22
공고: 실내 안내판 제작 설치 용역
법인: 시연 법인
보강 필요 3개 · 사람 확인 2개 · 근거 확인률 68%
```

### 3.7 검토 저장 영역

검토 상태 저장은 화면 중간에 일반 폼처럼 두기보다, 결과 확인 후 마지막에 배치하는 것이 좋습니다.

상태 라벨:

| 현재 값 | 새 화면 문구 |
|---|---|
| `pending` | `검토 전` |
| `reviewed` | `검토 완료` |
| `needs_followup` | `보강 필요` |
| `archived` | `보관` |

저장 버튼:

```text
검토 결과 저장
```

메모 placeholder:

```text
예: 면허증 업로드 후 다시 판단 검토 실행 필요
```

## 4. Gemini API 활용 제안

판단 엔진은 규칙 기반으로 부족조건을 만들고, Gemini는 그 결과를 사람이 이해하기 쉬운 설명으로 정리하는 역할을 맡습니다.

중요 원칙:

- Gemini가 새로운 사실을 만들어내면 안 됩니다.
- Gemini는 이미 계산된 `match_status`, `gap_reason`, `required_evidence_types`, `citation_candidates`, `source_text`만 바탕으로 요약합니다.
- Gemini 결과는 “사용자 설명용”이며, 원본 판단 데이터는 그대로 보존합니다.
- Gemini 호출 실패 시 기존 규칙 기반 문구로 fallback합니다.

### 4.1 백엔드 추가 함수

권장 함수:

```text
build_judgment_user_summary_with_ai(judgment_result, notice, corporation, selection)
```

실행 위치:

- `build_judgment_run()`에서 결정론적 판단 결과 생성
- 그 다음 Gemini로 사용자용 요약 생성
- 결과를 `result.user_summary`에 저장
- 실패 시 `result.user_summary`를 deterministic fallback으로 생성

### 4.2 Gemini 출력 JSON 스키마

```json
{
  "headline_status": "보강 필요",
  "plain_summary": "현재 법인 정보에서는 면허/등록 증빙이 부족합니다...",
  "top_priority_actions": [
    {
      "title": "면허/등록/허가증 업로드",
      "reason": "공고 참가자격 조건에 해당 증빙이 필요합니다.",
      "next_step": "증빙 업로드 메뉴에서 관련 PDF를 업로드하고 후보를 승인하세요.",
      "related_requirement_ids": ["..."],
      "documents": ["면허/등록/허가증"]
    }
  ],
  "missing_groups": [
    {
      "group": "면허/등록/허가",
      "count": 1,
      "summary": "승인된 법인 증빙에서 해당 면허 정보를 찾지 못했습니다."
    }
  ],
  "item_explanations": {
    "requirement_input_id": {
      "user_gap_summary": "해당 면허 보유 여부가 확인되지 않았습니다.",
      "next_action": "면허증 또는 등록증을 업로드하세요.",
      "evidence_hint": "면허/등록/허가증",
      "citation_summary": "검토 가능한 기준문서 근거가 있습니다."
    }
  },
  "risk_notes": [
    "기준문서 근거가 없는 항목은 검토 완료 전 원문 확인이 필요합니다."
  ]
}
```

## 5. 상태/문구 사전

### 5.1 판단 상태

| 내부값 | 사용자 문구 | 설명 |
|---|---|---|
| `matched` | `준비 확인` | 현재 법인 정보와 승인된 증빙 기준으로 조건을 충족한 것으로 보이는 항목 |
| `missing` | `보강 필요` | 현재 정보에서 충족 근거를 찾지 못한 항목 |
| `uncertain` | `사람 확인 필요` | 자동 판단만으로 결론을 내리기 어려운 항목 |
| `needs_review` | `사람 확인 필요` | 원문 또는 증빙 확인이 필요한 항목 |
| `not_applicable` | `적용 제외` | 현재 판단 대상에는 적용되지 않는 항목 |

### 5.2 기준문서 근거 상태

| 내부값 | 사용자 문구 | 설명 |
|---|---|---|
| `candidate_found` | `검토 가능한 근거 있음` | 기준문서 원문 후보가 충분한 점수로 검색됨 |
| `weak_candidate` | `근거 신뢰 낮음` | 후보는 있지만 점수가 낮아 원문 확인 필요 |
| `missing` | `기준문서 근거 없음` | 현재 기준문서 인덱스에서 적절한 근거를 찾지 못함 |

## 6. 구현 단계 제안

### Step 1. 즉시 UX 문구 정리

- 프론트에서 내부 상태값 직접 노출 제거
- `citation candidate_found`를 사용자 문구로 변환
- `status_label`, `citation_status`, `review_status` 모두 label mapper 적용
- 기존 `recommended_action` 문구를 더 명확한 한국어 문장으로 교체
- 실행 이력 선택 상태 표시
- 실행 이력 클릭 시 상세 결과 영역으로 스크롤

### Step 2. 화면 레이아웃 재구성

- 상단 `판단 요약` 카드 추가
- `우선 준비 항목` 섹션 추가
- `부족조건 상세` 목록형 카드로 변경
- 기준문서 근거는 접힘/펼침 구조로 변경
- 검토 저장 영역은 결과 하단으로 이동

### Step 3. Gemini 사용자 요약 추가

- 백엔드에 Gemini 기반 사용자 요약 함수 추가
- `result.user_summary` 저장
- Gemini 실패 시 deterministic fallback 생성
- 프론트는 `user_summary`를 우선 표시하고, 없으면 기존 결과로 요약 생성

### Step 4. 테스트 보강

- 프론트 계약 테스트
  - `citation candidate_found`, `weak_candidate`, `review_ready` 등 내부 문구가 화면에 노출되지 않는지 검증
  - 실행 이력 클릭 시 `active` class와 상세 영역 ref/scroll 코드가 존재하는지 검증
  - `Gemini 요약` 또는 fallback 요약 섹션이 렌더링되는지 검증
- 백엔드 테스트
  - Gemini 미설정 환경에서도 judgment run 생성이 실패하지 않는지 검증
  - AI 요약 실패 시 fallback user summary가 저장되는지 검증
  - `result.user_summary` 스키마 검증
- 브라우저 UX 테스트
  - 판단 실행
  - 실행 이력 클릭
  - 부족조건 상세 확인
  - 기준문서 근거 펼치기
  - 검토 상태 저장

## 7. 완료 기준

이 UX 개선은 다음 조건을 만족해야 완료로 봅니다.

- `판단 검토` 화면 첫 화면에서 `보강 필요`, `사람 확인 필요`, `준비 확인` 개수를 바로 이해할 수 있습니다.
- 사용자가 가장 먼저 준비해야 할 서류와 행동을 3개 이내 우선순위로 볼 수 있습니다.
- `citation candidate_found` 같은 내부 상태값이 화면에 노출되지 않습니다.
- 기준문서 근거는 문서명, 페이지, 섹션, 원문 요약 중심으로 표시됩니다.
- 실행 이력을 클릭하면 선택 표시가 바뀌고 상세 결과로 이동합니다.
- Gemini API가 설정되어 있으면 사용자용 판단 요약을 생성합니다.
- Gemini API가 없거나 실패해도 판단 검토 실행은 실패하지 않고 fallback 요약을 표시합니다.

## 8. Questions for Product Owner

- 화면 최상단의 큰 상태 라벨은 `보강 필요`, `확인 필요`, `대체로 준비됨` 중 어떤 표현을 우선 사용할지 확정이 필요합니다.
- “지원 가능/불가능” 표현은 계속 피하고, “준비 상태/보강 필요” 중심으로 유지하는 것이 맞는지 확인이 필요합니다.
- Gemini 요약을 매 실행마다 생성할지, 사용자가 `AI로 정리` 버튼을 눌렀을 때만 생성할지 결정이 필요합니다.

## 9. 구현 반영 업데이트 - 부족조건 미리보기와 판단 검토 모달 UX

2026-06-14 구현에서는 `판단 검토`만이 아니라 `부족조건 미리보기`도 같은 원칙으로 정리했습니다.

### 9.1 메인 화면 정보량 축소

두 화면 모두 첫 화면에는 다음 정보만 남깁니다.

- 실행 대상 선택
- 실행 버튼
- 사용자용 요약 카드
- 우선 준비 항목
- `이력 보기`, `결과 자세히 보기`, `근거 보기`로 연결되는 액션

최근 이력, 조건별 전체 상세, 법인 프로필, 공고 요구조건 후보, 기준문서 근거 원문은 페이지 하단에 길게 펼치지 않고 모달에서 확인합니다.

### 9.2 Gemini 사용자 요약 정책

백엔드는 비교/판단 결과 생성 후 `result.user_summary`를 저장합니다.

공통 구조:

```json
{
  "headline_status": "보강 필요",
  "plain_summary": "사람이 바로 이해할 수 있는 요약",
  "top_priority_actions": [],
  "missing_groups": [],
  "item_explanations": {},
  "risk_notes": [],
  "evidence_links": [],
  "generated_by": "gemini | fallback"
}
```

운영 원칙:

- Gemini는 판단을 새로 내리지 않습니다.
- Gemini는 이미 계산된 비교/판단 결과를 쉬운 한국어로 재정리합니다.
- Gemini 미설정 또는 호출 실패 시 `generated_by: fallback` 요약을 저장합니다.
- fallback이어도 화면은 항상 동작해야 합니다.

### 9.3 근거 링크 정책

사용자 화면에는 내부 ID보다 “어떤 근거를 확인하는지”가 먼저 보여야 합니다.

지원 링크:

- `증빙서류 보기`: 법인 증빙 문서의 파일명, 문서유형, 추출 텍스트, 승인 후보 확인
- `기준문서 근거 보기`: 기준문서명, 버전, 페이지, 섹션, 청크 원문 확인
- `공고 요구조건 보기`: 공고 요구조건 후보의 원문 문장과 추출값 확인

근거 링크는 새 페이지 이동이 아니라 현재 화면의 모달에서 열립니다.

### 9.4 추가 API 계약

- `GET /api/basis-documents/{basis_document_id}/chunks/{chunk_id}`
  - 기준문서 청크 원문과 기준문서 메타데이터를 반환합니다.
- `GET /api/notice-requirements/{requirement_candidate_id}`
  - 공고 요구조건 후보 원문과 저장 공고 메타데이터를 반환합니다.
- `GET /api/corporation-evidence-documents/{id}`
  - 기존 증빙 상세 API를 근거 모달에서 재사용합니다.

### 9.5 회귀 방지 테스트 기준

- Gemini 미설정 상태에서도 비교/판단 실행은 성공해야 합니다.
- Gemini mock 응답은 `user_summary`에 저장되어야 합니다.
- 근거 상세 API는 존재하지 않는 ID에 대해 404를 반환해야 합니다.
- `candidate_found`, `weak_candidate`, `review_ready` 같은 내부 상태값은 사용자 페이지 소스에 직접 노출하지 않습니다.
- `demo-comparison-history-modal`, `demo-comparison-detail-modal`, `demo-comparison-evidence-modal`, `demo-judgment-history-modal`, `demo-judgment-detail-modal`, `demo-judgment-evidence-modal` selector를 유지합니다.

---

# AI / Engineering Version (English)

## Objective

Redesign the `JudgmentRunsPage` because it is the core product workflow. The page must communicate missing requirements, required evidence, next actions, and basis-document support in plain stakeholder-facing language.

## Current Problems

- Run history selection has weak feedback and does not scroll/focus the selected result.
- Engine/internal labels leak into the UI, especially `citation candidate_found`.
- Current action text is generic and difficult to understand.
- Required documents are displayed as a disconnected flat list.
- The UI does not sufficiently use Gemini to produce user-facing explanations from deterministic judgment outputs.

## Proposed Information Architecture

1. Execution controls
   - notice selector
   - corporation selector
   - run button
   - basis index status

2. Judgment summary
   - headline status: `보강 필요`, `확인 필요`, `대체로 준비됨`, or `검토 불가`
   - plain Korean summary
   - core counts
   - Gemini-generated explanation when available

3. Priority preparation actions
   - grouped by license/registration/permit, certification/company type, direct production/product/technology, submitted documents, corporation profile gaps, and basis evidence review

4. Requirement details
   - list-style cards rather than dense four-column panels
   - each card shows requirement source, current evidence, gap, next action, required documents, and basis evidence summary

5. Basis evidence
   - collapsed by default
   - show document title, page, section, plain evidence status, and source preview
   - never expose raw internal statuses

6. Run history
   - active selected state
   - click scrolls/focuses result detail
   - filters by review status

7. Review save area
   - placed after result review
   - labels mapped to user-facing Korean terms

## Status Label Mapping

Judgment:

- `matched` -> `준비 확인`
- `missing` -> `보강 필요`
- `uncertain` -> `사람 확인 필요`
- `needs_review` -> `사람 확인 필요`
- `not_applicable` -> `적용 제외`

Citation:

- `candidate_found` -> `검토 가능한 근거 있음`
- `weak_candidate` -> `근거 신뢰 낮음`
- `missing` -> `기준문서 근거 없음`

Review:

- `pending` -> `검토 전`
- `reviewed` -> `검토 완료`
- `needs_followup` -> `보강 필요`
- `archived` -> `보관`

## Gemini Integration

Add a backend helper after deterministic judgment generation:

```text
build_judgment_user_summary_with_ai(judgment_result, notice, corporation, selection)
```

The AI must not create new facts. It only rewrites deterministic result data into user-facing summaries and action guidance.

Store the output under:

```text
result.user_summary
```

Fallback to deterministic summary generation if Gemini is not configured or fails.

## Implementation Steps

1. Clean labels and immediate interaction issues.
2. Rebuild the page layout around summary, priority actions, detailed gaps, and evidence.
3. Add Gemini user summary generation and fallback.
4. Add frontend/backend tests and browser UX checks.

## Acceptance Criteria

- No raw status labels such as `candidate_found`, `weak_candidate`, or `review_ready` are visible.
- Users can understand the top missing requirements within 10 seconds.
- Run-history click visibly selects a run and scrolls/focuses the detail area.
- Gemini summary is shown when configured; deterministic fallback is shown otherwise.
- Basis evidence is shown as document/page/section/source preview, not internal citation metadata.

## Implementation Update - Modal Summary UX

The implemented scope now covers both `NoticeComparisonPage` and `JudgmentRunsPage`.

- Main pages are summary-first and avoid rendering long histories/details inline.
- Histories, detail results, notice requirements, corporation profiles, and evidence source text open in modal dialogs.
- Backend comparison and judgment outputs store `user_summary`.
- Gemini rewrites deterministic result data into stakeholder-facing Korean summaries only; it does not create new judgment facts.
- Deterministic fallback summaries are stored when Gemini is not configured or fails.
- Evidence links are normalized across corporation evidence documents, basis chunks, and notice requirement candidates.

Additional API contracts:

- `GET /api/basis-documents/{basis_document_id}/chunks/{chunk_id}`
- `GET /api/notice-requirements/{requirement_candidate_id}`
- existing `GET /api/corporation-evidence-documents/{id}`

Regression coverage should assert fallback summaries, mocked Gemini summaries, evidence detail API 404 handling, modal selectors, and absence of raw internal status labels in user-facing page source.
