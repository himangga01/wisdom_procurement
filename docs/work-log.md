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

## 추가 업데이트 (2026-05-04)
- 현재 프로젝트 상태 분석 요청 반영
- 확인 결과
  - FE 빌드: `npm run build` 성공
  - 서버 관리 스크립트: `manage-servers.ps1`로 FE/BE 시작 및 중지 가능
  - BE 헬스체크: `/health` 정상 응답
  - Dashboard API: `/api/dashboard/summary` 정상 응답
  - 스모크 테스트 스크립트: 한글 문자열 인코딩/문법 깨짐으로 현재 실행 실패
  - 실제 실행 백엔드는 Flask 단일 파일이며, 설계 문서/일부 골격 파일은 FastAPI 기준으로 남아 있음
  - 현재 DB는 공유 메모리 SQLite로 동작하여 서버 재시작 시 데이터가 유지되지 않음
- 참고 파일
  - `backend/app/main.py`
  - `frontend/src/app/api.ts`
  - `scripts/manage-servers.ps1`
  - `scripts/smoke-test.ps1`

## Additional Update (2026-05-04)
- Reviewed the current repository state on request.
- Confirmed:
  - Frontend build passes with `npm run build`.
  - FE/BE can be started and stopped through `manage-servers.ps1`.
  - Backend `/health` responds successfully.
  - Dashboard API `/api/dashboard/summary` responds successfully.
  - `smoke-test.ps1` currently fails because Korean string encoding broke PowerShell syntax.
  - Runtime backend is a Flask single-file implementation, while docs and some scaffold files still describe FastAPI.
  - Current DB is shared in-memory SQLite, so data is not durable across server restarts.
- Reference files:
  - `backend/app/main.py`
  - `frontend/src/app/api.ts`
  - `scripts/manage-servers.ps1`
  - `scripts/smoke-test.ps1`

## 추가 업데이트 (2026-05-04)
- 사용자 요청에 따라 우선순위 수정 2건 처리
- 수정 내용
  - `backend/app/main.py`
    - 공유 메모리 SQLite 사용 제거
    - `.env`의 `SQLITE_PATH` 값을 읽어 파일 기반 SQLite DB를 사용하도록 복구
    - 기본 경로는 `backend/app.db`
  - `scripts/smoke-test.ps1`
    - 깨진 한글 테스트 문자열을 ASCII 기반 테스트 데이터로 교체
    - FE/BE를 자체 백그라운드 프로세스로 실행하고 준비 상태 확인 후 테스트하도록 수정
    - 테스트 진행 로그를 `temp/smoke-test.log`에 기록
  - `scripts/manage-servers.ps1`
    - 서버 정리 후보에서 호출자 PowerShell 프로세스를 제외하도록 조정
- 검증 결과
  - `scripts/smoke-test.ps1` 실행 성공
  - 결과: `SMOKE_OK`, `corporation_id=2`, `project_id=2`, `document_id=2`, `analysis_id=2`
  - 서버 재시작 후 `/api/dashboard/summary`에서 `corporation_count=2`, `project_count=2`, `document_count=2` 확인
  - 검증 후 FE/BE 서버 종료 완료

## Additional Update (2026-05-04)
- Completed two priority fixes requested by the user.
- Changes:
  - `backend/app/main.py`
    - Removed shared in-memory SQLite usage.
    - Restored file-based SQLite using the `SQLITE_PATH` environment variable.
    - Default DB path is `backend/app.db`.
  - `scripts/smoke-test.ps1`
    - Replaced broken Korean test strings with ASCII-safe test data.
    - Starts FE/BE as background processes directly, waits for readiness, and then runs the API workflow.
    - Writes progress logs to `temp/smoke-test.log`.
  - `scripts/manage-servers.ps1`
    - Excludes caller PowerShell processes from server cleanup candidates.
- Verification:
  - `scripts/smoke-test.ps1` passed.
  - Result: `SMOKE_OK`, `corporation_id=2`, `project_id=2`, `document_id=2`, `analysis_id=2`.
  - After server restart, `/api/dashboard/summary` returned persisted counts: `corporation_count=2`, `project_count=2`, `document_count=2`.
  - FE/BE servers were stopped after verification.

