# 한국어 버전

## 프로젝트 개요
`SMART 조달청 계산기`는 단일 관리자 사용자(행정사)가 법인 정보를 관리하고, 프로젝트를 생성하고, 조달 관련 PDF/DOCX 문서를 프로젝트 단위로 업로드하여 AI 기반 요약과 구조화 결과를 확인하는 로컬 실행형 웹 어드민 포탈입니다.

## 현재 코드 기준 요약
최종 문서 갱신일: 2026-06-07

- 현재 PDF 리더 기본값은 `OpenDataLoader PDF` 우선 `auto` 모드이며, Java/패키지/timeout/변환 실패 시 `PyMuPDF`로 fallback합니다.
- 일반 업로드 문서, 나라장터 공고 첨부 PDF, 기준문서 PDF는 같은 `extract_document()` 진입점을 사용하므로 현재 기본 PDF 리더 정책을 공유합니다.
- DOCX 추출은 `python-docx` 기반이며, 문단뿐 아니라 표 cell 텍스트도 분석 입력에 포함합니다.
- 기준문서 RAG 검색 source는 운영 산출물인 `storage/basis-index/basis-index.json`입니다. JSON 인덱스가 없거나 DB와 불일치하면 검색/승인/판단 citation 사용을 막고 rebuild를 요구합니다.
- 기준문서 재처리 중 원본 파일이 사라진 경우에도 기존 completed/indexed RAG 산출물이 있으면 기존 검색 지식을 보존합니다.
- 판단 엔진은 확정 합격 판정이 아니라 `부족 조건`, `필요 서류`, `준비 가이드`, `citation 상태` 중심으로 결과를 저장합니다.
- 운영 화면에는 운영 대시보드, 작업 실행/실패 이력, 백업/검증/복원계획, 나라장터 자동 수집, 판단 이력이 포함됩니다.
- `계약서 생성` 화면은 저장 공고와 법인 기본정보를 기준으로 검토용 `용역표준계약서` DOCX 초안을 생성합니다.
- `외부 접속` 화면은 `scripts/manage-ngrok.ps1`가 만든 ngrok public URL 상태를 표시합니다. 프론트 화면에서 ngrok start/stop은 직접 실행하지 않습니다.

이 프로젝트는 단계적으로 확장됩니다.
- Phase 1: 업로드, 관리, 요약 MVP
- Phase 1.5: 나라장터 게시판, 공고 API 조회, 첨부 다운로드, 공고 자동 분석
- Phase 1.6: 법인 증빙자료 자동 추출과 법인 프로필 보강
- Phase 2: 기준 PDF 관리와 로컬 RAG 준비
- Phase 2 운영 보강: 기준문서 규칙 후보 승인/반려/수정, 나라장터 자동 수집 운영 화면
- Phase 3: 부족조건 중심 판단 엔진과 조달 공고 자동 수집
- Phase 4: 운영 대시보드, 작업/실패 관리, 백업/복원 관리
- Phase 4E: ngrok 기반 로컬 서비스 외부 접속 지원
- Phase 5A: 저장 공고/법인 기반 계약서 DOCX 초안 생성

## 현재 단계 계획

### Phase 1
- 로그인 없는 단일 관리자 포탈
- 법인 CRUD
- 프로젝트 CRUD
- 프로젝트 기반 PDF/DOCX 업로드
- 업로드 메타데이터 수집
- PDF/DOCX 텍스트 추출
- 스캔 PDF OCR
- AI 요약
- 구조화 결과 저장
- 재분석 버튼

### Phase 1.5
- 나라장터 게시판
- 공고 검색 진입 시 최근 1개월 기준 자동 조회
- 공고 리스트/상세 조회
- 기본 검색 및 상세검색
- 공고 첨부파일 목록 표시
- PDF/DOCX 첨부파일 다운로드
- 라디오 박스로 공고 1개 선택
- `공고 상세 저장` 액션
- `저장한 공고` 게시판
- 공고 메타데이터 저장
- 첨부 PDF/DOCX 자동 다운로드
- 기존 문서 파싱/요약 파이프라인 재사용
- 저장된 공고 분석 결과 조회
- 설정 > API 연동에서 나라장터 API 키 설정/연결 상태 확인

