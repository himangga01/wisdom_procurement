# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`에서 법인 정보를 사용자가 직접 입력하기보다, 증빙서류 업로드와 자동 추출을 통해 법인 프로필을 구성/보강하는 기능의 설계 및 구현 방향을 정의합니다.

이 기능은 Phase 2 기준문서/RAG 개발 전에 우선 개발하는 선행 단계로 둡니다.

## 핵심 UX 원칙
- 법인 등록은 수동 폼 입력이 아니라 `증빙서류 업로드`로 시작한다.
- 첫 증빙서류는 사업자등록증명 또는 사업자등록증 사본을 우선 권장한다.
- 법인은 관리 법인그룹 단위로 관리한다. 기본 그룹명은 `기본 관리그룹`이다.
- 같은 사업자등록번호라도 관리 법인그룹이 다르면 중복 등록을 허용한다.
- 같은 사업자등록번호와 같은 관리 법인그룹 조합은 중복 등록으로 차단한다.
- 사용자는 파일을 올리고, 시스템이 자동 추출한 값을 확인/수정한다.
- 사업자등록증이 없을 때만 최소 수동 입력 폼을 제공한다.
- 이후 모든 법인 정보 보강도 가능하면 증빙서류 업로드 -> 자동 추출 -> 사용자 확인 순서로 진행한다.
- 알 수 없는 서류도 버리지 않고 LLM 기반 문서 분류로 최대한 유형과 추출 후보를 파악한다.

## 개발 단계 재배치

### Phase 1.6: 법인 증빙자료 자동 추출 기반
Phase 2 전에 우선 개발합니다.

포함 범위:
- 법인 등록 첫 화면을 사업자등록증/사업자등록증명 업로드 중심으로 변경
- 법인 증빙자료 업로드 메뉴/탭
- PDF/DOCX/JPG/JPEG/PNG 텍스트 추출
- 이미지 증빙 OCR
- 증빙서류 문서 유형 자동 분류
- 사업자등록증명/사업자등록증 기본 필드 자동 추출
- 기타 증빙서류의 LLM 기반 자동 분류
- 추출 결과 확인/수정 UX
- 확인된 추출값으로 법인 프로필 업데이트
- 추출 신뢰도와 `확인 필요` 상태 표시
- 추출 후보는 필드별 선택/수정 후 선택된 후보만 반영한다.
- 선택하지 않은 후보는 보류 상태로 남겨 잘못된 OCR/추출값이 기존 법인정보를 덮어쓰지 않도록 한다.

비범위:
- 최종 자격 판단
- 기준문서 RAG
- HWP/HWPX 직접 파싱
- 외부 기관 실시간 진위확인 API 연동

### Phase 1.6 재검토 결론
개발 방향은 적절하지만, 한 번에 모든 증빙서류를 높은 정확도로 자동 추출하려고 하면 범위가 과도합니다.

따라서 Phase 1.6은 `Phase 2 이전에 완료해야 하는 선행 단계`로 유지하되, 내부 구현을 3개 묶음으로 나눕니다.

#### Phase 1.6A: 증빙자료 기반 법인 등록 MVP
- 사업자등록증명/사업자등록증 업로드 우선 등록 UX
- 수동 입력 fallback
- 관리 법인그룹 입력/선택
- 사업자등록번호 + 관리 법인그룹 중복 정책
- `corporation_evidence_documents` 저장
- `corporation_profile_update_candidates` 저장
- PDF/DOCX 텍스트 추출
- JPG/JPEG/PNG OCR 어댑터 연결
- 사업자등록증명/사업자등록증 규칙 기반 필드 추출
- 추출 결과 확인 후 승인된 필드만 법인 프로필 반영

#### Phase 1.6B: 주요 증빙자료 확장
- 중소기업확인서
- 여성기업확인서
- 장애인기업확인서
- 직접생산확인증명서
- 조달청 경쟁입찰참가자격 등록증
- 주요 면허/등록/허가증
- 납세/4대보험/신용평가/실적증명서의 기본 분류와 핵심 필드 추출

#### Phase 1.6C: 알 수 없는 증빙자료와 운영 안정화
- LLM 기반 알 수 없는 문서 분류 fallback
- 수동 문서 유형 지정
- 수동 지정 결과를 향후 규칙 후보로 저장
- 충돌 처리 고도화
- 개인정보 마스킹/로그 redaction 점검
- 샘플 문서 기반 회귀 테스트 보강

### 재검토 후 보완해야 할 핵심 가드레일
- UX 문구는 `사업자등록증명`을 우선 권장하고, `사업자등록증 사본`은 기본정보 추출 후보로 허용한다.
- SMPP 등 일부 제출처에서는 사업자등록증 사본 또는 열람용 서류가 공식 제출서류로 인정되지 않을 수 있으므로, 시스템은 `공식 제출 가능 여부는 공고별 확인 필요`로 표시한다.
- LLM 분류는 API 키가 설정된 경우에만 실행하고, 미설정이면 `확인 필요` 상태로 보관한다.
- LLM 결과는 절대 자동 확정하지 않는다.
- 사업자등록번호, 대표자명, 주소, 주민/장애/보훈 관련 정보 등 민감 가능 정보는 로그에 원문 노출하지 않는다.
- 현재 백엔드 구현은 Flask 기반이므로 Phase 1.6에서는 FastAPI 마이그레이션 없이 기존 Flask 구조에 맞춰 구현한다.
- OCR 엔진은 어댑터로 추상화한다. 로컬 OCR이 준비되지 않은 환경에서는 이미지 증빙을 `OCR 설정 필요` 또는 `확인 필요`로 처리한다.

