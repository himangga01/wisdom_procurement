# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`의 핵심 확장 기능인 `법인 사업자 대 공고문 부족조건/준비 상태 판단`을 구현하기 위한 상세 계획서입니다.

핵심 제품 가정은 다음입니다.

- 대부분의 사업자는 특정 공고문에 바로 대응할 준비가 끝난 상태가 아니다.
- 따라서 단순한 확정 판정보다, `왜 지금은 어려운지`, `무엇이 부족한지`, `지원하려면 무엇을 준비해야 하는지`를 알려주는 것이 더 중요하다.
- 판단 결과는 반드시 공고문 내용, 기준문서 조항, 법인 입력 정보, 보유 증빙자료를 근거로 설명해야 한다.
- 근거가 부족한 경우 `불가능`으로 단정하지 않고 `검토 필요`와 `추가 확인 필요 항목`으로 분리한다.

## 구현 단계 위치

### Phase 1.6
- Phase 2 전에 법인 증빙자료 자동 추출 기반을 먼저 구현한다.
- 법인 프로필 입력 필드 확장
- 법인 증빙자료 관리
- 증빙자료 업로드/자동 추출/자동 분류
- 알 수 없는 증빙자료 LLM 분류 fallback
- 사용자 확인 후 법인 프로필 업데이트
- 상세 증빙자료 taxonomy와 구현 계획은 `docs/corporation-evidence-auto-extraction-plan.md`를 따른다.

### Phase 2
- 기준문서 관리
- 기준 PDF 자동 텍스트 추출, OCR, 정규화, 청킹
- 로컬 벡터 인덱싱
- 기준문서 검색 준비
- 최종 판단 결과는 아직 제공하지 않음

### Phase 2.5 권장
- 공고 요구조건 구조화 추출 고도화
- 기준문서에서 조건/제출서류/예외 규칙을 검색하는 내부 API 준비
- 내부 검토용 `요건 대비 보유정보 매트릭스` 제공

### Phase 3
- 법인 대 공고 부족조건/준비 상태 판단
- 부족 조건 분석
- 준비 필요 인증/면허/서류 출력
- 근거 조항 citation 출력
- 준비 체크리스트와 준비 가이드 생성

## 핵심 판단 흐름
```text
법인 프로필
  + 법인 증빙자료
  + 나라장터 공고 메타데이터
  + 공고문/첨부 PDF 분석 결과
  + 기준문서 RAG 검색 결과
    -> 요구조건 추출
    -> 법인 보유 조건과 매칭
    -> 부족 항목 산출
    -> 준비 가이드 생성
    -> 근거 조항과 불확실성 표시
```

## 결과 상태 정의
최종 화면은 낙관적인 확정 판정 중심이 아니라 `부족조건과 준비 상태` 중심이어야 합니다.

- `matched`: 법인 입력/증빙과 공고 요구조건이 현재 데이터 기준으로 일치함
- `missing`: 필요한 면허, 인증, 지역, 기업유형, 실적, 금액 조건, 제출서류 중 하나 이상이 부족함
- `uncertain`: 자동 비교만으로 판단하기 어려움
- `needs_review`: 공고문, 기준문서, 법인 입력 정보, 증빙자료 중 사람이 확인해야 할 부분이 있음
- `not_applicable`: 해당 조건이 현재 법인 또는 공고에는 적용되지 않음
- `citation_missing`: 기준문서 citation이 없어 확정 근거로 사용할 수 없음

권장 기본값은 `needs_review`입니다. 시스템이 근거 없이 확정 판정을 쉽게 출력하면 안 됩니다.

## 법인 사업자 입력 필드 추가 검토

### 설계 원칙
- 법인 입력값은 판단 엔진의 `사실 데이터`로 사용된다.
- 사용자가 잘 모르는 항목은 빈 값으로 둘 수 있어야 한다.
- 입력값마다 `확인됨/미확인`, `유효기간`, `증빙자료 연결`을 둘 수 있어야 한다.
- 자유 텍스트만으로 판단하지 않고, 가능한 항목은 구조화 필드로 받는다.
- 법인 정보와 법인 증빙자료는 분리하되 서로 연결할 수 있어야 한다.
- 법인 등록 UX는 수동 입력 폼이 아니라 `증빙자료 업로드 -> 자동 추출 -> 사용자 확인` 흐름을 기본값으로 둔다.
- 첫 진입 시 사업자등록증 업로드를 우선 요청하고, 사용자가 `사업자등록증 없음`을 선택한 경우에만 직접 입력 폼을 제공한다.

### 필수에 가까운 기본 필드
| 필드 | 목적 | 비고 |
|---|---|---|
| 법인명 | 표시/검색 | 기존 필드 유지 |
| 사업자등록번호 | 업체 식별 | 개인정보/민감정보 취급 주의, 화면 마스킹 검토 |
| 법인등록번호 | 법인 식별 | 선택 필드로 시작 권장 |
| 대표자명 | 일부 서류/증빙 확인 | 선택 필드 |
| 본점 소재지 | 지역 제한 판단 | 시/도, 시/군/구 분리 권장 |
| 지점/사업장 소재지 | 지역 제한 예외 판단 | 다중 입력 가능 구조 |
| 업종/사업분야 | 공고 업종 조건 비교 | 자유 텍스트 + 표준 태그 병행 |
| 회사 규모 | 중소기업/소기업/소상공인 등 | 확인서 유효기간 필요 |
| 내부 메모 | 행정사 실무 메모 | 기존 필드 유지 |

### 자격/면허/인증 필드
이 영역은 부족조건/준비 상태 판단의 핵심입니다.

| 필드 | 예시 | 판단 활용 |
|---|---|---|
| 면허/등록명 | 조경식재공사업, 정보통신공사업 등 | 공고 참가자격 매칭 |
| 면허/등록번호 | 등록증 번호 | 증빙자료 확인 |
| 발급/등록기관 | 지자체, 협회, 중앙부처 등 | 근거 신뢰도 |
| 취득일 | 2024-01-01 | 실적/유효성 참고 |
| 만료일 | 2027-01-01 | 유효기간 판단 |
| 상태 | 보유, 준비중, 만료, 확인필요 | 부족 조건 산출 |
| 증빙자료 연결 | 등록증 PDF 등 | citation/확인 근거 |

### 조달/입찰 관련 필드
| 필드 | 목적 |
|---|---|
| 나라장터 경쟁입찰참가자격 등록 여부 | 나라장터 입찰 기본 자격 확인 |
| 조달업체 등록번호 | 향후 API/서류 연동 여지 |
| 입찰참가 제한/제재 여부 | 결격 사유 판단 |
| 공동수급 가능 여부 | 단독 불가 시 대안 안내 |
| 하도급/협력사 활용 가능 여부 | 준비 가이드 참고 |

### 기업유형/우대/제한 관련 필드
| 필드 | 예시 |
|---|---|
| 중소기업확인서 | 중기업, 소기업, 소상공인 |
| 여성기업 확인 | 여성기업 확인서 |
| 장애인기업 확인 | 장애인기업 확인서 |
| 사회적기업/협동조합 | 인증서 |
| 벤처기업/창업기업 | 벤처확인서, 창업기업 확인 |
| 직접생산확인증명서 | 물품/용역 공고 확장 시 중요 |