### Phase 1.6
- 법인 등록 첫 화면을 증빙서류 업로드 중심으로 변경
- 사업자등록증명/사업자등록증 업로드 후 법인 기본정보 자동 추출
- 법인 증빙자료 업로드/목록/상세/삭제
- PDF/DOCX/JPG/JPEG/PNG 증빙자료 텍스트 추출과 OCR
- 증빙서류 유형 자동 분류
- 알 수 없는 증빙서류 LLM 기반 분류
- 추출 결과 확인/수정 후 법인 프로필 업데이트
- 증빙자료 기반 법인정보 충돌/만료/확인 필요 상태 표시

Phase 1.6은 한 번에 모든 증빙자료를 완전 자동화하지 않고, `1.6A -> 1.6B -> 1.6C`로 나누어 진행합니다.
- 1.6A: 사업자등록증명/사업자등록증 기반 법인 등록 MVP
- 1.6B: 주요 조달 증빙자료 확장
- 1.6C: 알 수 없는 증빙자료 LLM 분류와 운영 안정화

### Phase 2
- 기준 PDF 별도 메뉴
- 기준문서 CRUD
- 기준문서 유형/카테고리 관리
- 기준문서 버전 관리
- 자동 OCR
- 자동 청킹
- 청크 메타데이터 생성
- 로컬 벡터 인덱싱
- 처리 상태 조회
- 재처리 버튼
- 기준문서 규칙 후보 추출
- 규칙 후보 승인/반려/수정 관리
- 검색/citation 평가 지표 관리

### Phase 2 운영 보강
- `기준문서 규칙 후보 관리` 화면에서 자동 추출 후보를 검토한다.
- 승인된 규칙 후보만 향후 판단 근거 후보로 우선 사용한다.
- `나라장터 자동 수집 관리` 화면에서 API 수집 실행, 이력, 저장 결과, 실패 사유를 확인한다.
- MuPDF known issue 목록은 로컬 QA 산출물 JSON이 있을 때 동적으로 읽는다.
- JSON 기준문서 인덱스 상태를 운영 대시보드와 검증 API에서 확인하고, 손상/불일치 시 검색과 citation 사용을 차단한다.

### Phase 3
- 조달 공고 자동 수집
- 공고 및 첨부 자동 수집
- 공고 분석 저장
- 법인-공고 요구조건 매칭
- 기준문서 검색 기반 판단
- 근거 조항 출력
- 체크리스트 생성
- 준비 가이드 생성

### Phase 4
- 운영 대시보드
- 작업 실행/재시도/실패 이력 관리
- 실패 사유와 최근 작업 상태 조회
- 백업 생성, 백업 검증, 복원계획 dry-run
- 백업 manifest와 기준문서 JSON 인덱스 checksum 검증

### Phase 4E
- `scripts/manage-ngrok.ps1`로 백엔드/프론트엔드 ngrok tunnel 실행
- `GET /api/external-access/status`로 public URL 상태 확인
- `설정 > 외부 접속` 화면에서 공개 URL, 로컬 URL, 주의사항 확인
- ngrok token/API key/raw env 원문은 status 파일과 화면에 노출하지 않음

### Phase 5A
- `계약서 생성` 화면에서 저장 공고와 법인을 선택
- 계약번호, 계약금액, 계약기간, 위치, 전화번호, 그 밖의 사항, 붙임서류 입력
- 표준계약서 필드 매핑 미리보기
- `용역표준계약서` DOCX 초안 생성/다운로드
- 계약서 생성/검토/삭제 이력을 작업 이력에 기록

## 주요 기능
- 법인 관리
- 프로젝트 중심 이력 관리
- 메타데이터 포함 파일 업로드
- 문서 분석 결과 페이지
- 검색/필터/상세/수정/삭제
- 나라장터 공고 검색/상세/저장/분석 설계
- 나라장터 API 설정 상태 확인 설계
- 기준 PDF 별도 지식 자산 관리
- 계약서 DOCX 초안 생성/다운로드
- ngrok 외부 접속 상태 확인
- 향후 판단 엔진 확장을 고려한 구조