### Phase 2
- 기준문서 관리
- 기준 PDF 청킹/인덱싱
- 로컬 RAG 검색 기반 구축

### Phase 3
- 법인 증빙자료 + 공고 요구조건 + 기준문서 RAG를 결합한 부족조건/준비 상태 판단

## 웹 조사 기반 증빙서류 분류

### 1. 법인 기본 식별 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 사업자등록증명 | 상호/법인명, 사업자등록번호, 대표자, 사업장 주소, 업태, 종목, 발급일 | 법인 기본정보 자동 생성 |
| 사업자등록증 사본 | 상호/법인명, 사업자등록번호, 대표자, 주소, 업태, 종목 | 기본정보 후보, 단 공식 제출서류 여부는 공고별 확인 필요 |
| 법인등기사항증명서/법인등기부등본 | 법인명, 법인등록번호, 본점, 대표자, 임원, 목적 | 법인성/대표자/본점 검증 |
| 법인인감증명서 | 법인명, 등록번호, 인감, 발급일 | 계약/입찰 제출서류 |
| 사용인감계 | 법인명, 대표자, 사용인감, 위임 범위 | 사용인감 제출 여부 판단 |

웹 조사 메모:
- 정부24의 사업자등록증명 민원은 사업내역 증명 목적의 발급서류입니다.
- SMPP는 직접생산확인, 여성/장애인기업 확인 등 서비스를 위해 기업정보 등록이 필요하며, 업체명/주소/대표자 변경 등에 사업자등록증명 제출을 요구합니다.
- SMPP 안내에는 사업자등록증명과 공장등록증명은 최근 90일 이내 발급 서류로 제출해야 한다는 조건이 표시됩니다.

### 2. 조달/나라장터 등록 관련 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 조달청 경쟁입찰참가자격 등록증 | 업체명, 등록번호, 등록 업종/물품/공사/용역, 유효/등록 상태 | 나라장터 입찰 기본 자격 |
| 나라장터 업체 등록 정보 출력물 | 조달업체 정보, 참가자격 등록 내용 | 참가자격 등록 여부 보조 |
| 4대 보험 가입자 명부 | 사업장명, 가입자 수, 가입일 | 상시근로자/인력 보유 근거 |

웹 조사 메모:
- 정부24의 나라장터 경쟁입찰 참가자격 등록 안내에는 물품·공사·용역·외자 입찰 참가를 위한 조달청 등록 민원으로 설명되어 있으며, 법인등기사항증명서나 4대 보험 중 1개 이상의 보험가입자 명부 같은 서류가 언급됩니다.

### 3. 기업유형/우대조건 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 중소기업확인서 | 기업명, 사업자등록번호, 규모 유형, 유효기간, 발급번호 | 중소기업/소기업/소상공인 제한 |
| 여성기업확인서 | 기업명, 대표자, 사업자등록번호, 확인번호, 유효기간 | 여성기업 제한/우대 |
| 장애인기업확인서 | 기업명, 대표자, 사업자등록번호, 확인번호, 유효기간 | 장애인기업 제한/우대 |
| 사회적기업 인증서 | 기업명, 인증번호, 인증일, 발급기관 | 사회적기업 제한/우대 |
| 예비사회적기업 지정서 | 기업명, 지정번호, 지정기간, 지자체/부처 | 예비사회적기업 조건 |
| 협동조합 설립신고확인증 | 조합명, 설립일, 신고번호 | 협동조합 조건 |
| 벤처기업확인서 | 기업명, 확인유형, 확인번호, 유효기간 | 벤처기업 조건 |
| 창업기업확인서 | 기업명, 창업일, 확인번호, 유효기간 | 창업기업 제한/우대 |
| 직접생산확인증명서 | 기업명, 세부품명, 제품명, 유효기간, 공장/생산 정보 | 물품/용역 공고 직접생산 조건 |

웹 조사 메모:
- SMPP는 중소·여성·장애인기업 확인서 신청/발급을 공공구매 구매촉진 제도로 안내합니다.
- 중소기업확인서 발급은 중소기업현황정보시스템을 통해 가능하다고 안내됩니다.
- 직접생산확인 제도는 공공기관 조달계약에서 중소기업자의 직접생산 여부를 확인하기 위한 제도로 안내됩니다.
- 벤처기업확인제도는 벤처확인종합관리시스템을 통한 확인신청/발급관리 흐름이 있습니다.
- 사회적기업 포털은 사회적기업 인증과 판로/공공조달 관련 정보를 제공합니다.

### 4. 면허/등록/허가 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 건설업 등록증 | 업종명, 등록번호, 등록일, 관할기관 | 공사 공고 참가자격 |
| 전기공사업 등록증 | 등록번호, 업종, 유효상태 | 전기공사 조건 |
| 정보통신공사업 등록증 | 등록번호, 업종, 유효상태 | 정보통신공사 조건 |
| 소방시설공사업 등록증 | 업종, 등록번호, 관할기관 | 소방 공사 조건 |
| 산림사업법인 등록증 | 산림사업 종류, 등록번호 | 산림/조경 공고 조건 |
| 엔지니어링사업자 신고증 | 전문분야, 신고번호 | 용역 공고 조건 |
| 소프트웨어사업자 일반현황 관리확인서 | 사업자 정보, 신고/관리번호, 결산연도 | 정보화 용역 조건 |
| 환경/폐기물/운송/보안 관련 허가증 | 허가 종류, 허가번호, 유효기간 | 특수 업종 조건 |

