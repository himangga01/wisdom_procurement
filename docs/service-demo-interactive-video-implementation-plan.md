# 서비스 데모 영상 인터랙션 구현계획

## 목적
이 문서는 `scripts/create-service-demo-video.mjs`가 실제 포탈을 천천히 조작하면서, 비개발자가 서비스 흐름을 이해할 수 있는 데모 영상을 만들도록 관리하는 기준 문서입니다.

이번 개정의 핵심은 기존 빠른 화면 이동 중심 영상이 아니라, 다음 업무 흐름을 실제 클릭, 파일 업로드, 검색, 선택, 실행, 결과 확인까지 보여주는 것입니다.

- 법인 등록과 증빙 업로드
- 나라장터 공고 검색과 공고 선택
- 기준문서 관리에서 RAG 기준문서 업로드
- 부족조건 미리보기
- 판단 검토
- 계약서 생성과 생성 결과 확인
- 운영 상태와 작업 이력 확인

## 최신 메뉴 구조 반영
현재 왼쪽 메뉴는 아래 순서와 역할을 기준으로 촬영합니다.

| 메뉴 그룹 | 촬영 대상 |
| --- | --- |
| 업무 현황 | 대시보드에서 전체 흐름 진입 |
| 내부 관리 | 법인 관리, 프로젝트 관리 |
| 공고 업무 | 나라장터 공고 검색, 저장한 공고, 부족조건 미리보기, 판단 검토, 계약서 생성 |
| 기준문서 / RAG | 기준문서 관리, 규칙 후보 관리, 검색 평가 |
| 문서 분석 | 업로드 문서 분석 |
| 설정 | 운영 대시보드, 작업 이력, 자동 수집 관리, 백업/복원, API 설정, 외부 접속 |

영상 스크립트는 메뉴 텍스트가 조금 바뀌어도 `data-demo-id` 우선 selector를 사용하고, 필요한 경우 href 기반 fallback을 사용합니다.

## 화면 전환 속도
사용자가 업무 흐름을 따라갈 수 있도록 모든 자동 조작 속도를 늦춥니다.

- 기본 화면 단계 대기: `DEFAULT_STEP_DELAY_MS = 1050`
- 클릭 후 대기: `DEFAULT_CLICK_DELAY_MS = 950`
- 입력 후 대기: `DEFAULT_TYPE_DELAY_MS = 650`
- 파일 선택 후 대기: `DEFAULT_FILE_DELAY_MS = 1100`
- 메뉴 이동 후 대기: `DEFAULT_NAVIGATION_DELAY_MS = 1350`
- 장면 사이 대기: `DEFAULT_SCENE_GAP_MS = 1250`
- 설명 오버레이 유지: `DEFAULT_OVERLAY_HOLD_MS = 3400`
- Playwright slow motion: `DEFAULT_INTERACTIVE_SLOW_MO_MS = 90`

영상 안의 오른쪽 상단 설명 팝업에는 `시연`이라는 단어를 사용하지 않습니다. 대신 `업무 흐름`, `화면 확인`, `제품 흐름`, `실행 결과` 같은 표현을 사용합니다.

## 입력 자료

### 법인 등록과 증빙 업로드 자료
폴더: `D:\project\wisdom_procurement\source\test_doc`

필수로 선택하는 사업자등록증 자료:

- `1.벡트_사업자등록증.pdf`

추가로 함께 보여줄 수 있는 증빙자료:

- `2.중소기업확인서_중기업_20260331.pdf`
- `20250226_(주)벡트_직생(동영상제작).pdf`
- `소프트웨어사업자확인서(2023결산)_벡트.pdf`
- `정보통신공사업등록증_벡트.pdf`
- `ISO9001인증서_20270731.pdf`
- `녹색기술제품확인서_20240523_(주)벡트_UITL86GZA5W외 3제품.pdf`

선정 이유:

- 벡트 사업자등록증으로 새 법인을 생성하는 장면을 보여줍니다.
- 중소기업확인서, 직접생산확인증명서, 소프트웨어사업자확인서, 정보통신공사업등록증은 조달 업무에서 자주 확인되는 법인 역량 자료입니다.
- ISO와 녹색기술제품 확인서는 우대, 인증, 품질 관련 증빙이 별도 문서로 관리되는 흐름을 보여줍니다.

