# 한국어 버전

## 프로젝트 개요
`SMART 조달청 계산기`는 단일 관리자 사용자(행정사)가 법인 정보를 관리하고, 프로젝트를 생성하고, 조달 관련 PDF/DOCX 문서를 프로젝트 단위로 업로드하여 AI 기반 요약과 구조화 결과를 확인하는 로컬 실행형 웹 어드민 포탈입니다.

이 프로젝트는 단계적으로 확장됩니다.
- Phase 1: 업로드, 관리, 요약 MVP
- Phase 1.5: 나라장터 게시판, 공고 API 조회, 첨부 다운로드, 공고 자동 분석
- Phase 1.6: 법인 증빙자료 자동 추출과 법인 프로필 보강
- Phase 2: 기준 PDF 관리와 로컬 RAG 준비
- Phase 3: 판단 엔진과 조달 공고 자동 수집

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

### Phase 3
- 조달 공고 자동 수집
- 공고 및 첨부 자동 수집
- 공고 분석 저장
- 법인-공고 요구조건 매칭
- 기준문서 검색 기반 판단
- 근거 조항 출력
- 체크리스트 생성
- 준비 가이드 생성

## 주요 기능
- 법인 관리
- 프로젝트 중심 이력 관리
- 메타데이터 포함 파일 업로드
- 문서 분석 결과 페이지
- 검색/필터/상세/수정/삭제
- 나라장터 공고 검색/상세/저장/분석 설계
- 나라장터 API 설정 상태 확인 설계
- 기준 PDF 별도 지식 자산 관리
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
  - PDF 기본 추출 엔진은 `PyMuPDF`
  - DOCX는 `python-docx` 유지
  - 스캔/이미지형 PDF는 추출 텍스트 부족 시 OCR fallback 적용
- AI: External LLM API
- Future Vector Store: Qdrant 우선, Chroma 대안

## 추천 AI/API 전략
- 기본 Provider/모델: Google Gemini `gemini-2.5-flash`
- 보조 Provider/모델: OpenAI `gpt-5.4-mini`, `gpt-5.4`
- 포탈에서 분석 실행 시 사용할 Provider/모델을 선택할 수 있습니다.
- 실제 API 키는 `backend/.env`에 직접 입력하며, 화면에는 설정 여부와 마스킹 값만 표시합니다.
- PDF는 `PyMuPDF`로 텍스트/블록/페이지 구조를 먼저 추출
- OCR은 텍스트 레이어가 부족한 PDF에만 fallback으로 적용
- OCR 주 엔진은 `PaddleOCR PP-OCRv5`, 경량 대안은 `Tesseract(kor+eng)`로 둔다.
- PaddleOCR은 Windows 기준 Python 3.13.13 런타임(`py -3.13`)에서 우선 검증한다.
- 정규화된 추출 텍스트를 모델에 전달
- 요약은 JSON 구조화 출력 + 사용자용 마크다운 병행 저장
- 재분석은 프롬프트 버전/입력 해시 기반으로 캐시 제어

## 로컬 개발 가이드

### 사전 요구사항
- Python 3.13.13
- Node.js 20+
- npm 또는 pnpm

### 환경 변수 예시
백엔드 `.env`
```env
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
SQLITE_PATH=./app.db
STORAGE_ROOT=./storage
AI_PROVIDER_DEFAULT=gemini
AI_MODEL_DEFAULT=gemini-2.5-flash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL_PRIMARY=gpt-5.4-mini
OPENAI_MODEL_SECONDARY=gpt-5.4
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL_PRIMARY=gemini-2.5-flash
OCR_ENGINE=paddle
OCR_LANG=kor+eng
OCR_DEVICE=cpu
OCR_MIN_TEXT_LENGTH=80
OCR_RENDER_DPI=220
NARA_API_SERVICE_KEY=your_nara_api_key_here
NARA_BID_PUBLIC_API_BASE_URL=https://apis.data.go.kr/1230000/ad/BidPublicInfoService
NARA_PUBDATA_API_BASE_URL=https://apis.data.go.kr/1230000/ao/PubDataOpnStdService
NARA_API_RESPONSE_TYPE=json
```

프론트엔드 `.env`
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 실행 예시
백엔드
```bash
cd backend
py -3.13 -m pip install -r requirements.txt
py -3.13 -m pip install -r requirements-ocr.txt
$env:APP_PORT="8000"
py -3.13 -m app.main
```

프론트엔드
```bash
cd frontend
npm install
npm run dev
```