## 추천 저장소 구조
```text
wisdom_procurement/
  frontend/
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      repositories/
      pipelines/
      workers/
    storage/
      uploads/
      basis/
      cache/
  docs/
    technical-design.md
    ux-design.md
    narajangteo-board-design.md
  README.md
  AGENTS.md
```

## 기술 스택
- Frontend: React + TypeScript + Vite + React Router
- Backend: Python 3.13.13 + Flask
- DB: SQLite
- File Storage: Local filesystem
- OCR: PaddleOCR PP-OCRv5 primary, Tesseract fallback candidate
- Parsing: PDF, DOCX only
  - PDF 기본 추출 엔진은 `OpenDataLoader PDF` 우선 `auto` 모드
  - `OpenDataLoader PDF` 실패, Java 미설치, timeout 시 `PyMuPDF` fallback
  - DOCX는 `python-docx`를 사용하며 문단과 표 cell 텍스트를 함께 추출
  - 스캔/이미지형 PDF는 추출 텍스트 부족 시 OCR fallback 적용
- AI: External LLM API
- Future Vector Store: Qdrant 우선, Chroma 대안

## 추천 AI/API 전략
- 기본 Provider/모델: Google Gemini `gemini-2.5-flash`
- 보조 Provider/모델: OpenAI `gpt-5.4-mini`, `gpt-5.4`
- 포탈에서 분석 실행 시 사용할 Provider/모델을 선택할 수 있습니다.
- 실제 API 키는 `backend/.env`에 직접 입력하며, 화면에는 설정 여부와 마스킹 값만 표시합니다.
- PDF는 `OpenDataLoader PDF`로 Markdown/JSON/table metadata를 먼저 추출
- `PyMuPDF`는 빠른 fallback 및 PDF 렌더링/OCR 보조 엔진으로 유지
- OCR은 텍스트 레이어가 부족한 PDF에만 fallback으로 적용
- OCR 주 엔진은 `PaddleOCR PP-OCRv5`, 경량 대안은 `Tesseract(kor+eng)`로 둔다.
- PaddleOCR은 Windows 기준 Python 3.13.13 런타임(`py -3.13`)에서 우선 검증한다.
- 정규화된 추출 텍스트를 모델에 전달
- 요약은 JSON 구조화 출력 + 사용자용 마크다운 병행 저장
- 재분석은 프롬프트 버전/입력 해시 기반으로 캐시 제어

## 로컬 세팅과 테스트 빠른 가이드

이 절은 다른 PC에서 처음 받는 사람이 가장 짧은 경로로 서비스를 실행하고 테스트해 보기 위한 순서입니다. Windows PowerShell 기준으로 작성했습니다.

### 1. 사전 설치
- Python `3.13.13`
  - 확인: `py -3.13 --version`
  - `py -3.13`이 안 되면 Python 3.13 설치 후 Windows Python Launcher가 잡혔는지 확인합니다.
- Node.js `20.19.0 이상` 또는 `22.12.0 이상`
  - 현재 검증 환경: Node `24.14.1`, npm `11.11.0`
  - 확인: `node -v`, `npm -v`
- Git
- Windows PowerShell
- Java 11 이상
  - OpenDataLoader PDF 변환에 필요합니다.
  - 확인: `java -version`
  - Java가 없거나 변환이 실패하면 기본 `auto` 모드에서 `PyMuPDF` fallback으로 동작합니다.

OCR 엔진은 기본 테스트에 필수는 아닙니다. OCR 의존성이 없어도 업로드/분석 흐름은 `needs_ocr_setup` 또는 fallback 상태로 동작해야 합니다.

### 2. 저장소 받기
```powershell
git clone <repository-url>
cd wisdom_procurement
```

이미 저장소를 받은 경우에는 최신 상태로 맞춥니다.

```powershell
git pull
```

### 3. 백엔드 의존성 설치
```powershell
cd backend
py -3.13 -m pip install --upgrade pip
py -3.13 -m pip install -r requirements.txt
cd ..
```

OCR까지 로컬에서 직접 검증하려면 별도로 설치합니다.

```powershell
cd backend
py -3.13 -m pip install -r requirements-ocr.txt
cd ..
```

