# 한국어 버전

## 프로젝트 개요
`SMART 조달청 계산기`는 단일 관리자 사용자(행정사)가 법인 정보를 관리하고, 프로젝트를 생성하고, 조달 관련 PDF/DOCX 문서를 프로젝트 단위로 업로드하여 AI 기반 요약과 구조화 결과를 확인하는 로컬 실행형 웹 어드민 포탈입니다.

이 프로젝트는 단계적으로 확장됩니다.
- Phase 1: 업로드, 관리, 요약 MVP
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
  README.md
  AGENTS.md
```

## 기술 스택
- Frontend: React + TypeScript + Vite + React Router + TanStack Query
- Backend: Python 3.12 + FastAPI + SQLAlchemy + Pydantic
- DB: SQLite
- File Storage: Local filesystem
- OCR: Local OCR pipeline
- Parsing: PDF, DOCX only
- AI: External LLM API
- Future Vector Store: Qdrant 우선, Chroma 대안

## 추천 AI/API 전략
- 주 모델: `OpenAI GPT-5.1`
- 저비용 보조 모델: `GPT-5 mini`
- OCR은 로컬에서 처리한 뒤 정규화 텍스트를 모델에 전달
- 요약은 JSON 구조화 출력 + 사용자용 마크다운 병행 저장
- 재분석은 프롬프트 버전/입력 해시 기반으로 캐시 제어

## 로컬 개발 가이드

### 사전 요구사항
- Python 3.12+
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
OPENAI_API_KEY=your_key_here
OPENAI_MODEL_PRIMARY=gpt-5.1
OPENAI_MODEL_SECONDARY=gpt-5-mini
OCR_LANGUAGES=kor+eng
```

프론트엔드 `.env`
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 실행 예시
백엔드
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
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
4. 기준문서 파이프라인 추가
5. 판단 엔진 및 크롤러 확장

---

# AI / Engineering Version (English)

## Overview
`SMART Procurement Calculator` is a local-first admin portal for a single administrator who manages corporations, creates projects, uploads procurement-related PDF/DOCX documents, and reviews AI-generated summaries and structured outputs.

## Phase Plan
- Phase 1: upload/manage/summarize MVP
- Phase 2: basis PDF management and local RAG preparation
- Phase 3: judgment engine and procurement notice auto-collection

## Stack
- Frontend: React, TypeScript, Vite, TanStack Query
- Backend: FastAPI, SQLAlchemy, Pydantic
- DB: SQLite
- Storage: local filesystem
- OCR: local OCR pipeline
- LLM: GPT-5.1 primary, GPT-5 mini secondary
- Future vector DB: Qdrant preferred, Chroma optional

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
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
- PDF Files Guide: [https://platform.openai.com/docs/guides/pdf-files](https://platform.openai.com/docs/guides/pdf-files)
- Qdrant Concepts: [https://qdrant.tech/documentation/concepts/vectors/](https://qdrant.tech/documentation/concepts/vectors/)