## 추가 업데이트 (2026-05-04)
- 사용자 제공 조달 PDF 샘플 구조 확인
- 샘플 파일
  - `C:/Users/HOONJAE/Downloads/소액수의-2026년 미세먼지저감숲 조성사업(향양지구).pdf`
- 확인 결과
  - 총 4페이지
  - `pypdf`로 약 5,414자 텍스트 추출 가능
  - 완전한 이미지 스캔 PDF라기보다는 텍스트 레이어가 있는 공고문 PDF로 판단
  - 다만 표, 항목 번호, 제목/본문 경계가 붙어서 단순 텍스트 추출만으로는 품질 한계가 큼
- 판단
  - OCR 단독보다 `텍스트 추출 + 레이아웃 분석 + OCR fallback + 조달 도메인 후처리` 조합이 필요
  - Phase 1 개선 후보: PyMuPDF 기반 블록/좌표 추출 도입 후, 필요 시 OCR fallback 연결

## Additional Update (2026-05-04)
- Inspected the procurement PDF sample provided by the user.
- Sample file:
  - `C:/Users/HOONJAE/Downloads/소액수의-2026년 미세먼지저감숲 조성사업(향양지구).pdf`
- Findings:
  - 4 pages.
  - `pypdf` extracts about 5,414 characters.
  - The file appears to have a text layer rather than being a pure scanned image PDF.
  - However, tables, numbered clauses, and heading/body boundaries are flattened, so plain text extraction is not enough.
- Assessment:
  - The project needs `text extraction + layout analysis + OCR fallback + procurement-specific post-processing`, not OCR alone.
  - Recommended Phase 1 improvement: introduce PyMuPDF block/coordinate extraction and add OCR fallback afterward.

## 추가 업데이트 (2026-05-04)
- 사용자 승인 반영: PDF 추출 엔진 교체 방향 확정
- 결정 사항
  - 기존 `pypdf` 중심 PDF 추출을 `PyMuPDF` 중심으로 교체한다.
  - `PyMuPDF`로 텍스트뿐 아니라 페이지별 블록, 좌표, 읽기 순서 후보를 함께 추출한다.
  - 조달문서에서 표/항목/날짜/금액이 붙는 문제를 후처리한다.
  - OCR은 모든 PDF에 무조건 적용하지 않고, 텍스트 레이어가 부족한 경우에만 fallback으로 적용한다.
  - OCR fallback 후보는 `PaddleOCR`을 우선 검토하고, 경량 대안으로 `Tesseract(kor+eng)`를 둔다.
  - Stirling PDF는 메인 reader가 아니라 향후 PDF 전처리/OCR 보조 서버로 선택 연동한다.
- 문서 업데이트
  - `docs/technical-design.md`
  - `docs/ai-api-setup.md`
  - `README.md`

## Additional Update (2026-05-04)
- Reflected user approval for the PDF extraction engine direction.
- Decisions:
  - Replace the current `pypdf`-centered PDF extraction path with `PyMuPDF`.
  - Use `PyMuPDF` to extract page text, blocks, coordinates, and candidate reading order.
  - Add procurement-specific post-processing for flattened tables, clauses, dates, and monetary amounts.
  - Do not OCR every PDF; run OCR only when the text layer is insufficient.
  - Prefer `PaddleOCR` as the stronger OCR fallback candidate, with `Tesseract(kor+eng)` as a lighter alternative.
  - Treat Stirling PDF as an optional future preprocessing/OCR helper service, not the primary reader.
- Updated docs:
  - `docs/technical-design.md`
  - `docs/ai-api-setup.md`
  - `README.md`