각 항목은 단순 체크박스가 아니라 `보유 여부`, `유효기간`, `증빙자료`, `메모`를 함께 저장해야 합니다.

### 저입력 법인 등록 UX 원칙
법인 등록은 최대한 `직접 입력`이 아니라 `선택`, `체크`, `업로드 후 자동 추출` 중심으로 구성합니다.

입력 방식 우선순위:

1. 증빙자료 업로드 후 자동 추출
2. 체크박스/토글
3. 검색형 드롭다운
4. 날짜 선택기
5. 숫자 입력
6. 자유 텍스트 입력

자유 텍스트는 내부 메모, 기타 항목, 자동 추출 실패 시 보정 정도에만 제한적으로 사용합니다.

### 증빙자료 우선 법인 등록 UX
법인 등록의 첫 화면은 일반 입력 폼이 아니라 `사업자등록증 업로드` 화면으로 시작합니다.

첫 화면 구성:

```text
법인 등록을 시작하려면 사업자등록증을 업로드해주세요.
시스템이 법인명, 사업자등록번호, 대표자명, 사업장 주소, 업태/종목을 자동으로 추출합니다.

[사업자등록증 업로드]
[사업자등록증이 없어요 / 나중에 입력할게요]
```

사용자 흐름:

1. 사용자가 사업자등록증 파일을 업로드한다.
2. 시스템이 이미지/PDF/Word 파일을 읽어 텍스트를 추출한다.
3. 사업자등록증 문서 유형인지 자동 분류한다.
4. 법인 기본정보 후보를 구조화해서 추출한다.
5. 사용자는 추출 결과를 확인하고 틀린 값만 수정한다.
6. 확인된 값으로 법인 프로필을 생성한다.
7. 이후 면허/인증/기업유형/실적 증빙자료를 추가 업로드하도록 안내한다.

사업자등록증에서 자동 추출할 후보:

- 법인명 또는 상호
- 사업자등록번호
- 대표자명
- 개업연월일
- 법인등록번호가 문서에 있는 경우
- 사업장 소재지
- 본점/사업장 주소의 시/도, 시/군/구
- 업태
- 종목
- 발급일 또는 문서 출력일

지원 파일 형식 권장:

- PDF
- DOCX
- JPG/JPEG
- PNG
- 추후 필요 시 DOC는 LibreOffice 변환 또는 별도 변환기를 통해 지원 검토

`사업자등록증 없음` 선택 시:

- 최소 직접 입력 폼을 표시한다.
- 직접 입력 필드는 법인명, 본점 지역, 대표 업종/사업분야만 우선 요청한다.
- 사업자등록번호, 대표자명, 상세 주소는 선택 입력으로 둔다.
- 화면 상단에 `사업자등록증을 나중에 업로드하면 정보가 자동 보강됩니다.` 안내를 표시한다.
- 수동 입력으로 만든 법인은 `증빙자료 없음` 또는 `기본정보 미검증` 상태로 표시한다.

자동 추출 결과 확인 UX:

- 원본 문서 미리보기와 추출 결과를 좌우로 배치한다.
- 추출된 필드는 신뢰도에 따라 표시한다.
  - 높음: 바로 채움
  - 중간: 노란색 `확인 필요`
  - 낮음: 빈 값 또는 추천값으로 표시
- 사용자는 전체를 다시 입력하지 않고 틀린 값만 수정한다.
- `확인 후 법인 생성` 버튼을 눌러야 프로필에 확정 반영한다.

자동 추출 파이프라인:

```text
upload_evidence
  -> detect_file_type
  -> extract_text_or_ocr
  -> classify_document_type
  -> extract_business_registration_fields
  -> normalize_registration_number_and_address
  -> return_review_candidates
  -> user_confirm
  -> create_or_update_corporation_profile
```

추출 상태값:

- `uploaded`
- `extracting`
- `ocr_processing`
- `classifying`
- `field_extracted`
- `needs_review`
- `confirmed`
- `failed`

이 흐름은 사업자등록증뿐 아니라 면허/등록증, 중소기업확인서, 실적증명서, 신용평가서에도 동일한 패턴으로 확장합니다.

### 기업유형/우대조건 UX
기업유형과 우대조건은 직접 입력이 아니라 체크박스 카드 또는 토글 카드로 받습니다.

권장 UI:

```text
[ ] 중소기업확인서
    - 세부유형: 드롭다운(중기업/소기업/소상공인/확인필요)
    - 만료일: 날짜 선택
    - 증빙자료: 파일 연결 또는 업로드

[ ] 여성기업
    - 만료일: 날짜 선택
    - 증빙자료: 파일 연결 또는 업로드

[ ] 장애인기업
[ ] 사회적기업
[ ] 협동조합
[ ] 벤처기업
[ ] 창업기업
[ ] 직접생산확인증명서
```

각 체크박스는 선택하면 필요한 세부 필드만 펼쳐집니다. 선택하지 않은 항목은 접힌 상태로 두어 화면 부담을 줄입니다.

상태값:

- `보유`
- `준비중`
- `보유하지 않음`
- `확인 필요`

기본값은 `확인 필요`입니다. 사용자가 모르는 항목을 억지로 입력하게 만들지 않습니다.

### 면허/인증 UX
면허/인증은 텍스트 직접 입력보다 `검색형 드롭다운 + 직접 추가` 방식을 권장합니다.

권장 UI:

- 업종/면허 검색 입력
- 자주 쓰는 면허 빠른 선택 칩
- 선택한 면허 리스트
- 각 면허별 상태, 취득일, 만료일, 증빙자료 연결

빠른 선택 칩 예시:

- 조경식재공사업
- 산림사업법인
- 정보통신공사업
- 전기공사업
- 소프트웨어사업자
- 직접생산확인

목록에 없는 면허는 `직접 추가`로 입력하되, 이후 자동완성 후보로 재사용할 수 있게 합니다.

### 실적/인력/장비 UX
실적/인력/장비는 처음부터 상세 입력을 강제하지 않습니다.

권장 방식:

- `없음`
- `있음`
- `확인 필요`

중 하나를 먼저 선택하게 하고, `있음`을 선택한 경우에만 상세 입력을 펼칩니다.

실적은 직접 입력보다 실적증명서 업로드를 우선합니다.

업로드 후 시스템이 추출할 후보:

- 발주처
- 사업명
- 계약기간
- 계약금액
- 수행 분야
- 증빙 문서명

사용자는 추출 결과를 확인/수정만 합니다.

### 법인 등록 추천 흐름
처음 등록 시에는 사용자가 직접 최소 정보를 입력하는 방식보다 `사업자등록증 업로드`를 우선합니다.

1단계 기본 흐름:

- 사업자등록증 업로드
- 이미지/PDF/Word 텍스트 추출
- 법인 기본정보 자동 추출
- 사용자가 추출 결과 확인