웹 조사 메모:
- SMPP 기업정보 변경 안내는 보유면허 변경 시 관련 인증서, 허가증, 등록증 등을 제출서류로 예시합니다.
- 한국SW산업협회는 소프트웨어사업자 일반 현황 관리확인서와 소프트웨어사업 수행실적증명서를 발급서류로 안내합니다.

### 5. 생산/시설/공장 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 공장등록증명서 | 공장 소재지, 업종, 면적, 등록일 | 직접생산/제조 요건 |
| 건축물대장 | 소재지, 용도, 면적 | 소규모 공장/작업장 대체 근거 |
| 부동산등기부등본 | 소재지, 소유자, 용도 | 자가 사업장/공장 근거 |
| 임대차계약서 | 임대인/임차인, 소재지, 기간 | 임차 사업장 근거 |
| 생산설비 목록/사진 | 장비명, 수량, 설치장소 | 직접생산/기술능력 근거 |

웹 조사 메모:
- SMPP 직접생산 안내는 생산공장, 공장등록증명서, 건축물대장, 부동산등기부등본, 사업자등록증명 등의 대체 관계를 설명합니다.

### 6. 재무/신용/세금/보험 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 기업신용평가등급확인서 | 등급, 평가일, 유효기간, 평가기관 | 적격심사/재무 안정성 |
| 기술평가등급확인서 | 등급, 평가일, 평가기관 | 신인도/기술능력 |
| 표준재무제표증명 | 매출, 자산, 부채, 자본, 회계연도 | 규모/재무조건 |
| 부가가치세과세표준증명 | 과세기간, 매출 과세표준 | 매출/실적 보조 |
| 국세 납세증명서 | 체납 여부, 유효기간 | 계약/입찰 제출 |
| 지방세 납세증명서 | 체납 여부, 유효기간 | 계약/입찰 제출 |
| 4대보험 완납증명서 | 사업장명, 완납 여부, 유효기간 | 공공입찰 제출 |

웹 조사 메모:
- 실제 입찰공고 사례에서는 최근 3회계연도 재무제표, 표준재무제표증명, 국세/지방세 납세증명서, 4대보험 완납증명서, 기업 신용평가등급확인서 등이 제출서류로 등장합니다.

### 7. 실적/인력/기술자 증빙
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 실적증명서 | 발주처, 사업명, 계약금액, 수행기간, 분야 | 실적 제한 충족 여부 |
| 계약서 사본 | 계약명, 금액, 기간, 계약상대방 | 실적 보조 |
| 세금계산서 | 공급자/공급받는자, 금액, 작성일 | 실적/매출 보조 |
| 경력증명서 | 인력명, 경력기간, 담당업무 | 전문인력 요건 |
| 재직증명서 | 인력명, 재직기간, 소속 | 인력 보유 요건 |
| 자격증 사본 | 자격명, 자격번호, 취득일 | 기술자 요건 |
| 고용보험/건강보험 자격득실 | 인력 고용 기간 | 재직/경력 보조 |

웹 조사 메모:
- 실제 입찰공고 사례에서는 실적증명서, 계약서 사본, 세금계산서가 실적증빙자료로 사용될 수 있다고 안내합니다.
- 정보화 용역 등에서는 소프트웨어사업 수행실적증명서가 별도 증빙으로 등장할 수 있습니다.

### 8. 입찰 제출/서약/보증 관련 서류
| 서류 | 주요 추출 필드 | 활용 |
|---|---|---|
| 입찰참가신청서 | 공고명, 업체명, 대표자, 신청일 | 제출 체크리스트 |
| 청렴계약서/청렴서약서 | 업체명, 대표자, 서약일 | 제출 체크리스트 |
| 입찰보증보험증권 | 보험금액, 보증기간, 피보험자 | 보증 요건 |
| 공동수급협정서 | 구성사, 대표사, 지분율 | 공동수급 조건 |
| 위임장 | 위임자, 대리인, 위임범위 | 대리 제출 |
| 개인정보 수집이용 동의서 | 대상자, 동의 범위 | 제출 체크리스트 |
| 각종 확약서/서약서 | 서약 내용, 업체명, 대표자 | 제출 체크리스트 |

이 유형은 법인 프로필 업데이트보다는 특정 공고의 제출서류 체크리스트 생성에 더 적합합니다.

## 자동 분류/추출 전략

### 1차: 규칙 기반 분류
파일명, 문서 제목, 상단 문구, 주요 키워드로 분류합니다.

예시:
- `사업자등록증명`, `사업자등록번호`, `상호`, `대표자`
- `중소기업확인서`, `소기업`, `소상공인`, `유효기간`
- `여성기업확인서`, `장애인기업확인서`
- `직접생산확인증명서`, `세부품명`, `공장`
- `납세증명서`, `체납`, `유효기간`
- `실적증명서`, `계약금액`, `수행기간`

### 2차: LLM 기반 알 수 없는 서류 분류
규칙 기반 분류가 실패하거나 신뢰도가 낮으면 LLM을 사용합니다.

