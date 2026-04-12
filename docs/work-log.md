# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기` 프로젝트의 실제 작업 내역을 누적 기록합니다.  
요청하신 대로 앞으로 이 대화에서 작업이 진행될 때마다 이 파일을 업데이트합니다.

## 최신 업데이트
- 업데이트 시각: `2026-04-05 19:59:35 +09:00`
- 작업 범위: Phase 1 착수 + AI API 세팅 문서 추가

### 1) 문서 작업
- 프로젝트 설계 문서 재작성
  - `README.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `AGENTS.md`
- AI API 세팅 가이드 신규 작성
  - `docs/ai-api-setup.md`

### 2) 백엔드 초기 구현 (Phase 1)
- FastAPI + SQLite 기반 백엔드 골격 생성
- 도메인 모델 생성
  - `corporations`
  - `projects`
  - `project_documents`
  - `analyses`
- 핵심 API 라우트 구현
  - 대시보드 요약
  - 법인 CRUD
  - 프로젝트 CRUD
  - 문서 업로드/조회/삭제
  - 문서 분석/재분석
  - 최신 분석 조회
- 파이프라인 구현
  - 파일 파싱(PDF/DOCX)
  - OCR 연동 포인트(placeholder)
  - 요약기(OpenAI 연동 + fallback)
  - 분석 캐시/재분석 처리

### 3) 프론트엔드 초기 구현 (Phase 1)
- React + Vite + TypeScript 스캐폴딩 생성
- 어드민 기본 라우팅/레이아웃 생성
- 페이지 구현
  - Dashboard
  - Corporations
  - Projects
  - Documents(업로드/분석 버튼)
  - Analysis(결과 확인)
- API 클라이언트 연결

### 4) 공통/운영
- `.gitignore` 추가
- `backend/.env.example`, `frontend/.env.example` 추가
- `backend/requirements.txt` 추가

## 검증 메모
- 코드 런타임 검증은 현재 환경에 패키지(`fastapi` 등) 미설치 상태라 미완료
- `compileall` 실행 시 `__pycache__` 파일 권한 이슈 발생 (문법 이슈보다는 환경 권한 이슈)

## 다음 작업 예정
1. 백엔드/프론트 의존성 설치 후 스모크 테스트
2. OCR 실제 엔진 연결(Tesseract 또는 PaddleOCR)
3. 목록 검색/필터/수정/삭제 UX 고도화

## 추가 업데이트 (2026-04-05)
- 요청사항 반영
  - AI API 세팅 문서 생성: `docs/ai-api-setup.md`
  - 스모크 테스트 스크립트 추가: `scripts/smoke-test.ps1`
- 실제 실행 결과
  - 백엔드 의존성 설치 및 서버 기동 성공
  - 자동 API 스모크 시나리오 성공
    - corporation_id=1
    - project_id=1
    - document_id=1
    - analysis_id=1
- 자동 수정 내역
  - Python 3.14 환경의 패키지 호환 이슈로 백엔드 런타임 의존성 조정
  - 로컬 파일 기반 SQLite I/O 실패로 인해 테스트 런타임을 공유 메모리 SQLite 방식으로 보정
  - 포트 충돌(8000) 회피를 위해 백엔드 실행 포트 18000 적용
- FE 상태
  - 이 환경에서 Vite dev server가 `spawn EPERM`으로 안정 실행되지 않아 스크립트에서 경고 후 백엔드 스모크를 계속 수행하도록 처리

## 추가 업데이트 (2026-04-05 20:45:05 +09:00)
- 사용자 요청으로 FE/BE 서버 수동 검증용 기동 수행
- BE 서버 기동 확인
  - URL: `http://127.0.0.1:18000`
  - Health: `{"status":"ok"}`
- FE 서버 기동 확인
  - URL: `http://127.0.0.1:5173`
  - 응답: `HTTP/1.1 200 OK`
- FE 기동 실패 원인 수정
  - `frontend/package.json`, `frontend/tsconfig.json`의 UTF-8 BOM 제거
  - BOM으로 인한 Vite JSON 파싱 오류 해결

## 추가 업데이트 (2026-04-05 20:50:24 +09:00)
- 사용자 요청으로 기존 실행 중이던 우리 프로젝트 FE/BE 프로세스를 종료
- 새 포트로 서버 재기동
  - BE: `http://127.0.0.1:18111`
  - FE: `http://127.0.0.1:5199`
- 상태 확인
  - BE health: `{"status":"ok"}`
  - FE HTTP HEAD: `200 OK`
- 실행 상태 파일 갱신
  - `temp/servers.status.json`

## 추가 업데이트 (2026-04-05)
- 사용자 요청으로 실행 중인 FE/BE 서버 종료 수행
- 종료 대상
  - FE 포트: `5199` (기존 테스트 포트 포함 `5173`, `5174`)
  - BE 포트: `18111` (기존 테스트 포트 포함 `18000`, `8000`)
- 검증
  - `netstat` 기준 해당 포트 LISTEN 항목 없음 확인

---