2단계 예외 흐름:

- 사용자가 `사업자등록증 없음` 선택
- 최소 직접 입력 폼 제공
- 법인명, 본점 지역, 대표 업종/사업분야만 우선 입력
- 나머지는 선택 입력 또는 추후 보강

3단계 빠른 체크:

- 보유한 기업유형/우대조건 체크
- 보유한 면허/인증 선택

4단계 증빙자료 업로드:

- 사업자등록증
- 면허/인증서
- 중소기업확인서 등

5단계 자동 보강:

- 업로드 자료에서 만료일, 발급기관, 인증명 후보 추출
- 사용자는 추출 결과를 확인만 함

### 법인 준비도 표시
법인 상세 화면에는 입력 완료율이 아니라 `판단 준비도`를 표시합니다.

예시:

```text
공고 판단 준비도 62%
- 기본정보: 충분
- 면허/인증: 증빙 2건 필요
- 기업유형: 중소기업확인서 만료일 확인 필요
- 실적: 정보 없음
- 제재 여부: 확인 필요
```

이렇게 하면 사용자가 모든 필드를 채우는 것이 아니라, 판단에 필요한 부족 정보를 우선 보강할 수 있습니다.

### 실적/역량 관련 필드
| 필드 | 목적 |
|---|---|
| 최근 3년 유사 사업 실적 | 실적 제한 공고 대응 |
| 단일 계약 최대 실적 금액 | 금액 기준 비교 |
| 누적 실적 금액 | 총액 기준 비교 |
| 시공능력평가액 또는 수행능력 지표 | 공사/용역 공고 판단 |
| 보유 기술자/전문인력 | 인력 기준 공고 대응 |
| 장비 보유 현황 | 장비 요건 대응 |
| 신용평가등급 | 신용/재무 기준 대응 |
| 재무제표/매출 규모 | 규모 조건 대응 |

### 법인 증빙자료 모델 추가 권장
법인 프로필 필드만으로는 판단 신뢰도가 낮습니다. 따라서 `법인 증빙자료` 도메인을 추가하는 것이 좋습니다.

예상 테이블:

```text
corporation_evidence_documents
- id
- corporation_id
- evidence_type
- title
- original_file_name
- stored_file_path
- issue_date
- expiry_date
- issuer
- verification_status
- extracted_text_path
- parsed_metadata_json
- linked_profile_field
- memo
- created_at
- updated_at
```

권장 증빙자료 유형:

- 사업자등록증
- 법인등기부등본
- 면허/등록증
- 중소기업확인서
- 여성기업/장애인기업/사회적기업 등 확인서
- 직접생산확인증명서
- 실적증명서
- 신용평가서
- 기술자 보유 증빙
- 장비 보유 증빙
- 기타 내부 검토자료

## 법인 입력 UX 권장 구조
법인 등록 화면은 한 번에 모든 정보를 요구하면 사용성이 떨어집니다. 단계형 탭 구조를 권장합니다.

- 기본정보
- 소재지/지역
- 업종/면허/인증
- 기업유형/우대조건
- 실적/인력/장비
- 증빙자료
- 내부 메모

각 탭에는 `판단에 필요한 이유`를 짧게 안내합니다.

예시:

```text
면허/인증 정보는 공고의 참가자격 조건과 비교됩니다.
만료일이 지난 인증은 충족 조건으로 보지 않습니다.
```

## 기준문서 관리 설계 재검토

### 기준문서의 역할
기준문서는 일반 공고문과 다릅니다. 일반 공고문은 분석 대상이고, 기준문서는 판단 근거입니다.

기준문서는 다음 질문에 답하기 위한 지식 자산입니다.

- 이 공고의 참가 조건은 어떤 법령/규정/내부 기준과 연결되는가?
- 특정 면허/인증이 왜 필요한가?
- 어떤 서류가 필수 제출서류인가?
- 특정 조건을 충족하지 못하면 대체 가능성이 있는가?
- 부족한 조건을 준비하려면 어떤 절차가 필요한가?

### 기준문서 카테고리
| 카테고리 | 예시 | 활용 |
|---|---|---|
| 법령/규정 | 국가계약법, 지방계약법 관련 자료 | 결격/제한/절차 근거 |
| 조달청/나라장터 기준 | 입찰참가자격 등록, 전자입찰 기준 | 시스템/등록 조건 |
| 업종/면허 기준 | 건설업, 정보통신, 산림/조경 등 | 참가자격 판단 |
| 기업유형 인증 기준 | 중소기업, 여성기업, 장애인기업 등 | 제한/우대 조건 |
| 제출서류 기준 | 입찰서류, 증빙서류 목록 | 체크리스트 생성 |
| 내부 검토 기준 | 행정사 내부 판단 기준 | 실무 판단 보조 |
| 준비 가이드 | 인증 취득 절차, 서류 발급 절차 | 부족 항목 안내 |

### 기준문서 메타데이터 확장
```text
basis_documents
- id
- title
- category
- subcategory
- issuing_organization
- jurisdiction
- version_label
- effective_date
- expiry_date
- source_url
- source_type
- legal_status
- priority
- tags_json
- original_file_name
- stored_file_path
- file_hash
- processing_status
- chunk_count
- rule_count
- active_version
- memo
- created_at
- updated_at
```

핵심 메타데이터 설명:

- `category`: 검색 필터와 판단 영역 분리
- `effective_date`, `expiry_date`: 기준문서 유효성 판단
- `legal_status`: 현행, 폐지, 참고, 내부 기준 등
- `priority`: 같은 조건에 여러 문서가 걸릴 때 우선순위 결정
- `active_version`: 현재 판단에 사용할 버전 여부
- `rule_count`: 추출된 판단 규칙 수

### 기준문서 처리 상태
```text
uploaded
extracting
ocr_required
ocr_processing
normalizing
chunking
extracting_rules
embedding
indexed
failed
```

### 기준문서 청크 메타데이터 확장
```text
basis_document_chunks
- id
- basis_document_id
- chunk_index
- chunk_text
- chunk_text_normalized
- page_start
- page_end
- section_title
- section_path
- clause_number
- rule_type
- topic_tags_json
- applies_to_json
- chunk_hash
- token_count
- embedding_model
- vector_id
- vector_status
- created_at
```

### 판단 규칙 추출 테이블 권장
청크 검색만으로도 RAG는 가능하지만, 부족조건/준비 상태 판단은 조건 비교가 필요합니다. 따라서 기준문서에서 구조화된 규칙을 별도 추출하는 것을 권장합니다.

```text
basis_rules
- id
- basis_document_id
- chunk_id
- rule_type
- requirement_name
- requirement_description
- condition_json
- required_evidence_json
- applies_to_json
- exception_json
- severity
- confidence
- citation_text
- page_start
- page_end
- created_at
- updated_at
```

`rule_type` 예시:

- `eligibility_requirement`
- `required_document`
- `exclusion_condition`
- `license_requirement`
- `region_requirement`
- `company_type_requirement`
- `experience_requirement`
- `financial_requirement`
- `preparation_step`