### 기준문서 관리 자료
폴더: `D:\project\wisdom_procurement\source\rag_doc`

사용 파일:

- `RAG_기준문서_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`

이 파일은 기준문서 관리에서 업로드하고, 처리 상태와 생성된 청크를 확인하는 장면에 사용합니다.

### 나라장터 공고 검색 조건
벡트의 전자칠판, 영상장치, 소프트웨어, 정보통신 관련 증빙과 맞는 공고를 찾기 위해 아래 기본값을 사용합니다.

- 업무유형: `물품`
- API 값: `goods`
- 검색어: `전자칠판`
- 기간: 실행일 기준 최근 180일

검색 결과가 존재하면 첫 번째 공고를 선택하고 저장/분석을 실행합니다. 결과가 없거나 API가 부분 실패하면 경고 배너와 검색 조건이 보이도록 촬영하고, 기존 저장 공고가 있으면 저장 공고 화면에서 후속 흐름을 이어갑니다.

## 상세 데모 시나리오

### 1. 도입 화면
목표: 서비스가 조달 업무를 한 흐름으로 묶는다는 점을 먼저 보여줍니다.

진행:

1. 대시보드로 이동합니다.
2. 상단 로고와 주요 바로가기 아이콘을 보여줍니다.
3. 설명 팝업에는 “법인 등록부터 판단 결과와 계약서 초안까지 한 흐름으로 확인합니다.”라고 표시합니다.

확인 기준:

- 현재 대시보드는 별도 루트 `data-demo-id`를 두지 않으므로 `/` 경로와 상단 헤더를 기준으로 화면을 유지합니다.
- 향후 대시보드에 루트 selector가 추가되면 스크립트의 page-root 확인 목록에 함께 추가합니다.

### 2. 법인 등록과 증빙 업로드
목표: 단순히 목록을 보여주는 것이 아니라, 실제 법인을 등록하는 과정을 보여줍니다.

진행:

1. 왼쪽 메뉴의 `내부 관리` 그룹에서 `법인 관리`로 이동합니다.
2. `증빙 업로드` 탭을 클릭합니다.
3. 기존 법인 연결 값은 기본 미선택 상태를 유지하고, 새 법인 생성 문구가 보이도록 합니다.
4. 파일 선택에서 `1.벡트_사업자등록증.pdf`를 선택합니다.
5. 업로드 버튼을 클릭합니다.
6. 자동 추출 결과가 표시되면 후보 반영 버튼을 클릭해 새 법인을 생성합니다.
7. 법인 목록으로 이동해 벡트 법인이 생성되었는지 확인합니다.
8. 다시 증빙 업로드 탭으로 이동합니다.
9. 새로 생성된 벡트 법인을 선택합니다.
10. 추가 증빙자료 중 필요한 파일을 여러 개 선택합니다.
11. 업로드 후 증빙자료 관리 목록에서 처리 상태와 문서유형이 보이는지 확인합니다.

필수 selector:

- `data-demo-id="demo-corporations-page"`
- `data-demo-id="demo-corporation-upload-tab"`
- `data-demo-id="demo-evidence-file-input"`
- `data-demo-id="demo-evidence-upload-submit"`
- `data-demo-id="demo-latest-evidence-result"`
- `data-demo-id="demo-corporation-directory-tab"`
- `data-demo-id="demo-corporation-list"`
- `data-demo-id="demo-evidence-document-list"`

### 3. 나라장터 공고 검색과 선택
목표: 실제 나라장터 API 검색 조건을 입력하고, 벡트에 맞는 공고 후보를 찾는 장면을 보여줍니다.

진행:

1. 왼쪽 메뉴의 `공고 업무` 그룹에서 `나라장터 공고 검색`으로 이동합니다.
2. 업무유형을 `물품`으로 선택합니다.
3. 검색어에 `전자칠판`을 입력합니다.
4. 시작일과 종료일을 최근 180일 범위로 입력합니다.
5. 검색 버튼을 클릭합니다.
6. 검색 결과 테이블을 천천히 스크롤하거나 첫 결과에 마우스를 올려 업무유형, 공고명, 공고번호를 보여줍니다.
7. 첫 번째 결과를 클릭해 공고를 선택합니다.
8. 저장/분석 버튼을 클릭합니다.
9. 저장 또는 분석 상태가 보이면 다음 화면으로 이동합니다.