# AI / Engineering Version (English)

## Purpose
This file is a cumulative execution log for actual implementation work.  
Per user request, it must be updated whenever new work is performed in this thread.

## Latest Entry
- Updated at: `2026-04-05 19:59:35 +09:00`
- Scope: Phase 1 implementation start + AI API setup documentation

## Completed Work
- Rewrote design/package docs: `README.md`, `docs/technical-design.md`, `docs/ux-design.md`, `AGENTS.md`
- Added AI API setup guide: `docs/ai-api-setup.md`
- Implemented backend scaffold (FastAPI + SQLite), models, routes, parsing/summary pipeline, cache/re-analysis flow
- Implemented frontend scaffold (React + Vite + TS), dashboard/admin pages, upload/analyze/result flow
- Added operational files: `.gitignore`, env examples, backend requirements

## Validation Notes
- Runtime verification is pending due to missing Python packages in current environment.
- `compileall` produced filesystem permission errors for `__pycache__` writes/deletes.

## Next Planned Steps
1. Install dependencies and run end-to-end smoke tests
2. Integrate real OCR engine
3. Improve search/filter/edit/delete UX paths

## Additional Update (2026-04-05)
- Added AI API setup guide: `docs/ai-api-setup.md`
- Added smoke script: `scripts/smoke-test.ps1`
- Backend smoke flow succeeded end-to-end (create corp -> create project -> upload -> analyze -> fetch latest analysis)
- Applied auto-fixes for environment constraints:
  - dependency compatibility adjustments for Python 3.14 runtime
  - switched runtime DB in smoke path to shared in-memory SQLite due file-based SQLite disk I/O errors
  - moved backend runtime port to `18000` to avoid local port conflict
- Frontend dev server remains unstable in this environment due `spawn EPERM`; script now warns and proceeds with backend smoke verification.

## Additional Update (2026-04-05 20:45:05 +09:00)
- Started FE/BE servers for direct manual verification.
- Backend verified at `http://127.0.0.1:18000` with health response.
- Frontend verified at `http://127.0.0.1:5173` with `HTTP 200`.
- Fixed frontend startup blocker by removing UTF-8 BOM from JSON files:
  - `frontend/package.json`
  - `frontend/tsconfig.json`

## Additional Update (2026-04-05 20:50:24 +09:00)
- Stopped previously running FE/BE processes for this project.
- Restarted servers on new ports:
  - BE: `http://127.0.0.1:18111`
  - FE: `http://127.0.0.1:5199`
- Verified service readiness:
  - backend health endpoint returned `{"status":"ok"}`
  - frontend responded with `HTTP 200`
- Updated runtime status file: `temp/servers.status.json`

## Additional Update (2026-04-05)
- Stopped running FE/BE servers per user request.
- Verified no LISTEN sockets on relevant ports:
  - FE-related: `5199`, `5173`, `5174`
  - BE-related: `18111`, `18000`, `8000`

## 추가 업데이트 (2026-04-05 21:03:18 +09:00)
- 사용자 요청으로 Phase 1 포탈 UX 사용성 리뷰 및 화면 업그레이드 진행
- 리뷰한 주요 사용성 이슈
  - 정보 구조가 평평해서 다음 액션이 잘 보이지 않음
  - 프로젝트/법인/문서의 관계가 화면에서 직관적으로 드러나지 않음
  - 업로드 폼과 분석 결과 화면이 너무 단순해서 재검토 피로도가 큼
  - 전체 색감이 차갑고 어두워 브랜드 인상이 약함
- 적용한 개선
  - 앱 셸 재구성: 벚꽃 테마 사이드바, 히어로 패널, 단계 안내 문맥 강화
  - 대시보드 개편: 다음 액션 안내, KPI 카드, 추천 워크플로 추가
  - 법인 관리 개편: MVP 필드 확장, 검색 추가, 빈 상태/설명 강화
  - 프로젝트 관리 개편: 법인 연결 문맥 강화, 카드형 프로젝트 목록 추가
  - 문서 관리 개편: 업로드 메타데이터 UX 개선, 검색/상태 필터, 프로젝트/법인명 표시
  - 분석 결과 개편: 핵심 요약/요구사항/확인 포인트 카드화, 재분석 버튼 정리
  - 디자인 개편: 벚꽃 느낌의 밝은 핑크/코랄/연그린 기반 컬러 시스템으로 전환
- 검증
  - `frontend`에서 `npm run build` 성공

## Additional Update (2026-04-05 21:03:18 +09:00)
- Per user request, reviewed and upgraded Phase 1 portal UX.
- Main UX findings
  - flat information hierarchy
  - weak visibility of project/corporation/document relationships
  - upload and analysis screens too bare for repeated review work
  - color system felt dull and unmemorable
- Implemented improvements
  - redesigned app shell with sakura-themed sidebar and hero context
  - upgraded dashboard with next-action guidance and KPI cards
  - improved corporation/project/document flows with richer forms, search, filters, and empty states
  - redesigned analysis view into summary cards and clearer re-analysis flow
  - replaced muted palette with brighter sakura pink / coral / soft leaf accents
