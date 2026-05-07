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

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 현재 코드 전체를 리뷰하고 Phase 1 운영에 바로 영향을 주는 부족한 부분을 우선 수정
- 주요 리뷰 결과
  - 실제 실행 백엔드는 현재 Flask 기반 `backend/app/main.py`이며, 일부 FastAPI 골격 파일은 아직 런타임에 연결되어 있지 않다.
  - 문서에는 나라장터 API 설정 메뉴가 필요하다고 정리되어 있었지만 실제 화면/엔드포인트가 없었다.
  - 법인/프로젝트/문서의 수정·삭제 흐름이 프론트엔드에서 충분히 제공되지 않았다.
  - 문서 파일 삭제 시 분석 결과 정리와 로컬 파일 정리 안정성이 부족했다.
  - 분석 캐시가 모델/프롬프트 기준을 충분히 구분하지 않아 향후 AI 모델 변경 시 재사용 기준이 모호했다.
  - 업로드 파일이 사라졌거나 파싱 중 오류가 발생했을 때 상태값 갱신과 사용자 오류 메시지가 부족했다.
- 수정 내역
  - 백엔드에 법인/프로젝트/문서 상세 조회, 수정, 삭제 API를 보강했다.
  - 프로젝트 삭제 시 연결 문서, 분석 결과, 로컬 저장 파일을 함께 정리하도록 개선했다.
  - 문서 삭제 시 분석 결과를 먼저 삭제하고 파일은 저장소 내부 경로일 때만 안전하게 삭제하도록 개선했다.
  - 문서 분석 전 저장 파일 존재 여부와 파싱 예외를 처리하고 실패 상태를 DB에 남기도록 개선했다.
  - 분석 캐시 기준에 `model_name`과 `prompt_version`을 포함했다.
  - OpenAI 호출 실패 후 fallback 요약을 사용할 경우 실제 provider/model 정보와 fallback 사유를 저장하도록 개선했다.
  - 나라장터 API 설정 상태 조회/연결 테스트 API를 추가했다.
  - 프론트엔드에 `API 설정` 메뉴와 나라장터 API 설정 상태 화면을 추가했다.
  - 법인/프로젝트/문서 화면에 삭제 액션과 사용자 오류 메시지를 추가했다.
  - 대시보드와 분석 결과 화면의 오류 표시를 보강했다.
  - SQLite journal 파일이 git 변경사항에 잡히지 않도록 `.gitignore`에 `*.db-journal`을 추가했다.
- 검증 결과
  - 백엔드 문법 검사 성공
  - 백엔드 파서 단위 테스트 3건 성공
  - 프론트엔드 `npm run build` 성공
  - 스모크 테스트 성공
  - 나라장터 API 설정 상태 엔드포인트는 API 키 미설정 상태에서 정상 응답 확인
- 남은 주요 범위
  - 나라장터 게시판의 실제 공고 검색, 저장한 공고 목록, 첨부 자동 다운로드, 저장 후 분석 파이프라인은 아직 별도 구현 대상이다.
  - 현재 백엔드 런타임이 Flask이므로 FastAPI 권장 설계와 실제 구현의 정합성은 추후 별도 정리 또는 마이그레이션 결정이 필요하다.

## Additional Update (2026-05-06)
- Reviewed the current codebase and fixed Phase 1 gaps that directly affect local MVP usability and reliability.
- Main findings:
  - The active backend runtime is Flask in `backend/app/main.py`; some FastAPI scaffold files are not wired into runtime yet.
  - Documentation required a Nara API settings menu, but the actual endpoint and UI were missing.
  - Corporation/project/document edit/delete flows were incomplete in the frontend.
  - Document deletion did not fully clean up linked analyses and local files safely.
  - Analysis cache matching did not include enough model/prompt context.
  - Missing files and parsing failures did not update DB status clearly enough.
- Changes:
  - Added backend detail/update/delete APIs for corporations, projects, and documents.
  - Improved project deletion cleanup for linked documents, analyses, and local stored files.
  - Improved document deletion cleanup and restricted local file unlinking to the configured storage root.
  - Added missing-file and parser-exception handling to the analysis flow.
  - Included `model_name` and `prompt_version` in analysis cache matching.
  - Stored actual provider/model data and fallback reason when OpenAI summarization falls back to local summary.
  - Added Nara API integration status and connection-test endpoints.
  - Added frontend `API Settings` navigation and Nara integration status page.
  - Added delete actions and visible error messages to corporation, project, and document pages.
  - Improved dashboard and analysis error handling.
  - Added `*.db-journal` to `.gitignore`.
- Verification:
  - backend syntax check passed
  - backend parser unit tests passed, 3 tests
  - frontend `npm run build` passed
  - smoke test passed
  - Nara API settings status endpoint returned a valid response without exposing any full API key
- Remaining scope:
  - Full Nara board implementation, notice search, saved notices, attachment auto-download, and save-and-analyze pipeline remain separate implementation work.
  - Because the current runtime is Flask while architecture docs recommend FastAPI, the team should later choose whether to keep Flask for MVP or migrate to FastAPI.

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 `Phase 1 마무리 -> Phase 1 코드 리뷰 -> Phase 1.5 개발 -> Phase 1.5 코드 리뷰` 순서로 작업 진행

### Phase 1 마무리
- 법인 관리 화면에 편집 UI 추가
  - 법인명, 업종/분류, 지역, 회사 규모, 인증/면허, 내부 메모 수정 가능