필수 selector:

- `data-demo-id="demo-nara-board-page"`
- `data-demo-id="demo-nara-business-type"`
- `data-demo-id="demo-nara-search-keyword"`
- `data-demo-id="demo-nara-search-start-date"`
- `data-demo-id="demo-nara-search-end-date"`
- `data-demo-id="demo-nara-search-submit"`
- `data-demo-id="demo-nara-result-list"`
- `data-demo-id="demo-nara-result-row"`
- `data-demo-id="demo-nara-save-analyze"`

부분 실패 처리:

- `data-demo-id="demo-nara-partial-error"`가 보이면, 일부 업무유형 조회 실패를 안내하는 장면으로 유지합니다.
- 전체 실패 시에는 기존 저장 공고 화면으로 이동해 최근 저장 공고를 선택하는 보조 흐름을 사용합니다.

### 4. 저장한 공고 확인
목표: 검색한 공고가 저장되어 후속 업무에 연결되는 것을 보여줍니다.

진행:

1. `저장한 공고` 메뉴로 이동합니다.
2. 방금 저장한 공고 또는 가장 최근 저장 공고를 선택합니다.
3. 공고 기본정보, 첨부 처리 상태, 요구조건 추출 상태를 짧게 보여줍니다.

필수 selector:

- `data-demo-id="demo-saved-notices-page"`
- `data-demo-id="demo-saved-notice-list"`
- `data-demo-id="demo-saved-notice-detail-link"`
- `data-demo-id="demo-saved-notice-detail-page"`

### 5. 기준문서 관리와 RAG 기준문서 업로드
목표: 기준문서가 별도 지식 자산으로 등록되고, 이후 판단 근거 검색에 사용되는 흐름을 보여줍니다.

진행:

1. 왼쪽 메뉴의 `기준문서 / RAG` 그룹에서 `기준문서 관리`로 이동합니다.
2. 기준문서 업로드 폼에 문서명과 버전을 입력합니다.
3. 파일 선택에서 `RAG_기준문서_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`를 선택합니다.
4. 필요하면 `OCR 강제 실행` 토글은 끄고, 일반 추출 흐름을 먼저 보여줍니다.
5. 기준문서 업로드 버튼을 클릭합니다.
6. 처리 상태에서 텍스트 추출, OCR, 청크, 인덱스 상태를 확인합니다.
7. 기준문서 상세를 열고 생성된 청크는 `더보기`로 일부만 펼칩니다.

필수 selector:

- `data-demo-id="demo-basis-documents-page"`
- `data-demo-id="demo-basis-file-input"`
- `data-demo-id="demo-basis-upload-submit"`
- `data-demo-id="demo-basis-document-list"`
- `data-demo-id="demo-basis-document-row"`
- `data-demo-id="demo-basis-document-detail"`
- `data-demo-id="demo-basis-processing-status"`
- `data-demo-id="demo-basis-processing-progress"`
- `data-demo-id="demo-basis-chunk-list-toggle"`
- `data-demo-id="demo-basis-chunk-expand"`

### 6. 부족조건 미리보기
목표: 공고 요구조건과 법인 보유자료를 비교하고, 무엇이 준비되어 있고 무엇을 확인해야 하는지 보여줍니다.

진행:

1. `공고 업무` 그룹에서 `부족조건 미리보기`로 이동합니다.
2. 공고 선택 드롭다운에서 저장한 공고를 선택합니다.
3. 법인 선택 드롭다운에서 벡트 법인을 선택합니다.
4. 비교 실행 버튼을 클릭합니다.
5. 결과 카드에서 준비 확인, 준비 필요, 사람 확인 필요 항목을 보여줍니다.
6. 요구조건 보기 버튼을 클릭해 공고 요구조건 후보 모달을 엽니다.
7. 후보명, 유형, 요구값, 원문 문장이 한 화면에서 읽히는지 확인합니다.
8. 비교 이력 보기 버튼을 클릭하고, 최근 비교 결과 상세를 연 뒤 뒤로가기 버튼으로 이력 목록으로 돌아오는 장면을 보여줍니다.

