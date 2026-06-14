# SMART 조달청 계산기 Rocket Pitch

# 한국어 버전

## 문서 목적
이 문서는 비개발자 청중에게 `SMART 조달청 계산기`를 쉽고 설득력 있게 소개하기 위한 발표용 설명 문서입니다.

기술 구조를 설명하기보다 다음 흐름으로 서비스를 이해시키는 데 초점을 둡니다.

```text
문제 제기 -> 해결 방법 -> 제품 시연 -> 사용 요청
```

## 한 줄 소개
`SMART 조달청 계산기`는 나라장터 공고, 법인 증빙자료, 기준문서를 한 곳에 모아 조달 참여 준비에 필요한 부족조건과 필요서류를 빠르게 확인하도록 돕는 로컬 실행형 AI 업무 포탈입니다.

## 30초 Rocket Pitch
조달 업무에서 가장 오래 걸리는 일은 공고문, 첨부파일, 법인 증빙자료, 기준문서를 따로 열어 보며 “우리 법인이 지금 무엇이 부족한가”를 확인하는 과정입니다.

`SMART 조달청 계산기`는 나라장터 공고를 저장하고, 첨부 PDF/DOCX를 자동 분석하며, 법인 증빙자료와 기준문서를 함께 비교해 부족조건, 필요서류, 준비 가이드를 보여줍니다.

이 서비스는 최종 합격을 단정하는 도구가 아니라, 담당자가 더 빠르고 안전하게 검토할 수 있도록 근거와 확인이 필요한 항목을 정리해 주는 조달 업무 보조 포탈입니다.

## 발표 대상
- 조달 업무를 검토하는 행정사
- 법인 입찰 준비 담당자
- 공고문과 증빙자료를 반복 확인하는 내부 실무자
- 조달 업무 자동화를 검토하는 의사결정자

## 1. 문제 제기

### 문제 1. 공고문과 첨부파일이 너무 많고 형식이 제각각입니다
나라장터 공고에는 본문, 첨부 PDF, DOCX, 표, 금액, 마감일, 면허 제한, 지역 제한이 섞여 있습니다.

담당자는 공고마다 파일을 내려받고, 중요한 조건을 다시 찾아보고, 누락된 제출서류가 없는지 수작업으로 확인해야 합니다.

### 문제 2. 법인 정보와 증빙자료가 따로 관리됩니다
사업자등록증, 중소기업확인서, 직접생산확인증명서, 면허증, 실적증명서, 신용평가서 같은 자료는 입찰 검토에 중요하지만 대부분 파일 단위로 흩어져 있습니다.

결과적으로 “이 법인이 해당 공고를 준비할 수 있는 상태인가”를 판단하려면 여러 문서와 메모를 동시에 봐야 합니다.

### 문제 3. 기준문서는 표와 조항이 많아 근거 확인이 어렵습니다
직접생산 확인기준 같은 기준문서는 페이지 수가 많고 표가 많습니다.

특정 제품, 세부품명, 설비, 인력, 생산공정 조건을 찾기 위해 긴 PDF를 반복 검색해야 하며, 조건을 찾더라도 어느 근거를 기준으로 판단했는지 정리하기 어렵습니다.

### 문제 4. 계약서 초안 작성도 반복 업무입니다
공고와 법인 정보가 이미 정리되어 있어도 계약서 초안을 다시 작성하려면 공고번호, 계약금액, 계약기간, 법인 기본정보를 사람이 옮겨 적어야 합니다.

이 과정에서 누락이나 오타가 생길 수 있고, 검토용 초안을 만드는 데도 시간이 듭니다.

### 문제 5. 운영 중 실패와 이력을 추적하기 어렵습니다
문서 분석, 첨부 다운로드, AI 요약, OCR, 기준문서 인덱싱 같은 작업은 실패할 수 있습니다.

실무에서는 “어떤 작업이 실패했는지”, “다시 실행해야 하는지”, “백업은 정상인지”를 볼 수 있어야 합니다.

## 2. 해결 방법

### 해결 1. 나라장터 공고를 검색하고 저장합니다
사용자는 나라장터 공고를 검색하고, 필요한 공고를 저장할 수 있습니다.

저장된 공고는 내부 게시판처럼 다시 볼 수 있으며, 공고 첨부 PDF/DOCX는 자동으로 내려받아 분석합니다.