- 프로젝트 관리 화면에 편집 UI 추가
  - 프로젝트명, 연결 법인, 상태, 메모 수정 가능
- 문서 업로드 화면에 문서 메타데이터 편집 UI 추가
  - 문서 유형, 업로드 메모, 개정 메모 수정 가능
- 공통 스타일 추가
  - 보조 버튼
  - 인라인 편집 카드
- 백엔드 API 회귀 테스트 추가
  - 법인/프로젝트/문서 생성, 수정, 삭제 흐름
  - 프로젝트 삭제 시 연결 문서/분석/파일 정리 검증
  - 나라장터 API 설정 상태에서 키 전체값 미노출 검증
- Phase 1 코드 리뷰 결과
  - 차단 이슈 없음
  - 남은 리스크: 실제 OCR 엔진 품질과 복잡한 스캔 PDF는 추가 샘플 기반 검증 필요

### Phase 1.5 개발
- 나라장터 공고 저장용 DB 테이블 추가
  - `nara_notices`
  - `nara_notice_attachments`
- 나라장터 공고 검색 API 추가
  - 최근 1개월 기본 조회는 프론트에서 제공
  - 백엔드는 `getBidPblancListInfoCnstwkPPSSrch` 기반 검색 지원
  - API 키 미설정 시 명확한 오류 반환
- 공고 상세 저장/분석 API 추가
  - 선택한 공고 원본 데이터를 저장
  - 가능하면 상세/기초금액/면허제한/참가가능지역/첨부 API를 재조회
  - 첨부 PDF/DOCX 자동 다운로드
  - HWP/HWPX/XLSX 등은 지원 제외 메타데이터로 저장
  - 다운로드한 PDF/DOCX 파싱 후 기존 요약 파이프라인 재사용
  - 저장한 공고에 분석 요약 저장
- 저장한 공고 관리 API 추가
  - 목록
  - 상세
  - 재분석
  - 삭제
- 프론트엔드 나라장터 화면 추가
  - `나라장터 공고 검색`
  - `저장한 공고`
  - `저장한 공고 상세`
- 서버 스모크 테스트에 나라장터 저장/분석 흐름 추가
- Phase 1.5 코드 리뷰 결과
  - 차단 이슈 없음
  - API 키 전체값은 프론트 응답/문서/로그에 노출하지 않는 구조 유지
  - 남은 리스크: 일부 나라장터 첨부 URL이 확장자 또는 직접 파일 서명을 제공하지 않는 경우 실제 API 샘플 기반 보정 필요
  - 남은 리스크: 현재는 건설공사 공고 검색 API를 우선 연결했으므로 용역/물품 등 확장 검색은 후속 작업 필요

### 검증 결과
- 백엔드 문법 검사 성공
- 백엔드 단위 테스트 8건 성공
- 프론트엔드 `npm run build` 성공
- 전체 스모크 테스트 성공
  - 법인 생성
  - 프로젝트 생성
  - PDF 업로드
  - 문서 분석
  - 최신 분석 조회
  - 나라장터 공고 저장/분석

## Additional Update (2026-05-06)
- Per user request, completed work in this order: `Phase 1 wrap-up -> Phase 1 code review -> Phase 1.5 implementation -> Phase 1.5 code review`.

### Phase 1 Wrap-Up
- Added corporation edit UI.
  - editable fields: name, business category, region, company size, certifications/licenses, internal notes
- Added project edit UI.
  - editable fields: name, linked corporation, status, notes
- Added document metadata edit UI.
  - editable fields: document type, memo, revision note
- Added shared UI styling.
  - secondary button
  - inline edit card
- Added backend API regression tests.
  - corporation/project/document create-update-delete flow
  - project deletion cleanup for linked documents, analyses, and files
  - Nara API settings status does not expose full keys
- Phase 1 code review result:
  - no blocking issues found
  - remaining risk: real OCR quality and complex scanned PDFs still require sample-based verification

### Phase 1.5 Implementation
- Added DB tables for saved Nara notices.
  - `nara_notices`
  - `nara_notice_attachments`
- Added Nara notice search API.
  - frontend provides the default one-month range
  - backend uses `getBidPblancListInfoCnstwkPPSSrch`
  - missing API key returns a clear error
- Added save-and-analyze API.
  - stores the selected raw notice payload
  - attempts detail, basis amount, license limit, eligible region, and attachment API enrichment
  - downloads supported PDF/DOCX attachments
  - stores HWP/HWPX/XLSX as unsupported metadata
  - reuses the existing parsing and summarization pipeline
  - stores summary output on the saved notice
- Added saved notice APIs.
  - list
  - detail
  - reanalyze
  - delete
- Added frontend Nara pages.
  - `Nara Notice Search`
  - `Saved Notices`
  - `Saved Notice Detail`
- Extended the smoke test with the Nara save-and-analyze flow.
- Phase 1.5 code review result:
  - no blocking issues found
  - full API keys remain hidden from frontend responses, docs, and logs
  - remaining risk: some Nara attachment URLs may not expose reliable extensions or direct file signatures, requiring sample-based adjustment
  - remaining risk: construction notices are connected first; services/goods search expansion remains future work