필수 selector:

- `data-demo-id="demo-notice-comparison-page"`
- `data-demo-id="demo-comparison-notice-select"`
- `data-demo-id="demo-comparison-corporation-select"`
- `data-demo-id="demo-notice-comparison-run"`
- `.result-summary-panel`
- `data-demo-id="demo-comparison-requirements-modal"`
- `data-demo-id="demo-comparison-history-open"`
- `data-demo-id="demo-comparison-history-modal"`
- `data-demo-id="demo-comparison-detail-modal"`

### 7. 판단 검토
목표: 규칙 기반 판단과 Gemini 보조 판단 결과가 사용자에게 이해 가능한 형태로 정리되는 것을 보여줍니다.

진행:

1. `공고 업무` 그룹에서 `판단 검토`로 이동합니다.
2. 공고 선택 드롭다운에서 저장한 공고를 선택합니다.
3. 법인 선택 드롭다운에서 벡트 법인을 선택합니다.
4. 판단 검토 실행 버튼을 클릭합니다.
5. 판단 결과 영역에서 준비 확인, 준비 필요, 사람 확인 필요를 명확한 사용자 문구로 보여줍니다.
6. 우선 준비 항목 카드에서 관련 조건 전체 목록을 확인합니다.
7. 기준문서 근거 보기, 공고 원문 보기, 증빙서류 보기 링크가 있으면 클릭해 모달로 원문을 확인합니다.
8. 판단 검토 실행 이력 보기 버튼을 클릭합니다.
9. 판단 실행 이력에서 항목 하나를 클릭해 판단 상세를 엽니다.
10. 판단 검토 실행 이력으로 돌아가기 버튼으로 이력 목록에 복귀합니다.

필수 selector:

- `data-demo-id="demo-judgment-runs-page"`
- `data-demo-id="demo-judgment-notice-select"`
- `data-demo-id="demo-judgment-corporation-select"`
- `data-demo-id="demo-judgment-run-create"`
- `.result-summary-panel`
- `data-demo-id="demo-judgment-history-open"`
- `data-demo-id="demo-judgment-history-modal"`
- `data-demo-id="demo-judgment-detail-modal"`
- `data-demo-id="demo-judgment-evidence-modal"`

주의:

- 내부 상태값인 `citation`, `candidate_found`, `matched`, `missing`은 화면 설명 문구로 사용하지 않습니다.
- 사용자 표시 문구는 `준비 확인`, `준비 필요`, `사람 확인 필요` 중심으로 유지합니다.

### 8. 계약서 생성
목표: 저장 공고와 법인 정보를 기반으로 DOCX 계약서 초안을 생성하고 결과를 보여줍니다.

진행:

1. `공고 업무` 그룹에서 `계약서 생성`으로 이동합니다.
2. 공고 선택에서 저장한 공고를 선택합니다.
3. 법인 선택에서 벡트 법인을 선택합니다.
4. 판단 결과 선택이 있으면 방금 생성한 판단 실행 결과를 선택합니다.
5. 계약서 미리보기 또는 생성 버튼을 클릭합니다.
6. 생성 결과 목록에서 계약서 초안 상태를 확인합니다.
7. 다운로드 버튼을 클릭해 DOCX 파일이 생성되는 흐름을 보여줍니다.

필수 selector:

- `data-demo-id="demo-contracts-page"`
- `data-demo-id="demo-contract-notice-select"`
- `data-demo-id="demo-contract-corporation-select"`
- `data-demo-id="demo-contract-judgment-select"`
- `data-demo-id="demo-contract-preview"`
- `data-demo-id="demo-contract-create"`
- `data-demo-id="demo-contract-list"`
- `data-demo-id="demo-contract-download"`

### 9. 운영 상태와 작업 이력 확인
목표: 외부 공개 전 운영자가 실패 사유와 처리 상태를 확인할 수 있다는 점을 보여줍니다.

진행:

1. `설정` 그룹에서 `운영 대시보드`로 이동합니다.
2. 최근 실패, 백업, API 연결 상태를 확인합니다.
3. `작업 이력` 메뉴로 이동합니다.
4. 최근 실행 이력과 실패 사유가 보이는지 확인합니다.

필수 selector:

- `data-demo-id="demo-operations-page"`
- `data-demo-id="demo-operations-summary"`
- `data-demo-id="demo-operation-runs-page"`
- `data-demo-id="demo-operation-error-detail"`

## 실행 명령

권장 실행 래퍼:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create-demo-video.ps1
```

`scripts/create-demo-video.ps1`의 기본값은 최신 전체 업무 흐름에 맞춥니다.

- `Mode`: `full-workflow-demo`
- `NaraKeyword`: `전자칠판`
- `NaraBusinessType`: `goods`
- `EvidenceFileLimit`: `4`

설정 파일 `scripts/demo-video.config.json`도 같은 기본값을 유지합니다. 설정 파일의 장면 목록은 현재 스크립트 장면명인 `intro`, `corporations`, `nara-board`, `saved-notice`, `basis-documents`, `notice-comparison`, `judgment-runs`, `contracts`, `operations`, `operation-runs`만 사용합니다. 예전 장면명인 `dashboard`는 사용하지 않습니다.

전체 흐름을 실제 파일과 실제 나라장터 API로 녹화:

```powershell
npm run demo:record -- --mode full-workflow-demo --nara-keyword "전자칠판" --nara-business-type goods --evidence-file-limit 4
```

나라장터 API를 사용하지 않고 UI 흐름만 점검:

```powershell
npm run demo:record -- --mode full-workflow-demo --dry-run --skip-preflight
```

특정 장면만 점검:

```powershell
npm run demo:record -- --mode full-workflow-demo --scene corporations,nara-board,basis-documents,notice-comparison,judgment-runs,contracts --dry-run --skip-preflight
```

파일 경로를 명시적으로 바꿔 실행:

```powershell
npm run demo:record -- --mode full-workflow-demo --test-doc-dir "D:\project\wisdom_procurement\source\test_doc" --rag-doc-dir "D:\project\wisdom_procurement\source\rag_doc"
```

## 실패와 보조 흐름

- 벡트 사업자등록증 파일이 없으면 스크립트는 명확한 오류를 내고 종료합니다.
- 추가 증빙자료 일부가 없으면 존재하는 파일만 선택하고 콘솔에 누락 파일을 기록합니다.
- RAG 기준문서가 없으면 기준문서 업로드 장면은 오류를 내고 종료합니다.
- 나라장터 API가 실패하면 부분 실패 배너를 보여주고, 후속 흐름은 기존 저장 공고를 이용할 수 있도록 설계합니다.
- 계약서 다운로드 이벤트가 잡히지 않으면 다운로드 버튼 클릭 장면까지만 유지하고, 콘솔에 이유를 남깁니다.

## 리뷰 체크리스트

- 법인 관리에서 실제 `증빙 업로드` 동작이 보이는가?
- `1.벡트_사업자등록증.pdf` 업로드 후 새 법인이 생성되는가?
- 추가 증빙자료가 벡트 법인에 연결되는가?
- 나라장터 공고 검색에서 `전자칠판`과 `물품` 조건이 보이는가?
- 공고 검색 결과를 실제로 클릭하고 저장/분석하는가?
- 기준문서 관리에서 `RAG_기준문서` PDF 업로드가 보이는가?
- 부족조건 미리보기와 판단 검토에서 공고/법인을 직접 선택하는가?
- 판단 검토 결과가 사용자가 이해할 수 있는 상태 문구로 표시되는가?
- 계약서 생성과 다운로드 버튼 클릭이 보이는가?
- 화면 전환 속도가 너무 빠르지 않은가?
- 설명 팝업에 금지 문구가 보이지 않는가?
- 모든 핵심 조작이 `data-demo-id` 기반으로 안정적으로 동작하는가?

## 추가하면 좋은 장면

- 기준문서 청크 더보기 버튼을 눌러 긴 문서가 한 번에 펼쳐지지 않는 UX를 보여줍니다.
- 판단 검토에서 기준문서 근거 링크를 열어 RAG가 단순 요약이 아니라 근거 확인 흐름을 제공한다는 점을 보여줍니다.
- 법인 증빙자료 관리에서 처리 상태가 `검토 대기`, `처리 완료`, `확인 필요`로 나뉘는 이유를 짧게 보여줍니다.
- 운영 대시보드에서 실패 사유와 재시도 흐름을 보여줍니다.

## Questions for Product Owner

- 벡트 법인에 가장 맞는 나라장터 검색어를 `전자칠판`으로 고정할지, `영상장치`, `교육장비`, `스마트칠판` 후보도 보조 검색어로 둘지 결정이 필요합니다.
- 계약서 생성 장면에서 실제 DOCX를 브라우저 안에서 미리보기까지 보여줄지, 다운로드 완료까지만 보여줄지 결정이 필요합니다.
- 기준문서 업로드 장면에서 OCR 강제 실행을 켤지 여부를 영상 길이 기준으로 결정해야 합니다.

---

# AI / Engineering Version (English)

## Goal
Update the interactive service demo video workflow so it records a slower, complete, real-user path through corporation onboarding, Nara notice search, basis RAG upload, comparison, judgment review, contract generation, and operations review.

## Current Navigation Contract

| Group | Routes Covered |
| --- | --- |
| Overview | Dashboard |
| Internal Admin | Corporations, Projects |
| Notice Work | Nara search, saved notices, comparison, judgment review, contracts |
| Basis / RAG | Basis documents, rule candidates, retrieval evaluations |
| Document Analysis | Uploaded documents |
| Settings | Operations, operation runs, collection runs, backups, integrations, external access |

## Recording Policy

- Use `data-demo-id` selectors first.
- Use text or route fallback only when selector is missing.
- Keep transitions slow enough for viewers to understand menu movement.
- Do not use the Korean forbidden overlay word in the script.
- Record real interactions: file upload, dropdown selection, search, row selection, run execution, modal open, download click.

## Required Files

- Business registration: `source/test_doc/1.벡트_사업자등록증.pdf`
- Supporting evidence:
  - `source/test_doc/2.중소기업확인서_중기업_20260331.pdf`
  - `source/test_doc/20250226_(주)벡트_직생(동영상제작).pdf`
  - `source/test_doc/소프트웨어사업자확인서(2023결산)_벡트.pdf`
  - `source/test_doc/정보통신공사업등록증_벡트.pdf`
  - `source/test_doc/ISO9001인증서_20270731.pdf`
  - `source/test_doc/녹색기술제품확인서_20240523_(주)벡트_UITL86GZA5W외 3제품.pdf`
- Basis document: `source/rag_doc/RAG_기준문서_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`

## Scenario Steps

1. Dashboard orientation.
2. Corporation registration and evidence upload.
3. Nara notice search with `business_type=goods` and keyword `전자칠판`.
4. Saved notice confirmation.
5. Basis document upload and processing status review.
6. Notice comparison run and history/detail modal review.
7. Judgment review run with Gemini-assisted explanation and evidence links.
8. Contract generation and DOCX download click.
9. Operations dashboard and operation history review.

## Commands

Recommended wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create-demo-video.ps1
```

The wrapper and `scripts/demo-video.config.json` must default to `full-workflow-demo`, keyword `전자칠판`, business type `goods`, and evidence file limit `4`.

```powershell
npm run demo:record -- --mode full-workflow-demo --nara-keyword "전자칠판" --nara-business-type goods --evidence-file-limit 4
```

```powershell
npm run demo:record -- --mode full-workflow-demo --dry-run --skip-preflight
```

## Test Expectations

- `scripts/create-service-demo-video.mjs` must expose `full-workflow-demo`.
- The script must include helpers for selecting dropdowns and clicking first visible demo selectors.
- The script must include dedicated functions for corporation onboarding, basis upload, Nara search, comparison, judgment, and contract generation.
- The plan and script must reference the VECT files, the RAG basis file, `전자칠판`, and `goods`.
- The script must avoid the forbidden Korean overlay word.
- Contract tests should verify these requirements.