### 스모크 테스트 실행
```bash
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
```
스모크 스크립트는 백엔드 서버를 기동하고 `법인 생성 -> 프로젝트 생성 -> 문서 업로드 -> 분석 -> 결과 조회`를 자동 검증합니다.

### 나라장터 API 테스트 실행
```bash
cd D:\project\wisdom_procurement
$env:NARA_API_SERVICE_KEY="your_key_here"
py -3.13 scripts\test-nara-api.py --date 20260505 --num-of-rows 10
```
실제 인증키는 Git에 커밋하지 말고 환경변수 또는 `backend/.env`로만 관리합니다.

### 백엔드 단위 테스트 실행
```bash
cd backend
py -3.13 -m unittest discover -s tests -v
```
현재 단위 테스트는 `PyMuPDF` 기반 PDF 추출, OCR 후보 판정, DOCX 추출 경로를 검증합니다.

### 서버 관리 스크립트
```bash
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action status
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action restart
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action stop
```
기본 포트는 `BE=18111`, `FE=5199`입니다. 필요하면 `-BackendPort`, `-FrontendPort` 옵션으로 바꿀 수 있습니다.

## 문서 링크
- [기술 설계서](/D:/project/wisdom_procurement/docs/technical-design.md)
- [UX 설계서](/D:/project/wisdom_procurement/docs/ux-design.md)
- [AI API 세팅 가이드](/D:/project/wisdom_procurement/docs/ai-api-setup.md)
- [OCR 엔진 구현계획](/D:/project/wisdom_procurement/docs/ocr-engine-implementation-plan.md)
- [핵심 기술 요소 및 활용 기술 정리](/D:/project/wisdom_procurement/docs/technology-summary.md)
- [법인 증빙자료 자동 추출 설계](/D:/project/wisdom_procurement/docs/corporation-evidence-auto-extraction-plan.md)
- [Phase 1.6 안정화 계획](/D:/project/wisdom_procurement/docs/phase-1.6-stabilization-plan.md)
- [Phase 1.7 안정화 계획](/D:/project/wisdom_procurement/docs/phase-1.7-stabilization-plan.md)
- [지원 가능성 판단 및 로컬 RAG 상세 구현계획](/D:/project/wisdom_procurement/docs/eligibility-rag-implementation-plan.md)
- [나라장터 API 분석](/D:/project/wisdom_procurement/docs/narajangteo-api-analysis.md)
- [나라장터 API 테스트 결과](/D:/project/wisdom_procurement/docs/narajangteo-api-test-result-20260505.md)
- [나라장터 게시판 설계](/D:/project/wisdom_procurement/docs/narajangteo-board-design.md)
- [작업 로그](/D:/project/wisdom_procurement/docs/work-log.md)
- [에이전트 가이드](/D:/project/wisdom_procurement/AGENTS.md)

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

## Phase Plan
- Phase 1: upload/manage/summarize MVP
- Phase 1.5: Nara Marketplace board, API notice search, attachment download, notice analysis
- Phase 1.6: corporation evidence auto-extraction and profile enrichment
- Phase 2: basis PDF management and local RAG preparation
- Phase 3: judgment engine and procurement notice auto-collection

## Stack
- Frontend: React, TypeScript, Vite, React Router
- Backend: Python 3.13.13; current implementation uses Flask; FastAPI remains an optional future refactor target
- DB: SQLite
- Storage: local filesystem
- PDF extraction: PyMuPDF as the default PDF reader/extractor
- DOCX extraction: python-docx
- OCR: PaddleOCR PP-OCRv5 primary, Tesseract as a lighter fallback candidate
- Runtime command: use Windows `py -3.13` or `C:\Python313\python.exe`; do not run backend/OCR with any other Python runtime
- LLM: Gemini `gemini-2.5-flash` as the default model; OpenAI `gpt-5.4-mini` / `gpt-5.4` as selectable alternatives
- Future vector DB: Qdrant preferred, Chroma optional

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
- Eligibility / RAG Plan: [docs/eligibility-rag-implementation-plan.md](docs/eligibility-rag-implementation-plan.md)
- Gemini API Docs: [https://ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
- Gemini Structured Outputs: [https://ai.google.dev/gemini-api/docs/structured-output](https://ai.google.dev/gemini-api/docs/structured-output)
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
- PDF Files Guide: [https://platform.openai.com/docs/guides/pdf-files](https://platform.openai.com/docs/guides/pdf-files)
- Qdrant Concepts: [https://qdrant.tech/documentation/concepts/vectors/](https://qdrant.tech/documentation/concepts/vectors/)