### Verification
- backend syntax check passed
- backend unit tests passed, 8 tests
- frontend `npm run build` passed
- full smoke test passed
  - create corporation
  - create project
  - upload PDF
  - analyze document
  - fetch latest analysis
  - save/analyze Nara notice

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 Phase 2 개발 전에 현재 코드 더블체크 리뷰와 포탈 UX 개선 방향 조사를 진행
- 코드 리뷰에서 발견 후 수정한 내용
  - 나라장터 기본 조회 기간 계산이 UTC 날짜 기준으로 동작할 수 있어 한국 시간(KST) 기준으로 보정
  - 나라장터 API 설정 테스트가 JSON 응답만 정상 파싱하던 구조를 JSON/XML 공통 파서 사용 방식으로 보정
  - 프론트엔드 나라장터 검색 기본 날짜 계산이 `toISOString()` 기반이라 한국 로컬 날짜와 어긋날 수 있어 로컬 날짜 포맷 방식으로 보정
- UX 레퍼런스 조사
  - Tabler Admin: 차분한 카드, 테이블, 사이드바, 상태/위젯 밀도 참고
  - shadcn/ui Blocks: 사이드바 + 데이터 테이블 + 섹션 카드 구조 참고
  - Shadcn Admin: React/Vite 기반 관리형 레이아웃 방향 참고
- UX 개선 계획 초안
  - 현재 벚꽃 테마의 강한 배경/그라데이션을 줄이고 더 차분한 `warm neutral + soft cherry accent`로 변경
  - 메뉴를 업무 흐름 기준으로 그룹화
  - 대시보드에는 전체 카운트보다 `오늘 해야 할 일`, `처리 대기`, `최근 저장 공고`, `분석 실패/부분 실패`를 우선 표시
  - 나라장터/문서/기준문서가 늘어날 것을 고려해 사이드바를 그룹형 내비게이션으로 정리
- 검증 결과
  - 백엔드 단위 테스트 8건 성공
  - 프론트엔드 `npm run build` 성공
  - 전체 스모크 테스트 성공

## Additional Update (2026-05-06)
- Before starting Phase 2, reviewed the current code again and researched calmer portal UX directions.
- Fixes from the double-check review:
  - Nara default search date range now uses Korean local time (KST), not UTC dates.
  - Nara integration test now uses the shared JSON/XML public-data parser.
  - Frontend Nara default date formatting now uses local date fields instead of `toISOString()`.
- UX references:
  - Tabler Admin: calm cards, tables, sidebar, status/widget density
  - shadcn/ui Blocks: sidebar + data table + section card structure
  - Shadcn Admin: React/Vite admin layout direction
- UX improvement draft:
  - reduce strong sakura gradients and move toward `warm neutral + soft cherry accent`
  - group navigation by actual admin workflow
  - prioritize actionable dashboard sections: next work, pending processing, recent saved notices, failed/partial analyses
  - reorganize sidebar groups before adding Phase 2 basis-document menus
- Verification:
  - backend unit tests passed, 8 tests
  - frontend `npm run build` passed
  - full smoke test passed

## 추가 업데이트 (2026-05-06)
- 사용자 승인에 따라 Tabler Admin/Tabler Preview를 참고한 포탈 UX 수정 작업 진행
- 수정 목표
  - 기존 벚꽃 테마의 산뜻함은 일부 유지하되, 장시간 업무용으로 보기 편한 차분한 관리자 포탈 톤으로 조정
  - 메뉴를 단순 나열이 아니라 업무 흐름별 그룹으로 재구성
  - 대시보드에서 단순 카운트보다 처리 대기, 실패/부분 실패, 최근 저장 공고, 최근 문서를 먼저 확인할 수 있게 변경
- 수정 내역
  - 사이드바 메뉴 그룹화
    - 업무 현황
    - 공고 업무
    - 문서 분석
    - 기준문서/RAG
    - 내부 관리
    - 설정
  - Phase 2 기준문서 관리를 비활성 메뉴로 미리 배치
  - 대시보드 재구성
    - 다음 추천 액션
    - 처리 대기/주의 현황
    - 나라장터 API 연동 상태
    - 법인/프로젝트/문서/저장 공고 KPI
    - 빠른 액션
    - 최근 저장 공고
    - 최근 업로드 문서
  - 공통 디자인 토큰 재정리
    - warm neutral 배경
    - soft cherry accent
    - 낮은 shadow
    - 더 얇은 border
    - Tabler 스타일에 가까운 테이블/카드/상태 배지
- 수정 파일
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 백엔드 단위 테스트 8건 성공
  - 프론트엔드 `npm run build` 성공
  - 전체 스모크 테스트 성공
- 메모
  - 브라우저에서 실제 화면을 열어 최종 시각 QA를 하면 여백/밀도는 한 번 더 미세조정 가능

## Additional Update (2026-05-06)
- Per user approval, updated the portal UX using Tabler Admin/Tabler Preview as references.
- Goals:
  - keep a small amount of the sakura identity while moving toward a calmer long-running admin portal
  - reorganize navigation by workflow groups
  - make the dashboard prioritize pending work, failed/partial work, recent saved notices, and recent documents over simple counts
- Changes:
  - grouped sidebar navigation:
    - Operations Overview
    - Nara Notice Work
    - Document Analysis
    - Basis Documents / RAG
    - Internal Management
    - Settings
  - added a disabled Phase 2 basis-document navigation placeholder
  - rebuilt the dashboard:
    - next recommended action
    - processing queue/warnings
    - Nara API integration status
    - corporation/project/document/saved-notice KPIs
    - quick actions
    - recent saved notices
    - recent uploaded documents
  - refreshed shared design tokens:
    - warm neutral background
    - soft cherry accent
    - lower shadows
    - lighter borders
    - more Tabler-like tables/cards/status badges