### 기준문서 관리 화면 재검토
기준문서 화면은 단순 파일 목록이 아니라 `판단 근거 관리 콘솔`이어야 합니다.

필요 화면:

- 기준문서 목록
- 기준문서 업로드
- 기준문서 상세
- 처리 상태/오류 상세
- 청크 미리보기
- 추출 규칙 목록
- 재처리
- 버전 비교
- 현재 사용 버전 지정

목록 컬럼:

- 문서명
- 카테고리
- 발행기관
- 버전
- 유효 시작일
- 현재 사용 여부
- 처리 상태
- 청크 수
- 규칙 수
- 최근 처리일

## 로컬 RAG 상세 구현계획

### RAG 적용이 적합한 이유
부족조건/준비 상태 판단은 단순 요약 문제가 아닙니다. 공고문 조건과 기준문서 근거를 함께 찾아야 합니다.

RAG가 필요한 이유:

- 기준문서가 많고 길다.
- 조건별 근거 조항을 매번 LLM 컨텍스트에 전부 넣을 수 없다.
- 판단 결과에 citation이 필요하다.
- 기준문서 버전과 카테고리 필터가 필요하다.
- 추후 내부 기준이 계속 추가된다.

### RAG가 하면 안 되는 일
RAG 자체가 최종 판단을 대신하면 안 됩니다.

역할 분리:

- RAG: 관련 근거 후보 검색
- Rule extractor: 공고/기준문서에서 조건 구조화
- Matcher: 법인 보유 정보와 요구조건 비교
- LLM: 사용자에게 이해하기 쉬운 설명과 준비 가이드 생성

### 권장 로컬 벡터 저장소
1차 권장: `Qdrant local`

이유:

- 로컬 단일 PC 운영 가능
- 메타데이터 필터링이 강함
- 문서 버전, 카테고리, 조항 유형, 유효기간 필터가 중요함
- Python 클라이언트 연동이 안정적임

대안: `Chroma`

- 초기 프로토타입은 단순함
- 별도 서비스 없이 빠르게 붙이기 쉬움
- 다만 메타데이터 필터/운영 안정성은 Qdrant 쪽이 더 적합

권장 결정:

- Phase 2 MVP: Qdrant local을 기본 목표로 설계
- 설치/운영 부담이 크면 Chroma persistent mode로 임시 구현 가능
- 인터페이스는 `VectorIndexService`로 추상화해 교체 가능하게 유지

### 임베딩 전략
권장 구조:

- 기준문서 청크마다 임베딩 생성
- 공고 요구조건마다 검색 쿼리 임베딩 생성
- 검색 시 metadata filter + vector similarity 병행
- 검색 결과는 반드시 chunk id와 citation 정보 포함

임베딩 모델 선택 기준:

- 한국어 문서 검색 품질
- 긴 조항 텍스트의 의미 보존
- 비용
- 로컬 단일 PC 운영에서 인덱스 재생성 속도

권장 구현:

- `embedding_provider`: `openai` 또는 `local`
- `embedding_model`: 환경변수로 관리
- 같은 청크 해시와 같은 임베딩 모델이면 재사용
- 모델 변경 시 전체 재인덱싱 가능해야 함

### 인덱스 컬렉션 설계
컬렉션명 예시:

```text
basis_chunks_v1
```

벡터 payload:

```json
{
  "chunk_id": "uuid",
  "basis_document_id": "uuid",
  "title": "입찰참가자격 기준",
  "category": "license_requirement",
  "subcategory": "construction",
  "version_label": "2026-01",
  "issuing_organization": "조달청",
  "effective_date": "2026-01-01",
  "legal_status": "active",
  "page_start": 12,
  "page_end": 13,
  "section_title": "입찰참가자격",
  "clause_number": "제4조",
  "rule_type": "eligibility_requirement",
  "topic_tags": ["면허", "지역제한", "입찰참가자격"]
}
```

### 기준문서 인입 파이프라인
```text
upload_basis_pdf
  -> save_original_file
  -> create_basis_document
  -> extract_text_by_page
  -> detect_ocr_need
  -> run_ocr_if_needed
  -> normalize_text
  -> detect_sections_and_clauses
  -> split_chunks
  -> extract_rules_optional
  -> create_embeddings
  -> upsert_vectors
  -> mark_indexed
```

### 청킹 전략
1차 분할:

- 페이지
- 제목
- 조항 번호
- 표 제목
- 항목 번호

2차 분할:

- 500~900 토큰
- 80~150 토큰 오버랩
- 하나의 조항이 너무 길면 조항 내부 항목 단위로 분할
- 표는 행 단위 의미가 깨지지 않도록 텍스트 정규화 후 분할

청킹 금지 원칙:

- 사용자가 직접 청킹하지 않는다.
- 문서 업로드 후 시스템이 자동 처리한다.
- 실패 시 사용자는 재처리만 실행한다.

### 공고문 요구조건 추출
공고문 분석 결과에서 다음 구조를 추출해야 합니다.

```json
{
  "notice_requirements": [
    {
      "requirement_id": "req-001",
      "type": "license",
      "title": "조경식재공사업 등록",
      "description": "입찰참가자는 조경식재공사업 등록을 보유해야 함",
      "required": true,
      "source": "notice_attachment",
      "source_page": 2,
      "source_text": "..."
    }
  ],
  "required_documents": [],
  "deadlines": [],
  "unclear_items": []
}
```

추출 대상:

- 참가자격
- 면허/업종
- 지역 제한
- 기업유형 제한
- 실적 제한
- 금액/재무 조건
- 공동수급 조건
- 필수 제출서류
- 제출 기한
- 현장설명/질의응답 조건
- 결격/제재 조건

### 검색 쿼리 생성 전략
각 요구조건마다 검색 쿼리를 생성합니다.

예시:

```text
요구조건: 조경식재공사업 등록 보유
검색 쿼리:
- 조경식재공사업 입찰참가자격 등록 기준
- 조경식재공사업 면허 보유 공사 입찰 참가 조건
- 조경식재공사업 등록증 제출서류
필터:
- category in ["업종/면허 기준", "제출서류 기준"]
- legal_status = "active"
```

### 매칭 로직
판단은 3단계로 수행합니다.

1. 공고문 요구조건을 구조화한다.
2. 요구조건별로 기준문서 근거를 검색한다.
3. 법인 프로필/증빙자료와 비교한다.

매칭 상태:

- `met`: 충족
- `missing`: 부족
- `expired`: 보유했지만 만료
- `unverified`: 입력은 있으나 증빙자료 없음
- `unknown`: 법인 정보가 없어 판단 불가
- `not_applicable`: 해당 없음

