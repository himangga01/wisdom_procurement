# 서비스 시연 영상 인터랙티브 녹화 구현계획

## 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기` 시연 영상을 단순 화면 이동형 녹화에서 실제 사용자가 조작하는 것처럼 보이는 인터랙티브 녹화로 보강하기 위한 구현계획입니다.

현재 기본 영상 생성 도구는 `stable-demo` 방식으로 동작합니다. 이 방식은 백엔드 API로 데모 데이터를 먼저 만들고, Playwright가 화면 경로를 이동하며 녹화합니다. 안정적이지만, 보는 사람이 “어느 메뉴를 클릭했고 어떤 버튼을 눌렀는지”를 따라가기 어렵습니다.

이번 보강의 목표는 다음입니다.

- 실제 버튼 클릭 장면을 보여준다.
- 실제 파일 업로드 장면을 보여준다.
- 실제 `source/test_doc/` PDF OCR 처리 장면을 보여준다.
- 실시간 나라장터 API 검색 장면을 보여준다.
- 화면 문구가 바뀌어도 안정적으로 녹화할 수 있도록 `data-demo-id` selector를 추가한다.
- 마우스 포인터와 클릭 효과를 영상에 표시해 시청자가 이동 흐름을 이해하게 한다.

## 현재 상태
이미 구현된 영상 생성 파일은 다음입니다.

- `scripts/create-service-demo-video.mjs`
- `scripts/prepare-service-demo-data.mjs`
- `scripts/render-service-demo-video.mjs`
- `scripts/inspect-service-demo-video.mjs`
- `scripts/demo-video-utils.mjs`
- `scripts/create-demo-video.ps1`
- `scripts/demo-video.config.json`

현재 가능한 것:

- API 기반 데모 데이터 생성
- Playwright Chromium 녹화
- WebM 생성
- MP4 변환
- FFprobe 검사
- scene별 screenshot/report 생성

현재 부족한 것:

- 메뉴 클릭 이동 장면
- 실제 버튼 클릭 장면
- 실제 파일 선택/업로드 장면
- OCR 진행 상태 polling
- 실시간 나라장터 검색 클릭 흐름
- 영상에 보이는 마우스 포인터
- 안정적인 `data-demo-id` selector 계약

## 구현 목표

## 이번 구현 범위
이번 작업은 시연 영상 자동화의 기반을 먼저 안정화하는 범위로 진행합니다.

즉시 구현하는 항목:

- 주요 메뉴와 시연 화면에 `data-demo-id` selector를 추가한다.
- Playwright 녹화 스크립트에 `interactive-demo`, `real-pdf-demo`, `live-nara-demo` 모드 인자를 추가한다.
- `interactive-demo`에서는 왼쪽 메뉴 클릭 이동, 버튼 클릭, 마우스 포인터 이동/클릭 ripple을 실제 영상에 보이게 한다.
- `real-pdf-demo`와 `live-nara-demo`는 실제 업로드/실시간 검색 장면을 실행할 수 있는 함수와 dry-run 경로를 추가한다.
- 실제 OCR 장시간 처리와 실시간 나라장터 API 실패 가능성은 영상 report의 warning/fallback으로 기록한다.
- 정적 계약 테스트로 필수 selector가 사라지지 않도록 막는다.

이번 작업에서 의도적으로 분리하는 항목:

- 모든 `source/test_doc/` PDF를 영상에서 전부 OCR 처리하지 않는다. 영상은 대표 PDF 1개 업로드 장면을 우선 지원한다.
- 실시간 나라장터 API가 실패했을 때 영상을 실패로 끝내지 않고, 경고를 기록한 뒤 seeded demo 화면으로 fallback할 수 있게 한다.
- 계약서 다운로드 파일을 실제로 열어 보여주는 장면은 다음 영상 보강 단계로 분리한다.

## 1. 녹화 모드 확장
`scripts/create-service-demo-video.mjs`의 `--mode`를 명확히 지원합니다.

### `stable-demo`
현재 기본 방식입니다.

- API로 데모 데이터를 먼저 생성
- 화면 경로를 직접 이동
- 가장 안정적인 발표/공유용 기본 영상
- 외부 API, 긴 OCR 작업에 의존하지 않음

### `interactive-demo`
새로 추가할 사용자 조작형 기본 영상입니다.