### 해결 2. 문서 내용을 자동으로 읽고 정리합니다
서비스는 PDF와 DOCX 문서에서 텍스트와 표 내용을 추출합니다.

PDF는 OpenDataLoader 기반 추출을 우선 사용하고, 필요한 경우 PyMuPDF와 OCR을 보조로 사용합니다.

비개발자 관점에서는 다음처럼 이해하면 됩니다.

```text
파일 업로드 또는 공고 저장
-> 문서 내용 읽기
-> 표와 주요 문장 추출
-> AI 요약과 구조화 결과 생성
-> 화면에서 검토
```

### 해결 3. 법인 증빙자료를 업로드하고 필요한 값만 반영합니다
법인 증빙자료를 업로드하면 서비스가 문서 유형과 주요 값을 자동 추출합니다.

다만 추출 결과를 바로 확정하지 않고, 사용자가 확인한 값만 법인 프로필에 반영합니다.

이 방식은 OCR이나 AI가 틀린 값을 법인 정보에 덮어쓰는 위험을 줄입니다.

### 해결 4. 기준문서를 지식 자산으로 바꿉니다
기준문서 PDF를 업로드하면 서비스가 텍스트 추출, OCR, 청킹, 인덱싱을 자동으로 처리합니다.

이후 공고 요구조건이나 법인 준비 상태를 검토할 때 기준문서의 관련 조항과 표를 빠르게 찾는 데 활용합니다.

핵심은 사용자가 직접 기준문서를 쪼개거나 검색 인덱스를 만들 필요가 없다는 점입니다.

### 해결 5. 최종 판정이 아니라 부족조건 중심으로 보여줍니다
서비스는 “지원 가능”을 쉽게 단정하지 않습니다.

대신 다음 정보를 중심으로 보여줍니다.

- 현재 준비된 조건
- 부족한 조건
- 추가 확인이 필요한 조건
- 필요한 제출서류
- 기준문서 근거 상태
- 다음 준비 가이드

이 접근은 실무자가 최종 판단을 더 빠르게 검토하도록 돕는 방식입니다.

### 해결 6. 계약서 DOCX 초안을 생성합니다
저장된 공고와 법인 기본정보를 기준으로 `용역표준계약서` 형식의 DOCX 초안을 생성합니다.

생성된 계약서는 바로 확정 문서가 아니라, 관리자가 검토하고 수정하기 위한 초안입니다.

### 해결 7. 운영 대시보드와 이력으로 관리합니다
서비스는 운영 대시보드, 작업 이력, 실패 관리, 백업/검증/복원계획 화면을 제공합니다.

따라서 단순 분석 도구가 아니라, 실제 운영 중 상태를 추적할 수 있는 업무 포탈로 사용할 수 있습니다.

## 3. 제품 시연 흐름

### 시연 목표
청중이 “이 서비스가 실제 조달 검토 시간을 어떻게 줄이는지”를 화면 흐름으로 이해하게 만드는 것이 목표입니다.

영상은 단순 기능 나열이 아니라 다음 이야기로 이어져야 합니다.

```text
법인 준비 -> 공고 확보 -> 기준문서 준비 -> 부족조건 확인 -> 계약서 초안 -> 운영 이력 확인
```

시연 영상에서 반드시 지킬 메시지는 다음입니다.

- 이 서비스는 최종 합격을 자동 확정하지 않습니다.
- 담당자가 놓치기 쉬운 공고 요구조건, 부족한 증빙, 기준문서 근거 후보를 빠르게 모아 줍니다.
- OCR/AI 추출 결과는 사용자가 검토한 뒤 반영합니다.
- 계약서는 최종본이 아니라 검토용 DOCX 초안입니다.
- 운영자는 실패 이력, 재시도, 백업 상태를 확인할 수 있습니다.

### 영상 생성 기본 전제
첫 공식 영상은 반복 가능한 `stable-demo` 모드로 생성합니다.

`stable-demo`는 실시간 나라장터 API와 긴 OCR 작업에 의존하지 않고, 백엔드 API로 시연용 데이터를 먼저 만든 뒤 실제 포탈 화면을 이동하며 녹화합니다. 이렇게 하면 발표 직전 네트워크 지연이나 외부 API 상태 때문에 영상이 흔들리지 않습니다.

이후 필요하면 두 가지 확장 영상을 추가합니다.