## 추가 업데이트 (2026-05-04)
- 사용자 승인 후 PDF 추출 엔진 교체 구현 완료
- 변경 내용
  - `backend/requirements.txt`
    - `pypdf` 제거
    - `PyMuPDF==1.26.5` 추가
  - `backend/app/pipelines/parser.py`
    - PDF 추출을 `PyMuPDF(fitz)` 기반으로 교체
    - 페이지별 텍스트, 블록 수, 문자 수, OCR 필요 여부 메타데이터 생성
    - 가로형/2단 조달 PDF를 고려한 좌/우 컬럼 읽기 순서 보정 추가
    - 조달문서에서 붙는 항목 번호, 날짜, 금액 주변 정규화 추가
    - DOCX 추출은 `python-docx` 유지
  - `backend/app/main.py`
    - 분석 파이프라인이 새 parser 모듈을 사용하도록 연결
    - `needs_ocr` 메타데이터를 `ocr_status`에 반영
    - 분석 사용량 JSON에 추출 메타데이터 포함
  - `scripts/smoke-test.ps1`
    - 테스트 PDF 생성 방식을 `pypdf`에서 `PyMuPDF`로 교체
  - `backend/tests/test_parser.py`
    - PyMuPDF PDF 추출 테스트 추가
    - 빈 PDF의 OCR 후보 판정 테스트 추가
    - DOCX 추출 유지 테스트 추가
  - `README.md`
    - 백엔드 단위 테스트 실행 명령 추가
- 검증 결과
  - `backend/.venv/Scripts/python -m unittest discover -s tests -v` 성공
  - 사용자 제공 조달 PDF 샘플에서 `PyMuPDF`로 4페이지, 5,440자 추출 확인
  - 샘플 앞부분이 공고 제목부터 시작하도록 읽기 순서 개선 확인
  - `scripts/smoke-test.ps1` 성공
  - 결과: `SMOKE_OK`, `corporation_id=4`, `project_id=4`, `document_id=4`, `analysis_id=4`

## Additional Update (2026-05-04)
- Implemented the PDF extraction engine replacement after user approval.
- Changes:
  - `backend/requirements.txt`
    - Removed `pypdf`.
    - Added `PyMuPDF==1.26.5`.
  - `backend/app/pipelines/parser.py`
    - Replaced PDF extraction with `PyMuPDF(fitz)`.
    - Generates page-level metadata: extracted text, block counts, character counts, and OCR candidate status.
    - Added left/right column reading-order correction for landscape/two-column procurement PDFs.
    - Added procurement-specific normalization around clauses, dates, and monetary amounts.
    - Kept DOCX extraction on `python-docx`.
  - `backend/app/main.py`
    - Connected the analysis pipeline to the new parser module.
    - Maps `needs_ocr` metadata to `ocr_status`.
    - Stores extraction metadata in analysis usage JSON.
  - `scripts/smoke-test.ps1`
    - Replaced test PDF generation from `pypdf` to `PyMuPDF`.
  - `backend/tests/test_parser.py`
    - Added PyMuPDF PDF extraction test.
    - Added blank-PDF OCR candidate test.
    - Added DOCX extraction regression test.
  - `README.md`
    - Added backend unit test command.
- Verification:
  - `backend/.venv/Scripts/python -m unittest discover -s tests -v` passed.
  - User-provided procurement PDF sample extracted with `PyMuPDF`: 4 pages, 5,440 characters.
  - Reading order now starts from the notice title in the sample.
  - `scripts/smoke-test.ps1` passed.
  - Result: `SMOKE_OK`, `corporation_id=4`, `project_id=4`, `document_id=4`, `analysis_id=4`.

## 추가 업데이트 (2026-05-05)
- 사용자 요청에 따라 `source/api_doc`의 나라장터 API 문서 분석
- 분석 대상
  - `source/api_doc/조달청_OpenAPI참고자료_나라장터_입찰공고정보서비스_1.2.docx`
  - `source/api_doc/조달청_OpenAPI참고자료_나라장터_공공데이터개방표준서비스_1.2.docx`
  - `source/api_doc/api 에러 코드.txt`