- Verification
  - `npm run build` passed in `frontend`

## 추가 업데이트 (2026-04-05 21:16:12 +09:00)
- FE/BE 서버를 한 번에 관리하는 올인원 스크립트 추가
  - `scripts/manage-servers.ps1`
- 지원 액션
  - `start`
  - `stop`
  - `restart`
  - `status`
- 기본 포트
  - BE: `18111`
  - FE: `5199`
- 서버 상태는 `temp/servers.status.json`에 기록되도록 구성
- `scripts/smoke-test.ps1`도 새 관리 스크립트를 사용하도록 정리
- 실제 검증
  - `start -> status -> restart -> status -> stop -> status` 순차 검증 완료
  - 최종 상태는 서버 중지 상태

## Additional Update (2026-04-05 21:16:12 +09:00)
- Added all-in-one FE/BE server management script:
  - `scripts/manage-servers.ps1`
- Supported actions:
  - `start`
  - `stop`
  - `restart`
  - `status`
- Default ports:
  - BE: `18111`
  - FE: `5199`
- Script writes runtime state to `temp/servers.status.json`
- Updated `scripts/smoke-test.ps1` to reuse the new server manager
- Verified sequential lifecycle:
  - `start -> status -> restart -> status -> stop -> status`
  - final state is stopped

## 추가 업데이트 (2026-04-05 21:19:05 +09:00)
- 사용자 피드백 반영
  - `manage-servers.ps1` 실행 시 비어 있는 Windows 터미널 창 2개가 뜨는 문제 수정
- 변경 내용
  - FE/BE 프로세스 시작 시 `Start-Process -WindowStyle Hidden` 적용
  - 서버가 콘솔 창 없이 백그라운드에서 실행되도록 조정
- 검증
  - `start -> status -> stop -> status` 순차 실행 확인
  - 최종 상태는 서버 중지 상태

## Additional Update (2026-04-05 21:19:05 +09:00)
- Addressed user feedback about empty Windows terminal windows appearing.
- Updated `manage-servers.ps1` to start FE/BE processes with hidden window mode.
- Verified sequential lifecycle again:
  - `start -> status -> stop -> status`
  - final state is stopped

## 추가 업데이트 (2026-04-05)
- `manage-servers.ps1`로 서버 실행 요청 반영
- 실행 결과
  - BE: 실행 성공 (`http://127.0.0.1:18111`)
  - FE: 실행 성공 (`http://127.0.0.1:5199`)

## Additional Update (2026-04-05)
- Started servers using `manage-servers.ps1`
- Result:
  - BE running at `http://127.0.0.1:18111`
  - FE running at `http://127.0.0.1:5199`

## 추가 업데이트 (2026-04-05 21:40:00 +09:00)
- 사용자 질문 기준으로 현재 구현의 "내부 fallback 요약" 동작 방식 점검
- 확인 결과
  - PDF/DOCX 텍스트 추출은 로컬 처리이며 API 키가 필요하지 않음
  - `OPENAI_API_KEY`가 있으면 `gpt-5.1`로 요약 호출
  - API 키가 없거나 API 호출 실패 시 규칙 기반 fallback 요약 사용
  - fallback 요약은 AI 모델이 아니라 텍스트 앞부분/일부 줄을 재구성하는 임시 로직
- 참고 파일
  - `backend/app/main.py`
  - `docs/ai-api-setup.md`

## Additional Update (2026-04-05 21:40:00 +09:00)
- Reviewed the current "internal fallback summary" behavior in response to a product question.
- Confirmed:
  - PDF/DOCX text extraction is local and does not require an API key.
  - If `OPENAI_API_KEY` exists, the app calls `gpt-5.1` for summary generation.
  - If the key is missing or the API call fails, the app uses a deterministic fallback summary.
  - The fallback is not an AI model; it is a temporary rule-based summarization path built from extracted text lines.
- Reference files:
  - `backend/app/main.py`
  - `docs/ai-api-setup.md`

## 추가 업데이트 (2026-04-05 21:47:00 +09:00)
- 사용자 질문 기준으로 현재 PDF 텍스트 추출/요약 라이브러리 사용 현황 점검
- 확인 결과
  - PDF 텍스트 추출: `pypdf`
  - DOCX 텍스트 추출: `python-docx`
  - AI 요약 API 호출: `openai` Python SDK
  - 스캔 PDF용 OCR 엔진은 아직 실제 연결되지 않음
- 참고 파일
  - `backend/requirements.txt`
  - `backend/app/main.py`

## Additional Update (2026-04-05 21:47:00 +09:00)
- Reviewed the current libraries used for PDF extraction and summarization in response to a user question.
- Confirmed:
  - PDF text extraction: `pypdf`
  - DOCX text extraction: `python-docx`
  - AI summary API call: `openai` Python SDK
  - No real OCR engine is connected yet for scanned PDFs
- Reference files:
  - `backend/requirements.txt`
  - `backend/app/main.py`