- `real-pdf-demo`: `source/test_doc/`의 실제 법인 증빙 PDF와 기준문서 PDF 처리 장면을 더 길게 보여주는 영상
- `live-nara-demo`: 실제 나라장터 API 검색 장면을 포함하는 영상

### 전체 장면 구성

| 장면 | Playwright scene id | 화면 경로 | 권장 길이 | 핵심 메시지 | 성공 신호 |
| --- | --- | --- | --- | --- | --- |
| 0. 오프닝 | `intro` | `/` | 3~5초 | 서비스가 공고, 법인, 기준문서, 계약서를 한 흐름으로 묶는다는 점 | 대시보드 또는 로고 영역 표시 |
| 1. 법인/증빙 준비 | `corporations` | `/corporations` | 8~15초 | 법인 정보와 증빙자료를 먼저 정리한다 | 시연 법인명, 증빙 업로드/관리 영역 표시 |
| 2. 대시보드 | `dashboard` | `/` | 5~8초 | 오늘 볼 업무와 운영 상태를 한 화면에서 확인한다 | 최근 공고, 문서, 준비도/상태 카드 표시 |
| 3. 나라장터 검색 | `nara-board` | `/nara-board` | 6~10초 | 공사/용역/물품/기타 공고를 검색하고 저장 흐름으로 연결한다 | 업무유형 선택, 검색 조건, 결과 영역 표시 |
| 4. 저장 공고 상세 | `saved-notice` | `/nara-saved-notices/:id` | 8~15초 | 저장한 공고의 요구조건 후보를 확인한다 | 공고명, 분석 상태, 요구조건 후보 표시 |
| 5. 기준문서/RAG | `basis-documents` | `/basis-documents` | 8~15초 | 기준문서를 검색 가능한 지식으로 만든다 | parse/chunk/index 상태 또는 기준문서명 표시 |
| 6. 부족조건 미리보기 | `notice-comparison` | `/notice-comparison` | 8~12초 | 공고 요구조건과 법인 준비 상태를 비교한다 | 준비됨/부족/확인 필요 요약 표시 |
| 7. 판단 검토 | `judgment-runs` | `/judgment-runs` | 8~12초 | 부족조건 중심 판단과 citation 후보를 검토한다 | 판단 run, 부족조건, citation 후보 표시 |
| 8. 계약서 생성 | `contracts` | `/contracts?...` | 8~12초 | 공고와 법인 정보를 기반으로 DOCX 초안을 만든다 | 계약서 초안, 다운로드 링크 또는 생성 이력 표시 |
| 9. 운영 대시보드 | `operations` | `/operations` | 5~8초 | 실패, 검토대기, 백업 상태를 운영 관점에서 본다 | 운영 요약 카드 표시 |
| 10. 작업 이력 | `operation-runs` | `/operation-runs` | 5~8초 | 어떤 작업이 언제 성공/실패했는지 추적한다 | 기준문서 처리, 판단 실행, 계약서 생성 이력 표시 |

### 장면 0. 오프닝
화면은 대시보드 또는 상단 로고 영역에서 시작합니다.

시청자가 첫 3초 안에 이해해야 하는 메시지는 다음입니다.

```text
SMART 조달청 계산기는 공고, 법인 증빙, 기준문서, 계약서 초안을 하나의 검토 흐름으로 관리합니다.
```

화면에서 보여줄 것:

- `SMART Procurement`
- `SMART 조달청 계산기`
- 왼쪽 업무 메뉴
- 대시보드 첫 화면

발표 멘트:

```text
지금 보시는 화면은 조달 검토 업무를 한 흐름으로 묶은 로컬 실행형 포탈입니다.
공고를 저장하고, 법인 증빙자료와 기준문서를 함께 검토한 뒤, 부족조건과 계약서 초안까지 이어집니다.
```

Playwright 자동화 메모:

- route: `/`
- scene id: `intro`
- 기대 텍스트: `SMART 조달청 계산기`
- 화면 이동 후 작은 오버레이 제목은 `SMART 조달청 계산기`

### 장면 1. 법인을 등록하고 증빙자료를 준비합니다
법인 관리 화면에서 시연 법인과 증빙자료 처리 영역을 보여줍니다.

이 장면의 목적은 “공고를 보기 전에 우리 법인의 준비 자료를 먼저 구조화한다”는 점을 전달하는 것입니다.