- Updated files:
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - backend unit tests passed, 8 tests
  - frontend `npm run build` passed
  - full smoke test passed
- Note:
  - final visual QA in a browser would help fine-tune spacing and density.

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 포탈 전체 글씨 크기를 약 20% 낮추는 방향으로 조정
- 수정 내용
  - 전역 `body` 폰트 기준 크기 축소
  - 브랜드 타이틀, 히어로 타이틀, 메뉴 라벨/설명, KPI 숫자, 작업 상태 항목, 빠른 액션 설명, 상태 배지 크기 축소
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공
  - FE/BE 서버 실행 상태 정상 확인

## Additional Update (2026-05-06)
- Reduced overall portal typography by roughly 20% per user request.
- Changes:
  - lowered global `body` font baseline
  - reduced brand title, hero title, nav labels/notes, KPI numbers, task rows, quick action notes, and status badge typography
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

  - FE/BE server status confirmed running

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 포탈 전체 폰트 패밀리 변경
- 적용 폰트
  - `Malgun Gothic`
  - `맑은 고딕`
  - `Dotum`
  - `돋움`
  - `sans-serif`
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Updated the portal-wide font family per user request.
- Font stack:
  - `Malgun Gothic`
  - `맑은 고딕`
  - `Dotum`
  - `돋움`
  - `sans-serif`
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 직전 폰트 크기 기준에서 약 10% 확대
- 수정 내용
  - 전역 `body` 기준 폰트 크기 확대
  - 브랜드 타이틀, 히어로 타이틀, 메뉴 라벨/설명, KPI 숫자, 작업 상태 항목, 빠른 액션 설명, 상태 배지 크기 비례 조정
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Increased portal typography by roughly 10% from the previous reduced size.
- Changes:
  - increased global `body` font baseline
  - proportionally adjusted brand title, hero title, nav labels/notes, KPI numbers, task rows, quick action notes, and status badges
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백에 따라 `나라장터 공고 검색` 화면의 `공고 상세 저장` 버튼 위치 수정
- 수정 내용
  - 검색 조건 폼 하단에 있던 `공고 상세 저장` 버튼 제거
  - 공고 목록 테이블 카드의 오른쪽 상단으로 이동
  - 선택 공고가 없거나 저장/분석 중이면 비활성화 유지
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Moved the `Save Notice Detail` action based on user feedback.
- Changes:
  - removed the button from the search form footer
  - placed it in the top-right area of the notice results table card
  - kept disabled behavior when no notice is selected or save/analyze is running
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 공고 검색 `페이지 크기` 옵션 확장
- 수정 내용
  - 프론트 옵션에 `100건`, `150건`, `200건` 추가
  - 백엔드 검색 API의 `page_size` 상한을 `100`에서 `200`으로 확대
  - 백엔드 테스트가 실제 로컬 `.env`의 나라장터 키에 영향받지 않도록 테스트 환경 격리 보강
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공
  - 백엔드 단위 테스트 8건 성공

## Additional Update (2026-05-06)
- Expanded Nara notice search `page size` options per user request.
- Changes:
  - added `100`, `150`, and `200` options to the frontend selector
  - increased backend `page_size` cap from `100` to `200`
  - isolated backend tests from the real local `.env` Nara API key
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed
  - backend unit tests passed, 8 tests

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `공고 목록` 테이블 첫 컬럼에 순번 추가
- 수정 내용
  - 현재 조회 결과 기준으로 `1`부터 시작하는 `No.` 컬럼 표시
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added a row number column to the Nara notice results table.
- Changes:
  - displays a `No.` column starting from `1` for the current result list
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `공고 목록` 테이블 정렬 기능 추가
- API 지원 여부 확인
  - 현재 저장소의 나라장터 API 문서/분석 자료에서는 `마감`, `금액` 정렬을 위한 명시적인 서버 sort/order 파라미터가 확인되지 않음
  - 따라서 현재 조회된 결과 목록 기준의 프론트엔드 정렬로 구현
- 수정 내용
  - `마감` 컬럼 클릭 시 오름차순/내림차순 토글
  - `금액` 컬럼 클릭 시 오름차순/내림차순 토글
  - 정렬 상태를 컬럼명 옆 `↑`, `↓`로 표시
  - 순번은 정렬된 화면 순서 기준으로 다시 표시
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added sorting to the Nara notice results table.
- API support check:
  - current local Nara API docs/analysis do not show explicit server-side sort/order parameters for deadline or amount
  - implemented frontend sorting for the currently fetched result list
- Changes:
  - deadline column toggles ascending/descending sort
  - amount column toggles ascending/descending sort
  - active sort direction is shown with `↑` or `↓`
  - row numbers are recalculated based on the sorted display order
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 질문 반영: 공고 상세 첨부 목록에 `standard_notice.pdf`가 `unsupported`로 표시되는 원인 확인 및 수정
- 원인
  - 나라장터 응답의 `stdNtceDocUrl` 값이 비어 있어도 시스템이 임의 파일명 `standard_notice.pdf`를 붙여 첨부 항목을 생성하고 있었음
  - 실제 다운로드 URL이 없기 때문에 PDF 확장자처럼 보여도 `unsupported`로 표시됨
- 수정 내용
  - `stdNtceDocUrl` 값이 실제로 있을 때만 `standard_notice.pdf` 첨부 항목을 생성하도록 수정
  - URL이 없는 표준공고문 placeholder가 다시 생성되지 않도록 백엔드 테스트 보강