- 왼쪽 메뉴를 실제 클릭하며 이동
- 주요 버튼 클릭 장면 표시
- 마우스 포인터 오버레이 표시
- 데이터 생성은 여전히 API 기반으로 먼저 준비할 수 있음
- 장면 설명보다 “사용자가 어디를 눌렀는지”를 더 잘 보여주는 영상

### `real-pdf-demo`
실제 법인 증빙 PDF 처리 장면을 보여주는 확장 영상입니다.

- `source/test_doc/`의 실제 PDF 사용
- 법인 증빙 업로드 input에 실제 파일 지정
- 업로드 버튼 클릭
- OCR/파싱/분류 상태 polling
- 처리 결과 또는 검토 필요 상태 표시

### `live-nara-demo`
실시간 나라장터 API 검색을 보여주는 확장 영상입니다.

- 나라장터 검색 화면에서 업무유형 선택
- 검색어/기간 입력
- 검색 버튼 클릭
- 결과 row 표시
- 저장/분석 버튼 클릭
- 저장 공고 상세 이동
- API 실패 시 partial error 또는 fallback 표시

## 2. 마우스 포인터 오버레이
Playwright 녹화에서 실제 OS 마우스 포인터는 안정적으로 보이지 않을 수 있습니다. 따라서 브라우저 DOM 위에 데모 전용 포인터를 표시합니다.

추가할 함수:

```js
async function installDemoCursor(page)
async function moveCursorTo(page, locator, options)
async function clickWithCursor(page, locator, options)
async function typeWithCursor(page, locator, text, options)
```

동작:

- 화면 위에 작은 포인터 DOM을 고정 표시
- 클릭 대상 중앙으로 부드럽게 이동
- 클릭 시 원형 ripple 표시
- 클릭한 메뉴/버튼이 화면에서 강조되도록 짧은 지연 추가
- screenshot과 video에 포인터가 함께 찍히도록 구현

포인터 스타일:

- 흰색 또는 밝은 계열 포인터
- 파란색 외곽선
- 클릭 시 파란색 ripple
- `pointer-events: none`
- z-index 최상위

## 3. 메뉴 클릭 기반 이동
현재 `stable-demo`는 `page.goto(route)`로 이동합니다. `interactive-demo`에서는 가능하면 왼쪽 메뉴를 실제 클릭합니다.

클릭 이동 대상:

- 대시보드
- 운영 대시보드
- 작업 이력
- 나라장터 공고 검색
- 저장한 공고
- 부족조건 미리보기
- 판단 검토
- 계약서 생성
- 기준문서 관리
- 법인 관리

동적 상세 화면 처리:

- 저장 공고 상세:
  - `저장한 공고` 메뉴 클릭
  - 시연 공고 row 또는 상세 링크 클릭
- 계약서 생성:
  - `계약서 생성` 메뉴 클릭
  - 필요 시 query param route로 보정
- 기준문서 상세:
  - `기준문서 관리` 메뉴 클릭
  - 시연 기준문서 row 클릭 또는 목록에서 확인

추가할 함수:

```js
async function navigateBySidebar(page, demoId)
async function openSavedNoticeDetail(page, data)
async function openContractScene(page, data)
async function openBasisDocumentScene(page, data)
```

## 4. `data-demo-id` selector 추가 계획
화면 문구가 바뀌어도 Playwright가 안정적으로 동작하도록 핵심 UI에 `data-demo-id`를 추가합니다.

## 사이드바 selector

| 화면 | selector |
| --- | --- |
| 대시보드 | `sidebar-dashboard` |
| 운영 대시보드 | `sidebar-operations` |
| 작업 이력 | `sidebar-operation-runs` |
| 백업/복원 | `sidebar-backups` |
| 나라장터 공고 검색 | `sidebar-nara-board` |
| 저장한 공고 | `sidebar-nara-saved-notices` |
| 부족조건 미리보기 | `sidebar-notice-comparison` |
| 판단 검토 | `sidebar-judgment-runs` |
| 계약서 생성 | `sidebar-contracts` |
| 자동 수집 관리 | `sidebar-nara-collection-runs` |
| 문서 업로드 | `sidebar-documents` |
| 기준문서 관리 | `sidebar-basis-documents` |
| 규칙 후보 관리 | `sidebar-basis-rule-candidates` |
| 검색 평가 | `sidebar-basis-retrieval-evaluations` |
| 법인 관리 | `sidebar-corporations` |
| 프로젝트 관리 | `sidebar-projects` |
| API 설정 | `sidebar-settings-nara` |
| 외부 접속 | `sidebar-settings-external-access` |