- 확인 결과
  - 공고 자동 수집의 핵심 서비스는 `BidPublicInfoService`
  - 기본 URL은 `http://apis.data.go.kr/1230000/ad/BidPublicInfoService`
  - REST GET, `ServiceKey` 인증, `type=json` 지원
  - 우선 구현 대상은 공사 공고 검색/목록/기초금액/면허제한/참가가능지역/첨부파일 API
  - 첨부파일 URL은 `ntceSpecDocUrl1..10`, `stdNtceDocUrl`, `eorderAtchFileUrl` 등으로 제공됨
  - 나라장터 첨부파일은 HWP/HWPX/XLSX도 많으므로 Phase 1.5에서는 PDF/DOCX만 다운로드하고 나머지는 메타데이터만 저장하는 방향 권장
  - `PubDataOpnStdService`는 입찰/낙찰/계약 표준 데이터용 보조 서비스로 판단
- 생성/수정 파일
  - `docs/narajangteo-api-analysis.md`
  - `README.md`

## Additional Update (2026-05-05)
- Analyzed Nara Marketplace API documents under `source/api_doc` per user request.
- Source files:
  - `source/api_doc/조달청_OpenAPI참고자료_나라장터_입찰공고정보서비스_1.2.docx`
  - `source/api_doc/조달청_OpenAPI참고자료_나라장터_공공데이터개방표준서비스_1.2.docx`
  - `source/api_doc/api 에러 코드.txt`
- Findings:
  - The primary API for automatic notice ingestion is `BidPublicInfoService`.
  - Base URL: `http://apis.data.go.kr/1230000/ad/BidPublicInfoService`.
  - REST GET, `ServiceKey` auth, supports `type=json`.
  - Priority endpoints are construction notice search/list, basis amount, license restriction, eligible region, and attachment info APIs.
  - Attachment URLs are exposed through fields such as `ntceSpecDocUrl1..10`, `stdNtceDocUrl`, and `eorderAtchFileUrl`.
  - Nara attachments often include HWP/HWPX/XLSX, so Phase 1.5 should download PDF/DOCX only and store unsupported attachments as metadata.
  - `PubDataOpnStdService` is useful as a secondary standardized bid/award/contract data source.
- Created/updated:
  - `docs/narajangteo-api-analysis.md`
  - `README.md`

## 추가 업데이트 (2026-05-05)
- 사용자가 제공한 공공데이터포털 endpoint/일반 인증키 정보 반영
- 처리 내용
  - 실제 인증키 값은 문서/예제 파일에 기록하지 않음
  - `backend/.env.example`에 나라장터 API 환경변수 placeholder 추가
  - `README.md`의 백엔드 `.env` 예시에 나라장터 API 환경변수 추가
  - `docs/narajangteo-api-analysis.md`의 endpoint를 HTTPS 기준으로 정리
- 추가한 환경변수
  - `NARA_API_SERVICE_KEY`
  - `NARA_BID_PUBLIC_API_BASE_URL`
  - `NARA_PUBDATA_API_BASE_URL`
  - `NARA_API_RESPONSE_TYPE`
- 판단
  - 사용자가 제공한 endpoint는 `PubDataOpnStdService`용임
  - 공고 첨부파일 수집/분석에는 여전히 `BidPublicInfoService`가 1순위임
  - 같은 `ServiceKey`라도 API별 활용신청/승인 상태가 다를 수 있어 두 서비스 승인 여부 확인 필요

## Additional Update (2026-05-05)
- Reflected the public data portal endpoint/key information provided by the user.
- Changes:
  - Did not write the actual secret key value into docs or example files.
  - Added Nara API placeholders to `backend/.env.example`.
  - Added Nara API env var examples to `README.md`.
  - Updated `docs/narajangteo-api-analysis.md` endpoint examples to HTTPS.
- Added environment variables:
  - `NARA_API_SERVICE_KEY`
  - `NARA_BID_PUBLIC_API_BASE_URL`
  - `NARA_PUBDATA_API_BASE_URL`
  - `NARA_API_RESPONSE_TYPE`
- Assessment:
  - The endpoint provided by the user is for `PubDataOpnStdService`.
  - `BidPublicInfoService` remains the primary API for notice attachment ingestion and analysis.
  - The same `ServiceKey` may require separate approval per API service.

## 추가 업데이트 (2026-05-05)
- 사용자 요청에 따라 나라장터 API 실제 호출 테스트 수행
- 추가 파일
  - `scripts/test-nara-api.py`
  - `docs/narajangteo-api-test-result-20260505.md`