현재 구현 상태:
- 규칙 기반 분류가 `needs_review`이고 추출 텍스트가 존재하며 AI API 키가 설정된 경우에만 실행한다.
- 기본 Provider는 Gemini이며, 현재 기본 모델은 `gemini-2.5-flash`이다.
- LLM 결과는 `ai_suggested` 상태로 저장하고 자동 확정하지 않는다.
- LLM이 만든 후보 필드는 기존 후보 검토 UX에서 체크/수정/선택 반영을 거쳐야만 법인 프로필에 반영된다.
- API 키가 없거나 LLM 호출이 실패하면 기존 `needs_review` 상태와 수동 검토 흐름을 유지한다.

LLM 입력:
- 파일명
- 첫 3~5페이지 텍스트
- OCR 텍스트 일부
- 표/키-값 후보

LLM 출력:

```json
{
  "document_type": "unknown_or_detected_type",
  "confidence": 0.0,
  "reason": "",
  "candidate_profile_updates": [],
  "candidate_required_fields": [],
  "recommended_user_action": "",
  "is_profile_evidence": true,
  "is_notice_submission_document": false,
  "needs_human_review": true
}
```

중요 정책:
- LLM이 분류한 결과는 자동 확정하지 않는다.
- 사용자가 확인해야 법인 프로필에 반영한다.
- 신뢰도가 낮으면 `확인 필요 서류`로 보관한다.
- 새로운 문서 유형은 관리자가 `이 유형으로 저장`을 선택하면 향후 규칙 후보로 저장할 수 있다.
- 추출 텍스트가 비어 있거나 OCR/파싱이 실패한 파일은 사용자가 문서 유형을 수동 지정했더라도 정적 인증/우대 후보를 생성하지 않는다.

## 법인 프로필 업데이트 방식
증빙서류는 바로 법인 정보를 덮어쓰지 않습니다.

권장 흐름:

```text
업로드
  -> 추출
  -> 후보값 생성
  -> 사용자 검토
  -> 승인된 필드만 업데이트
  -> 변경 이력 기록
```

충돌 처리:
- 기존 법인명과 사업자등록증명 법인명이 다르면 `충돌` 표시
- 기존 대표자와 새 문서 대표자가 다르면 `변경 후보` 표시
- 기존 주소와 새 문서 주소가 다르면 `본점 이전 가능성` 표시
- 동일 사업자등록번호가 같은 관리 법인그룹에 있으면 신규 법인 생성 차단
- 동일 사업자등록번호가 다른 관리 법인그룹에 있으면 등록 허용 + 안내 표시
- 만료일이 지난 증빙은 자동으로 `만료` 상태
- 같은 유형의 최신 문서가 업로드되면 이전 문서는 보관하고 대표 증빙만 갱신

## UX 설계

### 법인 등록 첫 화면
```text
법인 정보를 직접 입력하지 않아도 됩니다.
사업자등록증명 또는 사업자등록증을 업로드하면 기본정보를 자동으로 채워드립니다.

[관리 법인그룹 선택 / 새 그룹 입력]
[파일 업로드]
[사업자등록증이 없어요 / 직접 입력할게요]
```

### 증빙자료 업로드 화면
- 드래그 앤 드롭
- 여러 파일 업로드
- 파일별 예상 문서 유형 표시
- `분석 중`, `확인 필요`, `반영 완료`, `지원 안 됨` 상태 표시
- 알 수 없는 문서는 `AI로 문서 유형 파악 중` 표시

### 추출 결과 확인 화면
- 왼쪽: 원본 문서 미리보기
- 오른쪽: 추출된 필드 목록
- 필드별 상태
  - 자동 반영 가능
  - 확인 필요
  - 기존값과 충돌
  - 만료됨
- 액션
  - 이 값 반영
  - 무시
  - 직접 수정
  - 다른 필드에 연결

### 법인 상세 증빙자료 탭
- 증빙자료 목록
- 문서 유형
- 추출 상태
- 유효기간
- 연결된 법인 필드
- 대표 증빙 여부
- 재추출 버튼
- 수동 유형 지정

## 지원 파일 형식
Phase 1.6 우선 지원:
- PDF
- DOCX
- JPG/JPEG
- PNG

보류:
- DOC: 변환기 필요
- HWP/HWPX: 프로젝트 기존 범위상 직접 파싱 제외. 사용자가 PDF로 변환 후 업로드하도록 안내
- ZIP: 여러 증빙자료 묶음 업로드는 추후 압축 해제 정책 검토

## OCR/LLM 구현 방침
- OCR은 `OcrService` 어댑터로 분리한다.
- 1차 구현은 로컬 OCR 엔진을 호출할 수 있는 구조를 먼저 만들고, OCR 엔진 미설치 시 사용자에게 설정 필요 상태를 보여준다.
- 후보 엔진:
  - Tesseract: 설치가 비교적 단순하지만 한국어 문서 정확도는 샘플 검증 필요
  - PaddleOCR: 한국어/표 문서 품질은 기대할 수 있으나 Windows 설치와 의존성이 무거울 수 있음
- LLM은 OCR 대체재가 아니라 `추출된 텍스트 기반 문서 유형 분류와 필드 후보 정리`에 우선 사용한다.
- 이미지 자체를 LLM Vision으로 보내는 방식은 개인정보/비용 이슈가 있으므로 별도 승인 후 옵션으로 둔다.