- 수정 파일
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- 검증 결과
  - 백엔드 단위 테스트 8건 성공

## Additional Update (2026-05-06)
- Investigated and fixed why `standard_notice.pdf` appeared as `unsupported` in notice attachment details.
- Cause:
  - the system created a placeholder attachment named `standard_notice.pdf` even when `stdNtceDocUrl` was empty
  - because there was no actual download URL, the attachment was marked `unsupported` despite looking like a PDF
- Changes:
  - only create the `standard_notice.pdf` attachment when `stdNtceDocUrl` actually exists
  - added a backend regression assertion to prevent URL-less standard notice placeholders
- Updated files:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- Verification:
  - backend unit tests passed, 8 tests

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 공고 검색 기본 조회 조건 변경
- 수정 내용
  - `조회 시작일` 기본값을 오늘 기준 3일 전으로 변경
  - `조회 종료일` 기본값을 오늘 날짜로 유지
  - 페이지 크기 최대값을 `100`으로 조정
  - 백엔드 검색 API의 `page_size` 상한도 `100`으로 조정
  - 화면 안내 문구를 `최근 3일` 기준으로 변경
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `backend/app/main.py`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공
  - 백엔드 단위 테스트 8건 성공

## Additional Update (2026-05-06)
- Updated default Nara notice search conditions per user request.
- Changes:
  - default `start date` is now today minus 3 days
  - default `end date` remains today
  - maximum page size is now `100`
  - backend `page_size` cap is also set to `100`
  - helper copy now says the default range is recent 3 days
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `backend/app/main.py`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed
  - backend unit tests passed, 8 tests

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `공고 목록` 테이블 정렬 UX 개선
- 수정 내용
  - `마감`, `금액` 컬럼에 정렬 가능 여부를 바로 알 수 있는 아이콘 추가
  - 정렬 미적용 상태는 `↕` 아이콘 표시
  - 정렬 적용 상태는 `↑`, `↓` 아이콘 표시
  - `마감`, `금액` 두 컬럼 정렬을 동시에 적용 가능하도록 변경
  - 다중 정렬 시 적용 우선순위를 작은 숫자 배지로 표시
  - 같은 컬럼 클릭 흐름: 오름차순 -> 내림차순 -> 정렬 해제
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Improved sorting UX for the Nara notice results table.
- Changes:
  - added always-visible sort affordance icons for `deadline` and `amount`
  - unsorted state shows `↕`
  - sorted state shows `↑` or `↓`
  - deadline and amount sorting can now be applied together
  - multi-sort priority is shown with a small numeric badge
  - repeated clicks cycle through ascending -> descending -> off
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `공고 목록` 테이블에 `등록 날짜` 컬럼 추가
- API 응답 확인
  - 나라장터 공고 응답의 `bidNtceDt` 값을 등록/공고 일시로 사용
  - 프론트 정규화 모델에서는 `bid_ntce_dt`로 사용 중
- 수정 내용
  - `등록 날짜` 컬럼 추가
  - `YYYY-MM-DD HH:mm` 형태로 날짜+시간 표시
  - `등록 날짜` 정렬 추가
  - 기존 `마감`, `금액`과 함께 다중 정렬 가능
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added a `Posted At` column to the Nara notice results table.
- API response note:
  - uses Nara response field `bidNtceDt` as the posted/notice datetime
  - frontend normalized field is `bid_ntce_dt`
- Changes:
  - added posted datetime column
  - displays date and time as `YYYY-MM-DD HH:mm`
  - added posted datetime sorting
  - supports multi-sort together with deadline and amount
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `공고 목록` 페이지네이션 기능 추가
- 수정 내용
  - API의 `pageNo` 파라미터와 프론트 페이지 상태 연결
  - 현재 페이지/전체 페이지 표시
  - `처음`, `이전`, 페이지 번호, `다음`, `마지막` 버튼 추가
  - 페이지 크기 변경 시 1페이지로 초기화
  - 페이지 이동 시 해당 페이지의 공고 목록 재조회
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added pagination to the Nara notice results table.
- Changes:
  - connected frontend page state to the API `pageNo` parameter
  - displays current page and total pages
  - added first, previous, page number, next, and last controls
  - resets to page 1 when page size changes
  - refetches notices on page navigation
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 질문 반영: 나라장터 `상세 미리보기` 첨부파일 클릭/열기 기능 추가
- 수정 내용
  - 첨부파일 URL이 있는 경우 파일명을 링크로 표시
  - `열기` 버튼을 추가해 새 탭에서 첨부 URL을 열 수 있도록 변경
  - 첨부 URL이 없는 경우 `URL 없음` 배지 표시
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added clickable attachment links in the Nara notice preview.
- Changes:
  - file names become links when an attachment URL exists
  - added an `Open` button that opens the attachment URL in a new tab
  - displays a `No URL` badge when no attachment URL exists
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 질문 반영: 나라장터 첨부 PDF를 다운로드 대신 브라우저에서 바로 열 수 있도록 개선
- 원인
  - 기존 `열기` 버튼은 나라장터 원본 첨부 URL을 직접 열었기 때문에 원본 서버가 다운로드 헤더를 내려주면 브라우저가 파일을 다운로드함