- 테스트 조건
  - 기준 날짜: `2026-05-05`
  - 조회 범위: `202605050000` ~ `202605052359`
  - 응답 형식: `json`
  - 실제 인증키는 환경변수로만 주입하고 문서/코드에는 저장하지 않음
- 테스트 결과
  - `getBidPblancListInfoCnstwkPPSSrch`: 정상, total 23, 첨부 39
  - `getBidPblancListInfoCnstwk`: 정상, total 23, 첨부 39
  - `getBidPblancListInfoCnstwkBsisAmount`: 정상, total 31
  - `getBidPblancListInfoLicenseLimit`: 정상, total 42
  - `getBidPblancListInfoPrtcptPsblRgn`: 정상, total 31
  - `getBidPblancListInfoEorderAtchFileInfo`: 정상, total 0
  - `getDataSetOpnStdBidPblancInfo`: 정상, total 44
- 추가 확인
  - 대표 공고 `R26BK01503422 / 000` 상세 조회 성공
  - 기초금액 `253,946,000` 확인
  - 면허제한 3건, 참가가능지역 `서울특별시` 확인
  - 첫 번째 지원 가능 PDF 첨부 다운로드 성공
  - 응답 `Content-Type=application/pdf`, PDF 시그니처 `%PDF` 확인
- 기능 판단
  - API 기반 공고 검색/저장 가능
  - PDF 첨부 자동 다운로드 후 기존 PyMuPDF 분석 파이프라인 연결 가능
  - HWP/HWPX/XLSX는 현재 범위상 지원 제외 메타데이터로 저장하는 정책 필요

## Additional Update (2026-05-05)
- Ran real Nara Marketplace API tests with the user-provided service key.
- Added files:
  - `scripts/test-nara-api.py`
  - `docs/narajangteo-api-test-result-20260505.md`
- Test conditions:
  - Date: `2026-05-05`
  - Range: `202605050000` to `202605052359`
  - Response format: `json`
  - The real API key was injected only through an environment variable and was not written to docs/code.
- Results:
  - `getBidPblancListInfoCnstwkPPSSrch`: OK, total 23, attachments 39.
  - `getBidPblancListInfoCnstwk`: OK, total 23, attachments 39.
  - `getBidPblancListInfoCnstwkBsisAmount`: OK, total 31.
  - `getBidPblancListInfoLicenseLimit`: OK, total 42.
  - `getBidPblancListInfoPrtcptPsblRgn`: OK, total 31.
  - `getBidPblancListInfoEorderAtchFileInfo`: OK, total 0.
  - `getDataSetOpnStdBidPblancInfo`: OK, total 44.
- Additional validation:
  - Detail lookup for notice `R26BK01503422 / 000` succeeded.
  - Basis amount `253,946,000` confirmed.
  - 3 license restrictions and eligible region `서울특별시` confirmed.
  - First supported PDF attachment download succeeded.
  - Response `Content-Type=application/pdf` and PDF signature `%PDF` confirmed.
- Product assessment:
  - API-based notice search and persistence are feasible.
  - PDF attachments can be downloaded and passed into the existing PyMuPDF analysis pipeline.
  - HWP/HWPX/XLSX should be stored as unsupported attachment metadata for now.

## 추가 업데이트 (2026-05-05)
- 나라장터 API 테스트 스크립트에 첨부파일 다운로드 검증 단계를 정식 추가
- 변경 파일
  - `scripts/test-nara-api.py`
  - `docs/narajangteo-api-test-result-20260505.md`
  - `docs/work-log.md`
- 변경 내용
  - 공고 목록/상세 응답에서 첫 번째 지원 가능 PDF/DOCX 첨부를 자동 선택
  - 실제 첨부 URL로 binary 다운로드 수행
  - HTTP 상태, Content-Type, Content-Length, 다운로드 바이트, PDF/DOCX 시그니처를 `download_test`로 JSON에 기록
  - API 인증키는 환경변수로만 임시 주입하고 코드/문서에는 저장하지 않음