화면에서 보여줄 것:

- 법인 관리 화면
- 증빙 업로드 탭
- 증빙자료 관리 또는 법인 목록/준비도 탭
- 시연 법인명
- 사업자등록증명, 중소기업확인서, 면허/등록/허가증 같은 문서유형 옵션

발표 멘트:

```text
조달 검토는 먼저 우리 법인의 기본정보와 증빙자료가 준비되어 있어야 합니다.
사업자등록증, 확인서, 면허증 같은 자료를 올리면 서비스가 문서 유형과 주요 값을 추출합니다.
다만 AI가 뽑은 값을 바로 확정하지 않고, 사용자가 확인한 값만 법인 프로필에 반영합니다.
```

강조 포인트:

- 자동 추출은 보조 기능입니다.
- 사용자가 승인한 값만 법인 프로필에 반영됩니다.
- 알 수 없는 문서도 검토 필요 상태로 남겨 운영자가 확인할 수 있습니다.

Playwright 자동화 메모:

- route: `/corporations`
- scene id: `corporations`
- 기대 텍스트: 시연 데이터의 `corporation.name`
- 현재 `stable-demo`는 API로 시연 법인을 먼저 만든 뒤 이 화면을 녹화합니다.
- 실제 업로드 클릭 장면이 필요하면 추후 `data-demo-id="demo-corporation-evidence-upload"` 같은 안정 selector를 UI에 추가합니다.

### 장면 2. 대시보드에서 오늘 확인할 업무를 봅니다
대시보드에서 최근 공고, 최근 문서, 법인 준비 상태, 운영 상태를 확인합니다.

이 장면은 “사용자가 어디서 업무를 시작하는가”를 보여주는 허브 장면입니다.

화면에서 보여줄 것:

- 대시보드 상단 요약
- 최근 저장 공고
- 최근 업로드 문서 또는 처리 상태
- 법인 준비도 또는 운영 상태 카드

발표 멘트:

```text
법인과 문서를 등록한 뒤에는 대시보드에서 현재 업무 상태를 봅니다.
최근 저장한 공고와 처리 상태를 한눈에 확인하고, 다음에 어떤 검토를 해야 하는지 찾을 수 있습니다.
```

Playwright 자동화 메모:

- route: `/`
- scene id: `dashboard`
- 기대 텍스트는 고정하지 않아도 됩니다. 카드 렌더링과 screenshot 생성이 성공 신호입니다.

### 장면 3. 나라장터 공고를 검색하고 저장합니다
나라장터 공고 검색 화면에서 업무유형과 검색 조건을 보여줍니다.

영상에서는 반드시 “공사만 보는 것이 아니라 용역/물품/기타까지 확장되었다”는 점을 보여줍니다.

화면에서 보여줄 것:

- 업무유형 선택: 전체, 공사, 용역, 물품, 기타
- 검색어/기간 입력 영역
- 검색 결과 테이블 또는 결과 안내 영역
- 저장/분석으로 이어지는 액션

발표 멘트:

```text
나라장터에서 공고를 찾은 뒤 다시 파일을 따로 정리하지 않아도 됩니다.
공사, 용역, 물품, 기타 공고를 검색하고 필요한 공고를 저장하면 내부 검토 대상으로 관리됩니다.
저장한 공고는 첨부 문서 분석과 요구조건 추출 흐름으로 이어집니다.
```

Playwright 자동화 메모:

- route: `/nara-board`
- scene id: `nara-board`
- `stable-demo`에서는 실제 검색 결과 클릭까지 강제하지 않고 검색 화면과 저장 흐름을 보여줍니다.
- `live-nara-demo`에서는 `business_type=all` 또는 `service/goods` 검색을 실제로 실행합니다.
- ngrok 또는 외부 접속 녹화 시 API 요청에는 `ngrok-skip-browser-warning` 헤더가 자동 포함되어야 합니다.

### 장면 4. 저장한 공고의 요구조건 후보를 확인합니다
저장 공고 상세 화면에서 공고 분석 결과와 요구조건 후보를 확인합니다.

이 장면은 “공고문에서 사람이 놓칠 수 있는 조건을 먼저 뽑아 준다”는 메시지를 전달합니다.

화면에서 보여줄 것:

- 공고명
- 발주기관/수요기관
- 분석 상태
- 요구조건 후보
- 지역 제한, 면허 제한, 금액, 일정, 제출서류 후보
- 첨부파일 다운로드/분석 상태가 있으면 함께 표시