## 법인/증빙 화면 selector

| 목적 | selector |
| --- | --- |
| 법인/증빙 페이지 루트 | `demo-corporations-page` |
| 증빙 업로드 탭 | `demo-corporation-evidence-upload-tab` |
| 추출값 검토 탭 | `demo-corporation-evidence-review-tab` |
| 증빙자료 관리 탭 | `demo-corporation-evidence-library-tab` |
| 법인 목록/준비도 탭 | `demo-corporation-directory-tab` |
| 증빙 파일 input | `demo-evidence-file-input` |
| 증빙 업로드 버튼 | `demo-evidence-upload-submit` |
| 최신 증빙 결과 | `demo-latest-evidence-result` |
| 증빙 목록 | `demo-evidence-document-list` |
| 법인 목록 | `demo-corporation-list` |

## 나라장터 검색 selector

| 목적 | selector |
| --- | --- |
| 나라장터 검색 페이지 루트 | `demo-nara-board-page` |
| 업무유형 선택 | `demo-nara-business-type` |
| 검색어 입력 | `demo-nara-search-keyword` |
| 시작일 입력 | `demo-nara-search-start-date` |
| 종료일 입력 | `demo-nara-search-end-date` |
| 검색 버튼 | `demo-nara-search-submit` |
| 검색 결과 목록 | `demo-nara-result-list` |
| 검색 결과 row | `demo-nara-result-row` |
| 저장/분석 버튼 | `demo-nara-save-analyze` |
| partial error 배너 | `demo-nara-partial-error` |

## 저장 공고 selector

| 목적 | selector |
| --- | --- |
| 저장 공고 목록 | `demo-saved-notice-list` |
| 저장 공고 row | `demo-saved-notice-row` |
| 저장 공고 상세 링크 | `demo-saved-notice-detail-link` |
| 저장 공고 상세 페이지 | `demo-saved-notice-detail-page` |
| 요구조건 후보 영역 | `demo-notice-requirements` |
| 첨부 분석 상태 | `demo-notice-attachment-status` |

## 기준문서/RAG selector

| 목적 | selector |
| --- | --- |
| 기준문서 페이지 루트 | `demo-basis-documents-page` |
| 기준문서 파일 input | `demo-basis-file-input` |
| OCR 강제 실행 토글 | `demo-basis-force-ocr-toggle` |
| 기준문서 업로드 버튼 | `demo-basis-upload-submit` |
| 기준문서 목록 | `demo-basis-document-list` |
| 기준문서 row | `demo-basis-document-row` |
| 처리 상태 영역 | `demo-basis-processing-status` |
| 청크 목록 | `demo-basis-chunk-list` |
| 청크 더보기 버튼 | `demo-basis-chunk-expand` |

## 부족조건/판단 selector

| 목적 | selector |
| --- | --- |
| 부족조건 미리보기 페이지 | `demo-notice-comparison-page` |
| 공고 선택 | `demo-comparison-notice-select` |
| 법인 선택 | `demo-comparison-corporation-select` |
| 비교 실행 버튼 | `demo-notice-comparison-run` |
| 비교 결과 요약 | `demo-comparison-summary` |
| 판단 검토 페이지 | `demo-judgment-runs-page` |
| 판단 실행 버튼 | `demo-judgment-run-create` |
| 판단 결과 목록 | `demo-judgment-run-list` |
| citation 후보 영역 | `demo-judgment-citation-candidates` |

## 계약서 selector

| 목적 | selector |
| --- | --- |
| 계약서 페이지 | `demo-contracts-page` |
| 공고 선택 | `demo-contract-notice-select` |
| 법인 선택 | `demo-contract-corporation-select` |
| 판단 run 선택 | `demo-contract-judgment-select` |
| 미리보기 버튼 | `demo-contract-preview` |
| 생성 버튼 | `demo-contract-create` |
| 계약서 목록 | `demo-contract-list` |
| 다운로드 링크 | `demo-contract-download` |

## 운영 selector

| 목적 | selector |
| --- | --- |
| 운영 대시보드 페이지 | `demo-operations-page` |
| 운영 요약 카드 | `demo-operations-summary` |
| 작업 이력 페이지 | `demo-operation-runs-page` |
| 작업 이력 목록 | `demo-operation-run-list` |
| 작업 이력 row | `demo-operation-run-row` |
| 실패 사유 영역 | `demo-operation-error-detail` |