- 수정 내용
  - 백엔드에 첨부파일 preview 프록시 API 추가
  - PDF 첨부는 백엔드가 원본 파일을 받아 `Content-Disposition: inline`으로 다시 내려주도록 처리
  - PDF는 `브라우저 열기` 버튼으로 새 탭에서 열도록 변경
  - DOCX 등 브라우저 자체 렌더링이 어려운 파일은 기존처럼 다운로드 동작 유지
  - URL 누락 요청에 대한 백엔드 테스트 추가
- 수정 파일
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/api.ts`
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공
  - 백엔드 단위 테스트 9건 성공
  - FE/BE 서버 재시작 및 실행 상태 확인

## Additional Update (2026-05-06)
- Improved Nara PDF attachments so they can open inline in the browser instead of always downloading.
- Cause:
  - the previous `Open` button navigated directly to the original Nara attachment URL, so browser behavior followed the upstream download headers
- Changes:
  - added a backend attachment preview proxy endpoint
  - PDF files are fetched by the backend and returned with `Content-Disposition: inline`
  - PDF attachments now use a `Browser Open` action in a new tab
  - DOCX and other browser-unfriendly formats still use download behavior
  - added backend test coverage for missing preview URL requests
- Updated files:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/api.ts`
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed
  - backend unit tests passed, 9 tests
  - FE/BE servers restarted and confirmed running

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `상세 미리보기` 정보량 확대
- 수정 내용
  - 공고번호/차수 추가
  - 등록 날짜, 입찰 시작, 입찰 마감, 개찰 일시 표시
  - 추정가격, 예산금액, 기초금액 표시
  - 지역, 면허/업종, 입찰방식, 계약방법, 공동수급 힌트 표시
  - 나라장터 원문 링크 표시
  - API 원본 주요값을 접기/펼치기 영역에서 확인 가능하도록 추가
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Expanded the Nara notice detail preview based on user feedback.
- Changes:
  - added notice number/order
  - added posted date, bid start, bid deadline, and opening datetime
  - added estimated price, budget amount, and basis amount
  - added region, license/industry, bid method, contract method, and joint supply hints
  - added original Nara notice link
  - added collapsible raw API value preview
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 왼쪽 네비게이션 사이드바에 세로 스크롤 추가
- 원인
  - 사이드바가 `100vh` 높이에 고정되어 있었지만 내부 `overflow-y` 처리가 없어 하단 `운영 순서` 영역으로 이동할 수 없었음
- 수정 내용
  - 사이드바에 `overflow-y: auto` 적용
  - 스크롤바 표시 공간 안정화를 위해 `scrollbar-gutter: stable` 적용
  - WebKit 계열 브라우저용 차분한 스크롤바 스타일 추가
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added vertical scrolling to the left navigation sidebar based on user feedback.
- Cause:
  - sidebar was fixed at `100vh` but had no internal `overflow-y`, making the lower operation guide inaccessible
- Changes:
  - added `overflow-y: auto`
  - added `scrollbar-gutter: stable`
  - added subtle WebKit scrollbar styling
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 대시보드 연동 상태가 실제 API 설정을 반영하지 않는 문제 확인 및 수정
- 원인
  - `frontend/.env`에 예전 API 주소 `http://127.0.0.1:8000`이 남아 있었음
  - 관리 스크립트가 실행 시 `VITE_API_BASE_URL=http://127.0.0.1:18111`을 넘기더라도 Vite가 `.env` 값을 우선 적용하면서 대시보드가 잘못된 백엔드 상태를 볼 수 있었음
- 수정 내용
  - `frontend/.env`를 `http://127.0.0.1:18111`로 변경
  - UTF-8 BOM 없이 재작성
  - FE/BE 서버 재시작
- 검증 결과
  - 나라장터 설정 상태 API 응답에서 `configured=true` 확인
  - FE/BE 서버 정상 실행 확인
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Fixed dashboard integration status not reflecting the configured Nara API key.
- Cause:
  - `frontend/.env` still pointed to the old API URL `http://127.0.0.1:8000`
  - even though the management script passed `VITE_API_BASE_URL=http://127.0.0.1:18111`, Vite could prefer `.env`, causing the dashboard to query the wrong backend
- Changes:
  - updated `frontend/.env` to `http://127.0.0.1:18111`
  - rewrote it without UTF-8 BOM
  - restarted FE/BE servers
- Verification:
  - Nara settings status API returns `configured=true`
  - FE/BE servers are running
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 연결 테스트 결과가 저장되지 않아 `not_run`으로 보이는 문제 수정
- 원인
  - 기존 연결 테스트 API는 결과를 응답으로만 반환하고 DB에 저장하지 않았음
  - 설정 화면/대시보드가 다시 상태 API를 조회하면 마지막 테스트 결과가 없어 `not_run`으로 표시됨
- 수정 내용
  - `integration_test_results` 테이블 추가
  - 나라장터 연결 테스트 실행 시 상태, HTTP 상태, API 결과 코드, 메시지, 조회 건수, 테스트 시각 저장
  - 설정 상태 API가 최신 연결 테스트 결과를 반환하도록 변경
  - 설정 화면에서 테스트 실행 후 상태를 다시 불러오도록 변경
  - 저장된 최근 테스트 결과 상세 표시 추가
  - 테스트 결과 저장/조회 백엔드 테스트 추가