### 4. 프론트엔드 의존성 설치
```powershell
cd frontend
npm install
npx playwright install chromium
cd ..
```

`playwright`는 UX monkey 테스트에 사용됩니다. 화면 테스트까지 돌릴 PC라면 Chromium 설치까지 해두는 편이 좋습니다.

### 5. 환경 파일 준비
서버 관리 스크립트는 `backend/.env`, `frontend/.env`가 없으면 `.env.example`을 복사해 줍니다. 직접 만들고 싶으면 아래처럼 복사합니다.

```powershell
Copy-Item backend\.env.example backend\.env -ErrorAction SilentlyContinue
Copy-Item frontend\.env.example frontend\.env -ErrorAction SilentlyContinue
```

기본 테스트만 할 때는 API 키가 없어도 됩니다. 실제 AI 요약, Gemini 비교, 나라장터 API 조회를 테스트하려면 `backend/.env`에 키를 넣습니다.

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
NARA_API_SERVICE_KEY=
```

PDF 리더는 기본적으로 OpenDataLoader를 먼저 시도하고 실패하면 PyMuPDF로 fallback합니다. 기본값은 `backend/.env.example`에 들어 있으며, 직접 조정하려면 `backend/.env`에 아래 값을 넣습니다.

```env
PDF_READER_ENGINE=auto
PDF_READER_ODL_VERSION=2.4.7
PDF_READER_ODL_TABLE_METHOD=cluster
PDF_READER_ODL_READING_ORDER=xycut
PDF_READER_ODL_FORMAT=markdown,json
PDF_READER_ODL_TIMEOUT_SECONDS=180
PDF_READER_ODL_THREADS=1
PDF_READER_ODL_ENABLE_HYBRID=false
PDF_READER_ALLOW_PYMUPDF_FALLBACK=true
```

엔진 선택:
- `auto`: OpenDataLoader 우선, 실패 시 PyMuPDF fallback
- `opendataloader`: OpenDataLoader만 사용
- `pymupdf`: 기존 PyMuPDF만 사용

주의:
- API 키는 Git에 커밋하지 않습니다.
- 프론트엔드에는 전체 API 키를 노출하지 않습니다.
- `scripts/manage-servers.ps1`로 실행하면 기본 백엔드 주소는 `http://127.0.0.1:18111`, 프론트 주소는 `http://127.0.0.1:5199`입니다.

### 5-1. Gemini API 키 발급
Gemini 기반 AI 요약/비교 기능을 실제로 테스트하려면 Google AI Studio에서 Gemini API 키를 발급받아야 합니다.