## 5. 실제 버튼 클릭 장면
`interactive-demo`에서는 아래 액션을 실제 클릭합니다.

- 왼쪽 메뉴 클릭
- 탭 클릭
- 검색 버튼 클릭
- 저장/분석 버튼 클릭
- 기준문서 청크 더보기 클릭
- 비교 실행 버튼 클릭
- 판단 실행 버튼 클릭
- 계약서 미리보기/생성 버튼 클릭
- 작업 이력 row 클릭

모든 클릭은 `clickWithCursor()`를 통해 실행합니다.

## 6. 실제 파일 업로드 장면
파일 업로드는 Playwright의 `setInputFiles()`로 처리합니다.

법인 증빙 업로드 흐름:

```text
법인 관리 메뉴 클릭
-> 증빙 업로드 탭 클릭
-> 파일 input에 source/test_doc PDF 지정
-> 업로드 버튼 클릭
-> 처리 완료 또는 검토 필요 상태 polling
-> 증빙자료 관리 탭에서 업로드 이력 확인
```

기준문서 업로드 흐름:

```text
기준문서 관리 메뉴 클릭
-> 기준문서 PDF input 지정
-> OCR 강제 실행 옵션 선택 여부 표시
-> 업로드 또는 재처리 실행
-> parse/OCR/chunk/index 상태 polling
-> 청크 더보기 클릭
```

## 7. 실제 `source/test_doc/` PDF OCR 처리 장면
`real-pdf-demo`는 실제 PDF 처리 시간이 길 수 있으므로 별도 timeout 정책을 둡니다.

기본 정책:

- 파일별 timeout: 180초
- 전체 evidence scene timeout: 10분
- 처리 완료 상태: `completed`, `classified`, `manual`, `needs_review`
- 실패 상태: `failed`, `needs_ocr_setup`, `unavailable`
- timeout 시 현재까지의 상태를 report에 기록하고 다음 장면으로 넘어갈지 실패 처리할지 옵션으로 제어

추천 샘플:

- `source/test_doc/1.벡트_사업자등록증.pdf`
- `source/test_doc/2.중소기업확인서_중기업_20260331.pdf`
- `source/test_doc/20250226_(주)벡트_직생(동영상제작).pdf`
- `source/test_doc/기업신용평가등급확인서_벡트(공공기관 제출용).pdf`

## 8. 실시간 나라장터 API 검색 장면
`live-nara-demo`는 실제 API 상태에 영향을 받으므로 fallback 정책을 둡니다.

흐름:

```text
나라장터 공고 검색 메뉴 클릭
-> 업무유형 전체 또는 용역/물품 선택
-> 검색어 입력
-> 기간 입력
-> 검색 버튼 클릭
-> 결과 row 확인
-> 저장/분석 클릭
-> 저장 공고 상세 이동
```

preflight:

- `NARA_API_SERVICE_KEY` 설정 확인
- `/api/settings/integrations/nara/status` 정상 확인
- 검색 API 응답 확인

fallback:

- API 응답이 `partial_failed`이면 경고 배너를 영상에 포함
- 전체 실패 시 seeded stable notice로 이동
- 실패 원인은 `artifacts/demo-video/latest-report.json`에 기록

## 9. Playwright 스크립트 변경 계획
대상 파일:

- `scripts/create-service-demo-video.mjs`
- 필요 시 `scripts/prepare-service-demo-data.mjs`

추가할 구조:

```js
const DEMO_SELECTORS = { ... }

async function installDemoCursor(page) {}
async function moveCursorTo(page, locator, options = {}) {}
async function clickWithCursor(page, locator, options = {}) {}
async function typeWithCursor(page, locator, text, options = {}) {}

async function navigateBySidebar(page, selectorKey) {}
async function runStableScene(page, scene, data) {}
async function runInteractiveScene(page, scene, data) {}
async function runRealPdfEvidenceScene(page, data) {}
async function runLiveNaraSearchScene(page, data) {}
async function waitForProcessingStatus(page, locator, statuses, options = {}) {}
```

mode별 정책:

| mode | 데이터 생성 | 이동 방식 | 파일 업로드 | 라이브 API | 포인터 |
| --- | --- | --- | --- | --- | --- |
| `stable-demo` | API seed | route 직접 이동 | 없음 | 없음 | 선택 |
| `interactive-demo` | API seed | 메뉴/버튼 클릭 우선 | 선택 | 없음 | 필수 |
| `real-pdf-demo` | API seed + 실제 업로드 | 메뉴/버튼 클릭 | 필수 | 없음 | 필수 |
| `live-nara-demo` | API seed + live search | 메뉴/버튼 클릭 | 선택 | 필수 | 필수 |