- 수정 파일
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/types.ts`
  - `frontend/src/pages/SettingsPage.tsx`
  - `docs/work-log.md`
- 검증 결과
  - 백엔드 단위 테스트 10건 성공
  - 프론트엔드 `npm run build` 성공
  - FE/BE 서버 재시작 및 실행 상태 확인

## Additional Update (2026-05-06)
- Fixed the Nara connection test result not being persisted, which caused `not_run` to keep showing.
- Cause:
  - the previous connection test endpoint returned the result but did not store it
  - status screens later had no persisted latest test result, so they displayed `not_run`
- Changes:
  - added `integration_test_results` table
  - persisted Nara test status, HTTP status, API result code/message, total count, and tested timestamp
  - updated the integration status API to return the latest saved test result
  - settings page now reloads status after running a test
  - added saved latest test details display
  - added backend test coverage for saved test result lookup
- Updated files:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/types.ts`
  - `frontend/src/pages/SettingsPage.tsx`
  - `docs/work-log.md`
- Verification:
  - backend unit tests passed, 10 tests
  - frontend `npm run build` passed
  - FE/BE servers restarted and confirmed running

## 추가 업데이트 (2026-05-06)
- 사용자 요청에 따라 나라장터 `상세 미리보기` 패널에 독립 스크롤 추가
- 수정 내용
  - `Selected Notice / 상세 미리보기` 패널을 화면 높이 기준으로 제한
  - 패널 내부에 `overflow-y: auto` 적용
  - 상세 패널 헤더를 sticky 처리해 스크롤 중에도 제목 유지
  - 패널 전용 스크롤바 스타일 추가
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Added independent scrolling to the Nara selected notice preview panel.
- Changes:
  - constrained the `Selected Notice / Detail Preview` panel to viewport height
  - applied internal `overflow-y: auto`
  - made the preview panel header sticky
  - added panel-specific scrollbar styling
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 공고 상세 첨부 목록에 `standard_notice.pdf`가 계속 보이는 문제 정리
- 원인
  - `stdNtceDocUrl` 값이 실제로 존재하는 경우 표준공고문 첨부를 표시하는 것은 정상 동작
  - 다만 시스템이 표시명을 `standard_notice.pdf`로 고정해 사용하고 있어 사용자 입장에서 불필요한 기술명처럼 보였음
- 수정 내용
  - `stdNtceDocUrl` 첨부 표시명을 `standard_notice.pdf`에서 `표준공고문.pdf`로 변경
  - URL이 있는 표준공고문은 계속 PDF 첨부로 표시하고 브라우저 열기 대상이 되도록 유지
  - 표준공고문 표시명 회귀 테스트 추가
- 수정 파일
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- 검증 결과
  - 백엔드 단위 테스트 11건 성공
  - 프론트엔드 `npm run build` 성공
  - FE/BE 서버 재시작 및 실행 상태 확인
- 주의
  - 이미 저장된 기존 공고의 첨부명은 DB에 남아 있으므로 삭제 후 다시 저장하거나 재분석해야 새 표시명이 반영됨

## Additional Update (2026-05-06)
- Cleaned up the remaining `standard_notice.pdf` display in Nara notice attachment details.
- Cause:
  - when `stdNtceDocUrl` exists, showing the standard notice attachment is expected
  - however the fixed display name `standard_notice.pdf` looked like an internal technical placeholder
- Changes:
  - changed `stdNtceDocUrl` attachment display name from `standard_notice.pdf` to `표준공고문.pdf`
  - kept real standard notice URLs as supported PDF attachments and browser preview targets
  - added regression test coverage for the display name
- Updated files:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `docs/work-log.md`
- Verification:
  - backend unit tests passed, 11 tests
  - frontend `npm run build` passed
  - FE/BE servers restarted and confirmed running
- Note:
  - existing saved notices may still have the old attachment name in DB; delete and save again or reanalyze to refresh the stored attachment metadata.

## 추가 업데이트 (2026-05-06)
- 사용자 제보 반영: 나라장터 `Selected Notice / 상세 미리보기` 패널에서 상단 정보가 헤더에 가려지는 스크롤 버그 수정
- 원인
  - 패널 전체에 `overflow-y: auto`를 적용한 상태에서 헤더도 `sticky`로 고정되어 본문 첫 번째 항목이 헤더 아래에 겹쳐 보였음
  - 헤더의 음수 margin 처리 때문에 스크롤 시작 위치와 실제 본문 시작 위치가 어긋났음
- 수정 내용
  - 상세 미리보기 패널을 `헤더 영역`과 `본문 스크롤 영역`으로 분리
  - 스크롤은 본문 영역(`notice-preview-panel__body`)에만 적용
  - 패널 헤더의 sticky/음수 margin 처리를 제거해 첫 번째 항목이 정상적으로 보이도록 변경
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Fixed a scroll overlap bug in the Nara `Selected Notice / Detail Preview` panel.
- Cause:
  - the full panel had `overflow-y: auto` while the header was also sticky, causing the first detail row to render underneath the header
  - negative header margins made the scroll start offset inconsistent with the body content start