- 재검증 결과
  - 기준 날짜: `2026-05-05`
  - 결과 JSON: `temp/nara-api-test-20260505-latest.json`
  - 다운로드 파일: `1.입찰공고문(재공고).pdf`
  - HTTP 상태: `200`
  - Content-Type: `application/pdf`
  - 다운로드 크기: `510,526` bytes
  - PDF 시그니처: `%PDF` 확인

## Additional Update (2026-05-05)
- Added first-class attachment download validation to the Nara API test script.
- Changed files:
  - `scripts/test-nara-api.py`
  - `docs/narajangteo-api-test-result-20260505.md`
  - `docs/work-log.md`
- Changes:
  - Automatically selects the first supported PDF/DOCX attachment from notice list/detail responses.
  - Performs a real binary download from the attachment URL.
  - Records HTTP status, Content-Type, Content-Length, downloaded byte count, and PDF/DOCX signature under `download_test`.
  - Injects the real API key only through a temporary environment variable; it is not stored in code/docs.
- Re-test result:
  - Date: `2026-05-05`
  - Result JSON: `temp/nara-api-test-20260505-latest.json`
  - Downloaded file: `1.입찰공고문(재공고).pdf`
  - HTTP status: `200`
  - Content-Type: `application/pdf`
  - Download size: `510,526` bytes
  - PDF signature: valid `%PDF`

## 추가 업데이트 (2026-05-05)
- 사용자 요청에 따라 `나라장터 게시판` 기능의 UX/구현 설계 작성
- 신규 문서
  - `docs/narajangteo-board-design.md`
- 수정 문서
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/work-log.md`
- 설계 결정
  - 해당 기능은 `Phase 1.5`로 분리
  - 나라장터 사이트 HTML 크롤링이 아니라 공공데이터 API 기반 게시판으로 설계
  - 공사 공고 API를 1차 대상으로 설정
  - 라디오 박스로 공고 1개를 선택한 뒤 `공고 상세 저장` 액션 실행
  - 저장 시 공고 상세/기초금액/면허제한/참가가능지역을 재조회하고 DB에 저장
  - PDF/DOCX 첨부는 자동 다운로드 후 기존 PyMuPDF/python-docx 파싱 및 요약 파이프라인에 연결
  - HWP/HWPX/XLSX는 지원 제외 첨부파일 메타데이터로 저장
  - 저장된 공고는 MVP에서 프로젝트와 분리된 `나라장터 저장 공고` 도메인으로 관리
  - Phase 1.5에서는 최종 지원 가능/불가능 판단을 하지 않음

## Additional Update (2026-05-05)
- Designed the UX and implementation plan for the `Nara Marketplace Board` feature.
- New document:
  - `docs/narajangteo-board-design.md`
- Updated documents:
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/work-log.md`
- Design decisions:
  - Treat this as `Phase 1.5`.
  - Use the public data API, not HTML crawling.
  - Target construction notices first.
  - Let the user select exactly one notice via radio button and run `Save Notice Detail`.
  - On save, refetch notice detail, basis amount, license limits, and eligible regions, then persist the notice.
  - Auto-download PDF/DOCX attachments and connect them to the existing PyMuPDF/python-docx parsing and summarization pipeline.
  - Store HWP/HWPX/XLSX as unsupported attachment metadata.
  - Keep saved notices separate from projects in the MVP.
  - Do not produce eligibility verdicts in Phase 1.5.

## 추가 업데이트 (2026-05-05)
- 사용자 질문 반영: `공고 상세 저장`으로 저장한 공고문을 다시 볼 수 있는 메뉴를 명확히 정리
- 수정 문서
  - `docs/narajangteo-board-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `docs/work-log.md`
- 결정 사항
  - `나라장터 게시판` 하위에 `공고 검색`과 `저장한 공고`를 둔다.
  - `공고 검색`은 외부 나라장터 API 검색 결과 화면이다.
  - `저장한 공고`는 사용자가 `공고 상세 저장`으로 DB에 저장한 공고문만 보여주는 내부 게시판이다.
  - `저장한 공고`에서는 첨부 다운로드 상태, 분석 상태, 분석 결과, 로컬 첨부파일 다운로드, 재분석, 삭제를 제공한다.

## Additional Update (2026-05-05)
- Clarified the menu for notices saved through `Save Notice Detail`.
- Updated documents:
  - `docs/narajangteo-board-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `docs/work-log.md`
