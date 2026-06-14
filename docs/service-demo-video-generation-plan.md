# 한국어 버전

## 문서 목적
이 문서는 `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 기준으로, `SMART 조달청 계산기`가 실제로 동작하는 모습을 동영상으로 생성하기 위한 지원 가능성 검토와 구현 계획을 정리한다.

## 결론
현재 코드 상태 기준으로 시연 영상 생성은 지원 가능하다.

프론트엔드가 React/Vite로 구성되어 있고, 이미 Playwright 기반 UX 테스트 스크립트가 존재하므로 브라우저 자동 조작과 화면 녹화를 같은 계층에서 구현할 수 있다. 최근 `source/test_doc/` 실제 PDF 테스트로 법인 증빙자료 업로드/분류/OCR 흐름도 데모 데이터로 사용할 수 있는 상태가 되었다.

권장 방식은 다음과 같다.

1. 로컬 백엔드와 프론트엔드를 실행한다.
2. Playwright가 브라우저를 열고 시연 흐름대로 화면을 조작한다.
3. Playwright의 `recordVideo` 기능으로 각 시연 장면을 WebM으로 저장한다.
4. FFmpeg로 장면을 병합하고, 필요한 경우 제목/자막/속도 조절/MP4 변환을 수행한다.
5. 최종 결과물을 `artifacts/demo-video/` 아래에 저장한다.

## 재검토 결과

기존 계획은 영상 생성 가능성과 큰 흐름은 맞지만, 실제 구현을 바로 시작하기에는 다음 내용이 부족했다.

- 영상 녹화 전에 서비스 로직이 정상인지 확인하는 preflight 절차가 약했다.
- 실시간 나라장터 API, 실제 PDF OCR, 이미 저장된 데모 데이터 중 어떤 모드를 기본값으로 쓸지 명확하지 않았다.
- 장면별로 어떤 화면/데이터/성공 신호를 기다려야 하는지 정의가 부족했다.
- Playwright가 클릭할 안정적인 selector 정책이 없었다.
- 긴 OCR/분석 작업이 끝날 때까지 기다리는 방식과 timeout/fallback 정책이 부족했다.
- 녹화 산출물의 품질 검증 기준이 단순히 “파일 생성” 수준에 머물렀다.
- 실패 시 trace, screenshot, API 응답, 단계별 로그를 남기는 구조가 더 필요했다.

보강 방향은 다음과 같다.

1. `제품 시연 흐름` 파이프라인 테스트를 영상 녹화 전 필수 preflight로 사용한다.
2. 기본 영상은 `stable-demo` 모드로 만든다.
3. 실제 PDF/OCR과 실시간 나라장터 API는 선택 모드로 분리한다.
4. 장면별 성공 신호를 API 응답과 화면 텍스트로 이중 확인한다.
5. 녹화 실패 시 재현 가능한 리포트를 남긴다.

## 영상 생성 모드

### 1. `stable-demo` 모드
- 목적: 반복 가능한 1차 공식 데모 영상 생성
- 데이터:
  - 테스트용 법인/공고/기준문서/판단/계약서 데이터를 스크립트가 API로 생성
  - 실제 외부 API 호출 없음
  - OCR 장시간 대기 없음
- 장점:
  - 가장 안정적
  - CI 또는 다른 PC에서도 재현 가능
  - 영상 녹화 실패 원인을 UI/스크립트 문제로 좁히기 쉬움
- 기본값:
  - 첫 구현은 이 모드로 한다.

### 2. `real-pdf-demo` 모드
- 목적: 실제 법인 증빙 PDF 처리 장면을 보여주는 운영형 데모
- 데이터:
  - `source/test_doc/`에서 선별한 PDF 사용
  - 권장 샘플:
    - `1.벡트_사업자등록증.pdf`
    - `2.중소기업확인서_중기업_20260331.pdf`
    - `20250226_(주)벡트_직생(동영상제작).pdf`
    - `기업신용평가등급확인서_벡트(공공기관 제출용).pdf`
    - `정보통신공사업등록증_벡트.pdf`
    - `특허증_IR센서의 교체가 용이한 구조가 적용된 프레임을 포함하는 전자칠판.pdf`
- 주의:
  - PaddleOCR 실행 시간이 길 수 있다.
  - 영상에서는 OCR 진행 상태와 완료 결과를 모두 보여주되, 전체 대기 시간을 그대로 노출하지 않도록 장면 분리 또는 배속을 적용한다.

### 3. `live-nara-demo` 모드
- 목적: 나라장터 실시간 API 검색 장면을 보여주는 데모
- 데이터:
  - `business_type=all`, `service`, `goods` 검색을 활용
  - API 실패 시 저장된 demo notice로 fallback
- 주의:
  - 공공데이터 포털 응답 지연, 점검, 키 제한에 따라 실패할 수 있다.
  - 공식 발표/공유 영상은 `stable-demo` 또는 이미 저장된 공고 기반으로 만드는 편이 안전하다.

## 사전 검증 기준

영상 녹화 전에 다음 테스트가 통과해야 한다.

```powershell
cd backend
py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v
cd ..
npm run build
py -3.13 scripts\check-encoding.py
git diff --check
```

이 preflight가 실패하면 영상 녹화를 시작하지 않는다.

## 현재 서비스 기준 지원 범위

### 지원 가능
- 법인 관리 화면에서 법인 등록
- `source/test_doc/` PDF 증빙자료 업로드
- 증빙자료 자동 분류, OCR, 후보값 확인
- 대시보드 상태 확인
- 나라장터 공고 검색, 업무유형 선택, 저장
- 저장 공고 상세에서 요구조건 후보 확인
- 기준문서 업로드, OCR 강제 실행 옵션, 처리 상태 확인
- 부족조건 미리보기 또는 판단 검토 실행
- 계약서 DOCX 초안 생성
- 운영 대시보드와 작업 이력 확인

### 영상화 시 주의할 점
- 나라장터 실시간 API는 네트워크와 공공데이터 포털 상태에 따라 응답이 흔들릴 수 있다.
- 기준문서 PDF OCR은 긴 문서일수록 오래 걸리므로 영상에서는 이미 처리된 기준문서 또는 짧은 샘플 기준문서로 먼저 구성하는 편이 안정적이다.
- OCR/LLM/나라장터 API 키 원문은 포탈에 마스킹되어야 하며, 녹화 스크립트는 `.env` 파일이나 원문 로그 화면을 열지 않는다.
- 실제 시연 영상은 “최종 합격 판정”이 아니라 “부족조건과 확인 필요 항목을 찾는 업무 보조”로 표현해야 한다.

## 시연 영상 구성

### 전체 길이
권장 길이: 4분 30초 ~ 6분

너무 길게 모든 OCR 완료를 기다리는 영상보다, 핵심 흐름을 빠르게 보여주고 시간이 오래 걸리는 작업은 진행 상태와 완료 결과를 함께 보여주는 편이 적합하다.

### 장면 0. 오프닝
- 화면: 로고 또는 대시보드 첫 화면
- 목적: 서비스 정체성 전달
- 자막: `SMART 조달청 계산기 - 공고, 법인 증빙, 기준문서, 계약서 초안을 한 흐름으로 관리합니다.`
- 예상 길이: 10초

### 장면 1. 법인을 등록하고 증빙자료를 준비합니다
- 화면: `법인 관리`
- 동작:
  - 데모 법인 생성 또는 기존 데모 법인 선택
  - `source/test_doc/1.벡트_사업자등록증.pdf` 업로드
  - 추가 증빙으로 `중소기업확인서`, `직접생산확인증명서`, `기업신용평가등급확인서`, `특허증` 중 2~3개 업로드
  - 자동 분류와 후보값 표시 확인
- 강조:
  - 사용자가 승인한 값만 법인 프로필에 반영
  - 증빙 PDF OCR/분류가 실제로 작동
- 예상 길이: 55초

### 장면 2. 대시보드에서 오늘 확인할 업무를 봅니다
- 화면: `대시보드`
- 동작:
  - 최근 공고, 최근 문서, 법인 준비 상태, 운영 상태 확인
- 강조:
  - 업무 시작 화면에서 오늘 볼 대상을 찾을 수 있음
- 예상 길이: 25초

### 장면 3. 나라장터 공고를 검색하고 저장합니다
- 화면: `나라장터 공고 검색`
- 동작:
  - 업무유형 `전체` 또는 데모에 맞는 `용역/물품` 선택
  - 키워드 검색
  - 결과에서 공고 선택
  - 저장/분석 실행
- 강조:
  - 공사/용역/물품/기타 확장 검색
  - 저장 후 첨부 문서 분석 흐름 연결
- 예상 길이: 50초

### 장면 4. 저장한 공고의 요구조건 후보를 확인합니다
- 화면: `저장한 공고 상세`
- 동작:
  - 공고 기본정보 확인
  - 첨부 분석 상태 확인
  - 요구조건 후보, 제출서류, 제한조건 영역 확인
- 강조:
  - 공고문에서 놓치기 쉬운 조건을 후보로 정리
- 예상 길이: 40초

### 장면 5. 기준문서를 업로드하고 검색 가능한 지식으로 만듭니다
- 화면: `기준문서 관리`
- 동작:
  - 기준문서 목록 또는 업로드 화면 진입
  - 기준문서 처리 상태 확인
  - 청크/인덱스 상태와 OCR 상태 확인
  - 검색 예시 실행
- 강조:
  - PDF 기준문서가 RAG 검색 가능한 JSON basis index로 변환됨
  - 긴 문서도 처리 진행 상태를 볼 수 있음
- 예상 길이: 45초

### 장면 6. 공고와 법인을 비교해 부족조건을 확인합니다
- 화면: `부족조건 미리보기` 또는 `판단 검토`
- 동작:
  - 저장 공고와 데모 법인 선택
  - 부족조건 미리보기 실행
  - 준비됨/부족/확인 필요/citation 후보 확인
- 강조:
  - 합격 단정이 아니라 준비해야 할 조건을 찾는 흐름
  - 기준문서 근거 후보를 함께 확인
- 예상 길이: 55초

### 장면 7. 계약서 초안을 생성합니다
- 화면: `계약서 생성`
- 동작:
  - 저장 공고, 법인, 판단 run 선택
  - 계약번호/금액/기간 같은 필드 확인
  - 미리보기 생성
  - DOCX 초안 생성
- 강조:
  - 반복 입력 감소
  - 최종 계약서는 관리자 검토 대상
- 예상 길이: 45초

### 장면 8. 운영 상태와 실패 이력을 확인합니다
- 화면: `운영 대시보드`, `작업 이력`
- 동작:
  - 최근 실패/성공 작업 확인
  - 재시도 가능 작업 확인
  - 백업 상태 확인
- 강조:
  - AI 처리 결과만이 아니라 운영 상태와 실패 사유까지 관리
- 예상 길이: 35초

### 장면 9. 클로징
- 화면: 대시보드 또는 계약서 생성 완료 화면
- 자막: `실제 공고와 실제 법인 증빙자료로 조달 준비 상태를 더 빠르게 검토합니다.`
- 예상 길이: 10초

## 장면별 테스트 계약

영상 생성 스크립트는 각 장면을 단순 클릭 순서로만 처리하지 않고, 다음 성공 신호를 확인해야 한다.

| 장면 | 주요 라우트 | 선행 조건 | 성공 신호 | 실패 시 기록 |
| --- | --- | --- | --- | --- |
| 장면 1 법인/증빙 | `/corporations` | 데모 파일 존재 | 증빙 문서가 `completed` 또는 후보 표시 상태, 법인 프로필 반영 가능 | 업로드 응답, 화면 스크린샷, console error |
| 장면 2 대시보드 | `/` | 법인 또는 공고 1건 이상 | 법인/문서/공고 상태 카드가 렌더링됨 | 대시보드 API 응답 |
| 장면 3 나라장터 검색 | `/nara-board` | API 키 또는 stable fixture | 검색 결과 행 또는 demo notice 표시 | 검색 API 응답, partial_errors |
| 장면 4 저장 공고 상세 | `/nara-saved-notices/:id` | 저장 공고 id | 요구조건 후보/첨부 분석 상태 표시 | saved notice detail 응답 |
| 장면 5 기준문서/RAG | `/basis-documents` | 기준문서 PDF 또는 seeded basis | `parse/chunk/index completed` 또는 검색 결과 표시 | basis detail, basis-index status |
| 장면 6 부족조건 | `/notice-comparison` 또는 `/judgment-runs` | 공고, 법인, 기준문서 | 준비됨/부족/확인 필요 항목 표시 | comparison/judgment 응답 |
| 장면 7 계약서 | `/contracts` | 공고, 법인, 필요 시 judgment run | DOCX 생성 완료와 다운로드 링크 표시 | contract create 응답 |
| 장면 8 운영 이력 | `/operations`, `/operation-runs` | 위 작업 실행 완료 | `basis_document_processing`, `judgment_run`, `contract_create` 이력 표시 | operation-runs 응답 |

## 데이터 세팅 전략

### stable-demo 데이터 세팅
- API를 통해 데모 데이터를 생성한다.
- 스크립트는 매 실행마다 고유 접두어를 사용한다.
  - 예: `DEMO-20260614-<seed>`
- 이미 같은 seed의 데이터가 있으면 재사용하거나 삭제 후 재생성할 수 있게 한다.
- 추천 옵션:
  - `--seed 20260614`
  - `--reuse-data`
  - `--reset-demo-data`

### real-pdf-demo 데이터 세팅
- `source/test_doc/` 파일 존재 여부를 먼저 확인한다.
- 없는 파일은 해당 장면에서 건너뛰지 말고 실패로 기록한다.
- 실제 PDF OCR은 오래 걸릴 수 있으므로 다음 정책을 둔다.
  - 기본 timeout: 파일당 180초
  - 전체 evidence scene timeout: 10분
  - timeout 발생 시 현재까지 성공한 증빙과 실패 파일명을 report에 기록

### live-nara-demo 데이터 세팅
- `NARA_API_SERVICE_KEY` configured 상태를 먼저 확인한다.
- 검색 실패 또는 `partial_failed`이면 경고 배너 장면을 찍고, stable demo notice로 이어간다.
- 공식 영상 생성에서는 `live-nara-demo`를 기본값으로 쓰지 않는다.

## 안정적인 화면 조작 정책

Playwright 스크립트는 다음 우선순위로 요소를 찾는다.

1. 접근성 role/name
   - 예: `page.getByRole("button", { name: "계약서 초안 생성" })`
2. label, placeholder, visible text
3. route와 API 응답 기반 direct navigation
4. 필요한 경우에만 `data-demo-id` 추가

UI 텍스트가 바뀌어도 반드시 유지되어야 하는 핵심 액션에는 향후 `data-demo-id`를 추가하는 것이 좋다.

우선 추가 후보:

- `demo-corporation-evidence-upload`
- `demo-nara-search`
- `demo-nara-save-analyze`
- `demo-basis-upload`
- `demo-notice-comparison-run`
- `demo-judgment-run`
- `demo-contract-create`
- `demo-operation-run-list`

다만 첫 구현에서는 기존 접근성 텍스트와 라우트 기반으로 최대한 진행하고, 불안정한 지점이 발견될 때만 UI에 `data-demo-id`를 추가한다.

## 구현 계획

### Step 0. 사전 파이프라인 검증
- `test_service_rocket_pitch_demo_pipeline_flow`를 먼저 실행한다.
- 실패하면 영상 녹화를 중단한다.
- 성공하면 `artifacts/demo-video/preflight.json`에 결과를 기록한다.

### Step 1. 라이브러리 설치와 실행 환경 확인
- `ffmpeg-static` 설치 여부 확인
- Playwright Chromium 설치 여부 확인
- 백엔드/프론트엔드 서버 URL 확인
- ngrok 영상이 필요한 경우 공개 URL 대신 로컬 URL에서 먼저 녹화한다.

### Step 2. 자동 녹화 스크립트 추가
- 신규 스크립트 후보:
  - `scripts/create-service-demo-video.mjs`
  - `scripts/demo-video.config.json`
- 스크립트 역할:
  - 서버 주소 확인
  - Playwright Chromium 실행
  - 장면별 라우트 이동
  - 입력/클릭/업로드 자동 수행
  - 장면별 스크린 녹화 저장
  - 실패 시 스크린샷과 trace 저장
- 기본 출력:
  - `artifacts/demo-video/raw/*.webm`
  - `artifacts/demo-video/screenshots/*.png`
  - `artifacts/demo-video/report.json`

CLI 옵션:

```powershell
node scripts\create-service-demo-video.mjs `
  --mode stable-demo `
  --frontend-url http://127.0.0.1:5199 `
  --backend-url http://127.0.0.1:18111 `
  --out-dir artifacts/demo-video `
  --seed 20260614 `
  --headless `
  --slow-mo 0
```

지원 옵션:

- `--mode stable-demo|real-pdf-demo|live-nara-demo`
- `--scene all|corporation|dashboard|nara|notice|basis|comparison|contract|operations`
- `--dry-run`
- `--headless` / `--headed`
- `--slow-mo <ms>`
- `--reuse-data`
- `--reset-demo-data`
- `--trace on|off`
- `--video-size 1920x1080`

`scripts/demo-video.config.json` 예시:

```json
{
  "mode": "stable-demo",
  "frontendUrl": "http://127.0.0.1:5199",
  "backendUrl": "http://127.0.0.1:18111",
  "outputDir": "artifacts/demo-video",
  "videoSize": { "width": 1920, "height": 1080 },
  "seed": "20260614",
  "timeouts": {
    "sceneMs": 120000,
    "ocrSceneMs": 600000,
    "apiPollMs": 300000
  },
  "realPdfFiles": [
    "source/test_doc/1.벡트_사업자등록증.pdf",
    "source/test_doc/2.중소기업확인서_중기업_20260331.pdf",
    "source/test_doc/20250226_(주)벡트_직생(동영상제작).pdf",
    "source/test_doc/기업신용평가등급확인서_벡트(공공기관 제출용).pdf"
  ]
}
```

### Step 3. 영상 후처리 스크립트 추가
- 신규 스크립트 후보:
  - `scripts/render-service-demo-video.mjs`
- 역할:
  - 장면 WebM 병합
  - MP4 변환
  - 장면 제목 자막 삽입
  - 필요하면 1.1~1.3배속 적용
- 기본 출력:
  - `artifacts/demo-video/smart-procurement-demo.mp4`
  - `artifacts/demo-video/smart-procurement-demo.webm`
  - `artifacts/demo-video/smart-procurement-demo.chapters.json`
  - `artifacts/demo-video/qa-report.json`

후처리 기준:

- 원본 WebM은 보존한다.
- MP4는 H.264 + AAC 또는 무음 H.264로 만든다.
- 장면 사이에는 0.3~0.8초 정도의 짧은 title card를 넣는다.
- OCR 대기 장면은 필요 시 1.3배속 이상으로 처리한다.
- 실패 장면은 최종 영상에 넣지 않고 `failed-scenes/`에 별도 보관한다.

### Step 4. 실행 명령 추가
- `frontend/package.json` 또는 루트 실행 문서에 다음 명령을 추가한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start
cd frontend
npm run demo:preflight
npm run demo:record -- --mode stable-demo
npm run demo:render
```

또는 루트에서 한 번에 실행하는 PowerShell 스크립트를 둔다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create-demo-video.ps1
```

### Step 5. 결과 검증
- 영상 파일이 생성되는지 확인한다.
- 영상 길이, 해상도, 파일 크기를 확인한다.
- 각 장면에 blank page, console error, API error toast가 없는지 확인한다.
- 계약서 DOCX 생성 장면에서 다운로드 링크가 표시되는지 확인한다.
- 영상 중 API 키 원문이나 `.env` 파일이 노출되지 않는지 확인한다.

### Step 6. 리포트와 재현 정보 저장
- `report.json`에 다음 값을 저장한다.
  - 실행 시각
  - git commit 또는 working tree summary
  - mode
  - seed
  - frontend/backend URL
  - scene별 시작/종료 시각
  - scene별 성공/실패
  - 생성된 주요 데이터 id
  - console error 목록
  - API 실패 목록
  - 최종 영상 파일 경로와 크기

### Step 7. 문서와 work-log 갱신
- README 또는 별도 실행 가이드에 영상 생성 명령을 추가한다.
- `docs/work-log.md`에 실행 결과와 검증 결과를 기록한다.

## 필요한 라이브러리

### 이미 사용 중인 라이브러리
- `playwright`: 프론트엔드 devDependency에 존재
- `typescript`, `vite`: 기존 프론트엔드 빌드에 존재

### 추가 설치 권장
- `ffmpeg-static` 또는 로컬 FFmpeg
  - 목적: WebM 병합, MP4 변환, 자막 삽입
- 선택: `ffprobe-static`
  - 목적: 최종 영상 길이/해상도/코덱 검증 자동화
- 선택: `@ffmpeg-installer/ffmpeg`
  - 목적: Windows PC별 FFmpeg 설치 차이를 줄임

권장 설치:

```powershell
cd frontend
npm install -D ffmpeg-static ffprobe-static
npx playwright install chromium
```

시스템 FFmpeg를 직접 설치해도 된다.

```powershell
winget install Gyan.FFmpeg
```

## 권장 영상 생성 방식

### 1순위: 자동 녹화 + 자동 후처리
- 장점:
  - 반복 생성 가능
  - UI 변경 후 회귀 확인 가능
  - 데모 영상과 UX 테스트를 함께 관리 가능
- 단점:
  - 스크립트 작성이 필요
  - 네트워크 API나 OCR 장시간 작업은 안정화 장치가 필요

### 2순위: 자동 데이터 세팅 + 수동 녹화
- 장점:
  - 빠르게 첫 영상을 만들 수 있음
  - 발표자가 실제 조작하는 느낌을 줄 수 있음
- 단점:
  - 재현성이 떨어짐
  - 같은 영상 품질을 반복하기 어려움

### 3순위: 스크린샷 기반 모션 영상
- 장점:
  - 안정적이고 빠름
  - API/OCR 대기 시간이 문제되지 않음
- 단점:
  - 실제 서비스가 움직이는 느낌이 약함

## 테스트 계획

### 0. 파이프라인 preflight
```powershell
cd backend
py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v
```

이 테스트가 실패하면 영상 녹화를 시작하지 않는다.

### 문서/스크립트 정적 검증
```powershell
py -3.13 scripts\check-encoding.py
git diff --check
```

### 프론트엔드 빌드 검증
```powershell
cd frontend
npm run build
```

### 녹화 스모크 테스트
```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start
cd frontend
npm run demo:record -- --mode stable-demo --scene dashboard --dry-run
```

검증 기준:
- 브라우저가 열림
- 대시보드 라우트 접근 가능
- console error 0건
- blank page 아님
- `artifacts/demo-video/report.json` 생성

### 전체 영상 생성 테스트
```powershell
cd frontend
npm run demo:record -- --mode stable-demo
npm run demo:render
```

검증 기준:
- 최종 MP4 파일 생성
- 해상도 1920x1080 또는 1440x900
- 전체 길이 4분 30초 ~ 6분
- 화면 깨짐 없음
- 주요 장면 8개가 모두 포함됨
- API 키 원문 노출 없음
- 장면별 report status가 모두 `completed`
- `basis_document_processing`, `judgment_run`, `contract_create` 작업 이력 장면이 포함됨
- 계약서 생성 장면에서 DOCX 다운로드 링크가 표시됨
- 최종 영상에서 blank frame 비율이 1% 미만

### 영상 파일 검증
FFmpeg/FFprobe를 설치한 경우 다음 정보를 자동 검증한다.

```powershell
cd frontend
npm run demo:inspect
```

검증 항목:
- container
- duration
- width/height
- video codec
- file size
- scene count
- render timestamp

### 실제 PDF 모드 테스트
```powershell
cd frontend
npm run demo:record -- --mode real-pdf-demo --scene corporation
```

검증 기준:
- 선택한 `source/test_doc/` PDF가 모두 존재
- OCR이 필요한 파일은 진행 상태 또는 완료 상태가 표시됨
- 분류 결과가 `unknown`만으로 끝나지 않음
- 실패 파일은 report에 파일명과 오류 사유가 기록됨

### 실시간 나라장터 모드 테스트
```powershell
cd frontend
npm run demo:record -- --mode live-nara-demo --scene nara
```

검증 기준:
- API 키 configured 상태 확인
- 검색 성공 시 업무유형 배지 표시
- 일부 실패 시 partial warning 배너 표시
- 전체 실패 시 stable demo notice fallback 사용

## 예상 산출물
- `scripts/create-service-demo-video.mjs`
- `scripts/render-service-demo-video.mjs`
- `scripts/create-demo-video.ps1`
- `scripts/demo-video.config.json`
- `scripts/prepare-service-demo-data.mjs`
- `scripts/inspect-service-demo-video.mjs`
- `artifacts/demo-video/smart-procurement-demo.mp4`
- `artifacts/demo-video/smart-procurement-demo.webm`
- `artifacts/demo-video/report.json`
- `artifacts/demo-video/qa-report.json`
- `docs/service-demo-video-generation-plan.md`
- `docs/work-log.md` 업데이트

## 남은 의사결정
- 공식 공유용 첫 영상은 `stable-demo` 모드로 생성한다.
- 실제 PDF/OCR 장면은 별도 확장 영상 또는 짧은 삽입 장면으로 둘지 결정해야 한다.
- 실시간 나라장터 API 검색 장면을 본편에 넣을지, 별도 부록 영상으로 둘지 결정해야 한다.
- 기준문서 OCR 완료 과정을 실제로 기다릴지, 완료된 상태를 보여주는 방식으로 편집할지 결정해야 한다.
- 발표자 음성을 넣을지, 화면 자막만 넣을지 결정해야 한다.
- 최종 영상 해상도를 1920x1080으로 고정할지, 현재 포탈에 맞춰 1440x900으로 만들지 결정해야 한다.

## 권장 실행 순서
1. `stable-demo` 데이터 준비 스크립트를 만든다.
2. `test_service_rocket_pitch_demo_pipeline_flow`를 preflight로 연결한다.
3. `dashboard` 단일 장면 dry-run 녹화를 먼저 성공시킨다.
4. `corporation -> dashboard -> nara` 3개 장면을 묶어 녹화한다.
5. 전체 8개 장면을 `stable-demo`로 녹화한다.
6. FFmpeg 후처리와 inspect 리포트를 추가한다.
7. `real-pdf-demo`에서 법인 증빙 장면만 별도 검증한다.
8. `live-nara-demo`는 검색 장면 옵션으로 추가한다.
9. 마지막으로 자막/타이틀/배속을 다듬는다.

## 구현 착수 체크리스트

- [ ] `ffmpeg-static`, `ffprobe-static` 설치
- [ ] `demo:preflight`, `demo:record`, `demo:render`, `demo:inspect` npm script 추가
- [ ] `scripts/demo-video.config.json` 추가
- [ ] `scripts/prepare-service-demo-data.mjs` 추가
- [ ] `scripts/create-service-demo-video.mjs` 추가
- [ ] `scripts/render-service-demo-video.mjs` 추가
- [ ] `scripts/inspect-service-demo-video.mjs` 추가
- [ ] `stable-demo` 전체 녹화 성공
- [ ] `real-pdf-demo` 법인 증빙 장면 검증
- [ ] `docs/work-log.md` 결과 기록

---

# AI / Engineering Version (English)

## Purpose
This document evaluates and plans automated demo-video generation for the service flow described in `docs/service-rocket-pitch.md`, section `3. 제품 시연 흐름`.

## Feasibility
Video generation is feasible with the current codebase.

The frontend is a React/Vite application, Playwright is already available as a dev dependency, and UX automation already exists. The recommended implementation is to drive the real portal with Playwright, record scene-level WebM clips, then use FFmpeg to merge, encode, and optionally add subtitles.

The plan has been strengthened to require the backend Rocket Pitch pipeline regression test as a preflight before recording. This keeps the demo video tied to real service behavior rather than only browser navigation.

## Modes
- `stable-demo`: deterministic seeded data, no live Nara API, no long OCR dependency. This is the default mode for the first official demo video.
- `real-pdf-demo`: uses selected PDFs from `source/test_doc/` to show actual evidence parsing/OCR/classification.
- `live-nara-demo`: uses the configured Nara API and falls back to seeded demo data when the live API fails.

## Preflight
Run before any recording:

```powershell
cd backend
py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v
cd ..
npm run build
py -3.13 scripts\check-encoding.py
git diff --check
```

If preflight fails, recording should stop.

## Recommended Architecture
- `scripts/create-service-demo-video.mjs`
  - starts or validates app URLs
  - drives Chromium with Playwright
  - executes the scene script
  - records WebM clips
  - saves screenshots and a JSON report
- `scripts/render-service-demo-video.mjs`
  - merges clips
  - converts WebM to MP4
  - adds title cards/subtitles if needed
- `scripts/create-demo-video.ps1`
  - optional one-command Windows wrapper
- `scripts/prepare-service-demo-data.mjs`
  - creates/reuses deterministic demo records through backend APIs
- `scripts/inspect-service-demo-video.mjs`
  - validates output duration, resolution, codec, size, and scene count

## Scene Contracts
Each scene should have route, prerequisite, success signal, and failure artifacts.

- corporation/evidence: `/corporations`, evidence upload completed and candidates visible
- dashboard: `/`, dashboard cards rendered
- Nara search/save: `/nara-board`, result rows or fallback demo notice available
- saved notice detail: `/nara-saved-notices/:id`, requirements visible
- basis/RAG: `/basis-documents`, parse/chunk/index completed or search result visible
- comparison/judgment: `/notice-comparison` or `/judgment-runs`, gap-first items visible
- contracts: `/contracts`, DOCX generation and download link visible
- operations: `/operations` and `/operation-runs`, `basis_document_processing`, `judgment_run`, and `contract_create` visible

## Demo Flow
1. Register corporation and upload evidence PDFs from `source/test_doc/`.
2. Show the dashboard.
3. Search and save a Nara notice.
4. Review extracted notice requirements.
5. Show basis-document ingestion and searchable RAG index status.
6. Compare corporation readiness against notice requirements.
7. Generate a DOCX contract draft.
8. Review operations dashboard and operation history.

## Dependencies
Already present:
- `playwright`
- `vite`
- `typescript`

Recommended additions:
- `ffmpeg-static` or system FFmpeg
- `ffprobe-static` for output inspection
- Chromium browser binaries via `npx playwright install chromium`

## Output
- `artifacts/demo-video/raw/*.webm`
- `artifacts/demo-video/smart-procurement-demo.mp4`
- `artifacts/demo-video/report.json`
- `artifacts/demo-video/qa-report.json`

## Validation
- backend pipeline preflight
- frontend build
- encoding check
- whitespace check
- scene-level dry-run
- full stable-demo recording
- FFprobe output inspection
- verify no blank page, console error, raw `.env`, or raw API key screen is captured
- verify all required scenes are present
- verify final DOCX creation/download and operation history scenes are captured

## Recommended Execution Order
1. Implement stable demo data preparation.
2. Wire the Rocket Pitch pipeline test as preflight.
3. Record a single dashboard dry-run scene.
4. Record the first three scenes.
5. Record the full stable-demo flow.
6. Add FFmpeg render and inspect steps.
7. Add real-pdf-demo evidence scene.
8. Add live-nara-demo as an optional scene.

## 현재 구현된 실행 명령

`stable-demo` 영상 생성은 다음 명령으로 실행한다.

```powershell
cd frontend
npm run demo:browser-install
npm run demo:preflight
npm run demo:record
npm run demo:render
npm run demo:inspect
```

Windows에서는 다음 래퍼로 서버 시작, 녹화, MP4 변환, 검사까지 이어서 실행할 수 있다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create-demo-video.ps1
```

현재 산출물 위치는 다음과 같다.

- `artifacts/demo-video/latest-demo-data.json`
- `artifacts/demo-video/latest-report.json`
- `artifacts/demo-video/latest-render.json`
- `artifacts/demo-video/latest-inspection.json`
- `artifacts/demo-video/service-demo-<seed>.mp4`

세부 구현 계획과 파일별 역할은 `docs/service-demo-video-implementation-plan.md`를 기준으로 본다.

## Implemented Command Set

The deterministic `stable-demo` mode is implemented with these commands:

```powershell
cd frontend
npm run demo:browser-install
npm run demo:preflight
npm run demo:record
npm run demo:render
npm run demo:inspect
```

The Windows wrapper is:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create-demo-video.ps1
```

Implementation details are tracked in `docs/service-demo-video-implementation-plan.md`.