발표 멘트:

```text
공고를 저장하면 지역 제한, 면허 제한, 마감일, 금액, 제출서류 같은 요구조건 후보를 먼저 정리합니다.
담당자는 이 후보를 원문과 비교하면서 빠르게 확인할 수 있습니다.
```

Playwright 자동화 메모:

- route: `/nara-saved-notices/:id`
- scene id: `saved-notice`
- 기대 텍스트: 시연 데이터의 `notice.bid_ntce_nm`
- `prepare-service-demo-data.mjs`가 생성한 저장 공고 ID를 사용합니다.

### 장면 5. 기준문서를 업로드하고 검색 가능한 지식으로 만듭니다
기준문서 관리 화면에서 기준문서 처리 상태를 보여줍니다.

이 장면의 핵심은 “긴 PDF를 그냥 보관하는 것이 아니라 RAG 검색 가능한 기준 지식으로 바꾼다”는 점입니다.

화면에서 보여줄 것:

- 기준문서 업로드 영역
- 기준문서 목록
- parse completed
- OCR 상태
- chunk completed
- index completed
- 생성된 청크는 전체 본문이 한 번에 펼쳐지지 않고 더보기로 관리되는 모습

발표 멘트:

```text
직접생산 확인기준처럼 긴 기준문서는 표와 조항이 많아 사람이 매번 찾기 어렵습니다.
서비스는 기준문서를 추출하고 청킹한 뒤 JSON basis index로 만들어, 이후 공고 요구조건과 판단 근거 후보를 찾는 데 사용합니다.
```

Playwright 자동화 메모:

- route: `/basis-documents`
- scene id: `basis-documents`
- 기대 텍스트: 시연 데이터의 `basis_document.title`
- 긴 실제 기준문서 PDF OCR 장면은 `real-pdf-demo`에서 별도 촬영하는 것이 안정적입니다.
- `stable-demo`는 짧은 기준문서 fixture로 index 완료 상태를 빠르게 보여줍니다.

### 장면 6. 공고와 법인을 비교해 부족조건을 확인합니다
부족조건 미리보기 화면에서 저장 공고와 법인 준비 상태를 비교합니다.

이 장면은 서비스의 핵심 가치가 가장 잘 드러나는 장면입니다.

화면에서 보여줄 것:

- 저장 공고 선택
- 법인 선택
- 준비된 조건
- 부족 가능성이 있는 조건
- 확인 필요 조건
- 필요한 증빙 또는 확인 메모

발표 멘트:

```text
이 화면의 목적은 합격을 단정하는 것이 아닙니다.
지금 준비된 조건과 부족 가능성이 있는 조건, 추가 확인이 필요한 조건을 빠르게 나누어 보여주는 것입니다.
담당자는 여기서 검토 우선순위를 정할 수 있습니다.
```

Playwright 자동화 메모:

- route: `/notice-comparison`
- scene id: `notice-comparison`
- 기대 텍스트: 시연 데이터의 `corporation.name`
- `stable-demo`에서는 API로 비교 결과를 먼저 생성한 뒤 화면을 녹화합니다.

### 장면 7. 부족조건 중심 판단 결과와 citation 후보를 검토합니다
판단 검토 화면에서 부족조건 중심 판단 run을 확인합니다.

장면 6이 요약 비교라면, 장면 7은 더 깊은 검토 화면입니다.

화면에서 보여줄 것:

- 판단 run 목록 또는 상세
- 준비됨, 부족, 확인 필요 상태
- 기준문서 citation 후보
- 준비 가이드
- 검토 상태

발표 멘트:

```text
서비스는 쉽게 '지원 가능'이라고 말하지 않습니다.
대신 부족조건, 필요한 증빙, 기준문서 근거 후보, 다음 준비 가이드를 함께 보여줍니다.
최종 판단은 담당자가 이 근거를 검토한 뒤 내립니다.
```

Playwright 자동화 메모:

- route: `/judgment-runs`
- scene id: `judgment-runs`
- 기대 텍스트: 시연 데이터의 `corporation.name`
- `basis_document_processing`과 `judgment_run` operation이 preflight에서 생성되어 있어야 합니다.