## 10. 프론트엔드 변경 계획
대상 파일:

- `frontend/src/app/App.tsx`
- `frontend/src/pages/CorporationsPage.tsx`
- `frontend/src/pages/NaraBoardPage.tsx`
- `frontend/src/pages/NaraSavedNoticesPage.tsx`
- `frontend/src/pages/NaraSavedNoticeDetailPage.tsx`
- `frontend/src/pages/BasisDocumentsPage.tsx`
- `frontend/src/pages/NoticeComparisonPage.tsx`
- `frontend/src/pages/JudgmentRunsPage.tsx`
- `frontend/src/pages/ContractsPage.tsx`
- `frontend/src/pages/OperationsPage.tsx`
- `frontend/src/pages/OperationRunsPage.tsx`

변경 원칙:

- 기존 UX를 바꾸지 않는다.
- `data-demo-id`만 추가한다.
- selector는 기능 의미 중심으로 짓는다.
- 반복 row에는 같은 `data-demo-id`와 `data-demo-key` 또는 `data-demo-row-id`를 함께 둘 수 있다.
- 버튼 문구가 바뀌어도 Playwright는 `data-demo-id`를 우선 사용한다.

## 11. 테스트 계획

## 정적 계약 테스트
`backend/tests/test_frontend_contracts.py`에 추가합니다.

검증:

- 필수 sidebar `data-demo-id` 존재
- 각 주요 페이지 루트 `data-demo-id` 존재
- 업로드 input selector 존재
- 검색/저장/분석 버튼 selector 존재
- 계약서 미리보기/생성 selector 존재
- 작업 이력 list/row selector 존재

## 영상 dry-run 테스트

```powershell
cd frontend
npm run demo:record -- --mode interactive-demo --dry-run --scene intro,corporations
npm run demo:record -- --mode interactive-demo --dry-run --scene nara-board
npm run demo:record -- --mode real-pdf-demo --dry-run --scene corporations
npm run demo:record -- --mode live-nara-demo --dry-run --scene nara-board
```

## 전체 영상 테스트

```powershell
cd frontend
npm run demo:preflight
npm run demo:record -- --mode interactive-demo
npm run demo:render
npm run demo:inspect
```

## 일반 검증

```powershell
py -3.13 -m unittest tests.test_frontend_contracts -v
npm run build
py -3.13 scripts\check-encoding.py
git diff --check
```

## 12. 구현 순서

1. 프론트엔드 핵심 요소에 `data-demo-id` 추가
2. 정적 계약 테스트 추가
3. Playwright 마우스 포인터 오버레이 구현
4. `clickWithCursor`, `typeWithCursor`, `navigateBySidebar` 구현
5. `interactive-demo` 모드 구현
6. 실제 파일 업로드 장면 구현
7. `real-pdf-demo` 모드 구현
8. 실시간 나라장터 검색 장면 구현
9. `live-nara-demo` 모드 구현
10. dry-run으로 장면별 검증
11. 실제 MP4 생성
12. 문서와 work-log 업데이트

## 13. 위험과 대응

| 위험 | 대응 |
| --- | --- |
| 실제 OCR 시간이 길다 | `real-pdf-demo`를 별도 영상으로 분리하고 timeout/fallback 적용 |
| 나라장터 API 응답이 불안정하다 | `live-nara-demo`는 선택 모드로 두고 stable fixture fallback 적용 |
| 화면 문구가 바뀌어 Playwright가 깨진다 | 핵심 요소는 `data-demo-id` selector 우선 사용 |
| 마우스 포인터가 화면을 가린다 | pointer 위치와 overlay 위치를 분리하고 작은 크기로 유지 |
| 실제 클릭 장면이 테스트 데이터를 중복 생성한다 | seed/reuse/reset 옵션을 유지하고 report에 생성 ID 기록 |
| ngrok 환경에서 요청이 막힌다 | Vite allowedHosts, CORS, `ngrok-skip-browser-warning` 검증 유지 |

## 14. 완료 기준