## API 초안
```text
POST /api/corporations/onboarding/evidence
POST /api/corporations/onboarding/manual
POST /api/corporations/onboarding/confirm-extraction

GET /api/corporations/{id}/evidence-documents
POST /api/corporations/{id}/evidence-documents
GET /api/corporation-evidence-documents/{id}
PATCH /api/corporation-evidence-documents/{id}
DELETE /api/corporation-evidence-documents/{id}
POST /api/corporation-evidence-documents/{id}/extract
POST /api/corporation-evidence-documents/{id}/classify
POST /api/corporation-evidence-documents/{id}/apply-extracted-fields
```

## 데이터 모델 추가 제안

### corporation_evidence_documents
```text
- id
- corporation_id
- evidence_type
- evidence_scope
- title
- original_file_name
- stored_file_path
- mime_type
- file_extension
- file_size
- file_hash
- issue_date
- expiry_date
- issuer
- extraction_status
- classification_status
- document_type_confidence
- verification_status
- extracted_text_path
- extracted_fields_json
- parsed_metadata_json
- linked_profile_fields_json
- is_primary_for_type
- review_status
- error_message
- created_at
- updated_at
```

### corporation_profile_update_candidates
```text
- id
- corporation_id
- evidence_document_id
- target_field
- current_value
- extracted_value
- normalized_value
- confidence
- conflict_status
- user_decision
- decided_at
- created_at
```

## 구현 순서
1. Phase 1.6A: 증빙자료 유형 taxonomy 최소 세트 확정
2. Phase 1.6A: 법인 등록 첫 화면을 사업자등록증명/사업자등록증 업로드 우선 UX로 변경
3. Phase 1.6A: 법인 증빙자료 DB/API 추가
4. Phase 1.6A: PDF/DOCX 텍스트 추출과 이미지 OCR 어댑터 연결
5. Phase 1.6A: 사업자등록증명/사업자등록증 규칙 기반 추출 구현
6. Phase 1.6A: 추출 결과 검토/확정 UX 구현
7. Phase 1.6A: 법인 프로필 업데이트 후보/충돌 처리 구현
8. Phase 1.6A: 사업자등록번호 + 관리 법인그룹 중복 정책 구현
9. Phase 1.6B: 주요 증빙서류 유형별 규칙 기반 추출 추가
10. Phase 1.6C: 알 수 없는 문서 LLM 분류 fallback 추가
11. Phase 1.6C: 증빙자료 탭과 재추출/수동 유형 지정 UX 고도화
12. Phase 1.6C: 샘플 증빙자료 기반 테스트 구축

## Phase 1.6A 완료 기준
- 사업자등록증명/사업자등록증 파일 업로드로 법인 등록을 시작할 수 있다.
- PDF/DOCX/JPG/JPEG/PNG 파일이 저장되고 증빙자료 목록에서 조회된다.
- PDF/DOCX는 텍스트 추출 결과를 저장한다.
- 이미지 파일은 OCR 가능/불가 상태를 명확히 표시한다.
- 사업자등록번호, 법인명/상호, 대표자, 주소, 업태, 종목 후보를 추출한다.
- 추출값은 바로 반영되지 않고 사용자 확인 화면을 거친다.
- 사용자가 승인한 필드만 법인 프로필에 반영된다.
- 같은 관리 법인그룹 안에서 동일 사업자등록번호 중복 생성을 차단한다.
- 다른 관리 법인그룹에 동일 사업자등록번호가 있으면 안내 후 등록을 허용한다.
- 기존값과 다른 추출값은 충돌로 표시된다.
- 사업자등록번호 등 민감 정보는 로그와 목록 화면에서 마스킹된다.
- OCR/LLM 미설정 상태에서도 수동 확인 흐름으로 업무를 계속할 수 있다.

## 테스트 계획
- 사업자등록증명 PDF 자동 추출 테스트
- 사업자등록증 이미지 OCR 테스트
- DOCX 증빙자료 텍스트 추출 테스트
- 알 수 없는 문서 LLM 분류 mock 테스트
- LLM 분류 결과가 `ai_suggested` 후보로만 저장되고 자동 반영되지 않는지 테스트
- 기존 법인 정보와 추출값 충돌 테스트
- 만료일이 지난 증빙 상태 테스트
- 사용자가 승인한 필드만 프로필에 반영되는지 테스트
- 사용자가 선택한 후보만 반영되고 수정 입력값이 우선 적용되는지 테스트
- 빈 텍스트 + 수동 문서 유형 지정 시 정적 후보가 생성되지 않는지 테스트
- HWP/HWPX 업로드 시 지원 제외 안내 테스트