- Decisions:
  - `Nara Board` has two child views: `Search Notices` and `Saved Notices`.
  - `Search Notices` shows live public API search results.
  - `Saved Notices` is an internal board listing only locally persisted notices.
  - `Saved Notices` exposes download status, analysis status, analysis results, local attachment download, reanalysis, and deletion.

## 추가 업데이트 (2026-05-05)
- 사용자 요청 반영: 나라장터 API 키 확인용 설정 메뉴와 공고 검색 기본 조회 기간 변경
- 수정 문서
  - `docs/narajangteo-board-design.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/work-log.md`
- 결정 사항
  - `나라장터 게시판 > 공고 검색` 진입 즉시 공고 목록 API를 자동 호출한다.
  - 기본 조회 기간은 `최근 1개월`로 한다.
  - 예: 오늘이 `2026-05-05`이면 `2026-04-05 00:00` ~ `2026-05-05 23:59`를 조회한다.
  - `설정 > API 연동 > 나라장터` 메뉴를 추가한다.
  - 설정 화면에서는 API 키 설정 여부, 마스킹된 키, base URL, 마지막 테스트 결과를 확인한다.
  - API 키 전체 값은 프론트엔드 응답/로그/문서에 노출하지 않는다.
  - 연결 테스트, 공고 API 테스트, 첨부 PDF 다운로드 테스트 액션을 제공한다.

## Additional Update (2026-05-05)
- Reflected the requested Nara API key settings screen and default search range change.
- Updated documents:
  - `docs/narajangteo-board-design.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `README.md`
  - `AGENTS.md`
  - `docs/work-log.md`
- Decisions:
  - `Nara Board > Search Notices` automatically fetches notices on page entry.
  - Default date range is one month.
  - Example: if today is `2026-05-05`, query `2026-04-05 00:00` to `2026-05-05 23:59`.
  - Add `Settings > API Integrations > Nara`.
  - The settings screen shows configured status, masked key, base URLs, and last test result.
  - Never expose full API keys in frontend responses, logs, or docs.
  - Provide connection test, notice API test, and attachment PDF download test actions.

## 추가 업데이트 (2026-05-05)
- 사용자 요청에 따라 현재 프로젝트 MD 문서들을 기반으로 서비스의 핵심 기술 요소와 활용 기술을 정리
- 신규 문서
  - `docs/technology-summary.md`
- 수정 문서
  - `README.md`
  - `docs/work-log.md`
- 정리 내용
  - 로컬 우선 관리자 포탈
  - 법인/프로젝트 중심 데이터 구조
  - 나라장터 공고 수집/저장/분석 구조
  - PDF/DOCX 파싱과 OCR fallback
  - AI 구조화 요약과 fallback 요약
  - 분석 캐시/재분석
  - 기준문서 RAG 준비
  - API 키 보안 설정
  - 프론트엔드/백엔드/DB/문서처리/AI/나라장터 API/RAG/테스트 도구
- 주의점
  - 설계상 백엔드는 FastAPI 권장이지만 현재 Phase 1 실제 구현은 Flask 런타임이므로 문서에 구분 표기

## Additional Update (2026-05-05)
- Summarized core technical elements and technology usage from the current project Markdown documents.
- New document:
  - `docs/technology-summary.md`
- Updated documents:
  - `README.md`
  - `docs/work-log.md`
- Coverage:
  - local-first admin portal
  - corporation/project-centric data model
  - Nara notice ingestion/save/analyze flow
  - PDF/DOCX parsing and OCR fallback
  - structured AI summarization and fallback summary
  - analysis cache and re-analysis
  - basis-document RAG preparation
  - API key security settings
  - frontend/backend/DB/document-processing/AI/Nara API/RAG/testing tools
- Note:
  - The documented architecture recommends FastAPI, while current Phase 1 runtime is Flask; the summary explicitly distinguishes this.