### 판단 결과 스키마
```json
{
  "overall_status": "needs_review",
  "summary": "현재 법인은 필수 면허와 중소기업 확인서 유효성 확인이 부족하여 추가 준비가 필요합니다.",
  "requirements": [
    {
      "requirement_id": "req-001",
      "name": "조경식재공사업 등록",
      "status": "missing",
      "severity": "blocking",
      "why_required": "공고 참가자격에 명시됨",
      "corporation_current_state": "법인 프로필에 해당 면허 없음",
      "needed_action": "조경식재공사업 등록증 보유 여부를 확인하고 증빙자료를 업로드하세요.",
      "required_documents": ["조경식재공사업 등록증"],
      "evidence_citations": [
        {
          "basis_document_title": "업종별 입찰참가자격 기준",
          "page": 12,
          "section": "입찰참가자격",
          "quote": "..."
        }
      ]
    }
  ],
  "preparation_checklist": [],
  "uncertainty_notes": [],
  "confidence": "medium"
}
```

### 준비 가이드 생성 원칙
준비 가이드는 친절해야 하지만, 법적 확정 판단처럼 보이면 안 됩니다.

출력 항목:

- 현재 부족한 조건
- 왜 필요한지
- 준비해야 할 인증/면허/서류
- 확인해야 할 기관 또는 발급처
- 예상 선행 작업
- 사용자가 입력/업로드해야 할 자료
- 공동수급 등 대안 가능성
- 행정사 검토 필요 항목

예시 문구:

```text
현재 프로필에는 해당 면허 보유 정보가 없습니다.
이 공고는 참가자격에 특정 업종 등록을 요구하므로, 먼저 보유 여부를 확인해야 합니다.
이미 보유 중이라면 등록증 PDF를 법인 증빙자료에 업로드해주세요.
보유하지 않았다면 해당 면허 취득 가능성과 공동수급 가능 여부를 별도로 검토해야 합니다.
```

## API 설계 초안

### 법인 프로필 확장
```text
GET /api/corporations/{id}/readiness-profile
PATCH /api/corporations/{id}/readiness-profile
GET /api/corporations/{id}/evidence-documents
POST /api/corporations/{id}/evidence-documents
DELETE /api/corporation-evidence-documents/{id}
POST /api/corporation-evidence-documents/{id}/parse
```

### 기준문서
```text
GET /api/basis-documents
POST /api/basis-documents
GET /api/basis-documents/{id}
PATCH /api/basis-documents/{id}
DELETE /api/basis-documents/{id}
POST /api/basis-documents/{id}/reprocess
GET /api/basis-documents/{id}/chunks
GET /api/basis-documents/{id}/rules
POST /api/basis-documents/{id}/activate-version
```

### RAG 검색
```text
POST /api/rag/search-basis
POST /api/rag/search-requirement-evidence
GET /api/rag/index/status
POST /api/rag/index/rebuild
```

### 판단 엔진
```text
POST /api/eligibility/evaluate
GET /api/eligibility/evaluations/{id}
POST /api/eligibility/evaluations/{id}/rerun
GET /api/eligibility/evaluations/{id}/checklist
```

## UI 설계 초안

### 법인 상세 화면
- 준비 상태 요약 카드
- 필수 입력 누락 알림
- 면허/인증 탭
- 기업유형/우대조건 탭
- 실적/인력/장비 탭
- 증빙자료 탭
- 최근 판단 이력 탭

### 저장한 공고 상세 화면
- `법인 선택 후 준비 상태 검토` 버튼
- 검토 대상 법인 선택
- 검토 전 부족 데이터 안내
- 검토 결과 화면으로 이동

### 준비 상태 검토 결과 화면
- 상단 상태 배지
  - 준비 확인
  - 부족 조건
  - 확인 필요
- 핵심 부족 조건 카드
- 조건별 매칭 테이블
- 준비 서류 체크리스트
- 근거 조항 패널
- 불확실성/추가 확인 필요 항목
- 재검토 버튼

## 데이터 품질과 안전장치
- 기준문서 인덱스가 없으면 최종 판단 실행을 막고 기준문서 업로드를 안내한다.
- 법인 핵심 필드가 부족하면 `검토 필요`로 출력한다.
- 증빙자료가 없는 보유 항목은 `unverified`로 표시한다.
- 만료일이 지난 인증은 충족으로 보지 않는다.
- RAG 검색 결과 citation이 없는 조건은 확정 판단에 사용하지 않는다.
- LLM 출력은 JSON schema 검증을 통과해야 저장한다.
- 모든 판단 결과는 `행정 실무 검토 보조` 문구를 함께 표시한다.

## 구현 순서 제안
1. Phase 1.6에서 법인 프로필 확장 스키마 설계
2. Phase 1.6에서 법인 증빙자료 업로드/파싱/자동 분류 도메인 추가
3. Phase 1.6에서 사용자 확인 후 법인 프로필 업데이트 UX 구현
4. Phase 2에서 기준문서 관리 DB/API/UX 구현
5. Phase 2에서 기준 PDF 파싱/OCR/정규화/청킹 구현
6. Phase 2에서 Qdrant 또는 Chroma 로컬 인덱스 연결
7. Phase 2에서 기준문서 청크 검색 API 구현
8. Phase 2.5에서 기준문서 규칙 추출 실험
9. Phase 2.5에서 공고문 요구조건 구조화 추출 강화
10. Phase 3에서 법인 대 요구조건 매칭 엔진 구현
11. Phase 3에서 부족 조건/준비 가이드 생성
12. Phase 3에서 근거 citation UI 구현
13. 샘플 공고와 샘플 법인으로 회귀 테스트 구축

## 테스트 계획
- 법인 필드 저장/수정/삭제 테스트
- 법인 증빙자료 업로드/삭제 테스트
- 기준 PDF 업로드 후 청크 생성 테스트
- OCR 필요 PDF fallback 테스트
- 같은 문서 재처리 시 이전 청크 안전 교체 테스트
- 벡터 검색 메타데이터 필터 테스트
- 공고 요구조건 추출 스키마 테스트
- 매칭 상태별 테스트
  - 충족
  - 부족
  - 만료
  - 증빙 없음
  - 정보 없음
- citation 없는 결과가 확정 판단에 쓰이지 않는지 테스트
- 판단 결과 JSON schema 검증 테스트

## Assumptions
- 사업자등록번호는 향후 판단/식별에 필요하지만, Phase 2.5에서는 마스킹과 로컬 저장을 전제로 선택 필드로 시작한다.
- 법인 증빙자료는 PDF, DOCX, JPG/JPEG, PNG를 우선 지원한다.
- 구형 DOC 파일은 추후 LibreOffice 변환 또는 별도 변환 경로가 준비될 때 지원한다.
- 기준문서는 PDF만 허용한다.
- 판단 엔진은 Phase 3 전까지 사용자에게 확정 결과로 노출하지 않는다.
- 로컬 RAG는 외부 벡터 DB 클라우드가 아니라 로컬 PC 저장소를 사용한다.
- 일부 인증/면허의 실제 취득 가능성이나 기간은 시스템이 확정하지 않고 준비 가이드 수준으로 안내한다.

## Questions for Product Owner
- 사업자등록번호를 필수 입력으로 둘 것인가, 선택 입력으로 둘 것인가?
- 첫 판단 대상 업종은 공사 중심인가, 용역/물품까지 포함인가?
- 기준문서 카테고리와 우선순위는 누가 관리할 것인가?
- 준비 가이드에서 예상 소요 기간/비용까지 안내해야 하는가?
- 공동수급 가능성 안내를 어느 수준까지 제공할 것인가?
- 판단 결과를 인쇄/PDF/Excel로 내보내야 하는가?