## 참고한 웹 자료
- [SMPP 기업정보 등록/변경 안내](https://www.smpp.go.kr/cst/smppInf/SelectCstMgrE.do)
- [SMPP 기업확인서 신청/발급 안내](https://www.smpp.go.kr/cst/smppInf/SelectMpeJ2.do)
- [SMPP 직접생산확인 안내](https://www.smpp.go.kr/cst/smppInf/SelectMpeI2.do)
- [정부24 사업자등록증명 발급](https://www.gov.kr/main?CappBizCD=12100000016&HighCtgCD=A09002&a=AA020InfoCappViewApp)
- [정부24 나라장터 경쟁입찰 참가자격 등록](https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=12300000001&HighCtgCD=A09001)
- [벤처기업확인제도 안내](https://www.smes.go.kr/venturein/institution/systemGuide)
- [한국SW산업협회 SW사업자 실적관리](https://www.sw.or.kr/site/sw/01/10113000000002017070309.jsp)
- [사회적기업 포털](https://www.seis.or.kr/mainPage.do)

## Assumptions
- 법인 증빙자료 자동 추출은 Phase 1.6으로 Phase 2 전에 개발한다.
- 법인 증빙자료는 PDF, DOCX, JPG/JPEG, PNG를 우선 지원한다.
- HWP/HWPX는 직접 파싱하지 않고 PDF 변환 안내를 우선 제공한다.
- LLM 분류 결과는 자동 확정하지 않고 사용자 확인 후 반영한다.
- 외부 기관 진위확인 API는 후속 확장으로 둔다.
- Phase 1.6A는 실제 백엔드 현황에 맞춰 Flask 기반으로 구현한다.
- OCR 엔진 설치 여부는 사용자 PC 환경에 따라 다를 수 있으므로 기능 상태로 표시한다.

## Questions for Product Owner
- 증빙자료 업로드를 여러 파일 동시 업로드로 시작할 것인가, 사업자등록증 1개부터 시작할 것인가?
- 문서 진위확인이 필요한 범위는 어디까지인가?
- HWP/HWPX 증빙자료가 많을 경우 PDF 변환 안내만으로 충분한가?
- 이미지 증빙 OCR 품질이 부족할 경우 외부 Vision API 사용을 허용할 것인가?

## 현재 코드 기준 메모
최종 갱신일: 2026-06-07

- 법인 증빙자료 업로드/분류/추출/후보 승인 흐름은 현재 코드에 구현되어 있습니다.
- 추출 후보는 자동으로 법인 프로필에 반영되지 않고, 사용자가 선택/수정/승인한 값만 반영합니다.
- DOCX 증빙자료는 현재 문단과 표 cell 텍스트를 함께 추출합니다.
- 이 문서는 Phase 1.6 설계/이력 문서이며, 최신 전체 실행 기준은 `docs/current-code-documentation-audit.md`와 `docs/work-log.md`를 함께 봅니다.

---

# AI / Engineering Version (English)

## Current Code Note
Last updated: 2026-06-07

- Corporation evidence upload/classification/extraction/review flows are implemented.
- Extracted candidates are not auto-applied; only selected/edited/approved values update the corporation profile.
- DOCX evidence parsing currently includes paragraphs and table cells.
- Treat this as a Phase 1.6 design/history document; use `docs/current-code-documentation-audit.md` and `docs/work-log.md` for the latest whole-service interpretation.

## Purpose
This document defines the evidence-first corporation onboarding and evidence auto-extraction plan. The system should update corporation profiles from uploaded evidence documents instead of relying primarily on manual user input.

This work must be implemented before Phase 2 basis-document/RAG development.

## Core UX Principles
- Corporation onboarding starts with evidence upload, not manual form entry.
- Business registration certificate/proof is the recommended first evidence document.
- User uploads files, system extracts fields, and user confirms/corrects results.
- Manual entry is shown only when the user does not have the certificate.
- Future corporation profile enrichment should follow upload -> extract -> review -> apply.
- Unknown evidence documents should be classified by an LLM fallback where possible.

## Phase Change

### Phase 1.6: Corporation Evidence Auto-Extraction Foundation
Must be developed before Phase 2.

Included:
- evidence-first corporation registration screen
- corporation evidence upload tab/menu
- PDF/DOCX/JPG/JPEG/PNG text extraction
- image OCR
- evidence document classification
- business registration document field extraction
- LLM fallback classification for unknown evidence
- extraction review/correction UX
- confirmed field application to corporation profile
- extraction confidence and needs-review status

Not included:
- final eligibility judgment
- basis-document RAG
- HWP/HWPX direct parsing
- external source-of-truth verification APIs

### Phase 1.6 Review Conclusion
The direction is valid and should stay before Phase 2. However, implementing every evidence type with high extraction accuracy in one pass is too broad. Phase 1.6 should therefore be delivered as three smaller internal milestones.

#### Phase 1.6A: Evidence-Based Corporation Registration MVP
- business registration proof/certificate upload-first onboarding UX
- manual-entry fallback when the administrator does not have the document
- management group selection/input
- duplicate policy based on business registration number + management group
- `corporation_evidence_documents`
- `corporation_profile_update_candidates`
- PDF/DOCX extraction
- JPG/JPEG/PNG OCR adapter seam
- business registration number/name/representative/address/basic business type extraction
- review screen before applying extracted data
- approved values only update the corporation profile

#### Phase 1.6B: Core Evidence Expansion
- SME confirmation
- women-owned business confirmation
- disabled-owned business confirmation
- direct production confirmation
- Nara registration-related documents
- major licenses/certifications
- tax/insurance/credit/performance documents as basic evidence records

#### Phase 1.6C: Unknown Evidence + Operational Hardening
- unknown-document classification fallback using LLM when the API key is configured
- manual document type assignment
- manual correction history as future extraction-rule candidates
- conflict handling between existing corporation fields and newly extracted values
- sensitive-data log redaction
- regression fixtures for major evidence categories

### Critical Guardrails After Review
- UX copy should prioritize `사업자등록증명` as the reliable evidence document, while still allowing `사업자등록증 사본` as a basic profile extraction source.
- Some agencies may not accept a copy or screen-viewed document as official submission evidence. The UI should show: `공식 제출 가능 여부는 공고별 확인 필요`.
- LLM classification runs only when an AI API key is configured. Without a key, unknown documents stay in `확인 필요`.
- LLM output must never auto-update corporation profiles. It can only create review candidates.
- Sensitive values such as business registration number, representative name, address, resident-related values, disability/veteran-related values, and detailed personal identifiers must not be logged in raw form.
- The current backend is Flask, so Phase 1.6 should be implemented on the current Flask backend instead of introducing a FastAPI migration in this phase.
- OCR should be abstracted behind an adapter. If local OCR is not available, image evidence should enter `OCR 설정 필요` or `확인 필요` instead of failing the entire corporation flow.

## Evidence Taxonomy From Web Research

### Identity / Registration Evidence
- business registration proof/certificate
- business registration certificate copy
- corporate registry extract
- corporate seal certificate
- seal-use authorization form

Extracted fields:
- corporation name
- business registration number
- corporate registration number
- representative name
- address
- business type/items
- issue date

### Procurement / Nara Registration Evidence
- Nara competitive bidding participant registration certificate
- Nara vendor registration printout
- social insurance subscriber list

### Company Type / Preferential Evidence
- SME confirmation
- women-owned business confirmation
- disabled-owned business confirmation
- social enterprise certificate
- preliminary social enterprise designation
- cooperative registration/confirmation
- venture business confirmation
- startup business confirmation
- direct production confirmation certificate

### License / Permit Evidence
- construction business registration
- electrical construction registration
- information communications construction registration
- fire-fighting facility construction registration
- forestry business registration
- engineering business registration
- software business general-status confirmation
- environmental/waste/transport/security permits

### Production / Facility Evidence
- factory registration certificate
- building register
- real-estate registry extract
- lease agreement
- production equipment list/photos

### Financial / Tax / Insurance Evidence
- corporate credit rating confirmation
- technology rating confirmation
- standard financial statement certificate
- VAT taxable base certificate
- national tax payment certificate
- local tax payment certificate
- four-major-social-insurance payment certificate

### Track Record / Staff / Technical Evidence
- performance certificate
- contract copy
- tax invoice
- career certificate
- employment certificate
- qualification certificate
- employment/health insurance history

### Bid Submission / Pledge / Guarantee Documents
- bid participation application
- integrity pledge
- bid bond/guarantee insurance
- joint-supply agreement
- power of attorney
- privacy consent
- various pledge forms

These documents usually update notice-specific checklists rather than persistent corporation profile fields.

## Classification / Extraction Strategy

### Rule-Based First Pass
Use file name, title text, top-page text, keywords, and key-value patterns.

Examples:
- business registration proof: business registration number, representative, business type/items
- SME confirmation: SME/small/micro, validity period
- direct production confirmation: product item, factory, validity period
- tax certificate: arrears/payment status, validity period
- performance certificate: client, contract amount, period

### LLM Fallback For Unknown Documents
If rule-based classification fails or confidence is low, call an LLM with:
- file name
- first 3-5 pages of extracted text
- OCR text sample
- table/key-value candidates

Current implementation:
- Runs only when rule classification returns `needs_review`, extracted text exists, and an AI API key is configured.
- Uses the shared AI provider abstraction. The current default is Gemini `gemini-2.5-flash`.
- Saves LLM output as `ai_suggested`, never as confirmed profile data.
- LLM-created candidates must go through checkbox/edit/apply review before profile updates.
- Missing key or provider failure keeps the evidence in the existing manual review flow.

Output:

```json
{
  "document_type": "unknown_or_detected_type",
  "confidence": 0.0,
  "reason": "",
  "candidate_profile_updates": [],
  "candidate_required_fields": [],
  "recommended_user_action": "",
  "is_profile_evidence": true,
  "is_notice_submission_document": false,
  "needs_human_review": true
}
```

Policy:
- LLM classification is never auto-applied.
- User confirmation is required before profile updates.
- Low-confidence documents remain `needs_review`.
- Admin can save a manually assigned type as a future rule candidate.
- Empty extraction text must not create static certification/preference candidates even when a document type is manually selected.

## Profile Update Flow
```text
upload
  -> extract
  -> create candidate values
  -> user review
  -> apply only approved fields
  -> write audit trail
```

Conflict rules:
- different corporation name -> conflict
- different representative -> change candidate
- different address -> possible headquarters relocation
- same business registration number inside the same management group -> block new corporation creation
- same business registration number in a different management group -> allow creation with warning
- expired document -> expired status
- newer document of same type can become primary while older documents remain archived

## UX

### First Registration Screen
```text
You do not need to type corporation information manually.
Upload business registration evidence and the system will fill basic information.

[Select management group / enter new group]
[Upload File]
[I do not have it / Enter manually]
```

### Evidence Upload Screen
- drag and drop
- multi-file upload
- predicted document type
- statuses: analyzing, needs review, applied, unsupported
- unknown document: AI classification in progress

### Extraction Review Screen
- left: original document preview
- right: extracted fields
- field statuses: auto-applicable, needs review, conflict, expired
- actions: apply, ignore, edit, map to another field

## Supported Formats
Phase 1.6:
- PDF
- DOCX
- JPG/JPEG
- PNG

Deferred:
- DOC: needs conversion
- HWP/HWPX: direct parsing remains out of scope; guide user to convert to PDF
- ZIP: future batch upload policy

## OCR / LLM Implementation Policy

OCR:
- Use a backend `OcrService` adapter instead of coupling the app to one OCR engine.
- Tesseract is simpler to install locally, but Korean procurement/evidence samples must be validated before committing to it as the only engine.
- PaddleOCR may provide stronger Korean layout handling but has heavier Windows installation cost.
- If OCR is unavailable, the file should still be stored and shown as `OCR 설정 필요`.

LLM:
- LLMs should classify unknown evidence and propose extracted fields from already extracted text.
- LLMs should not be treated as a replacement for deterministic parsing/OCR.
- LLM Vision for images should be a later optional mode because it can increase privacy and cost risk.

## API Draft
```text
POST /api/corporations/onboarding/evidence
POST /api/corporations/onboarding/manual
POST /api/corporations/onboarding/confirm-extraction

GET /api/corporations/{id}/evidence-documents
POST /api/corporations/{id}/evidence-documents
GET /api/corporation-evidence-documents/{id}
PATCH /api/corporation-evidence-documents/{id}
DELETE /api/corporation-evidence-documents/{id}
POST /api/corporation-evidence-documents/{id}/extract
POST /api/corporation-evidence-documents/{id}/classify
POST /api/corporation-evidence-documents/{id}/apply-extracted-fields
```

## Data Model

### corporation_evidence_documents
```text
- id
- corporation_id
- evidence_type
- evidence_scope
- title
- original_file_name
- stored_file_path
- mime_type
- file_extension
- file_size
- file_hash
- issue_date
- expiry_date
- issuer
- extraction_status
- classification_status
- document_type_confidence
- verification_status
- extracted_text_path
- extracted_fields_json
- parsed_metadata_json
- linked_profile_fields_json
- is_primary_for_type
- review_status
- error_message
- created_at
- updated_at
```

### corporation_profile_update_candidates
```text
- id
- corporation_id
- evidence_document_id
- target_field
- current_value
- extracted_value
- normalized_value
- confidence
- conflict_status
- user_decision
- decided_at
- created_at
```

## Implementation Order
1. Phase 1.6A: finalize the minimum evidence taxonomy.
2. Phase 1.6A: change corporation onboarding to business-registration evidence-first UX.
3. Phase 1.6A: add evidence document DB/API.
4. Phase 1.6A: connect PDF/DOCX extraction and image OCR adapter seam.
5. Phase 1.6A: implement rule-based business registration extraction.
6. Phase 1.6A: implement extraction review/confirmation UX.
7. Phase 1.6A: implement update candidates and conflict handling.
8. Phase 1.6A: implement duplicate policy for business registration number + management group.
9. Phase 1.6B: add rule-based extraction for major evidence types.
10. Phase 1.6C: add LLM fallback classification for unknown documents.
11. Phase 1.6C: improve evidence tab, re-extract, and manual type assignment UX.
12. Phase 1.6C: build tests with sample evidence documents.

## Phase 1.6A Done Criteria
- The administrator can start corporation registration by uploading business registration evidence.
- PDF/DOCX/JPG/JPEG/PNG files are stored and visible in the evidence list.
- PDF/DOCX extracted text is stored.
- Image files clearly show OCR available/unavailable status.
- Extracted values are shown as candidates and require explicit administrator approval.
- Candidate review supports per-field selection and value correction before approval.
- Only selected candidates are applied; unselected candidates stay pending.
- same-group duplicate business registration numbers are blocked.
- other-group duplicate business registration numbers are allowed with a warning.
- Unsupported or OCR-unavailable files do not break the flow.
- Business registration evidence is stored separately from general project documents.
- No final eligibility verdict is shown.

## Test Plan
- business registration PDF extraction
- business registration image OCR
- DOCX evidence extraction
- unknown document LLM classification mock
- extracted-vs-current conflict handling
- expired evidence status
- approved-only profile updates
- same-group duplicate block
- other-group duplicate warning
- empty-text manual document type should not generate static profile candidates
- HWP/HWPX unsupported guidance

## Sources
- [SMPP corporation info registration/change](https://www.smpp.go.kr/cst/smppInf/SelectCstMgrE.do)
- [SMPP company confirmation application/issuance](https://www.smpp.go.kr/cst/smppInf/SelectMpeJ2.do)
- [SMPP direct production confirmation](https://www.smpp.go.kr/cst/smppInf/SelectMpeI2.do)
- [Gov24 business registration proof](https://www.gov.kr/main?CappBizCD=12100000016&HighCtgCD=A09002&a=AA020InfoCappViewApp)
- [Gov24 Nara competitive bidding participant registration](https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=12300000001&HighCtgCD=A09001)
- [Venture business confirmation system](https://www.smes.go.kr/venturein/institution/systemGuide)
- [KOSA SW business performance management](https://www.sw.or.kr/site/sw/01/10113000000002017070309.jsp)
- [Social Enterprise Portal](https://www.seis.or.kr/mainPage.do)

## Assumptions
- Phase 1.6 is required before Phase 2.
- Evidence uploads support PDF, DOCX, JPG/JPEG, and PNG first.
- Corporations belong to a management group. The default group name is `기본 관리그룹`.
- Duplicate policy is scoped by `business_registration_number + management_group_name`.
- Same registration number in a different management group is allowed with a warning.
- HWP/HWPX direct parsing remains out of scope.
- LLM classification requires user confirmation before profile updates.
- External official verification APIs are future scope.
- Phase 1.6A should be implemented on the current Flask backend.
- OCR availability may differ by local PC, so the pipeline must degrade gracefully.

## Questions for Product Owner
- Should the first upload allow one certificate only or multi-file upload?
- Which evidence types should be rule-extracted first after business registration?
- Is PDF conversion guidance enough for HWP/HWPX evidence files?
- If local image OCR quality is insufficient, is an external Vision API allowed?