### 장면 8. 계약서 DOCX 초안을 생성합니다
계약서 생성 화면에서 저장 공고, 법인, 판단 run을 연결해 DOCX 초안을 확인합니다.

이 장면은 “검토가 끝난 정보를 반복 입력하지 않는다”는 메시지를 전달합니다.

화면에서 보여줄 것:

- 공고 선택
- 법인 선택
- 판단 run 선택
- 계약번호, 금액, 기간 입력값
- 계약서 미리보기 또는 생성된 계약서 목록
- DOCX 다운로드 링크

발표 멘트:

```text
공고와 법인 정보가 이미 정리되어 있으므로, 계약서 초안 작성에서도 반복 입력을 줄일 수 있습니다.
생성된 DOCX는 최종 계약서가 아니라, 관리자가 검토하고 수정하기 위한 초안입니다.
```

Playwright 자동화 메모:

- route: `/contracts?notice_id=<id>&corporation_id=<id>&judgment_run_id=<id>`
- scene id: `contracts`
- 기대 텍스트: 시연 데이터의 `contract.title`
- 현재 영상 스크립트는 API로 계약서를 먼저 생성하고, 화면에서는 생성된 결과를 보여줍니다.

### 장면 9. 운영 대시보드에서 상태를 확인합니다
운영 대시보드에서 최근 성공/실패, 검토 대기, 백업 상태를 확인합니다.

이 장면은 “AI 기능도 운영 관리가 가능해야 한다”는 점을 보여줍니다.

화면에서 보여줄 것:

- 운영 요약
- 실패/검토대기/연동 상태
- 백업 상태
- 판단 run 또는 기준문서 처리 관련 운영 카드

발표 멘트:

```text
문서 분석이나 AI 판단은 실패할 수 있습니다.
중요한 것은 실패를 숨기지 않고, 어떤 작업이 실패했는지와 다시 실행할 수 있는지 관리자가 볼 수 있는 것입니다.
```

Playwright 자동화 메모:

- route: `/operations`
- scene id: `operations`
- 카드 렌더링과 screenshot 성공을 기본 성공 신호로 사용합니다.

### 장면 10. 작업 이력에서 실행 결과를 추적합니다
작업 이력 화면에서 기준문서 처리, 판단 실행, 계약서 생성 이력을 확인합니다.

마지막 장면은 “이 서비스는 결과 화면만 있는 것이 아니라 운영 이력을 남긴다”는 메시지로 닫습니다.

화면에서 보여줄 것:

- 기준문서 처리
- 판단 실행
- 계약서 생성
- 상태: completed, failed, retry 등
- 요청/결과/실패 사유 영역

발표 멘트:

```text
마지막으로 작업 이력을 보면 어떤 작업이 언제 실행됐고 성공했는지 확인할 수 있습니다.
문제가 생기면 실패 사유를 확인하고, 필요한 경우 재시도할 수 있습니다.
```

Playwright 자동화 메모:

- route: `/operation-runs`
- scene id: `operation-runs`
- 기대 텍스트: `기준문서 처리`
- 내부 코드명보다 실제 화면 라벨을 기준으로 검증합니다.

### 영상 자동화와 Playwright 코드 작성 기준
Playwright 코드는 이미 `scripts/create-service-demo-video.mjs`에 기본 구현되어 있습니다.

따라서 현재 `stable-demo` 영상은 새 Playwright 코드를 매번 작성하지 않아도 다음 명령으로 생성할 수 있습니다.

```powershell
cd frontend
npm run demo:preflight
npm run demo:record
npm run demo:render
npm run demo:inspect
```

다만 아래 경우에는 Playwright 코드 보강이 필요합니다.

1. 실제 버튼 클릭 과정을 영상에 넣고 싶을 때
   - 예: 법인 증빙 파일 선택, 나라장터 검색 버튼 클릭, 계약서 생성 버튼 클릭
   - 필요한 작업: 해당 버튼/입력에 안정적인 `data-demo-id`를 추가하고 Playwright가 그 selector를 클릭하도록 구현

2. 실제 PDF 업로드/OCR 장면을 길게 보여주고 싶을 때
   - 예: `source/test_doc/`의 실제 법인 증빙 PDF 업로드
   - 필요한 작업: `real-pdf-demo` 모드에서 파일 선택, 업로드, 처리 완료 polling, timeout/fallback 구현