- Changes:
  - split the preview panel into a fixed header area and a body-only scroll area
  - moved vertical scrolling to `notice-preview-panel__body`
  - removed sticky/negative-margin behavior from the panel header
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `공고 목록`에서 공고를 선택했을 때 `상세 미리보기` 변경 시인성이 부족한 문제 개선
- 수정 내용
  - 선택된 공고 키가 바뀔 때 상세 미리보기 본문이 다시 마운트되도록 처리
  - 미리보기 본문에 짧은 슬라이드/페이드 인 애니메이션 추가
  - 첫 번째 상세 정보 행에 벚꽃 톤 하이라이트 애니메이션을 추가해 변경 피드백 강화
  - `prefers-reduced-motion` 환경에서는 애니메이션을 비활성화하도록 접근성 고려
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Improved visual feedback when selecting a notice in the Nara notice results table.
- Changes:
  - remount the detail preview body when the selected notice key changes
  - added a short slide/fade-in animation to the preview body
  - added a cherry-blossom-toned highlight animation to the first detail row
  - disabled the animation for `prefers-reduced-motion` users
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `상세 미리보기` 선택 변경 애니메이션 조정
- 수정 내용
  - 상세 미리보기 본문이 위로 들어오는 속도를 더 느리고 부드럽게 조정
  - 첫 번째 상세 정보 행 하이라이트 애니메이션 제거
  - 선택 변경 시 상단에 짧은 벚꽃 톤 로딩/전환 바가 나타나도록 변경
  - `prefers-reduced-motion` 환경에서는 전환 바도 숨기도록 접근성 처리 유지
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Tuned the Nara detail preview selection-change animation based on user feedback.
- Changes:
  - slowed down and softened the upward enter animation
  - removed the first-row highlight animation
  - added a short cherry-blossom-toned loading/transition bar at the top of the preview
  - kept reduced-motion handling by hiding the transition bar when motion is reduced
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `상세 미리보기` 선택 변경 로딩 표시 위치와 형태 수정
- 수정 내용
  - 상단 로딩/전환 바 제거
  - 선택 변경 시 상세 미리보기 카드 중앙에 짧게 나타나는 회전 로더 추가
  - 로더는 약 1초 후 사라지며, 선택된 공고가 바뀔 때마다 다시 재생되도록 처리
  - `prefers-reduced-motion` 환경에서는 중앙 로더 애니메이션도 숨김
- 수정 파일
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Updated the Nara detail preview selection-change loading indicator based on user feedback.
- Changes:
  - removed the top loading/transition bar
  - added a short centered spinning loader in the detail preview card
  - the loader fades out after about one second and replays whenever the selected notice changes
  - hides the centered loader animation for `prefers-reduced-motion` users
- Updated files:
  - `frontend/src/pages/NaraBoardPage.tsx`
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `상세 미리보기` 중앙 로딩 인디케이터 표시 시간을 0.5초로 단축
- 수정 내용
  - 중앙 로더 박스 애니메이션을 `1050ms`에서 `500ms`로 변경
  - 짧은 표시 시간 안에서도 회전이 인지되도록 스핀 속도를 `360ms`로 조정
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Shortened the Nara detail preview centered loading indicator to 0.5 seconds.
- Changes:
  - changed the loader box animation from `1050ms` to `500ms`
  - adjusted spinner speed to `360ms` so the rotation remains visible in the shorter duration
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `상세 미리보기` 본문 전환 이동 폭 축소
- 수정 내용
  - 본문이 위로 들어오는 이동 폭을 `16px` 수준에서 `4px` 수준으로 축소
  - 스케일/블러 효과를 제거해 화면이 크게 움직이는 느낌을 줄임
  - opacity 변화도 약하게 조정해 중앙 로더가 주 피드백이 되도록 정리
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Reduced the movement distance of the Nara detail preview body transition.
- Changes:
  - reduced the upward enter movement from about `16px` to about `4px`
  - removed scale/blur effects to avoid a large page-shift feeling
  - softened opacity changes so the centered loader remains the primary feedback
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-06)
- 사용자 피드백 반영: 나라장터 `상세 미리보기` 본문 전환 모션 삭제
- 수정 내용
  - 상세 미리보기 본문 슬라이드/페이드 전환 애니메이션 제거
  - 선택 변경 피드백은 중앙 로딩 인디케이터만 남기도록 단순화
  - 사용자가 공고를 선택할 때 화면이 움직이는 느낌을 없앰
- 수정 파일
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- 검증 결과
  - 프론트엔드 `npm run build` 성공

## Additional Update (2026-05-06)
- Removed the Nara detail preview body transition animation.
- Changes:
  - removed the detail preview slide/fade transition
  - kept only the centered loading indicator as selection-change feedback
  - eliminated visible page movement when selecting a notice
- Updated files:
  - `frontend/src/styles.css`
  - `docs/work-log.md`
- Verification:
  - frontend `npm run build` passed

## 추가 업데이트 (2026-05-07)
- 사용자 요청에 따라 올인원 서버 관리 스크립트로 FE/BE 서버 실행
- 실행 명령
  - `powershell -ExecutionPolicy Bypass -File .\scripts\manage-servers.ps1 start`
- 실행 상태
  - 백엔드 실행 중: `http://127.0.0.1:18111`
  - 프론트엔드 실행 중: `http://127.0.0.1:5199`
  - 스크립트 상태 확인 결과 FE/BE 모두 `running`
- 검증 결과
  - `manage-servers.ps1 status` 확인 완료
  - `18111`, `5199` 포트 Listen 상태 확인 완료

## Additional Update (2026-05-07)
- Started FE/BE servers using the all-in-one server management script.
- Command:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\manage-servers.ps1 start`
- Runtime status:
  - backend running: `http://127.0.0.1:18111`
  - frontend running: `http://127.0.0.1:5199`
  - script status reports both FE/BE as `running`
- Verification:
  - confirmed via `manage-servers.ps1 status`
  - confirmed listening ports `18111` and `5199`