발급 절차:
1. Google 계정으로 [Google AI Studio](https://aistudio.google.com/)에 로그인합니다.
2. [Google AI Studio API keys](https://aistudio.google.com/app/apikey) 페이지로 이동합니다.
3. 처음 사용하는 계정이면 약관에 동의합니다.
4. `Create API key` 또는 `API 키 만들기`를 선택합니다.
5. 새 Google Cloud 프로젝트를 만들거나 기존 프로젝트를 선택해 API 키를 생성합니다.
6. 생성된 키를 복사해 `backend/.env`에 입력합니다.

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_PROVIDER_DEFAULT=gemini
AI_MODEL_DEFAULT=gemini-2.5-flash
GEMINI_MODEL_PRIMARY=gemini-2.5-flash
```

PowerShell에서 임시로만 넣고 테스트하려면:

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
```

참고:
- Google 공식 문서 기준 Gemini API 키는 Google AI Studio의 API keys 페이지에서 만들고 관리합니다.
- Gemini SDK는 일반적으로 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY` 환경변수를 읽을 수 있지만, 이 프로젝트는 `GEMINI_API_KEY`를 표준으로 사용합니다.
- Gemini API 키도 나라장터 키와 마찬가지로 README, 로그, 프론트엔드 화면, Git 커밋에 원문을 남기지 않습니다.

### 6. 서버 실행
가장 쉬운 방법은 서버 관리 스크립트를 쓰는 것입니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
```

상태 확인:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action status
```

브라우저에서 접속:

```text
http://127.0.0.1:5199
```

서버 중지:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action stop
```

포트를 바꾸고 싶으면:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start -BackendPort 18112 -FrontendPort 5200
```

### 7. 전체 테스트와 빌드
백엔드 전체 테스트:

```powershell
py -3.13 -m pytest backend/tests -q
```

OpenDataLoader 실제 기준문서 PDF QA:

```powershell
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine opendataloader --threads 4 --timeout-seconds 1200 --strict
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine auto --threads 4 --timeout-seconds 1200 --strict
```

OpenDataLoader 실패 시 PyMuPDF fallback QA:

```powershell
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine auto --threads 1 --timeout-seconds 1 --min-table-count 0 --min-table-row-chunks 0 --min-reference-table-row-coverage 0 --min-reference-table-row-token-coverage 0
```

프론트엔드 빌드:

```powershell
cd frontend
npm run build
cd ..
```

인코딩 검사:

```powershell
py -3.13 scripts/check-encoding.py
```

프론트 의존성 보안 검사:

```powershell
cd frontend
npm audit --audit-level=moderate
cd ..
```

### 8. API smoke 테스트
실제 백엔드/프론트 서버를 띄운 뒤 핵심 API 흐름을 자동으로 검증합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
```

스모크 테스트가 검증하는 흐름:
- 서버 기동
- 법인 생성
- 프로젝트 생성
- PDF 업로드
- 문서 분석
- 최신 분석 조회
- 나라장터 저장 공고 smoke 생성/분석
- 서버 정리

성공하면 `SMOKE_OK`가 출력됩니다.

### 9. UX monkey 테스트
먼저 서버를 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
```

그 다음 UX 테스트를 실행합니다.

```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531 --screenshot-dir ..\temp\ux-monkey
cd ..
```

이 테스트는 destructive 버튼을 기본적으로 피하면서 주요 라우트를 방문하고, blank page 여부와 기본 UI 사용 가능성을 확인합니다.

끝나면 서버를 중지합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action stop
```

### 10. 나라장터 API 테스트
나라장터 API 인증키가 있을 때만 실행합니다.

인증키 발급 절차:
1. 공공데이터포털에 로그인합니다.
2. [조달청_나라장터 입찰공고정보서비스](https://www.data.go.kr/data/15129394/openapi.do) 페이지로 이동합니다.
3. `활용신청`을 누르고 신청을 완료합니다.
4. 승인 후 공공데이터포털의 마이페이지 또는 활용신청 내역에서 일반 인증키를 확인합니다.
5. 받은 키를 `backend/.env`의 `NARA_API_SERVICE_KEY`에 넣거나, 테스트 실행 전 PowerShell 환경변수로 넣습니다.

참고:
- 이 API는 REST 방식이며 JSON/XML 응답을 제공합니다.
- 공공데이터포털 기준 개발단계와 운영단계 모두 자동승인으로 표시되어 있습니다.
- 개발계정 기본 트래픽은 1,000건으로 표시됩니다. 운영 트래픽은 활용사례 등록 후 증설 신청이 필요할 수 있습니다.
- 인증키 원문은 README, 로그, 프론트엔드 화면, Git 커밋에 남기지 않습니다.

```powershell
$env:NARA_API_SERVICE_KEY="your_key_here"
py -3.13 scripts\test-nara-api.py --date 20260505 --num-of-rows 10
```

공고 PDF 샘플 수집/QA 스크립트도 실제 키가 있어야 안정적으로 동작합니다.

### 11. 수동 실행이 필요할 때
서버 관리 스크립트 대신 직접 실행하려면 아래처럼 실행합니다.

백엔드:

```powershell
cd backend
$env:APP_PORT="18111"
$env:PYTHONUTF8="1"
py -3.13 -m app.main
```

프론트엔드:

```powershell
cd frontend
$env:VITE_API_BASE_URL="http://127.0.0.1:18111"
npm run dev -- --host 127.0.0.1 --port 5199
```

### 12. ngrok 외부 접속
ngrok 외부 접속은 개발/시연용입니다. 먼저 [ngrok](https://ngrok.com/)을 설치하고, ngrok 대시보드에서 발급받은 token을 로컬 CLI에 등록합니다.

```powershell
ngrok config add-authtoken <your-ngrok-token>
```

실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start
```

상태 확인:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 status
```

중지:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 stop
```

화면에서는 `설정 > 외부 접속`에서 public URL을 확인합니다. public URL이 켜져 있는 동안 로컬 서비스가 외부에 노출되므로 민감 문서 업로드와 URL 공유 범위를 주의합니다.

### 13. 계약서 DOCX 초안 생성
1. 나라장터 공고를 검색하고 `공고 상세 저장`을 실행합니다.
2. `법인 관리`에서 계약상대자로 사용할 법인 기본정보를 확인합니다.
3. `계약서 생성` 화면에서 저장 공고와 법인을 선택합니다.
4. 계약번호, 계약금액, 계약기간, 위치, 전화번호, 그 밖의 사항, 붙임서류를 입력합니다.
5. `미리보기`로 표준계약서 필드 매핑을 확인합니다.
6. `계약서 초안 생성` 후 DOCX를 다운로드합니다.

생성된 문서는 `용역표준계약서` 양식을 따른 검토용 초안입니다. 법률 검토나 관리자 확인 없이 확정 계약서로 사용하지 않습니다.

### 14. 자주 나는 문제
- `py -3.13`을 찾지 못함
  - Python 3.13.13 설치와 Windows Python Launcher 설정을 확인합니다.
- `npm run build`가 Node 버전을 요구함
  - Node.js `20.19.0 이상` 또는 `22.12.0 이상`으로 올립니다.
- 포트가 이미 사용 중
  - `scripts/manage-servers.ps1 -Action stop`을 먼저 실행하거나 `-BackendPort`, `-FrontendPort`를 바꿉니다.
- 나라장터 API가 실패함
  - `NARA_API_SERVICE_KEY` 설정 여부, 키 인코딩, 공공데이터포털 승인 상태를 확인합니다.
- OCR 관련 경고가 나옴
  - 기본 테스트에는 치명적이지 않습니다. OCR을 실제로 검증할 때만 `backend/requirements-ocr.txt`를 설치합니다.

## 문서 링크
- [기술 설계서](docs/technical-design.md)
- [UX 설계서](docs/ux-design.md)
- [AI API 세팅 가이드](docs/ai-api-setup.md)
- [OCR 엔진 구현계획](docs/ocr-engine-implementation-plan.md)
- [핵심 기술 요소 및 활용 기술 정리](docs/technology-summary.md)
- [비개발자용 서비스 Rocket Pitch](docs/service-rocket-pitch.md)
- [법인 증빙자료 자동 추출 설계](docs/corporation-evidence-auto-extraction-plan.md)
- [Phase 1.6 안정화 계획](docs/phase-1.6-stabilization-plan.md)
- [Phase 1.7 안정화 계획](docs/phase-1.7-stabilization-plan.md)
- [Phase 2 / 2.5 구현계획](docs/phase-2-implementation-plan.md)
- [P1/P2/문서 보강 수정계획서](docs/p1-p2-doc-remediation-plan.md)
- [남은 개발 단계 로드맵](docs/remaining-development-roadmap.md)
- [Phase 2 종료 보강 ~ Phase 3 실행계획](docs/phase-2-closeout-to-phase-3-execution-plan.md)
- [부족조건 판단 및 로컬 RAG 상세 구현계획](docs/eligibility-rag-implementation-plan.md)
- [나라장터 API 분석](docs/narajangteo-api-analysis.md)
- [나라장터 API 테스트 결과](docs/narajangteo-api-test-result-20260505.md)
- [나라장터 게시판 설계](docs/narajangteo-board-design.md)
- [OpenDataLoader PDF 리더 교체 및 테스트 계획](docs/opendataloader-pdf-replacement-test-plan.md)
- [PDF/RAG 코드리뷰 수정계획](docs/pdf-rag-code-review-remediation-plan.md)
- [현재 코드/문서 감사 리포트](docs/current-code-documentation-audit.md)
- [ngrok 외부 접속 및 계약서 DOCX 자동 생성 설계/구현계획](docs/ngrok-external-access-and-contract-docx-plan.md)
- [작업 로그](docs/work-log.md)
- [에이전트 가이드](AGENTS.md)

## 가정
- Phase 1은 단일 관리자, 단일 PC 운영
- Phase 1에는 로그인 없음
- HWP는 범위 제외
- 기준문서는 PDF만 허용
- 프로젝트는 우선 1개 법인에 연결

## 미해결 질문
- 법인 프로필에 사업자등록번호를 MVP 필수로 넣을지
- OCR 오류 보정 UI가 필요한지
- 분석 결과 내보내기(PDF/Excel)가 필요한지
- 기준문서 카테고리 체계를 누가 운영할지

## 로드맵
1. 문서 설계 확정
2. 저장소 스캐폴딩 생성
3. Phase 1 MVP 구현
4. Phase 1.5 나라장터 게시판과 공고 자동 분석 추가
5. Phase 1.6 법인 증빙자료 자동 추출과 법인 프로필 보강
6. 기준문서 파이프라인과 로컬 RAG 추가
7. 부족 조건/준비 가이드 중심 판단 엔진 확장
8. 조달 공고 자동 수집 확장

---

# AI / Engineering Version (English)

## Overview
`SMART Procurement Calculator` is a local-first admin portal for a single administrator who manages corporations, creates projects, uploads procurement-related PDF/DOCX documents, and reviews AI-generated summaries and structured outputs.

## Current Code Snapshot
Last documentation update: 2026-06-07

- Default PDF extraction is `PDF_READER_ENGINE=auto`: OpenDataLoader first, PyMuPDF fallback.
- Target documents, Nara notice attachments, and basis PDFs share the same `extract_document()` entrypoint.
- DOCX extraction includes both paragraphs and table cell text.
- Basis retrieval uses the operational JSON index artifact at `storage/basis-index/basis-index.json`; invalid or inconsistent index state blocks search/citation usage and requires rebuild.
- The gap-first judgment engine stores missing conditions, required documents, preparation guidance, and citation status rather than optimistic final eligibility.
- Phase 4 operations pages cover dashboard, operation runs, failures/retries, backups, validation, and restore dry-runs.
- The contract draft page generates review-only `용역표준계약서` DOCX drafts from saved notices and corporation profile data.
- The external access page displays ngrok public URLs created by `scripts/manage-ngrok.ps1`; the frontend does not start or stop ngrok directly.

## Phase Plan
- Phase 1: upload/manage/summarize MVP
- Phase 1.5: Nara Marketplace board, API notice search, attachment download, notice analysis
- Phase 1.6: corporation evidence auto-extraction and profile enrichment
- Phase 2: basis PDF management and local RAG preparation
- Phase 2 operations hardening: basis rule candidate review and Nara collection run management
- Phase 3: gap-first judgment engine and procurement notice auto-collection
- Phase 4: operations dashboard, operation/failure management, and backup/restore management
- Phase 4E: ngrok external access for the local-first service
- Phase 5A: DOCX contract draft generation from saved notices and corporation data

## Stack
- Frontend: React, TypeScript, Vite, React Router
- Backend: Python 3.13.13; current implementation uses Flask; FastAPI remains an optional future refactor target
- DB: SQLite
- Storage: local filesystem
- PDF extraction: OpenDataLoader PDF in `auto` mode by default, with PyMuPDF fallback
- DOCX extraction: python-docx paragraphs plus table cells
- OCR: PaddleOCR PP-OCRv5 primary, Tesseract as a lighter fallback candidate
- Runtime command: use Windows `py -3.13` or `C:\Python313\python.exe`; do not run backend/OCR with any other Python runtime
- LLM: Gemini `gemini-2.5-flash` as the default model; OpenAI `gpt-5.4-mini` / `gpt-5.4` as selectable alternatives
- Future vector DB: Qdrant preferred, Chroma optional

## Quick Setup And Verification
This project is optimized for local Windows PowerShell operation.

Required tools:
- Python `3.13.13`
- Node.js `20.19.0+` or `22.12.0+`
- npm
- Git
- Java 11+ for OpenDataLoader PDF conversion

Install backend dependencies:

```powershell
cd backend
py -3.13 -m pip install --upgrade pip
py -3.13 -m pip install -r requirements.txt
cd ..
```

Install frontend dependencies and the browser runtime for UX tests:

```powershell
cd frontend
npm install
npx playwright install chromium
cd ..
```

Start local servers:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
```

Default URLs:
- Backend: `http://127.0.0.1:18111`
- Frontend: `http://127.0.0.1:5199`

Stop local servers:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action stop
```

Start ngrok external access after configuring the ngrok token:

```powershell
ngrok config add-authtoken <your-ngrok-token>
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 status
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 stop
```

Generate a contract draft:
- save a Nara notice
- confirm corporation profile data
- open `계약서 생성`
- preview the standard-form mapping
- generate and download the DOCX draft

Run full backend tests:

```powershell
py -3.13 -m pytest backend/tests -q
```

Run real basis PDF OpenDataLoader QA:

```powershell
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine opendataloader --threads 4 --timeout-seconds 1200 --strict
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine auto --threads 4 --timeout-seconds 1200 --strict
```

Run fallback QA:

```powershell
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine auto --threads 1 --timeout-seconds 1 --min-table-count 0 --min-table-row-chunks 0 --min-reference-table-row-coverage 0 --min-reference-table-row-token-coverage 0
```

Run frontend build:

```powershell
cd frontend
npm run build
cd ..
```

Run encoding and dependency checks:

```powershell
py -3.13 scripts/check-encoding.py
cd frontend
npm audit --audit-level=moderate
cd ..
```

Run live API smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
```

Run UX monkey smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531 --screenshot-dir ..\temp\ux-monkey
cd ..
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action stop
```

Environment notes:
- `scripts/manage-servers.ps1` copies `.env.example` files when `.env` files are missing.
- API keys are optional for basic local tests.
- Real Gemini/OpenAI/Nara API tests require keys in `backend/.env` or process environment variables.
- `PDF_READER_ENGINE=auto` tries OpenDataLoader first and falls back to PyMuPDF when Java/package/timeout/conversion failures occur.
- Gemini API users can create and manage keys in [Google AI Studio API keys](https://aistudio.google.com/app/apikey), then copy the issued key into `GEMINI_API_KEY`.
- Nara API users must apply for access on the [Public Data Portal Nara Bid Notice API page](https://www.data.go.kr/data/15129394/openapi.do), then copy the issued service key into `NARA_API_SERVICE_KEY`.
- Never commit API keys.

Phase 1.6 should be delivered incrementally:
- 1.6A: business registration evidence-based corporation registration MVP
- 1.6B: core procurement evidence expansion
- 1.6C: unknown evidence LLM classification and operational hardening

## Assumptions
- single admin only in phase 1
- no auth in phase 1
- PDF and DOCX only for target documents
- PDF only for basis documents
- project maps to one corporation in MVP

## Open Questions
- whether business registration number is required in MVP
- whether OCR correction UI is needed
- whether export is needed
- who owns basis taxonomy

## References
- OCR Engine Implementation Plan: [docs/ocr-engine-implementation-plan.md](docs/ocr-engine-implementation-plan.md)
- Corporation Evidence Auto-Extraction Plan: [docs/corporation-evidence-auto-extraction-plan.md](docs/corporation-evidence-auto-extraction-plan.md)
- Phase 1.7 Stabilization Plan: [docs/phase-1.7-stabilization-plan.md](docs/phase-1.7-stabilization-plan.md)
- P1/P2/Documentation Remediation Plan: [docs/p1-p2-doc-remediation-plan.md](docs/p1-p2-doc-remediation-plan.md)
- Gap Judgment / RAG Plan: [docs/eligibility-rag-implementation-plan.md](docs/eligibility-rag-implementation-plan.md)
- Gemini API Docs: [https://ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
- Gemini Structured Outputs: [https://ai.google.dev/gemini-api/docs/structured-output](https://ai.google.dev/gemini-api/docs/structured-output)
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
- PDF Files Guide: [https://platform.openai.com/docs/guides/pdf-files](https://platform.openai.com/docs/guides/pdf-files)
- Qdrant Concepts: [https://qdrant.tech/documentation/concepts/vectors/](https://qdrant.tech/documentation/concepts/vectors/)