3. 실시간 나라장터 API 검색 장면을 넣고 싶을 때
   - 예: `business_type=service` 또는 `goods` 검색 결과를 실제로 조회
   - 필요한 작업: `live-nara-demo` 모드에서 API 키 상태 확인, partial failure 배너 처리, 검색 결과 fallback 구현

4. 화면 문구가 자주 바뀌어 자동화가 흔들릴 때
   - 필요한 작업: 화면 요소에 `data-demo-id`를 추가하고 텍스트 기반 검증을 selector 기반 검증으로 전환

현재 권장 방식은 다음입니다.

```text
1차 공식 영상: stable-demo
-> API로 검증된 데모 데이터를 만들고 화면 이동 중심으로 녹화

2차 보강 영상: real-pdf-demo
-> 실제 증빙 PDF와 기준문서 OCR 처리 장면 추가

3차 선택 영상: live-nara-demo
-> 실시간 나라장터 검색 장면 추가
```

### 영상 생성 전 체크리스트
녹화 전에는 다음 조건을 확인합니다.

- `npm run demo:preflight`가 통과했는가
- 백엔드/프론트 dev server가 정상 실행 중인가
- ngrok 영상이 아니라면 로컬 URL 기준으로 녹화하는가
- ngrok으로 녹화한다면 Vite `allowedHosts`와 API CORS가 정상인가
- 화면에 `.env`, API key 원문, 서버 로그 원문이 노출되지 않는가
- 장면별 screenshot이 모두 생성되는가
- `npm run demo:inspect` 결과가 `passed`인가

## 4. 사용 요청

### 요청 1. 실제 업무 샘플로 검증해 주세요
서비스 품질은 실제 공고와 실제 증빙자료에서 확인해야 합니다.

검증에 필요한 샘플:

- 최근 나라장터 공고 5~10건
- 공고 첨부 PDF/DOCX
- 실제 기준문서 PDF
- 사업자등록증, 확인서, 면허증, 실적증명서 등 법인 증빙자료 샘플
- 기존에 사람이 정리한 체크리스트나 검토 결과

### 요청 2. 추출 결과가 맞는지 업무 담당자가 확인해 주세요
AI가 뽑은 결과는 담당자의 업무 기준과 비교해야 합니다.

확인할 항목:

- 공고 요구조건이 맞게 추출되었는지
- 제출서류가 빠지지 않았는지
- 법인 증빙자료 값이 올바른지
- 기준문서 근거가 실무 판단에 쓸 수 있는지
- 계약서 초안에 필요한 항목이 충분한지

### 요청 3. “자동 확정”보다 “검토 속도 향상” 기준으로 평가해 주세요
이 서비스는 담당자의 판단을 대체하는 도구가 아닙니다.

평가 기준은 다음이 적합합니다.

- 공고 검토 시간이 줄었는가
- 요구조건 누락 가능성이 줄었는가
- 증빙자료 확인이 쉬워졌는가
- 기준문서 근거를 찾는 시간이 줄었는가
- 계약서 초안 작성 시간이 줄었는가
- 실패 이력과 백업 상태를 관리자가 이해할 수 있는가

### 요청 4. 시범 운영 담당자를 정해 주세요
실제 운영에서 좋은 결과를 내려면 한 명 이상의 업무 담당자가 다음 역할을 맡아야 합니다.

- 공고 샘플 선정
- 법인 증빙자료 샘플 제공
- 추출 결과 검토
- 화면 용어 피드백
- 계약서 초안 항목 검토
- 우선 개선사항 정리

## 핵심 메시지
`SMART 조달청 계산기`는 조달 업무를 완전 자동으로 끝내는 기계가 아닙니다.

대신 공고, 첨부파일, 법인 증빙자료, 기준문서를 한 흐름으로 묶어 담당자가 더 빠르게 검토하고, 부족조건과 필요서류를 더 명확하게 확인하도록 돕는 업무 보조 포탈입니다.

## 청중에게 남길 마지막 문장
“이 서비스의 목표는 판단을 대신하는 것이 아니라, 조달 검토자가 놓치기 쉬운 조건과 서류를 더 빨리 발견하도록 돕는 것입니다.”

## 참고한 내부 문서
- `README.md`
- `docs/technical-design.md`
- `docs/ux-design.md`
- `docs/technology-summary.md`
- `docs/ai-api-setup.md`
- `docs/narajangteo-api-analysis.md`
- `docs/narajangteo-board-design.md`
- `docs/eligibility-rag-implementation-plan.md`
- `docs/ngrok-external-access-and-contract-docx-plan.md`
- `docs/work-log.md`