- `interactive-demo` 영상에서 왼쪽 메뉴 이동과 클릭 포인터가 보인다.
- 주요 버튼 클릭 장면이 최소 5개 이상 포함된다.
- `real-pdf-demo`에서 `source/test_doc/` PDF 업로드 장면이 동작한다.
- `live-nara-demo`에서 나라장터 API 검색 장면이 동작하거나 명확한 fallback을 기록한다.
- 모든 핵심 Playwright selector가 `data-demo-id` 기반으로 검증된다.
- `npm run demo:inspect`가 `passed`를 반환한다.
- `docs/work-log.md`에 구현과 검증 결과가 기록된다.

## Questions for Product Owner

- 실제 OCR 장면을 공식 메인 영상에 넣을까요, 아니면 별도 보강 영상으로 둘까요?
- 실시간 나라장터 API 검색 실패 장면도 자연스러운 운영 사례로 보여줄까요, 아니면 항상 fallback으로 숨길까요?
- 영상 길이는 1분 내외로 압축할까요, 아니면 3~5분 제품 시연형으로 갈까요?

---

# AI / Engineering Version (English)

## Purpose
This document defines the implementation plan for upgrading the current demo recording pipeline from route-based stable recording to interactive, user-like video capture.

The requested scope is:

- show real button clicks
- show real file uploads
- show actual `source/test_doc/` PDF OCR processing
- show live Nara API search
- add stable `data-demo-id` selectors so Playwright remains reliable when UI copy changes
- show a visible mouse cursor and click ripple in the recorded video

## Current State
Existing scripts:

- `scripts/create-service-demo-video.mjs`
- `scripts/prepare-service-demo-data.mjs`
- `scripts/render-service-demo-video.mjs`
- `scripts/inspect-service-demo-video.mjs`
- `scripts/demo-video-utils.mjs`
- `scripts/create-demo-video.ps1`
- `scripts/demo-video.config.json`

Current capability:

- seed demo data through backend APIs
- record the app with Playwright Chromium
- generate WebM
- render MP4
- inspect MP4 with FFprobe
- save scene screenshots and JSON reports

Missing capability:

- menu-click navigation
- real button-click scenes
- real file upload scenes
- OCR polling
- live Nara search flow
- visible cursor overlay
- stable `data-demo-id` selector contract

## Target Modes

| mode | Purpose |
| --- | --- |
| `stable-demo` | deterministic recording using seeded data and direct route navigation |
| `interactive-demo` | user-like recording with sidebar clicks, button clicks, and visible cursor |
| `real-pdf-demo` | actual `source/test_doc/` PDF upload and OCR/classification scenes |
| `live-nara-demo` | live Nara API search, save/analyze, and fallback handling |

## Required Playwright Additions

```js
async function installDemoCursor(page) {}
async function moveCursorTo(page, locator, options = {}) {}
async function clickWithCursor(page, locator, options = {}) {}
async function typeWithCursor(page, locator, text, options = {}) {}
async function navigateBySidebar(page, selectorKey) {}
async function runInteractiveScene(page, scene, data) {}
async function runRealPdfEvidenceScene(page, data) {}
async function runLiveNaraSearchScene(page, data) {}
async function waitForProcessingStatus(page, locator, statuses, options = {}) {}
```

## Required Frontend Selector Additions

Add `data-demo-id` attributes to:

- sidebar nav items
- corporation evidence upload controls
- Nara search controls
- saved notice list/detail
- basis document upload/status/chunk controls
- comparison/judgment controls
- contract preview/create/download controls
- operations and operation-runs lists

## Test Plan

Static tests:

```powershell
py -3.13 -m unittest tests.test_frontend_contracts -v
```

Dry-run tests:

```powershell
cd frontend
npm run demo:record -- --mode interactive-demo --dry-run --scene intro,corporations
npm run demo:record -- --mode real-pdf-demo --dry-run --scene corporations
npm run demo:record -- --mode live-nara-demo --dry-run --scene nara-board
```

Full video:

```powershell
cd frontend
npm run demo:preflight
npm run demo:record -- --mode interactive-demo
npm run demo:render
npm run demo:inspect
```

General validation:

```powershell
npm run build
py -3.13 scripts\check-encoding.py
git diff --check
```

## Done Criteria

- visible cursor and click ripple appear in the recording
- sidebar menu navigation is shown
- key actions are clicked through Playwright
- actual file upload is supported
- real PDF OCR flow is supported in `real-pdf-demo`
- live Nara search is supported in `live-nara-demo`
- required selectors are tested through frontend contract tests
- MP4 inspection passes
- `docs/work-log.md` records implementation and verification results