## 현재 코드 기준 메모
최종 갱신일: 2026-06-07

- 부족조건 중심 판단 엔진은 `judgment_runs` 기반으로 구현되어 있습니다.
- 판단 결과는 최종 합격/불합격 확정이 아니라 `matched`, `missing`, `uncertain`, `needs_review`, `not_applicable`, citation 상태와 준비 가이드를 저장합니다.
- 기준문서 citation은 JSON basis index가 valid일 때만 검색/승인/판단에 사용합니다.
- 승인된 기준문구 후보 citation도 JSON basis index 건강 상태를 통과해야 판단 엔진에서 우선 사용합니다.
- citation이 없거나 점수가 약한 조건은 확정 근거가 아니라 검토 리스크로 표시합니다.
- 현재 PDF reader 기본값은 OpenDataLoader 우선 `auto` 모드이며, 기준문서 table metadata는 `table_row` chunk로 이어집니다.

---

# AI / Engineering Version (English)

## Current Code Note
Last updated: 2026-06-07

- The gap-first judgment engine is implemented through `judgment_runs`.
- Judgment output stores `matched`, `missing`, `uncertain`, `needs_review`, `not_applicable`, citation status, and preparation guidance rather than final eligibility verdicts.
- Basis citations are usable only when the JSON basis index is valid.
- Approved rule-candidate citations also require JSON basis-index health before the judgment engine prefers them.
- Missing or weak citations are review risks, not final evidence.
- Current PDF reader default is OpenDataLoader-first `auto`, and basis table metadata feeds `table_row` chunks.

## Purpose
This document defines the detailed implementation plan for the future corporation-vs-notice eligibility/readiness feature.

The product thesis is not optimistic eligibility. Most corporations will not be immediately ready to apply. The core value is to explain:

- why the corporation is currently not ready
- which requirements are missing
- which certifications, licenses, or documents are needed
- which evidence clauses support the recommendation
- which items still need human review

## Phase Placement

### Phase 1.6
- implement corporation evidence auto-extraction foundation before Phase 2
- expanded corporation readiness profile
- corporation evidence document management
- evidence upload/extraction/classification
- LLM fallback classification for unknown evidence documents
- reviewed profile updates
- detailed taxonomy and implementation plan lives in `docs/corporation-evidence-auto-extraction-plan.md`

### Phase 2
- basis document management
- automatic PDF extraction/OCR/normalization/chunking
- local vector indexing
- retrieval preparation only
- no final eligibility verdict

### Recommended Phase 2.5
- improved notice requirement extraction
- basis evidence search API
- internal requirement-vs-profile matrix

### Phase 3
- eligibility/readiness evaluation
- missing requirement analysis
- required certification/document guidance
- evidence citation rendering
- preparation checklist and guide generation

## Core Evaluation Flow
```text
corporation profile
  + corporation evidence documents
  + Nara notice metadata
  + notice attachment analysis
  + basis-document RAG results
    -> extract requirements
    -> match against corporation state
    -> compute gaps
    -> generate preparation guide
    -> render citations and uncertainty notes
```

## Result States
- `matched`: current corporation data/evidence matches the requirement
- `missing`: required licenses, certifications, regions, company types, performance, amounts, or documents are missing
- `uncertain`: automated comparison is not enough
- `needs_review`: notice, basis document, corporation data, or evidence requires human review
- `not_applicable`: the requirement does not apply in the current context
- `citation_missing`: no basis-document citation is available, so the item must not become final evidence

Default should be `needs_review`. The system must not produce confident final verdicts without strong evidence and citations.

## Corporation Field Expansion

### Design Principles
- Corporation fields become factual inputs for the matcher.
- Unknown fields must be allowed.
- Each important field should support verification status, expiry date, and linked evidence.
- Structured fields should be preferred over free text where possible.
- Corporation profile and corporation evidence documents should be separate but linkable.
- Corporation onboarding should default to `evidence upload -> automatic extraction -> user confirmation`, not manual form entry.
- The first screen should ask for a business registration certificate. Manual input is shown only when the user selects `I do not have the certificate`.

### Recommended Core Fields
| Field | Purpose | Notes |
|---|---|---|
| corporation_name | display/search | existing |
| business_registration_number | entity identification | mask in UI |
| corporate_registration_number | legal entity identification | optional first |
| representative_name | document/evidence matching | optional |
| headquarters_region | regional restrictions | split province/city/district |
| branch_locations | regional exceptions | multi-value |
| business_categories | requirement matching | free text + tags |
| company_size_classification | SME/small/micro checks | validity needed |
| internal_notes | admin notes | existing |

### License / Certification Fields
| Field | Purpose |
|---|---|
| license_name | requirement matching |
| license_number | evidence verification |
| issuing_authority | confidence/source |
| acquired_at | validity/context |
| expires_at | expiration check |
| status | owned, preparing, expired, unknown |
| evidence_document_id | linked proof |

### Procurement Fields
- Nara competitive bidding participant registration status
- procurement vendor registration number
- sanctions/restriction status
- joint supply/consortium availability
- subcontracting or partner availability

### Company Type / Preferential Fields
- SME confirmation
- women-owned business confirmation
- disabled-owned business confirmation
- social enterprise/cooperative
- venture/startup confirmation
- direct production certificate

Each item should store ownership status, validity period, evidence, and notes.

### Low-Text Corporation Input UX
Corporation registration should minimize manual typing. Prefer selection, toggles, dropdowns, and evidence upload with automatic extraction.

Input priority:

1. upload evidence and auto-extract fields
2. checkbox/toggle
3. searchable dropdown
4. date picker
5. numeric input
6. free text

Free text should be limited to internal notes, custom fallback items, and correction of failed extraction results.

### Evidence-First Corporation Onboarding UX
The first corporation registration screen should start with business registration certificate upload, not a general manual form.

First screen:

```text
Upload the business registration certificate to start corporation registration.
The system will extract corporation name, business registration number, representative name, address, business type, and business items.

[Upload Business Registration Certificate]
[I do not have it / I will enter it later]
```

User flow:

1. User uploads the business registration certificate.
2. System reads image/PDF/Word files and extracts text.
3. System classifies whether the file is a business registration certificate.
4. System extracts structured corporation profile candidates.
5. User reviews and corrects only wrong fields.
6. Confirmed values create the corporation profile.
7. System guides the user to upload license/certification/company-type/track-record evidence next.

Auto-extraction candidates:

- corporation name or trade name
- business registration number
- representative name
- opening date
- corporate registration number if present
- business address
- province/city/district parsed from address
- business type
- business items
- issue date or printed date

Recommended supported formats:

- PDF
- DOCX
- JPG/JPEG
- PNG
- DOC can be considered later through LibreOffice conversion or a separate converter

When `I do not have it` is selected:

- show a minimal manual form
- initially ask only for corporation name, headquarters region, and representative business category
- business registration number, representative name, and full address remain optional
- show guidance that uploading the certificate later will automatically enrich the profile
- corporations created manually should display `no evidence` or `basic information unverified`

Extraction review UX:

- show original document preview and extracted fields side-by-side
- show confidence per extracted field
  - high: prefilled
  - medium: `needs review`
  - low: empty or suggested value
- user corrects only inaccurate fields
- values are persisted only after `Confirm and create corporation`

Extraction pipeline:

```text
upload_evidence
  -> detect_file_type
  -> extract_text_or_ocr
  -> classify_document_type
  -> extract_business_registration_fields
  -> normalize_registration_number_and_address
  -> return_review_candidates
  -> user_confirm
  -> create_or_update_corporation_profile
```

Extraction states:

- `uploaded`
- `extracting`
- `ocr_processing`
- `classifying`
- `field_extracted`
- `needs_review`
- `confirmed`
- `failed`

The same pattern should later support license certificates, SME confirmations, performance certificates, and credit reports.

### Company Type / Preferential UX
Company type and preferential conditions should use checkbox cards or toggle cards, not manual text input.

Recommended UI:

```text
[ ] SME confirmation
    - subtype: dropdown(medium/small/micro/unknown)
    - expiry date: date picker
    - evidence: upload or link existing evidence

[ ] Women-owned business
    - expiry date: date picker
    - evidence: upload or link existing evidence

[ ] Disabled-owned business
[ ] Social enterprise
[ ] Cooperative
[ ] Venture company
[ ] Startup company
[ ] Direct production certificate
```

Each card expands only when selected. Unselected items stay collapsed to reduce visual burden.

Allowed statuses:

- `owned`
- `preparing`
- `not_owned`
- `unknown`

Default is `unknown`. The user must not be forced to answer fields they do not know yet.

### License / Certification UX
Licenses and certifications should use a searchable dropdown plus a manual add fallback.

Recommended UI:

- license search input
- quick-select chips for frequent licenses
- selected license list
- per-license status, acquired date, expiry date, linked evidence

Example quick chips:

- landscape planting construction
- forestry business corporation
- information and communications construction
- electrical construction
- software business operator
- direct production certificate

Unknown licenses can be manually added and reused as future autocomplete candidates.

### Track Record / Staff / Equipment UX
Do not force detailed entry first.

Start with:

- `none`
- `exists`
- `unknown`

Only expand detailed fields when `exists` is selected.

For track records, evidence upload should be preferred over manual entry.

Auto-extraction candidates:

- client
- project name
- contract period
- contract amount
- work category
- evidence document title

The user only confirms or corrects extraction results.

### Recommended Registration Flow
Initial registration should prioritize business registration certificate upload over manual form entry.

Step 1 default path:

- upload business registration certificate
- extract text from image/PDF/Word
- auto-extract corporation basic fields
- user reviews extracted results

Step 2 fallback path:

- user selects `I do not have it`
- show minimal manual form
- ask only for corporation name, headquarters region, and representative business category first
- defer the rest to optional fields or later enrichment

Step 3 quick checks:

- select owned company-type/preferential conditions
- select owned licenses/certifications

Step 4 evidence upload:

- business registration certificate
- license/certification documents
- SME confirmation, etc.

Step 5 auto-enrichment:

- extract expiry date, issuer, and certificate names from uploaded files
- user confirms the extracted candidates

### Readiness Indicator
Corporation detail should show judgment readiness, not just form completion.

Example:

```text
Notice evaluation readiness 62%
- basic information: sufficient
- licenses/certifications: 2 evidence documents needed
- company type: SME confirmation expiry date needs review
- track records: unknown
- sanctions/restrictions: unknown
```

This helps the user improve only the data that affects future evaluation.

### Capability / Track Record Fields
- similar project records in the last 3 years
- maximum single contract amount
- total contract amount
- construction/capability evaluation amount
- professional staff
- equipment inventory
- credit rating
- revenue/financial statement summary

## Corporation Evidence Documents
Recommended table:

```text
corporation_evidence_documents
- id
- corporation_id
- evidence_type
- title
- original_file_name
- stored_file_path
- issue_date
- expiry_date
- issuer
- verification_status
- extracted_text_path
- parsed_metadata_json
- linked_profile_field
- memo
- created_at
- updated_at
```

Recommended evidence types:
- business registration certificate
- corporate registry extract
- license/registration certificate
- SME confirmation
- women/disabled/social enterprise certificate
- direct production certificate
- performance certificate
- credit rating report
- technical staff evidence
- equipment evidence
- internal review materials

## Basis Document Management Recheck

### Role
Basis documents are not target notice documents. They are evidence assets for future reasoning.

They answer:
- which rule supports a notice requirement?
- why is a license/certification required?
- which documents must be submitted?
- are there exceptions or alternatives?
- what should the corporation prepare?

### Categories
- law/regulation
- procurement/Nara rules
- industry/license standards
- company-type certification standards
- required document standards
- internal review standards
- preparation guides

### Expanded Metadata
```text
basis_documents
- id
- title
- category
- subcategory
- issuing_organization
- jurisdiction
- version_label
- effective_date
- expiry_date
- source_url
- source_type
- legal_status
- priority
- tags_json
- original_file_name
- stored_file_path
- file_hash
- processing_status
- chunk_count
- rule_count
- active_version
- memo
- created_at
- updated_at
```

### Processing States
```text
uploaded
extracting
ocr_required
ocr_processing
normalizing
chunking
extracting_rules
embedding
indexed
failed
```

### Chunk Metadata
```text
basis_document_chunks
- id
- basis_document_id
- chunk_index
- chunk_text
- chunk_text_normalized
- page_start
- page_end
- section_title
- section_path
- clause_number
- rule_type
- topic_tags_json
- applies_to_json
- chunk_hash
- token_count
- embedding_model
- vector_id
- vector_status
- created_at
```

### Extracted Rules
```text
basis_rules
- id
- basis_document_id
- chunk_id
- rule_type
- requirement_name
- requirement_description
- condition_json
- required_evidence_json
- applies_to_json
- exception_json
- severity
- confidence
- citation_text
- page_start
- page_end
- created_at
- updated_at
```

Rule types:
- `eligibility_requirement`
- `required_document`
- `exclusion_condition`
- `license_requirement`
- `region_requirement`
- `company_type_requirement`
- `experience_requirement`
- `financial_requirement`
- `preparation_step`

## Local RAG Implementation Plan

### Why RAG Is Appropriate
Eligibility/readiness evaluation requires retrieving relevant clauses from many long basis documents. Full context injection is impractical and citation rendering is required.

RAG should retrieve evidence candidates. It should not make the final decision by itself.

Responsibility split:
- RAG: retrieve evidence chunks
- Rule extractor: structure notice and basis rules
- Matcher: compare corporation facts against requirements
- LLM: explain results and generate user-friendly preparation guidance

### Recommended Vector Store
Primary recommendation: `Qdrant local`