---

# AI / Engineering Version (English)

## Purpose
This document is a non-developer-facing rocket pitch for `SMART Procurement Calculator`.

It intentionally avoids implementation-heavy explanations and frames the product through:

```text
Problem -> Solution -> Product Demo -> Usage Request
```

## One-Liner
`SMART Procurement Calculator` is a local-first AI operations portal that helps procurement reviewers collect Nara notices, analyze attachments, manage corporation evidence, search basis documents, identify missing requirements, and generate review-only contract DOCX drafts.

## Product Positioning
- Not an automatic final eligibility verdict engine.
- Not a replacement for expert review.
- A workflow assistant that reduces manual document checking time.
- A local-first admin portal for a single operator, with ngrok-based demo/external access support.

## Current Product Capabilities Reflected
- Nara public API notice search, save, attachment download, and analysis.
- PDF/DOCX extraction using the shared document extraction pipeline.
- Corporation evidence upload, extraction, review, and profile enrichment.
- Basis PDF ingestion, OCR, chunking, JSON basis index, retrieval, and citation readiness.
- Gap-first judgment outputs: prepared, missing, uncertain, needs review, citation status.
- Operations dashboard, operation runs, failure tracking, backup validation, and restore dry-run.
- Contract DOCX draft generation from saved notice and corporation data.

## Demo Video Flow Contract
The primary recorded demo should use deterministic `stable-demo` mode.

`stable-demo` seeds demo data through backend APIs, then records the real portal screens with Playwright. This keeps the video stable even when live Nara API responses, OCR runtime duration, or external network conditions vary.

Scene contract:

| Scene | Playwright id | Route | Purpose | Success signal |
| --- | --- | --- | --- | --- |
| Intro | `intro` | `/` | Position the service as one workflow for notices, evidence, basis docs, and contract drafts. | Portal shell and product title are visible. |
| Corporation/evidence | `corporations` | `/corporations` | Show corporation setup and evidence management. | Seeded corporation name is visible. |
| Dashboard | `dashboard` | `/` | Show the operational entry point. | Dashboard cards render. |
| Nara board | `nara-board` | `/nara-board` | Show Nara search controls and business type coverage. | Search controls and results area render. |
| Saved notice | `saved-notice` | `/nara-saved-notices/:id` | Show extracted notice requirements. | Seeded notice title is visible. |
| Basis/RAG | `basis-documents` | `/basis-documents` | Show basis document processing and index readiness. | Seeded basis document title is visible. |
| Comparison | `notice-comparison` | `/notice-comparison` | Show notice-vs-corporation readiness comparison. | Seeded corporation name or comparison summary is visible. |
| Judgment review | `judgment-runs` | `/judgment-runs` | Show gap-first judgment and citation candidates. | Seeded corporation name or judgment run is visible. |
| Contract draft | `contracts` | `/contracts?notice_id=<id>&corporation_id=<id>&judgment_run_id=<id>` | Show review-only DOCX contract draft generation. | Seeded contract title is visible. |
| Operations | `operations` | `/operations` | Show operational state and failure visibility. | Operations cards render. |
| Operation runs | `operation-runs` | `/operation-runs` | Show traceable execution history. | Visible Korean label `기준문서 처리` is present. |

Playwright automation guidance:

- Current stable demo code lives in `scripts/create-service-demo-video.mjs`.
- Current data seeding code lives in `scripts/prepare-service-demo-data.mjs`.
- No new Playwright code is required for the basic `stable-demo` recording.
- Add Playwright code when the video must show real button clicks, file upload interactions, live Nara API search, or long-running OCR polling.
- Prefer stable `data-demo-id` selectors when text-based selectors become fragile.
- Keep `test_service_rocket_pitch_demo_pipeline_flow` as the preflight contract before recording.

Recommended command sequence:

```powershell
cd frontend
npm run demo:preflight
npm run demo:record
npm run demo:render
npm run demo:inspect
```

## Usage Ask
- Provide real notice and evidence samples.
- Review extraction results with domain experts.
- Evaluate the product by review-time reduction and missed-condition reduction, not by fully automated final decisions.
- Assign a pilot operator who can provide terminology and workflow feedback.