Reasons:
- local single-PC friendly
- strong metadata filtering
- useful for category/version/rule/effective-date filters
- stable Python client ecosystem

Fallback: `Chroma`

Recommendation:
- design against `VectorIndexService`
- implement Qdrant local as the target
- allow Chroma persistent mode as a temporary prototype fallback

### Embedding Strategy
- embed every basis chunk
- embed each notice requirement query
- combine metadata filters with semantic similarity
- always return chunk id and citation metadata
- cache embeddings by `chunk_hash + embedding_model`
- support full reindex when the embedding model changes

### Collection Design
```text
basis_chunks_v1
```

Payload:

```json
{
  "chunk_id": "uuid",
  "basis_document_id": "uuid",
  "title": "Eligibility Standard",
  "category": "license_requirement",
  "subcategory": "construction",
  "version_label": "2026-01",
  "issuing_organization": "Nara",
  "effective_date": "2026-01-01",
  "legal_status": "active",
  "page_start": 12,
  "page_end": 13,
  "section_title": "Eligibility",
  "clause_number": "Article 4",
  "rule_type": "eligibility_requirement",
  "topic_tags": ["license", "region", "bidding eligibility"]
}
```

### Ingestion Pipeline
```text
upload_basis_pdf
  -> save_original_file
  -> create_basis_document
  -> extract_text_by_page
  -> detect_ocr_need
  -> run_ocr_if_needed
  -> normalize_text
  -> detect_sections_and_clauses
  -> split_chunks
  -> extract_rules_optional
  -> create_embeddings
  -> upsert_vectors
  -> mark_indexed
```

### Chunking Strategy
Primary split:
- page
- heading
- clause number
- table title
- numbered list item

Secondary split:
- 500-900 tokens
- 80-150 token overlap
- preserve table row semantics where possible

No manual chunking UX is allowed.

### Notice Requirement Extraction
Target output:

```json
{
  "notice_requirements": [
    {
      "requirement_id": "req-001",
      "type": "license",
      "title": "Landscape planting construction license",
      "description": "Bidder must hold the required license.",
      "required": true,
      "source": "notice_attachment",
      "source_page": 2,
      "source_text": "..."
    }
  ],
  "required_documents": [],
  "deadlines": [],
  "unclear_items": []
}
```

Requirement categories:
- eligibility
- license/industry
- region
- company type
- experience
- financial
- consortium
- required documents
- deadlines
- exclusion/sanction

### Matching Statuses
- `met`
- `missing`
- `expired`
- `unverified`
- `unknown`
- `not_applicable`

### Evaluation Output Schema
```json
{
  "overall_status": "needs_review",
  "summary": "The corporation needs additional preparation because key license and certificate evidence is missing.",
  "requirements": [
    {
      "requirement_id": "req-001",
      "name": "Required license",
      "status": "missing",
      "severity": "blocking",
      "why_required": "Specified in the notice eligibility clause.",
      "corporation_current_state": "No matching license exists in the profile.",
      "needed_action": "Confirm license ownership or prepare acquisition/evidence.",
      "required_documents": ["license certificate"],
      "evidence_citations": []
    }
  ],
  "preparation_checklist": [],
  "uncertainty_notes": [],
  "confidence": "medium"
}
```

## API Draft

### Corporation Readiness
```text
GET /api/corporations/{id}/readiness-profile
PATCH /api/corporations/{id}/readiness-profile
GET /api/corporations/{id}/evidence-documents
POST /api/corporations/{id}/evidence-documents
DELETE /api/corporation-evidence-documents/{id}
POST /api/corporation-evidence-documents/{id}/parse
```

### Basis Documents
```text
GET /api/basis-documents
POST /api/basis-documents
GET /api/basis-documents/{id}
PATCH /api/basis-documents/{id}
DELETE /api/basis-documents/{id}
POST /api/basis-documents/{id}/reprocess
GET /api/basis-documents/{id}/chunks
GET /api/basis-documents/{id}/rules
POST /api/basis-documents/{id}/activate-version
```

### RAG
```text
POST /api/rag/search-basis
POST /api/rag/search-requirement-evidence
GET /api/rag/index/status
POST /api/rag/index/rebuild
```

### Eligibility
```text
POST /api/eligibility/evaluate
GET /api/eligibility/evaluations/{id}
POST /api/eligibility/evaluations/{id}/rerun
GET /api/eligibility/evaluations/{id}/checklist
```

## Safety Rules
- If no basis index exists, block final evaluation and guide the user to upload basis documents.
- If key corporation fields are missing, output `review_required`.
- Profile entries without evidence are `unverified`.
- Expired certificates do not count as met.
- Requirements without citations must not be used for final determinations.
- LLM outputs must pass JSON schema validation before persistence.
- UI must present this as administrative review assistance, not legal certification.

## Implementation Order
1. Phase 1.6A: implement business-registration evidence-first corporation onboarding.
2. Phase 1.6A: add corporation evidence upload/storage and reviewed profile update candidates.
3. Phase 1.6A: connect PDF/DOCX extraction and an OCR adapter seam for image evidence.
4. Phase 1.6B: expand core evidence categories and rule-based extraction.
5. Phase 1.6C: add unknown evidence LLM classification, manual type assignment, conflict handling, and sensitive-log redaction.
6. Phase 2: implement basis document DB/API/UX.
7. Phase 2: implement basis PDF extraction/OCR/normalization/chunking.
8. Phase 2: connect Qdrant or Chroma local index.
9. Phase 2: implement basis chunk search API.
10. Phase 2.5: experiment with basis rule extraction.
11. Phase 2.5: improve notice requirement extraction.
12. Phase 3: implement corporation-vs-requirement matcher.
13. Phase 3: generate missing requirements and preparation guide.
14. Phase 3: render evidence citations.
15. Add regression tests with sample notices and corporations.

## Test Plan
- corporation readiness field CRUD
- corporation evidence upload/delete
- basis PDF chunk generation
- OCR fallback
- safe reprocess replacing old chunks
- vector metadata filter search
- notice requirement extraction schema
- matcher statuses: met, missing, expired, unverified, unknown
- no final decision without citation
- eligibility output JSON schema validation

## Assumptions
- Business registration number starts as optional with masking.
- Corporation evidence documents should support PDF, DOCX, JPG/JPEG, and PNG first.
- Legacy DOC support is optional and should require a conversion path.
- Basis documents remain PDF-only.
- No final verdict is exposed before Phase 3.
- Local RAG uses local PC storage, not cloud vector DB.
- Preparation time/cost is guidance only unless explicitly modeled later.
- Phase 1.6 should be split into 1.6A, 1.6B, and 1.6C before Phase 2 starts.
- Phase 1.6A should be implemented on the current Flask backend without a FastAPI migration.
- LLM evidence classification requires a configured API key and produces review candidates only.

## Questions for Product Owner
- Should business registration number be required?
- Should the first evaluation scope be construction only?
- Who owns basis taxonomy and priority?
- Should preparation guidance include estimated time/cost?
- How far should consortium/joint-supply alternatives go?
- Is PDF/Excel export required for evaluation results?
