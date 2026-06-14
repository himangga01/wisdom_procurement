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
  - 비표준 Python 런타임의 패키지 호환 이슈로 백엔드 런타임 의존성 조정
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
  - dependency compatibility adjustments for a non-standard Python runtime
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
  - 당시 `OPENAI_API_KEY`가 있으면 이전 기본 모델로 요약 호출하도록 기록했으나, 이후 기본 모델은 `gpt-5.4-mini`로 변경됨
  - API 키가 없거나 API 호출 실패 시 규칙 기반 fallback 요약 사용
  - fallback 요약은 AI 모델이 아니라 텍스트 앞부분/일부 줄을 재구성하는 임시 로직
- 참고 파일
  - `backend/app/main.py`
  - `docs/ai-api-setup.md`

## Additional Update (2026-04-05 21:40:00 +09:00)
- Reviewed the current "internal fallback summary" behavior in response to a product question.
- Confirmed:
  - PDF/DOCX text extraction is local and does not require an API key.
  - At that time, `OPENAI_API_KEY` triggered the previous default model for summary generation; the current default model was later changed to `gpt-5.4-mini`.
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
- `py -3.13 -m unittest discover -s tests -v` 성공
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
- `py -3.13 -m unittest discover -s tests -v` passed.
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

## 추가 업데이트 (2026-05-10)
- 사용자 요청에 따라 향후 핵심 기능인 `법인 사업자 대 공고문 지원 가능성 판단`을 위한 상세 구현계획 수립
- 제품 방향 재정의
  - 단순 `지원 가능/불가능`보다 `현재 무엇이 부족한지`, `지원하려면 어떤 인증/면허/서류를 준비해야 하는지`를 핵심 가치로 정의
  - 대부분의 사업자는 즉시 지원 가능 상태가 아니므로 기본 설계는 부족 조건 분석과 준비 가이드 중심으로 정리
- 신규 문서
  - `docs/eligibility-rag-implementation-plan.md`
- 신규 문서 주요 내용
  - 법인 사업자 입력 필드 확장 검토
  - 법인 증빙자료 도메인 추가 권장
  - 기준문서 관리 기능 재검토
  - 기준문서 메타데이터/청크/판단 규칙 스키마 제안
  - Qdrant local 중심 로컬 RAG 구현계획
  - 공고 요구조건 추출, 법인 조건 매칭, 부족 항목/준비 가이드 출력 흐름
  - API 초안, UI 초안, 테스트 계획, 가정, 미해결 질문 정리
- 기존 문서 업데이트
  - `docs/technical-design.md`: 판단 제품 원칙, 법인 확장 필드, 기준문서/규칙/증빙자료 스키마, 판단 엔진 흐름 보강
  - `docs/ux-design.md`: 법인 준비 상태 프로필, 기준문서 관리 콘솔, 부족 조건 중심 판단 결과 UX 보강
  - `README.md`: 신규 문서 링크와 로드맵 보강
  - `AGENTS.md`: 미래 판단 엔진 가드레일 추가
- 검증 결과
  - 문서 생성/수정 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Created a detailed implementation plan for the future corporation-vs-notice eligibility/readiness feature.
- Product direction:
  - the core value is not a simple eligible/not-eligible verdict, but explaining missing requirements and required certifications/licenses/documents
  - since most corporations are not immediately ready, the design centers on gap analysis and preparation guidance
- New document:
  - `docs/eligibility-rag-implementation-plan.md`
- New document covers:
  - expanded corporation input fields
  - recommended corporation evidence document domain
  - basis document management recheck
  - basis metadata/chunk/rule schemas
  - local RAG implementation plan centered on Qdrant local
  - notice requirement extraction, corporation matching, missing requirement output, and preparation guide flow
  - API draft, UI draft, test plan, assumptions, and open questions
- Updated existing documents:
  - `docs/technical-design.md`: product judgment principles, expanded corporation fields, basis/rule/evidence schemas, judgment flow
  - `docs/ux-design.md`: corporation readiness profile, basis evidence console, gap-first judgment result UX
  - `README.md`: new document link and roadmap update
  - `AGENTS.md`: future judgment guardrails
- Verification:
  - confirmed document creation/updates
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- Phase 1.6 개발계획을 실제 구현 착수 관점에서 재검토했다.
- 결론:
  - 방향 자체는 문제 없음
  - 다만 모든 증빙자료를 한 번에 고정확도로 자동화하려는 범위는 과도함
  - Phase 1.6을 `1.6A`, `1.6B`, `1.6C`로 나누는 방식이 현실적임
- 확정한 분리:
  - Phase 1.6A: 사업자등록증명/사업자등록증 기반 법인 등록 MVP
  - Phase 1.6B: 중소기업확인서, 여성기업확인서, 장애인기업확인서, 직접생산확인증명서, 나라장터 등록 관련 서류, 주요 면허/인증 등 확장
  - Phase 1.6C: 알 수 없는 증빙자료 LLM 분류, 수동 유형 지정, 충돌 처리, 개인정보 로그 마스킹, 샘플 기반 테스트 강화
- 추가 가드레일:
  - 현재 백엔드는 Flask이므로 Phase 1.6에서 FastAPI 마이그레이션을 섞지 않음
  - OCR은 엔진 직접 결합이 아니라 `OcrService` 어댑터로 추상화
  - LLM 분류는 API 키가 있을 때만 실행하고 사용자 검토 후보로만 저장
  - 사업자등록번호, 대표자명, 주소 등 민감 정보는 로그 원문 노출 금지
- 업데이트한 문서:
  - `docs/corporation-evidence-auto-extraction-plan.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `docs/eligibility-rag-implementation-plan.md`
  - `README.md`
  - `AGENTS.md`
- 검증 결과:
  - 문서 간 Phase 1.6A/1.6B/1.6C 기준 정합성 확인
  - 현재 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Re-reviewed the Phase 1.6 implementation plan from a delivery-readiness perspective.
- Conclusion:
  - the direction is valid
  - the original all-at-once evidence automation scope is too broad
  - Phase 1.6 should be split into 1.6A, 1.6B, and 1.6C
- Confirmed split:
  - Phase 1.6A: business registration evidence-based corporation registration MVP
  - Phase 1.6B: SME, women-owned, disabled-owned, direct production, Nara registration, and major license/certification evidence expansion
  - Phase 1.6C: unknown evidence LLM classification, manual type assignment, conflict handling, sensitive-log redaction, and fixture-based test hardening
- Added guardrails:
  - implement Phase 1.6 on the current Flask backend without mixing in a FastAPI migration
  - keep OCR behind an `OcrService` adapter
  - run LLM classification only when an API key is configured and save output as review candidates only
  - do not log sensitive corporation or personal identifiers in raw form
- Updated documents:
  - `docs/corporation-evidence-auto-extraction-plan.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `docs/eligibility-rag-implementation-plan.md`
  - `README.md`
  - `AGENTS.md`
- Verification:
  - confirmed cross-document alignment for Phase 1.6A/1.6B/1.6C
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- OCR 엔진 구현계획을 작성했다.
- 공식 자료 기준으로 오픈소스 OCR 후보를 재검토했다.
- 결정:
  - 주 OCR 엔진은 `PaddleOCR PP-OCRv5`
  - 경량 fallback 후보는 `Tesseract OCR`
  - PDF 페이지 렌더링은 기존 `PyMuPDF`를 사용
  - 이미지 전처리는 `OpenCV`와 `Pillow`를 사용
  - OCR 엔진은 `OcrService/OcrEngine` 어댑터 구조로 구현
- 로컬 환경 확인:
  - 서비스 표준 Python은 `3.13.13`
  - Windows 실행 명령은 `py -3.13`
  - 실제 실행 파일은 `C:\Python313\python.exe`
- 리스크:
  - PaddleOCR/PaddlePaddle은 Python 3.13.13 기준으로 설치/검증해야 한다.
- 신규 문서:
  - `docs/ocr-engine-implementation-plan.md`
- 업데이트한 문서:
  - `README.md`
  - `docs/technical-design.md`
  - `AGENTS.md`
- 검증 결과:
  - OCR 구현계획 문서 생성 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Added an OCR engine implementation plan.
- Reviewed open-source OCR candidates from official sources.
- Decisions:
  - primary OCR engine: `PaddleOCR PP-OCRv5`
  - lightweight fallback candidate: `Tesseract OCR`
  - PDF page rendering: existing `PyMuPDF`
  - image preprocessing: `OpenCV` and `Pillow`
  - OCR architecture: `OcrService/OcrEngine` adapter
- Local environment check:
  - service standard Python: `3.13.13`
  - Windows command: `py -3.13`
  - executable: `C:\Python313\python.exe`
- Risk:
  - PaddleOCR/PaddlePaddle must be installed and validated against Python 3.13.13.
- New document:
  - `docs/ocr-engine-implementation-plan.md`
- Updated documents:
  - `README.md`
  - `docs/technical-design.md`
  - `AGENTS.md`
- Verification:
  - confirmed OCR plan document creation
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- OCR 엔진 구현을 시작했다.
- 구현 내용:
  - `backend/app/pipelines/ocr.py`를 실제 OCR 어댑터 구조로 교체
  - `OcrResult`, `OcrPageResult`, `OcrEngine` 구조 추가
  - `PaddleOcrEngine` 추가
  - `TesseractOcrEngine` fallback 후보 추가
  - `NoopOcrEngine` 추가
  - OCR 상태값 `skipped`, `completed`, `needs_ocr`, `needs_ocr_setup`, `unavailable`, `failed` 정리
  - PDF OCR 시 `PyMuPDF`로 페이지 이미지를 렌더링한 뒤 OCR 엔진에 전달
  - 이미지 파일 `.jpg`, `.jpeg`, `.png` OCR 실행 함수 추가
  - OCR 엔진 미설치 시 서버가 실패하지 않고 `needs_ocr_setup`으로 degrade
- 기존 파이프라인 연결:
  - 일반 문서 분석에서 `extract_document()` 이후 OCR 필요 시 `run_ocr_if_needed()` 호출
  - 나라장터 첨부파일 파싱에서도 동일 OCR 경로를 사용하도록 연결
  - legacy analysis service도 새 OCR 함수 시그니처에 맞춰 조정
- 의존성:
  - `backend/requirements-ocr.txt` 추가
  - PaddleOCR/PaddlePaddle은 Python 3.13.13 런타임에 설치하는 것을 권장
- 테스트:
  - `backend/tests/test_ocr.py` 추가
  - OCR skip 테스트
  - OCR 엔진 미설치 fallback 테스트
  - fake OCR 엔진 기반 이미지 OCR 테스트
  - fake OCR 엔진 기반 PDF 페이지 렌더링 테스트
  - 실제 사업자등록증 이미지 OCR 선택 테스트 추가
- 사용자 제공 샘플 이미지 테스트:
  - `OCR_SAMPLE_IMAGE_PATH`로 이미지 경로를 받아 실행
  - `RUN_REAL_OCR_TESTS=1`일 때만 실제 OCR 테스트 실행
  - 현재 Python 3.13.13 런타임에 OCR 의존성이 없으면 실제 OCR 테스트는 정상 skip 처리됨
- 검증 결과:
  - `py -3.13 -m unittest tests.test_ocr -v`
  - 결과: 5개 테스트 중 4개 통과, 1개 실제 OCR 선택 테스트 skip
  - `py -3.13 -m unittest discover -s tests -v`
  - 결과: 16개 테스트 중 15개 통과, 1개 실제 OCR 선택 테스트 skip

## Additional Update (2026-05-10)
- Started OCR engine implementation.
- Implemented:
  - replaced `backend/app/pipelines/ocr.py` with a real adapter-based OCR module
  - added `OcrResult`, `OcrPageResult`, and `OcrEngine`
  - added `PaddleOcrEngine`
  - added `TesseractOcrEngine` fallback candidate
  - added `NoopOcrEngine`
  - standardized OCR statuses: `skipped`, `completed`, `needs_ocr`, `needs_ocr_setup`, `unavailable`, `failed`
  - PDF OCR renders pages with `PyMuPDF` before passing images to the OCR engine
  - image OCR supports `.jpg`, `.jpeg`, and `.png`
  - missing OCR dependencies degrade to `needs_ocr_setup` instead of crashing the server
- Pipeline wiring:
  - document analysis calls `run_ocr_if_needed()` after `extract_document()`
  - Nara attachment parsing uses the same OCR path
  - legacy analysis service was adjusted to the new OCR function signature
- Dependencies:
  - added `backend/requirements-ocr.txt`
  - PaddleOCR/PaddlePaddle should be installed into the Python 3.13.13 runtime first
- Tests:
  - added `backend/tests/test_ocr.py`
  - OCR skip test
  - missing engine fallback test
  - fake-engine image OCR test
  - fake-engine PDF page rendering test
  - optional real business-registration image OCR test
- User-provided sample image test:
  - reads image path from `OCR_SAMPLE_IMAGE_PATH`
  - runs only when `RUN_REAL_OCR_TESTS=1`
  - the real OCR test is skipped safely when OCR dependencies are not installed in Python 3.13.13
- Verification:
  - `py -3.13 -m unittest tests.test_ocr -v`
  - result: 4 passed, 1 optional real OCR test skipped
  - `py -3.13 -m unittest discover -s tests -v`
  - result: 15 passed, 1 optional real OCR test skipped

## 추가 업데이트 (2026-05-10)
- PaddleOCR 실제 설치와 사업자등록증 이미지 OCR 검증을 진행했다.
- 설치 과정:
  - 초기 임시 Python 3.13 환경에는 `pip`가 없어 `ensurepip --upgrade`로 pip를 설치했다.
  - `paddleocr`, `paddlepaddle`, `opencv-python`, `pillow`, `numpy`, `pytesseract` 설치를 진행했다.
  - `python-bidi==0.6.9`가 Rust 빌드 중 `python313.lib`를 찾지 못해 실패했다.
  - `python-bidi==0.4.2`를 먼저 설치한 뒤 OCR 의존성 설치가 성공했다.
- PaddlePaddle 버전 검증:
  - `paddlepaddle==3.3.1`은 PP-OCRv5 실행 중 oneDNN/PIR 런타임 오류가 발생했다.
  - `paddlepaddle==3.2.2`로 낮춘 뒤 실제 OCR이 성공했다.
  - `backend/requirements-ocr.txt`를 `paddlepaddle==3.2.2`, `python-bidi==0.4.2` 기준으로 고정했다.
- 사용자 제공 이미지 검증:
  - 원본 경로: `C:\Users\HOONJAE\Desktop\지혜행정사사무소\SH평가\10.SH평가_온세이엔씨_3등급\사업자등록증.png`
  - PowerShell/Python 경로 전달 중 한글 경로가 깨져 PaddleOCR가 파일을 열지 못하는 문제가 있었다.
  - 테스트 전용으로 `backend/storage/ocr-samples/business_registration.png`에 복사했다.
  - 민감한 샘플 이미지가 Git에 들어가지 않도록 `.gitignore`에 `backend/storage/ocr-samples/`를 추가했다.
- 실제 OCR 결과:
  - 상태: `completed`
  - 평균 신뢰도: 약 `0.9336`
  - 주요 인식 내용:
    - `등록번호:142-81-28387`
    - `주식회사 온세이엔씨`
    - `안영식`
    - `경기도 성남시 수정구 청계산로 686, 8층 820호`
    - `2022년 03월 30일`
- 테스트:
  - `py -3.13 -m unittest tests.test_ocr.OcrPipelineTests.test_business_registration_sample_image_with_real_engine_when_enabled -v`
  - 결과: 실제 사업자등록증 이미지 OCR 테스트 통과
  - `py -3.13 -m unittest discover -s tests -v`
  - 결과: 16개 테스트 통과, 1개 선택 테스트 skip
  - `py -3.13 -m unittest discover -s tests -v`
  - 결과: 16개 테스트 통과, 1개 선택 테스트 skip
- 추가 수정:
  - 일반 API 테스트에서 실제 PaddleOCR가 실행되지 않도록 `OCR_ENGINE=noop`을 설정했다.
  - OCR 모듈은 한글 경로 파일을 엔진에 넘길 때 ASCII 임시 경로로 복사하는 방어 로직을 추가했다.

## Additional Update (2026-05-10)
- Installed PaddleOCR dependencies and verified real OCR using the provided business registration image.
- Installation:
  - the initial temporary Python 3.13 environment had no `pip`, so `ensurepip --upgrade` was used.
  - installed `paddleocr`, `paddlepaddle`, `opencv-python`, `pillow`, `numpy`, and `pytesseract`.
  - `python-bidi==0.6.9` failed while building because `python313.lib` was unavailable.
  - installing `python-bidi==0.4.2` first allowed the OCR dependency installation to complete.
- PaddlePaddle version validation:
  - `paddlepaddle==3.3.1` failed during PP-OCRv5 inference with a oneDNN/PIR runtime error.
  - downgrading to `paddlepaddle==3.2.2` made real OCR succeed.
  - `backend/requirements-ocr.txt` now pins `paddlepaddle==3.2.2` and `python-bidi==0.4.2`.
- User-provided sample image:
  - original path: `C:\Users\HOONJAE\Desktop\지혜행정사사무소\SH평가\10.SH평가_온세이엔씨_3등급\사업자등록증.png`
  - Korean path text was corrupted when passed through PowerShell/Python, so PaddleOCR could not open the original path directly.
  - copied the image to `backend/storage/ocr-samples/business_registration.png` for local testing.
  - added `backend/storage/ocr-samples/` to `.gitignore` so the sensitive image is not committed.
- Real OCR result:
  - status: `completed`
  - average confidence: about `0.9336`
  - key recognized values:
    - `등록번호:142-81-28387`
    - `주식회사 온세이엔씨`
    - `안영식`
    - `경기도 성남시 수정구 청계산로 686, 8층 820호`
    - `2022년 03월 30일`
- Tests:
  - `py -3.13 -m unittest tests.test_ocr.OcrPipelineTests.test_business_registration_sample_image_with_real_engine_when_enabled -v`
  - result: real business registration image OCR test passed
  - `py -3.13 -m unittest discover -s tests -v`
  - result: 16 tests passed, 1 optional test skipped
  - `py -3.13 -m unittest discover -s tests -v`
  - result: 16 tests passed, 1 optional test skipped
- Additional fixes:
  - set `OCR_ENGINE=noop` in general API flow tests so they do not invoke real PaddleOCR.
  - added defensive logic that copies non-ASCII image paths to temporary ASCII paths before OCR engine calls.

## 추가 업데이트 (2026-05-10)
- 사용자의 요청에 따라 전역 로컬 Python 3.13 설치/복구 후 PaddlePaddle OCR을 다시 검증했다.
- 확인 결과:
  - 기존 `C:\Python313\python.exe`는 존재했지만 `pip`가 없고 `sys.prefix`가 작업 폴더로 잡히는 비정상 상태였다.
  - Winget 기준 `Python.Python.3.13`은 `3.13.7` 설치 상태였고 `3.13.13` 업그레이드가 가능했다.
  - `winget upgrade --id Python.Python.3.13 --scope user --silent`로 Python 3.13.13 복구/업그레이드를 완료했다.
- 복구 후 정상 상태:
  - `py -3.13` 실행 파일: `C:\Python313\python.exe`
  - `sys.prefix`: `C:\Python313`
  - Python 버전: `3.13.13`
  - pip 버전: `26.0.1`
- 전역 Python 3.13에 설치한 의존성:
  - `requirements.txt`
  - `requirements-ocr.txt`
- 전역 Python 3.13 검증:
  - `paddle==3.2.2`
  - `paddleocr==3.3.3`
  - 실제 사업자등록증 이미지 OCR 테스트 통과
  - 전체 백엔드 테스트 통과
- 실행한 검증:
  - `py -3.13 -m unittest tests.test_ocr.OcrPipelineTests.test_business_registration_sample_image_with_real_engine_when_enabled -v`
  - 결과: 통과
  - `py -3.13 -m unittest discover -s tests -v`
  - 결과: 16개 테스트 통과, 1개 선택 테스트 skip
- 문서 업데이트:
  - `docs/ocr-engine-implementation-plan.md`
  - `docs/work-log.md`

## Additional Update (2026-05-10)
- Per user request, repaired/upgraded global local Python 3.13 and re-tested PaddlePaddle OCR.
- Findings:
  - existing `C:\Python313\python.exe` existed, but had no `pip` and its `sys.prefix` incorrectly pointed to the working directory.
  - Winget showed `Python.Python.3.13` installed at `3.13.7` with `3.13.13` available.
  - upgraded/repaired Python 3.13.13 with `winget upgrade --id Python.Python.3.13 --scope user --silent`.
- Healthy state after repair:
  - `py -3.13` executable: `C:\Python313\python.exe`
  - `sys.prefix`: `C:\Python313`
  - Python version: `3.13.13`
  - pip version: `26.0.1`
- Installed dependencies into global Python 3.13:
  - `requirements.txt`
  - `requirements-ocr.txt`
- Global Python 3.13 verification:
  - `paddle==3.2.2`
  - `paddleocr==3.3.3`
  - real business registration image OCR test passed
  - full backend test suite passed
- Verification commands:
  - `py -3.13 -m unittest tests.test_ocr.OcrPipelineTests.test_business_registration_sample_image_with_real_engine_when_enabled -v`
  - result: passed
  - `py -3.13 -m unittest discover -s tests -v`
  - result: 16 tests passed, 1 optional test skipped
- Updated documents:
  - `docs/ocr-engine-implementation-plan.md`
  - `docs/work-log.md`

## 추가 업데이트 (2026-05-10)
- 사용자 피드백 반영: 법인 등록 UX를 `직접 입력 최소화` 방식으로 재구성
- 설계 결정
  - 기업유형/우대조건은 직접 텍스트 입력이 아니라 체크박스 카드 또는 토글 카드로 입력
  - 중소기업확인서, 여성기업, 장애인기업, 사회적기업, 협동조합, 벤처기업, 창업기업, 직접생산확인증명서를 빠른 선택 항목으로 제공
  - 선택한 항목만 세부유형, 만료일, 증빙자료 연결 필드를 펼침
  - 면허/인증은 검색형 드롭다운과 자주 쓰는 면허 빠른 선택 칩으로 입력
  - 실적/인력/장비는 `없음`, `있음`, `확인 필요` 중 먼저 선택하고, `있음`일 때만 상세 입력
  - 증빙자료 업로드 후 자동 추출 결과를 확인/수정하는 흐름을 우선
  - 법인 상세에는 단순 입력 완료율이 아니라 `공고 판단 준비도`를 표시
- 수정 문서
  - `docs/eligibility-rag-implementation-plan.md`
  - `docs/ux-design.md`
  - `docs/work-log.md`
- 검증 결과
  - 문서 반영 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Updated corporation registration UX to minimize manual text entry.
- Design decisions:
  - company type and preferential conditions use checkbox/toggle cards instead of free text
  - quick-select items include SME, women-owned, disabled-owned, social enterprise, cooperative, venture, startup, and direct production certificate
  - selected cards reveal only subtype, expiry date, and linked evidence fields
  - licenses/certifications use searchable dropdowns and quick-select chips
  - track record/staff/equipment starts with `none`, `exists`, or `unknown`; details open only when `exists` is selected
  - evidence upload with automatic extraction is preferred over manual entry
  - corporation detail shows notice evaluation readiness instead of simple form completion
- Updated documents:
  - `docs/eligibility-rag-implementation-plan.md`
  - `docs/ux-design.md`
  - `docs/work-log.md`
- Verification:
  - confirmed document updates
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- 사용자 피드백 반영: 법인 등록 UX를 `사업자등록증 선업로드 + 자동추출 우선` 구조로 변경
- 설계 결정
  - 법인 등록 첫 화면은 일반 입력 폼이 아니라 `사업자등록증 업로드` 화면으로 시작
  - 사용자가 사업자등록증을 업로드하면 이미지/PDF/Word 파일에서 법인명, 사업자등록번호, 대표자명, 사업장 주소, 업태/종목을 자동 추출
  - 사용자는 자동 추출 결과를 확인하고 틀린 값만 수정
  - `사업자등록증 없음` 또는 `나중에 입력`을 선택한 경우에만 직접 입력 폼 표시
  - 수동 입력으로 생성된 법인은 `기본정보 미검증` 또는 `증빙자료 없음` 상태로 표시
  - 법인 증빙자료 파일 형식은 PDF, DOCX, JPG/JPEG, PNG 우선 지원
  - 구형 DOC 파일은 추후 변환 경로가 준비될 때 지원 검토
- 문서 보강
  - `docs/eligibility-rag-implementation-plan.md`: 증빙자료 우선 온보딩 UX, 자동 추출 후보 필드, 추출 파이프라인, 상태값 추가
  - `docs/ux-design.md`: 법인 등록 첫 화면과 자동 추출 결과 확인 화면 구성 추가
  - `docs/technical-design.md`: 법인 증빙자료 자동 추출 파이프라인, API 초안, 증빙자료 메타데이터 확장
  - `AGENTS.md`: 법인 등록은 사업자등록증 자동 추출을 우선한다는 미래 확장 가드레일 추가
- 검증 결과
  - 문서 반영 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Changed corporation registration UX to evidence-first onboarding with business registration certificate upload and automatic extraction.
- Design decisions:
  - first corporation registration screen starts with certificate upload, not a general manual form
  - image/PDF/Word files are read to extract corporation name, business registration number, representative name, business address, business type, and business items
  - user reviews extracted values and corrects only inaccurate fields
  - manual form is shown only when the user selects `no certificate` or `enter later`
  - manually created corporations show `basic information unverified` or `no evidence`
  - corporation evidence uploads should support PDF, DOCX, JPG/JPEG, and PNG first
  - legacy DOC support is deferred until a conversion path is available
- Updated documents:
  - `docs/eligibility-rag-implementation-plan.md`: evidence-first onboarding UX, extraction candidate fields, extraction pipeline, and states
  - `docs/ux-design.md`: first registration screen and extraction review screen
  - `docs/technical-design.md`: corporation evidence extraction pipeline, API draft, evidence metadata expansion
  - `AGENTS.md`: future extensibility guardrail for certificate-first onboarding
- Verification:
  - confirmed document updates
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- 사용자 요청에 따라 사업자등록증 외 법인 증빙서류 업로드/자동추출 기능을 Phase 2 이전 선행 개발 범위로 재정의
- 웹 조사 기반으로 조달/공공구매에서 자주 등장하는 증빙서류 유형을 상세 분류
- 참고한 주요 자료
  - SMPP 기업정보 등록/변경 안내
  - SMPP 중소·여성·장애인기업 확인서 신청/발급 안내
  - SMPP 직접생산확인 안내
  - 정부24 사업자등록증명 발급
  - 정부24 나라장터 경쟁입찰 참가자격 등록
  - 벤처기업확인제도 안내
  - 한국SW산업협회 SW사업자 실적관리 안내
  - 사회적기업 포털
- 신규 문서
  - `docs/corporation-evidence-auto-extraction-plan.md`
- 신규 문서 주요 내용
  - Phase 1.6 `법인 증빙자료 자동 추출 기반` 신설
  - 사업자등록증명/사업자등록증 외 증빙서류 taxonomy 정의
  - 법인 기본 식별, 조달 등록, 기업유형/우대, 면허/허가, 생산/시설, 재무/세금/보험, 실적/인력/기술자, 입찰 제출서류로 분류
  - PDF/DOCX/JPG/JPEG/PNG 우선 지원
  - HWP/HWPX는 직접 파싱 제외 및 PDF 변환 안내
  - 규칙 기반 분류 실패 시 LLM 기반 알 수 없는 증빙서류 분류 fallback 설계
  - 사용자 확인 후 승인된 필드만 법인 프로필 업데이트
  - 증빙자료 추출 결과 확인 UX, 충돌 처리, 만료 처리, 수동 유형 지정 UX 설계
- 기존 문서 업데이트
  - `README.md`: Phase 1.6 추가, 신규 문서 링크, 로드맵 수정
  - `docs/technical-design.md`: Phase 1.6 범위/비범위, 증빙자료 taxonomy 우선순위, LLM fallback 처리 추가
  - `docs/ux-design.md`: 법인 상세 증빙자료 탭, 다중 업로드, AI 분류, 추출 결과 확인 UX 추가
  - `docs/eligibility-rag-implementation-plan.md`: 법인 증빙자료 개발을 Phase 1.6으로 이동하고 Phase 2 이전 선행 단계로 정리
  - `AGENTS.md`: Phase 1.6 가드레일과 알 수 없는 증빙자료 LLM 분류 규칙 추가
- 검증 결과
  - 문서 생성/수정 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-10)
- Reframed corporation evidence upload/auto-extraction as a pre-Phase-2 implementation target.
- Researched common procurement/public-purchase evidence document categories from web sources.
- Key references:
  - SMPP corporation info registration/change
  - SMPP SME/women-owned/disabled-owned confirmation application and issuance
  - SMPP direct production confirmation
  - Gov24 business registration proof
  - Gov24 Nara competitive bidding participant registration
  - venture business confirmation system
  - KOSA SW business performance management
  - Social Enterprise Portal
- New document:
  - `docs/corporation-evidence-auto-extraction-plan.md`
- New document covers:
  - new Phase 1.6 `corporation evidence auto-extraction foundation`
  - evidence taxonomy beyond business registration evidence
  - identity, procurement registration, company type/preference, license/permit, production/facility, finance/tax/insurance, track record/staff/technical, and bid-submission document categories
  - PDF/DOCX/JPG/JPEG/PNG first support
  - HWP/HWPX direct parsing excluded with PDF conversion guidance
  - LLM fallback classification for unknown evidence documents
  - reviewed-only corporation profile updates
  - extraction review UX, conflict handling, expiration handling, and manual type assignment
- Updated existing documents:
  - `README.md`: added Phase 1.6, new document link, roadmap changes
  - `docs/technical-design.md`: Phase 1.6 scope/non-scope, evidence taxonomy priority, LLM fallback handling
  - `docs/ux-design.md`: evidence tab, multi-file upload, AI classification, extraction review UX
  - `docs/eligibility-rag-implementation-plan.md`: moved corporation evidence work into Phase 1.6 before Phase 2
  - `AGENTS.md`: Phase 1.6 guardrails and unknown evidence LLM classification rules
- Verification:
  - confirmed document creation/updates
  - no runtime code changes

## 추가 업데이트 (2026-05-10)
- 사용자 요청에 따라 프로젝트 문서와 실행 스크립트의 Python 기준을 `Python 3.13.13`으로 통일했다.
- 신규 런타임 기준
  - Windows 실행 명령: `py -3.13`
  - 실제 실행 파일: `C:\Python313\python.exe`
  - 저장소 기준 파일: `.python-version`
- 수정한 문서
  - `README.md`: 백엔드 스택, 설치/실행/테스트 명령, OCR 런타임 안내를 Python 3.13.13 기준으로 변경
  - `AGENTS.md`: AI 작업 가드레일에 Python 3.13.13 표준 런타임 규칙 추가
  - `docs/technical-design.md`: OCR/백엔드 런타임 기준 업데이트
  - `docs/technology-summary.md`: 백엔드 활용 기술을 Python 3.13.13로 변경
  - `docs/ai-api-setup.md`: 의존성 설치 명령을 `py -3.13` 기준으로 변경
  - `docs/ocr-engine-implementation-plan.md`: 과거 venv 중심 설명을 Python 3.13.13 표준 런타임 설명으로 교체
  - `docs/work-log.md`: 이번 실제 작업 내역 추가 및 과거 실행 명령을 현재 표준 명령 기준으로 정리
- 수정한 코드/스크립트
  - `.python-version` 추가
  - `scripts/manage-servers.ps1`: 백엔드 실행 시 `py -3.13` 또는 `C:\Python313\python.exe`를 찾아 사용하도록 변경
  - `scripts/smoke-test.ps1`: 스모크 테스트 백엔드 실행과 샘플 PDF 생성에 Python 3.13.13 사용
  - `scripts/manage-servers.ps1`, `scripts/smoke-test.ps1`: Windows `cmd.exe` 환경변수 설정을 `set "KEY=value"` 방식으로 수정해 `PYTHONUTF8` 공백 오류 해결
  - `backend/app/pipelines/ocr.py`: OCR 의존성 누락 메시지를 Python 3.13 런타임 기준으로 수정
  - `backend/requirements-ocr.txt`: OCR 의존성 설치 기준을 Python 3.13.13으로 명시
- 검증 결과
  - `py -3.13 -c "import sys; print(sys.version); print(sys.executable)"`: `3.13.13`, `C:\Python313\python.exe` 확인
  - 오래된 Python 버전/venv 기준 문구 검색 결과: 없음
  - 실제 사업자등록증 OCR 테스트: 통과
  - 전체 백엔드 단위 테스트: 16개 통과, 1개 선택 OCR 테스트 skip
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 확인

## Additional Update (2026-05-10)
- Standardized project documentation and execution scripts on `Python 3.13.13`.
- Runtime standard:
  - Windows command: `py -3.13`
  - executable: `C:\Python313\python.exe`
  - repository marker: `.python-version`
- Updated documents:
  - `README.md`: backend stack, install/run/test commands, and OCR runtime notes now use Python 3.13.13
  - `AGENTS.md`: added Python 3.13.13 runtime guardrails for future agents
  - `docs/technical-design.md`: updated backend/OCR runtime standard
  - `docs/technology-summary.md`: changed backend stack to Python 3.13.13
  - `docs/ai-api-setup.md`: changed dependency install commands to `py -3.13`
  - `docs/ocr-engine-implementation-plan.md`: replaced old venv-oriented guidance with the Python 3.13.13 runtime standard
  - `docs/work-log.md`: added this work entry and normalized historical execution commands to the current standard where appropriate
- Updated code/scripts:
  - added `.python-version`
  - `scripts/manage-servers.ps1`: backend startup now resolves `py -3.13` or `C:\Python313\python.exe`
  - `scripts/smoke-test.ps1`: backend startup and sample PDF generation now use Python 3.13.13
  - `scripts/manage-servers.ps1` and `scripts/smoke-test.ps1`: fixed Windows `cmd.exe` env var assignment with `set "KEY=value"` to avoid invalid `PYTHONUTF8` values
  - `backend/app/pipelines/ocr.py`: updated missing OCR dependency message to reference the Python 3.13 runtime
  - `backend/requirements-ocr.txt`: documented Python 3.13.13 as the OCR dependency runtime
- Verification:
  - `py -3.13 -c "import sys; print(sys.version); print(sys.executable)"`: confirmed `3.13.13` and `C:\Python313\python.exe`
  - stale Python/venv wording search: no matches
  - real business-registration OCR test: passed
  - full backend unit test suite: 16 passed, 1 optional OCR test skipped
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test

## 추가 업데이트 (2026-05-10)
- Phase 1.6A 개발을 시작했고, `증빙자료 기반 법인 등록 MVP`의 1차 구현을 완료했다.
- 백엔드 구현
  - `corporation_evidence_documents` 테이블 추가
  - `corporation_profile_update_candidates` 테이블 추가
  - 기존 `corporations` 테이블에 사업자등록번호, 대표자, 법인등록번호, 사업장 주소, 본점 주소, 개업일, 업태, 종목, 증빙 검증 상태 컬럼 추가
  - `backend/app/pipelines/corporation_evidence.py` 신규 추가
  - 사업자등록증명/사업자등록증 규칙 기반 분류 구현
  - 법인명, 사업자등록번호, 대표자, 법인등록번호, 개업연월일, 사업장 주소, 지역, 업태/종목 후보 추출 구현
  - PDF/DOCX는 기존 파서 재사용, 이미지 파일은 OCR 파이프라인 사용
  - 증빙자료 업로드 API 추가
  - 증빙자료 상세/목록/삭제 API 추가
  - 추출 후보 승인 시 기존 법인 업데이트 또는 새 법인 생성 API 추가
- 프론트엔드 구현
  - 법인 관리 화면 상단을 `증빙자료 먼저 업로드` UX로 변경
  - 기존 법인 연결 또는 새 법인 생성 예정 선택 지원
  - 증빙서류 유형 자동 분류/수동 지정 선택 지원
  - 추출 후보 카드 UI 추가
  - `추출값 승인 및 반영` 액션 추가
  - 법인 목록에 사업자등록번호, 대표자, 증빙 확인 상태 표시 추가
  - 법인 편집 폼에 사업자등록번호, 대표자, 사업장 주소 필드 추가
- 테스트 추가/수정
  - `backend/tests/test_corporation_evidence.py` 신규 추가
  - 사업자등록증 규칙 기반 핵심 필드 추출 테스트 추가
  - 알 수 없는 증빙자료는 확인 필요 상태로 남기는 테스트 추가
  - `backend/tests/test_api_flows.py`에 증빙자료 업로드 후 후보 추출/승인/새 법인 생성 테스트 추가
  - 기존 법인에 증빙자료 승인값을 반영하는 API 테스트 추가
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 20개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 확인
- 다음 단계
  - Phase 1.6A-2: 이미지 사업자등록증 업로드 UX 실사용 검증과 OCR 결과 보정 UX 추가
  - Phase 1.6A-3: 후보값 개별 승인/거절, 수동 수정 후 승인 기능 고도화
  - Phase 1.6B: 중소기업확인서, 여성기업확인서, 장애인기업확인서, 직접생산확인증명서 등 주요 증빙자료 확장

## Additional Update (2026-05-10)
- Started Phase 1.6A implementation and completed the first MVP slice for evidence-based corporation onboarding.
- Backend:
  - added `corporation_evidence_documents`
  - added `corporation_profile_update_candidates`
  - extended `corporations` with business registration number, representative name, corporate registration number, business/headquarters address, opening date, business type/item, and evidence verification status
  - added `backend/app/pipelines/corporation_evidence.py`
  - implemented rule-based business registration proof/certificate classification
  - implemented extraction candidates for corporation name, business registration number, representative, corporate registration number, opening date, address, region, business type, and business item
  - reused existing PDF/DOCX parsing and image OCR pipelines
  - added evidence upload, list/detail/delete APIs
  - added approval API that updates an existing corporation or creates a new corporation from approved candidates
- Frontend:
  - changed the corporation page to evidence-first onboarding
  - supports linking evidence to an existing corporation or preparing a new corporation
  - supports auto/manual evidence type selection
  - added extraction candidate cards
  - added approve-and-apply action
  - added business registration number, representative, and evidence verification status to the corporation list
  - added business registration number, representative, and business address to the edit form
- Tests:
  - added `backend/tests/test_corporation_evidence.py`
  - added business registration extraction tests
  - added unknown evidence review-state test
  - extended API flow tests for evidence upload, candidate extraction, approval, new corporation creation, and existing corporation update
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 20 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test
- Next:
  - Phase 1.6A-2: validate real image business-registration uploads and add OCR correction UX
  - Phase 1.6A-3: improve per-candidate approve/reject and manual correction before approval
  - Phase 1.6B: expand rules for SME, women-owned, disabled-owned, direct production, and other core procurement evidence

## 추가 업데이트 (2026-05-10)
- Phase 1.6A 코드 리뷰를 다시 진행하고, 발견된 결함을 먼저 수정했다.
- 리뷰 후 수정한 내용
  - 사용자가 증빙서류 유형을 수동으로 `사업자등록증/사업자등록증명`으로 지정해도 자동 분류 결과가 `unknown`이면 추출 후보가 비어버릴 수 있는 문제를 수정했다.
  - 수동 지정 유형이 자동 분류보다 우선 적용되도록 `requested_document_type` 흐름을 백엔드 파이프라인과 업로드 API에 반영했다.
  - 중소기업확인서처럼 사업자등록번호/대표자 정보가 포함된 증빙서류가 넓은 사업자등록증 규칙에 먼저 걸려 오분류될 수 있는 문제를 수정했다.
  - `certifications_json` 같은 목록형 법인 프로필 값이 증빙 승인 시 기존 값을 덮어쓰는 문제를 방지하기 위해 병합 로직을 추가했다.
- Phase 1.6B 개발 내용
  - 중소기업확인서, 여성기업확인서, 장애인기업확인서, 직접생산확인증명서, 나라장터 경쟁입찰참가자격 등록증, 주요 면허/등록증 분류 규칙을 추가했다.
  - 주요 증빙서류에서 `certifications_json`, `company_size_classification`, `preference_tags_json`, `direct_production_items_json`, `license_summary`, `procurement_registration_status`, `evidence_expiry_summary` 후보값을 추출하도록 확장했다.
  - 법인 DB 스키마에 우대/제한 태그, 직접생산 품목, 면허 요약, 조달 등록 상태, 증빙 만료 요약 컬럼을 추가했다.
  - 증빙 승인 시 기존 법인 정보와 신규 추출값을 안전하게 병합하도록 백엔드 반영 로직을 보강했다.
  - 법인 관리 포탈의 증빙 업로드 유형 선택지를 주요 조달 증빙서류까지 확장했다.
  - 법인 목록과 편집 UX에서 우대/제한 태그, 직접생산 품목, 면허 요약을 확인/수정할 수 있도록 업데이트했다.
- 테스트 추가/수정
  - 수동 증빙 유형 지정 시에도 사업자등록증 후보가 추출되는 테스트를 추가했다.
  - 중소기업확인서에서 기업규모/우대 태그/인증 후보가 추출되는 테스트를 추가했다.
  - 여성기업확인서, 직접생산확인증명서, 경쟁입찰참가자격 등록증, 면허/등록증 추출 테스트를 추가했다.
  - 증빙 승인 시 기존 인증 목록을 보존하면서 신규 인증/우대 태그를 병합하는 API 테스트를 추가했다.
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 25개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 상태 확인
- 다음 단계
  - Phase 1.6B-2: OCR 결과 보정 UX와 후보값 개별 승인/거절 기능 고도화
  - Phase 1.6B-3: 실제 증빙서류 샘플을 추가해 추출 규칙 정밀도 보정
  - Phase 1.7 후보: 공고 요구조건과 법인 프로필 필드 간 비교 준비 화면 설계

## Additional Update (2026-05-10)
- Re-reviewed Phase 1.6A code and fixed review findings before continuing Phase 1.6B.
- Review fixes:
  - fixed a manual evidence-type override bug where candidates could be empty when auto-classification returned `unknown`
  - wired `requested_document_type` through the upload API and extraction pipeline
  - fixed classifier precedence so SME-style documents are not incorrectly classified as business registration documents only because they contain business registration numbers and representatives
  - added safe merge logic for list-style corporation profile fields such as `certifications_json`
- Phase 1.6B implementation:
  - added classification rules for SME confirmation, women-owned confirmation, disabled-owned confirmation, direct production confirmation, procurement registration certificates, and major license/registration certificates
  - expanded extraction candidates for `certifications_json`, `company_size_classification`, `preference_tags_json`, `direct_production_items_json`, `license_summary`, `procurement_registration_status`, and `evidence_expiry_summary`
  - extended the corporation schema with preference tags, direct production items, license summary, procurement registration status, and evidence expiry summary
  - strengthened approval logic so extracted evidence updates merge safely into existing corporation profiles
  - expanded the corporation portal evidence-type selector for core procurement evidence documents
  - updated corporation list/edit UX for preference tags, direct production items, and license summary
- Tests:
  - added manual evidence-type extraction coverage
  - added SME confirmation extraction coverage
  - added women-owned, direct-production, procurement-registration, and license extraction coverage
  - added API coverage for merging existing certifications with new evidence-derived certifications and preference tags
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 25 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test

## 추가 업데이트 (2026-05-10 23:02:49 +09:00)
- 요청 범위
  - 나라장터 `공고 상세 저장`을 페이지 이동과 무관하게 계속 진행되는 백그라운드 작업 구조로 변경했다.
- 수정 내용
  - `/api/nara/notices/save-and-analyze` API가 오래 대기하지 않고 `202 queued`로 즉시 응답하도록 변경했다.
  - 공고는 먼저 DB에 `save_status=saving`, `download_status=pending`, `analysis_status=pending` 상태로 저장된다.
  - 서버 단일 백그라운드 워커가 공고 상세 조회, 첨부 다운로드, PDF/DOCX 파싱, OCR 필요 여부 판단, AI 요약, 요구조건 후보 추출을 이어서 처리한다.
  - SQLite 연결을 요청/작업 단위 커넥션으로 바꿔 백그라운드 처리 중 상세 화면 조회가 가능하도록 했다.
  - 저장 공고 상세 화면은 처리 중 상태에서 2초마다 자동 갱신한다.
  - 나라장터 공고 목록 저장 버튼 문구를 `작업 등록 중...`으로 변경하고, 저장 직후 `처리 상태 보기` 링크를 제공한다.
  - 공고 재분석도 동일하게 백그라운드 큐에 등록되도록 변경했다.
- 테스트/검증
  - 비동기 저장 API 테스트를 `202 queued -> 상세 polling -> completed/partial_failed` 흐름으로 수정했다.
  - `py -3.13 -m unittest discover -s tests -v`: 42개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공

## Additional Update (2026-05-10 23:02:49 +09:00)
- Scope
  - Converted Nara `save and analyze notice` into a background-processing flow that continues after page navigation.
- Changes
  - `/api/nara/notices/save-and-analyze` now returns immediately with `202 queued`.
  - Notices are first persisted with `save_status=saving`, `download_status=pending`, and `analysis_status=pending`.
  - A single backend worker continues detail fetch, attachment download, PDF/DOCX parsing, OCR handling, AI summary, and requirement candidate extraction.
  - SQLite now uses per-operation connections so detail polling can continue while the worker processes the notice.
  - Saved notice detail page polls every 2 seconds while the pipeline is running.
  - Nara board copy now reflects background job registration and links to the processing status page.
  - Saved notice reanalysis also uses the same background queue.
- Verification
  - Updated async API test to assert `202 queued`, then poll saved notice detail until final status.
  - `py -3.13 -m unittest discover -s tests -v`: 42 passed, 1 optional OCR test skipped
  - `npm run build`: passed

## 추가 업데이트 (2026-05-10 23:15:05 +09:00)
- 요청 범위
  - 사업자등록증 이미지 OCR 결과에서 `사업의 종류 / 업태 / 종목` 표가 깨지는 문제를 개선했다.
- 수정 내용
  - 규칙 기반 후처리에 사업자등록증 `사업의 종류` 표 전용 정규화 로직을 추가했다.
  - `전문기\n업` -> `전문기업`, `도매 및\n소매업` -> `도매 및 소매업`처럼 OCR 줄깨짐을 보정한다.
  - `업태`는 `건설업`, `도소매`, `도매 및 소매업` 같은 큰 분류로 정리하고, `종목`은 세부 항목 목록으로 분리한다.
  - AI API 키가 설정되어 있으면 사업자등록증 OCR 텍스트를 LLM으로 한 번 더 정리해 `business_type`, `business_item`, `business_category` 후보를 덮어쓴다.
  - LLM은 없는 값을 만들지 않고, 사용자 검토용 후보로만 저장되며 `AI 업태/종목 정리` warning을 남긴다.
- 테스트/검증
  - 깨진 OCR 샘플 텍스트 기반 규칙 보정 테스트 추가
  - LLM 정규화 hook 테스트 추가
  - `py -3.13 -m unittest discover -s tests -v`: 44개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공

## Additional Update (2026-05-10 23:15:05 +09:00)
- Scope
  - Improved business registration OCR handling for broken `business type / business item` tables.
- Changes
  - Added business-registration-specific rule cleanup for the `사업의 종류` table.
  - Repairs OCR line breaks such as `전문기\n업` -> `전문기업` and `도매 및\n소매업` -> `도매 및 소매업`.
  - Separates coarse business type values from detailed business item values.
  - When an AI key is configured, the OCR text is sent through an LLM cleanup pass that replaces `business_type`, `business_item`, and `business_category` review candidates.
  - LLM cleanup remains a review-candidate step and records an `AI business type/item cleanup` warning.
- Verification
  - Added rule-based broken OCR table test.
  - Added LLM cleanup hook test.
  - `py -3.13 -m unittest discover -s tests -v`: 44 passed, 1 optional OCR test skipped
  - `npm run build`: passed

## 추가 업데이트 (2026-05-10 22:49:01 +09:00)
- 요청 범위
  - UX/사용성 개선 포인트 1~5번을 모두 실제 코드에 반영했다.
- 수정 내용
  - 법인 관리 화면을 `증빙 업로드`, `추출값 검토`, `증빙자료 관리`, `법인 목록/준비도` 탭형 워크스페이스로 재구성했다.
  - 증빙자료 상세 검토를 별도 탭으로 분리하고, 재처리/보정 텍스트 재분석/선택 반영의 차이를 설명하는 안내 카드를 추가했다.
  - 추출 후보 카드에 `기존값`과 `추출값` 비교 영역을 추가해 승인 전 덮어쓰기 위험을 더 쉽게 확인하도록 했다.
  - 대시보드에 `오늘 처리할 큐` 영역을 추가해 증빙 검토 대기, OCR/추출 보정 필요, 낮은 준비도 법인, 요구조건 추출 완료 공고를 바로 볼 수 있게 했다.
  - 나라장터 공고 목록의 `공고 상세 저장` 버튼을 테이블 상단 sticky 액션바로 이동해, 선택한 공고와 저장 액션의 맥락을 분명히 했다.
- 검증 결과
  - `npm run build`: 성공
  - `py -3.13 -m unittest discover -s tests -v`: 42개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인

## Additional Update (2026-05-10 22:49:01 +09:00)
- Scope
  - Implemented all requested UX improvement items 1 through 5.
- Changes
  - Reworked the corporation page into a tabbed workspace: evidence upload, extraction review, evidence library, and corporation directory/readiness.
  - Moved evidence review into a clearer dedicated flow and added help cards explaining reprocess, corrected-text reanalysis, and selected candidate application.
  - Added current profile value vs extracted value comparison to each extraction candidate card.
  - Added a dashboard `Today Queue` section for pending evidence review, OCR/extraction correction needs, low-readiness corporations, and notices with extracted requirement candidates.
  - Moved the Nara board `Save notice detail` action into a sticky action bar above the result table.
- Verification
  - `npm run build`: passed
  - `py -3.13 -m unittest discover -s tests -v`: 42 passed, 1 optional OCR test skipped
  - `git diff --check`: no whitespace errors; only Windows CRLF warnings

## 추가 업데이트 (2026-05-10 22:11:10 +09:00)
- 사용자 요청에 따라 Step 1부터 Step 5까지 순차 개발을 진행했고, 각 step 종료 시 테스트와 코드리뷰 관점 검토를 수행했다.
- Step 1: 증빙서류 추출 룰 튜닝
  - 신용평가, 국세/지방세 납세, 4대보험 완납, 실적증명, 재무/매출 증빙 문서 유형을 규칙 기반 분류/추출 범위에 포함했다.
  - 기존 AI fallback 테스트 샘플이 새 룰에 정상 분류되는 충돌을 발견하고, 진짜 미분류 문서 샘플로 테스트 의도를 보정했다.
- Step 2: 증빙자료 관리 UX 확장
  - 증빙자료 전체 목록 API를 후보 수, 승인 후보 수, 연결 법인명과 함께 내려주도록 확장했다.
  - 증빙자료 메타데이터 수정 API와 재처리 API를 추가했다.
  - 포탈 법인 관리 화면에 증빙자료 관리 테이블, 상세 검토, 메타데이터 저장, 재처리, 삭제 액션을 추가했다.
- Step 3: OCR 보정 UX
  - OCR/파싱 텍스트를 사용자가 직접 수정한 뒤 해당 텍스트 기준으로 다시 분류/추출하는 API를 추가했다.
  - 상세 검토 화면에 `OCR/파싱 텍스트 보정` 영역과 재분석 버튼을 추가했다.
- Step 4: 법인 프로필 준비도 화면
  - 법인 정보와 승인된 증빙 후보를 기반으로 `프로필 준비도` 점수, 누락 항목, 증빙 수를 계산하는 API를 추가했다.
  - 법인 관리 화면에 준비도 카드를 추가했다.
  - 준비도는 최종 지원 가능/불가능 판정이 아니라 판단 준비 상태 안내로 제한했다.
- Step 5: 공고 요구조건 추출 강화
  - 나라장터 저장 공고 분석 결과에 `notice_requirements` 구조를 추가했다.
  - 지역, 면허/업종, 기업유형, 제출/증빙서류, 금액, 주요 일정을 후보값으로 추출한다.
  - 저장 공고 상세 화면에 `요구조건 구조화 후보` 카드를 추가했다.
- 문서 업데이트
  - `docs/technical-design.md`: Phase 1.6 현재 구현 상태와 파이프라인 설명 갱신
  - `docs/ux-design.md`: 증빙자료 관리, OCR 보정, 준비도 카드, 공고 요구조건 후보 UX 반영
  - `docs/work-log.md`: 현재 작업 내역 기록
- 검증 결과
  - `py -3.13 -m unittest discover -s backend\tests -v`: 39개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공

## Additional Update (2026-05-10 22:11:10 +09:00)
- Implemented user-requested Steps 1 through 5 sequentially, with tests and review after each step.
- Step 1: expanded corporation evidence extraction rules for credit rating, tax/local tax, insurance payment, performance, and financial/revenue evidence.
- Step 2: added evidence list enrichment, metadata update, reprocess API, and portal management UX.
- Step 3: added corrected OCR/parser text reanalysis API and portal correction UX.
- Step 4: added corporation readiness API and cards that show missing inputs only, not eligibility verdicts.
- Step 5: added Nara notice requirement candidate extraction under `analysis_summary_json.notice_requirements` and rendered it on the saved notice detail page.
- Documentation updated:
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `docs/work-log.md`
- Verification:
  - `py -3.13 -m unittest discover -s backend\tests -v`: 39 passed, 1 optional OCR test skipped
  - `npm run build`: passed

## 추가 업데이트 (2026-05-10 22:23:25 +09:00)
- 사용자 요청에 따라 전체 코드리뷰를 진행했고, 직전 구현 범위인 증빙자료 관리, OCR 보정, 법인 준비도, 나라장터 요구조건 추출을 집중 검토했다.
- 리뷰에서 수정한 사항
  - Gemini 기본 모델은 `gemini-2.5-flash`인데 포탈 fallback 옵션과 백엔드 모델 옵션 라벨에 `Flash-Lite`가 남아 있던 표시 불일치를 수정했다.
  - 증빙자료 재처리/보정 재분석 시 이미 승인된 동일 후보값이 다시 pending 후보로 중복 생성될 수 있는 흐름을 방지했다.
- 새로 추가한 테스트
  - AI 모델 설정 응답이 `gemini-2.5-flash`를 올바르게 표시하고 `Flash-Lite` 잔여 라벨을 노출하지 않는지 검증
  - 증빙자료 재처리 시 승인된 후보는 보존하고 동일 pending 후보를 중복 생성하지 않는지 검증
  - OCR/파싱 보정 텍스트가 비어 있으면 재분석을 거부하는지 검증
  - 공고 요구조건 추출이 지역, 면허, 기업유형, 제출서류 후보를 추출하되 지원 가능 판정 문구를 만들지 않는지 검증
- 검증 결과
  - `py -3.13 -m unittest discover -s backend\tests -v`: 42개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인

## Additional Update (2026-05-10 22:23:25 +09:00)
- Performed a full code review focused on the latest evidence management, OCR correction, corporation readiness, and Nara requirement extraction work.
- Fixes:
  - corrected stale `Flash-Lite` labels for the current `gemini-2.5-flash` model
  - prevented reprocess/corrected-text reanalysis from recreating identical pending candidates that were already approved
- Added tests:
  - AI model label/default regression
  - evidence reprocess preserves approved candidates without duplicate pending values
  - corrected OCR/parser text requires non-empty input
  - Nara requirement extraction returns candidates without eligibility verdict wording
- Verification:
  - `py -3.13 -m unittest discover -s backend\tests -v`: 42 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `git diff --check`: no whitespace errors; Windows CRLF warnings only

## 추가 업데이트 (2026-05-10)
- OpenAI API 권장 모델 설정을 현재 무료 일일 사용량 정책에 맞춰 조정했다.
- 변경 내용
  - 기본 요약 모델을 `gpt-5.4-mini`로 변경
  - 정밀 보조 모델 설정값을 `gpt-5.4`로 추가/정리
  - `backend/.env.example`, `backend/app/main.py`, `README.md`, `docs/ai-api-setup.md`, `docs/technical-design.md`, `docs/technology-summary.md`, `docs/narajangteo-api-test-result-20260505.md`의 모델 표기를 정리
  - `docs/ai-api-setup.md`에 API 키 입력 위치, 한 줄 입력 규칙, 서버 재시작 필요사항을 추가
- 설정 확인
  - `backend/.env`에 `OPENAI_API_KEY`가 설정되어 있는지 확인했다.
  - 실제 키 값은 출력하지 않았고, 설정 여부와 길이만 확인했다.
  - `OPENAI_MODEL_PRIMARY=gpt-5.4-mini`, `OPENAI_MODEL_SECONDARY=gpt-5.4` 설정을 확인했다.
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 30개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인

## Additional Update (2026-05-10)
- Updated the recommended OpenAI model configuration based on the current free daily shared-traffic allowance.
- Changes:
  - set the primary summarization model to `gpt-5.4-mini`
  - added/normalized the precision secondary model setting as `gpt-5.4`
  - updated model references in `backend/.env.example`, `backend/app/main.py`, `README.md`, `docs/ai-api-setup.md`, `docs/technical-design.md`, `docs/technology-summary.md`, and `docs/narajangteo-api-test-result-20260505.md`
  - documented where to put the OpenAI API key, the single-line `.env` rule, and the need to restart the backend after changes
- Configuration check:
  - confirmed that `backend/.env` contains an `OPENAI_API_KEY` entry without exposing the actual secret
  - confirmed `OPENAI_MODEL_PRIMARY=gpt-5.4-mini` and `OPENAI_MODEL_SECONDARY=gpt-5.4`
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 30 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `git diff --check`: no whitespace errors; only Windows CRLF warnings

## 추가 업데이트 (2026-05-10)
- 사용자가 입력한 OpenAI API 키 동작 여부를 재확인했다.
- 백엔드 서버를 포트 `18111`에서 재실행했고 `/health` 응답이 `ok`인지 확인했다.
- 키 값은 출력하지 않고 `backend/.env`의 설정 여부와 모델 설정만 확인했다.
- OpenAI 최소 JSON 응답 테스트를 `gpt-5.4-mini`로 재시도했다.
- 결과
  - 백엔드 서버 상태: 정상
  - API 키 로딩: 정상
  - OpenAI 응답: `RateLimitError`, HTTP `429`, code `insufficient_quota`
- 판단
  - 현재 문제는 서버 재시작/환경변수 반영 문제가 아니라 OpenAI 프로젝트의 사용 가능 쿼터, 결제, 예산 한도 또는 프로젝트 사용 제한 문제로 보인다.

## Additional Update (2026-05-10)
- Retried the OpenAI API key connectivity check after restarting the backend server.
- Restarted the backend on port `18111` and confirmed `/health` returns `ok`.
- Did not print the secret key; only verified key presence and model configuration.
- Retried a minimal JSON response request with `gpt-5.4-mini`.
- Result:
  - backend server: healthy
  - API key loading: successful
  - OpenAI response: `RateLimitError`, HTTP `429`, code `insufficient_quota`
- Assessment:
  - This is not a backend restart or environment loading issue. It appears to be an OpenAI project quota, billing, budget-limit, or usage-limit issue.

## 추가 업데이트 (2026-05-10)
- AI API 구조를 OpenAI 단일 호출에서 Gemini/OpenAI 동시 지원 구조로 변경했다.
- 백엔드 변경
  - 기본 Provider/모델을 `gemini` / `gemini-2.5-flash-lite`로 변경
  - `google-genai==2.0.1` 의존성 추가
  - `GEMINI_API_KEY`, `GEMINI_MODEL_PRIMARY`, `AI_PROVIDER_DEFAULT`, `AI_MODEL_DEFAULT` 환경변수 추가
  - 기존 `OPENAI_API_KEY`, `OPENAI_MODEL_PRIMARY`, `OPENAI_MODEL_SECONDARY`는 보조 Provider로 유지
  - `/api/settings/ai-models` API 추가: 키 설정 여부, 마스킹 키, 선택 가능한 모델 목록 제공
  - 문서 분석/재분석 API와 나라장터 저장/재분석 API가 `model_provider`, `model_name` 선택값을 받도록 변경
  - 캐시 조회 기준을 `input_hash + prompt_version + model_provider + model_name`으로 강화
  - 선택 Provider 키가 없거나 호출 실패 시 기존 fallback 요약으로 안전하게 전환
- 프론트엔드 변경
  - 문서 이력 화면, 분석 결과 화면, 나라장터 공고 검색 저장 액션, 저장 공고 상세 재분석에 AI 모델 선택 UI 추가
  - 선택값은 localStorage에 저장해 다음 분석에서도 유지
  - 설정 화면에서 Gemini/OpenAI 키 설정 여부와 기본 모델을 확인할 수 있도록 추가
- 문서 변경
  - `README.md`, `docs/ai-api-setup.md`, `docs/technical-design.md`, `docs/technology-summary.md`, `docs/narajangteo-api-test-result-20260505.md` 업데이트
- 검증 결과
  - `py -3.13 -m pip install -r backend/requirements.txt`: 성공
  - `py -3.13 -m unittest discover -s tests -v`: 32개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - Gemini SDK 더미 키 테스트: SDK 호출 파라미터는 정상이며, 예상대로 `API key not valid` 응답 확인

## Additional Update (2026-05-10)
- Changed the AI API architecture from OpenAI-only to dual Gemini/OpenAI support.
- Backend changes:
  - default provider/model is now `gemini` / `gemini-2.5-flash-lite`
  - added `google-genai==2.0.1`
  - added `GEMINI_API_KEY`, `GEMINI_MODEL_PRIMARY`, `AI_PROVIDER_DEFAULT`, and `AI_MODEL_DEFAULT`
  - kept `OPENAI_API_KEY`, `OPENAI_MODEL_PRIMARY`, and `OPENAI_MODEL_SECONDARY` as secondary provider settings
  - added `/api/settings/ai-models` for masked key status and selectable model options
  - document analysis/re-analysis and Nara save/re-analysis APIs now accept `model_provider` and `model_name`
  - cache lookup now includes `input_hash + prompt_version + model_provider + model_name`
  - missing key or provider failure falls back to the deterministic local summary
- Frontend changes:
  - added AI model selectors to document history, analysis result, Nara notice save/analyze, and saved notice re-analysis flows
  - persisted model selection in localStorage
  - added Gemini/OpenAI configuration status to the settings page
- Documentation:
  - updated `README.md`, `docs/ai-api-setup.md`, `docs/technical-design.md`, `docs/technology-summary.md`, and `docs/narajangteo-api-test-result-20260505.md`
- Verification:
  - `py -3.13 -m pip install -r backend/requirements.txt`: passed
  - `py -3.13 -m unittest discover -s tests -v`: 32 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - Gemini SDK dummy-key call reached the API and returned the expected invalid-key response, confirming the SDK call shape is valid

## 추가 업데이트 (2026-05-10)
- 사용자가 입력한 Gemini API 키 동작 여부를 확인했다.
- 키 값은 출력하지 않고 `GEMINI_API_KEY` 설정 여부와 길이만 확인했다.
- 백엔드의 실제 `summarize_with_ai` 경로로 `gemini-2.5-flash-lite` 최소 조달문서 요약 호출을 실행했다.
- 결과
  - `GEMINI_API_KEY`: 설정됨
  - Provider: `gemini`
  - Model: `gemini-2.5-flash-lite`
  - 호출 결과: 성공
  - 요약 JSON과 Markdown 출력 생성 확인
- 참고
  - 이미 실행 중인 백엔드 서버가 있다면 `.env` 변경 반영을 위해 서버 재시작이 필요하다.

## Additional Update (2026-05-10)
- Verified the Gemini API key entered by the user.
- Did not print the secret value; only checked key presence and length.
- Ran a minimal Korean procurement summary request through the backend `summarize_with_ai` path using `gemini-2.5-flash-lite`.
- Result:
  - `GEMINI_API_KEY`: configured
  - provider: `gemini`
  - model: `gemini-2.5-flash-lite`
  - API call: successful
  - structured JSON and Markdown summary were generated
- Note:
  - If a backend server is already running, restart it so the new `.env` value is loaded.

## 추가 업데이트 (2026-05-10)
- 사용 요청에 따라 Gemini 기본 모델 후보를 `gemini-2.5-flash`로 먼저 실제 호출 테스트했다.
- 테스트 결과
  - `gemini-2.5-flash`: 호출 성공
  - JSON 응답 생성 성공
- 호출 성공에 따라 기본 Gemini 모델을 `gemini-2.5-flash-lite`에서 `gemini-2.5-flash`로 변경했다.
- 변경 범위
  - `backend/.env`
  - `backend/.env.example`
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/aiModel.ts`
  - `README.md`
  - `docs/ai-api-setup.md`
  - `docs/technical-design.md`
  - `docs/technology-summary.md`
  - `docs/narajangteo-api-test-result-20260505.md`
- 참고
  - 이미 실행 중인 백엔드 서버가 있으면 기본 모델 변경 반영을 위해 재시작이 필요하다.

## Additional Update (2026-05-10)
- Tested `gemini-2.5-flash` as the requested Gemini default model candidate before changing configuration.
- Test result:
  - `gemini-2.5-flash`: call succeeded
  - JSON response generation succeeded
- Because the call succeeded, changed the default Gemini model from `gemini-2.5-flash-lite` to `gemini-2.5-flash`.
- Updated:
  - `backend/.env`
  - `backend/.env.example`
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/aiModel.ts`
  - `README.md`
  - `docs/ai-api-setup.md`
  - `docs/technical-design.md`
  - `docs/technology-summary.md`
  - `docs/narajangteo-api-test-result-20260505.md`
- Note:
  - Restart any running backend server so the changed default model is loaded.

## 추가 업데이트 (2026-05-10)
- Phase 1.6B의 추출 후보 검토 UX를 개선했다.
- 변경 내용
  - 법인 증빙자료 업로드 후 자동 추출 후보를 체크박스 기반으로 선택할 수 있게 변경
  - 후보값을 법인 프로필에 반영하기 전에 사용자가 직접 수정할 수 있는 입력 필드 추가
  - `전체 선택`, `선택 해제`, `N개 선택 반영` 액션 추가
  - 선택하지 않은 후보는 보류 상태로 남기고 법인 프로필에 반영하지 않도록 UX를 변경
  - 모바일 화면에서 후보 검토 카드가 1열로 접히도록 반응형 스타일 추가
- 테스트 보강
  - 선택한 후보만 반영되고 수정 입력값이 우선 적용되는 백엔드 회귀 테스트 추가
- 문서 업데이트
  - `docs/ux-design.md`: 현재 구현된 필드별 선택/수정 후보 검토 UX 반영
  - `docs/corporation-evidence-auto-extraction-plan.md`: 선택 후보만 반영하는 가드레일과 테스트 항목 추가
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 33개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공

## Additional Update (2026-05-10)
- Improved the Phase 1.6B extraction candidate review UX.
- Changes:
  - extracted evidence candidates can now be selected with checkboxes
  - candidate values can be corrected before applying them to the corporation profile
  - added select-all, clear-selection, and selected-count apply actions
  - unselected candidates remain pending and are not applied to the corporation profile
  - added responsive single-column candidate cards for smaller screens
- Test coverage:
  - added a backend regression test proving only selected candidates are applied and edited values take precedence
- Documentation:
  - updated `docs/ux-design.md` with the implemented per-field candidate review UX
  - updated `docs/corporation-evidence-auto-extraction-plan.md` with the selected-candidates-only guardrail and test item
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 33 passed, 1 optional OCR test skipped
  - `npm run build`: passed

## 추가 업데이트 (2026-05-10)
- Phase 1.6C의 알 수 없는 증빙서류 AI 분류 fallback을 백엔드에 추가했다.
- 변경 내용
  - 규칙 기반 증빙서류 분류가 실패하고 추출 텍스트가 존재할 때만 LLM 분류를 시도
  - Gemini/OpenAI 공통 Provider abstraction을 사용하며 현재 기본 모델은 `gemini-2.5-flash`
  - LLM 응답은 문서 유형, 분류 신뢰도, 법인 프로필 후보 필드, 경고 목록 JSON으로 파싱
  - 지원하지 않는 문서 유형/필드 키는 저장하지 않도록 검증
  - LLM 결과는 `ai_suggested` 상태로 저장하고 자동 확정하지 않음
  - LLM 후보도 필드별 체크/수정/선택 반영 UX를 거쳐야 법인 프로필에 반영
  - API 키가 없거나 LLM 호출이 실패하면 기존 `needs_review` 수동 검토 흐름 유지
- 테스트 보강
  - 알 수 없는 증빙서류가 AI 분류 fallback을 통해 `ai_suggested` 후보로 저장되고, 후보 상태가 `pending`으로 유지되는 테스트 추가
- 문서 업데이트
  - `docs/technical-design.md`: 현재 LLM fallback 구현 상태 반영
  - `docs/corporation-evidence-auto-extraction-plan.md`: 구현 조건, 기본 모델, 안전 가드레일, 테스트 항목 반영
  - `docs/ux-design.md`: AI 제안 후보도 동일 검토 UX를 사용한다고 명시
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 34개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공

## Additional Update (2026-05-10)
- Added the Phase 1.6C unknown-evidence AI classification fallback to the backend.
- Changes:
  - attempts LLM classification only when rule-based evidence classification fails and extracted text exists
  - uses the shared Gemini/OpenAI provider abstraction; current default model is `gemini-2.5-flash`
  - parses LLM output into document type, confidence, corporation profile candidates, and warnings
  - rejects unsupported document types or unsupported profile field keys
  - stores LLM results as `ai_suggested`, never as confirmed profile data
  - AI-created candidates must go through the same checkbox/edit/apply review UX before profile updates
  - missing API key or provider failure keeps the evidence in the existing `needs_review` manual flow
- Test coverage:
  - added a backend regression test proving unknown evidence can become `ai_suggested` with pending review candidates
- Documentation:
  - updated `docs/technical-design.md` with the current LLM fallback implementation
  - updated `docs/corporation-evidence-auto-extraction-plan.md` with run conditions, default model, guardrails, and test item
  - updated `docs/ux-design.md` to state that AI-suggested candidates use the same review UX
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 34 passed, 1 optional OCR test skipped
  - `npm run build`: passed

## 추가 업데이트 (2026-05-10)
- 사용자가 확정한 `사업자등록번호 + 관리 법인그룹` 중복 정책을 설계문서, UX문서, 구현에 반영했다.
- 정책 정리
  - 같은 사업자등록번호라도 관리 법인그룹이 다르면 중복 등록을 허용한다.
  - 같은 사업자등록번호와 같은 관리 법인그룹 조합은 중복 법인으로 보고 등록을 차단한다.
  - 다른 관리 법인그룹에 동일 사업자등록번호가 있으면 등록은 허용하되 안내 메시지를 표시한다.
  - 기본 관리 법인그룹 이름은 `기본 관리그룹`으로 둔다.
- 문서 업데이트
  - `docs/technical-design.md`: 법인 관리 필드, 중복 정책, 증빙 승인 파이프라인, AI/Engineering 가정 업데이트
  - `docs/ux-design.md`: 법인 관리 화면, 증빙자료 등록 UX, 법인 선택 UX, 중복 안내 UX 업데이트
  - `docs/corporation-evidence-auto-extraction-plan.md`: Phase 1.6A 범위, 구현 순서, 완료 기준, 테스트 계획 업데이트
- 백엔드 구현
  - `corporations.management_group_name` 컬럼 추가
  - `corporation_evidence_documents.management_group_name` 컬럼 추가
  - 수동 법인 등록 시 동일 사업자등록번호 + 동일 관리그룹 중복 차단
  - 동일 사업자등록번호 + 다른 관리그룹은 허용하고 warning 반환
  - 법인 수정 시에도 같은 중복 정책 적용
  - 증빙자료 승인으로 신규 법인을 생성할 때도 같은 중복 정책 적용
  - 사업자등록번호 포맷 정규화 추가
  - `candidate_ids: []`가 전체 후보 승인으로 처리되지 않도록 보호 로직 추가
- 프론트엔드 구현
  - 법인 직접 등록 폼에 관리 법인그룹 입력 추가
  - 증빙자료 업로드 폼에 관리 법인그룹 입력/자동완성 추가
  - 기존 법인에 증빙자료를 연결하면 해당 법인의 관리그룹을 사용하도록 처리
  - 법인 목록 테이블에 관리그룹 컬럼 추가
  - 중복 사업자등록번호가 다른 그룹에 있을 때 안내 배너 표시
- 테스트 추가
  - 같은 사업자등록번호 + 같은 관리그룹 등록 차단 테스트
  - 같은 사업자등록번호 + 다른 관리그룹 등록 허용 및 warning 테스트
  - 증빙 승인 기반 신규 법인 생성 시 관리그룹 중복 정책 테스트
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 28개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 상태 확인

## Additional Update (2026-05-10)
- Applied the product-approved duplicate policy based on `business_registration_number + management_group_name`.
- Policy:
  - the same business registration number is allowed across different management groups
  - the same business registration number inside the same management group is blocked
  - duplicates in other groups return warnings but do not block creation
  - default management group name is `기본 관리그룹`
- Documentation:
  - updated `docs/technical-design.md`
  - updated `docs/ux-design.md`
  - updated `docs/corporation-evidence-auto-extraction-plan.md`
- Backend:
  - added `management_group_name` to corporations
  - added `management_group_name` to corporation evidence documents
  - implemented duplicate checks for manual create, update, and evidence-approval-created corporations
  - normalized business registration numbers before storage/comparison
  - protected `candidate_ids: []` from being treated as approve-all
- Frontend:
  - added management group input/autocomplete to manual corporation creation
  - added management group input/autocomplete to evidence upload
  - linked evidence uploads use the selected existing corporation's management group
  - added management group column to the corporation table
  - displayed warnings for same registration number in another group
- Tests:
  - same-group duplicate block
  - other-group duplicate warning/allow
  - evidence approval duplicate policy
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 28 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test

## 추가 업데이트 (2026-05-10)
- 현재까지 누적된 코드 수정 내용 전체 리뷰와 설계문서 재검토를 수행했다.
- 코드 리뷰 후 수정
  - 법인 관리 수동 등록 폼 안에 편집용 `관리 법인그룹` 입력이 잘못 들어간 UX 버그를 수정했다.
  - 편집 폼에는 올바른 위치에 `관리 법인그룹` 입력을 배치했다.
  - 증빙 승인 API에서 `candidate_ids: []`가 전달될 때 전체 후보가 승인될 수 있는 방어 취약점을 수정했다.
  - 추출 텍스트가 비어 있거나 OCR/파싱이 실패한 경우, 수동 문서 유형 지정만으로 중소기업/여성기업 등 정적 인증 후보가 생성되지 않도록 수정했다.
- 테스트 보강
  - `candidate_ids: []` + 수동 필드값 승인 시 후보 전체가 승인되지 않는 테스트 추가
  - 빈 텍스트 + 수동 핵심 증빙 유형 지정 시 정적 후보가 생성되지 않는 테스트 추가
- 문서 재검토 및 수정
  - `README.md`: 현재 프론트 실제 의존성에 맞춰 TanStack Query를 활성 기술 스택에서 제거
  - `docs/technical-design.md`: 현재 React state/API 클라이언트 구조와 향후 후보 기술을 구분
  - `docs/technology-summary.md`: 현재 구현 기술과 향후 후보 기술을 구분
  - `docs/technical-design.md`, `docs/corporation-evidence-auto-extraction-plan.md`: 빈 텍스트/파싱 실패 시 후보 생성 금지 정책 추가
  - `docs/technical-design.md`: 이미 확정된 사업자등록번호 필드 질문 제거 및 남은 UX 질문으로 교체
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 30개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 상태 확인

## Additional Update (2026-05-10)
- Performed a full review of accumulated code changes and rechecked design documentation.
- Code fixes:
  - fixed a portal UX bug where the edit-only management group field was accidentally rendered inside the manual-create form
  - placed management group editing in the correct edit form location
  - fixed the approval API so `candidate_ids: []` cannot approve every pending candidate
  - prevented static certification/preference candidates from being generated when extracted text is empty, even if a document type is manually selected
- Tests:
  - added coverage for `candidate_ids: []` with manual field values
  - added coverage for empty-text manual core evidence classification
- Documentation:
  - updated `README.md` to remove TanStack Query from active frontend stack
  - updated `docs/technical-design.md` to distinguish current React state/API-client implementation from future candidates
  - updated `docs/technology-summary.md` to separate active stack from future refactor candidates
  - updated `docs/technical-design.md` and `docs/corporation-evidence-auto-extraction-plan.md` with the empty-text candidate-generation guardrail
  - removed a resolved product question about business registration number inclusion and replaced it with the remaining candidate-review UX question
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 30 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `git diff --check`: no whitespace errors; only Windows CRLF warnings
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test
- Next:
  - Phase 1.6B-2: improve OCR correction UX and per-candidate approve/reject workflow
  - Phase 1.6B-3: tune extraction rules with additional real evidence samples
  - Phase 1.7 candidate: design a preparation screen for comparing notice requirements with corporation profile fields

## 추가 업데이트 (2026-05-10)
- Phase 1.6A + Phase 1.6B 통합 코드 리뷰를 수행했다.
- 검토 범위
  - 증빙자료 업로드 API
  - OCR/파싱 연동
  - 증빙서류 자동 분류/후보 추출 파이프라인
  - 추출 후보 승인 및 법인 프로필 반영 로직
  - 법인 관리 포탈 UX
  - 관련 백엔드 테스트와 프론트엔드 빌드
- 리뷰에서 확인한 주요 개선 필요사항
  - 추출 실패/빈 텍스트 상태에서 수동 문서 유형만으로 인증/우대 후보가 생성될 수 있다.
  - 현재 승인 UX/API는 후보값을 개별 선택/수정하지 않고 전체 적용하므로 기존 법인명/사업자번호 같은 핵심 식별값이 보조 증빙 OCR 오류로 덮일 수 있다.
  - API에서 `candidate_ids: []`가 전달되면 아무것도 승인하지 않는 대신 전체 후보가 승인될 수 있다.
  - 사업자등록번호 기준 중복 법인 방지 로직이 아직 없다.
- 검증 결과
  - `py -3.13 -m unittest discover -s tests -v`: 25개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 성공
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - 스모크 테스트 후 FE/BE 서버 종료 상태 확인

## Additional Update (2026-05-10)
- Performed an integrated code review for Phase 1.6A + Phase 1.6B.
- Review scope:
  - evidence upload API
  - OCR/parsing integration
  - evidence classification and candidate extraction pipeline
  - candidate approval and corporation profile update flow
  - corporation portal UX
  - related backend tests and frontend build
- Key review findings:
  - manual document type selection can create certification/preference candidates even when extraction failed or text is empty
  - the current approval API/UX applies all candidates at once, so supplemental evidence OCR errors can overwrite core identity fields
  - `candidate_ids: []` currently behaves like no filter and may approve all pending candidates
  - duplicate corporation prevention by business registration number is not implemented yet
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 25 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test

## 추가 업데이트 (2026-05-10) - 전역 처리중 UX 적용
- 사용자 액션으로 서버 API 호출이나 긴 처리가 발생하는 지점을 점검했다.
- 공통 UX 컴포넌트 `WorkOverlayProvider` / `useWorkOverlay`를 추가했다.
- 처리 중에는 전체 화면 오버레이, 원형 로딩바, 흐림 배경, 클릭/이동 차단, 단계형 진행 문구를 보여주도록 했다.
- 완료/실패 시 상단 토스트로 결과를 안내하도록 했다.
- 적용한 주요 흐름:
  - 법인/증빙자료: 증빙 업로드 OCR 분석, 추출값 반영, 상세 조회, 메타데이터 저장, 재처리, 보정 텍스트 재분석, 삭제, 법인 등록/수정/삭제, 증빙/준비도 새로고침
  - 나라장터: 공고 검색, 페이지 이동 검색, 공고 상세 저장 작업 등록, 저장 공고 검색/삭제, 저장 공고 재분석
  - 일반 문서: 문서 업로드, 분석, 삭제, 메타데이터 수정, 분석 결과 재분석
  - 프로젝트/설정: 프로젝트 생성/수정/삭제, 설정 새로고침, 나라장터 API 연결 테스트
- 검증 결과:
  - `npm run build`: 통과

## Additional Update (2026-05-10) - Global Processing UX
- Reviewed user-triggered API and long-running processing flows across the portal.
- Added shared `WorkOverlayProvider` / `useWorkOverlay`.
- Processing tasks now show a blocking full-screen overlay with circular spinner, blurred background, staged progress copy, and navigation/click blocking.
- Completion and failure feedback now appears through global toast notifications.
- Applied to corporation evidence, Nara board, saved notices, document upload/analysis, projects, settings, and analysis rerun actions.
- Verification:
  - `npm run build`: passed

## 추가 업데이트 (2026-05-22) - Phase 1.6 안정화 계획 작성
- Phase 2 개발 전에 먼저 수행할 `Phase 1.6 법인 증빙자료 자동 추출 안정화` 계획을 별도 문서로 작성했다.
- 신규 문서:
  - `docs/phase-1.6-stabilization-plan.md`
- 주요 내용:
  - 현재 구현 기준선 정리
  - 안정화 목표와 비범위 명확화
  - OCR/파싱 안정화
  - 사업자등록증 업태/종목 정리 개선 방향
  - LLM 정리 단계 안정화
  - 후보값 안전 반영, 충돌 처리, 핵심 필드 보호
  - 증빙자료 상태/재처리 UX 정리
  - 데이터 무결성, 개인정보/로그 마스킹 점검
  - 샘플 기반 회귀 테스트 계획
  - Phase 1.6 완료 기준과 제품 오너 확인 질문
- README 문서 링크에 Phase 1.6 안정화 계획을 추가했다.
- 검증 결과:
  - 문서 생성 및 링크 업데이트 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-22) - Phase 1.6 Stabilization Plan
- Added a dedicated stabilization plan for Phase 1.6 corporation evidence auto-extraction before Phase 2 begins.
- New document:
  - `docs/phase-1.6-stabilization-plan.md`
- Covered:
  - current implementation baseline
  - stabilization goals and non-scope
  - OCR/parsing stabilization
  - business-registration business type/item cleanup
  - LLM cleanup reliability
  - safe candidate application, conflict handling, and core-field protection
  - evidence status and reprocessing UX
  - data integrity, privacy, and log-masking review
  - sample-based regression testing
  - Phase 1.6 done criteria and product-owner questions
- Added the new document link to `README.md`.
- Verification:
  - confirmed document creation and README link update
  - no runtime code changes

## 추가 업데이트 (2026-05-22) - Phase 1.6 안정화 실행 1차
- Phase 1.6 안정화 계획에 따라 기준선 테스트를 먼저 수행했다.
- 코드 수정:
  - 사업자등록증 `사업의 종류` 영역에서 `사업의`, `종류`, `업태`, `종목` 라벨이 후보값에 섞이지 않도록 후처리를 강화했다.
  - `전문기` + `업`, `도매 및` + `소매업`처럼 OCR 줄바꿈으로 끊어진 값을 자동 결합하도록 보강했다.
  - Gemini/OpenAI가 사업자등록증 업태/종목을 정리한 뒤에도 `business_type`, `business_item`, `business_category` 후보를 다시 sanitize하도록 변경했다.
  - LLM이 `사업의 종류`, `업태`, `종목` 같은 표 라벨을 반환해도 사용자 검토 후보에는 정리된 값만 남도록 방어했다.
- 테스트 추가:
  - 라벨이 여러 줄로 깨진 사업자등록증 OCR 텍스트 회귀 테스트
  - 라벨이 한 줄에 섞인 사업자등록증 OCR 텍스트 회귀 테스트
  - LLM 업태/종목 정리 결과 sanitize 테스트
  - API 레벨 LLM sloppy output sanitize 테스트
  - 실제 사업자등록증 이미지 opt-in OCR 테스트에 후처리 후보 검증 추가
- 문서 업데이트:
  - `docs/phase-1.6-stabilization-plan.md`에 진행 상태를 추가했다.
- UX 수정:
  - 법인 증빙자료 상세/목록/후보 카드에서 `pending`, `skipped`, `classified` 같은 개발자용 상태값을 한국어 배지 라벨로 표시하도록 변경했다.
  - 증빙서류 유형도 코드값 대신 `사업자등록증 사본`, `중소기업확인서`처럼 사용자용 라벨로 표시하도록 정리했다.
- 검증 결과:
  - `py -3.13 -m unittest tests.test_corporation_evidence -v`: 12개 테스트 통과
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_business_registration_kind_fields_use_ai_cleanup_when_configured tests.test_api_flows.ApiFlowTests.test_business_registration_ai_cleanup_sanitizes_sloppy_label_output -v`: 2개 테스트 통과
  - 사용자 제공 사업자등록증 이미지 opt-in 테스트: PaddleOCR 완료 및 업태/종목 후보 검증 통과
  - `py -3.13 -m unittest discover -s tests -v`: 47개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 통과
  - `scripts/smoke-test.ps1`: `SMOKE_OK` 통과
  - `git diff --check`: 공백 오류 없음, 기존 Windows CRLF 경고만 확인

## Additional Update (2026-05-22) - Phase 1.6 Stabilization Execution 1
- Established the current Phase 1.6 regression baseline before changing code.
- Code changes:
  - hardened business-registration `business kind` cleanup so table labels such as `사업의`, `종류`, `업태`, and `종목` do not leak into candidates
  - joined OCR-split suffixes such as `전문기` + `업` and split business type labels such as `도매 및` + `소매업`
  - sanitized Gemini/OpenAI business-kind cleanup output before turning it into `business_type`, `business_item`, and `business_category` candidates
  - prevented sloppy LLM label output from degrading review candidates
- Tests added:
  - multiline broken business-registration OCR regression
  - inline-label business-registration OCR regression
  - LLM business-kind sanitize unit test
  - API-level sloppy LLM output sanitize test
  - post-OCR candidate assertions in the real business-registration image opt-in test
- Documentation:
  - updated `docs/phase-1.6-stabilization-plan.md` with progress notes
- UX:
  - replaced raw developer statuses such as `pending`, `skipped`, and `classified` with Korean badge labels in evidence detail/list/candidate cards
  - displayed evidence document types with stakeholder-friendly labels instead of raw code values
- Verification:
  - `py -3.13 -m unittest tests.test_corporation_evidence -v`: 12 passed
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_business_registration_kind_fields_use_ai_cleanup_when_configured tests.test_api_flows.ApiFlowTests.test_business_registration_ai_cleanup_sanitizes_sloppy_label_output -v`: 2 passed
  - user-provided business-registration image opt-in test: PaddleOCR completed and business type/item extraction passed
  - `py -3.13 -m unittest discover -s tests -v`: 47 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: passed with `SMOKE_OK`
  - `git diff --check`: no whitespace errors, only existing Windows CRLF warnings

## 추가 업데이트 (2026-05-22) - 서버 한글깨짐 방지 수정
- 서버 소스와 스크립트의 한글깨짐 가능 지점을 점검했다.
- 코드 수정:
  - Flask JSON 응답에서 한글이 `\uXXXX` 형태로만 보이지 않도록 `app.json.ensure_ascii = False`와 `JSON_AS_ASCII = False`를 설정했다.
  - 나라장터/외부 API 텍스트 응답 디코딩을 `decode_http_body()` 공통 함수로 정리했다.
  - 외부 응답 charset이 잘못되거나 누락되어도 `charset -> utf-8-sig -> utf-8 -> cp949 -> euc-kr` 순서로 fallback하도록 변경했다.
  - `scripts/test-nara-api.py`도 동일한 디코딩 fallback을 사용하도록 수정했다.
  - `scripts/manage-servers.ps1`, `scripts/smoke-test.ps1`에 UTF-8 콘솔 입출력과 `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1` 설정을 추가했다.
  - `scripts/check-encoding.py`를 추가해 서버/테스트/스크립트/문서의 UTF-8 디코딩 실패와 mojibake 패턴을 검사하도록 했다.
  - 스모크 테스트 시작 시 인코딩 체크를 먼저 실행하도록 연결했다.
- 테스트 추가:
  - CP949로 들어온 한글 응답이 UTF-8 charset 오표기 상황에서도 정상 복원되는 단위 테스트를 추가했다.
- 검증 결과:
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `py -3.13 -m py_compile scripts/check-encoding.py scripts/test-nara-api.py`: 통과
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_decode_http_body_falls_back_to_korean_legacy_encodings -v`: 통과
  - `py -3.13 -m unittest discover -s tests -v`: 48개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 통과
  - `scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - 스모크 테스트 후 FE/BE 서버 종료 상태 확인
  - `git diff --check`: 공백 오류 없음, 기존 Windows CRLF 경고만 확인

## Additional Update (2026-05-22) - Korean Encoding Hardening
- Reviewed Korean text corruption risks across backend source and operational scripts.
- Code changes:
  - configured Flask JSON output with `app.json.ensure_ascii = False` and `JSON_AS_ASCII = False`
  - centralized external text response decoding in `decode_http_body()`
  - added decode fallback order: `charset -> utf-8-sig -> utf-8 -> cp949 -> euc-kr`
  - updated `scripts/test-nara-api.py` to use the same fallback decoding strategy
  - configured UTF-8 console input/output and Python UTF-8 mode in `scripts/manage-servers.ps1` and `scripts/smoke-test.ps1`
  - added `scripts/check-encoding.py` to detect UTF-8 decode failures and mojibake patterns in backend/tests/scripts/docs
  - wired the encoding check into smoke test startup
- Tests:
  - added coverage for CP949 Korean response fallback when charset is incorrectly reported as UTF-8
- Verification:
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `py -3.13 -m py_compile scripts/check-encoding.py scripts/test-nara-api.py`: passed
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_decode_http_body_falls_back_to_korean_legacy_encodings -v`: passed
  - `py -3.13 -m unittest discover -s tests -v`: 48 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - confirmed FE/BE servers stopped after smoke test
  - `git diff --check`: no whitespace errors, only existing Windows CRLF warnings

## 추가 업데이트 (2026-05-22) - Phase 1.7 부족조건 미리보기 1차 구현
- Phase 1.7A부터 1.7F까지 순서대로 구현했다.
- 개발 범위:
  - 저장한 나라장터 공고에서 요구조건 후보를 DB 테이블로 분리 저장하는 구조 추가
  - `notice_requirement_candidates` 테이블 추가
  - `notice_corporation_comparisons` 테이블 추가
  - 저장 공고 분석 완료 시 요구조건 후보 자동 생성
  - 요구조건 후보 조회/재추출 API 추가
  - 법인 프로필을 비교용 구조로 정규화하는 API 추가
  - 공고 요구조건 후보와 법인 준비상태를 비교하는 1차 rule-based 엔진 추가
  - 비교 결과 저장, 상세 조회, 전체 이력 조회, 공고별 이력 조회 API 추가
  - 요구조건 재추출 시 기존 비교 결과를 무효화해 stale 결과가 남지 않도록 처리
  - 포탈에 `부족조건 미리보기` 메뉴와 화면 추가
  - 공고 선택, 법인 선택, 요구조건 후보 확인, 법인 비교 프로필 확인, 비교 실행, 최근 비교 이력 확인 UX 추가
- 중요한 제약:
  - Phase 1.7 결과는 최종 지원 가능/불가능 판정이 아니다.
  - 출력 상태는 `준비된 항목`, `부족 가능성`, `확인 필요`, `법인 정보 없음`으로 제한했다.
  - 기준문서 RAG와 최종 판단 엔진은 아직 구현하지 않았다.
- 테스트 추가:
  - 저장 공고 요구조건 후보 API 테스트
  - 법인 비교 프로필 정규화 API 테스트
  - 공고-법인 부족조건 미리보기 생성/저장 테스트
  - 비교 이력 조회 테스트
  - 요구조건 재추출 시 기존 비교 이력 무효화 테스트
- 검증 결과:
  - `py -3.13 -m unittest discover -s tests -v`: 51개 테스트 통과, 1개 선택 OCR 테스트 skip
  - `npm run build`: 통과
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - 브라우저 확인: `http://127.0.0.1:5199/notice-comparison` 라우팅, 주요 버튼 렌더링, 콘솔 에러 없음 확인
  - 브라우저 확인 후 FE/BE 서버 종료 확인
  - `git diff --check`: 공백 오류 없음, 기존 Windows CRLF 경고만 확인

## Additional Update (2026-05-22) - Phase 1.7 Gap Preview Initial Implementation
- Implemented Phase 1.7A through 1.7F in order.
- Scope delivered:
  - added a persisted requirement-candidate model for saved Nara notices
  - added `notice_requirement_candidates`
  - added `notice_corporation_comparisons`
  - auto-generates requirement candidates when saved-notice analysis finishes
  - added requirement candidate read/re-extract APIs
  - added corporation comparison-profile normalization API
  - added first-pass rule-based comparison between notice requirements and corporation readiness profile
  - added comparison creation, detail, global history, and notice-specific history APIs
  - invalidates stale comparisons when requirement candidates are re-extracted
  - added the portal `Gap Preview` menu/page
  - added UX for selecting a saved notice and corporation, reviewing requirement candidates/profile, running comparison, and viewing comparison history
- Guardrails:
  - Phase 1.7 output is not a final eligibility verdict.
  - statuses are limited to `prepared`, `possibly_missing`, `needs_review`, and `not_found`.
  - basis-document RAG and final judgment engine remain out of scope.
- Tests added:
  - saved-notice requirement candidate API test
  - corporation comparison profile normalization API test
  - notice/corporation gap-preview creation and persistence test
  - comparison history retrieval test
  - stale comparison invalidation test after requirement re-extraction
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 51 passed, 1 optional OCR test skipped
  - `npm run build`: passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - browser check: confirmed `http://127.0.0.1:5199/notice-comparison` route, primary button rendering, and no console errors
  - confirmed FE/BE servers were stopped after browser verification
  - `git diff --check`: no whitespace errors, only existing Windows CRLF warnings

## 추가 업데이트 (2026-05-22) - 로컬 Python 3.13 워크스페이스 설정
- 로컬 개발 도구가 Python 3.13을 기본으로 사용하도록 VS Code 워크스페이스 설정을 추가했다.
- 변경 파일:
  - `.vscode/settings.json`
- 설정 내용:
  - `python.defaultInterpreterPath`를 `backend/.venv313/Scripts/python.exe`로 고정
  - `python.envFile`을 `backend/.env`로 지정
  - Pylance 분석 경로에 `backend` 추가
  - VS Code 테스트 실행을 Python `unittest` 기준으로 설정
  - Windows 터미널 환경에 `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` 추가
- 확인한 내용:
  - 루트 `.python-version`은 이미 `3.13.13`
  - `backend/.venv313`은 Python `3.13.13`
  - `backend/.venv`는 Python `3.14.3` 기반이므로 기본 인터프리터로 쓰지 않도록 워크스페이스 설정에서 제외
- 검증 결과:
  - `.\.venv313\Scripts\python.exe -c "import sys; print(sys.version); print(sys.executable)"`: Python `3.13.13` 확인
  - `.\.venv313\Scripts\python.exe -m unittest tests.test_api_flows.ApiFlowTests.test_decode_http_body_falls_back_to_korean_legacy_encodings -v`: 통과
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## Additional Update (2026-05-22) - Local Python 3.13 Workspace Settings
- Added VS Code workspace settings so local development tools prefer Python 3.13.
- Changed file:
  - `.vscode/settings.json`
- Settings:
  - pinned `python.defaultInterpreterPath` to `backend/.venv313/Scripts/python.exe`
  - set `python.envFile` to `backend/.env`
  - added `backend` to Pylance analysis paths
  - configured VS Code tests to use Python `unittest`
  - added `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` to Windows terminal env
- Confirmed:
  - root `.python-version` already contains `3.13.13`
  - `backend/.venv313` uses Python `3.13.13`
  - `backend/.venv` uses Python `3.14.3`, so the workspace explicitly avoids selecting it as the default interpreter
- Verification:
  - `.\.venv313\Scripts\python.exe -c "import sys; print(sys.version); print(sys.executable)"`: confirmed Python `3.13.13`
  - `.\.venv313\Scripts\python.exe -m unittest tests.test_api_flows.ApiFlowTests.test_decode_http_body_falls_back_to_korean_legacy_encodings -v`: passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## 추가 업데이트 (2026-05-22) - Phase 1.7 안정화 계획 작성
- Phase 1.7 `부족조건 미리보기` 기능의 안정화 계획 문서를 추가했다.
- 새 문서:
  - `docs/phase-1.7-stabilization-plan.md`
- 포함 내용:
  - 현재 구현 기준
  - 안정화 목표
  - 비범위
  - 핵심 원칙
  - 요구조건 후보 추출 안정화
  - 법인 비교 프로필 정규화 안정화
  - 비교 엔진 안전성 개선
  - 포탈 UX 안정화
  - 재분석/재추출/이력 무결성
  - 테스트 및 샘플 QA 체계
  - 보안/개인정보/로그 점검
  - 권장 개발 순서
  - 완료 기준
  - Product Owner 확인 질문
- README 문서 링크에 Phase 1.7 안정화 계획을 추가했다.

## Additional Update (2026-05-22) - Phase 1.7 Stabilization Plan
- Added a stabilization plan document for the Phase 1.7 `Gap Preview` feature.
- New document:
  - `docs/phase-1.7-stabilization-plan.md`
- Covered:
  - current implementation baseline
  - stabilization goals
  - non-scope
  - core principles
  - requirement candidate extraction hardening
  - corporation comparison profile normalization hardening
  - comparison engine safety
  - portal UX stabilization
  - re-analysis/re-extraction/history integrity
  - testing and sample QA strategy
  - security/privacy/logging review
  - recommended execution order
  - completion criteria
  - product-owner questions
- Added the Phase 1.7 stabilization plan link to README.

## 추가 업데이트 (2026-05-22) - Phase 1.7 안정화 진행
- 작업 범위:
  - 저장 공고 요구조건 후보 추출 안정화
  - 법인 비교 프로필 정규화 보강
  - 공고-법인 부족조건 미리보기 비교 엔진 오탐 방지
  - 비교 이력 무효화 조건 정리
  - 포탈 `부족조건 미리보기` UX 문구와 결과 우선순위 개선
- 백엔드 수정:
  - 지역 별칭 그룹을 추가해 `전남`, `전라남도`, `해남군` 같은 공고 지역 표현을 함께 인식하도록 보강
  - 면허/업종, 기업유형, 제출서류 토큰 그룹을 중앙 상수로 분리
  - `조경식재공사업`과 `조경식재`처럼 같은 의미의 면허는 매칭하되, `전기공사업`과 `전기/소방/통신자재`처럼 성격이 다른 텍스트는 매칭하지 않도록 보수적 비교 로직 적용
  - `중소기업`이 `소기업`으로 잘못 추출되는 문제를 방지
  - `국세 납세증명서`와 `지방세 납세증명서`가 서로 섞일 수 있는 넓은 별칭을 제거
  - 법인 프로필/승인 증빙/공고 요구조건 재추출 시 오래된 비교 결과가 남지 않도록 비교 이력을 무효화
- 프론트엔드 수정:
  - `부족조건 미리보기` 화면에서 최종 자격 판정이 아니라는 안내를 더 명확히 표시
  - 결과 카드 우선순위를 `부족 가능성`, `확인 필요`, `법인 정보 없음`, `준비된 항목` 순서로 변경
  - 법인 증빙자료 보강, 저장 공고 재확인, 요구조건 다시 추출 액션을 바로 찾을 수 있도록 CTA 영역 추가
  - 요구조건 재추출 시 기존 비교 결과가 정리된다는 설명을 화면에 추가
- 테스트 추가/보강:
  - 공고 요구조건 추출에서 지역 별칭, 붙어 있는 제출서류명, 기업유형 오탐 방지 테스트 추가
  - 면허/업종 보수적 매칭 테스트 추가
  - 국세/지방세 납세증명서 혼동 방지 테스트 추가
  - 법인 프로필 변경, 증빙 승인/재분석/삭제, 공고 요구조건 재추출 시 비교 이력 무효화 테스트 보강
- 검증 결과:
  - `py -3.13 -m unittest discover -s tests -v`: 53개 테스트 통과, 선택 OCR 실엔진 테스트 1개 skip
  - `npm run build`: 통과
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - 인앱 브라우저 확인: `http://127.0.0.1:5199/notice-comparison` 라우트, 최종 판정 아님 안내, CTA 렌더링, 콘솔 에러 없음 확인
- 코드리뷰 결과:
  - 초기 안정화 후 자체 리뷰에서 `납세증명서` 일반 별칭이 국세/지방세를 섞을 수 있는 위험을 발견하고 수정
  - Phase 1.7은 여전히 최종 지원 가능/불가능 판정이 아니라 부족조건 미리보기 범위로 제한됨을 확인

## Additional Update (2026-05-22) - Phase 1.7 Stabilization Execution
- Scope:
  - hardened saved-notice requirement candidate extraction
  - improved corporation comparison-profile normalization
  - reduced false-positive matches in the notice-vs-corporation gap preview engine
  - clarified comparison invalidation rules
  - improved the portal UX copy and result priority for the `Gap Preview` page
- Backend changes:
  - added region alias groups for expressions such as `전남`, `전라남도`, and `해남군`
  - centralized license, company-type, and required-document token groups
  - allowed equivalent license matches such as `조경식재공사업` vs `조경식재`, while avoiding unrelated text matches such as `전기공사업` vs `전기/소방/통신자재`
  - prevented `중소기업` from being extracted as an explicit `소기업` condition
  - removed the broad `납세증명서` alias that could mix up national-tax and local-tax certificates
  - invalidated stale comparison history when corporation profile/evidence data or notice requirement candidates change
- Frontend changes:
  - made it clearer that the gap preview is not a final eligibility verdict
  - reordered result panels to prioritize `possibly missing`, `needs review`, `not found`, and then `prepared`
  - added CTAs for corporation evidence upload, saved-notice review, and requirement re-extraction
  - explained that re-extracting requirements clears stale comparison results
- Tests:
  - added tests for region aliases, no-space document names, and company-type false-positive prevention
  - added conservative license-matching tests
  - added national-tax vs local-tax certificate mismatch coverage
  - strengthened stale comparison invalidation coverage for corporation/profile/evidence/requirement changes
- Verification:
  - `py -3.13 -m unittest discover -s tests -v`: 53 tests passed, 1 optional real OCR test skipped
  - `npm run build`: passed
  - `git diff --check`: no whitespace errors, Windows CRLF warnings only
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - in-app browser check: confirmed the `http://127.0.0.1:5199/notice-comparison` route, non-final-verdict notice, CTA rendering, and no console errors
- Review result:
  - during self-review, found and fixed the broad `납세증명서` alias risk
  - confirmed Phase 1.7 remains a gap-preview feature, not a final eligibility decision engine

## 추가 업데이트 (2026-05-22) - Phase 2 / 2.5 구현계획 작성
- Phase 2 기준문서/RAG 준비 개발을 실제 작업 가능한 세부 단계로 나눈 실행계획 문서를 추가했다.
- 신규 문서:
  - `docs/phase-2-implementation-plan.md`
- 주요 내용:
  - Phase 2A: 기준문서 도메인/DB 골격
  - Phase 2B: 기준문서 CRUD/API
  - Phase 2C: 기준 PDF 파싱/OCR/정규화 파이프라인
  - Phase 2D: 자동 청킹
  - Phase 2E: 로컬 벡터 인덱싱
  - Phase 2F: 기준문서 검색 API
  - Phase 2G: 기준문서 관리 UX
  - Phase 2H: 안정화/회귀 테스트
  - Phase 2.5A~D: 기준문서 규칙 추출 실험, 공고 요구조건 구조화 고도화, 검색/citation 품질 평가, Phase 3 입력 계약 확정
- README 문서 링크에 Phase 2 / 2.5 구현계획을 추가했다.
- 검증 결과:
  - 문서 생성 및 README 링크 업데이트 확인
  - 코드 실행 변경 없음

## Additional Update (2026-05-22) - Phase 2 / 2.5 Implementation Plan
- Added an execution-focused implementation plan for Phase 2 basis-document/RAG preparation.
- New document:
  - `docs/phase-2-implementation-plan.md`
- Covered:
  - Phase 2A: basis domain and DB skeleton
  - Phase 2B: basis CRUD/API
  - Phase 2C: basis PDF parsing/OCR/normalization pipeline
  - Phase 2D: automatic chunking
  - Phase 2E: local vector indexing
  - Phase 2F: basis search API
  - Phase 2G: basis management UX
  - Phase 2H: stabilization/regression tests
  - Phase 2.5A-D: basis rule extraction experiments, notice requirement structuring, retrieval/citation quality evaluation, and Phase 3 input contract
- Added the Phase 2 / 2.5 plan link to README.
- Verification:
  - confirmed document creation and README link update
  - no runtime code changes

## 추가 업데이트 (2026-05-22) - Phase 1.7 실제 공고 PDF 종료 QA
- 사용자 요청에 따라 Phase 1.7 종료 QA를 실제 나라장터 API와 공고문 PDF 샘플 기반으로 수행하도록 설계/구현했다.
- 코드/스크립트:
  - `.gitignore`: `backend/tests/nara-pdf-samples/` 제외 경로 추가
  - `scripts/fetch-nara-phase17-samples.py`: 나라장터 API 검색 -> PDF 다운로드 -> PyMuPDF 텍스트 추출 -> Phase 1.7 요구조건 후보 추출 -> 최종 판정 문구 금지 검사 -> manifest/요약 생성
  - `backend/tests/test_nara_phase17_live_samples.py`: `RUN_NARA_PHASE17_QA=1`일 때만 로컬 PDF 샘플을 검증하는 opt-in 테스트 추가
- 실제 다운로드 샘플:
  - `R26BK01526927-000`: 남면보건지소 그린리모델링 건축(설비) 공사, 후보 49개
  - `R26BK01526928-000`: 원북보건지소 그린리모델링 건축(설비) 공사, 후보 49개
  - `R26BK01526931-000`: 문내 충무 마을안길 정비공사, 후보 50개
  - `R26BK01526932-000`: 화산 석전 마을안길 정비공사, 후보 50개
  - `R26BK01526933-000`: 화원 평리 마을안길 정비공사, 후보 50개
- 로컬 산출물:
  - `backend/tests/nara-pdf-samples/01-R26BK01526927-000.pdf`
  - `backend/tests/nara-pdf-samples/02-R26BK01526928-000.pdf`
  - `backend/tests/nara-pdf-samples/03-R26BK01526931-000.pdf`
  - `backend/tests/nara-pdf-samples/04-R26BK01526932-000.pdf`
  - `backend/tests/nara-pdf-samples/05-R26BK01526933-000.pdf`
  - `backend/tests/nara-pdf-samples/manifest.json`
  - `backend/tests/nara-pdf-samples/qa-summary.md`
- 검증 결과:
  - `py -3.13 -m py_compile scripts\fetch-nara-phase17-samples.py backend\tests\test_nara_phase17_live_samples.py`: 통과
  - `py -3.13 -m unittest discover -s tests -v`: 54개 테스트 통과, 2개 opt-in 테스트 skip
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - `py -3.13 scripts\fetch-nara-phase17-samples.py --date-from 20260501 --date-to 20260522 --target-count 5 --num-of-rows 80 --max-pages-per-window 4`: 샘플 5개 수집 성공
  - `RUN_NARA_PHASE17_QA=1 py -3.13 -m unittest tests.test_nara_phase17_live_samples -v`: 3개 테스트 통과

## Additional Update (2026-05-22) - Phase 1.7 Real Notice PDF Closeout QA
- Implemented and ran Phase 1.7 closeout QA against real Nara API notice PDF samples.
- Code/scripts:
  - `.gitignore`: ignored `backend/tests/nara-pdf-samples/`
  - `scripts/fetch-nara-phase17-samples.py`: searches Nara notices, downloads PDFs, extracts text with PyMuPDF, extracts Phase 1.7 requirement candidates, checks final-verdict wording is absent, and writes a manifest/summary
  - `backend/tests/test_nara_phase17_live_samples.py`: added opt-in local sample QA under `RUN_NARA_PHASE17_QA=1`
- Downloaded samples:
  - `R26BK01526927-000`: 49 candidates
  - `R26BK01526928-000`: 49 candidates
  - `R26BK01526931-000`: 50 candidates
  - `R26BK01526932-000`: 50 candidates
  - `R26BK01526933-000`: 50 candidates
- Local artifacts:
  - `backend/tests/nara-pdf-samples/*.pdf`
  - `backend/tests/nara-pdf-samples/manifest.json`
  - `backend/tests/nara-pdf-samples/qa-summary.md`
- Verification:
  - `py -3.13 -m py_compile scripts\fetch-nara-phase17-samples.py backend\tests\test_nara_phase17_live_samples.py`: passed
  - `py -3.13 -m unittest discover -s tests -v`: 54 passed, 2 opt-in tests skipped
  - `npm run build`: passed
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: no whitespace errors, Windows CRLF warnings only
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
  - sample collection command downloaded five unique QA-passing notice PDFs
  - `RUN_NARA_PHASE17_QA=1 py -3.13 -m unittest tests.test_nara_phase17_live_samples -v`: 3 passed

## 추가 업데이트 (2026-05-22) - Phase 2A-H 기준문서 MVP 구현
- 사용자 요청에 따라 Phase 2A부터 Phase 2H까지 기준문서 업로드/청킹/인덱싱/검색 MVP를 구현했다.
- 백엔드:
  - `basis_documents`, `basis_document_chunks` 테이블 추가
  - `storage/basis/`, `storage/basis-index/` 분리 저장소 추가
  - `GET/POST/PATCH/DELETE /api/basis-documents`, 재처리, 청크 조회 API 추가
  - 기준 PDF 처리 흐름을 `텍스트 추출 -> OCR 확인 -> 정규화 -> 청킹 -> local-token-v1 인덱싱`으로 연결
  - OCR 미설치/텍스트 없는 PDF는 `needs_ocr_setup`으로 degrade
  - `POST /api/basis-search` 추가, 결과는 최종 판단이 아닌 citation 후보 청크로만 반환
- 프론트엔드:
  - `기준문서 관리` 메뉴 활성화
  - 기준 PDF 업로드, 목록, 상세, 메타데이터 편집, 재처리, 청크 미리보기, 검색 UI 추가
  - 기준문서 타입/API 클라이언트 추가
- 테스트:
  - Phase 2A-B: 기준문서 CRUD/PDF 포맷 가드 테스트
  - Phase 2C-D: 파싱/정규화/청킹/재처리 테스트, OCR 미설치 degrade 테스트
  - Phase 2E-F: 로컬 인덱스/검색 후보 테스트
- 검증 결과:
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2a_2b_basis_document_crud_and_pdf_guard -v`: 통과
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2c_2d_basis_processing_extracts_normalizes_and_chunks tests.test_api_flows.ApiFlowTests.test_phase2c_basis_blank_pdf_degrades_when_ocr_is_unavailable -v`: 통과
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase2e_2f_basis_index_and_search_returns_candidates_only -v`: 통과
  - `py -3.13 -m unittest discover -s tests -v`: 58개 테스트 중 56개 통과, 2개 opt-in 테스트 skip
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: 공백 오류 없음, Windows CRLF 경고만 확인
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
- 코드 리뷰 결과:
  - Phase 2C-D 리뷰 중 한글 테스트 PDF 생성 방식이 PyMuPDF 기본 폰트에서 깨지는 문제를 발견해 테스트 본문을 안정적인 ASCII PDF로 조정했다.
  - OCR 엔진 미설치 degrade 테스트를 추가했다.
  - Phase 2G 리뷰 중 검색 필터 상태에서 업로드/삭제 후 선택 문서 갱신이 꼬일 수 있는 문제를 수정했다.
- 남은 운영 QA:
  - 실제 기준 PDF 3~5개 수동 QA는 제품 오너가 우선 샘플을 선정한 뒤 수행한다.
  - 이미지 기반 한글 기준 PDF는 OCR 엔진 설치 후 품질을 재확인한다.

## Additional Update (2026-05-22) - Phase 2A-H Basis Document MVP
- Implemented the Phase 2 basis-document upload/chunk/index/search MVP from Phase 2A through Phase 2H.
- Backend:
  - added `basis_documents` and `basis_document_chunks`
  - added separate `storage/basis/` and `storage/basis-index/`
  - added basis document CRUD, reprocess, and chunk APIs
  - wired processing as `extract -> OCR check -> normalize -> chunk -> local-token-v1 index`
  - missing OCR or textless PDFs degrade to `needs_ocr_setup`
  - added `POST /api/basis-search`, returning citation candidate chunks only
- Frontend:
  - enabled the `Basis Documents` menu
  - added upload, list, detail, metadata edit, reprocess, chunk preview, and search UX
  - added basis document types and API client methods
- Tests:
  - Phase 2A-B CRUD/PDF guard coverage
  - Phase 2C-D parsing/normalization/chunk/reprocess and OCR-degrade coverage
  - Phase 2E-F local index/search candidate coverage
- Verification:
  - Phase-focused tests: passed
  - `py -3.13 -m unittest discover -s tests -v`: 56 passed, 2 opt-in skipped
  - `npm run build`: passed
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: no whitespace errors, Windows CRLF warnings only
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `ENCODING_CHECK_OK`, `SMOKE_OK`
- Review result:
  - fixed test PDF content after finding PyMuPDF default font does not embed Korean text reliably in generated unit-test PDFs
  - added explicit OCR-unavailable degradation coverage
  - fixed basis-page selection refresh after upload/delete under active search filters
- Remaining operational QA:
  - manual QA with 3-5 real basis PDFs still needs product-owner sample selection
  - image-only Korean basis PDFs should be rechecked after OCR engine setup

## 추가 업데이트 (2026-05-22) - Phase 2 운영 QA: 나라장터 랜덤 PDF 10개
- 사용자 요청에 따라 나라장터 API에서 공고문 PDF 10개를 랜덤 순서로 다운로드하고 Phase 2 기준문서 파이프라인 운영 QA를 수행했다.
- 코드/스크립트:
  - `.gitignore`: `backend/tests/nara-phase2-basis-qa-samples/` 제외 경로 추가
  - `scripts/fetch-nara-phase2-basis-qa-samples.py`: 나라장터 API 검색 -> 랜덤 순서 후보 선택 -> PDF 다운로드 -> 기준문서 API 업로드 -> 추출/OCR/정규화/청킹/인덱싱/검색 검증 -> manifest/요약 생성
  - `backend/tests/test_nara_phase2_basis_qa_samples.py`: `RUN_NARA_PHASE2_QA=1`일 때만 로컬 PDF 샘플을 기준문서 파이프라인으로 재검증하는 opt-in 테스트 추가
- 실행 조건:
  - 기간: `20260501` ~ `20260522`
  - 랜덤 시드: `20260522203720`
  - 목표 샘플: 10개
  - 최소 텍스트 길이: 300자
- 실제 다운로드 샘플:
  - `R26BK01501003-000`: 2026년도 사방댐설치사업(상주 남장 산88-4), 13,840자, 10청크, 10벡터
  - `R26BK01501098-001`: 비인면 구복리 개거수로 정비공사, 7,342자, 6청크, 6벡터
  - `R26BK01501018-000`: 2026년도 계류보전사업(성주 초전 용봉), 13,841자, 10청크, 10벡터
  - `R26BK01501129-000`: 지방하천 만덕천 재해복구사업, 7,948자, 6청크, 6벡터
  - `R26BK01501000-000`: 2026년도 계류보전사업(상주 공성 도곡), 13,969자, 10청크, 10벡터
  - `R26BK01501008-000`: 2026년도 사방댐설치사업(상주 외서 백전), 13,967자, 10청크, 10벡터
  - `R26BK01501131-000`: 마산면 마명리 배수로 공사, 7,336자, 6청크, 6벡터
  - `R26BK01501012-000`: 2026년도 계류보전사업(고령 덕곡 예), 13,839자, 10청크, 10벡터
  - `R26BK01501088-000`: 문곡지구 소규모 배수개선사업(2차), 7,344자, 6청크, 6벡터
  - `R26BK01500999-001`: 2026년도 계류보전사업(김천 지례 울곡), 13,970자, 10청크, 10벡터
- 검증 결과:
  - `py -3.13 -m py_compile scripts\fetch-nara-phase2-basis-qa-samples.py backend\tests\test_nara_phase2_basis_qa_samples.py`: 통과
  - `py -3.13 scripts\fetch-nara-phase2-basis-qa-samples.py --date-from 20260501 --date-to 20260522 --target-count 10 --num-of-rows 100 --max-pages-per-window 6 --window-days 7 --min-text-chars 300`: 샘플 10개 수집 및 Phase 2 QA 통과
  - `RUN_NARA_PHASE2_QA=1 py -3.13 -m unittest discover -s tests -p test_nara_phase2_basis_qa_samples.py -v`: 2개 테스트 통과
- 로컬 산출물:
  - `backend/tests/nara-phase2-basis-qa-samples/*.pdf`
  - `backend/tests/nara-phase2-basis-qa-samples/manifest.json`
  - `backend/tests/nara-phase2-basis-qa-samples/qa-summary.md`
- QA 메모:
  - 이번 QA는 실제 나라장터 공고문 PDF를 사용해 Phase 2 파이프라인 안정성을 검증한 것이다.
  - 법령/예규 같은 진짜 기준문서 PDF의 검색 품질 평가는 별도 샘플 선정 후 추가 수행할 수 있다.

## Additional Update (2026-05-22) - Phase 2 Operational QA: 10 Random Nara PDFs
- Downloaded 10 random Nara notice PDFs through the Nara API and ran Phase 2 basis-pipeline operational QA.
- Code/scripts:
  - `.gitignore`: ignored `backend/tests/nara-phase2-basis-qa-samples/`
  - `scripts/fetch-nara-phase2-basis-qa-samples.py`: searches Nara notices, randomly chooses PDF candidates, downloads PDFs, uploads them through the basis API, validates extract/OCR/normalize/chunk/index/search, and writes a manifest/summary
  - `backend/tests/test_nara_phase2_basis_qa_samples.py`: opt-in local sample QA under `RUN_NARA_PHASE2_QA=1`
- Run settings:
  - date range: `20260501` to `20260522`
  - random seed: `20260522203720`
  - target samples: 10
  - minimum text length: 300
- Verification:
  - py_compile for the new script and test: passed
  - sample collection command downloaded 10 Phase 2 QA-passing PDFs
  - `RUN_NARA_PHASE2_QA=1` opt-in tests: 2 passed
- Local artifacts:
  - `backend/tests/nara-phase2-basis-qa-samples/*.pdf`
  - `backend/tests/nara-phase2-basis-qa-samples/manifest.json`
  - `backend/tests/nara-phase2-basis-qa-samples/qa-summary.md`
- QA note:
  - This validates Phase 2 pipeline stability with real Nara notice PDFs.
  - Retrieval quality against official law/regulation basis PDFs can still be evaluated after sample selection.

## 추가 업데이트 (2026-05-22) - 공고문 PDF 테스트 공용 캐시와 랜덤 샘플 30개
- 사용자 요청에 따라 앞으로 공고문 PDF 관련 테스트가 매번 나라장터 API를 호출하지 않고, 이미 다운로드한 로컬 PDF 샘플을 우선 사용하도록 수정했다.
- 코드/스크립트:
  - `.gitignore`: `backend/tests/nara-notice-pdf-samples/` 제외 경로 추가
  - `backend/tests/nara_pdf_sample_cache.py`: 공용 공고문 PDF manifest 탐색/로딩 유틸 추가
  - `backend/tests/test_nara_phase17_live_samples.py`: 기본 샘플 경로를 공용 캐시 우선으로 변경하고 기존 `nara-pdf-samples/`는 fallback으로 유지
  - `backend/tests/test_nara_phase2_basis_qa_samples.py`: 기본 샘플 경로를 공용 캐시 우선으로 변경하고 기존 `nara-phase2-basis-qa-samples/`는 fallback으로 유지
  - `scripts/fetch-nara-notice-pdf-samples.py`: 공용 테스트용 나라장터 공고문 PDF 랜덤 수집 스크립트 추가
- 공용 캐시 정책:
  - 기본 경로: `backend/tests/nara-notice-pdf-samples/`
  - 기본 manifest: `backend/tests/nara-notice-pdf-samples/manifest.json`
  - 테스트에서 `NARA_NOTICE_PDF_SAMPLE_MANIFEST`를 지정하면 해당 manifest를 우선 사용
  - Phase별 env override(`NARA_PHASE17_SAMPLE_MANIFEST`, `NARA_PHASE2_SAMPLE_MANIFEST`)도 유지
  - opt-in 테스트만 로컬 PDF 샘플을 사용하며, 일반 테스트 실행에서는 네트워크 없이 skip
- 다운로드 결과:
  - 실행 명령: `py -3.13 scripts\fetch-nara-notice-pdf-samples.py --date-from 20260401 --date-to 20260522 --target-count 30 --num-of-rows 100 --max-pages-per-window 10 --window-days 7 --min-text-chars 300 --min-candidates 3`
  - 기간: `20260401` ~ `20260522`
  - 랜덤 시드: `20260522204523`
  - 샘플 수: 30개 / 30개
  - skip: 10개
  - 샘플별 텍스트 길이: 최소 3,886자, 최대 62,828자
  - 샘플별 요구조건 후보 수: 최소 31개, 최대 86개
- 검증 결과:
  - `py -3.13 -m py_compile scripts\fetch-nara-notice-pdf-samples.py backend\tests\nara_pdf_sample_cache.py backend\tests\test_nara_phase17_live_samples.py backend\tests\test_nara_phase2_basis_qa_samples.py`: 통과
  - `RUN_NARA_PHASE17_QA=1`, `RUN_NARA_PHASE2_QA=1`로 공용 30개 PDF 샘플 재사용 테스트: 5개 테스트 통과
  - `py -3.13 -m unittest discover -s tests -v`: 59개 테스트 중 56개 통과, 3개 opt-in 테스트 skip
- QA 메모:
  - 일부 PDF에서 PyMuPDF가 내부 PDF 문법 경고를 출력했지만, 샘플 검증과 opt-in 테스트는 모두 통과했다.
  - 로컬 산출물은 `backend/tests/nara-notice-pdf-samples/` 아래에 저장되며 Git에는 포함하지 않는다.

## Additional Update (2026-05-22) - Shared Notice PDF Test Cache And 30 Random Samples
- Updated notice-PDF-related tests to prefer already downloaded local PDF samples instead of calling the Nara API every time.
- Code/scripts:
  - `.gitignore`: ignored `backend/tests/nara-notice-pdf-samples/`
  - `backend/tests/nara_pdf_sample_cache.py`: shared sample manifest loading helper
  - Phase 1.7 and Phase 2 opt-in PDF tests now prefer the shared cache and keep their legacy folders as fallback
  - `scripts/fetch-nara-notice-pdf-samples.py`: reusable random Nara notice PDF sample downloader
- Shared cache policy:
  - default path: `backend/tests/nara-notice-pdf-samples/`
  - default manifest: `backend/tests/nara-notice-pdf-samples/manifest.json`
  - `NARA_NOTICE_PDF_SAMPLE_MANIFEST` can override the shared manifest
  - phase-specific manifest env vars are still supported
- Download result:
  - date range: `20260401` to `20260522`
  - random seed: `20260522204523`
  - sample count: 30/30
  - skipped candidates: 10
  - text length range: 3,886 to 62,828 chars
  - requirement candidate range: 31 to 86 candidates
- Verification:
  - py_compile for the new script/helper/tests: passed
  - shared-cache opt-in tests under `RUN_NARA_PHASE17_QA=1` and `RUN_NARA_PHASE2_QA=1`: 5 passed
  - default backend test discovery: 56 passed, 3 opt-in skipped
- QA note:
  - PyMuPDF emitted internal PDF syntax warnings for a few real-world PDFs, but parsing and tests passed.
  - Local artifacts are stored under `backend/tests/nara-notice-pdf-samples/` and ignored by Git.

## 추가 업데이트 (2026-05-22) - 남은 개발 단계 재정리
- 사용자 요청에 따라 Phase 2A-H 구현과 운영 QA 이후 남은 개발 단계를 재정리했다.
- 신규 문서:
  - `docs/remaining-development-roadmap.md`: 현재 완료 기준선, Phase 2 종료 보강, Phase 2.5A-D, Phase 3A-G, Phase 4 운영 제품화 후보를 정리
- README 문서 링크에 남은 개발 단계 로드맵을 추가했다.
- 핵심 결론:
  - Phase 2A-H는 MVP와 실제 공고문 PDF 기반 운영 QA까지 완료된 상태로 본다.
  - 다음 개발은 Phase 2 기능 추가가 아니라 Phase 2.5의 기준문서 규칙 후보 추출, 공고 요구조건 구조화, 검색/citation 평가, Phase 3 계약 확정이다.
  - Phase 3 판단 엔진 구현 전에는 citation 없는 조건을 확정 판단 근거로 쓰지 않는다.
  - 권장 다음 작업은 `Phase 2 종료 보강 -> 실제 기준문서 PDF 샘플 선정 -> Phase 2.5A/2.5C` 순서다.

## Additional Update (2026-05-22) - Remaining Development Roadmap
- Reorganized the remaining development roadmap after Phase 2A-H implementation and operational QA.
- New document:
  - `docs/remaining-development-roadmap.md`: current baseline, Phase 2 closeout hardening, Phase 2.5A-D, Phase 3A-G, and Phase 4 operations candidates
- Added the roadmap link to README.
- Key conclusion:
  - Phase 2A-H is treated as MVP-complete with real notice PDF operational QA.
  - The next work is not more Phase 2 feature work, but Phase 2.5 basis rule extraction, notice requirement structuring, retrieval/citation evaluation, and Phase 3 contract definition.
  - Uncited conditions must not become final judgment evidence before Phase 3.
  - Recommended next sequence is `Phase 2 closeout hardening -> official basis PDF sample selection -> Phase 2.5A/2.5C`.

## 추가 업데이트 (2026-05-22) - Phase 2 종료 보강, Phase 2.5A-D, Phase 3A-G 구현
- 사용자 요청에 따라 각 단계별 세부 실행계획을 먼저 작성하고, 해당 계획을 기준으로 MVP 구현과 테스트를 진행했다.
- 신규 문서:
  - `docs/phase-2-closeout-to-phase-3-execution-plan.md`: Phase 2 종료 보강, Phase 2.5A-D, Phase 3A-G 단계별 작업/테스트 계획
- 백엔드 구현:
  - Phase 2 종료 보강: `/api/qa/phase2-closeout`
  - Phase 2.5A: `basis_rule_candidates` 테이블, 기준문서 청크 기반 규칙 후보 추출/조회 API
  - Phase 2.5B: 저장 공고 요구조건을 Phase 3 입력 스키마로 변환하는 structured requirements API
  - Phase 2.5C: `basis_retrieval_evaluations` 테이블과 검색/citation 품질 평가 API
  - Phase 2.5D: `/api/judgment-contract`
  - Phase 3A-G: `judgment_runs`, `nara_collection_runs`, 부족조건 중심 판단 실행/조회/검토 API, citation 후보 연결, 준비 가이드, API 기반 나라장터 수집 run
- 프론트엔드 구현:
  - `/judgment-runs` 판단 검토 화면 추가
  - 판단 실행, 실행 이력, 부족/확인 필요/citation coverage 확인, 검토 상태/메모 저장 연결
- 테스트:
  - Phase 2 종료 보강 테스트 추가
  - Phase 2.5A-D 테스트 추가
  - Phase 3A-G 테스트 추가
  - 전체 backend 테스트: 67개 중 64개 통과, 3개 opt-in skip
  - frontend `npm run build`: 통과
- 코드 리뷰 중 수정:
  - 합성 PDF에서 한글 기본 폰트 추출이 불안정한 테스트 fixture를 ASCII 기반으로 보정
  - `공고일시`, `입찰개시`, `개찰일시`가 지역 후보로 오인되는 정규식 후처리 버그 수정
  - 새 판단 결과 payload에서 `지원 가능` 표현이 남지 않도록 문구 수정

## Additional Update (2026-05-22) - Phase 2 Closeout, Phase 2.5A-D, Phase 3A-G
- Wrote the detailed execution plan first, then implemented and tested the planned MVP slices.
- New document:
  - `docs/phase-2-closeout-to-phase-3-execution-plan.md`
- Backend:
  - Phase 2 closeout summary API
  - basis rule candidate extraction APIs and table
  - structured notice requirement API for Phase 3 input
  - retrieval/citation evaluation APIs and table
  - judgment contract API
  - judgment run APIs/table with gap-first matching, citation candidates, preparation guide, and review workflow
  - API-based Nara collection run APIs/table
- Frontend:
  - added `/judgment-runs` review page for running and reviewing judgment runs
- Verification:
  - backend test discovery: 67 tests, 64 passed, 3 opt-in skipped
  - frontend `npm run build`: passed
- Review fixes:
  - adjusted synthetic PDF fixtures away from unreliable Korean default-font extraction
  - fixed false region extraction for `공고일시`, `입찰개시`, and `개찰일시`
  - removed remaining `지원 가능` wording from new judgment payloads

## 작업 기록 (2026-05-24) - P2 운영 보강 구현
- 기준문서 규칙 후보 관리:
  - `basis_rule_candidates`에 `review_note`, `reviewed_at`, `reviewer_name`을 추가했다.
  - 후보 상세 조회, 수정, 승인, 반려 API를 추가했다.
  - 승인 시 `condition_text`, `citation_candidate_id`, 기준문서/chunk 존재 여부를 검증한다.
  - `/basis-rule-candidates` 운영 화면을 추가해 필터, 추출, 수정 저장, 승인, 반려를 수행할 수 있게 했다.
- 나라장터 자동 수집 관리:
  - 수집 이력 API에 `status`, `keyword` 필터를 추가했다.
  - `/nara-collection-runs` 운영 화면을 추가해 수집 실행, 이력, 저장 결과, 스킵 수, 실패 사유를 확인할 수 있게 했다.
- 운영 안정성:
  - 규칙 후보, 판단 이력, 수집 이력, 검색 평가 이력 조회용 인덱스를 추가했다.
  - Phase 2 closeout known issue 목록은 하드코딩 대신 로컬 `qa-known-issues.json` 또는 manifest의 known issue 필드를 동적으로 읽게 했다.
- 문서:
  - `README.md`, `docs/remaining-development-roadmap.md`, `docs/phase-2-closeout-to-phase-3-execution-plan.md`에 P2 운영 보강 완료 상태를 반영했다.

## Additional Update (2026-05-24) - P2 Operations Hardening
- Basis rule candidate management:
  - added review metadata columns to `basis_rule_candidates`
  - added detail, edit, approve, and reject APIs
  - approval now requires condition text, citation id, and valid basis document/chunk references
  - added `/basis-rule-candidates` admin UX
- Nara collection management:
  - added status/keyword filters to collection run history
  - added `/nara-collection-runs` admin UX for execution, history, saved results, skipped counts, and failure messages
- Operations hardening:
  - added indexes for rule candidates, judgment runs, collection runs, and retrieval evaluations
  - moved Phase 2 closeout known issues from hardcoded code to dynamic local QA JSON/manifest loading

## 작업 기록 (2026-05-24) - P1/P2/문서 보강 착수
- 신규 계획서:
  - `docs/p1-p2-doc-remediation-plan.md`에 P1, P2, 문서 보강 수정계획을 작성하고 README 문서 링크에 추가했다.
- P1 보강:
  - 기준문서 citation ID를 `basis:{basis_document_id}:chunk:{basis_chunk_id}` 형식으로 검증한다.
  - 기준 규칙 후보 승인 시 citation이 실제 후보의 기준문서/chunk와 일치해야만 승인된다.
  - 승인된 기준 규칙 후보를 judgment 실행 시 일반 기준문서 검색보다 먼저 사용하고, fallback 검색 여부와 승인 후보 ID를 결과에 남긴다.
  - 나라장터 수집 실행은 API 키 미설정 같은 업무 실패도 저장된 run payload로 반환해 관리자가 실패 이력을 바로 볼 수 있게 했다.
- P2 보강:
  - 기준 규칙 후보 화면에서 기준문서 ID 직접 입력 대신 기준문서 선택 목록을 사용하도록 개선했다.
  - citation 후보는 자유 입력 대신 백엔드가 제공한 citation option 선택 방식으로 바꿨다.
  - `approved/rejected -> needs_review` 전환 시 리뷰 시각과 리뷰어를 초기화하는 상태 정책을 반영했다.
  - 나라장터 수집 이력 필터에 `partial_failed`를 추가하고, 실패 사유/결과 JSON까지 keyword 검색 범위를 넓혔다.
  - `/basis-retrieval-evaluations` 화면을 추가해 검색 coverage와 누락 citation을 운영자가 확인할 수 있게 했다.
- 문서/문구 보강:
  - 공고 상세 화면의 오래된 Phase 1.6 문구를 기능 중심 문구로 수정했다.
  - 핵심 설계 문서에서 `eligible/not_eligible` 중심 예시를 부족조건 중심 상태로 교체했다.
  - `remaining-development-roadmap.md`의 Product Owner 질문을 `open/decided/deferred` 상태로 정리했다.
- 테스트:
  - citation 검증, 리뷰 상태 재개방, 승인 후보 judgment 연결, 나라장터 수집 실패/부분 실패 테스트를 추가했다.
  - 관련 backend 테스트와 frontend build를 1차 통과했다.

## Additional Update (2026-05-24) - P1/P2/Documentation Remediation Started
- New plan:
  - added `docs/p1-p2-doc-remediation-plan.md` and linked it from README.
- P1 remediation:
  - standardized basis citation IDs as `basis:{basis_document_id}:chunk:{basis_chunk_id}`
  - approval now validates that the citation belongs to the candidate's actual basis document and chunk
  - judgment runs prefer approved rule candidates before generic basis search and store fallback/provenance metadata
  - Nara collection business failures such as missing API keys now return saved run payloads for admin visibility
- P2 remediation:
  - basis rule candidate extraction now uses a basis document selector in the admin page
  - citation editing uses backend-provided citation options instead of free text
  - reopening reviewed candidates clears reviewer timestamp/name metadata
  - collection run filters include `partial_failed`, and keyword search includes failure/result JSON
  - added `/basis-retrieval-evaluations` for retrieval coverage and missed-citation review
- Documentation/copy:
  - replaced stale Phase 1.6 user-facing copy in saved notice detail
  - replaced final-verdict-centric examples with gap-first item states in core planning docs
  - consolidated Product Owner questions with `open/decided/deferred` states in the roadmap
- Verification:
  - added tests for citation validation, reopen metadata, approved-rule judgment wiring, and Nara failed/partial collection runs
  - targeted backend tests and frontend build passed

## 작업 기록 (2026-05-24) - 문서 보강 재확인
- 전체 Markdown 문서를 다시 스캔해 한국어 우선 작성, `AI / Engineering Version (English)` 섹션, Product Owner 질문 섹션, 최종 판정 중심 표현 잔존 여부를 확인했다.
- 정리한 문서:
  - `README.md`: RAG 계획 링크명을 `부족조건 판단 및 로컬 RAG 상세 구현계획`으로 변경
  - `docs/narajangteo-board-design.md`: `지원 가능 첨부` 표현을 `처리 가능 첨부`로 변경
  - `docs/narajangteo-api-test-result-20260505.md`: PDF/DOCX 첨부 처리 가능 여부와 자격 판단 표현이 섞이지 않도록 수정
  - `docs/narajangteo-api-analysis.md`: `eligible regions`를 `participation regions`로 변경
  - `docs/eligibility-rag-implementation-plan.md`: 문서 목적과 상태 예시를 `부족조건/준비 상태 판단` 중심으로 정리
  - `docs/corporation-evidence-auto-extraction-plan.md`, `docs/technical-design.md`, `docs/ux-design.md`, `docs/phase-1.6-stabilization-plan.md`, `docs/phase-1.7-stabilization-plan.md`, `docs/phase-2-closeout-to-phase-3-execution-plan.md`, `docs/technology-summary.md`, `docs/remaining-development-roadmap.md`: 최종 자격 판정/준비 상태 중심 표현으로 보정
- 재확인 결과:
  - 모든 MD 파일에 `AI / Engineering Version (English)` 섹션이 존재한다.
  - 현재 설계/UX 문서의 상태 예시는 `matched`, `missing`, `uncertain`, `needs_review`, `not_applicable`, `citation_missing` 중심으로 정리됐다.
  - 남은 `지원 가능`/`eligible` 검색 결과는 AGENTS 가드레일, 금지 문자열 테스트 설명, 보강 계획서의 문제 설명, work-log 역사 기록에 한정된다.
  - `py -3.13 scripts\check-encoding.py`: 통과
  - `git diff --check -- README.md AGENTS.md docs`: 공백 오류 없음, Windows LF/CRLF 경고만 확인

## Additional Update (2026-05-24) - Documentation Hardening Recheck
- Re-scanned all Markdown documents for Korean-first content, `AI / Engineering Version (English)` sections, Product Owner question sections, and stale final-verdict wording.
- Cleaned up current design/planning docs so supported-file wording no longer looks like eligibility judgment wording.
- Reframed the RAG/judgment plan around gap-first readiness states.
- Remaining `지원 가능` / `eligible` hits are limited to AGENTS guardrails, forbidden-string test descriptions, the remediation plan's problem statement, and historical work-log entries.
- Verification:
  - every MD file has an English engineering section
  - encoding check passed
  - diff whitespace check has no errors, only Windows LF/CRLF warnings

## 작업 기록 (2026-05-24) - D-4 코드 구조 분리 착수
- D-4 코드 구조 분리를 큰 리팩터링 대신 안전한 1차 절단면으로 시작했다.
- 신규 모듈:
  - `backend/app/core/text.py`: `clean_text`, `parse_int`, 기준문서 검색 token/vector helper
  - `backend/app/core/json_utils.py`: JSON dict/list 파싱 helper
  - `backend/app/core/citations.py`: 기준문서 citation ID 표준 생성/파싱 helper
  - `backend/app/services/basis_rule_candidates.py`: 기준 규칙 후보 승인 검증, 리뷰 상태 전환 정책, 판단 매칭 점수, citation 결과 merge helper
  - `backend/app/services/nara_api.py`: 나라장터 응답 파싱, 첨부 정규화, 안전 URL 검사, 첨부 다운로드 helper
  - `backend/app/pipelines/basis_document.py`: 기준문서 정규화, 청킹, 로컬 인덱싱, 재처리, 검색 후보 생성 파이프라인
- `backend/app/main.py`에서는 위 helper의 중복 정의를 제거하고 import로 대체했다.
- 검증:
  - 관련 기준 규칙 후보/판단 테스트 4개 통과
  - 나라장터 디코딩/저장/표준공고문 첨부/수집 실행 targeted 테스트 4개 통과
  - Phase 2 기준문서 처리/검색 targeted 테스트 5개 통과
  - Phase 3 citation targeted 테스트 3개 통과
  - 전체 백엔드 unittest 통과: 73 tests OK, 3 skipped
  - 신규 모듈과 `main.py` py_compile 통과

## Additional Update (2026-05-24) - D-4 Code Structure Split Started
- Started D-4 with a low-risk first slice rather than a broad rewrite.
- New modules:
  - `backend/app/core/text.py`
  - `backend/app/core/json_utils.py`
  - `backend/app/core/citations.py`
  - `backend/app/services/basis_rule_candidates.py`
  - `backend/app/services/nara_api.py`
  - `backend/app/pipelines/basis_document.py`
- Removed duplicate helper definitions from `backend/app/main.py` and imported them from the new modules.
- Verification:
  - four targeted basis-rule/judgment tests passed
  - four targeted Nara decoding/save/attachment/collection tests passed
  - five targeted Phase 2 basis processing/search tests passed
  - three targeted Phase 3 citation tests passed
  - full backend unittest discovery passed: 73 OK, 3 skipped
  - py_compile passed for `main.py` and the new modules

## 작업 기록 (2026-05-24) - Phase 4A 운영 대시보드 시작
- Phase 4 운영 제품화 작업을 시작했고, 1차 범위는 운영 대시보드로 제한했다.
- 추가/수정한 항목:
  - `backend/app/services/operations.py`: 운영 요약 집계 서비스
  - `GET /api/operations/summary`: DB, storage, OCR, 나라장터 API, AI provider 상태와 실패/검토대기 집계 API
  - `frontend/src/pages/OperationsPage.tsx`: `/operations` 운영 대시보드 UX
  - `frontend/src/app/types.ts`, `frontend/src/app/api.ts`, `frontend/src/app/App.tsx`: 타입/API/라우트/메뉴 연결
- 테스트:
  - 빈 DB 운영 요약 응답 테스트
  - 실패 작업과 검토 대기 큐 집계 테스트
  - API 키 원문 비노출 테스트
  - 프론트엔드 빌드 통과
  - 브라우저에서 `/operations` 주요 섹션 렌더 확인
- 남은 Phase 4 작업:
  - Phase 4B `operation_runs` 작업 이력 테이블과 서비스
  - Phase 4C 실패 상세/재시도 API와 UX
  - Phase 4D 백업/복원

## Additional Update (2026-05-24) - Phase 4A Operations Dashboard Started
- Started Phase 4 operational productization with a focused Phase 4A dashboard slice.
- Added/updated:
  - `backend/app/services/operations.py`
  - `GET /api/operations/summary`
  - `frontend/src/pages/OperationsPage.tsx`
  - frontend type/API/route/navigation wiring
- Tests:
  - empty-database operations summary
  - failure and review-queue aggregation
  - raw API key non-exposure
  - frontend build
  - browser render check for `/operations`
- Remaining Phase 4 work:
  - Phase 4B shared `operation_runs`
  - Phase 4C failure detail and retry API/UX
  - Phase 4D backup and restore

## 작업 기록 (2026-05-24) - Phase 4B/4C 작업 이력과 Phase 4D 백업 dry-run
- Phase 4B/4C 작업/실패 관리 구현을 진행했다.
- 추가/수정한 항목:
  - `operation_runs` 테이블과 인덱스
  - `backend/app/services/operations.py`에 작업 이력 payload/list/record helper 추가
  - `GET /api/operation-runs`
  - `GET /api/operation-runs/:id`
  - `POST /api/operation-runs/:id/retry`
  - 나라장터 수집, 판단 실행, 기준문서 재처리, 기준 규칙 후보 추출 이력 기록
  - `/operation-runs` 작업/실패 관리 UX
- Phase 4D 백업/복원 1차 구현을 진행했다.
- 추가/수정한 항목:
  - `backup_runs` 테이블과 인덱스
  - `backend/app/services/backups.py`: 백업 ZIP 생성, manifest/checksum 검증, 복원 dry-run 계획 생성
  - `GET /api/backups`
  - `POST /api/backups`
  - `GET /api/backups/:id`
  - `POST /api/backups/validate`
  - `POST /api/backups/restore-plan`
  - `POST /api/backups/:id/restore`: direct restore는 차단하고 dry-run만 허용
  - `/backups` 백업/복원 UX
- 테스트:
  - 나라장터 수집 작업 이력 기록 테스트 통과
  - 작업 재시도 새 이력 생성 테스트 통과
  - 백업 생성/검증/`.env` 제외 테스트 통과
  - 복원 dry-run 및 직접 복원 차단 테스트 통과
  - 전체 백엔드 unittest 통과: 80 OK, 3 skipped
  - 프론트엔드 빌드 통과
- 남은 항목:
  - 일반 문서 분석/증빙자료 분석까지 작업 이력 기록 확장
  - 실제 파일 교체 복원은 사용자 승인 후 별도 단계에서 구현
  - 백업 저장 위치 선택과 자동 백업 주기 설정은 별도 확장

## Additional Update (2026-05-24) - Phase 4B/4C Operation Runs And Phase 4D Backup Dry-Run
- Implemented Phase 4B/4C operation/failure management.
- Added/updated:
  - `operation_runs` table and indexes
  - operation run helper functions in `backend/app/services/operations.py`
  - `GET /api/operation-runs`
  - `GET /api/operation-runs/:id`
  - `POST /api/operation-runs/:id/retry`
  - run recording for Nara collection, judgment runs, basis document reprocessing, and basis rule extraction
  - `/operation-runs` UX
- Implemented the first Phase 4D backup/restore slice.
- Added/updated:
  - `backup_runs` table and indexes
  - `backend/app/services/backups.py`
  - `GET /api/backups`
  - `POST /api/backups`
  - `GET /api/backups/:id`
  - `POST /api/backups/validate`
  - `POST /api/backups/restore-plan`
  - `POST /api/backups/:id/restore` with direct restore blocked and dry-run allowed
  - `/backups` UX
- Tests:
  - operation run recording for Nara collection
  - retry creates a linked new run
  - backup creation/validation/`.env` exclusion
  - restore dry-run and direct restore blocking
  - full backend unittest discovery passed: 80 OK, 3 skipped
  - frontend build passed

## 작업 기록 (2026-05-31) - P1/P2 코드리뷰 보강 및 회귀 수정
- 코드리뷰에서 확인된 P1/P2 안정성 항목을 계획 순서대로 보강했다.
- 수정한 주요 항목:
  - P1-3: 백업 ZIP 생성 시 실행 중인 SQLite DB 파일을 직접 압축하지 않고 `sqlite3.Connection.backup()` 기반 스냅샷 DB를 생성해 압축하도록 수정
  - P1-2: 나라장터 첨부 다운로드 경로에도 외부 URL 검증을 적용하고 localhost/사설망/redirect 차단을 공통화
  - P1-1: 기준문서 재처리 실패 시 기존 청크와 승인된 기준 규칙 후보가 유지되도록 1차 보강
  - P2-2: 백업 검증/복원계획 API의 `file_path`를 `storage/backups` 하위 ZIP으로 제한
  - P2-1: 나라장터 재분석이 부분 실패할 경우 기존 첨부/요구조건/비교/판단 결과를 유지하도록 수정
- 추가 코드리뷰 후 즉시 수정계획 2개를 별도 문서에 정리했다.
  - `docs/코드리뷰 후 수정필요.md`
  - 즉시 수정계획: 기준문서 재처리 swap 원자성 보강, 나라장터 재분석 첨부 없음/지원 첨부 없음 보존
  - 기록만 한 항목: 첨부 URL DNS rebinding/shared address 보강, 백업 dry-run restore 경로 제한 일관화
- 즉시 수정계획 2개 구현:
  - `backend/app/pipelines/basis_document.py`
    - 기준문서 재처리를 SQLite savepoint와 JSON 인덱스 스냅샷 복구 방식으로 보강
    - 재처리 중간 실패 시 기존 DB 청크, 기존 JSON 인덱스, 기존 승인 후보 상태가 유지되도록 수정
  - `backend/app/main.py`
    - 기존 결과가 있는 나라장터 공고 재분석에서 지원 가능한 첨부가 0개이면 결과를 교체하지 않고 기존 분석 결과를 보존
    - 보존 사유를 `error_message`에 명확히 기록
  - `docs/코드리뷰 후 수정필요.md`
    - 두 즉시 수정계획에 완료 체크 추가
- 추가/보강 테스트:
  - 기준문서 인덱싱 실패 시 기존 청크/후보 보존 테스트
  - 기준문서 swap 단계 실패 시 기존 청크/인덱스/후보 상태 보존 테스트
  - 나라장터 재분석 부분 실패 시 기존 첨부/요구조건 보존 테스트
  - 나라장터 재분석 첨부 없음/지원 제외 첨부만 있는 경우 기존 결과 보존 테스트
  - 백업 스냅샷 DB 생성 및 임시 파일 제거 테스트
  - 백업 `file_path` 제한 테스트
  - 내부망 첨부 URL 차단 테스트
- 검증:
  - 전체 백엔드 unittest 통과: 91 OK, 3 skipped
  - 프론트엔드 `npm run build` 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - 관련 파일 `git diff --check` 통과

## Additional Update (2026-05-31) - P1/P2 Review Hardening And Regression Fixes
- Hardened P1/P2 stability findings in the requested order.
- Main fixes:
  - P1-3: backup creation now uses a consistent SQLite snapshot via `sqlite3.Connection.backup()` instead of zipping the live DB file directly
  - P1-2: Nara attachment downloads now share external URL validation and block localhost/private-network/unsafe redirect targets
  - P1-1: basis document reprocessing was first hardened to preserve existing chunks and approved rule candidates on failure
  - P2-2: backup validation and restore-plan APIs now restrict raw `file_path` inputs to ZIP files under `storage/backups`
  - P2-1: Nara notice reanalysis preserves previous attachments, requirements, comparisons, and judgment runs when the new run partially fails
- Added `docs/코드리뷰 후 수정필요.md` with immediate remediation plans and backlog-only review findings.
- Implemented the two immediate remediation plans:
  - `backend/app/pipelines/basis_document.py`
    - wraps basis reprocessing in a SQLite savepoint
    - snapshots and restores the JSON basis index on failure
    - preserves old DB chunks, old JSON index entries, and reviewed rule candidates unless the new run completes successfully
  - `backend/app/main.py`
    - treats reanalysis of an existing Nara notice with zero supported attachments as preserved partial failure
    - keeps existing analysis artifacts and records a clear preservation reason
  - `docs/코드리뷰 후 수정필요.md`
    - marked the two immediate plans as completed
- Tests added or expanded:
  - basis indexing failure preserves existing chunks and candidates
  - basis swap-stage failure preserves existing chunks, index, and candidate status
  - Nara partial reanalysis failure preserves prior attachments and requirements
  - Nara reanalysis with no supported attachments preserves prior results
  - SQLite backup snapshot creation and temp cleanup
  - backup path restriction
  - private-network attachment URL rejection
- Verification:
  - full backend unittest discovery passed: 91 OK, 3 skipped
  - frontend build passed
  - encoding check passed: `ENCODING_CHECK_OK`
  - related `git diff --check` passed

## 작업 기록 (2026-05-31) - work-log 기록 누락 보정
- 사용자가 모든 작업 활동을 `docs/work-log.md`에 기록해야 함을 재확인했다.
- 직전 P1/P2 코드리뷰 보강 작업은 `docs/코드리뷰 후 수정필요.md`에는 먼저 반영되었지만, `docs/work-log.md` 기록이 완료 보고 이후에 보정되었다.
- 앞으로 코드 수정, 문서 수정, 테스트 실행, 코드리뷰 결과, 검증 결과는 완료 응답 전에 `docs/work-log.md`에 먼저 기록한다.
- 문서 규칙은 한국어 기록을 먼저 작성하고, 이어서 AI/Engineering용 English 기록을 작성하는 방식으로 유지한다.

## Additional Update (2026-05-31) - Work-Log Discipline Correction
- The user reconfirmed that every work activity must be recorded in `docs/work-log.md`.
- The prior P1/P2 review-hardening work was first checked in `docs/코드리뷰 후 수정필요.md`, and the `docs/work-log.md` entry was corrected after the completion response.
- Going forward, code changes, documentation changes, test runs, review findings, and verification results must be recorded in `docs/work-log.md` before the final completion response.
- Documentation remains Korean-first, followed by an AI/Engineering English section.

## 작업 기록 (2026-05-31) - 전체 코드리뷰, 테스트 보강, UX 몽키테스트 제안
- 사용자 요청에 따라 전체 코드리뷰 관점으로 백엔드 안정성, 프론트 라우팅/UX 계약, 테스트 체계를 재확인했다.
- 코드리뷰에서 확인하고 수정한 항목:
  - `/api/backups/<id>/restore` dry-run 경로가 백업 경로 제한 helper를 우회하던 문제를 수정했다.
  - DB에 오염된 `file_path`가 들어가도 `storage/backups` 밖 ZIP을 dry-run restore 검증 대상으로 쓰지 못하도록 제한했다.
  - 프론트 사이드바 메뉴의 `/basis-rule-candidates`, `/nara-collection-runs` 경로가 실제 화면은 열리지만 상단 hero metadata는 대시보드 fallback을 쓰던 UX 회귀를 수정했다.
- 추가한 테스트 코드:
  - `backend/tests/test_api_flows.py`
    - `test_phase4d_restore_dry_run_rejects_backup_path_outside_backup_directory`
  - `backend/tests/test_frontend_contracts.py`
    - 사이드바 nav 경로가 React `<Route>`에 등록되어 있는지 검증
    - 사이드바 nav 경로가 page metadata를 가지고 있는지 검증
- UX 몽키테스트 제안 및 구현:
  - 완전 랜덤 클릭보다 `시드 고정 안전 몽키테스트`를 추천했다.
  - 기본 모드는 삭제/승인/반려/복원/저장/생성/실행/재시도 같은 파괴적 클릭을 피하도록 설계했다.
  - `scripts/ux-monkey-test.mjs` 추가
  - `frontend/package.json`에 `ux:monkey` script 추가
  - `docs/ux-monkey-testing-plan.md` 작성
- 보강 문서:
  - `docs/ux-monkey-testing-plan.md`
  - `docs/코드리뷰 후 수정필요.md`의 백업 dry-run restore 경로 제한 항목 완료 체크 업데이트
- 검증:
  - `py -3.13 -m unittest discover -s tests -v`: 94 OK, 3 skipped
  - `npm run build`: 통과
  - `npm run ux:monkey -- --help`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - 관련 파일 `git diff --check`: 통과
- 남은 리뷰 리스크:
  - 첨부 URL 검증의 DNS rebinding/shared address hardening은 아직 backlog로 남아 있다.
  - 파괴적 몽키테스트는 전용 임시 DB/storage 실행 표준이 정해진 뒤 활성화하는 편이 안전하다.

## Additional Update (2026-05-31) - Full Code Review, Test Hardening, UX Monkey Proposal
- Re-reviewed backend stability, frontend routing/UX contracts, and the current test strategy.
- Findings fixed:
  - `/api/backups/<id>/restore` dry-run bypassed the restricted backup path helper.
  - Corrupted DB `file_path` values can no longer make dry-run restore validate ZIP files outside `storage/backups`.
  - Frontend routes `/basis-rule-candidates` and `/nara-collection-runs` rendered but fell back to dashboard hero metadata; dedicated page metadata was added.
- Tests added:
  - `backend/tests/test_api_flows.py`
    - `test_phase4d_restore_dry_run_rejects_backup_path_outside_backup_directory`
  - `backend/tests/test_frontend_contracts.py`
    - verifies sidebar nav paths are registered as React routes
    - verifies sidebar nav paths have page metadata
- UX monkey testing:
  - recommended seeded safe monkey testing rather than fully random destructive clicking
  - default mode avoids destructive controls such as delete, approve, reject, restore, save, create, run, and retry
  - added `scripts/ux-monkey-test.mjs`
  - added `frontend/package.json` script `ux:monkey`
  - documented the strategy in `docs/ux-monkey-testing-plan.md`
- Documentation updates:
  - added `docs/ux-monkey-testing-plan.md`
  - marked the backup dry-run restore path restriction item complete in `docs/코드리뷰 후 수정필요.md`
- Verification:
  - full backend unittest discovery passed: 94 OK, 3 skipped
  - frontend build passed
  - `npm run ux:monkey -- --help` passed
  - encoding check passed: `ENCODING_CHECK_OK`
  - related `git diff --check` passed
- Remaining review risks:
  - attachment URL DNS rebinding/shared address hardening remains in backlog
  - destructive monkey testing should wait until a standard temporary DB/storage launcher exists

## 작업 기록 (2026-05-31) - 기준문서 RAG 코드리뷰
- 사용자 요청에 따라 코드 수정 없이 기준문서 RAG 관련 코드만 정적 리뷰했다.
- 검토 범위:
  - `backend/app/pipelines/basis_document.py`
  - `backend/app/services/basis_rule_candidates.py`
  - `backend/app/core/citations.py`
  - `backend/app/core/text.py`
  - `backend/app/main.py`의 기준문서 검색, 규칙 후보, citation, judgment 연결부
  - `frontend/src/pages/BasisDocumentsPage.tsx`
  - `frontend/src/pages/BasisRuleCandidatesPage.tsx`
  - `frontend/src/pages/BasisRetrievalEvaluationsPage.tsx`
  - 관련 테스트 코드 일부
- 확인한 주요 문제:
  - 규칙 후보 재추출이 기존 후보를 먼저 삭제하고, 새 후보가 0건이어도 완료로 커밋될 수 있어 승인/반려된 기준문구 후보가 사라질 수 있다.
  - 기준문서 검색과 승인 후보 judgment 연결이 `processing_status`, `index_status`, `vector_status`를 필터하지 않아 실패/미인덱스/보존 청크가 citation 후보로 쓰일 수 있다.
  - 로컬 JSON 인덱스를 생성하지만 검색은 DB 청크에서 토큰 벡터를 즉석 재계산하므로 인덱스 파일 손상이나 상태 불일치가 검색 품질 평가에 드러나지 않는다.
  - 규칙 후보 승인 검증은 citation 형식과 chunk 존재만 확인하고, 해당 chunk가 현재 검색 가능한 정상 인덱스인지 확인하지 않는다.
  - 검색 평가 화면은 이력 조회 중심이고 프론트 API client에는 평가 생성 호출이 없어 운영자가 화면에서 기준문서 검색 평가를 실행할 수 없다.
- 이번 요청은 "파악만"이므로 테스트 추가나 코드 수정은 진행하지 않았다.

## Additional Update (2026-05-31) - Basis RAG Code Review
- Per the user's request, reviewed only the basis-document RAG code path without changing implementation code.
- Review scope:
  - `backend/app/pipelines/basis_document.py`
  - `backend/app/services/basis_rule_candidates.py`
  - `backend/app/core/citations.py`
  - `backend/app/core/text.py`
  - basis search, rule-candidate, citation, and judgment wiring inside `backend/app/main.py`
  - `frontend/src/pages/BasisDocumentsPage.tsx`
  - `frontend/src/pages/BasisRuleCandidatesPage.tsx`
  - `frontend/src/pages/BasisRetrievalEvaluationsPage.tsx`
  - selected related tests
- Main findings:
  - rule-candidate extraction deletes existing candidates first and can commit zero new candidates, which can erase reviewed/approved basis-rule work.
  - basis search and approved-rule judgment retrieval do not filter by `processing_status`, `index_status`, or `vector_status`, so failed/unindexed/preserved chunks may still become citation candidates.
  - the local JSON index is written, but search recomputes token vectors from DB chunks, hiding index-file corruption or index/status mismatches from retrieval evaluation.
  - rule-candidate approval validates citation shape and chunk existence only, not whether the chunk is current, indexed, or from a healthy basis document.
  - the retrieval-evaluation UI is history-only, and the frontend API client has no create-evaluation call, so operators cannot run retrieval evaluation from the screen.
- No tests or code fixes were added because the request was review-only.

## 작업 기록 (2026-05-31) - 기준문서 RAG 수정계획 확인
- 사용자 요청에 따라 직전 기준문서 RAG 코드리뷰에서 파악한 문제점의 수정계획을 정리했다.
- 계획 범위:
  - 규칙 후보 재추출의 기존 승인/반려 후보 보존
  - 기준문서 검색과 judgment citation의 active/indexed 상태 필터 보강
  - JSON 인덱스와 DB 검색 상태 불일치 정리
  - 규칙 후보 승인 시 정상 청크/정상 문서 검증 강화
  - 검색/citation 평가 실행 UX/API client 연결
- 이번 단계에서는 코드 수정과 테스트 추가는 진행하지 않고, 사용자 확인용 계획만 제시한다.

## Additional Update (2026-05-31) - Basis RAG Remediation Plan Confirmation
- Per the user's request, prepared a remediation plan for the basis-document RAG findings identified in the previous review.
- Plan scope:
  - preserve existing reviewed/approved/rejected rule candidates during re-extraction
  - add active/indexed-state filtering to basis search and judgment citations
  - clarify and enforce JSON-index vs DB-search consistency
  - strengthen rule-candidate approval validation against healthy/current indexed chunks
  - connect retrieval/citation evaluation creation through frontend API and UX
- No implementation or test changes were made in this step; this is a plan-confirmation response only.

## 작업 기록 (2026-05-31) - 기준문서 RAG 보강 구현, 테스트, 재리뷰
- 사용자 요청에 따라 기준문서 RAG 코드리뷰에서 파악한 문제를 계획 순서대로 수정했다.
- 구현한 항목:
  - 규칙 후보 재추출이 기존 후보를 먼저 삭제하지 않도록 변경했다.
  - 새 규칙 후보가 0건이면 기존 후보를 보존하고 `no_candidates_extracted_existing_preserved` 상태로 응답한다.
  - 동일 규칙 후보는 `rule_type + condition_text 정규화 key + target_scope` 기준으로 기존 후보를 갱신하며, 승인/반려 상태와 리뷰 메타데이터를 유지한다.
  - 더 이상 추출되지 않는 승인/반려 후보는 citation을 비우고 `needs_review`로 내려 재검토 대상으로 표시한다.
  - 기준문서 검색은 `processing_status='completed'`, `index_status='completed'`, `vector_status='indexed'`, `vector_id<>''` 청크만 반환하도록 제한했다.
  - judgment의 승인 규칙 후보 citation 조회도 동일하게 completed/indexed 기준문서와 indexed chunk만 사용하도록 제한했다.
  - 규칙 후보 승인 검증이 문서 완료/인덱싱 상태와 chunk 인덱싱 상태를 확인하도록 강화했다.
  - 검색 응답과 검색 평가 결과에 `index_source: db_chunks_completed_indexed`를 추가해 현재 검색 기준을 명시했다.
  - 프론트 API client에 검색 평가 생성 호출을 추가하고, 검색/citation 평가 화면에서 질의셋을 입력해 평가를 실행할 수 있게 했다.
- 추가/보강한 테스트:
  - failed/unindexed 기준문서 청크가 기준문서 검색에서 제외되는 테스트
  - 규칙 후보 재추출 시 승인/반려 후보가 보존되는 테스트
  - 새 규칙 후보 0건 재추출 시 기존 후보가 삭제되지 않는 테스트
  - unindexed chunk citation 후보는 승인할 수 없는 테스트
  - unhealthy approved rule candidate가 judgment citation에 사용되지 않는 테스트
  - 프론트에서 검색 평가 생성 API와 화면 연결이 존재하는지 확인하는 계약 테스트
- 검증 결과:
  - RAG targeted 테스트 14개 통과
  - 전체 백엔드 unittest 통과: 100 tests OK, 3 skipped
  - 프론트엔드 `npm run build` 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - 관련 파일 `git diff --check`: 통과
- 수정 후 RAG 재리뷰 결과:
  - 직전 P1 문제였던 기존 후보 선삭제, failed/unindexed chunk 검색 노출, 승인 검증 부족은 재현 방지 테스트가 추가된 상태로 해소됐다.
  - 남은 리스크는 구조/품질 개선 성격이다.
  - 수동으로 수정한 `condition_text`를 재추출 매칭 key로 쓰기 때문에, 사용자가 승인 후보 문구를 많이 고친 뒤 재추출하면 같은 원문 후보도 다른 후보로 판단되어 `needs_review`가 될 수 있다.
  - JSON 인덱스는 여전히 생성/삭제되지만 실제 검색 source는 DB 청크이므로, JSON 인덱스가 캐시인지 복구용 산출물인지 문서화 또는 reconciliation 작업이 필요하다.
  - 새 후보가 0건일 때 기존 후보를 보존하는 정책은 데이터 손실은 막지만, 실제로 기준문서에서 규칙이 사라진 경우 stale 후보가 남을 수 있어 관리자 안내/일괄 재검토 UX가 있으면 좋다.

## Additional Update (2026-05-31) - Basis RAG Hardening, Tests, And Re-Review
- Implemented the requested basis-document RAG fixes in the planned order.
- Implemented:
  - rule-candidate re-extraction no longer deletes existing candidates up front
  - zero-candidate extraction preserves existing candidates and returns `no_candidates_extracted_existing_preserved`
  - matching candidates are updated by `rule_type + normalized condition_text key + target_scope`, while preserving approved/rejected status and review metadata
  - reviewed candidates that no longer match generated candidates are moved back to `needs_review` with citation cleared
  - basis search now returns only completed/indexed basis documents and indexed chunks
  - judgment approved-rule citations use the same completed/indexed filters
  - rule-candidate approval now requires a completed/indexed basis document and indexed chunk
  - basis search and retrieval evaluation now expose `index_source: db_chunks_completed_indexed`
  - frontend API and UX can now create retrieval/citation evaluations
- Tests added or expanded:
  - failed/unindexed chunks are excluded from basis search
  - re-extraction preserves reviewed candidates
  - zero-candidate re-extraction preserves existing candidates
  - unindexed citation chunks cannot be approved
  - unhealthy approved rule candidates are not used by judgment citations
  - frontend contract verifies retrieval evaluation creation is wired
- Verification:
  - 14 targeted RAG tests passed
  - full backend unittest discovery passed: 100 tests OK, 3 skipped
  - frontend build passed
  - encoding check passed: `ENCODING_CHECK_OK`
  - related `git diff --check` passed
- Post-fix RAG review:
  - the previous P1 findings around destructive candidate extraction, failed/unindexed chunk exposure, and weak approval validation are covered by regression tests now
  - remaining risks are structural/quality improvements
  - because manual edits to `condition_text` are part of the re-extraction match key, heavily edited approved candidates can be moved back to `needs_review` on re-extraction
  - the JSON index is still generated and deleted, but DB chunks are now the explicit search source; this needs documentation or reconciliation if the JSON index remains operationally important
  - preserving candidates when extraction returns zero prevents data loss, but can leave stale candidates if the basis document truly no longer contains rule text

## 작업 기록 (2026-05-31) - 기준문서 RAG P2 수정계획 문서화
- 사용자 요청에 따라 남은 P2 리스크 2개에 대한 수정계획을 문서화했다.
- 신규 문서:
  - `docs/basis-rag-json-index-management-plan.md`
- 주요 결정:
  - JSON 인덱스는 제거하지 않고 운영 산출물로 유지한다.
  - SQLite DB는 기준문서/청크/후보/리뷰 상태의 원본 저장소로 두고, JSON 인덱스는 로컬 RAG 검색 인덱스 산출물로 관리한다.
- 계획 내용:
  - 수동 수정 가능한 `condition_text`와 재추출 매칭용 안정 key를 분리한다.
  - `source_condition_text`, `source_condition_hash`, `extraction_key` 필드를 추가한다.
  - JSON 인덱스 schema v2, checksum, status/validate/rebuild API, 백업/복원 검증 연동 계획을 정리했다.
  - 검색을 중기적으로 JSON 인덱스 우선으로 전환하는 순서를 정리했다.
- 이번 단계는 계획 문서 작성만 진행했으며 구현 코드는 수정하지 않았다.

## Additional Update (2026-05-31) - Basis RAG P2 Remediation Plan Documented
- Documented the remediation plan for the two remaining P2 RAG risks.
- New document:
  - `docs/basis-rag-json-index-management-plan.md`
- Key decision:
  - keep the JSON index as an operational artifact
  - keep SQLite as the source of truth for basis documents/chunks/candidates/review state, and manage JSON as the local RAG retrieval index artifact
- Covered:
  - separate editable `condition_text` from stable re-extraction matching keys
  - add `source_condition_text`, `source_condition_hash`, and `extraction_key`
  - introduce JSON index schema v2, checksum, status/validate/rebuild APIs, and backup/restore validation integration
  - plan a staged migration to JSON-index-first retrieval
- This step only added the plan document; implementation code was not changed.

## 작업 기록 (2026-05-31) - 기준문서 RAG 추가 코드리뷰
- 사용자 요청에 따라 기준문서 RAG 관련 코드를 추가로 정적 리뷰했다.
- 이번 단계에서는 코드 수정 없이 문제점 파악만 진행했다.
- 추가 확인 범위:
  - 기준 규칙 후보 재추출/갱신 로직
  - 기준문서 검색 필터
  - 승인 규칙 후보 judgment 연결
  - JSON 인덱스 로드/저장/삭제 흐름
  - 검색 평가 UX/API 연결부
- 추가로 파악한 문제:
  - 승인/반려 후보가 재추출과 매칭되면 `condition_text`, `required_evidence_types_json`, `related_profile_fields_json`, `citation_candidate_id`, `confidence`가 자동 추출값으로 갱신되지만 승인/반려 상태와 리뷰 메타데이터는 유지된다. 이 경우 관리자가 승인한 후보의 의미가 자동으로 바뀔 수 있다.
  - 규칙 후보 추출 API는 기준문서가 `completed/indexed` 상태인지 확인하지 않고 모든 청크를 대상으로 후보를 만든다. failed/unindexed 문서에서도 후보 추출은 completed operation으로 기록될 수 있다.
  - JSON 인덱스 로드는 파일 손상/JSON decode 실패를 빈 인덱스로 처리하고, 이후 저장 작업이 손상 파일을 조용히 덮어쓸 수 있다. JSON 인덱스를 운영 산출물로 유지하려면 손상 상태를 보존/보고해야 한다.
- 테스트는 실행하지 않았고 정적 코드리뷰만 수행했다.

## Additional Update (2026-05-31) - Additional Basis RAG Code Review
- Per the user's request, performed an additional static review of the basis-document RAG code path.
- No implementation code was changed in this step.
- Additional review scope:
  - basis rule-candidate re-extraction/update logic
  - basis search filters
  - approved-rule candidate judgment wiring
  - JSON index load/save/delete flow
  - retrieval evaluation UX/API wiring
- Additional findings:
  - when an approved/rejected candidate matches re-extraction, `condition_text`, `required_evidence_types_json`, `related_profile_fields_json`, `citation_candidate_id`, and `confidence` are overwritten from automatic extraction while the approved/rejected status and review metadata remain; this can silently change reviewed evidence semantics
  - rule-candidate extraction does not require the basis document to be completed/indexed and can create candidates for failed/unindexed documents while recording the operation as completed
  - JSON index loading treats corrupt/unreadable JSON as an empty index; a subsequent save can silently overwrite the corrupt artifact, which is unsafe if JSON is retained as an operational index artifact
- No tests were run; this was static review only.

## 작업 기록 (2026-05-31) - 기준문서 RAG 추가 문제점 수정계획 작성
- 사용자 요청에 따라 추가 코드리뷰에서 찾은 문제점 전체에 대한 수정계획서를 작성했다.
- 신규 문서:
  - `docs/basis-rag-additional-remediation-plan.md`
- 포함한 문제:
  - 승인/반려 후보가 자동 재추출로 조용히 덮어써지는 문제
  - failed/unindexed 기준문서에서도 규칙 후보 추출이 실행되는 문제
  - JSON 인덱스 손상이 빈 인덱스로 처리되고 덮어써질 수 있는 문제
  - 수동 수정 가능한 `condition_text`가 재추출 매칭 key에 들어가는 문제
  - JSON 인덱스를 운영 산출물로 유지하기 위한 검색/검증/복구 계획
- 이번 단계는 수정계획 문서 작성만 진행했으며 구현 코드는 수정하지 않았다.

## Additional Update (2026-05-31) - Additional Basis RAG Remediation Plan
- Per the user's request, documented the remediation plan for all additional basis RAG findings.
- New document:
  - `docs/basis-rag-additional-remediation-plan.md`
- Covered issues:
  - approved/rejected candidates can be silently overwritten by automatic re-extraction
  - rule-candidate extraction can run for failed/unindexed basis documents
  - corrupt JSON indexes can be treated as empty and overwritten
  - editable `condition_text` is part of the re-extraction matching key
  - JSON index operational management for search, validation, and recovery
- This step only added the plan document; implementation code was not changed.

## 작업 기록 (2026-05-31) - 기준문서 RAG 수정계획 구현 및 재테스트
- 사용자 요청에 따라 `docs/basis-rag-additional-remediation-plan.md`와 `docs/basis-rag-json-index-management-plan.md`의 계획대로 구현을 진행했다.
- 구현 범위:
  - `basis_rule_candidates`에 `source_condition_text`, `source_required_evidence_types_json`, `source_related_profile_fields_json`, `source_confidence`, `source_condition_hash`, `extraction_key` 필드 추가
  - 규칙 후보 재추출 시 `extraction_key`를 우선 사용하고, 승인/반려 후보의 수동 수정 필드를 자동 추출값으로 덮어쓰지 않도록 변경
  - failed/unindexed 기준문서의 규칙 후보 추출을 409 `basis_not_ready`로 차단하고 operation run에 실패 사유 기록
  - JSON 인덱스 schema v2, checksum, 손상/불일치 검증, 명시적 rebuild 흐름 추가
  - 검색 API를 JSON 인덱스 source로 전환하고 인덱스 손상/불일치 시 DB fallback 없이 409 반환
  - `GET /api/basis-index/status`, `POST /api/basis-index/validate`, `POST /api/basis-index/rebuild` 추가
  - 백업 manifest/검증에 `basis-index.json` checksum 포함
  - 운영 대시보드 health 응답과 프론트 타입에 기준문서 인덱스 상태 추가
- 문서 보강:
  - `docs/basis-rag-additional-remediation-plan.md` 구현 상태 체크 완료
  - `docs/basis-rag-json-index-management-plan.md` 구현 상태 체크 완료
- 추가/수정 테스트:
  - 승인 후보 수동 수정값 보존 재추출 테스트
  - 기준문서 미준비 상태 후보 추출 차단 테스트
  - JSON 인덱스 손상 감지, 검색 차단, rebuild 복구 테스트
  - JSON 인덱스 검색 source 및 백업 manifest checksum 검증 테스트
- 검증 결과:
  - Python 3.13 환경에 `pytest`가 없어 `py -3.13 -m pip install -r backend/requirements.txt pytest`로 테스트 의존성을 맞춘 뒤 검증
  - `py -3.13 -m compileall backend/app` 통과
  - `py -3.13 -m pytest backend/tests -q` 결과: 99 passed, 3 skipped
  - `npm run build` 통과
  - `py -3.13 scripts/check-encoding.py` 결과: `ENCODING_CHECK_OK`

## Additional Update (2026-05-31) - Implemented Basis RAG Remediation And Retested
- Implemented the remediation plan from `docs/basis-rag-additional-remediation-plan.md` and `docs/basis-rag-json-index-management-plan.md`.
- Implementation scope:
  - added source/stable-key columns to `basis_rule_candidates`
  - changed rule-candidate re-extraction to prefer `extraction_key` and preserve manually reviewed approved/rejected fields
  - blocked rule-candidate extraction for failed/unindexed basis documents with HTTP 409 `basis_not_ready` and operation-run failure metadata
  - added JSON index schema v2, checksum validation, corruption/inconsistency detection, and explicit rebuild flow
  - switched basis search to the JSON index source and return HTTP 409 on corrupt/inconsistent indexes without DB fallback
  - added `GET /api/basis-index/status`, `POST /api/basis-index/validate`, and `POST /api/basis-index/rebuild`
  - included `basis-index.json` checksum in backup manifests and validation
  - exposed basis-index health in operations summary and frontend types
- Documentation updates:
  - checked off implementation status in the additional remediation plan
  - checked off implementation status in the JSON index management plan
- Tests added/updated:
  - approved candidate manual-field preservation during re-extraction
  - not-ready basis document extraction block
  - corrupt JSON index detection, search block, and rebuild recovery
  - JSON search source and backup manifest checksum coverage
- Verification:
  - installed missing Python 3.13 test dependencies with `py -3.13 -m pip install -r backend/requirements.txt pytest` before verification
  - `py -3.13 -m compileall backend/app` passed
  - `py -3.13 -m pytest backend/tests -q`: 99 passed, 3 skipped
  - `npm run build` passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-05-31) - 오늘 수정 코드 재검토
- 사용자 요청에 따라 오늘 수정된 기준문서 RAG/JSON 인덱스/백업/운영/프론트 연결 코드를 MD 계획 기준으로 재검토했다.
- 참고 문서:
  - `docs/basis-rag-additional-remediation-plan.md`
  - `docs/basis-rag-json-index-management-plan.md`
  - `docs/work-log.md`
- 재검토 범위:
  - `backend/app/pipelines/basis_document.py`
  - `backend/app/main.py`
  - `backend/app/services/backups.py`
  - `backend/app/services/operations.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/api.ts`
  - `frontend/src/app/types.ts`
  - `frontend/src/pages/OperationsPage.tsx`
- 확인 결과:
  - 핵심 구현 흐름은 계획과 대체로 일치한다.
  - 검색 API는 JSON 인덱스를 사용하고 손상/불일치 시 409로 막는다.
  - 규칙 후보 재추출은 승인/반려 수동 수정값을 보존한다.
  - 백업 manifest에는 `basis-index.json` checksum이 포함된다.
- 추가 발견사항:
  - 검색 평가 저장 payload의 `result.index_source`와 policy 문구가 아직 `db_chunks_completed_indexed`를 가리켜 JSON 인덱스 전환 상태와 불일치한다.
  - 기준문서 삭제 API는 손상된 JSON 인덱스에서 `BasisIndexError`를 409로 변환하지 않아 500으로 노출될 수 있다.
- 재검증:
  - `py -3.13 -m pytest backend/tests -q` 결과: 99 passed, 3 skipped
  - `npm run build` 통과
  - `py -3.13 scripts/check-encoding.py` 결과: `ENCODING_CHECK_OK`

## Additional Update (2026-05-31) - Re-reviewed Today's Modified Code
- Re-reviewed today's basis RAG / JSON index / backup / operations / frontend wiring changes against the MD plans.
- Reference documents:
  - `docs/basis-rag-additional-remediation-plan.md`
  - `docs/basis-rag-json-index-management-plan.md`
  - `docs/work-log.md`
- Review scope:
  - `backend/app/pipelines/basis_document.py`
  - `backend/app/main.py`
  - `backend/app/services/backups.py`
  - `backend/app/services/operations.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/src/app/api.ts`
  - `frontend/src/app/types.ts`
  - `frontend/src/pages/OperationsPage.tsx`
- Result:
  - the core implementation mostly matches the plan
  - search uses the JSON index and returns 409 on corrupt/inconsistent indexes
  - rule-candidate re-extraction preserves manually reviewed approved/rejected fields
  - backup manifests include the `basis-index.json` checksum
- Additional findings:
  - retrieval evaluation stored metadata still reports `result.index_source` and policy as DB-chunk based, which is inconsistent with JSON-index-first search
  - basis document deletion does not translate `BasisIndexError` from a corrupt JSON index into HTTP 409, so it can surface as a generic 500
- Verification:
  - `py -3.13 -m pytest backend/tests -q`: 99 passed, 3 skipped
  - `npm run build` passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-05-31) - 기준문서 RAG P2 후속 수정계획 작성
- 사용자 요청에 따라 오늘 재검토에서 발견된 P2 후속 이슈 2건에 대한 수정계획서를 작성했다.
- 신규 문서:
  - `docs/basis-rag-p2-followup-fix-plan.md`
- 계획 대상:
  - 검색 평가 저장 payload의 `result.index_source`와 policy 문구가 JSON 인덱스 전환 상태와 불일치하는 문제
  - 기준문서 삭제 API가 손상된 JSON 인덱스에서 `BasisIndexError`를 409로 변환하지 않아 500으로 노출될 수 있는 문제
- 문서에는 다음 항목을 포함했다.
  - 왜 이슈가 계속 나오는지에 대한 원인 설명
  - 수정 원칙
  - 파일별 수정 방향
  - 테스트 계획
  - 완료 기준
  - 구현 순서
- 이번 단계는 계획 문서 작성만 진행했으며 구현 코드는 수정하지 않았다.

## Additional Update (2026-05-31) - Basis RAG P2 Follow-up Fix Plan
- Per the user's request, documented the fix plan for the two follow-up P2 issues found in today's review.
- New document:
  - `docs/basis-rag-p2-followup-fix-plan.md`
- Planned fixes:
  - align retrieval evaluation `result.index_source` and policy copy with JSON-index-first retrieval
  - map `BasisIndexError` in basis document deletion to HTTP 409 instead of surfacing a generic 500
- The document includes:
  - why these follow-up issues appeared
  - fix principles
  - file-level implementation plan
  - test plan
  - completion criteria
  - implementation order
- This step only added the plan document; implementation code was not changed.

## 작업 기록 (2026-05-31) - 기준문서 RAG P2 후속 수정 구현 및 재리뷰
- 사용자 요청에 따라 `docs/basis-rag-p2-followup-fix-plan.md`의 계획대로 P2 후속 이슈 2건을 수정했다.
- 구현한 수정:
  - 검색 평가 저장 결과의 `result.index_source`를 `json_basis_index`로 변경했다.
  - 검색 평가 policy 문구를 JSON 기준문서 인덱스 기준 citation 후보 설명으로 변경했다.
  - 기준문서 삭제 API에서 `delete_basis_vectors()`가 `BasisIndexError`를 발생시키면 HTTP 409와 `basis_index_unavailable`, `rebuild_required: true`를 반환하도록 변경했다.
- 추가/수정한 테스트:
  - `test_phase25c_retrieval_evaluation_tracks_citation_coverage`에 검색 평가 source/policy assertion을 추가했다.
  - `test_basis_document_delete_returns_409_when_basis_index_is_corrupt`를 추가해 손상 인덱스에서 삭제가 중단되고, rebuild 후 삭제가 정상 동작하는지 검증했다.
- 실행한 검증:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "basis_document_delete_returns_409 or retrieval_evaluation_tracks_citation_coverage"` 결과: 2 passed, 76 deselected
  - `py -3.13 -m compileall backend/app` 통과
  - `py -3.13 -m pytest backend/tests -q` 결과: 100 passed, 3 skipped
  - `npm run build` 통과
  - `py -3.13 scripts/check-encoding.py` 결과: `ENCODING_CHECK_OK`
  - 관련 파일 `git diff --check` 통과
- 문서 보강:
  - `docs/basis-rag-p2-followup-fix-plan.md`의 깨진 한국어 섹션을 읽을 수 있는 한국어/영어 구조로 다시 정리했다.
  - 수정 완료 항목을 체크하고, 후속 코드리뷰 결과를 계획서에 반영했다.
- 수정 후 코드리뷰 결과:
  - 이번 계획의 2개 이슈는 구현과 테스트로 해소됐다.
  - 추가 리스크 1건을 확인했다. `delete_basis_vectors()`가 `load_basis_index()`만 사용해 파일 손상은 막지만, JSON 인덱스가 파일 없음 또는 DB와 불일치한 상태인지는 삭제 전에 충분히 검증하지 않는다.
  - 여러 기준문서가 있는 상태에서 `basis-index.json`이 없으면 삭제 API가 빈 인덱스를 새로 저장한 뒤 대상 문서를 삭제할 수 있고, 남은 기준문서 chunk가 DB에는 있지만 JSON 인덱스에는 없는 상태가 될 수 있다.
  - 권장 후속 조치는 삭제 전에 `validate_basis_index(conn)`로 missing/inconsistent/corrupt 상태를 확인하고, DB에 indexed chunk가 있으면 409 rebuild 필요 응답으로 막는 것이다.

## Additional Update (2026-05-31) - Implemented Basis RAG P2 Follow-up Fixes And Re-reviewed
- Per the user's request, implemented the two follow-up P2 fixes from `docs/basis-rag-p2-followup-fix-plan.md`.
- Implemented:
  - changed retrieval evaluation `result.index_source` to `json_basis_index`
  - updated retrieval evaluation policy copy to describe JSON basis-index citation candidates
  - changed basis document deletion to map `BasisIndexError` from `delete_basis_vectors()` to HTTP 409 with `basis_index_unavailable` and `rebuild_required: true`
- Tests added/updated:
  - added source/policy assertions to `test_phase25c_retrieval_evaluation_tracks_citation_coverage`
  - added `test_basis_document_delete_returns_409_when_basis_index_is_corrupt`
- Verification:
  - targeted pytest: 2 passed, 76 deselected
  - `py -3.13 -m compileall backend/app` passed
  - `py -3.13 -m pytest backend/tests -q`: 100 passed, 3 skipped
  - `npm run build` passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - related `git diff --check` passed
- Documentation:
  - rewrote `docs/basis-rag-p2-followup-fix-plan.md` so the Korean section is readable and the English engineering section remains present
  - checked off completed implementation items and added the post-fix review result
- Post-fix review:
  - the planned two issues are fixed and covered by tests
  - one additional follow-up risk remains: `delete_basis_vectors()` uses `load_basis_index()` and does not validate DB/index consistency before deletion
  - if `basis-index.json` is missing while multiple basis documents still have indexed chunks, deletion can save an empty JSON index and leave remaining DB chunks missing from the JSON index
  - recommended follow-up: call `validate_basis_index(conn)` before deletion and return a 409 rebuild-required response for missing/inconsistent/corrupt index states when DB indexed chunks exist

## 작업 기록 (2026-05-31) - 기준문서 삭제 전 JSON 인덱스 정합성 검증 보강
- 사용자 요청에 따라 기준문서 삭제 경로의 남은 P2 리스크를 계획서에 P2-3으로 추가하고, 계획대로 수정했다.
- 계획 문서:
  - `docs/basis-rag-p2-followup-fix-plan.md`
- 구현한 수정:
  - `delete_basis_document()`에서 `delete_basis_vectors()` 호출 전에 `validate_basis_index(conn)`를 먼저 실행하도록 변경했다.
  - `rebuild_required` 상태이면 삭제를 진행하지 않고 HTTP 409, `basis_index_unavailable`, `index_status`, `rebuild_required: true`, `errors`를 반환하도록 변경했다.
  - `validate_basis_index()`가 `basis-index.json` 파일 없음과 DB indexed chunk 존재 상태를 `inconsistent`가 아니라 `missing`으로 분류하도록 순서를 보정했다.
- 추가한 테스트:
  - `test_basis_document_delete_returns_409_when_basis_index_is_missing`
  - `test_basis_document_delete_returns_409_when_basis_index_is_inconsistent`
- 검증 결과:
  - 최초 targeted 테스트에서 missing 상태가 `inconsistent`로 분류되는 문제를 발견했고, `validate_basis_index()` 상태 분류 순서를 수정했다.
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "basis_document_delete_returns_409_when_basis_index"` 결과: 3 passed, 77 deselected
  - `py -3.13 -m compileall backend/app` 통과
  - `py -3.13 -m pytest backend/tests -q` 결과: 102 passed, 3 skipped
  - `npm run build` 통과
  - `py -3.13 scripts/check-encoding.py` 결과: `ENCODING_CHECK_OK`

## Additional Update (2026-05-31) - Validate Basis Index Consistency Before Basis Document Deletion
- Per the user's request, added the remaining P2 deletion risk as P2-3 in the follow-up plan and implemented it.
- Plan document:
  - `docs/basis-rag-p2-followup-fix-plan.md`
- Implemented:
  - `delete_basis_document()` now calls `validate_basis_index(conn)` before `delete_basis_vectors()`
  - when `rebuild_required` is true, deletion aborts with HTTP 409, `basis_index_unavailable`, `index_status`, `rebuild_required: true`, and `errors`
  - `validate_basis_index()` now classifies a missing `basis-index.json` with indexed DB chunks as `missing` rather than `inconsistent`
- Tests added:
  - `test_basis_document_delete_returns_409_when_basis_index_is_missing`
  - `test_basis_document_delete_returns_409_when_basis_index_is_inconsistent`
- Verification:
  - the first targeted test run caught the missing-state classification issue, which was fixed in `validate_basis_index()`
  - targeted pytest: 3 passed, 77 deselected
  - `py -3.13 -m compileall backend/app` passed
  - `py -3.13 -m pytest backend/tests -q`: 102 passed, 3 skipped
  - `npm run build` passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-05-31) - 현재 서비스 전체 테스트, 빌드, API, UX 검증
- 사용자 요청에 따라 현재 서비스 코드 상태에서 전체 테스트, 빌드, API smoke, UX 테스트를 진행했다.
- 실행한 기본 검증:
  - `py -3.13 -m pytest backend/tests -q`: 102 passed, 3 skipped, 5 warnings
  - `npm run build`: 통과
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
- 실행한 API smoke:
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `SMOKE_OK`
  - 실제 서버에서 법인 생성, 프로젝트 생성, PDF 업로드, 문서 분석, 최신 분석 조회, 나라장터 공고 저장/분석 smoke 흐름이 통과했다.
- 발견한 테스트 인프라 문제:
  - `scripts/ux-monkey-test.mjs`는 Playwright를 요구하지만 `frontend/package.json`에 `playwright` devDependency가 없었다.
  - Playwright 추가 후 `npm audit`에서 Vite/esbuild/PostCSS 계열 moderate 취약점이 보고되었다.
- 수정계획 문서:
  - `docs/current-service-verification-remediation-plan.md`
- 자동 수정:
  - `frontend`에 `playwright` devDependency를 추가했다.
  - `npx playwright install chromium`으로 Chromium 런타임을 설치했다.
  - `npm audit fix`로 PostCSS 취약점을 정리했다.
  - `npm audit fix --force` 후 Vite가 8.0.14로 올라갔고, peer dependency 정합성을 위해 `@vitejs/plugin-react`를 6.0.2로 업데이트했다.
  - 최종 `npm audit --audit-level=moderate`: 0 vulnerabilities
- UX 검증:
  - `powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start -BackendPort 18111 -FrontendPort 5199`로 서버 기동 확인
  - `npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531 --screenshot-dir ..\temp\ux-monkey-20260531`: `status: ok`
  - UX monkey 방문 라우트 16개: `/`, `/operations`, `/operation-runs`, `/backups`, `/nara-board`, `/nara-saved-notices`, `/notice-comparison`, `/judgment-runs`, `/nara-collection-runs`, `/documents`, `/basis-documents`, `/basis-rule-candidates`, `/basis-retrieval-evaluations`, `/corporations`, `/projects`, `/settings/integrations/nara`
  - UX monkey 스크린샷 저장 위치: `temp/ux-monkey-20260531`
  - in-app 브라우저로 주요 6개 라우트 DOM/콘솔 점검: blank page 없음, `main` landmark 1개씩 존재, console error 0건
  - in-app 브라우저 full-page screenshot은 CDP screenshot timeout이 있었지만, UX monkey Playwright screenshot은 정상 생성되어 시각 검증 산출물로 사용했다.
- 수정 후 최종 재검증:
  - `py -3.13 -m pytest backend/tests -q`: 102 passed, 3 skipped, 5 warnings
  - `npm run build`: 통과
  - `npm audit --audit-level=moderate`: 0 vulnerabilities
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - 관련 파일 `git diff --check`: 통과

## Additional Update (2026-05-31) - Full Current-Service Verification, API Smoke, And UX Tests
- Per the user's request, ran full current-service verification across tests, build, live API smoke, and UX tests.
- Baseline verification:
  - `py -3.13 -m pytest backend/tests -q`: 102 passed, 3 skipped, 5 warnings
  - `npm run build`: passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
- Live API smoke:
  - `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`: `SMOKE_OK`
  - Verified live server flows for corporation creation, project creation, PDF upload, document analysis, latest analysis lookup, and Nara notice save/analyze smoke flow.
- Test-infrastructure findings:
  - `scripts/ux-monkey-test.mjs` required Playwright, but `frontend/package.json` did not declare `playwright`.
  - After adding Playwright, `npm audit` reported moderate Vite/esbuild/PostCSS advisories.
- Remediation plan:
  - `docs/current-service-verification-remediation-plan.md`
- Automatic fixes:
  - added `playwright` as a frontend devDependency
  - installed the Playwright Chromium runtime
  - ran `npm audit fix` for PostCSS
  - ran `npm audit fix --force`, which upgraded Vite to 8.0.14, then upgraded `@vitejs/plugin-react` to 6.0.2 for peer compatibility
  - final `npm audit --audit-level=moderate`: 0 vulnerabilities
- UX verification:
  - started local servers on backend `18111` and frontend `5199`
  - `npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531 --screenshot-dir ..\temp\ux-monkey-20260531`: `status: ok`
  - UX monkey visited 16 routes including operations, backups, Nara, basis documents, rule candidates, retrieval evaluations, corporations, projects, and settings
  - screenshots saved under `temp/ux-monkey-20260531`
  - in-app browser DOM/console check covered 6 key routes with no blank pages, one `main` landmark per route, and zero console errors
  - in-app browser full-page screenshot hit a CDP screenshot timeout, but the Playwright UX monkey screenshots were generated successfully and used as the visual artifact
- Final verification after fixes:
  - `py -3.13 -m pytest backend/tests -q`: 102 passed, 3 skipped, 5 warnings
  - `npm run build`: passed
  - `npm audit --audit-level=moderate`: 0 vulnerabilities
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - related `git diff --check`: passed

## 작업 기록 (2026-05-31) - README 신규 PC 세팅 가이드 보강
- 사용자 요청에 따라 다른 PC에서 새 사용자가 쉽게 세팅하고 테스트할 수 있도록 `README.md`를 업데이트했다.
- 한국어 섹션에 `로컬 세팅과 테스트 빠른 가이드`를 추가/정리했다.
- 포함한 내용:
  - 사전 설치 버전: Python 3.13.13, Node.js 20.19.0 이상 또는 22.12.0 이상, npm, Git, PowerShell
  - 저장소 clone/pull 절차
  - 백엔드 의존성 설치
  - 프론트엔드 의존성 설치와 Playwright Chromium 설치
  - `.env.example` 기반 환경 파일 준비
  - `scripts/manage-servers.ps1` 기반 서버 실행/상태확인/중지
  - 전체 백엔드 테스트, 프론트 빌드, 인코딩 검사, npm audit
  - API smoke 테스트
  - UX monkey 테스트
  - 나라장터 API 테스트
  - 수동 서버 실행 방법
  - 자주 나는 문제와 해결 방향
- 영어 `AI / Engineering Version` 섹션에도 `Quick Setup And Verification`을 추가해 AI/엔지니어가 같은 절차를 이해할 수 있게 했다.
- 검증:
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## Additional Update (2026-05-31) - README Setup Guide For New PCs
- Updated `README.md` so another person can set up and test the project easily on a different PC.
- Added/refined the Korean `로컬 세팅과 테스트 빠른 가이드` section.
- Covered:
  - required versions: Python 3.13.13, Node.js 20.19.0+ or 22.12.0+, npm, Git, PowerShell
  - clone/pull flow
  - backend dependency installation
  - frontend dependency installation and Playwright Chromium installation
  - `.env.example` based environment file setup
  - server start/status/stop via `scripts/manage-servers.ps1`
  - backend tests, frontend build, encoding check, and npm audit
  - API smoke testing
  - UX monkey testing
  - Nara API testing
  - manual server execution
  - common troubleshooting notes
- Added an English `Quick Setup And Verification` section under `AI / Engineering Version`.
- Verification:
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-05-31) - README 나라장터 API 활용신청 안내 보강
- 사용자 질문에 따라 README의 나라장터 API 테스트 가이드에 공공데이터포털 활용신청 절차가 충분히 들어 있는지 확인했다.
- 기존 README에는 `NARA_API_SERVICE_KEY` 입력과 API 키 관리 주의는 있었지만, 사용자가 어느 페이지에서 활용신청해야 하는지까지는 명확하지 않았다.
- 공공데이터포털의 `조달청_나라장터 입찰공고정보서비스` 페이지를 확인했다.
  - URL: `https://www.data.go.kr/data/15129394/openapi.do`
  - 페이지에는 `활용신청` 버튼, REST API, JSON/XML 포맷, 개발/운영 자동승인, 개발계정 기본 트래픽 1,000건 안내가 표시된다.
- README 보강 내용:
  - 공공데이터포털 로그인
  - `조달청_나라장터 입찰공고정보서비스` 페이지 이동
  - `활용신청`
  - 승인 후 인증키 확인
  - `backend/.env`의 `NARA_API_SERVICE_KEY` 또는 PowerShell 환경변수에 키 입력
  - 인증키 원문을 README/로그/프론트엔드/Git에 남기지 말라는 주의
- 영어 Quick Setup 섹션에도 Nara API 신청 페이지와 `NARA_API_SERVICE_KEY` 입력 안내를 추가했다.

## Additional Update (2026-05-31) - README Nara API Application Guidance
- Checked whether the README clearly explains how users should apply for and enter the Nara API token.
- The README already mentioned `NARA_API_SERVICE_KEY`, but it did not clearly point users to the Public Data Portal application page.
- Verified the Public Data Portal page:
  - URL: `https://www.data.go.kr/data/15129394/openapi.do`
  - The page shows the Nara Bid Notice API, `활용신청`, REST API, JSON/XML format, automatic approval for development/operation stages, and a 1,000-request development quota.
- README updates:
  - log in to the Public Data Portal
  - open the Nara Bid Notice API page
  - apply via `활용신청`
  - retrieve the issued service key after approval
  - enter it in `backend/.env` as `NARA_API_SERVICE_KEY` or set it as a PowerShell environment variable
  - do not expose raw API keys in README, logs, frontend screens, or Git commits
- Added the Nara API application link to the English Quick Setup notes as well.

## 작업 기록 (2026-05-31) - README 문서 링크 상대경로 수정
- 사용자 요청에 따라 README의 `문서 링크` 섹션에서 클릭이 되지 않는 링크를 수정했다.
- 원인:
  - 기존 링크가 `/D:/project/wisdom_procurement/...` 형태의 로컬 절대경로였기 때문에 다른 PC, GitHub, 일반 Markdown 뷰어에서 정상 링크로 동작하지 않을 수 있었다.
- 수정:
  - 모든 문서 링크를 저장소 루트 기준 상대경로로 변경했다.
  - 예: `/D:/project/wisdom_procurement/docs/technical-design.md` -> `docs/technical-design.md`
  - `AGENTS.md`도 `/D:/project/wisdom_procurement/AGENTS.md` -> `AGENTS.md`로 변경했다.
- 검증:
  - README `문서 링크` 섹션의 링크 18개 파일 존재 확인: `README_DOC_LINKS_OK count=18`
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- README.md docs/work-log.md`: 통과

## Additional Update (2026-05-31) - Fixed README Document Links
- Fixed the broken README `문서 링크` section per the user's request.
- Cause:
  - Links used local absolute Windows paths such as `/D:/project/wisdom_procurement/...`, which do not work reliably on other PCs, GitHub, or regular Markdown viewers.
- Fix:
  - Changed all document links to repository-relative paths.
  - Example: `/D:/project/wisdom_procurement/docs/technical-design.md` -> `docs/technical-design.md`
  - Changed the agent guide link to `AGENTS.md`.
- Verification:
  - Checked all 18 README document links exist: `README_DOC_LINKS_OK count=18`
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- README.md docs/work-log.md`: passed

## 작업 기록 (2026-05-31) - README Gemini API 키 발급 안내 추가
- 사용자 요청에 따라 README에 Gemini API 사용을 위한 토큰/API 키 발급 방법을 추가했다.
- 공식 Google AI Developers 문서를 확인했다.
  - Gemini API 키는 Google AI Studio의 API keys 페이지에서 생성/관리할 수 있다.
  - Gemini SDK는 일반적으로 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY` 환경변수를 읽을 수 있다.
- README 보강 내용:
  - Google AI Studio 로그인
  - Google AI Studio API keys 페이지 이동
  - 약관 동의
  - `Create API key` 또는 `API 키 만들기`
  - Google Cloud 프로젝트 선택/생성 후 키 발급
  - `backend/.env`의 `GEMINI_API_KEY`에 입력
  - PowerShell 임시 환경변수 입력 예시
  - 이 프로젝트는 `GEMINI_API_KEY`를 표준으로 사용한다는 안내
  - Gemini API 키 원문을 README/로그/프론트엔드/Git에 남기지 말라는 주의
- 영어 Quick Setup 섹션에도 Google AI Studio API keys 링크와 `GEMINI_API_KEY` 입력 안내를 추가했다.

## Additional Update (2026-05-31) - README Gemini API Key Guide
- Added Gemini API token/key issuance guidance to the README per the user's request.
- Checked the official Google AI Developers documentation.
  - Gemini API keys can be created and managed from the Google AI Studio API keys page.
  - Gemini SDKs can generally read `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variables.
- README updates:
  - sign in to Google AI Studio
  - open the Google AI Studio API keys page
  - accept Terms of Service if prompted
  - create an API key
  - choose or create a Google Cloud project
  - copy the key into `backend/.env` as `GEMINI_API_KEY`
  - add a temporary PowerShell environment variable example
  - note that this project standardizes on `GEMINI_API_KEY`
  - warn not to expose raw Gemini API keys in README, logs, frontend screens, or Git commits
- Added the Google AI Studio API keys link to the English Quick Setup section as well.

## 작업 기록 (2026-05-31) - 실제 기준문서 RAG 및 테이블 추출 QA 계획 작성
- 사용자 요청에 따라 제공된 실제 기준문서 PDF를 대상으로 RAG 테스트와 테이블 추출 품질 검증을 진행하기 위한 계획을 먼저 작성했다.
- 대상 파일:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 사전 확인:
  - 파일 존재 확인 완료
  - 파일 크기 약 5.36MB 확인
- 신규 계획 문서:
  - `docs/real-basis-document-rag-test-plan.md`
- 계획에 포함한 내용:
  - 실제 기준문서 샘플 보관 폴더: `backend/tests/real-basis-document-samples/`
  - 원문 PDF는 기본적으로 Git에 커밋하지 않고 로컬 ignored fixture로 관리하는 정책
  - 샘플 등록 스크립트 계획
  - PDF 추출 품질 사전 분석 스크립트 계획
  - page/text/block/line/table-like line/필수 키워드 coverage 측정 계획
  - `/api/basis-documents` 업로드 기반 실제 RAG 테스트 계획
  - JSON basis index 상태 검증 계획
  - 직접생산/세부품명/생산설비/검사설비/공장등록 등 RAG 검색 질의 후보
  - 테이블 기반 질의와 chunk 의미 보존 검증 기준
  - 실패 시 PyMuPDF 정규화/청킹/테이블 metadata 보강 후보
- 이번 단계에서는 사용자 요청대로 계획만 작성했고, PDF 복사/테스트 코드 작성/RAG 실행/추출 알고리즘 변경은 하지 않았다.

## Additional Update (2026-05-31) - Real Basis Document RAG And Table Extraction QA Plan
- Per the user's request, created the plan first for testing the provided real basis-document PDF with RAG and table-heavy extraction QA.
- Target file:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- Preflight:
  - confirmed the file exists
  - confirmed size is about 5.36MB
- New plan document:
  - `docs/real-basis-document-rag-test-plan.md`
- Covered:
  - local fixture directory: `backend/tests/real-basis-document-samples/`
  - raw PDF should be treated as a local ignored fixture by default
  - sample registration script plan
  - PDF extraction preflight analysis script plan
  - page/text/block/line/table-like-line/required-term coverage metrics
  - real RAG tests via `/api/basis-documents`
  - JSON basis index validation
  - candidate RAG queries around direct production, item detail names, production equipment, inspection equipment, and factory registration
  - table-oriented query tests and chunk semantic preservation thresholds
  - potential PyMuPDF normalization, chunking, and table metadata hardening if QA fails
- No PDF copy, test implementation, RAG execution, or extraction algorithm change was performed in this planning step.

## 작업 기록 (2026-06-05) - 실제 기준문서 RAG 상세 구현계획 보강
- 사용자 요청에 따라 `docs/real-basis-document-rag-test-plan.md`에 실제 구현 가능한 수준의 상세 구현계획을 추가했다.
- 이번 작업은 계획 상세화만 진행했으며, 아직 PDF 복사/스크립트 작성/테스트 작성/RAG 실행은 하지 않았다.
- 상세화한 항목:
  - `.gitignore`에 추가할 실제 기준문서 샘플 산출물 제외 규칙
  - `backend/tests/real-basis-document-samples/README.md`와 `manifest.example.json` 작성 계획
  - `scripts/register-real-basis-document-sample.py`의 CLI 옵션, 입출력, manifest schema, 검증 기준
  - `scripts/analyze-real-basis-document-pdf.py`의 CLI 옵션, PyMuPDF 추출 지표, table-like line 탐지 휴리스틱, report schema, 성공/실패 기준
  - `backend/tests/test_real_basis_document_rag.py`의 실행 정책, 환경변수, helper 함수 구성
  - 업로드/청킹/인덱싱 테스트 케이스
  - RAG 검색 질의 테스트 케이스
  - 검색 평가 API 테스트 케이스
  - 테이블 기반 RAG 품질 테스트 케이스
  - README/샘플 README/work-log 문서화 범위
  - 기본/엄격 검증 명령
  - 구현 완료 체크리스트
- 계획상 핵심 성공 기준:
  - 실제 기준문서 업로드 후 chunk 10개 이상
  - `vector_count == chunk_count`
  - JSON basis index valid
  - RAG 질의 coverage 80% 이상
  - table-like 질의 coverage 80% 이상
  - `직접생산`, `생산설비`, `검사설비` 관련 검색 성공

## Additional Update (2026-06-05) - Detailed Real Basis Document RAG Implementation Plan
- Per the user's request, expanded `docs/real-basis-document-rag-test-plan.md` into a detailed implementation plan.
- This step only detailed the plan; no PDF copy, script implementation, test implementation, or RAG execution was performed.
- Added details for:
  - gitignore rules for local real-basis artifacts
  - sample README and `manifest.example.json`
  - `scripts/register-real-basis-document-sample.py` CLI options, inputs/outputs, manifest schema, and validation criteria
  - `scripts/analyze-real-basis-document-pdf.py` CLI options, PyMuPDF extraction metrics, table-like line heuristics, report schema, and success/failure criteria
  - `backend/tests/test_real_basis_document_rag.py` execution policy, environment variables, and helper functions
  - upload/chunk/index test case
  - RAG search query test case
  - retrieval evaluation API test case
  - table-aware RAG QA test case
  - README/sample README/work-log documentation scope
  - basic and strict verification commands
  - implementation completion checklist
- Key planned thresholds:
  - at least 10 chunks after upload
  - `vector_count == chunk_count`
  - valid JSON basis index
  - at least 80% RAG query coverage
  - at least 80% table-like query coverage
  - successful searches around direct production, production equipment, and inspection equipment

## 작업 기록 (2026-06-05) - 실제 기준문서 RAG 테스트 구현 및 실행
- 사용자 요청에 따라 `docs/real-basis-document-rag-test-plan.md`의 상세 구현계획을 실제 코드와 테스트로 구현했다.
- 추가/수정 파일:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `backend/tests/real-basis-document-samples/manifest.example.json`
  - `scripts/register-real-basis-document-sample.py`
  - `scripts/analyze-real-basis-document-pdf.py`
  - `backend/tests/test_real_basis_document_rag.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/work-log.md`
- 실제 기준문서 PDF를 로컬 테스트 샘플 폴더에 복사하고 `manifest.json`을 생성했다.
  - 원본: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
  - 저장 위치: `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
  - sha256: `e4672ed3d7f4626064729f4db9a329f30f7f9109d9fb19df1b16d5865edfd8c7`
- 실제 PDF와 `manifest.json`, `extraction-report.json`, `extraction-baseline.json`은 `.gitignore` 대상 로컬 산출물로 관리하도록 했다.
- 추출 분석 결과:
  - 파일 크기: 5,360,737 bytes
  - 페이지 수: 489
  - 추출 문자 수: 702,598
  - page coverage: 1.0
  - 청크 수: 495
  - table-like line 후보 수: 80
  - 필수 키워드 `직접생산`, `확인기준`, `중소기업자간`, `경쟁제품`, `세부품명`, `생산시설`, `검사설비` 모두 확인
- 구현한 테스트:
  - 실제 기준문서 샘플 manifest/PDF 검증
  - `/api/basis-documents` 업로드, 청킹, JSON 인덱싱 검증
  - `/api/basis-search` RAG 검색 citation 후보 검증
  - `/api/basis-retrieval-evaluations` 검색 평가 저장/coverage 검증
  - 테이블형 라인 기반 query가 RAG 검색 가능한지 검증
- 테스트 실행 결과:
  - `py -3.13 -m py_compile scripts/register-real-basis-document-sample.py scripts/analyze-real-basis-document-pdf.py backend/tests/test_real_basis_document_rag.py`: 통과
  - `py -3.13 scripts/analyze-real-basis-document-pdf.py --strict`: 통과
  - `$env:RUN_REAL_BASIS_RAG_TESTS='1'; py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q`: `5 passed, 10 subtests passed`
  - `py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q`: `5 skipped`
  - `py -3.13 -m pytest backend/tests -q`: `102 passed, 8 skipped`
  - `py -3.13 scripts/check-encoding.py`: 통과
- PyMuPDF에서 `SwigPyPacked`, `SwigPyObject`, `swigvarlink` 관련 DeprecationWarning이 출력되지만 테스트 실패는 아니며 현재 known warning으로 기록한다.
- 이번 구현에서 파서/청킹 알고리즘 자체 수정은 필요하지 않았다.

## Additional Update (2026-06-05) - Real Basis Document RAG Test Implementation
- Implemented the detailed real-basis-document RAG QA plan.
- Added local sample management, extraction analysis, and opt-in real RAG pytest coverage.
- Changed files:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `backend/tests/real-basis-document-samples/manifest.example.json`
  - `scripts/register-real-basis-document-sample.py`
  - `scripts/analyze-real-basis-document-pdf.py`
  - `backend/tests/test_real_basis_document_rag.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/work-log.md`
- Local ignored artifacts were generated for the copied PDF, manifest, extraction report, and baseline.
- Extraction QA passed with 702,598 extracted characters, 489 pages, 495 chunks, and 80 table-like line candidates.
- Opt-in real RAG tests passed with 5 tests and 10 subtests.
- Full backend pytest passed with 102 passed and 8 skipped.
- Encoding check passed.

## 작업 기록 (2026-06-05) - 실제 기준문서 PDF 파싱 텍스트와 외부 TXT 비교
- 사용자 요청에 따라 외부에서 추출한 TXT 기준 텍스트와 우리 서비스가 직접 PDF를 파싱해 추출한 텍스트를 비교했다.
- 기준 TXT:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).txt`
- 추가/수정 파일:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `scripts/compare-real-basis-document-txt.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/work-log.md`
- 생성된 로컬 ignored 산출물:
  - `backend/tests/real-basis-document-samples/text-comparison-report.json`
- 실행 명령:
  - `py -3.13 -m py_compile scripts/compare-real-basis-document-txt.py`
  - `py -3.13 scripts/compare-real-basis-document-txt.py --reference-txt "<TXT 경로>" --strict`
  - `py -3.13 scripts/check-encoding.py`
- 비교 결과:
  - TXT 인코딩: `utf-8-sig`
  - PDF page count: 489
  - 서비스 파싱 텍스트: 702,598자
  - TXT 기준 텍스트: 728,596자
  - compact 기준 문자 수: 서비스 554,921자, TXT 554,696자
  - service token multiset recall in TXT: 0.9001
  - TXT token multiset recall in service: 0.7725
  - service unique token recall in TXT: 0.7719
  - TXT unique token recall in service: 0.8441
  - service char 5-gram recall in TXT: 0.8103
  - TXT char 5-gram recall in service: 0.8107
  - service line coverage in TXT: 0.9948
  - TXT line coverage in service: 0.9495
  - numeric recall: service -> TXT 0.9880, TXT -> service 0.9970
  - 필수 키워드 `직접생산`, `확인기준`, `중소기업자간`, `경쟁제품`, `세부품명`, `생산시설`, `검사설비` 모두 양쪽 텍스트에서 확인
- 해석:
  - 우리 서비스가 추출한 텍스트의 상당 부분은 외부 TXT와 일치한다.
  - TXT 기준 텍스트가 서비스 텍스트보다 약 26,000자 더 길고 토큰 수도 많아, TXT 전체를 서비스가 모두 회수하는 비율은 상대적으로 낮다.
  - line coverage와 숫자 recall은 높아 조항/숫자 기반 RAG 검색에는 충분히 안정적인 편으로 판단한다.
- 검증:
  - 비교 스크립트 strict 기준 통과
  - 인코딩 검사 통과

## Additional Update (2026-06-05) - Real Basis PDF Extraction Compared Against External TXT
- Compared service-side direct PDF parsing output against the user's external TXT extraction.
- Added `scripts/compare-real-basis-document-txt.py` and documented it in the sample README.
- Generated local ignored report: `backend/tests/real-basis-document-samples/text-comparison-report.json`.
- Result:
  - service text: 702,598 characters
  - external TXT: 728,596 characters
  - compact character counts were close: service 554,921, TXT 554,696
  - service token multiset recall in TXT: 0.9001
  - TXT token multiset recall in service: 0.7725
  - service char 5-gram recall in TXT: 0.8103
  - TXT char 5-gram recall in service: 0.8107
  - service line coverage in TXT: 0.9948
  - TXT line coverage in service: 0.9495
  - numeric recall was high in both directions
  - all required terms were found in both texts
- Strict comparison thresholds passed.

## 작업 기록 (2026-06-05) - 실제 기준문서 DOCX 표 포함 비교 지원
- 사용자 지적에 따라 DOCX 기준 파일에 표가 존재한다는 점을 반영해, 기존 비교 스크립트가 `.docx` 기준 파일도 처리하도록 보강했다.
- 수정 파일:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `scripts/compare-real-basis-document-txt.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/work-log.md`
- 변경 내용:
  - `--reference-file` 옵션 추가
  - 기존 `--reference-txt` 옵션은 하위 호환용으로 유지
  - `.txt`와 `.docx` 기준 파일 자동 분기
  - DOCX의 `document.paragraphs`, `document.tables` 기반 문단/표 메타데이터 수집
  - DOCX 패키지 내부 `word/*.xml`의 `w:t` 텍스트를 직접 읽어 표/텍스트박스/분할 XML 텍스트를 포함
  - DOCX 비교 리포트 산출물 `backend/tests/real-basis-document-samples/docx-comparison-report.json`을 `.gitignore`에 추가
- 실제 DOCX 비교 실행:
  - 기준 DOCX: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx`
  - 실행 명령: `py -3.13 scripts/compare-real-basis-document-txt.py --reference-file "<DOCX 경로>" --output backend/tests/real-basis-document-samples/docx-comparison-report.json --strict`
- 중요한 발견:
  - `python-docx` 문단/표 셀 방식만 쓰면 DOCX 추출 텍스트가 387,786자에 그쳐 strict 비교가 실패했다.
  - 같은 DOCX에서 패키지 XML `w:t` 텍스트를 직접 읽으면 720,588자가 추출되어 PDF/TXT 기준과 유사한 길이가 됐다.
- DOCX 기준 비교 결과:
  - DOCX 문단 수: 3,576
  - DOCX 표 수: 744
  - DOCX 표 셀 수: 15,523
  - 서비스 파싱 텍스트: 702,598자
  - DOCX XML 기준 텍스트: 720,588자
  - compact 기준 문자 수: 서비스 554,921자, DOCX 550,700자
  - service token multiset recall in DOCX: 0.9002
  - DOCX token multiset recall in service: 0.7721
  - service char 5-gram recall in DOCX: 0.8425
  - DOCX char 5-gram recall in service: 0.8489
  - service line coverage in DOCX: 0.9270
  - DOCX line coverage in service: 0.8992
  - numeric recall: service -> DOCX 0.9905, DOCX -> service 0.9971
  - strict 비교 기준 통과
- 기존 TXT 비교도 재실행해 strict 기준 통과를 확인했다.

## Additional Update (2026-06-05) - DOCX Table-Aware Reference Comparison Support
- Extended `scripts/compare-real-basis-document-txt.py` to accept `.docx` reference files through `--reference-file`.
- Kept `--reference-txt` for backward compatibility.
- DOCX support now records paragraph/table/table-cell metadata and uses raw DOCX package XML `w:t` text as the comparison reference when it captures more text than plain `python-docx`.
- Generated local ignored report: `backend/tests/real-basis-document-samples/docx-comparison-report.json`.
- Actual DOCX result:
  - DOCX paragraphs: 3,576
  - DOCX tables: 744
  - DOCX table cells: 15,523
  - service text: 702,598 characters
  - DOCX XML reference text: 720,588 characters
  - service token multiset recall in DOCX: 0.9002
  - DOCX token multiset recall in service: 0.7721
  - service char 5-gram recall in DOCX: 0.8425
  - DOCX char 5-gram recall in service: 0.8489
  - service line coverage in DOCX: 0.9270
  - DOCX line coverage in service: 0.8992
  - numeric recall was high in both directions
  - strict comparison thresholds passed

## 작업 기록 (2026-06-05) - DOCX 기준 비교 테스트 코드 추가 및 재검증
- 사용자 요청에 따라 DOCX 기준 파일 비교 구현을 테스트 코드로 고정하고 실제 비교테스트를 재실행했다.
- 추가/수정 파일:
  - `backend/tests/test_real_basis_reference_compare.py`
  - `scripts/compare-real-basis-document-txt.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/work-log.md`
- 테스트 코드 내용:
  - DOCX 헤더, 본문 문단, 표 셀 텍스트가 XML 기반 기준 추출에 포함되는지 검증
  - TXT 기준 파일 인코딩 감지와 한글 토큰 비교 recall 검증
  - 지원하지 않는 기준 파일 확장자 거부 검증
- 구현 중 발견 및 수정:
  - 작은 DOCX 샘플에서는 `[TABLE]` 마커 때문에 `python-docx` 문자열이 XML 문자열보다 길 수 있어 XML 추출 대신 python-docx 추출이 선택되는 문제가 있었다.
  - DOCX 기준 비교에서는 XML이 헤더/표/분할 XML 텍스트를 더 포괄하므로, DOCX는 XML `w:t` 텍스트를 우선 사용하도록 수정했다.
- 실제 DOCX 비교 재실행:
  - 기준 DOCX: `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx`
  - 리포트: `backend/tests/real-basis-document-samples/docx-comparison-report.json`
  - 결과: strict 기준 통과
  - 서비스 파싱 텍스트: 702,598자
  - DOCX XML 기준 텍스트: 720,588자
  - service token multiset recall in DOCX: 0.9002
  - DOCX token multiset recall in service: 0.7721
  - service char 5-gram recall in DOCX: 0.8425
  - DOCX char 5-gram recall in service: 0.8489
  - service line coverage in DOCX: 0.9270
  - DOCX line coverage in service: 0.8992
  - numeric recall: service -> DOCX 0.9905, DOCX -> service 0.9971
- 재검증:
  - `py -3.13 -m pytest backend/tests/test_real_basis_reference_compare.py -q`: `3 passed`
  - `py -3.13 scripts/compare-real-basis-document-txt.py --reference-file "<DOCX 경로>" --output backend/tests/real-basis-document-samples/docx-comparison-report.json --strict`: 통과
  - `py -3.13 scripts/compare-real-basis-document-txt.py --reference-file "<TXT 경로>" --output backend/tests/real-basis-document-samples/text-comparison-report.json --strict`: 통과
  - `py -3.13 -m pytest backend/tests -q`: `105 passed, 8 skipped`
  - `py -3.13 -m py_compile scripts/compare-real-basis-document-txt.py backend/tests/test_real_basis_reference_compare.py`: 통과

## Additional Update (2026-06-05) - DOCX Reference Comparison Tests And Re-Run
- Added `backend/tests/test_real_basis_reference_compare.py`.
- The new tests verify DOCX XML extraction includes header/body/table-cell text, TXT encoding detection and Korean token recall, and unsupported reference extension rejection.
- Fixed the DOCX reference extractor to prefer DOCX XML `w:t` text whenever available.
- Re-ran the actual real-basis DOCX comparison; strict thresholds passed.
- Re-ran the actual TXT comparison; strict thresholds passed.
- Targeted regression test passed with 3 tests.
- Full backend pytest passed with 105 passed and 8 skipped.

## 작업 기록 (2026-06-05) - MD 기준 비교 및 추출 로직 보완 계획 작성
- 사용자 요청에 따라 TXT/DOCX에 이어 MD 기준 파일 비교를 추가로 진행하고, 3개 기준 파일 비교 결과를 분석해 서비스 추출 로직 보완 계획을 작성했다.
- 기준 MD:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`
- 추가/수정 파일:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `backend/tests/test_real_basis_reference_compare.py`
  - `scripts/compare-real-basis-document-txt.py`
  - `docs/real-basis-document-rag-test-plan.md`
  - `docs/basis-document-extraction-improvement-plan.md`
  - `docs/work-log.md`
- 구현:
  - 비교 스크립트가 `.md`, `.markdown` 기준 파일을 지원하도록 확장
  - MD 기준 파일 회귀 테스트 추가
  - MD 비교 리포트 산출물 `backend/tests/real-basis-document-samples/md-comparison-report.json`을 `.gitignore`에 추가
- 실제 비교 테스트 재실행:
  - TXT strict 비교 통과
  - DOCX strict 비교 통과
  - MD strict 비교 통과
- MD 비교 결과:
  - 서비스 파싱 텍스트: 702,598자
  - MD 기준 텍스트: 1,719,849자
  - compact 기준 문자 수: 서비스 554,921자, MD 1,314,511자
  - service token multiset recall in MD: 0.9073
  - MD token multiset recall in service: 0.3541
  - service char 5-gram recall in MD: 0.9358
  - MD char 5-gram recall in service: 0.3951
  - service line coverage in MD: 0.9955
  - MD line coverage in service: 0.5200
  - numeric recall: service -> MD 0.9979, MD -> service 0.3625
- 3개 비교 결과 해석:
  - TXT/DOCX 기준으로는 서비스 PDF 직접 추출이 본문/숫자/핵심 키워드를 안정적으로 회수한다.
  - MD 기준은 TXT/DOCX보다 훨씬 길고 Markdown 표/설명/논리페이지/표 변환 결과를 포함하므로, raw reference recall이 낮게 나오는 것이 자연스럽다.
  - MD 비교의 핵심 의미는 현재 서비스가 표 구조와 행/열/논리페이지 metadata를 충분히 보존하지 않는다는 점이다.
- 작성한 보완 계획:
  - `docs/basis-document-extraction-improvement-plan.md`
  - 핵심 방향: plain text 추출 강화보다 table-aware extraction, table row chunking, logical page metadata, table citation metadata 보강

## Additional Update (2026-06-05) - MD Reference Comparison And Extraction Improvement Plan
- Added MD/Markdown reference support to `scripts/compare-real-basis-document-txt.py`.
- Added MD regression coverage to `backend/tests/test_real_basis_reference_compare.py`.
- Re-ran TXT, DOCX, and MD comparisons; all strict thresholds passed.
- Generated local ignored MD report: `backend/tests/real-basis-document-samples/md-comparison-report.json`.
- MD comparison result:
  - service text: 702,598 characters
  - MD reference text: 1,719,849 characters
  - service token multiset recall in MD: 0.9073
  - MD token multiset recall in service: 0.3541
  - service char 5-gram recall in MD: 0.9358
  - MD char 5-gram recall in service: 0.3951
  - service line coverage in MD: 0.9955
  - MD line coverage in service: 0.5200
- Wrote `docs/basis-document-extraction-improvement-plan.md`.
- Main conclusion: current PDF extraction is stable for body text and numbers, but RAG quality needs table-aware extraction, table-row chunking, logical-page metadata, and table citation metadata.

## 작업 기록 (2026-06-05) - 기준문서 PDF Markdown 재생성 및 기준 MD 비교
- 사용자 요청에 따라 기준문서 PDF를 직접 추출한 뒤 텍스트와 테이블을 포함한 Markdown으로 재생성하고, 사용자가 업로드한 기준 MD와 비교했다.
- 구현계획 문서:
  - `docs/basis-document-md-regeneration-comparison-plan.md`
- 추가/수정 파일:
  - `.gitignore`
  - `backend/tests/real-basis-document-samples/README.md`
  - `backend/tests/test_real_basis_md_regeneration.py`
  - `docs/basis-document-extraction-improvement-plan.md`
  - `docs/basis-document-md-regeneration-comparison-plan.md`
  - `docs/work-log.md`
  - `scripts/regenerate-real-basis-document-md.py`
- 생성 산출물:
  - `backend/tests/real-basis-document-samples/regenerated-basis-document.md`
  - `backend/tests/real-basis-document-samples/md-regeneration-comparison-report.json`
- 구현 내용:
  - manifest 또는 `--pdf` 입력으로 실제 기준문서 PDF를 읽도록 구성
  - 물리 1쪽은 단일 논리 페이지로, 2쪽부터는 좌/우 2단 논리 페이지로 분할
  - 각 논리 페이지의 clipped text를 추출
  - PyMuPDF `find_tables(clip=...)`로 논리 페이지별 표 후보를 추출
  - 표 후보를 Markdown table로 렌더링
  - 재생성 Markdown과 사용자 제공 기준 MD의 텍스트/숫자/라인/table row coverage를 비교
- 실행 결과:
  - 물리 페이지: 489
  - 논리 페이지: 977
  - 재생성 텍스트 문자 수: 697,837
  - 재생성 Markdown 문자 수: 1,635,197
  - 감지 표 수: 3,034
  - 감지 표 row 수: 11,900
  - 기준 MD 문자 수: 1,731,919
  - 기준 MD table 수: 1,928
  - 기준 MD table row 수: 11,351
  - regenerated token recall in reference: 0.9303
  - reference token recall in regenerated: 0.7931
  - regenerated char 5-gram recall in reference: 0.8665
  - reference char 5-gram recall in regenerated: 0.8171
  - regenerated table row coverage in reference: 0.7060
  - reference table row coverage in regenerated: 0.7644
  - strict 기준 통과
- 해석:
  - 977개 논리 페이지 재생성이 기준 MD의 원문 페이지 체계와 일치한다.
  - 단순 plain text 추출보다 Markdown 재생성 방식이 기준 MD와 더 잘 맞는다.
  - 표 row coverage는 기준선으로 사용할 수 있으나 최종 품질로 보기에는 아직 부족하다.
  - PyMuPDF `find_tables()`가 짧은 제목/고시문 조각을 표로 과검출하는 사례가 있어 table candidate filtering, 인접 table merge, row 품질 점수화가 다음 보강 우선순위다.

## Additional Update (2026-06-05) - PDF To Markdown Regeneration And Reference MD Comparison
- Implemented `scripts/regenerate-real-basis-document-md.py`.
- Added targeted tests in `backend/tests/test_real_basis_md_regeneration.py`.
- The script regenerates Markdown from the real basis-document PDF with logical page metadata, clipped text, and detected Markdown tables.
- The regenerated Markdown was compared against the user-provided reference MD.
- Generated local ignored artifacts:
  - `backend/tests/real-basis-document-samples/regenerated-basis-document.md`
  - `backend/tests/real-basis-document-samples/md-regeneration-comparison-report.json`
- Result:
  - physical pages: 489
  - logical pages: 977
  - regenerated Markdown characters: 1,635,197
  - detected tables: 3,034
  - detected table rows: 11,900
  - reference MD characters: 1,731,919
  - reference MD table rows: 11,351
  - regenerated token recall in reference: 0.9303
  - reference token recall in regenerated: 0.7931
  - regenerated table row coverage in reference: 0.7060
  - reference table row coverage in regenerated: 0.7644
  - strict thresholds passed
- Main follow-up: reduce false-positive table detection before using table rows as final RAG chunks.

## 작업 기록 (2026-06-05) - OpenDataLoader PDF 리더 전환 검토
- 사용자 요청에 따라 `opendataloader-project/opendataloader-pdf`를 현재 PDF 리더로 교체할 수 있는지 검토했다.
- 작성 문서:
  - `docs/opendataloader-pdf-reader-review.md`
- 확인한 외부 정보:
  - GitHub 저장소: `https://github.com/opendataloader-project/opendataloader-pdf`
  - PyPI 패키지: `opendataloader-pdf`
  - 최신 확인 버전: `2.4.7`
  - 라이선스: Apache-2.0
  - 요구사항: Java 11 이상, Python 3.10 이상
- 현재 서비스 분석:
  - PDF 추출 진입점은 `backend/app/pipelines/parser.py::extract_document()`
  - 현재 PDF 엔진은 PyMuPDF `page.get_text("blocks")`
  - 기준문서 파이프라인은 평문을 paragraph-window chunk로 변환
  - table id, row index, column headers, bbox, logical page metadata가 부족함
- 로컬 PoC:
  - OpenJDK 25 확인
  - `temp/opendataloader-venv` 임시 venv에 `opendataloader-pdf==2.4.7` 설치
  - 기준문서 앞 6쪽 변환: 약 0.92초, JSON/Markdown/Text 생성
  - 기준문서 120-125쪽 변환: 약 9.37초, JSON/Markdown/Text 생성
  - 120-125쪽 JSON 요소:
    - paragraph 426
    - table cell 407
    - table row 136
    - list item 95
    - list 43
    - table 27
    - heading 6
    - caption 4
  - 2행 이상 table 21개 확인
- 결론:
  - 기준문서 RAG와 table-row chunk에는 OpenDataLoader가 유리함
  - 단순 공고문 PDF까지 전면 교체하기에는 Java 의존성, 처리 시간, 출력 차이 리스크가 있음
  - 권장 방향은 OpenDataLoader를 기준문서/table-heavy PDF 보조 엔진으로 도입하고 PyMuPDF fallback을 유지하는 것

## Additional Update (2026-06-05) - OpenDataLoader PDF Reader Review
- Reviewed `opendataloader-project/opendataloader-pdf` as a possible replacement for the current PyMuPDF reader.
- Added `docs/opendataloader-pdf-reader-review.md`.
- Verified local prerequisites:
  - Java OpenJDK 25
  - Python 3.13
  - `opendataloader-pdf==2.4.7` in a temporary ignored venv
- Ran PoC conversions:
  - real basis first 6 pages: 0.92s
  - real basis pages 120-125: 9.37s
- Pages 120-125 produced structured JSON table elements:
  - 27 tables
  - 136 table rows
  - 407 table cells
  - 21 tables with at least two rows
- Recommendation:
  - do not fully replace PyMuPDF immediately
  - add OpenDataLoader as an optional basis-document/table-heavy PDF adapter
  - keep PyMuPDF as fallback for simple Nara notice PDFs and Java/package/timeout failures

## 작업 기록 (2026-06-05) - OpenDataLoader PDF 리더 교체 계획 및 테스트 계획 작성
- 사용자 요청에 따라 `opendataloader-project/opendataloader-pdf`를 PDF 리더 엔진으로 교체하기 위한 구현계획과 테스트계획을 작성했다.
- 작성 문서:
  - `docs/opendataloader-pdf-replacement-test-plan.md`
- 계획 방향:
  - 기본 PDF 리더를 OpenDataLoader 중심으로 전환
  - PyMuPDF는 제거하지 않고 fallback 엔진으로 유지
  - 기준문서 PDF는 OpenDataLoader JSON/Markdown/table metadata를 우선 사용
  - 나라장터 공고문 PDF는 회귀 테스트 통과 전까지 `auto` 모드로 보호
- 구현 단계:
  - ODL-1 의존성 및 설정 추가
  - ODL-2 PDF reader adapter 분리
  - ODL-3 OpenDataLoader JSON/Markdown 파싱
  - ODL-4 표 후보 필터링
  - ODL-5 기준문서 table-row chunk 추가
  - ODL-6 JSON basis index table metadata 확장
  - ODL-7 API/UX 반영
  - ODL-8 문서 및 운영 가이드 보강
- 테스트 계획:
  - 단위 테스트
  - 통합 테스트
  - 실제 기준문서 전체 489쪽 QA
  - 사용자 제공 TXT/DOCX/MD 기준 비교
  - 나라장터 PDF 30개 샘플 회귀 테스트
  - Java/패키지/timeout/fallback 실패 복구 테스트
  - 성능 테스트
  - UX/API 테스트
- 합격 기준:
  - backend 전체 테스트 통과
  - 실제 기준문서 전체 변환 성공
  - 기준 MD 대비 table-row coverage 개선
  - TXT/DOCX 본문/숫자 추출 회귀 없음
  - 나라장터 PDF 샘플 회귀 없음
  - Java/ODL 실패 시 PyMuPDF fallback 정상 작동

## Additional Update (2026-06-05) - OpenDataLoader PDF Replacement And Test Plan
- Added `docs/opendataloader-pdf-replacement-test-plan.md`.
- The plan defines a replacement path from PyMuPDF-centered extraction to OpenDataLoader-centered extraction.
- PyMuPDF remains as fallback for Java/package/timeout/conversion failures.
- Implementation phases:
  - dependencies/config
  - reader adapter split
  - ODL JSON/Markdown parsing
  - table candidate filtering
  - basis table-row chunks
  - JSON basis index metadata extension
  - API/UX updates
  - docs and rollout guide
- Test plan includes unit, integration, real basis PDF QA, Nara 30-PDF regression, failure recovery, performance, and UX/API tests.

## 작업 기록 (2026-06-05) - 사용자 제공 기준문서 PDF 고정 테스트 대상 추가
- 사용자 요청에 따라 OpenDataLoader PDF 리더 교체 계획에 실제 테스트 대상 PDF를 명시적으로 추가했다.
- 수정 문서:
  - `docs/opendataloader-pdf-replacement-test-plan.md`
- 고정 원본 PDF:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 테스트용 repo 샘플 경로:
  - `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 확인:
  - 사용자 제공 원본 PDF 경로가 현재 PC에 존재함을 확인했다.
- 계획에 추가한 필수 실행 시나리오:
  - `PDF_READER_ENGINE=opendataloader` 전체 변환
  - `PDF_READER_ENGINE=auto` 전체 변환
  - OpenDataLoader 실패 simulation 후 PyMuPDF fallback 확인
  - ODL Markdown/JSON 기반 재생성 MD와 사용자 제공 기준 MD 비교
  - table-row chunk 생성 후 직접생산 조건 검색 QA
  - 기준문서 재처리 실패 simulation 후 기존 chunk/index 보존 확인

## Additional Update (2026-06-05) - Fixed User Basis PDF Added To ODL Replacement QA Plan
- Updated `docs/opendataloader-pdf-replacement-test-plan.md`.
- Added the user-provided basis PDF as the fixed real-basis QA target.
- Verified that the source PDF path exists on the current PC.
- Added required scenarios for OpenDataLoader, auto mode, fallback simulation, regenerated Markdown comparison, table-row search QA, and failed reprocessing preservation.

## 작업 기록 (2026-06-05) - OpenDataLoader PDF 리더 교체 구현 및 QA 완료
- 사용자 요청에 따라 계획대로 PDF 리더 엔진을 OpenDataLoader 중심 `auto` 모드로 전환했다.
- 구현 파일:
  - `backend/app/pipelines/pdf_readers.py`
  - `backend/app/pipelines/parser.py`
  - `backend/app/pipelines/basis_document.py`
  - `backend/app/main.py`
  - `backend/app/core/config.py`
  - `backend/requirements.txt`
  - `backend/.env.example`
  - `frontend/src/app/api.ts`
  - `frontend/src/app/types.ts`
- 문서 보강:
  - `README.md`
  - `docs/technology-summary.md`
  - `docs/opendataloader-pdf-replacement-test-plan.md`
  - `docs/work-log.md`
- 구현 내용:
  - `opendataloader-pdf==2.4.7` 의존성 추가
  - `OpenDataLoaderPdfReader`, `PyMuPdfPdfReader`, `AutoPdfReader` adapter 분리
  - 기본 엔진을 `PDF_READER_ENGINE=auto`로 설정
  - Java/package/timeout/conversion 실패 시 PyMuPDF fallback 유지
  - OpenDataLoader JSON/Markdown에서 table metadata 추출
  - 의미 없는 1행 제목 table filtering 추가
  - 기준문서 처리 시 `table_row` chunk 생성
  - 기준문서 metadata 저장 시 전체 table payload 대신 preview만 저장해 DB metadata 비대화 방지
  - PDF 리더 상태 API 추가: `GET /api/settings/pdf-reader/status`
  - OpenDataLoader 실제 기준문서 QA 스크립트 추가: `scripts/run-opendataloader-real-basis-qa.py`
  - PDF 리더 설정값 `PDF_READER_ODL_FORMAT`을 실제 변환 인자에 반영하고, RAG metadata 보존을 위해 JSON 출력은 항상 포함되도록 보강
- 실제 기준문서 QA:
  - 대상: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
  - PDF page count: 489
  - `PDF_READER_ENGINE=opendataloader`: 통과
  - `PDF_READER_ENGINE=auto`: 통과
  - OpenDataLoader timeout simulation 후 PyMuPDF fallback: 통과
  - OpenDataLoader table count: 1,566
  - OpenDataLoader table row count: 10,637
  - 기준문서 table-row chunk count: 9,069
  - service row token coverage in reference MD: 1.0
  - reference MD row token coverage in service: 0.9795
  - exact table row coverage는 기준 MD와 ODL Markdown의 줄바꿈/셀 병합 차이 때문에 warning으로 유지
- 나라장터 PDF 회귀 QA:
  - Phase 1.7 live samples with `PDF_READER_ENGINE=auto`: `3 passed`, `90 subtests passed`
  - Phase 2 basis QA samples with `PDF_READER_ENGINE=auto`: `2 passed`, `60 subtests passed`
- 최종 테스트:
  - `py -3.13 -m py_compile backend/app/main.py backend/app/pipelines/pdf_readers.py backend/app/pipelines/parser.py backend/app/pipelines/basis_document.py backend/tests/test_api_flows.py backend/tests/test_pdf_readers.py backend/tests/test_basis_table_chunks.py scripts/run-opendataloader-real-basis-qa.py`: 통과
  - `py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_api_flows.py::ApiFlowTests::test_pdf_reader_status_exposes_engine_health_without_secrets -q`: `8 passed`
  - `py -3.13 -m pytest backend/tests -q`: `118 passed`, `8 skipped`
  - `npm --prefix frontend run build`: 통과
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: trailing whitespace 오류 없음, Windows CRLF 변환 warning만 출력

## Additional Update (2026-06-05) - OpenDataLoader PDF Reader Replacement Implemented And QA Completed
- Implemented the planned OpenDataLoader-centered PDF reader replacement.
- Key implementation:
  - added `opendataloader-pdf==2.4.7`
  - added `backend/app/pipelines/pdf_readers.py`
  - split PDF readers into `OpenDataLoaderPdfReader`, `PyMuPdfPdfReader`, and `AutoPdfReader`
  - set default operational mode to `PDF_READER_ENGINE=auto`
  - kept PyMuPDF fallback for Java/package/timeout/conversion failures
  - extracted OpenDataLoader table metadata from JSON/Markdown
  - filtered one-row title tables
  - added basis-document `table_row` chunks
  - added PDF reader status API: `GET /api/settings/pdf-reader/status`
  - added real basis QA script: `scripts/run-opendataloader-real-basis-qa.py`
  - wired `PDF_READER_ODL_FORMAT` into conversion args while always preserving JSON output for RAG metadata
- Real basis QA:
  - fixed basis PDF page count: 489
  - `PDF_READER_ENGINE=opendataloader`: passed
  - `PDF_READER_ENGINE=auto`: passed
  - timeout simulation with PyMuPDF fallback: passed
  - table count: 1,566
  - table row count: 10,637
  - basis table-row chunk count: 9,069
  - service row token coverage in reference MD: 1.0
  - reference MD row token coverage in service: 0.9795
  - exact table-row coverage remains a warning because of whitespace, line-break, and cell-merge differences between the reference MD and ODL Markdown
- Nara PDF regression QA:
  - Phase 1.7 live samples with `PDF_READER_ENGINE=auto`: `3 passed`, `90 subtests passed`
  - Phase 2 basis QA samples with `PDF_READER_ENGINE=auto`: `2 passed`, `60 subtests passed`
- Final verification:
  - py_compile passed
  - targeted PDF reader/API tests: `8 passed`
  - full backend tests: `118 passed`, `8 skipped`
  - frontend build passed
  - encoding check passed
  - `git diff --check` reported no whitespace errors, only Windows CRLF conversion warnings

## 작업 기록 (2026-06-05) - 전체 코드리뷰: PDF 리더 및 RAG 버그 수정
- 사용자 요청에 따라 전체 코드 리뷰를 진행했고, 특히 PDF 리더와 기준문서 RAG 코드를 자세히 재검토했다.
- 개선 제안이 아니라 실제 버그/문제점으로 판단한 항목만 수정했다.
- 발견 및 수정한 문제:
  - PDF 리더 상태 확인에서 `java -version` timeout/OSError가 원시 예외로 튀면 `/api/settings/pdf-reader/status`가 500으로 깨질 수 있었다.
    - `OpenDataLoaderPdfReader.status()`가 timeout/OSError를 상태 오류 문자열로 정규화하도록 수정했다.
  - 강제 OpenDataLoader 변환에서 subprocess timeout이 `PdfReaderError`가 아니라 원시 `TimeoutExpired`로 전파될 수 있었다.
    - `_run_convert()`에서 timeout/OSError를 `PdfReaderError`로 변환하도록 수정했다.
  - OpenDataLoader page metadata의 `char_count`만 사용하면 페이지 사이 `\n\n` 구분자만큼 offset이 누적 drift되어 기준문서 citation page metadata가 뒤쪽 페이지에서 틀어질 수 있었다.
    - `render_opendataloader_payload()`가 `char_start`/`char_end`를 기록하고, `basis_page_ranges()`가 명시 offset을 우선 사용하도록 수정했다.
  - table-row chunk 생성 시 빈 header cell을 제거해 뒤쪽 컬럼명이 앞당겨지는 문제가 있었다.
    - 빈 header도 위치 보존하고 빈 컬럼은 `col_n` fallback으로 표시하도록 수정했다.
  - RAG 검색 점수가 query token의 고유 매칭이 아니라 chunk token 빈도 합으로 계산되어, 같은 단어가 반복된 청크가 여러 조건을 고르게 포함한 청크보다 상위에 노출될 수 있었다.
    - `basis_search_score()`를 추가해 고유 query token coverage 기준으로 검색 점수를 계산하도록 수정했다.
    - 승인 규칙 후보 매칭 점수도 반복 token 과대평가를 막도록 동일하게 수정했다.
- 추가/수정 테스트:
  - Java timeout status 정규화 테스트
  - OpenDataLoader timeout -> `PdfReaderError` 정규화 테스트
  - OpenDataLoader page `char_start`/`char_end` metadata 테스트
  - 기준문서 page range explicit offset 테스트
  - 빈 table header 컬럼 밀림 방지 테스트
  - 반복 token 검색 점수 과대평가 방지 단위 테스트
  - 반복 token 청크가 `/api/basis-search` 상단을 오염시키지 않는 API 회귀 테스트
- 검증 결과:
  - `py -3.13 -m py_compile backend/app/pipelines/pdf_readers.py backend/app/pipelines/basis_document.py backend/app/services/basis_rule_candidates.py backend/tests/test_pdf_readers.py backend/tests/test_basis_table_chunks.py backend/tests/test_api_flows.py`: 통과
  - `py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_basis_table_chunks.py backend/tests/test_api_flows.py::ApiFlowTests::test_basis_search_ranking_does_not_overvalue_repeated_single_token -q`: `16 passed`
  - `py -3.13 -m pytest backend/tests -q`: `126 passed`, `8 skipped`
  - `npm --prefix frontend run build`: 통과
  - `py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine opendataloader --threads 4 --timeout-seconds 1200 --strict`: 통과
  - `RUN_REAL_BASIS_RAG_TESTS=1`, `PDF_READER_ENGINE=opendataloader` 기준 `py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q`: `5 passed`, `10 subtests passed`
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: trailing whitespace 오류 없음, Windows CRLF 변환 warning만 출력

## Additional Update (2026-06-05) - Full Code Review PDF Reader And RAG Bug Fixes
- Per user request, reviewed the full codebase with extra focus on the PDF reader and basis-document RAG paths.
- Fixed only concrete bugs/problems, not general improvement ideas.
- Fixed issues:
  - `java -version` timeout/OSError could break the PDF reader status API with a raw exception.
  - forced OpenDataLoader conversion timeout could leak raw `TimeoutExpired` instead of `PdfReaderError`.
  - page offset drift could corrupt citation page metadata because page ranges only used per-page `char_count` and ignored inserted `\n\n` separators.
  - table-row chunk generation dropped blank header cells and shifted later column labels.
  - RAG search scoring overvalued repeated instances of one query token over balanced unique-token coverage.
  - approved rule candidate matching had the same repeated-token overvaluation problem.
- Added regression tests for PDF reader timeout handling, page offsets, blank table headers, unique-token RAG scoring, and API-level search ranking.
- Verification:
  - py_compile passed
  - targeted tests: `16 passed`
  - full backend tests: `126 passed`, `8 skipped`
  - frontend build passed
  - real 489-page OpenDataLoader basis QA passed
  - real basis RAG opt-in tests passed: `5 passed`, `10 subtests passed`
  - encoding check passed
  - `git diff --check` reported no whitespace errors, only Windows CRLF conversion warnings

## 작업 기록 (2026-06-07) - PDF/RAG 코드리뷰 수정계획 작성
- 사용자 요청에 따라 전체 코드리뷰에서 발견된 PDF 리더 및 기준문서 RAG 문제 중 DNS rebinding 첨부 URL 이슈를 즉시 수정 범위에서 제외했다.
- 작성 문서:
  - `docs/pdf-rag-code-review-remediation-plan.md`
- 즉시 수정계획 대상:
  - 기준문서 원본 파일 없음 재처리 시 기존 RAG 인덱스 보존
  - 승인된 기준문구 후보와 판단 엔진의 JSON 인덱스 검증 일관성 보강
  - PyMuPDF fallback 기준문서 page citation offset 보정
  - OpenDataLoader JSON 중첩 텍스트 및 표 셀 누락 방지
  - DOCX 표 텍스트 추출 보강
  - 긴 단일 문단 chunk overlap 적용 오류 수정
- 기록만 하는 이슈:
  - 첨부 URL 검증 DNS rebinding/shared address 보강
- 이번 단계는 수정계획 및 이슈 기록만 진행했으며 구현 코드는 수정하지 않았다.

## Additional Update (2026-06-07) - PDF/RAG Code Review Remediation Plan
- Per user request, excluded the attachment URL DNS rebinding issue from the immediate fix scope.
- Added:
  - `docs/pdf-rag-code-review-remediation-plan.md`
- Immediate plan scope:
  - preserve existing RAG index when basis reprocess fails because the stored file is missing
  - align approved rule candidates and judgment with JSON basis-index validation
  - fix PyMuPDF fallback page citation offsets
  - prevent OpenDataLoader nested text/table-cell loss
  - extract DOCX table text
  - fix long single-paragraph chunk overlap
- Record-only issue:
  - attachment URL DNS rebinding/shared-address hardening
- No implementation code was changed in this planning step.

## 작업 기록 (2026-06-07) - PDF/RAG 코드리뷰 수정계획 구현
- 사용자 요청에 따라 `docs/pdf-rag-code-review-remediation-plan.md`의 즉시 수정계획을 구현했다.
- DNS rebinding/shared address 첨부 URL 검증 이슈는 사용자 요청대로 구현하지 않고 기록-only 상태를 유지했다.
- 구현 완료:
  - 기준문서 원본 파일이 사라진 재처리에서 기존 completed/indexed RAG 산출물이 있으면 문서 상태와 JSON 인덱스를 보존한다.
  - 기준문구 후보 승인 시 JSON 기준문서 인덱스가 valid이고 대상 chunk metadata가 일치해야 승인되도록 보강했다.
  - 판단 엔진이 JSON 인덱스 오류 상태에서 승인 후보 citation을 우회 사용하지 않도록 보강했다.
  - PyMuPDF fallback PDF reader가 page `char_start`/`char_end`를 기록하도록 보강했다.
  - OpenDataLoader JSON 변환에서 빈 `content` 아래 nested text/table cell text를 놓치지 않도록 보강했다.
  - DOCX 추출에서 표 cell 텍스트를 포함하도록 보강했다.
  - 긴 단일 문단 chunk의 overlap이 실제 chunk에 반영되도록 수정했다.
- 추가 테스트:
  - 원본 파일 없음 재처리 보존 테스트
  - JSON 인덱스 손상/누락 vector 상태에서 기준문구 후보 승인 차단 테스트
  - JSON 인덱스 오류 상태에서 판단 엔진 승인 후보 citation 차단 테스트
  - OpenDataLoader nested text/table cell 추출 테스트
  - PyMuPDF page offset 테스트
  - DOCX table cell 추출 테스트
  - 긴 단일 문단 overlap 테스트
- 검증:
  - `py -3.13 -m py_compile backend/app/pipelines/pdf_readers.py backend/app/pipelines/parser.py backend/app/pipelines/basis_document.py backend/app/main.py backend/app/services/basis_rule_candidates.py backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py backend/tests/test_api_flows.py`: 통과
  - `py -3.13 -m pytest backend/tests/test_pdf_readers.py backend/tests/test_parser.py backend/tests/test_basis_table_chunks.py -q`: `22 passed`
  - 신규 API 회귀 테스트 4개: `4 passed`
  - `py -3.13 -m pytest backend/tests -q`: `134 passed`, `8 skipped`

## Additional Update (2026-06-07) - Implemented PDF/RAG Code Review Remediation
- Implemented the immediate fix scope from `docs/pdf-rag-code-review-remediation-plan.md`.
- The attachment URL DNS rebinding/shared-address issue remains record-only per user request.
- Completed fixes:
  - preserve existing completed/indexed RAG artifacts when basis reprocess fails because the stored PDF is missing
  - require valid JSON basis-index and matching chunk metadata before approving basis rule candidates
  - prevent the judgment engine from bypassing invalid JSON index state via approved rule candidates
  - add PyMuPDF fallback page `char_start`/`char_end` metadata
  - preserve nested OpenDataLoader text/table-cell content
  - include DOCX table cell text in extraction
  - fix overlap for long single-paragraph basis chunks
- Verification:
  - py_compile passed
  - PDF/parser/table chunk targeted tests: `22 passed`
  - new API regression tests: `4 passed`
  - full backend tests: `134 passed`, `8 skipped`

## 작업 기록 (2026-06-07) - 전체 코드리뷰 및 MD 문서 최신화
- 사용자 요청에 따라 현재 코드 상태를 기준으로 전체 구조를 재검토하고 Markdown 문서의 누락/불일치 내용을 최신화했다.
- 코드 리뷰 기준으로 확인한 현재 상태:
  - PDF reader 기본값은 OpenDataLoader 우선 `auto` 모드이고 PyMuPDF는 fallback/OCR 보조 엔진이다.
  - 일반 문서, 나라장터 첨부 PDF, 기준문서 PDF는 `extract_document()` parser 정책을 공유한다.
  - DOCX 추출은 문단과 표 cell 텍스트를 함께 포함한다.
  - 기준문서 RAG 검색 source는 JSON basis index 운영 산출물이다.
  - 기준문구 후보 승인과 Phase 3 판단 citation은 JSON basis index 건강 상태를 요구한다.
  - Phase 4 운영 대시보드, 작업/실패 관리, 백업/검증/복원계획 dry-run이 구현되어 있다.
- 신규 문서:
  - `docs/current-code-documentation-audit.md`
- 주요 업데이트 문서:
  - `README.md`
  - `AGENTS.md`
  - `docs/technical-design.md`
  - `docs/technology-summary.md`
  - `docs/ai-api-setup.md`
  - `docs/ux-design.md`
  - `docs/ux-monkey-testing-plan.md`
  - `docs/current-service-verification-remediation-plan.md`
  - `docs/remaining-development-roadmap.md`
  - `docs/운영 제품화 세부계획서.md`
  - `docs/코드리뷰 후 수정필요.md`
  - PDF/RAG/기준문서/나라장터/Phase 계획 관련 기존 MD 문서들
  - `backend/tests/real-basis-document-samples/README.md`
- 정리한 문서 불일치:
  - PyMuPDF 중심 설명을 OpenDataLoader `auto` + PyMuPDF fallback으로 갱신
  - DB chunk 검색 source 표현을 JSON basis index 기준으로 갱신
  - DOCX 문단-only 설명을 표 cell 포함으로 갱신
  - Phase 2.5/3/4 계획서를 현재 구현 완료 + 남은 운영/보안 보강 중심으로 갱신
  - 실제 기준문서 PyMuPDF Markdown 재생성 산출물은 역사적 baseline으로 표시
  - OpenDataLoader QA 산출물과 table-row token coverage를 현재 기준으로 표시
  - 첨부 URL DNS rebinding/shared address 보강은 기록-only 보안 이슈로 유지
- 검증:
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: whitespace 오류 없음, Windows CRLF 변환 warning만 출력
  - README 문서 링크 존재 확인: `README_DOC_LINKS_OK count=26`
  - 오래된 `db_chunks_completed_indexed` 문자열은 현재 기준 문서에서 제거했고, 과거 이력인 `docs/work-log.md`에만 남아 있음을 확인

## Additional Update (2026-06-07) - Full Code Review And Markdown Documentation Refresh
- Reviewed the current code structure and refreshed Markdown documentation against the current implementation.
- Current code facts recorded:
  - default PDF reader is OpenDataLoader-first `auto`, with PyMuPDF fallback/OCR helper
  - normal documents, Nara PDFs, and basis PDFs share `extract_document()`
  - DOCX extraction includes paragraphs and table cells
  - basis retrieval source is the operational JSON basis index
  - rule-candidate approval and Phase 3 judgment citations require JSON basis-index health
  - Phase 4 operations dashboard, operation/failure management, and backup validation/restore dry-run are implemented
- Added:
  - `docs/current-code-documentation-audit.md`
- Updated README, AGENTS, technical/technology/UX/API/Phase/PDF/RAG/Nara/operations docs, and the real-basis sample README.
- Documentation drift fixed:
  - PyMuPDF-centered descriptions updated to OpenDataLoader `auto` plus PyMuPDF fallback
  - DB chunk retrieval wording updated to JSON basis index
  - DOCX paragraph-only wording updated to include table cells
  - Phase 2.5/3/4 plans marked as implemented where applicable, with remaining hardening called out
  - PyMuPDF regenerated real-basis Markdown artifacts marked as historical baselines
  - OpenDataLoader QA artifacts and table-row token coverage marked as current basis QA signals
  - attachment URL DNS rebinding/shared-address hardening remains record-only
- Verification:
  - encoding check passed
  - `git diff --check` reported no whitespace errors, only Windows CRLF conversion warnings
  - README doc links exist: `README_DOC_LINKS_OK count=26`
  - stale `db_chunks_completed_indexed` wording remains only in historical work-log entries

## 작업 기록 (2026-06-07) - 전체 코드리뷰 후 URL 안전성 회귀 테스트 보강
- 사용자 요청에 따라 전체 코드리뷰 관점에서 최근 변경 영역을 다시 점검하고, 실제로 테스트가 비어 있던 나라장터 첨부 URL 안전성 경계값을 보강했다.
- 코드리뷰 확인:
  - PDF 리더는 OpenDataLoader 우선 `auto` 모드와 PyMuPDF fallback 구조로 동작한다.
  - 기준문서 RAG 검색/평가/citation 경로는 JSON basis index 기준으로 정렬되어 있다.
  - 백업/복원 dry-run, 기준문서 재처리 swap, 나라장터 재분석 보존 경로는 기존 회귀 테스트가 이미 존재한다.
  - 나라장터 첨부 URL 검증은 localhost/사설망 차단 테스트는 있었지만 `100.64.0.0/10` 같은 non-global shared address와 DNS 해석 결과 non-global인 hostname 테스트가 부족했다.
- 수정:
  - `backend/app/services/nara_api.py`에서 link-local 사유를 private보다 먼저 판정하고, `ipaddress.is_global`이 아닌 주소를 `non-global address is not allowed`로 차단하도록 보강했다.
  - `backend/tests/test_nara_url_safety.py`를 추가해 literal unsafe URL, shared address, DNS-resolved non-global address, public address 허용을 검증했다.
  - `docs/코드리뷰 후 수정필요.md`, `docs/pdf-rag-code-review-remediation-plan.md`에서 shared/non-global 주소 차단은 완료로 정리하고 DNS rebinding 완화만 후속 이슈로 남겼다.
- 검증:
  - `py -3.13 -m pytest backend/tests/test_nara_url_safety.py -q`: `3 passed, 7 subtests passed`
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "attachment_preview_rejects_private_network_url or nara_notice_attachment_download_rejects_private_network_url or reanalysis"`: `4 passed, 82 deselected`
  - `py -3.13 -m pytest backend/tests -q`: `137 passed, 8 skipped, 5 warnings, 7 subtests passed`
  - `npm run build`: 통과
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: whitespace 오류 없음, Windows CRLF 변환 warning만 출력

## Additional Update (2026-06-07) - Full Code Review And URL Safety Regression Tests
- Reviewed the recently changed code paths and added missing regression coverage for Nara attachment URL safety boundaries.
- Review findings:
  - PDF reader remains OpenDataLoader-first `auto` with PyMuPDF fallback.
  - Basis RAG search, evaluation, and citation paths are aligned to the JSON basis index.
  - Backup restore dry-run, basis reprocess swap, and Nara reanalysis preservation already have regression tests.
  - Nara attachment URL validation covered localhost/private-network cases but lacked non-global shared-address and DNS-resolved non-global hostname coverage.
- Changes:
  - Updated `backend/app/services/nara_api.py` to classify link-local before private and reject any non-global IP address.
  - Added `backend/tests/test_nara_url_safety.py` for literal unsafe URLs, `100.64.0.0/10`, DNS-resolved non-global hostnames, and public-address acceptance.
  - Updated issue-tracking docs so shared/non-global blocking is marked fixed while DNS rebinding mitigation remains follow-up work.
- Verification:
  - `py -3.13 -m pytest backend/tests/test_nara_url_safety.py -q`: `3 passed, 7 subtests passed`
  - targeted Nara API flow pytest: `4 passed, 82 deselected`
  - `py -3.13 -m pytest backend/tests -q`: `137 passed, 8 skipped, 5 warnings, 7 subtests passed`
  - `npm run build`: passed
  - `py -3.13 scripts/check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: no whitespace errors, only Windows CRLF conversion warnings

## 작업 기록 (2026-06-07) - ngrok 외부 접속 및 계약서 DOCX 생성 계획 작성
- 사용자 요청에 따라 구현 전에 두 신규 기능의 FE/BE 설계와 구현계획을 우선 문서화했다.
- 작성 문서:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- 계획 범위:
  - Phase 4E: ngrok 기반 외부 접속 지원
  - Phase 5A: 법인 기본정보와 저장 공고문 기반 계약서 DOCX 자동 생성 MVP
- 주요 설계:
  - ngrok은 백엔드 public URL을 먼저 획득한 뒤 해당 URL을 `VITE_API_BASE_URL`로 주입해 프론트를 실행하는 순서로 설계
  - 외부 접속 상태 API와 `scripts/manage-ngrok.ps1` 추가 계획 수립
  - 계약서 생성은 `contract_documents` 테이블, `storage/contracts/`, `python-docx` 기반 생성 서비스로 설계
  - 생성물은 법률적으로 확정된 계약서가 아니라 관리자 검토가 필요한 기본 계약서 초안으로 정의
- 이번 단계는 계획 문서 작성만 수행했고 구현 코드는 수정하지 않았다.

## Additional Update (2026-06-07) - Planned ngrok External Access And DOCX Contract Drafts
- Wrote the FE/BE design and implementation plan before implementation, per user request.
- Added:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- Scope:
  - Phase 4E: ngrok-based external access for the local app
  - Phase 5A: DOCX contract draft generation from corporation and saved notice data
- Key design decisions:
  - ngrok flow discovers the backend public URL first, then starts the frontend with that URL as `VITE_API_BASE_URL`
  - add external access status API and `scripts/manage-ngrok.ps1`
  - contract generation uses a `contract_documents` table, `storage/contracts/`, and `python-docx`
  - generated documents are contract drafts requiring admin/legal review
- No implementation code was changed in this planning step.

## 작업 기록 (2026-06-07) - 계약서 표준양식 PDF 반영 계획 보강
- 사용자가 제공한 `[별지 제9호서식] 용역 표준계약서(지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙).pdf`를 계약서 생성 양식 기준으로 삼도록 계획 문서를 보강했다.
- 확인한 PDF:
  - `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/[별지 제9호서식] 용역 표준계약서(지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙).pdf`
  - 1페이지 A4 세로 양식
  - 제목 `용역표준계약서`
  - 계약번호/공고번호, `계약서` 세로 라벨 표, `계약내용` 세로 라벨 표, 붙임서류, 서명/날인란 포함
- 보강 문서:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- 반영 내용:
  - DOCX 생성물이 자유 서술형 계약서가 아니라 해당 표준계약서 양식의 표 구조를 재현해야 한다는 요구사항 추가
  - 공고/법인/사용자 입력값과 표준계약서 항목 간 필드 매핑 초안 추가
  - 원본 PDF는 사용자 로컬 파일이므로 저장소에 바로 커밋하지 않고, 구현 시 repository-native DOCX/code template으로 재현하는 정책 추가
  - DOCX layout 회귀 테스트 항목 추가
- 이번 단계는 계획 문서 보강만 수행했고 구현 코드는 수정하지 않았다.

## Additional Update (2026-06-07) - Added Standard Contract Form Reference To Plan
- Updated the contract generation plan to use the user-provided `[별지 제9호서식] 용역 표준계약서` PDF as the layout reference.
- Inspected reference PDF:
  - one-page A4 portrait form
  - title `용역표준계약서`
  - contract/notice number fields
  - contract party table with vertical `계약서` label
  - contract detail table with vertical `계약내용` label
  - attachment list and signature/seal lines
- Updated:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- Added:
  - requirement to reproduce the standard form table layout in DOCX
  - field mapping from saved notice/corporation/custom fields to the standard form
  - policy not to commit the user's local PDF unless explicitly approved
  - DOCX layout regression test expectations
- No implementation code was changed in this planning update.

## 작업 기록 (2026-06-07) - ngrok/계약서 기능 상세 구현 Step 세분화
- 사용자 요청에 따라 `docs/ngrok-external-access-and-contract-docx-plan.md`의 구현 순서를 더 세부적인 작업 단위로 나눴다.
- 보강 문서:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- 세분화한 구현 단계:
  - Step 0: 구현 전 정책 고정
  - Step 1: 계약서 BE 데이터 모델
  - Step 2: 계약서 BE 입력 스냅샷/검증
  - Step 3: 표준계약서 DOCX layout builder
  - Step 4: 계약서 BE API
  - Step 5: 계약서 FE 타입/API
  - Step 6: 계약서 FE 화면
  - Step 7: 기존 화면의 계약서 생성 진입점 연결
  - Step 8: ngrok 실행 스크립트
  - Step 9: ngrok 상태 API와 FE 설정 화면
  - Step 10: README/문서/전체 QA
- 각 step에 작업 항목, 테스트 기준, 완료 기준을 추가했다.
- 이번 단계는 구현 전 계획 세분화만 수행했고 구현 코드는 수정하지 않았다.

## Additional Update (2026-06-07) - Split ngrok/Contract Features Into Detailed Implementation Steps
- Split the implementation order in `docs/ngrok-external-access-and-contract-docx-plan.md` into smaller execution steps.
- Updated:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- Detailed steps added:
  - Step 0: product policy freeze
  - Step 1: contract backend data model
  - Step 2: contract backend snapshot and validation
  - Step 3: standard contract DOCX layout builder
  - Step 4: contract backend APIs
  - Step 5: contract frontend types/API
  - Step 6: contract frontend page
  - Step 7: contract entry points
  - Step 8: ngrok script
  - Step 9: ngrok status API and frontend settings page
  - Step 10: README/docs/full QA
- Added work items, tests, and exit criteria for the implementation steps.
- No implementation code was changed in this planning update.

## 작업 기록 (2026-06-07) - ngrok/계약서 구현계획 누락 항목 더블체크
- 사용자 요청에 따라 `docs/ngrok-external-access-and-contract-docx-plan.md`의 누락 가능 항목을 재검토했다.
- 보강 문서:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- 더블체크 후 추가한 항목:
  - 계약서 생성물의 immutable snapshot 정책
  - 용역표준계약서 전용 MVP와 비용역 공고 경고 정책
  - 계약서 `status`/`review_status` 허용값
  - 한글 파일명 다운로드와 파일시스템 안전명 분리
  - 법인 프로필 자동 수정 금지와 계약서용 custom field 저장 정책
  - DOCX 임시 파일 렌더링 후 성공 시 최종 경로 교체
  - 생성 실패 row, operation run, 실패 사유 기록
  - 계약서 이력 필터, 중복 생성 허용, 기존 초안 덮어쓰기 금지
  - ngrok 포트 충돌 처리, 재시작 시 public URL 변경 대응, status 파일 secret 미저장
  - README 링크/백업 문구/운영 작업 이력 라벨 갱신 항목
- Product Questions는 Step 0의 기본 정책과 충돌하지 않도록 “정책 변경 필요 여부” 형태로 정리했다.
- 이번 단계는 계획 문서 보강만 수행했고 구현 코드는 수정하지 않았다.

## Additional Update (2026-06-07) - Double-Checked Missing Items In ngrok/Contract Plan
- Reviewed `docs/ngrok-external-access-and-contract-docx-plan.md` for implementation gaps before coding.
- Updated:
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- Added missing implementation criteria:
  - immutable generated-contract snapshots
  - service-contract-only MVP with warning for unclear notice types
  - allowed `status` and `review_status` values
  - UTF-8-safe download names separated from filesystem-safe names
  - no automatic corporation profile mutation from contract custom fields
  - temporary DOCX render before final file move
  - failed contract rows, failed operation runs, and error reasons
  - contract history filters, duplicate drafts, and no overwrite behavior
  - ngrok port collision handling, public URL refresh behavior, and secret-free status files
  - README link, backup wording, and operations UI label updates
- Product Questions were adjusted so they no longer conflict with Step 0 default policies.
- No implementation code was changed in this planning update.

## 작업 기록 (2026-06-07) - Phase 5A Step 1 계약서 BE 데이터 모델/저장/백업 구현
- 구현 단계:
  - Step 0 정책 재확인 완료
  - Step 1 계약서 BE 데이터 모델/저장/백업 구현 완료
- 수정 파일:
  - `backend/app/main.py`
  - `backend/app/services/backups.py`
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- 구현 내용:
  - `contract_documents` 테이블과 인덱스 추가
  - 계약서 산출물 저장 위치 `storage/contracts/{id}/` 표준화
  - 계약서 status/review_status CHECK 제약 추가
  - 백업 포함 디렉터리에 `contracts` 추가
  - 계약서 저장 경로 helper 추가
- 테스트:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract"`
  - 결과: 2 passed, 86 deselected
- 다음 단계:
  - Step 2 계약서 입력 snapshot/검증 서비스 구현

## Additional Update (2026-06-07) - Phase 5A Step 1 Contract Backend Data Model
- Completed:
  - Step 0 policy check
  - Step 1 contract backend data model/storage/backup support
- Updated:
  - `backend/app/main.py`
  - `backend/app/services/backups.py`
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- Added:
  - `contract_documents` table and indexes
  - `storage/contracts/{id}/` storage convention
  - status/review_status CHECK constraints
  - backup inclusion for `storage/contracts`
  - contract output path helper
- Test:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract"`
  - Result: 2 passed, 86 deselected
- Next:
  - Step 2 contract input snapshot and validation service

## 작업 기록 (2026-06-07) - Phase 5A Step 2 계약서 입력 스냅샷/검증 구현
- 구현 단계:
  - Step 2 계약서 입력 스냅샷/검증 구현 완료
- 수정 파일:
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- 구현 내용:
  - `ContractInputError` 추가
  - `build_contract_input_snapshot()` 구현
  - `validate_contract_generation_input()` 구현
  - 공고/법인/judgment run allowlist snapshot 구성
  - custom field 정규화와 생성 필드 매핑 추가
  - raw_json, API key, token, ServiceKey 류 민감 문자열 미포함 검증 추가
  - 비용역 가능 공고에 대한 검토 경고 추가
- 테스트:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_input"`
  - 결과: 3 passed, 88 deselected
- 다음 단계:
  - Step 3 표준계약서 DOCX layout builder 구현

## Additional Update (2026-06-07) - Phase 5A Step 2 Contract Input Snapshot
- Completed:
  - Step 2 contract input snapshot and validation service
- Updated:
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- Added:
  - `ContractInputError`
  - `build_contract_input_snapshot()`
  - `validate_contract_generation_input()`
  - allowlisted notice/corporation/judgment snapshot
  - normalized custom fields and generated field mapping
  - secret exclusion tests for raw JSON/API key/token/ServiceKey values
  - warning for notices that are not clearly service contracts
- Test:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_input"`
  - Result: 3 passed, 88 deselected
- Next:
  - Step 3 standard contract DOCX layout builder

## 작업 기록 (2026-06-07) - Phase 5A Step 3 표준계약서 DOCX 빌더 구현
- 구현 단계:
  - Step 3 표준계약서 DOCX layout builder 구현 완료
- 수정 파일:
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- 구현 내용:
  - `render_standard_service_contract_docx()` 추가
  - A4 세로, 한글 기본 글꼴, 표준계약서 제목/상단 문구 적용
  - 계약번호/공고번호 표, `계약서` 표, `계약내용` 표, 붙임서류, 서명/날인란 생성
  - 입력 snapshot의 생성 필드를 DOCX에 자동 매핑
  - 임시 DOCX 렌더링 후 성공 시 최종 경로로 교체
  - 렌더링 실패 시 임시/부분 산출물이 남지 않도록 정리
- 테스트:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_docx"`
  - 결과: 2 passed, 91 deselected
- 다음 단계:
  - Step 4 계약서 BE API 구현

## Additional Update (2026-06-07) - Phase 5A Step 3 Standard Contract DOCX Builder
- Completed:
  - Step 3 standard contract DOCX layout builder
- Updated:
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- Added:
  - `render_standard_service_contract_docx()`
  - A4 portrait page setup and Korean font settings
  - standard title/header, contract/notice number table, party table, contract detail table, attachments, and signature lines
  - generated-field mapping from the immutable input snapshot
  - temporary render then final-path replacement
  - cleanup behavior for render failures
- Test:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_docx"`
  - Result: 2 passed, 91 deselected
- Next:
  - Step 4 contract backend APIs

## 작업 기록 (2026-06-07) - Phase 5A Step 4 계약서 BE API 구현
- 구현 단계:
  - Step 4 계약서 BE API 구현 완료
- 수정 파일:
  - `backend/app/main.py`
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- 구현 내용:
  - `GET /api/contracts`
  - `POST /api/contracts/preview`
  - `POST /api/contracts`
  - `GET /api/contracts/{id}`
  - `GET /api/contracts/{id}/download`
  - `PATCH /api/contracts/{id}/review`
  - `DELETE /api/contracts/{id}`
  - 계약서 생성/삭제/검토 변경 operation run 기록
  - 생성 실패 row와 실패 사유 기록
  - 다운로드 DOCX MIME과 UTF-8 파일명 header 적용
- 테스트:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_api"`
  - 결과: 2 passed, 93 deselected
- 발견/수정:
  - Windows에서 다운로드 응답 객체가 파일 핸들을 잡아 삭제 테스트가 실패했다.
  - 테스트에서 다운로드 응답 검증 후 `download_response.close()`를 호출하도록 수정했다.
- 다음 단계:
  - Step 5 프론트 타입/API helper 구현

## Additional Update (2026-06-07) - Phase 5A Step 4 Contract Backend APIs
- Completed:
  - Step 4 contract backend APIs
- Updated:
  - `backend/app/main.py`
  - `backend/app/services/contract_documents.py`
  - `backend/tests/test_api_flows.py`
- Added:
  - `GET /api/contracts`
  - `POST /api/contracts/preview`
  - `POST /api/contracts`
  - `GET /api/contracts/{id}`
  - `GET /api/contracts/{id}/download`
  - `PATCH /api/contracts/{id}/review`
  - `DELETE /api/contracts/{id}`
  - operation run logging for contract create/delete/review updates
  - failed generation row and error reason persistence
  - DOCX MIME type and UTF-8 download filename headers
- Test:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase5a_contract_api"`
  - Result: 2 passed, 93 deselected
- Fix during testing:
  - Windows held the downloaded DOCX file handle during delete verification.
  - The test now closes the download response after asserting the DOCX content.
- Next:
  - Step 5 frontend types and API helpers

## 작업 기록 (2026-06-07) - Phase 5A Step 5 프론트 타입/API helper 구현
- 구현 단계:
  - Step 5 프론트 타입/API helper 구현 완료
- 수정 파일:
  - `frontend/src/app/types.ts`
  - `frontend/src/app/api.ts`
- 구현 내용:
  - `ContractCustomFields`, `ContractValidation`, `ContractInputSnapshot`, `ContractPreview`, `ContractDocument` 타입 추가
  - 계약서 목록/미리보기/생성/상세/검토수정/삭제/다운로드 URL helper 추가
  - `buildApiUrl()` export 처리
- 테스트:
  - `npm run build`
  - 결과: 통과
- 다음 단계:
  - Step 6 계약서 FE 화면 구현

## Additional Update (2026-06-07) - Phase 5A Step 5 Frontend Types And API Helpers
- Completed:
  - Step 5 frontend types and API helpers
- Updated:
  - `frontend/src/app/types.ts`
  - `frontend/src/app/api.ts`
- Added:
  - `ContractCustomFields`, `ContractValidation`, `ContractInputSnapshot`, `ContractPreview`, and `ContractDocument` types
  - contract list/preview/create/detail/review/delete/download URL helpers
  - exported `buildApiUrl()`
- Test:
  - `npm run build`
  - Result: passed
- Next:
  - Step 6 contract frontend page

## 작업 기록 (2026-06-07) - Phase 5A Step 6 계약서 FE 화면 구현
- 구현 단계:
  - Step 6 계약서 FE 화면 구현 완료
- 수정 파일:
  - `frontend/src/pages/ContractsPage.tsx`
- 구현 내용:
  - 저장 공고/법인/judgment run 선택 폼 추가
  - 계약번호, 계약금액, 계약기간, 위치, 전화번호, 지연배상금률, 그 밖의 사항, 붙임서류 입력 추가
  - 계약서 미리보기 API 호출과 표준계약서 필드 매핑 표시
  - 계약서 초안 생성 API 호출과 생성 이력 refresh
  - 생성 이력 검색, review status 필터, 다운로드, 삭제 액션 추가
  - 실패 생성 응답도 화면 오류 상태와 이력 목록에 반영
- 테스트:
  - `npm run build`
  - 결과: 통과
- 다음 단계:
  - Step 7 기존 화면 진입점 연결

## Additional Update (2026-06-07) - Phase 5A Step 6 Contract Frontend Page
- Completed:
  - Step 6 contract frontend page
- Added:
  - `frontend/src/pages/ContractsPage.tsx`
- Implemented:
  - saved notice/corporation/judgment-run selectors
  - contract number, amount, period, location, phone, delay penalty, other terms, and attachments inputs
  - preview API action and standard-form field mapping panel
  - create API action and history refresh
  - generated history search, review-status filter, download, and delete actions
  - failed create response handling in UI state and history
- Test:
  - `npm run build`
  - Result: passed
- Next:
  - Step 7 existing workflow entry points

## 작업 기록 (2026-06-07) - Phase 5A Step 7 기존 화면 진입점 연결
- 구현 단계:
  - Step 7 기존 화면 진입점 연결 완료
- 수정 파일:
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/ContractsPage.tsx`
  - `frontend/src/pages/NaraSavedNoticeDetailPage.tsx`
  - `frontend/src/pages/JudgmentRunsPage.tsx`
  - `frontend/src/pages/NoticeComparisonPage.tsx`
- 구현 내용:
  - `/contracts` 라우트와 사이드바 `계약서 생성` 메뉴 추가
  - `/contracts?notice_id=...&corporation_id=...&judgment_run_id=...` query param 초기 선택 지원
  - 저장 공고 상세에서 공고 기준 계약서 생성 링크 추가
  - 판단 run 상세에서 공고/법인/judgment run 기준 계약서 생성 링크 추가
  - 부족조건 미리보기에서 선택 공고/법인 조합 기준 계약서 생성 링크 추가
- 테스트:
  - `npm run build`
  - 결과: 통과
- 다음 단계:
  - Step 8 ngrok 실행 스크립트 구현

## Additional Update (2026-06-07) - Phase 5A Step 7 Existing Workflow Entry Points
- Completed:
  - Step 7 existing workflow entry points
- Updated:
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/ContractsPage.tsx`
  - `frontend/src/pages/NaraSavedNoticeDetailPage.tsx`
  - `frontend/src/pages/JudgmentRunsPage.tsx`
  - `frontend/src/pages/NoticeComparisonPage.tsx`
- Added:
  - `/contracts` route and sidebar menu item
  - query-param initialization for notice/corporation/judgment-run ids
  - contract draft entry link from saved notice detail
  - contract draft entry link from selected judgment run
  - contract draft entry link from notice comparison
- Test:
  - `npm run build`
  - Result: passed
- Next:
  - Step 8 ngrok script

## 작업 기록 (2026-06-07) - Phase 4E Step 8 ngrok 실행 스크립트 구현
- 구현 단계:
  - Step 8 ngrok 실행 스크립트 구현 완료
- 추가 파일:
  - `scripts/manage-ngrok.ps1`
- 구현 내용:
  - `start`, `status`, `stop` action 추가
  - ngrok CLI/auth 설정 확인
  - 백엔드 서버 실행 후 backend tunnel public URL 조회
  - `VITE_API_BASE_URL=<backend public URL>`로 프론트엔드 실행
  - frontend tunnel public URL 조회
  - `temp/ngrok.status.json`에 public/local URL, port, pid, updated_at 저장
  - token/API key/raw env 값은 status 파일에 저장하지 않음
  - 포트 충돌 시 관리 대상 프로세스가 아니면 명확한 오류 반환
- 테스트:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 status`
  - `[System.Management.Automation.PSParser]::Tokenize(...)`
  - PATH를 비운 start 호출로 ngrok CLI 미설치 안내 확인
  - 결과: status JSON 출력, PowerShell parse 통과, `NGROK_MISSING_ERROR_OK`
- 다음 단계:
  - Step 9 ngrok 상태 API/FE 구현

## Additional Update (2026-06-07) - Phase 4E Step 8 ngrok Script
- Completed:
  - Step 8 ngrok script
- Added:
  - `scripts/manage-ngrok.ps1`
- Implemented:
  - `start`, `status`, and `stop` actions
  - ngrok CLI/auth checks
  - backend start, backend tunnel discovery, frontend start with backend public URL, frontend tunnel discovery
  - `temp/ngrok.status.json` with public/local URLs, ports, pids, and updated time
  - no token/API key/raw env values in status file
  - port collision guard for unmanaged processes
- Tests:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 status`
  - PowerShell parser tokenization
  - PATH-empty start call for ngrok-missing error
  - Result: status output, parse OK, `NGROK_MISSING_ERROR_OK`
- Next:
  - Step 9 ngrok status API and frontend page

## 작업 기록 (2026-06-07) - Phase 4E Step 9 ngrok 상태 API/FE 구현
- 구현 단계:
  - Step 9 ngrok 상태 API/FE 구현 완료
- 수정 파일:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/vite.config.ts`
  - `frontend/src/app/types.ts`
  - `frontend/src/app/api.ts`
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/ExternalAccessPage.tsx`
- 구현 내용:
  - `GET /api/external-access/status` 추가
  - `temp/ngrok.status.json` allowlist 응답과 secret-like 필드 미노출 처리
  - `VITE_ALLOW_NGROK_HOSTS=1`일 때 Vite `allowedHosts=true` 적용
  - `/settings/external-access` 화면/라우트/설정 메뉴 추가
  - 공개 URL 복사 버튼, PowerShell 명령 안내, 외부 노출 경고 추가
  - 프론트에서는 ngrok start/stop을 직접 실행하지 않고 상태만 표시
- 테스트:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase4e_external_access"`
  - `npm run build`
  - 결과: backend 1 passed, frontend build 통과
- 다음 단계:
  - Step 10 README/docs/전체 QA

## Additional Update (2026-06-07) - Phase 4E Step 9 ngrok Status API And Frontend
- Completed:
  - Step 9 ngrok status API and frontend page
- Updated:
  - `backend/app/main.py`
  - `backend/tests/test_api_flows.py`
  - `frontend/vite.config.ts`
  - `frontend/src/app/types.ts`
  - `frontend/src/app/api.ts`
  - `frontend/src/app/App.tsx`
  - `frontend/src/pages/ExternalAccessPage.tsx`
- Added:
  - `GET /api/external-access/status`
  - allowlisted status-file response with secret-like field exclusion
  - Vite `allowedHosts=true` when `VITE_ALLOW_NGROK_HOSTS=1`
  - `/settings/external-access` route, nav item, and page
  - public URL copy buttons, local PowerShell commands, and external exposure warning
  - frontend status-only behavior; no start/stop execution from UI
- Tests:
  - `py -3.13 -m pytest backend/tests/test_api_flows.py -q -k "phase4e_external_access"`
  - `npm run build`
  - Result: backend 1 passed, frontend build passed
- Next:
  - Step 10 README/docs/full QA

## 작업 기록 (2026-06-07) - Phase 4E/5A Step 10 문서/전체 QA 완료
- 구현 단계:
  - Step 10 README/docs/전체 QA 완료
- 수정 파일:
  - `README.md`
  - `docs/ux-monkey-testing-plan.md`
  - `scripts/ux-monkey-test.mjs`
  - `frontend/src/pages/BackupsPage.tsx`
  - `frontend/src/pages/OperationRunsPage.tsx`
- 문서/운영 보강:
  - README에 Phase 4E ngrok 외부 접속과 Phase 5A 계약서 DOCX 초안 생성 설명 추가
  - README 빠른 가이드에 ngrok token 등록/start/status/stop 방법 추가
  - README 빠른 가이드에 계약서 DOCX 초안 생성 절차 추가
  - README 문서 링크에 `docs/ngrok-external-access-and-contract-docx-plan.md` 추가
  - UX monkey route 목록에 `/contracts`, `/settings/external-access` 추가
  - safe monkey 위험 라벨에 다운로드/복사/외부/ngrok 관련 키워드 추가
  - 백업 화면 포함 항목에 `contracts` 추가
  - 작업 이력 화면에 계약서 생성/검토 변경/삭제 라벨 추가
- 전체 검증:
  - `py -3.13 -m py_compile backend/app/main.py backend/app/services/contract_documents.py`: 통과
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 3 tests OK
  - `npm run build`: 통과
  - `py -3.13 -m pytest backend/tests -q`: 147 passed, 8 skipped, 7 subtests passed
  - `powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start`: 서버 시작
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `SMOKE_OK`
  - `npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 40 --seed 20260607 --screenshot-dir ..\temp\ux-monkey-contracts`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: 공백 오류 없음, CRLF 변환 경고만 있음
- UX monkey 중 발견/수정:
  - 기존 `networkidle` 대기가 `/nara-board`에서 timeout을 유발했다.
  - route smoke 목적에 맞게 `domcontentloaded`를 기준으로 이동하고 짧은 network idle은 best-effort로 변경했다.
- 서버 상태:
  - 로컬 서버가 실행 중이다.
  - Backend: `http://127.0.0.1:18111`
  - Frontend: `http://127.0.0.1:5199`

## Additional Update (2026-06-07) - Phase 4E/5A Step 10 Docs And Full QA
- Completed:
  - Step 10 README/docs/full QA
- Updated:
  - `README.md`
  - `docs/ux-monkey-testing-plan.md`
  - `scripts/ux-monkey-test.mjs`
  - `frontend/src/pages/BackupsPage.tsx`
  - `frontend/src/pages/OperationRunsPage.tsx`
- Documentation/ops updates:
  - added Phase 4E ngrok external access and Phase 5A DOCX contract draft generation to README
  - added ngrok token/start/status/stop quick guide
  - added contract draft generation quick guide
  - added `docs/ngrok-external-access-and-contract-docx-plan.md` to README document links
  - added `/contracts` and `/settings/external-access` to UX monkey routes
  - added download/copy/external/ngrok labels to safe monkey dangerous-action filter
  - updated backup UI wording to include `contracts`
  - added operation labels for contract create/review/delete
- Full verification:
  - `py -3.13 -m py_compile backend/app/main.py backend/app/services/contract_documents.py`: passed
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 3 tests OK
  - `npm run build`: passed
  - `py -3.13 -m pytest backend/tests -q`: 147 passed, 8 skipped, 7 subtests passed
  - `powershell -ExecutionPolicy Bypass -File scripts\smoke-test.ps1`: `SMOKE_OK`
  - `npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 40 --seed 20260607 --screenshot-dir ..\temp\ux-monkey-contracts`: passed
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: no whitespace errors; CRLF conversion warnings only
- UX monkey fix:
  - changed route navigation from strict `networkidle` to `domcontentloaded` with best-effort short network-idle wait because `/nara-board` can keep network activity long enough to timeout.
- Server state:
  - Backend: `http://127.0.0.1:18111`
  - Frontend: `http://127.0.0.1:5199`

## 작업 기록 (2026-06-07) - ngrok 토큰 등록 및 외부 접속 실기동 보강
- 사용자 요청에 따라 ngrok authtoken을 로컬 ngrok 설정 파일에 등록했다.
- 토큰 값은 문서/상태 파일/응답에 기록하지 않았다.
- `scripts/manage-ngrok.ps1 start` 실기동 중 발견한 문제를 수정했다.
  - ngrok 3.39.3에서 `--web-addr` 플래그가 지원되지 않아 터널 public URL을 읽지 못하던 문제 수정
  - ngrok 로그 파일의 JSON 이벤트에서 public URL을 파싱하도록 변경
  - Windows PowerShell의 UTF-8 BOM 때문에 `GET /api/external-access/status`가 상태 파일을 JSON으로 읽지 못하던 문제 수정
  - `py.exe`/`cmd.exe`가 실제 서버 프로세스를 자식으로 띄우는 구조를 반영해 관리 PID의 자식 프로세스까지 포트 검증/정지 대상에 포함
- 검증:
  - `ngrok config add-authtoken <masked>`: 등록 완료
  - `powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start`: 통과
  - `GET http://127.0.0.1:18111/api/external-access/status`: `enabled=true` 및 public URL 반환 확인
  - 공개 프론트 URL 접속: HTTP 200 확인
  - 공개 백엔드 `/health` 접속: HTTP 200 확인
- 현재 실행 중:
  - Backend local: `http://127.0.0.1:18111`
  - Frontend local: `http://127.0.0.1:5199`
  - Backend public: `https://1b14-118-216-124-59.ngrok-free.app`
  - Frontend public: `https://0fa4-118-216-124-59.ngrok-free.app`

## Additional Update (2026-06-07) - ngrok Token Setup And External Access Runtime Fix
- Registered the user-provided ngrok authtoken in the local ngrok config.
- Did not write the raw token to docs, status payloads, or API responses.
- Fixed runtime issues found while starting `scripts/manage-ngrok.ps1`.
  - Replaced unsupported ngrok 3.39.3 `--web-addr` usage with JSON log parsing for public URLs.
  - Wrote `temp/ngrok.status.json` as UTF-8 without BOM so Python `json.loads()` can read it.
  - Treated child processes of managed `py.exe`/`cmd.exe` launchers as managed listeners for restart/stop safety.
- Verification:
  - `ngrok config add-authtoken <masked>`: passed
  - `powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start`: passed
  - `GET http://127.0.0.1:18111/api/external-access/status`: returned `enabled=true` and public URLs
  - public frontend URL: HTTP 200
  - public backend `/health`: HTTP 200

## 작업 기록 (2026-06-07) - API 키 설정 상태 재확인
- 사용자 문의에 따라 `backend/.env`의 NARA/Gemini 키 설정 여부와 실행 중 백엔드 API 응답을 재확인했다.
- 키 원문은 출력하지 않고 존재 여부, 길이, 마스킹 응답만 확인했다.
- 확인 결과:
  - `backend/.env`에 `NARA_API_SERVICE_KEY` 존재
  - `backend/.env`에 `GEMINI_API_KEY` 존재
  - `GET /api/settings/integrations/nara/status`: `configured=true`
  - `GET /api/settings/ai-models`: Gemini `configured=true`
  - 현재 Vite 프론트의 `VITE_API_BASE_URL`은 ngrok 백엔드 public URL을 가리킴
- 판단:
  - 설정 화면에서 키 미설정 문구가 보였다면 서버 재시작 전 상태 또는 브라우저 갱신 전 상태를 본 것으로 판단한다.

## Additional Update (2026-06-07) - API Key Configuration Status Recheck
- Rechecked local `backend/.env` key presence and runtime backend API responses after the user's question.
- Did not print raw secrets; only checked existence, length, and masked API responses.
- Results:
  - `NARA_API_SERVICE_KEY` exists in `backend/.env`
  - `GEMINI_API_KEY` exists in `backend/.env`
  - `GET /api/settings/integrations/nara/status`: `configured=true`
  - `GET /api/settings/ai-models`: Gemini `configured=true`
  - current Vite frontend points to the ngrok backend public URL via `VITE_API_BASE_URL`
- Assessment:
  - If the UI still showed missing-key text, it was likely a pre-restart or stale browser state.

## 작업 기록 (2026-06-07) - ngrok 공개 접속 CORS 오류 수정
- 사용자 브라우저 콘솔에서 `No Access-Control-Allow-Origin` 및 `net::ERR_FAILED` 오류가 발생한 원인을 확인했다.
- 확인 결과:
  - 백엔드 Flask CORS 설정 자체는 정상 동작했다.
  - `ngrok-skip-browser-warning` 헤더를 붙인 API 호출은 `Access-Control-Allow-Origin`이 포함된 HTTP 200을 반환했다.
  - 브라우저 User-Agent만 붙인 호출은 ngrok 무료 플랜 browser warning 응답이 먼저 나오며 CORS 헤더가 빠졌다.
- 수정:
  - `frontend/src/app/api.ts`에서 API base URL이 `*.ngrok-free.app`이면 모든 API fetch에 `ngrok-skip-browser-warning: 1` 헤더를 자동 추가하도록 변경했다.
  - 기존 `RequestInit.headers`를 보존하면서 런타임 헤더만 병합하도록 처리했다.
  - `backend/tests/test_frontend_contracts.py`에 ngrok warning skip 헤더 유지 테스트를 추가했다.
- 검증:
  - ngrok preflight `OPTIONS` 응답에서 `Access-Control-Allow-Headers: ngrok-skip-browser-warning` 확인
  - 브라우저 User-Agent + skip 헤더 API 호출에서 `Access-Control-Allow-Origin` 포함 HTTP 200 확인
  - 공개 프론트가 제공하는 `/src/app/api.ts`에 skip 헤더 코드 포함 확인
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 4 tests OK
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## Additional Update (2026-06-07) - ngrok Public Access CORS Fix
- Investigated the browser console `No Access-Control-Allow-Origin` and `net::ERR_FAILED` errors.
- Findings:
  - Flask CORS itself was working.
  - API calls with `ngrok-skip-browser-warning` returned HTTP 200 with `Access-Control-Allow-Origin`.
  - Browser-like calls without that header were intercepted by the ngrok free-plan browser warning response, which omitted CORS headers.
- Fix:
  - Updated `frontend/src/app/api.ts` to add `ngrok-skip-browser-warning: 1` to every API request when `VITE_API_BASE_URL` points to `*.ngrok-free.app`.
  - Preserved existing `RequestInit.headers` while merging the runtime header.
  - Added a frontend source-contract test in `backend/tests/test_frontend_contracts.py`.
- Verification:
  - ngrok preflight `OPTIONS` allows `ngrok-skip-browser-warning`.
  - Browser User-Agent + skip header API call returns HTTP 200 with `Access-Control-Allow-Origin`.
  - Public frontend-served `/src/app/api.ts` includes the skip-header logic.
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 4 tests OK
  - `npm run build`: passed
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-06-07) - 대시보드 문구 및 좌측 네비게이션 아이콘 정리
- 사용자 요청에 따라 현재 제품 상태와 맞지 않는 대시보드 문구를 정리했다.
  - 상단 히어로의 `Local PC`, `Phase 1.5`, `RAG Ready Next` 칩 제거
  - 대시보드 `오늘 처리할 큐` 제목을 `우선 확인할 항목`으로 변경
  - Phase 중심 설명 문장을 실제 큐 설명으로 변경
- 좌측 네비게이션의 `OV`, `OP`, `NB` 같은 2글자 약어를 모두 제거했다.
- `lucide-react`를 추가하고 메뉴 성격에 맞는 아이콘으로 교체했다.
  - 대시보드: `LayoutDashboard`
  - 운영: `Activity`, `History`, `DatabaseBackup`
  - 공고: `Search`, `BookmarkCheck`, `Scale`, `ClipboardCheck`, `FilePenLine`, `RefreshCw`
  - 문서/RAG/관리/설정: `FileText`, `Library`, `ListChecks`, `SearchCheck`, `Building2`, `FolderKanban`, `Plug`, `ExternalLink`
- 테스트 보강:
  - `backend/tests/test_frontend_contracts.py`에 오래된 Phase 칩 문구와 2글자 아이콘 약어가 재등장하지 않는지 확인하는 테스트 추가
- 검증:
  - `npm run build`: 통과
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 5 tests OK
  - `rg`로 오래된 문구/2글자 아이콘 약어 미검출 확인
  - Playwright 로컬 화면 검증: 네비 카드 18개, SVG 아이콘 18개, 아이콘 텍스트 없음, 오래된 문구 없음
  - Playwright 스크린샷 저장: `temp/dashboard-nav-icons-check.png`
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## Additional Update (2026-06-07) - Dashboard Copy And Sidebar Icon Cleanup
- Cleaned up dashboard copy that no longer matched the current product state.
  - Removed the hero chips `Local PC`, `Phase 1.5`, and `RAG Ready Next`.
  - Renamed `오늘 처리할 큐` to `우선 확인할 항목`.
  - Replaced phase-oriented queue copy with a concise operational queue description.
- Replaced two-letter sidebar abbreviations such as `OV`, `OP`, and `NB` with real icons.
- Added `lucide-react` and mapped each navigation item to a domain-appropriate icon.
- Test coverage:
  - Added a frontend source-contract test to prevent stale phase chips and two-letter icon abbreviations from returning.
- Verification:
  - `npm run build`: passed
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 5 tests OK
  - `rg`: no stale hero/queue copy or two-letter nav icon abbreviations found
  - Playwright local UI check: 18 nav cards, 18 SVG nav icons, no text inside icon slots, no stale copy
  - Playwright screenshot saved to `temp/dashboard-nav-icons-check.png`
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-06-07) - 대시보드 상단 히어로 문구 제거 및 아이콘 마스트헤드 적용
- 사용자 요청에 따라 대시보드 상단의 긴 설명 문구를 제거했다.
  - `Operations Overview`
  - `오늘 처리할 조달 업무를 한눈에`
  - `공고, 문서, 분석 상태를 운영형 대시보드로 정리해 다음 액션을 빠르게 찾습니다.`
- 상단 히어로를 텍스트 설명 영역 대신 아이콘형 마스트헤드로 교체했다.
  - 중앙: `LayoutDashboard`
  - 보조 아이콘: `Search`, `FileText`, `Library`, `ClipboardCheck`
- 테스트 보강:
  - `backend/tests/test_frontend_contracts.py`에서 해당 문구들이 다시 들어오지 않는지 확인
  - 히어로 아이콘 구조(`hero-panel--mark`, `hero-logo__core`)가 유지되는지 확인
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 5 tests OK
  - `npm run build`: 통과
  - `rg`로 삭제 대상 문구 미검출 확인
  - Playwright 화면 검증: 히어로 텍스트 없음, 히어로 SVG 5개 렌더링
  - Playwright 스크린샷 저장: `temp/dashboard-hero-logo-check.png`
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## Additional Update (2026-06-07) - Dashboard Hero Copy Removal And Icon Masthead
- Removed the long dashboard hero copy requested by the user:
  - `Operations Overview`
  - `오늘 처리할 조달 업무를 한눈에`
  - `공고, 문서, 분석 상태를 운영형 대시보드로 정리해 다음 액션을 빠르게 찾습니다.`
- Replaced the text hero with an icon masthead.
  - Main icon: `LayoutDashboard`
  - Supporting icons: `Search`, `FileText`, `Library`, `ClipboardCheck`
- Test coverage:
  - Extended `backend/tests/test_frontend_contracts.py` to block the removed copy from returning.
  - Asserted the new hero icon structure remains present.
- Verification:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 5 tests OK
  - `npm run build`: passed
  - `rg`: removed hero copy no longer found
  - Playwright UI check: no hero text, 5 hero SVG icons rendered
  - Playwright screenshot saved to `temp/dashboard-hero-logo-check.png`
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`

## 작업 기록 (2026-06-07) - smoke-test 데이터 삭제
- 사용자 요청에 따라 대시보드에 노출되던 smoke-test 데이터를 정리했다.
- 삭제 대상:
  - `SMOKE-*` / `Smoke Test Nara Notice` 저장 공고 19건
  - `smoke-sample.pdf` 업로드 문서 10건
  - `Smoke Test Project` 프로젝트 10건
  - `Smoke Test Corporation` 법인 10건
  - 연결 데이터: 나라장터 첨부 12건, 요구조건 후보 26건, 문서 분석 11건
- 파일 정리:
  - `backend/storage/uploads/15` ~ `backend/storage/uploads/24` 중 존재 디렉터리 삭제
  - `backend/storage/nara-notices/<SMOKE notice id>` 중 존재 디렉터리 삭제
  - 삭제 전 모든 경로가 `backend/storage` 하위 허용 루트에 있는지 검증했다.
- 검증:
  - DB 매칭 결과: smoke 공고/문서/프로젝트/법인 0건
  - orphan attachment/analysis 0건
  - `GET /api/dashboard/summary`: 법인/프로젝트/문서 count 0
  - `GET /api/documents`: 0건
  - `GET /api/corporations`: 0건
  - `GET /api/projects`: 0건
  - Playwright 대시보드 검증: `SMOKE-`, `Smoke Test`, `smoke-sample.pdf` 미노출
  - API 요청 실패 없음, 나라장터 API 상태 `설정됨`, 테스트 `ok`
  - 스크린샷 저장: `temp/dashboard-after-smoke-cleanup.png`

## Additional Update (2026-06-07) - smoke-test Data Cleanup
- Removed smoke-test data that was appearing on the dashboard.
- Deleted:
  - 19 saved notices matching `SMOKE-*` / `Smoke Test Nara Notice`
  - 10 uploaded documents named `smoke-sample.pdf`
  - 10 `Smoke Test Project` records
  - 10 `Smoke Test Corporation` records
  - related rows: 12 Nara attachments, 26 requirement candidates, 11 document analyses
- File cleanup:
  - Removed existing smoke upload directories under `backend/storage/uploads/15` through `24`.
  - Removed existing smoke notice directories under `backend/storage/nara-notices/<SMOKE notice id>`.
  - Verified all deleted paths were under allowed `backend/storage` roots before deletion.
- Verification:
  - DB match count for smoke notices/documents/projects/corporations is now 0.
  - Orphan attachment/analysis count is 0.
  - `GET /api/dashboard/summary`: corporation/project/document counts are 0.
  - `GET /api/documents`: 0 rows.
  - `GET /api/corporations`: 0 rows.
  - `GET /api/projects`: 0 rows.
  - Playwright dashboard check: no `SMOKE-`, `Smoke Test`, or `smoke-sample.pdf` text.
  - No failed API requests; Nara API badge shows configured and test ok.
  - Screenshot saved to `temp/dashboard-after-smoke-cleanup.png`.

## 작업 기록 (2026-06-07) - 포탈 테마와 한글 폰트 교체
- 사용자 요청에 따라 전체 포탈 테마를 추천안의 `Procurement Slate` 계열로 교체했다.
  - 배경: `#f6f8fb`
  - 본문: `#172033`
  - 주 브랜드: `#1d4ed8`
  - 강조 브랜드: `#1e3a8a`
  - 보조 포인트: `#0f766e`
- `frontend/src/styles.css`의 전역 토큰, 중복 테마 토큰, 버튼/입력/카드/사이드바/히어로/배지 계열 하드코딩 색상을 블루, 슬레이트, 틸 중심으로 정리했다.
- 깨진 한글 fallback 문자열과 `Dotum`/`돋움` fallback을 제거하고, 포탈 전반 폰트 스택을 `Pretendard Variable`, `Pretendard`, `Noto Sans KR`, `Apple SD Gothic Neo`, `Malgun Gothic`, `system-ui`, `sans-serif` 순서로 교체했다.
- 왼쪽 브랜드 설명 문구가 한 글자 단위로 어색하게 줄바꿈되는 문제를 발견해 `문서 분석 · 공고 저장 · 기준문서 확장`으로 짧게 정리했다.
- 회귀 테스트를 보강했다.
  - `backend/tests/test_frontend_contracts.py`에 Procurement Slate 토큰과 Pretendard 한글 폰트 스택 검증을 추가했다.
  - 이전 핑크/크림 테마 토큰과 깨진 폰트 fallback이 다시 들어오지 않도록 assertion을 추가했다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: 통과
  - `rg`로 이전 테마 토큰 및 깨진 폰트 fallback 미검출 확인
  - Playwright 빌드 산출물 화면 검증: 테마 CSS 변수, Pretendard 스택, stale copy 미노출 확인
  - Playwright 스크린샷 저장: `temp/portal-theme-check.png`

## Additional Update (2026-06-07) - Portal Theme And Korean Font Refresh
- Replaced the portal theme with the recommended `Procurement Slate` palette.
  - Background: `#f6f8fb`
  - Text: `#172033`
  - Primary brand: `#1d4ed8`
  - Deep brand: `#1e3a8a`
  - Secondary accent: `#0f766e`
- Updated global theme tokens, duplicate theme tokens, and major hard-coded UI colors in `frontend/src/styles.css` to blue, slate, and teal.
- Replaced the broken Korean font fallback stack with `Pretendard Variable`, `Pretendard`, `Noto Sans KR`, `Apple SD Gothic Neo`, `Malgun Gothic`, `system-ui`, and `sans-serif`.
- Shortened the sidebar brand copy to avoid awkward one-character wrapping.
- Test coverage:
  - Added frontend contract assertions for the Procurement Slate tokens and Korean font stack.
  - Added assertions preventing the old pink/cream tokens and broken font fallbacks from returning.
- Verification:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: passed
  - `rg`: no stale theme tokens or broken font fallbacks found in `frontend/src/styles.css`
  - Playwright production-build UI check: CSS variables, Pretendard stack, and stale copy checks passed
  - Screenshot saved to `temp/portal-theme-check.png`

## 작업 기록 (2026-06-07) - 상단 히어로 축소 및 워드마크 추가
- 사용자 요청에 따라 `hero-panel hero-panel--mark` 상단 영역을 더 작게 축소했다.
  - 실제 화면 검증 기준 히어로 높이: 약 84px
  - 중앙 메인 아이콘 크기와 보조 아이콘 크기를 함께 축소
  - 기존 넓은 빈 공간을 줄이고 운영 화면의 밀도를 높임
- 상단 히어로에 워드마크를 추가했다.
  - `SMART Procurement`
  - `SMART 조달청 계산기`
- 접근성 보강:
  - 워드마크 텍스트는 실제 텍스트로 노출
  - 장식 아이콘 그룹은 `aria-hidden`으로 처리
- 모바일 보강:
  - 640px 이하에서 워드마크와 아이콘이 겹치거나 밀리지 않도록 wrap 규칙 추가
- 테스트 보강:
  - `backend/tests/test_frontend_contracts.py`에 히어로 워드마크 구조와 축소된 히어로 크기 토큰 검증 추가
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: 통과
  - Playwright 빌드 산출물 화면 검증: 히어로 높이 84px, 워드마크 2줄, 보조 아이콘 4개, stale copy 미노출 확인
  - Playwright 스크린샷 저장: `temp/portal-hero-wordmark-check.png`

## Additional Update (2026-06-07) - Compact Hero Wordmark
- Reduced the `hero-panel hero-panel--mark` masthead size.
  - Verified rendered hero height: about 84px
  - Reduced the main icon and supporting icon sizes
  - Removed visual emptiness from the top masthead
- Added a visible masthead wordmark:
  - `SMART Procurement`
  - `SMART 조달청 계산기`
- Accessibility:
  - Kept the wordmark as real text.
  - Marked decorative icon groups as `aria-hidden`.
- Responsive behavior:
  - Added a 640px breakpoint so the wordmark and icon nodes wrap cleanly on narrow screens.
- Test coverage:
  - Extended `backend/tests/test_frontend_contracts.py` to assert the hero wordmark structure and compact height token.
- Verification:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: passed
  - Playwright production-build UI check: 84px hero height, two-line wordmark, four supporting icons, no stale copy
  - Screenshot saved to `temp/portal-hero-wordmark-check.png`

## 작업 기록 (2026-06-07) - 사이드바 브랜드 카드 아이콘 전용 정리
- 사용자 요청에 따라 왼쪽 상단 `brand-card`를 아이콘 전용 카드로 단순화했다.
  - 기존 `SC` 텍스트와 `SMART Procurement` / `SMART 조달청 계산기` / 설명 문구 블록 제거
  - 상단 히어로에 제품명이 이미 있으므로 사이드바는 장식성 브랜드 아이콘만 유지
  - `LayoutDashboard` 아이콘을 사용하고 장식 아이콘에는 `aria-hidden` 적용
  - `brand-card`에는 접근성 라벨 `SMART 조달청 계산기` 유지
- 스타일 보정:
  - `brand-card`를 한 칸짜리 `inline-grid` 카드로 변경
  - 실제 화면 기준 약 70x70 크기의 간결한 아이콘 카드로 확인
- 테스트 보강:
  - `backend/tests/test_frontend_contracts.py`에 브랜드 카드가 아이콘 전용 구조인지 검증 추가
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: 통과
  - Playwright 빌드 산출물 화면 검증: 브랜드 카드 텍스트 없음, SVG 1개, 약 70x70 크기 확인
  - Playwright 스크린샷 저장: `temp/portal-brand-icon-only-check.png`

## Additional Update (2026-06-07) - Sidebar Brand Card Icon-Only
- Simplified the sidebar `brand-card` to an icon-only mark.
  - Removed the previous `SC` text and the sidebar brand text block.
  - Kept the product name in the top hero wordmark instead.
  - Used the existing `LayoutDashboard` icon as the sidebar brand mark.
  - Marked the decorative icon as `aria-hidden` and kept an accessible label on `brand-card`.
- Styling:
  - Changed `brand-card` to a compact one-cell `inline-grid` card.
  - Verified rendered size: about 70x70.
- Test coverage:
  - Extended `backend/tests/test_frontend_contracts.py` to assert the icon-only brand-card structure.
- Verification:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: passed
  - Playwright production-build UI check: no brand-card text, one SVG icon, about 70x70 card size
  - Screenshot saved to `temp/portal-brand-icon-only-check.png`

## 작업 기록 (2026-06-07) - 사이드바 브랜드 카드 완전 제거
- 사용자 피드백에 따라 왼쪽 상단 `brand-card` 자체를 완전히 제거했다.
  - 사이드바는 별도 브랜드 카드 없이 바로 `업무 현황` 섹션부터 시작한다.
  - 제품명과 브랜드 표식은 상단 히어로 워드마크에만 유지한다.
- 정리 범위:
  - `frontend/src/app/App.tsx`에서 `brand-card` JSX 삭제
  - `frontend/src/styles.css`에서 `.brand-card`, `.brand-mark`, `.brand-copy` 관련 전용 스타일 제거
  - `backend/tests/test_frontend_contracts.py`에서 `brand-card`/`brand-mark`가 앱과 스타일에 남지 않는지 검증하도록 수정
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: 통과
  - `rg`: `brand-card`/`brand-mark`/`brand-copy`가 프론트 앱과 CSS에 남지 않음
  - Playwright 빌드 산출물 화면 검증: `brand-card` 0개, `brand-mark` 0개, 사이드바 시작 텍스트 `업무 현황` 확인
  - Playwright 스크린샷 저장: `temp/portal-brand-card-removed-check.png`

## Additional Update (2026-06-07) - Sidebar Brand Card Removed
- Removed the sidebar `brand-card` entirely after user feedback.
  - The sidebar now starts directly with the `업무 현황` navigation section.
  - Product branding remains only in the top hero wordmark.
- Cleanup scope:
  - Removed `brand-card` JSX from `frontend/src/app/App.tsx`.
  - Removed `.brand-card`, `.brand-mark`, and `.brand-copy`-specific styles from `frontend/src/styles.css`.
  - Updated `backend/tests/test_frontend_contracts.py` to assert that `brand-card` and `brand-mark` do not return.
- Verification:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 6 tests OK
  - `npm run build`: passed
  - `rg`: no `brand-card`/`brand-mark`/`brand-copy` in frontend app or CSS
  - Playwright production-build UI check: zero `brand-card`, zero `brand-mark`, sidebar starts with `업무 현황`
  - Screenshot saved to `temp/portal-brand-card-removed-check.png`

## 작업 기록 (2026-06-07) - 백엔드 디버깅 로그 추가 계획 작성
- 사용자 요청에 따라 이슈 발생 시 백엔드 단에서 디버깅할 수 있도록 파일 로그를 추가하는 계획을 작성했다.
- 현재 코드 분석 결과:
  - `operation_runs`, `backup_runs`, `nara_collection_runs` 등 관리자용 이력 DB는 존재한다.
  - 하지만 Flask 요청 단위 `request_id`, 예외 stacktrace, PDF/OCR/RAG/나라장터/계약서/백업 단계별 파일 로그는 부족하다.
  - `backend/app/main.py`에는 JSON UTF-8 보정용 `after_request`만 있고, 요청 시작/종료/예외 로깅 훅은 없다.
- 신규 계획 문서:
  - `docs/backend-debug-logging-plan.md`
- 계획 핵심:
  - `backend/storage/logs/backend.log`
  - `backend/storage/logs/backend-error.log`
  - JSON Lines + RotatingFileHandler
  - API 키, `serviceKey`, Authorization, 원문 OCR/LLM prompt 마스킹
  - 문서 분석, PDF 리더, 기준문서 RAG, 나라장터 첨부, AI 요약, 계약서 생성, 백업 로직에 우선 로그 추가
- 검증:
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- docs/backend-debug-logging-plan.md docs/work-log.md`: 공백 문제 없음

## Additional Update (2026-06-07) - Backend Debug Logging Plan
- Created a plan for backend file logging so failures can be debugged from local backend logs.
- Current code review summary:
  - User-facing operation history tables already exist.
  - Detailed developer-facing request ids, exception stacktraces, and domain step logs are missing.
  - `backend/app/main.py` currently has only the UTF-8 JSON `after_request` hook, not request lifecycle/error logging.
- New document:
  - `docs/backend-debug-logging-plan.md`
- Plan highlights:
  - `backend/storage/logs/backend.log`
  - `backend/storage/logs/backend-error.log`
  - JSON Lines + RotatingFileHandler
  - Sanitization for API keys, `serviceKey`, Authorization, raw OCR text, and LLM prompts
  - Priority logging for document analysis, PDF readers, basis RAG, Nara attachments, AI summary, contract generation, and backups
- Verification:
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- docs/backend-debug-logging-plan.md docs/work-log.md`: no whitespace errors
## 추가 업데이트 (2026-06-07) - 백엔드 디버깅 로그 구현

### 한국어 기록
- 작업 범위: 이슈 발생 시 백엔드에서 원인 추적이 가능하도록 공통 JSONL 로그, 요청 추적 ID, 예외 stacktrace 저장, 주요 실패 지점 이벤트 로그를 추가했다.
- 추가/수정 파일:
  - `backend/app/core/logging.py`: JSON Lines formatter, rotating file logger, 민감정보 마스킹, `log_event`, `log_exception`, `request_id` 유틸 추가.
  - `backend/app/core/config.py`: `BACKEND_LOG_DIR`, `BACKEND_LOG_LEVEL`, `BACKEND_LOG_MAX_MB`, `BACKEND_LOG_BACKUPS`, `BACKEND_LOG_FORMAT`, `BACKEND_LOG_REQUEST_BODY` 설정 필드 추가.
  - `backend/app/main.py`: Flask 요청 시작/완료 로그, `X-Request-ID` 응답 헤더, 전역 예외 로그, 문서 분석/AI 요약/나라장터 분석 실패 지점 로그 추가.
  - `backend/app/pipelines/parser.py`, `backend/app/pipelines/pdf_readers.py`, `backend/app/pipelines/ocr.py`, `backend/app/pipelines/basis_document.py`: PDF/문서 추출, OCR, 기준문서 RAG 처리/검색/인덱스 검증 이벤트 로그 추가.
  - `backend/app/services/nara_api.py`, `backend/app/services/contract_documents.py`, `backend/app/services/backups.py`: 나라장터 HTTP/첨부 다운로드, 계약서 생성, 백업 생성/검증/복원계획 로그 추가.
  - `backend/tests/test_backend_logging.py`: 로그 파일 생성, JSONL 구조, 민감값 마스킹 테스트 추가.
  - `backend/tests/test_api_flows.py`: API 응답의 `X-Request-ID` 계약 테스트 추가.
  - `.gitignore`: `backend/storage/logs/` 운영 로그 산출물 제외 규칙 추가.
- 로그 저장 정책:
  - 기본 저장 위치: `backend/storage/logs/backend.log`, `backend/storage/logs/backend-error.log`
  - 포맷: UTF-8 JSON Lines
  - 기본 회전 정책: 20MB, 10개 보관
  - 원문 API 키, Authorization, serviceKey/token 쿼리, 주민등록번호, 사업자등록번호는 마스킹한다.
- 검증:
  - AST 문법 검사: 통과
  - `backend.tests.test_backend_logging`: 3건 통과
  - `backend.tests.test_ocr`, `backend.tests.test_parser`, `backend.tests.test_nara_url_safety`: 12건 통과, 실 OCR 샘플 1건 skip
  - `backend.tests.test_api_flows.ApiFlowTests.test_api_responses_include_request_id_for_debug_logs`: 1건 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check`: 공백 오류 없음, CRLF 변환 경고만 발생
- 환경 메모:
  - 현재 샌드박스에서 Python `tempfile`이 만든 임시 디렉터리와 SQLite 기본 파일 DB journaling이 간헐적으로 `PermissionError`/`disk I/O error`를 발생시켜 표준 `unittest` 직접 실행은 일부 막혔다.
  - 로깅/문서/OCR/API 계약 검증은 프로젝트 하위 안전 임시 디렉터리와 테스트 프로세스 한정 SQLite journal 우회 러너로 실행했다.

### AI / Engineering Version (English)
- Implemented backend debug logging with JSONL rotating files, request correlation IDs, exception stack traces, and domain event logs.
- Added sensitive-data masking for API keys, service keys, auth headers, token query parameters, RRNs, and business registration numbers.
- Instrumented risky paths: Flask request lifecycle, document analysis, AI summary, parser, PDF readers, OCR, basis-document RAG/index validation/search, Nara API/downloads, contract generation, and backups.
- Added `backend/tests/test_backend_logging.py` and an API response `X-Request-ID` contract assertion.
- Added `.gitignore` coverage for `backend/storage/logs/`.
- Verified with AST parse, logging/OCR/parser/Nara URL safety unit tests, the API request-id contract test, encoding check, and diff whitespace check. Standard direct unittest execution was partially blocked by sandbox-specific tempfile/SQLite file I/O restrictions, so sandbox-safe test runners were used.
## 추가 업데이트 (2026-06-07) - 기준문서 청크 더보기 UI 적용

### 한국어 기록
- 작업 범위: 기준문서 관리 화면에서 생성된 청크 본문을 한 번에 모두 렌더링하지 않도록 기본 접힘 UI를 추가했다.
- 변경 내용:
  - `frontend/src/pages/BasisDocumentsPage.tsx`
    - 청크 본문 기본 표시 길이를 `CHUNK_PREVIEW_LIMIT = 360`자로 제한했다.
    - 긴 청크에는 `더보기` / `접기` 버튼을 표시한다.
    - 사용자가 펼친 청크만 전체 본문을 렌더링한다.
    - 기준문서 상세를 다시 불러오거나 다른 문서를 선택하면 펼침 상태를 초기화한다.
  - `frontend/src/styles.css`
    - `.chunk-row__body`, `.chunk-row__text`, `.chunk-row__toggle` 스타일을 추가했다.
  - `backend/tests/test_frontend_contracts.py`
    - 청크 본문이 다시 `<p>{chunk.chunk_text}</p>` 방식으로 전체 렌더링되지 않도록 계약 테스트를 추가했다.
- 기대 효과:
  - 청크 수가 많고 본문이 긴 기준문서에서도 초기 DOM 텍스트량이 줄어 기준문서 관리 페이지 렉을 줄인다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 7건 통과
  - `npm run build`: 통과

### AI / Engineering Version (English)
- Added collapsed-by-default chunk rendering on `BasisDocumentsPage`.
- Long chunks render only a 360-character preview until the user clicks `더보기`; expanded chunks can be collapsed with `접기`.
- Added CSS for chunk body/toggle and a frontend contract test to prevent reintroducing full chunk text rendering.
- Verified with frontend contract tests and production build.
## 추가 업데이트 (2026-06-07) - 기준문서 목록 로딩바 추가

### 한국어 기록
- 작업 범위: 기준문서 관리 메뉴에서 기준문서 목록을 불러오는 동안 로딩 상태가 명확히 보이도록 로딩바를 추가했다.
- 변경 내용:
  - `frontend/src/pages/BasisDocumentsPage.tsx`
    - `"기준문서를 불러오는 중입니다."` 로딩 상태에 `loading-state`와 `loading-bar`를 추가했다.
    - `role="progressbar"`와 `aria-label="기준문서 로딩 진행 상태"`를 넣어 접근성 정보를 제공한다.
  - `frontend/src/styles.css`
    - `.loading-state`, `.loading-bar`, `.loading-bar span`, `@keyframes loadingBarSweep` 스타일을 추가했다.
  - `backend/tests/test_frontend_contracts.py`
    - 기준문서 로딩 상태에 로딩바와 접근성 속성이 유지되는지 확인하는 계약 테스트를 추가했다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 8건 통과
  - `npm run build`: 통과

### AI / Engineering Version (English)
- Added an animated progress bar to the Basis Documents loading state.
- The loading UI now includes `role="progressbar"` and an accessible Korean label.
- Added frontend contract coverage and verified with tests plus production build.

## 추가 업데이트 (2026-06-07) - 기준문서 청크 지연 로딩 보강

### 한국어 기록
- 작업 범위: 기준문서 관리 화면의 `surface-card` 청크 영역이 페이지 진입 시 모든 청크 목록과 본문을 렌더링해 렉을 유발하던 문제를 보강했다.
- 변경 내용:
  - `backend/app/main.py`
    - 기준문서 상세 조회 API가 청크 목록을 기본 payload에 포함하지 않도록 변경했다.
    - 청크 목록은 `/api/basis-documents/<id>/chunks` 전용 API에서만 반환하도록 분리했다.
  - `frontend/src/app/api.ts`
    - `listBasisDocumentChunks(id)` API 클라이언트 함수를 추가했다.
  - `frontend/src/pages/BasisDocumentsPage.tsx`
    - 기준문서 목록 로딩 후 첫 문서를 자동 선택하지 않도록 변경했다.
    - 청크 영역은 기본적으로 "청크 본문은 숨겨져 있습니다." 안내만 보여주고, `청크 보기` 버튼을 눌렀을 때만 청크 API를 호출한다.
    - 청크 로딩 중에는 별도 로딩바를 표시하고, 다른 문서를 선택하면 청크 표시/확장 상태를 초기화한다.
  - `backend/tests/test_frontend_contracts.py`
    - 기준문서 화면이 `selectedDoc.chunks.map`으로 즉시 렌더링하지 않는지, 첫 문서 자동 선택 fallback이 없는지, 청크 전용 API를 사용하는지 검증하는 계약 테스트를 보강했다.
- 기대 효과:
  - 기준문서 관리 페이지 진입 시 큰 기준문서의 청크 목록/본문 DOM이 생성되지 않아 초기 렌더링 렉을 줄인다.
  - 사용자가 실제로 필요한 경우에만 청크 목록을 불러와 확인한다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 8건 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- frontend/src/pages/BasisDocumentsPage.tsx frontend/src/app/api.ts backend/app/main.py backend/tests/test_frontend_contracts.py docs/work-log.md frontend/src/styles.css`: 공백 오류 없음, CRLF 변환 경고만 발생

### AI / Engineering Version (English)
- Hardened the Basis Documents chunk UX from preview-only rendering to lazy loading.
- `GET /api/basis-documents/<id>` no longer includes chunks by default; chunks are returned only by `GET /api/basis-documents/<id>/chunks`.
- `BasisDocumentsPage` no longer auto-selects the first basis document after list load.
- The chunk `surface-card` now renders a hidden-state message by default and fetches chunks only after the user clicks `청크 보기`.
- Added frontend contract assertions to prevent immediate `selectedDoc.chunks.map` rendering and first-document fallback selection from returning.
- Verified with frontend contract tests, production build, encoding check, and diff whitespace check.

## 추가 업데이트 (2026-06-07) - 메뉴/액션 버튼 도움말 가이드 추가

### 한국어 기록
- 작업 범위: 왼쪽 메뉴와 주요 액션 버튼 오른쪽에 작은 원형 `?` 도움말 버튼을 추가하고, 클릭 시 해당 메뉴/버튼의 목적과 동작 설명을 보여주는 가이드 레이어를 구현했다.
- 변경 내용:
  - `frontend/src/app/helpGuides.tsx`
    - 메뉴별 상세 설명 데이터와 액션 버튼별 설명 매핑을 추가했다.
    - `ActionHelpProvider`를 추가해 화면의 일반 버튼과 `.link-button` 액션을 감지하고 오른쪽에 자동 `?` 도움말 버튼을 붙이도록 했다.
    - `HelpGuideButton`을 추가해 메뉴 항목처럼 명시적으로 붙이는 도움말 버튼을 제공했다.
    - 도움말 클릭 시 `role="dialog"` 모달로 요약과 상세 설명 목록을 표시한다.
  - `frontend/src/app/App.tsx`
    - 앱 전체를 `ActionHelpProvider`로 감쌌다.
    - 왼쪽 메뉴 항목을 `nav-card-row`로 구성하고 각 메뉴 오른쪽에 `HelpGuideButton`을 추가했다.
  - `frontend/src/styles.css`
    - `.nav-card-row`, `.help-guide-trigger`, `.action-help-trigger`, `.help-guide-backdrop`, `.help-guide-dialog` 스타일을 추가했다.
    - 전역 `button` 스타일에 덮이지 않도록 최종 override에서 `?` 아이콘을 16px 작은 원형 버튼으로 고정했다.
  - `backend/tests/test_frontend_contracts.py`
    - 메뉴/액션 도움말 provider 연결, 자동 버튼 감지 selector, dialog, 작은 아이콘 크기 계약 테스트를 추가했다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 9건 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- frontend/src/app/App.tsx frontend/src/app/helpGuides.tsx frontend/src/styles.css backend/tests/test_frontend_contracts.py docs/work-log.md`: 공백 오류 없음, CRLF 변환 경고만 발생

### AI / Engineering Version (English)
- Added a global help-guide layer for menu items and action buttons.
- `ActionHelpProvider` decorates normal `button` elements and `.link-button` anchors with a small circular `?` trigger.
- Menu rows now render an explicit `HelpGuideButton` next to each navigation card.
- Help content opens in an accessible dialog with a summary and detailed bullet list.
- Final CSS override keeps the `?` trigger at 16px so it does not inherit the primary action button treatment.
- Added frontend contract coverage and verified with tests, production build, encoding check, and diff whitespace check.

## 추가 업데이트 (2026-06-07) - OCR 기본 사용 설정 및 PaddleOCR 캐시 권한 복구

### 한국어 기록
- 작업 범위: 운영 대시보드에서 OCR이 `사용 불가`로 표시되고 실제 PaddleOCR 초기화도 실패하던 문제를 수정했다.
- 원인:
  - OCR 파이프라인 기본값은 `paddle`이었지만, 운영 상태 체크(`operations._ocr_health`)는 `OCR_ENGINE`이 없으면 `noop`으로 판단해 대시보드에 `사용 불가`를 표시했다.
  - 현재 `backend/.env`에 `OCR_ENGINE`이 명시되어 있지 않았다.
  - PaddleOCR 모델 캐시의 `korean_PP-OCRv5_mobile_rec/inference.yml` 파일 ACL이 깨져 실제 초기화 시 접근 거부가 발생했다.
  - PDF OCR 렌더링 임시파일도 OS 임시폴더를 사용해 샌드박스/권한 환경에서 실패할 수 있었다.
- 변경 내용:
  - `backend/app/services/operations.py`
    - OCR 상태 체크 기본 엔진을 `paddle`로 변경했다.
    - `paddleocr`, `paddle`, `fitz` 의존성 존재 여부를 확인해 누락 시 명확한 `unavailable` 사유를 반환하도록 했다.
    - 정상 설정 시 `configured`, `engine: paddle`, `language: kor+eng`로 표시되도록 했다.
  - `backend/.env`
    - 현재 PC 로컬 설정에 `OCR_ENGINE=paddle`, `OCR_MIN_TEXT_LENGTH=80`, `OCR_RENDER_DPI=220`, `OCR_TEMP_DIR=./storage/ocr-temp`, `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True`를 추가했다.
  - `backend/.env.example`
    - 다른 PC 세팅에서도 OCR이 기본 paddle 엔진으로 잡히도록 같은 OCR 설정 예시를 추가했다.
  - `backend/app/pipelines/ocr.py`
    - PDF OCR 렌더링과 한글 경로 우회용 임시파일을 OS 임시폴더가 아니라 `OCR_TEMP_DIR` 하위에 생성하도록 변경했다.
  - `backend/tests/test_operations_ocr_health.py`
    - OCR 상태 체크가 기본 `paddle`로 동작하고, `noop` 명시와 의존성 누락을 정확히 보고하는 테스트를 추가했다.
  - `backend/tests/test_ocr.py`
    - OCR 테스트 임시파일을 프로젝트 내부 테스트 디렉터리에 생성하도록 변경해 Windows 임시폴더 권한 문제를 피했다.
  - 로컬 환경 조치
    - `C:\Users\HOONJAE\.paddlex\official_models\korean_PP-OCRv5_mobile_rec` 모델 캐시 ACL을 reset하고 현재 사용자 권한을 재부여했다.
- 검증:
  - `py -3.13 -c "from dotenv import load_dotenv; load_dotenv('.env'); from app.pipelines.ocr import get_ocr_engine; e=get_ocr_engine(); print(e.name); print(e.is_available())"`: `paddle`, `True`
  - `py -3.13 -m unittest tests.test_operations_ocr_health tests.test_ocr -v`: 7건 통과, 실제 샘플 OCR 테스트 1건은 `RUN_REAL_OCR_TESTS=1` 미설정으로 skip
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- backend/app/services/operations.py backend/app/pipelines/ocr.py backend/.env backend/.env.example backend/tests/test_operations_ocr_health.py backend/tests/test_ocr.py docs/work-log.md`: 공백 오류 없음, CRLF 변환 경고만 발생
- 운영 메모:
  - 이미 실행 중인 백엔드 서버가 있다면 `.env` 변경을 반영하려면 서버 재시작이 필요하다.

### AI / Engineering Version (English)
- Fixed OCR health reporting so the operations dashboard no longer treats missing `OCR_ENGINE` as `noop`; default is now `paddle`, matching the OCR pipeline.
- Added explicit local/env-example OCR settings for PaddleOCR, OCR threshold, render DPI, OCR temp dir, and PaddleX model-source check disabling.
- Moved OCR rendering temp files from OS temp directories to `OCR_TEMP_DIR` to avoid Windows sandbox/temp ACL failures.
- Added OCR health contract tests and stabilized OCR tests with project-local temp directories.
- Repaired local PaddleOCR Korean recognition model cache ACL so `get_ocr_engine().is_available()` returns `True`.
- Verified with OCR health tests, OCR pipeline tests, real PaddleOCR initialization, encoding check, and diff whitespace check.

## 추가 업데이트 (2026-06-07) - 액션 도움말 버튼 간격 보정

### 한국어 기록
- 작업 범위: 자동으로 붙는 작은 `?` 도움말 버튼이 `section-heading` 안에서 액션 버튼과 멀리 떨어져 보이는 문제를 수정했다.
- 원인:
  - `section-heading`이 `justify-content: space-between`을 사용하고 있었고, 자동 삽입된 `?` 버튼이 액션 버튼과 같은 그룹이 아니라 별도 flex item으로 배치되었다.
  - 그 결과 `새로고침` 같은 버튼은 가운데 쪽에, `?` 버튼은 오른쪽 끝에 가까운 위치에 놓여 간격이 크게 벌어졌다.
- 변경 내용:
  - `frontend/src/styles.css`
    - `.section-heading`을 `justify-content: flex-start`, `column-gap: 6px`로 변경했다.
    - `.section-heading > :first-child`에 `margin-right: auto`를 적용해 제목 영역만 왼쪽에 두고, 이후 액션 버튼과 `?`는 오른쪽에서 붙어 보이도록 했다.
    - `.section-heading > .action-help-trigger`는 `margin-left: -2px`로 보정했다.
    - `.toolbar`, `.form-actions`, `.row` 내부의 `.action-help-trigger`는 기존 flex gap을 감안해 `margin-left: -6px`로 보정했다.
  - `backend/tests/test_frontend_contracts.py`
    - `section-heading`이 더 이상 버튼과 `?`를 크게 벌리는 `space-between` 구조가 아닌지 확인하는 계약 테스트를 보강했다.
- 기대 효과:
  - `새로고침 ?`, `업로드 ?`, `검색 ?`처럼 액션 버튼과 도움말 아이콘이 하나의 작은 조합처럼 보인다.
  - 여러 화면의 `section-heading`, `toolbar`, `form-actions`, `row` 영역에서 동일한 간격 규칙이 적용된다.
- 검증:
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 9건 통과
  - `npm run build`: 통과

### AI / Engineering Version (English)
- Fixed action help icon spacing by changing `.section-heading` away from `justify-content: space-between`.
- The first heading child now owns the left side with `margin-right: auto`, while action buttons and generated `?` triggers stay adjacent on the right.
- Added spacing overrides for `.section-heading`, `.toolbar`, `.form-actions`, and `.row` generated action help triggers.
- Extended frontend contract tests to lock the layout behavior and prevent the large button/help gap from returning.

## 추가 업데이트 (2026-06-07) - 기준문서 OCR 강제 실행 옵션 추가

### 한국어 기록
- 작업 범위: 기준문서 업로드 옵션과 기준문서 상세의 `재처리` 버튼 옆에 `OCR 강제 실행` 토글을 추가했다.
- 변경 이유:
  - 기준문서 PDF에 텍스트 레이어가 있더라도 표/문단 추출 품질을 비교하거나 스캔 품질을 확인해야 하는 경우가 있다.
  - 기존 자동 OCR은 추출 텍스트가 짧을 때만 실행되므로, 운영자가 특정 문서를 의도적으로 OCR 경로로 재처리할 수 있는 옵션이 필요했다.
- 변경 내용:
  - `frontend/src/pages/BasisDocumentsPage.tsx`
    - 업로드 폼에 `OCR 강제 실행` 토글을 추가했다.
    - 선택된 기준문서 상세의 `재처리` 버튼 바로 옆에 작은 inline 토글을 추가했다.
    - 업로드 요청은 `force_ocr=true/false` FormData를 전송한다.
    - 재처리 요청은 `{ force_ocr: boolean }` JSON body를 전송한다.
    - 문서 상세를 불러올 때 기존 `metadata.options.force_ocr` 값을 재처리 토글 초기값으로 반영한다.
  - `frontend/src/app/api.ts`
    - `reprocessBasisDocument(id, body)`가 JSON body를 받을 수 있게 변경했다.
  - `frontend/src/styles.css`
    - 업로드용 토글, 재처리 옆 inline 토글, 재처리 액션 그룹 스타일을 추가했다.
  - `backend/app/main.py`
    - 업로드 FormData의 `force_ocr` 값을 파싱하고 `metadata_json.options.force_ocr`로 저장한다.
    - 재처리 API에서 JSON body의 `force_ocr` 값을 받아 처리 옵션으로 전달한다.
    - operation run 요청 payload에도 실제 적용된 재처리 옵션을 기록한다.
  - `backend/app/pipelines/ocr.py`
    - `run_ocr_if_needed(..., force=True)` 옵션을 추가했다.
    - `force=True`이면 텍스트 길이 기준을 무시하고 OCR 엔진을 호출한다.
  - `backend/app/pipelines/basis_document.py`
    - 기준문서 메타데이터의 `options.force_ocr`와 재처리 override를 병합해 처리 옵션으로 사용한다.
    - 처리 결과 메타데이터에 `options.force_ocr`를 계속 남긴다.
  - `backend/tests/test_ocr.py`
    - 텍스트가 충분해도 `force=True`이면 OCR 엔진이 호출되는 테스트를 추가했다.
  - `backend/tests/test_basis_force_ocr_contracts.py`
    - 업로드/재처리 API, 기준문서 파이프라인, 프론트 토글 계약 테스트를 추가했다.
  - `backend/tests/test_api_flows.py`
    - 기준문서 업로드 시 강제 OCR 옵션이 저장되고, 재처리 시 옵션을 끌 수 있는 API flow 테스트를 추가했다.
- 동작 정책:
  - 토글 OFF: 기존과 동일하게 추출 텍스트가 충분하면 OCR을 건너뛴다.
  - 토글 ON: 추출 텍스트가 충분해도 OCR을 실행한다.
  - OCR이 실패하거나 엔진 설정이 없으면 기존 추출 텍스트를 fallback으로 사용하되, OCR 상태와 옵션은 메타데이터에 남긴다.
- 검증:
  - `py -3.13 -m unittest tests.test_ocr tests.test_basis_force_ocr_contracts tests.test_api_flows.ApiFlowTests.test_basis_document_force_ocr_option_is_stored_and_reprocessable -v`: 9건 통과, 실제 OCR 샘플 1건 skip
  - `py -3.13 -m unittest backend.tests.test_frontend_contracts -v`: 9건 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
  - `git diff --check -- backend/app/main.py backend/app/pipelines/basis_document.py backend/app/pipelines/ocr.py backend/tests/test_ocr.py backend/tests/test_basis_force_ocr_contracts.py backend/tests/test_api_flows.py frontend/src/app/api.ts frontend/src/pages/BasisDocumentsPage.tsx frontend/src/styles.css docs/work-log.md`: 공백 오류 없음, CRLF 변환 경고만 발생

### AI / Engineering Version (English)
- Added a force-OCR option for basis-document upload and basis-document reprocessing.
- Upload sends `force_ocr` through multipart FormData; reprocess sends `{ force_ocr: boolean }` as JSON.
- Backend stores the option under `metadata_json.options.force_ocr` and uses it as the processing option.
- `run_ocr_if_needed(..., force=True)` now bypasses the text-length skip rule and invokes OCR even when extracted text is long enough.
- Basis processing persists the selected option in processing metadata, including no-text/fallback paths.
- Added OCR unit coverage, source contract coverage, and a real API flow test for upload/reprocess option persistence.

## 추가 업데이트 (2026-06-07) - 기준문서 강제 OCR 재처리 skipped 원인 확인

### 한국어 기록
- 확인 대상:
  - 기준문서: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.)`
  - 파일명: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 증상:
  - 사용자가 기존 기준문서에서 `OCR 강제 실행`을 선택하고 `재처리`를 실행했지만, 처리 후 `ocr skipped`로 표시됐다.
- 확인 결과:
  - `backend/app.db`의 해당 기준문서 row는 `ocr_status=skipped`, `metadata.options=null`, `metadata.ocr.status=skipped` 상태였다.
  - `operation_runs`의 2026-06-07 23:24:24 재처리 이력 `request_json`에는 `options.force_ocr`가 없었다.
  - 현재 코드라면 재처리 요청에 `force_ocr`가 없더라도 operation run에는 `options` 키가 기록된다.
  - `temp/servers.status.json` 기준 서버 `updated_at`이 2026-06-07 18:37:04로, OCR 강제 실행 코드가 추가되기 전부터 백엔드가 떠 있었다.
  - 따라서 원인은 코드 로직 실패가 아니라 실행 중이던 백엔드가 변경 전 코드를 계속 사용한 것이다.
- 조치:
  - `scripts/manage-servers.ps1 -Action restart`로 백엔드/프론트를 재시작했다.
  - 재시작 후 상태:
    - 백엔드: `http://127.0.0.1:18111`, PID 31600, 시작 시각 2026-06-07 23:32:31
    - 프론트: `http://127.0.0.1:5199`, PID 20008, 시작 시각 2026-06-07 23:32:31
    - `/health`: `{"status":"ok"}`
- 테스트 보강:
  - `backend/tests/test_api_flows.py`
    - 기준문서 재처리 이력의 `operation_runs.request_json.options.force_ocr` 기록 검증을 추가했다.
- 검증:
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_basis_document_force_ocr_option_is_stored_and_reprocessable -v`: 통과

### AI / Engineering Version (English)
- Investigated why force-OCR reprocess still produced `ocr skipped` for the real basis document.
- The database row had no `metadata.options` and the latest operation run request had no `options.force_ocr`.
- The managed server status showed the backend had been running since 18:37, before the force-OCR code was added.
- Root cause: stale backend process, not the current code path.
- Restarted managed backend/frontend servers so the current route and pipeline code are loaded.
- Added API flow coverage to assert `operation_runs.request_json.options.force_ocr` is recorded during basis-document reprocess.

## 추가 업데이트 (2026-06-08) - ngrok 외부 접속 실행

### 한국어 기록
- 작업 범위: 로컬 백엔드/프론트 서비스를 실행하고 ngrok 공개 URL을 생성했다.
- 실행 명령:
  - `powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 -Action start`
- 실행 결과:
  - 백엔드 로컬 URL: `http://127.0.0.1:18111`
  - 프론트 로컬 URL: `http://127.0.0.1:5199`
  - 백엔드 ngrok URL: `https://7295-118-216-124-59.ngrok-free.app`
  - 프론트 ngrok URL: `https://69c9-118-216-124-59.ngrok-free.app`
  - 백엔드 PID: 14256
  - 프론트 PID: 24112
  - 백엔드 ngrok PID: 24108
  - 프론트 ngrok PID: 9640
  - 실행 시각: 2026-06-08 19:50:21 +09:00
- 검증:
  - `curl.exe -L -H "ngrok-skip-browser-warning: 1" https://7295-118-216-124-59.ngrok-free.app/health`: HTTP 200
  - `curl.exe -L -H "ngrok-skip-browser-warning: 1" https://69c9-118-216-124-59.ngrok-free.app`: HTTP 200
  - 프론트 ngrok origin에서 백엔드 API CORS 확인: `Access-Control-Allow-Origin: https://69c9-118-216-124-59.ngrok-free.app`
- 운영 메모:
  - ngrok 터널이 켜져 있는 동안 로컬 앱이 외부에 노출된다.
  - 종료할 때는 `powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 -Action stop`을 사용한다.

### AI / Engineering Version (English)
- Started local backend/frontend and ngrok tunnels through `scripts/manage-ngrok.ps1`.
- Verified backend and frontend public ngrok URLs return HTTP 200.
- Verified CORS allows the frontend ngrok origin when calling the backend public API.
- Logged active local/public URLs and managed process ids for follow-up debugging.

## 추가 업데이트 (2026-06-08) - 기준문서 강제 OCR 진행 상태 조사 및 표시 보강

### 한국어 기록
- 확인 대상:
  - 기준문서: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.)`
  - 파일명: `전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`
- 사용자 증상:
  - `OCR 강제 실행`을 체크하고 `재처리`를 눌렀는데 화면에는 계속 `ocr skipped`가 보였다.
- 백엔드 로그 확인 결과:
  - `2026-06-08T20:02:12+09:00`에 `/api/basis-documents/1/reprocess` 요청이 들어왔다.
  - `basis.processing.options` 로그에 `force_ocr=true`가 찍혔다.
  - OpenDataLoader PDF 리더가 489페이지, 700,988자, 테이블 1,566개를 추출했다.
  - 이후 `ocr.force_required`, `ocr.run.started`, `ocr.pdf.started`가 찍혔고 OCR 엔진은 `paddle`이었다.
  - 즉 강제 OCR 요청은 정상으로 들어왔고 PaddleOCR이 실제로 시작됐다.
- 현재 진행 상태:
  - `backend/storage/ocr-temp/wisdom_ocr_03376dafbb6147b8a8bd8f059a748710` 아래에 OCR 렌더링 이미지가 계속 생성되고 있다.
  - 확인 시점 기준 `page_179.png`까지 생성됐다.
  - 489페이지 전체 OCR이라 완료까지 오래 걸릴 수 있다.
- 원인:
  - 재처리 요청이 오래 실행되는 동안 `process_basis_document()` 내부 상태 변경이 같은 DB 트랜잭션에 묶여 커밋되지 않는다.
  - 그래서 화면이나 별도 조회에서는 이전 완료 상태인 `ocr skipped`가 계속 보였다.
  - 실제로는 강제 OCR이 진행 중이며, 표시만 이전 상태를 보고 있었다.
- 코드 보강:
  - `backend/app/main.py`
    - 재처리 API가 실제 처리에 들어가기 전에 `processing_status='parsing'`, `parse_status='processing'`, `ocr_status='processing'`, `chunk_status='pending'`, `index_status='pending'`을 먼저 저장하고 즉시 `conn.commit()`하도록 수정했다.
    - 다음 재처리부터 긴 OCR 중에도 화면/새로고침에서 이전 `ocr skipped`가 아니라 진행 상태를 볼 수 있다.
  - `backend/tests/test_basis_force_ocr_contracts.py`
    - 재처리 시작 상태 선커밋 계약을 테스트에 추가했다.
- 검증:
  - `py -3.13 -m unittest tests.test_basis_force_ocr_contracts -v`: 3건 통과
- 운영 메모:
  - 현재 진행 중인 489페이지 PaddleOCR 작업을 중단하지 않기 위해 서버 재시작은 하지 않았다.
  - 이번 표시 보강 코드는 다음 백엔드 재시작 후 적용된다.

### AI / Engineering Version (English)
- Investigated the real basis-document force-OCR reprocess after the user still saw `ocr skipped`.
- Logs show `force_ocr=true`, OpenDataLoader extraction completed for 489 pages, and PaddleOCR started.
- The old `ocr skipped` display is stale persisted state while the long synchronous OCR request is still running.
- Added a pre-processing status commit in the reprocess route so future long reprocess runs persist `ocr_status='processing'` before entering the long pipeline.
- Did not restart the active backend because the current 489-page OCR job is still running.

## 추가 업데이트 (2026-06-08) - 강제 OCR 재처리 진행 UI 추가

### 한국어 기록
- 작업 범위: 기준문서 상세 화면에서 강제 OCR 재처리 중임을 사용자가 명확히 볼 수 있도록 로딩바와 진행 안내를 추가했다.
- 사용자 증상:
  - 489페이지 기준문서가 PaddleOCR로 처리 중인데 화면에는 이전 상태인 `ocr skipped`가 계속 보여 혼란이 있었다.
- 변경 내용:
  - `frontend/src/pages/BasisDocumentsPage.tsx`
    - 재처리 버튼 클릭 직후 선택 문서의 상태를 프론트에서 즉시 `processing`으로 표시하도록 했다.
    - 재처리 중인 문서 상세 영역에 `basis-processing-panel`을 표시한다.
    - `OCR 강제 실행 처리 중`, 처리 경과 시간, 전체 페이지 처리 안내, indeterminate 로딩바를 보여준다.
    - 재처리 중에는 `OCR 강제 실행` 토글과 `재처리` 버튼을 비활성화해 중복 클릭을 막는다.
    - OCR 강제 실행 시 전역 작업 오버레이 설명과 단계 문구를 대용량 OCR 흐름에 맞게 바꿨다.
  - `frontend/src/app/workOverlay.tsx`
    - 전역 작업 오버레이에도 로딩바를 추가했다.
  - `frontend/src/styles.css`
    - 기준문서 처리 패널, 오버레이 로딩바, 재처리 중 disabled 상태 스타일을 추가했다.
  - `backend/tests/test_basis_force_ocr_contracts.py`
    - 강제 OCR 재처리 진행 UI와 중복 클릭 방지 계약을 테스트에 추가했다.
- 현재 운영 상태:
  - 기존 489페이지 PaddleOCR 작업은 계속 진행 중이며 확인 시점 기준 `page_208.png`까지 생성됐다.
  - 프론트 변경은 Vite 개발 서버에서 HMR로 반영될 수 있지만, 백엔드 선커밋 보강은 백엔드 재시작 후 적용된다.
  - 현재 OCR 작업을 끊지 않기 위해 백엔드 재시작은 하지 않았다.
- 검증:
  - `py -3.13 -m unittest tests.test_basis_force_ocr_contracts -v`: 3건 통과
  - `npm run build`: 통과

### AI / Engineering Version (English)
- Added visible long-running reprocess feedback for basis-document force OCR.
- The selected document is optimistically marked as `processing` immediately after reprocess starts.
- Added an inline `basis-processing-panel` with elapsed time, forced-OCR copy, and an indeterminate progress bar.
- Disabled the reprocess toggle/button while the selected document request is in flight.
- Added a progress bar to the global work overlay and updated force-OCR step copy.
- Verified with frontend contract tests and production build.

## 추가 업데이트 (2026-06-08) - 전체 서버 강제 종료

### 한국어 기록
- 사용자 요청에 따라 백엔드, 프론트엔드, ngrok 터널을 모두 강제 종료했다.
- 기존 상태 파일에 기록된 관리 프로세스와 포트 점유 프로세스를 기준으로 종료했다.
- 남아 있던 Vite 개발 서버 관련 `node.exe`/`cmd.exe` 프로세스도 추가로 정리했다.
- `temp/ngrok.status.json` 상태 파일은 일반 권한 삭제가 막혀 권한 상승으로 단일 파일 삭제를 수행했다.
- 종료 후 확인 결과:
  - `18111` 백엔드 포트: 리스너 없음
  - `5199` 프론트엔드 포트: 리스너 없음
  - `4040`, `4041` ngrok API 포트: 리스너 없음
  - `py`, `python`, `node`, `ngrok`, `cmd` 서버성 프로세스: 남은 항목 없음

### AI / Engineering Version (English)
- Force-stopped all local service processes on user request: backend, frontend, and ngrok tunnels.
- Cleaned up managed PIDs, port listeners, remaining Vite `node.exe`/`cmd.exe` processes, and the stale ngrok status file.
- Verified that backend, frontend, and ngrok ports no longer have listeners and no server-like processes remain.

## 추가 업데이트 (2026-06-08) - OCR 강제 실행 inline 경고 추가

### 한국어 기록
- 사용자 요청에 따라 기준문서 업로드와 기준문서 재처리의 `OCR 강제 실행` 선택 시 inline 경고 문구가 보이도록 수정했다.
- 경고 문구:
  - `OCR 강제 실행은 PDF 전체 페이지를 다시 판독하므로 대용량 기준문서는 오래 걸릴 수 있습니다.`
- 업로드 폼에서는 체크박스 선택 직후 폼 내부에 경고가 표시된다.
- 기존 기준문서 재처리 영역에서는 `OCR 강제 실행` 선택 후 `재처리`를 누르기 전에 버튼 아래 compact 경고가 표시된다.
- 진행 중에는 기존 `basis-processing-panel`의 진행 안내와 로딩바가 담당하므로, 사전 선택 경고와 처리 진행 안내를 분리했다.
- 회귀 방지를 위해 `backend/tests/test_basis_force_ocr_contracts.py`에 경고 문구와 스타일 class 확인을 추가했다.
- 검증:
  - `py -3.13 -m unittest tests.test_basis_force_ocr_contracts -v`: 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: 통과
  - `git diff --check`: 공백 오류 없음

### AI / Engineering Version (English)
- Added inline warning copy when force OCR is selected in both basis-document upload and reprocess controls.
- The upload form shows a full-width warning immediately after the force-OCR toggle.
- The reprocess action area shows a compact warning before the user starts reprocessing.
- Added CSS for `inline-warning` and `basis-reprocess-control`.
- Updated the force-OCR contract test to assert the warning copy and classes.
- Verified with the backend contract test, frontend production build, encoding check, and git whitespace check.

## 추가 업데이트 (2026-06-14) - FE/BE/ngrok 서버 실행

### 한국어 기록
- 사용자 요청에 따라 백엔드, 프론트엔드, ngrok 터널을 실행했다.
- 최초 일반 권한 실행에서는 ngrok 외부 접속이 sandbox 네트워크 제한으로 실패해 권한 상승으로 재실행했다.
- 실행 주소:
  - 백엔드 로컬: `http://127.0.0.1:18111`
  - 프론트엔드 로컬: `http://127.0.0.1:5199`
  - 백엔드 ngrok: `https://0354-118-216-124-59.ngrok-free.app`
  - 프론트엔드 ngrok: `https://8ed6-118-216-124-59.ngrok-free.app`
- 검증:
  - 로컬 백엔드 `/health`: HTTP 200
  - 로컬 프론트엔드: HTTP 200
  - ngrok 백엔드 `/health`: HTTP 200
  - ngrok 프론트엔드: HTTP 200
  - 백엔드 CORS: 프론트엔드 ngrok origin 허용 확인

### AI / Engineering Version (English)
- Started backend, frontend, and ngrok tunnels on user request.
- Initial sandboxed run failed to connect ngrok externally; reran with elevated permissions.
- Verified local backend/frontend, public ngrok backend/frontend, and CORS from the frontend ngrok origin.

## 추가 업데이트 (2026-06-14) - 비개발자용 서비스 Rocket Pitch 문서 작성

### 한국어 기록
- 사용자 요청에 따라 현재 작성된 Markdown 문서들을 참고해 비개발자 대상 서비스 설명 문서를 새로 작성했다.
- 신규 문서:
  - `docs/service-rocket-pitch.md`
- 문서 구성은 Rocket Pitch 흐름에 맞췄다.
  - 문제 제기
  - 해결 방법
  - 제품 시연
  - 사용 요청
- 기술 중심 설명 대신 조달 실무자가 이해하기 쉬운 업무 흐름 중심으로 작성했다.
- 핵심 메시지는 `최종 판단 자동화`가 아니라 `공고, 첨부파일, 법인 증빙자료, 기준문서를 묶어 부족조건과 필요서류를 빠르게 확인하는 업무 보조 포탈`로 정리했다.
- 참고한 주요 문서:
  - `README.md`
  - `docs/technical-design.md`
  - `docs/ux-design.md`
  - `docs/technology-summary.md`
  - `docs/eligibility-rag-implementation-plan.md`
  - `docs/ngrok-external-access-and-contract-docx-plan.md`
- README 문서 링크 목록에 `비개발자용 서비스 Rocket Pitch` 링크를 추가했다.

### AI / Engineering Version (English)
- Added a non-developer-facing rocket pitch document for the current service.
- The document frames the service through problem, solution, product demo, and usage request.
- It positions the product as a gap-first procurement review assistant rather than an automatic final-decision system.
- Added the new document to the README document-link section.

## 추가 업데이트 (2026-06-14) - Rocket Pitch 제품 시연 순서 조정

### 한국어 기록
- 사용자 피드백에 따라 `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름` 순서를 조정했다.
- 기존에는 대시보드가 시연 1번이었지만, 조달 검토 흐름상 법인 등록과 증빙자료 준비가 먼저 나오는 편이 자연스럽다고 판단했다.
- 변경 후 시연 흐름:
  - 시연 1: 법인을 등록하고 증빙자료를 준비
  - 시연 2: 대시보드에서 오늘 확인할 업무 확인
  - 시연 3: 나라장터 공고 검색/저장
  - 시연 4 이후: 요구조건 확인, 기준문서, 부족조건 비교, 계약서, 운영 상태
- AI / Engineering Version의 Demo Flow도 같은 순서로 맞췄다.

### AI / Engineering Version (English)
- Reordered the product demo flow in `docs/service-rocket-pitch.md` based on user feedback.
- Moved corporation registration and evidence preparation before the dashboard and Nara notice flow.
- Updated the English Demo Flow to match the Korean presentation sequence.

## 추가 업데이트 (2026-06-14) - 왼쪽 네비게이션 섹션별 배경색 구분

### 한국어 기록
- 사용자 요청에 따라 왼쪽 `sidebar` 네비게이션의 기능 그룹별 배경색을 다르게 적용했다.
- 메뉴 구조와 라우트는 유지하고, 기존 6개 그룹에 tone을 추가했다.
  - 업무 현황: `overview`
  - 공고 업무: `notice`
  - 문서 분석: `document`
  - 기준문서 / RAG: `rag`
  - 내부 관리: `admin`
  - 설정: `settings`
- 각 그룹은 낮은 채도의 업무용 tint 배경과 accent 색상을 사용한다.
- active 메뉴 아이콘은 해당 그룹의 accent 색상을 따라가도록 조정했다.
- 회귀 방지를 위해 프론트 계약 테스트에 nav group tone과 CSS class 검증을 추가했다.
- 검증:
  - `py -3.13 -m unittest tests.test_frontend_contracts -v`: 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: 통과
  - `git diff --check`: 공백 오류 없음
  - 브라우저 데스크톱 확인: 6개 섹션 배경색 적용, 도움말 버튼 겹침 0건
  - 브라우저 모바일 폭 확인: 6개 섹션 배경색 유지, 도움말 버튼 겹침 0건

### AI / Engineering Version (English)
- Added distinct visual tones for each left-sidebar navigation section.
- Kept navigation routes and grouping unchanged while adding group-level `tone` metadata.
- Added section background/accent CSS variables and tone-specific classes.
- Updated frontend contract tests to assert all six tones and the required CSS hooks.
- Verified with frontend contract tests, frontend build, encoding check, git whitespace check, and desktop/mobile browser checks.

## 추가 업데이트 (2026-06-14) - 네비게이션 아이콘 배경색 정합성 보강

### 한국어 기록
- 사용자 피드백에 따라 왼쪽 네비게이션의 `nav-icon` 배경색을 각 메뉴 그룹 배경색과 동일하게 맞췄다.
- 기존에는 메뉴 그룹 배경은 section tint를 사용하고, 아이콘 배경은 기본 회색 또는 active accent 색상을 사용해 색상이 따로 보였다.
- 변경 후:
  - 일반 아이콘 배경: `var(--nav-section-bg)`
  - active 아이콘 배경: `var(--nav-section-bg)`
  - 아이콘 선/색상: `var(--nav-section-accent)`
- 배경색은 동일하게 유지하고, 아이콘의 구분감은 얇은 outline과 accent 색상으로 처리했다.
- 회귀 방지를 위해 active `nav-icon`도 section background를 사용하는지 프론트 계약 테스트를 보강했다.
- 검증:
  - `py -3.13 -m unittest tests.test_frontend_contracts -v`: 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: 통과
  - `git diff --check`: 공백 오류 없음
  - 브라우저 계산 CSS 확인: 6개 섹션 모두 `nav-icon` 배경색과 섹션 배경색 일치

### AI / Engineering Version (English)
- Aligned `.nav-icon` backgrounds with each navigation section background.
- Replaced the default gray and active accent icon backgrounds with `var(--nav-section-bg)`.
- Kept contrast through icon color and subtle outline using `var(--nav-section-accent)`.
- Updated frontend contract tests to ensure active icons continue using the section background.
- Verified with frontend contract tests, frontend build, encoding check, git whitespace check, and browser computed-style checks.

## 추가 업데이트 (2026-06-14) - 네비게이션 아이콘 테두리 효과 제거

### 한국어 기록
- 사용자 피드백에 따라 왼쪽 네비게이션 `nav-icon`의 `box-shadow` 값을 삭제했다.
- 일반 아이콘과 active 아이콘 모두에서 inset outline처럼 보이던 그림자 효과를 제거했다.
- 아이콘 배경색은 메뉴 그룹 배경색과 동일하게 유지하고, 아이콘 색상만 그룹 accent 색상을 사용한다.
- 회귀 방지를 위해 `nav-icon`과 active `nav-icon` style block에 `box-shadow`가 없는지 프론트 계약 테스트를 보강했다.
- 검증:
  - `py -3.13 -m unittest tests.test_frontend_contracts -v`: 통과
  - `npm run build`: 통과
  - `py -3.13 scripts\check-encoding.py`: 통과
  - `git diff --check`: 공백 오류 없음
  - 브라우저 계산 CSS 확인: 6개 섹션 모두 `nav-icon` box-shadow `none`

### AI / Engineering Version (English)
- Removed the `.nav-icon` and `.nav-card.active .nav-icon` box-shadow styles.
- Kept icon backgrounds aligned with the section background and retained accent-colored icons only.
- Updated frontend contract tests to prevent nav icon box shadows from being reintroduced.
- Verified with frontend contract tests, frontend build, encoding check, git whitespace check, and browser computed-style checks.

## 추가 업데이트 (2026-06-14) - 데모 영상용 법인 증빙자료 샘플 확인

### 한국어 기록
- 사용자 요청에 따라 `D:\project\wisdom_procurement\source\test_doc` 폴더의 데모 전용 법인 증빙자료 샘플을 확인했다.
- 확인 결과:
  - PDF 파일 47개
  - PNG 파일 1개
- 대표 샘플:
  - `1.벡트_사업자등록증.pdf`
  - `2.중소기업확인서_중기업_20260331.pdf`
  - `20250226_(주)벡트_직생(동영상제작).pdf`
  - `기업신용평가등급확인서_벡트(공공기관 제출용).pdf`
  - `공장등록증명서_(주)벡트_250328.pdf`
  - `정보통신공사업등록증_벡트.pdf`
  - `ISO9001인증서_20270731.pdf`
  - `G-PASS기업 지정서_(주)벡트(VECT)_지정기간~271218-복사.pdf`
- 판단:
  - `service-rocket-pitch.md`의 제품 시연 흐름 중 법인 등록/증빙자료 준비 시연에 사용할 샘플이 충분히 존재한다.
  - 실제 데모 영상에서는 개인정보/민감정보 노출 여부를 확인하고 필요한 경우 마스킹 또는 데모 전용 화면/데이터로 대체해야 한다.

### AI / Engineering Version (English)
- Inspected `source/test_doc` as the demo corporation evidence sample directory.
- Found 47 PDF files and 1 PNG file.
- The folder contains enough evidence examples for the corporation registration/evidence portion of the service demo video.
- Future demo recording should check for sensitive information and use masking or demo-safe data where needed.

## 추가 업데이트 (2026-06-14) - 데모용 나라장터 공고 후보 샘플링

### 한국어 기록
- 데모 전용 법인 샘플(`source/test_doc`)의 증빙 구성을 기준으로 나라장터 공고 후보를 검토했다.
- 샘플 법인의 주요 적합 분야:
  - 직접생산확인증명서: 동영상제작
  - 정보통신공사업등록증
  - 전자칠판/인터랙티브화이트보드 관련 인증, 특허, 소프트웨어 품질 자료
  - LED전광판 관련 특허와 제조/공장 자료
- 기존 서비스의 `/api/nara/notices/search`는 현재 공사 공고 API(`getBidPblancListInfoCnstwkPPSSrch`) 중심이라, 위 샘플 법인에 잘 맞는 물품/용역 후보를 찾기에는 범위가 좁다는 점을 확인했다.
- 로컬 OpenAPI 참고문서에서 물품/용역 검색 operation을 확인했다.
  - `getBidPblancListInfoServcPPSSrch`
  - `getBidPblancListInfoThngPPSSrch`
  - `getBidPblancListInfoCnstwkPPSSrch`
  - `getBidPblancListInfoEtcPPSSrch`
- 실제 나라장터 API 키를 출력하지 않고, 물품/용역 API를 호출해 데모 후보를 샘플링했다.
- 추천 데모 공고 후보:
  - 1순위: `R26BK01560739-000` / `제31회 부산국제영화제 옥외영상채널 운영을 위한 LED 임차 및 운영 용역 업체 모집 공고`
    - 샘플 법인의 LED전광판, 영상/콘텐츠, 운영 용역 성격과 가장 잘 맞음
    - PDF 공고문 첨부가 있어 현재 PDF 분석 데모에 적합
    - 입찰마감: 2026-07-01 16:00
  - 2순위: `R26BK01563614-000` / `(가칭)검단3고등학교 신축 정보통신공사 관급자재(LED전광판)`
    - 정보통신공사업, LED전광판 제조/설치 증빙과 잘 맞음
    - PDF 공고문 첨부가 있음
  - 3순위: `R26BK01559211-000` / `제주MICE다목적복합시설 고도화사업」제주국제컨벤션센터 제2센터 LED스크린 구축`
    - LED스크린/전광판 구축 성격이라 전자칠판/디스플레이 계열 증빙 시연에 적합
    - PDF 공고문 첨부가 있음
- 결론:
  - 데모 본편에는 1순위 공고를 사용하고, 비교/부족조건 예시가 필요하면 2순위 또는 3순위 공고를 보조 샘플로 사용한다.
  - 향후 서비스 검색 UI도 공사뿐 아니라 물품/용역 operation을 함께 지원해야 샘플 법인과 실제 사업영역에 맞는 공고를 안정적으로 찾을 수 있다.

### AI / Engineering Version (English)
- Reviewed demo corporation evidence samples and mapped them to Nara notice domains.
- Confirmed that the current service search route is construction-first and does not cover the best demo-fit goods/service notices.
- Verified goods/service search operation names from local OpenAPI reference documents.
- Sampled real Nara API notice candidates without printing the API key.
- Recommended `R26BK01560739-000` as the primary demo notice because it best matches LED display, video channel operation, service-contract, and PDF attachment requirements.
- Recommended `R26BK01563614-000` and `R26BK01559211-000` as secondary demo candidates.

## 추가 업데이트 (2026-06-14) - 나라장터 물품/용역 검색 확장 및 법인 증빙 PDF 전부 별도화 구현

### 한국어 기록
- 사용자 요청 계획에 따라 나라장터 검색/저장/자동수집을 `전체`, `공사`, `용역`, `물품`, `기타` 업무유형으로 확장했다.
- 기본 검색값은 `전체`로 두었고, `all` 검색은 공사/용역/물품/기타 operation을 순차 호출한 뒤 `bidNtceNo + bidNtceOrd` 기준으로 중복 제거하도록 구현했다.
- 저장/분석 경로는 검색 결과의 `business_type`을 보존하고, 상세/기초금액 보강도 같은 업무유형 operation을 사용하도록 수정했다.
- 자동수집 실행에는 `business_type` 요청값을 추가했고, 실행 이력의 `criteria`, `result`, `result.items[]`에 업무유형을 기록하도록 했다.
- 프론트엔드 반영:
  - 나라장터 공고 검색 화면: 업무유형 선택, 결과 테이블 배지, 상세 미리보기 업무유형 표시
  - 나라장터 자동 수집 관리: 업무유형 선택, 이력/결과 업무유형 표시
  - 저장 공고 상세: 기본정보 업무유형 표시
- `source/test_doc/` 데모 법인 증빙 PDF 구성을 기준으로 새 법인 증빙 문서유형 20개를 별도 유형으로 추가했다.
- 새 문서유형은 규칙 기반 자동분류, 백엔드 문서 라벨, LLM 허용 목록, 프론트 문서유형 선택 목록에 모두 반영했다.
- 확장 증빙의 추출 후보는 기존 승인 흐름을 유지하며 `certifications_json`, `preference_tags_json`, `license_summary`, `business_item`, `evidence_expiry_summary` 같은 안전한 후보 필드로 매핑했다.
- 구현 중 추가로 발견한 버그와 수정:
  - `save_discovered_nara_notice()`에서 `business_type` 컬럼 추가 후 INSERT placeholder가 1개 부족해 자동수집 저장이 500으로 실패하던 문제를 수정했다.
  - 기준문서 재처리에서 파일이 사라진 경우, 재처리 API가 먼저 상태를 `parsing/processing`으로 바꿔 기존 completed/indexed 결과 보존 조건을 깨던 회귀를 수정했다.
  - 테스트 임시 디렉터리는 시스템 Temp 권한 차이를 줄이기 위해 `temp/api-tests` 또는 `WISDOM_TEST_TMPDIR` 기반으로 생성하도록 정리했다.
- 문서 보강:
  - `docs/narajangteo-api-analysis.md`: 업무유형별 operation 매핑과 운영 정책 추가
  - `docs/narajangteo-board-design.md`: 검색/자동수집 업무유형 UX 흐름 추가
  - `docs/corporation-evidence-auto-extraction-plan.md`: 새 증빙 문서유형과 후보 반영 정책 추가

검증:
- `py -3.13 -m unittest tests.test_corporation_evidence -v`: 14개 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 101개 통과
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 12개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음
- 참고: API flow 테스트와 frontend build는 현재 Codex sandbox의 SQLite/spawn 제한 때문에 승인된 외부 실행으로 검증했다.

### AI / Engineering Version (English)
- Implemented Nara `business_type=all|construction|service|goods|etc` across search, save/analyze, and collection runs.
- `all` search calls construction, service, goods, and etc search operations, merges results, deduplicates by notice number/order, and keeps item-level business type metadata.
- Save/analyze now preserves business type and uses matching detail/basis-amount operations.
- Added frontend business-type controls and badges to Nara search, collection runs, and saved notice detail.
- Added 20 separated corporation evidence document types based on `source/test_doc` demo samples.
- Wired the new evidence taxonomy into rule classification, backend labels, LLM allowed types, frontend manual options, and review-safe candidate extraction.
- Fixed two regressions found during verification: missing INSERT placeholder for discovered Nara notices and basis reprocess missing-file preservation being broken by premature status mutation.
- Verified with corporation evidence tests, full API flow tests, frontend contract tests, frontend build, encoding check, and whitespace check.

## 추가 업데이트 (2026-06-14) - 나라장터 병합 검색 및 확장 증빙 후보 매핑 버그 수정

### 한국어 기록
- 전체 코드 리뷰에서 발견한 버그를 우선순위대로 수정했다.
- 나라장터 `business_type=all` 검색:
  - 기존에는 각 업무유형의 같은 page 번호를 조회해 합친 뒤 자르기 때문에 전체 검색 2페이지 이후에서 공고 누락/중복 가능성이 있었다.
  - `전체` 검색 전용 병합 페이지네이션을 추가해 요청 page에 필요한 범위만큼 각 업무유형 최신 결과를 확보하고, 전체 최신순 정렬 후 page window를 반환하도록 수정했다.
  - `pagination_mode=merged_all`, `has_next_page`, `total_count_is_estimated`, `partial_errors` 응답 필드를 추가했다.
  - 일부 업무유형 API가 실패하면 성공 결과를 유지하고 `result_code=partial_failed`로 경고를 반환하며, 전체 실패 시에만 HTTP 502를 반환하도록 수정했다.
- 프론트 나라장터 검색 UX:
  - `전체` 검색에서는 `총 N건 추정`으로 표시하고 마지막 페이지 이동 버튼을 숨겼다.
  - 부분 실패가 있으면 결과 상단에 경고를 표시하되, 조회된 공고의 선택/저장/분석은 유지했다.
- 법인 증빙 전부 별도화 보강:
  - `소프트웨어사업자일반현황관리확인서`, `기술혁신형 중소기업 확인서` 같은 실제 파일명 변형이 generic 면허/중소기업 규칙보다 먼저 별도 문서유형으로 분류되도록 수정했다.
  - 확장 증빙 subject를 모든 문서에서 `business_item`으로 만들던 로직을 whitelist 방식으로 제한했다.
  - 공장소재지, G-PASS 지정번호, 조합원명 같은 값은 `license_summary`에는 남기되 `business_item` 후보로 생성하지 않게 했다.
- 기존 저장 공고 보정:
  - `nara_notices.business_type`이 기본값 `construction`으로 남아 있지만 `raw_json`에 용역/물품/기타 단서가 있는 경우만 안전하게 backfill 하도록 했다.

검증:
- `py -3.13 -m unittest tests.test_corporation_evidence -v`: 14개 통과
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 13개 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 105개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음
- 참고: API flow 테스트와 frontend build는 Codex sandbox의 디렉터리 생성/spawn 제한 때문에 sandbox 밖 실행으로 검증했다.

### AI / Engineering Version (English)
- Fixed merged pagination for Nara `business_type=all`.
- Added response metadata: `pagination_mode`, `has_next_page`, `total_count_is_estimated`, and `partial_errors`.
- Partial all-search operation failures now return successful results with `result_code=partial_failed`; all-operation failure remains HTTP 502.
- Updated the Nara board UI to show estimated counts, hide last-page jump for merged pagination, and show partial failure warnings.
- Moved extended corporation evidence rules before generic fallback rules for real software-business and Inno-Biz filename variants.
- Restricted extended evidence subject-to-`business_item` mapping to product/technology/software/patent/copyright-like document types.
- Added cautious saved-notice business-type backfill from raw JSON only when a better type can be inferred.
- Verified with corporation evidence tests, frontend contract tests, full API flow tests, frontend build, encoding check, and whitespace check.

## 추가 업데이트 (2026-06-14) - `source/test_doc` 실제 PDF 증빙 테스트

### 한국어 기록
- `source/test_doc/` 폴더의 PDF 47개를 대상으로 실제 서비스 흐름에 가까운 `extract_document()` → `run_ocr_if_needed()` → `analyze_corporation_evidence()` 테스트를 수행했다.
- 현재 로컬 OCR 상태:
  - `OCR_ENGINE=paddle`
  - PaddleOCR 사용 가능
  - OpenDataLoader PDF reader는 `auto` 모드에서 시도 후 PyMuPDF fallback이 적용됨
- 테스트 결과:
  - PDF 47개 처리 완료
  - 파싱 예외 0건
  - PaddleOCR 실행 30건
  - OCR skip 17건
  - OCR 실패/미설정 0건
  - OCR 후 최종 텍스트 0자 0건
  - 자동 분류 45건
  - 확인 필요 2건
  - 총 소요 약 445.5초
- 발견한 분류 보강점:
  - 직접생산확인증명서가 문서 본문에 포함된 `중소기업제품 구매촉진` 문구 때문에 중소기업확인서로 오분류될 수 있었다.
  - 기업신용평가등급확인서가 본문 내 중소기업 심사 문구 때문에 중소기업확인서로 오분류될 수 있었다.
  - 옥외광고업책임보험가입증명서가 옥외광고사업 등록 문구 때문에 옥외광고사업 등록증으로 오분류될 수 있었다.
  - 출자증권이 한국전자산업협동조합 문구 때문에 조합원증으로 오분류될 수 있었다.
  - 기술등급확인서와 기술평가우수기업인증서가 별도 문서유형으로 없어서 `unknown`으로 남았다.
- 수정:
  - 직접생산확인증명서, 기업신용평가등급확인서, 책임보험가입증명서, 출자증권의 분류 우선순위를 전용 규칙 우선으로 조정했다.
  - `technology_grade_confirmation`, `technology_evaluation_excellent_certificate` 문서유형을 백엔드 라벨, 규칙 기반 분류, LLM 허용 유형, 프론트 문서유형 선택 목록에 추가했다.
  - 실제 PDF에서 확인한 오분류 케이스를 단위 테스트 fixture로 추가했다.

검증:
- `py -3.13 -m unittest tests.test_corporation_evidence -v`
- `py -3.13 -m unittest tests.test_frontend_contracts -v`
- 실제 PDF targeted 재검증:
  - `20250226_(주)벡트_직생(동영상제작).pdf` → `direct_production_confirmation`
  - `기술등급확인서(T-2)_(주)벡트_20250912.pdf` → `technology_grade_confirmation`
  - `기술평가우수기업인증서_벡트_전자칠판제조기술.pdf` → `technology_evaluation_excellent_certificate`
  - `기업신용평가등급확인서_벡트(공공기관 제출용).pdf` → `credit_rating_certificate`
  - `옥외광고업책임보험가입증명서_(주)백트.pdf` → `insurance_policy_certificate`
  - `출자증권_한국전자산업협동조합.pdf` → `investment_share_certificate`

### AI / Engineering Version (English)
- Ran real `source/test_doc` PDF evidence verification through `extract_document()` -> `run_ocr_if_needed()` -> `analyze_corporation_evidence()`.
- 47 PDFs processed, 0 parse errors, 30 PaddleOCR completions, 17 OCR skips, 0 OCR failures, and 0 zero-text outputs after OCR.
- Initial run classified 45 PDFs and left 2 as needs-review/unknown.
- Found precedence issues for direct-production, credit-rating, insurance-policy, and investment-share evidence.
- Added separated document types for technology-grade and technology-evaluation excellent certificates.
- Added regression tests based on the real PDF failure patterns.

## 추가 업데이트 (2026-06-14) - 서비스 시연 영상 생성 지원 가능성 검토 및 계획

### 한국어 기록
- `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 기준으로 실제 서비스 화면을 동영상으로 생성할 수 있는지 재검토했다.
- 현재 코드 기준으로 법인 등록/증빙 PDF 업로드, 대시보드, 나라장터 검색/저장, 공고 요구조건 확인, 기준문서/RAG 처리 상태, 부족조건 미리보기/판단 검토, 계약서 DOCX 생성, 운영 이력 확인 흐름이 모두 화면 시연 대상으로 존재함을 확인했다.
- Playwright가 이미 프론트엔드 devDependency에 포함되어 있으므로 브라우저 자동 조작과 화면 녹화는 지원 가능하다고 판단했다.
- 후처리는 `ffmpeg-static` 또는 로컬 FFmpeg를 추가해 WebM 병합, MP4 변환, 자막 삽입 방식으로 계획했다.
- 신규 계획 문서 `docs/service-demo-video-generation-plan.md`를 작성했다.
- 권장 방향은 먼저 안정 데모 데이터 모드로 반복 가능한 영상을 만들고, 이후 실시간 나라장터 API 모드를 선택 옵션으로 추가하는 것이다.

검증:
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음

### AI / Engineering Version (English)
- Reviewed the current portal against the Rocket Pitch demo flow.
- Confirmed that corporation onboarding/evidence upload, dashboard, Nara notice search/save, saved-notice requirement review, basis/RAG status, readiness comparison/judgment review, DOCX contract generation, and operations history can be demonstrated in the UI.
- Planned a Playwright-based recording workflow with FFmpeg post-processing.
- Added `docs/service-demo-video-generation-plan.md`.
- Recommended starting with deterministic demo data, then adding live Nara API mode as an optional path.

## 추가 업데이트 (2026-06-14) - Rocket Pitch 제품 시연 흐름 기반 파이프라인 동작 테스트

### 한국어 기록
- 사용자 요청에 따라 `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 실제 서비스 로직 동작 테스트로 구성했다.
- 신규 계획 문서 `docs/service-demo-pipeline-test-plan.md`를 작성했다.
- `backend/tests/test_api_flows.py`에 `test_service_rocket_pitch_demo_pipeline_flow`를 추가했다.
- 테스트가 검증하는 흐름:
  - 법인 증빙자료 업로드와 승인
  - 중소기업확인서 증빙 승인과 법인 프로필 병합
  - 대시보드 상태 확인
  - 나라장터 공고 저장/분석
  - 저장 공고 요구조건 후보와 Phase 3 입력 스키마 확인
  - 기준문서 업로드, 청킹, JSON basis index 검색
  - 공고-법인 부족조건 미리보기
  - 부족조건 중심 판단 run 생성과 citation 후보 확인
  - 계약서 DOCX 미리보기, 생성, 다운로드
  - 운영 요약과 작업 이력 확인
- 반복 테스트 중 발견한 문제:
  - 계약서 DOCX 테스트가 표 셀 텍스트를 읽지 않아 공고명을 찾지 못했다. 테스트 검증 로직을 문단+표 셀 전체로 수정했다.
  - 기준문서 최초 업로드 처리는 성공하지만 `operation_runs`에 `basis_document_processing` 이력이 남지 않았다. 운영 이력 누락 버그로 보고 업로드 API에서도 작업 이력을 기록하도록 수정했다.
  - 최종 판정 금지어 검증이 `지원 가능한 첨부` 같은 안내 문구까지 오탐했다. 실제 verdict 필드/값 중심으로 테스트를 조정했다.

검증:
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v`: 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 106개 통과
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 13개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음
- 참고: `test_api_flows` 실행 중 기존 ResourceWarning/DeprecationWarning이 출력되었지만 테스트는 모두 통과했다.

### AI / Engineering Version (English)
- Converted the Rocket Pitch product demo flow into a backend API pipeline regression test.
- Added `docs/service-demo-pipeline-test-plan.md`.
- Added `test_service_rocket_pitch_demo_pipeline_flow` to `backend/tests/test_api_flows.py`.
- The scenario validates evidence upload/approval, corporation profile enrichment, dashboard state, Nara notice save/analyze, structured requirements, basis upload/index/search, notice-corporation comparison, gap-first judgment run, DOCX contract generation/download, and operation history.
- Found and fixed one real bug: initial basis-document upload processing did not create a `basis_document_processing` operation run.
- Adjusted test assertions for DOCX table text and final-verdict false positives.
- Verified with targeted pipeline test, full API flow tests, frontend contract tests, frontend build, encoding check, and whitespace check.

## 추가 업데이트 (2026-06-14) - 제품 시연 흐름 파이프라인 테스트 재실행

### 한국어 기록
- 사용자 요청에 따라 `제품 시연 흐름` 전용 파이프라인 테스트를 재실행했다.
- 단독 재실행 결과:
  - `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow -v`: 통과
- 추가 회귀 확인:
  - `py -3.13 -m unittest tests.test_api_flows -v`: 106개 통과
  - `py -3.13 -m unittest tests.test_frontend_contracts -v`: 13개 통과
- 재확인 결과:
  - 법인 증빙 업로드/승인, 공고 저장/분석, 기준문서 업로드/RAG 검색, 부족조건 비교, 판단 run, 계약서 DOCX 생성, 운영 이력 확인 흐름이 정상 동작했다.
  - 새로 발견된 실패 또는 수정 필요한 버그는 없었다.
  - 전체 API 테스트 중 기존 `ResourceWarning`과 `DeprecationWarning`이 출력되었지만 테스트 실패로 이어지지는 않았다.

### AI / Engineering Version (English)
- Re-ran the Rocket Pitch demo pipeline regression test on request.
- Targeted pipeline test passed.
- Full API flow suite passed: 106 tests.
- Frontend contract suite passed: 13 tests.
- No new blocking issues or fix-required bugs were found.
- Existing warning output appeared during the full API suite but did not fail tests.

## 추가 업데이트 (2026-06-14) - 서비스 시연 영상 생성 계획 재검토 및 보강

### 한국어 기록
- 사용자 요청에 따라 `docs/service-demo-video-generation-plan.md`를 재검토하고 구현 착수 가능한 수준으로 보강했다.
- 보강 내용:
  - 영상 녹화 전 `test_service_rocket_pitch_demo_pipeline_flow`를 preflight로 실행하도록 명시했다.
  - 영상 생성 모드를 `stable-demo`, `real-pdf-demo`, `live-nara-demo`로 분리했다.
  - 첫 공식 영상은 반복 가능한 `stable-demo` 모드로 만드는 것을 기본값으로 정리했다.
  - 장면별 라우트, 선행 조건, 성공 신호, 실패 시 기록해야 할 산출물을 표로 추가했다.
  - Playwright selector 정책과 필요한 경우에만 `data-demo-id`를 추가하는 기준을 정리했다.
  - `create-service-demo-video.mjs`, `render-service-demo-video.mjs`, `prepare-service-demo-data.mjs`, `inspect-service-demo-video.mjs`의 역할을 구체화했다.
  - `demo-video.config.json` 예시와 CLI 옵션을 추가했다.
  - FFmpeg/FFprobe 기반 후처리와 영상 QA 기준을 추가했다.
  - 실제 PDF 모드와 실시간 나라장터 모드의 fallback/timeout 정책을 보강했다.

검증:
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음

### AI / Engineering Version (English)
- Reviewed and strengthened `docs/service-demo-video-generation-plan.md`.
- Added pipeline preflight requirements, stable/real-pdf/live-nara recording modes, scene contracts, selector policy, script architecture, CLI/config examples, FFmpeg/FFprobe QA, and fallback policies.
- The plan now starts implementation with deterministic `stable-demo` recording, then extends to real PDFs and live Nara API.

## 추가 업데이트 (2026-06-14) - 서비스 시연 영상 생성 도구 구현 및 MP4 생성

### 한국어 기록
- `docs/service-demo-video-implementation-plan.md`를 추가해 실제 구현 범위, 실행 명령, 산출물 위치, 검증 절차를 문서화했다.
- `stable-demo` 영상 생성 도구를 구현했다.
  - `scripts/demo-video-utils.mjs`
  - `scripts/prepare-service-demo-data.mjs`
  - `scripts/create-service-demo-video.mjs`
  - `scripts/render-service-demo-video.mjs`
  - `scripts/inspect-service-demo-video.mjs`
  - `scripts/create-demo-video.ps1`
  - `scripts/demo-video.config.json`
- `frontend/package.json`에 데모 영상 명령을 추가했다.
  - `demo:browser-install`
  - `demo:preflight`
  - `demo:prepare`
  - `demo:record`
  - `demo:render`
  - `demo:inspect`
- 영상 생성 방식:
  - 백엔드 API로 시연 법인, 증빙 샘플, 저장 공고, 기준문서, 부족조건 비교, 판단 run, 계약서 초안을 생성한다.
  - Playwright Chromium으로 Rocket Pitch 시연 흐름의 11개 장면을 이동하며 WebM을 녹화한다.
  - `ffmpeg-static`으로 MP4 변환 후 `ffprobe-static`으로 검사한다.
- 구현 중 발견하고 수정한 문제:
  - Playwright가 SPA 라우트에서 `DOMContentLoaded`를 기다리면 `/corporations` 화면에서 녹화가 멈출 수 있었다. 라우트 이동을 `waitUntil: "commit"`으로 바꾸고 장면별 고정 대기/검사 방식으로 안정화했다.
  - 오버레이 삽입 시 함수형 `expect` 필드를 함께 직렬화하려 해 실패했다. 오버레이에는 제목과 부제만 넘기도록 수정했다.
  - Windows에서 `npm.cmd` spawn 방식이 `EINVAL`을 냈다. `cmd.exe /d /s /c npm ...` 방식으로 수정했다.
  - 나라장터 검색 요청이 라우트 이동 중 정상 abort되는 경우를 실패 요청에서 제외했다.
  - 작업 이력 화면의 기대 텍스트를 내부 코드명 `basis_document_processing`이 아니라 실제 UI 라벨 `기준문서 처리`로 보정했다.
- 생성된 최종 영상:
  - `artifacts/demo-video/service-demo-20260614104248.mp4`
  - 길이: 35.04초
  - 해상도: 1440x900
  - 코덱: H.264

검증:
- `cd frontend; npm run demo:browser-install`: 통과
- `cd frontend; npm run demo:preflight`: 통과
- `powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start`: 백엔드/프론트 준비 완료
- `cd frontend; npm run demo:record -- --skip-preflight --reuse-data --dry-run --scene intro,corporations`: 통과
- `cd frontend; npm run demo:record -- --skip-preflight`: WebM 생성 완료
- `cd frontend; npm run demo:record -- --skip-preflight --reuse-data`: 경고 없이 최종 WebM 재생성 완료
- `cd frontend; npm run demo:render`: MP4 변환 완료
- `cd frontend; npm run demo:inspect`: `status=passed`
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음. 기존 작업 파일들의 CRLF 변환 경고만 출력됨.

### AI / Engineering Version (English)
- Added an executable stable demo video toolchain.
- Added `docs/service-demo-video-implementation-plan.md`.
- Added demo scripts for data seeding, Playwright recording, FFmpeg rendering, FFprobe inspection, shared utilities, config, and a Windows wrapper.
- Added npm scripts for browser install, preflight, preparation, recording, rendering, and inspection.
- Generated `artifacts/demo-video/service-demo-20260614104248.mp4`.
- Fixed implementation issues found during execution:
  - changed SPA navigation wait from `domcontentloaded` to `commit`
  - avoided serializing function fields into the browser overlay
  - fixed Windows npm process spawning through `cmd.exe /d /s /c`
  - ignored expected `ERR_ABORTED` route-transition requests
  - aligned operation history scene expectations with the visible Korean label
- Verified preflight, dry-run, full recording, MP4 rendering, MP4 inspection, encoding check, and whitespace check.

## 추가 업데이트 (2026-06-14) - Vite ngrok allowed host 차단 수정

### 한국어 기록
- 사용자 제보 오류:
  - `Blocked request. This host ("8ed6-118-216-124-59.ngrok-free.app") is not allowed.`
- 원인:
  - 브라우저가 ngrok 프론트 URL로 접속하면 Vite dev server에는 `Host: <ngrok>.ngrok-free.app` 요청이 들어온다.
  - Vite의 host header 보호 기능이 해당 host를 허용 목록에서 찾지 못해 요청을 차단했다.
  - 기존 설정은 `VITE_ALLOW_NGROK_HOSTS=1` 환경변수에 의존했기 때문에 실행 방식이 조금만 달라도 ngrok host가 막힐 수 있었다.
- 수정:
  - `frontend/vite.config.ts`에서 기본 `allowedHosts`에 `localhost`, `127.0.0.1`, `.ngrok-free.app`를 포함했다.
  - `VITE_ALLOW_NGROK_HOSTS=1`이면 기존처럼 `allowedHosts=true`를 유지한다.
  - `backend/tests/test_frontend_contracts.py`에 Vite ngrok host 허용 정적 테스트를 추가했다.
- 주의:
  - Vite 설정은 dev server 시작 시 읽히므로, 이미 떠 있는 프론트 서버는 재시작해야 반영된다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 14개 통과
- `npm run build`: 통과
- `powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start`: 통과
- 프론트 ngrok URL `https://8ed6-118-216-124-59.ngrok-free.app/`: Vite HTML 정상 반환, `Blocked request` 미발생
- 백엔드 ngrok URL `https://0354-118-216-124-59.ngrok-free.app/health`: `{"status":"ok"}` 반환

### AI / Engineering Version (English)
- Fixed Vite dev server host blocking for ngrok frontend URLs.
- Root cause: Vite rejected `Host: <subdomain>.ngrok-free.app` unless `VITE_ALLOW_NGROK_HOSTS=1` had been applied to the running frontend process.
- Updated `frontend/vite.config.ts` to allow `localhost`, `127.0.0.1`, and `.ngrok-free.app` by default.
- Kept `VITE_ALLOW_NGROK_HOSTS=1` as a broader opt-in fallback.
- Added a frontend contract test to guard the Vite ngrok allowed-host configuration.
- Note: the running Vite dev server must be restarted because Vite reads this config at startup.
- Restarted ngrok/local services and verified the frontend public URL returns the Vite HTML instead of the blocked-host page.

## 추가 업데이트 (2026-06-14) - Rocket Pitch 제품 시연 흐름 영상 생성용 시나리오 보강

### 한국어 기록
- 사용자 요청에 따라 `docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 시연 영상 생성 기준으로 상세 보강했다.
- 보강 내용:
  - 시연 목표를 `법인 준비 -> 공고 확보 -> 기준문서 준비 -> 부족조건 확인 -> 계약서 초안 -> 운영 이력 확인` 흐름으로 명확화
  - `stable-demo`, `real-pdf-demo`, `live-nara-demo` 영상 모드 구분
  - 11개 장면의 Playwright scene id, 화면 경로, 권장 길이, 핵심 메시지, 성공 신호 표 추가
  - 장면별 화면에서 보여줄 것, 발표 멘트, 강조 포인트, Playwright 자동화 메모 추가
  - Playwright 코드 작성이 필요한 경우와 필요 없는 경우를 정리
  - 영상 생성 전 체크리스트 추가
  - English engineering 섹션의 `Demo Flow`를 `Demo Video Flow Contract`로 확장
- Playwright 관련 결론:
  - 현재 `stable-demo` 기본 영상은 이미 구현된 `scripts/create-service-demo-video.mjs`와 `scripts/prepare-service-demo-data.mjs`로 생성 가능하므로 매번 새 Playwright 코드를 작성할 필요는 없다.
  - 실제 클릭/파일 업로드/긴 OCR polling/실시간 나라장터 검색을 영상에 넣을 때는 Playwright scene 코드와 안정적인 `data-demo-id` selector 보강이 필요하다.

### AI / Engineering Version (English)
- Expanded `docs/service-rocket-pitch.md` section `3. 제품 시연 흐름` into a demo-video-ready scenario contract.
- Added scene IDs, routes, recommended duration, key message, success signal, presenter script, and Playwright automation notes.
- Clarified stable-demo vs real-pdf-demo vs live-nara-demo.
- Added a Playwright guidance section:
  - no new Playwright code is needed for the basic stable demo
  - new Playwright code is needed for real clicks, file uploads, OCR polling, live Nara API search, or fragile selectors
- Updated the English engineering section from a simple demo list to a `Demo Video Flow Contract`.

## 추가 업데이트 (2026-06-14) - 인터랙티브 시연 영상 구현계획 MD 작성

### 한국어 기록
- 사용자 요청에 따라 실제 버튼 클릭, 파일 업로드, `source/test_doc/` PDF OCR 처리, 실시간 나라장터 API 검색 장면을 시연 영상에 넣기 위한 별도 구현계획서를 작성했다.
- 신규 문서:
  - `docs/service-demo-interactive-video-implementation-plan.md`
- 계획서에 포함한 내용:
  - `stable-demo`, `interactive-demo`, `real-pdf-demo`, `live-nara-demo` 모드 구분
  - Playwright 마우스 포인터 오버레이와 실제 클릭/입력/업로드 헬퍼 설계
  - 화면 문구 변경에도 안정적인 `data-demo-id` selector 계약
  - 법인 등록, 증빙 PDF 업로드, 나라장터 검색, 저장 공고, 기준문서/RAG, 부족조건, 계약서, 운영 화면의 데모 selector 후보
  - 실제 PDF OCR 처리와 실시간 나라장터 API 검색을 영상에 넣을 때의 실행 조건, fallback, 위험요소
  - 구현 순서, 테스트 계획, 완료 기준, 제품 담당자 확인 질문

검증
- `py -3.13 scripts\check-encoding.py`: 통과

### AI / Engineering Version (English)
- Added `docs/service-demo-interactive-video-implementation-plan.md`.
- The plan covers interactive Playwright recording, visible cursor movement, real button clicks, file uploads, real `source/test_doc/` PDF OCR scenes, live Nara API search scenes, and stable `data-demo-id` selectors.
- The implementation is intentionally separated into demo modes so the existing stable API-seeded video remains available while interactive/live variants can be enabled when needed.

## 추가 업데이트 (2026-06-14) - 인터랙티브 시연 영상 기반 구현

### 한국어 기록
- `docs/service-demo-interactive-video-implementation-plan.md`를 재검토했고, 이번 구현 범위를 명확히 보강했다.
  - 즉시 구현: selector 계약, 인터랙티브 모드, 마우스 포인터/ripple, 대표 PDF 업로드 dry-run, live 나라장터 dry-run 경로
  - 분리 항목: 모든 PDF 전수 OCR 영상화, 실시간 API 실패를 fatal로 처리하는 방식, 계약서 다운로드 파일 직접 열기 장면
- 프론트엔드 주요 화면에 `data-demo-id` selector를 추가했다.
  - 사이드바 메뉴
  - 법인/증빙 업로드, 검토, 목록
  - 나라장터 검색, 결과 row, 저장/분석, partial error
  - 저장 공고 목록/상세, 첨부 상태, 요구조건
  - 기준문서 업로드, OCR 강제 실행, 재처리, 처리 상태, 청크 보기/더보기
  - 부족조건 비교, 판단 run, 계약서 생성/미리보기, 운영 대시보드, 작업 이력
- `scripts/create-service-demo-video.mjs`를 보강했다.
  - `interactive-demo`, `real-pdf-demo`, `live-nara-demo` 모드 지원
  - 데모용 마우스 포인터 DOM overlay와 클릭 ripple 추가
  - `clickWithCursor`, `typeWithCursor`, `setInputFilesWithCursor`, `navigateBySidebar` helper 추가
  - `source/test_doc/` 대표 PDF를 잡아 업로드 장면을 구성하는 dry-run 경로 추가
  - 실시간 나라장터 검색 dry-run 경로와 fallback warning 기록 추가
- `backend/tests/test_frontend_contracts.py`에 selector/영상 모드 계약 테스트를 추가했다.

검증
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 15개 통과
- `node --check scripts\create-service-demo-video.mjs`: 통과
- `npm run build`: 통과
- `npm run demo:record -- --mode interactive-demo --skip-preflight --reuse-data --dry-run --scene intro,corporations`: 통과, warning 0
- `npm run demo:record -- --mode interactive-demo --skip-preflight --reuse-data --dry-run --scene basis-documents,contracts,operation-runs`: 통과, warning 0
- `npm run demo:record -- --mode real-pdf-demo --skip-preflight --reuse-data --dry-run --scene corporations`: 통과, dry-run 제출 생략 warning 1
- `npm run demo:record -- --mode live-nara-demo --skip-preflight --reuse-data --dry-run --scene nara-board`: 통과, live 검색 생략 warning 1
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음. 기존 작업 파일들의 LF/CRLF 변환 경고만 출력됨.

### AI / Engineering Version (English)
- Reviewed and tightened `docs/service-demo-interactive-video-implementation-plan.md` with an explicit implementation slice.
- Added stable `data-demo-id` selectors across the frontend demo flow.
- Extended `scripts/create-service-demo-video.mjs` with interactive recording modes, a visible cursor overlay, click ripple, sidebar navigation, file upload helper, real PDF dry-run support, and live Nara dry-run support.
- Added frontend contract coverage for demo selectors and demo video modes.
- Verified frontend contract tests, script syntax, Vite build, interactive dry-runs, encoding, and whitespace checks.

## 추가 업데이트 (2026-06-14) - 인터랙티브 시연 영상 MP4 생성

### 한국어 기록
- 사용자 요청에 따라 `scripts/create-service-demo-video.mjs` 기반으로 실제 시연 영상을 생성했다.
- 실행 모드:
  - `interactive-demo`
- 생성 seed:
  - `20260614111559`
- 생성 산출물:
  - WebM 원본: `artifacts/demo-video/runs/20260614111559/raw-video/service-demo-20260614111559.webm`
  - MP4 최종본: `artifacts/demo-video/service-demo-20260614111559.mp4`
  - 녹화 리포트: `artifacts/demo-video/runs/20260614111559/record-report.json`
  - 렌더 리포트: `artifacts/demo-video/latest-render.json`
  - 검사 리포트: `artifacts/demo-video/latest-inspection.json`
- 영상 속성:
  - 길이: 58초
  - 해상도: 1440x900
  - 코덱: H.264
  - 파일 크기: 약 3.1 MB
- 실제 스크린샷으로 확인한 내용:
  - 영상 오버레이 한글은 정상 표시됨
  - 마우스 포인터 overlay와 클릭 위치 표시가 포함됨
  - PowerShell의 JSON 출력 일부만 한글이 깨져 보였고 파일/영상 자체 인코딩 문제는 아님

검증
- FE 서버 `http://127.0.0.1:5199/`: 200 응답
- BE 서버 `http://127.0.0.1:18111/api/dashboard/summary`: 200 응답
- `npm run demo:record -- --mode interactive-demo --skip-preflight`: 완료, warning 0
- `npm run demo:render`: 완료
- `npm run demo:inspect`: `status=passed`, duration 58초, 1440x900, h264, errors 없음

### AI / Engineering Version (English)
- Generated the interactive demo video from `scripts/create-service-demo-video.mjs`.
- Mode: `interactive-demo`.
- Seed: `20260614111559`.
- Final MP4: `artifacts/demo-video/service-demo-20260614111559.mp4`.
- Inspection passed with 58 seconds duration, 1440x900 resolution, H.264 codec, and no errors.
- Screenshot inspection confirmed the Korean overlay text renders correctly; only PowerShell JSON console output showed mojibake.

## 추가 업데이트 (2026-06-14) - 법인 증빙 검토 UX 및 법인 준비도 이동 버그 수정

### 한국어 기록
- 증빙자료 관리 테이블의 `처리` 컬럼이 `review_status=pending`을 그대로 `검토 대기`로 보여주던 문제를 확인했습니다.
  - 원인은 백엔드가 후보 수(`pending_candidate_count`, `approved_candidate_count`)를 이미 내려주고 있었지만, 프론트가 후보 수를 반영하지 않고 원본 검토 상태만 표시한 데 있었습니다.
  - 승인 대기 후보가 0개인 문서도 `검토 대기`처럼 보여 사용자가 승인 가능한 값이 있다고 오해할 수 있었습니다.
- 자동 추출 후보 확인 화면에서 승인 대기 후보가 없을 때 `전체 선택`, `선택 해제`, `0개 선택 반영` 버튼이 비활성화된 채 보이던 UX를 수정했습니다.
  - 승인 대기 후보가 있을 때만 선택 버튼을 보여줍니다.
  - 후보가 아예 없으면 `승인할 자동 추출 후보가 없습니다.` 안내를 보여줍니다.
  - 이미 승인/제외된 후보만 있으면 `승인 대기 후보가 없습니다.` 안내를 보여줍니다.
  - 선택 버튼 문구를 `승인 대기 후보 전체 선택`, `후보 선택 해제`, `선택한 후보 반영`으로 명확히 변경했습니다.
- 법인 목록/준비도 화면의 준비도 카드를 클릭 가능하게 변경했습니다.
  - 준비도 카드를 클릭하면 해당 법인의 `법인 정보 편집` 폼을 열고 자동 스크롤합니다.
  - 등록된 법인 목록의 `편집` 버튼도 같은 편집 폼으로 자동 이동합니다.
- 프론트 계약 테스트를 추가했습니다.
  - 후보 없음/승인 대기 없음 안내 문구와 후보 수 기반 처리 상태 계산을 검증합니다.
  - 준비도 카드 클릭, 편집 폼 스크롤, 관련 CSS 클래스를 검증합니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 17개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨
- 브라우저 DOM 확인: `/judgment-runs`, `/notice-comparison` 모두 공고/법인 기본값 미선택, 실행 버튼 비활성화, `계약서 초안 생성` 버튼 제거 확인
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Fixed corporation evidence review UX where raw `review_status=pending` was shown as if there were candidates ready for approval.
- Added candidate-count-aware evidence review labels:
  - pending candidates -> approval pending count
  - no candidates -> no candidate state
  - approved candidates -> approved state
  - failed extraction/OCR -> failed state
- Hid bulk-selection actions when no pending candidates exist and added explicit empty-state messages for no candidates or no pending candidates.
- Made corporation readiness cards clickable and routed both readiness-card clicks and directory edit actions to the inline edit form via smooth scroll.
- Added frontend contract coverage for the evidence review empty state and corporation readiness card edit navigation.

## 추가 업데이트 (2026-06-14) - 법인 프로필 준비도 카드 레이아웃 수정

### 한국어 기록
- 사용자 스크린샷 기준으로 `법인 프로필 준비도` 카드 사이에 작은 `?` 도움말 버튼이 끼어들어 grid 칸을 차지하는 문제를 확인했습니다.
- 원인은 준비도 카드를 클릭 가능하게 만들면서 `<button>`으로 렌더링했고, 전역 액션 도움말 데코레이터가 이 큰 카드 버튼을 일반 액션 버튼으로 판단해 자동 `?` 버튼을 삽입한 것이었습니다.
- 수정 내용:
  - 준비도 카드 버튼에 `data-help-ignore="true"`를 추가해 자동 도움말 데코레이터 대상에서 제외했습니다.
  - `.readiness-grid`에 `align-items: stretch`를 추가했습니다.
  - `.readiness-card`에 `min-height: 212px`를 추가해 카드 높이 흔들림을 줄였습니다.
  - 프론트 계약 테스트에 자동 도움말 제외와 카드 sizing 계약을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 17개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Fixed readiness card layout regression caused by the global action-help decorator inserting `?` buttons after clickable readiness card buttons.
- Added `data-help-ignore="true"` to readiness cards so they remain clickable without becoming decorated action buttons.
- Added stable card sizing through stretched grid alignment and a minimum card height.
- Added frontend contract coverage for the decorator opt-out and readiness card sizing rules.

## 추가 업데이트 (2026-06-14) - nav 메뉴 순서와 법인 증빙 다중 업로드 UX 수정

### 한국어 기록
- 사용자 요청에 따라 왼쪽 nav 메뉴 그룹 순서를 조정했습니다.
  - 변경 후 순서: `업무 현황` -> `내부 관리` -> `공고 업무` -> `기준문서 / RAG` -> `문서 분석` -> `설정`
  - `내부 관리`는 `업무 현황` 바로 아래로 이동했습니다.
  - `문서 분석`은 `설정` 바로 위로 이동했습니다.
- 법인 관리의 `증빙 업로드` 화면이 사업자등록증 전용처럼 보이던 문제를 수정했습니다.
  - 제목을 `법인 증빙자료 업로드`로 변경했습니다.
  - 사업자등록증명, 사업자등록증, 인증서, 면허, 확인서, 특허/저작권 문서 등 법인이 보유한 증빙자료를 같은 화면에서 업로드한다고 명시했습니다.
  - 파일 input에 `multiple`을 추가해 여러 파일을 한 번에 선택할 수 있게 했습니다.
  - 선택된 파일 목록과 개수를 화면에 표시합니다.
  - 여러 파일 선택 시 기존 단일 업로드 API를 파일별로 순차 호출하고, 완료 후 `증빙자료 관리` 탭으로 이동해 문서별 검토를 진행하도록 했습니다.
  - 단일 파일 업로드는 기존처럼 바로 `추출값 검토` 탭으로 이동합니다.
- 법인 관리 도움말도 여러 증빙자료 업로드 흐름에 맞춰 수정했습니다.
- 프론트 계약 테스트에 nav 그룹 순서와 다중 증빙 업로드 계약을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 17개 통과
- `npm run build`: 통과

### AI / Engineering Version (English)
- Reordered sidebar nav groups to: overview, admin, notice, RAG, document, settings.
- Clarified that corporation evidence upload is not limited to business registration documents.
- Added multi-file selection to the corporation evidence upload input.
- Implemented sequential uploads through the existing single-file backend API, routing batch uploads to the evidence library for per-document review.
- Added selected-file count/list UI and updated corporation help copy.
- Added frontend contract coverage for nav order and multi-file evidence upload behavior.

## 추가 업데이트 (2026-06-14) - 포탈 화면 설명 문구 전수 정리

### 한국어 기록
- 사용자 피드백에 따라 포탈 내부의 개발 단계명, UX 변경 이유, 내부 설명성 문구를 전수 검색하고 정리했습니다.
- 제거/교체한 대표 문구:
  - `Phase 1.6A/B`, `Phase 2 처리 현황`, `Phase 3 Review`, `Phase 4A`, `Phase 4B / 4C`, `Phase 4D`
  - `Project First`, `프로젝트 기준 UX로 바꾼 이유`
  - `업로드 화면에서 바꾼 점`, `업로드 자체보다 ... UX를 정리했습니다`
  - `Why It Matters`, `Manual Fallback`, `Evidence First`, `Profile Readiness`
- 화면 문구는 다음 기준으로 재정리했습니다.
  - 개발 단계명 대신 메뉴/기능명을 표시합니다.
  - “왜 바꿨는지” 대신 사용자가 지금 관리하는 항목을 표시합니다.
  - 영어 eyebrow 라벨은 한국어 기능 라벨로 통일합니다.
  - 설명 문장은 실제 동작, 입력값, 결과물 중심으로 짧게 정리합니다.
- 정리한 주요 화면:
  - 대시보드
  - 프로젝트 관리
  - 문서 업로드/문서 이력
  - 법인 관리/증빙 업로드/법인 준비도
  - 기준문서 관리/규칙 후보/검색 평가
  - 나라장터 검색/저장 공고/자동 수집
  - 부족조건 미리보기/판단 검토
  - 계약서 생성
  - 운영 대시보드/작업 이력/백업/복원
  - 설정/외부 접속/도움말/처리 오버레이
- 프론트 계약 테스트에 금지 문구 회귀 검사를 추가했습니다.
  - `frontend/src/**/*.tsx` 전체에서 `Phase`, `Project First`, `Why It Matters`, `Manual Fallback`, `Evidence First`, `Profile Readiness`, `Usability Upgrade`, `바꾼 이유`, `바꾼 점`, `UX로`, `UX를` 등이 다시 노출되면 실패합니다.

검증:
- `rg` 금지 문구 검색: 결과 없음
- eyebrow 라벨 전수 출력: 한국어 기능 라벨로 정리됨
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 18개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Audited frontend portal copy and removed internal phase labels, UX-rationale copy, and developer-facing eyebrow labels from user-visible TSX screens.
- Replaced phase/rationale copy with concise menu/function labels and action-oriented descriptions.
- Converted section eyebrow labels across portal screens to Korean functional labels.
- Added frontend contract coverage that scans `frontend/src/**/*.tsx` and fails if internal phase or UX-rationale phrases reappear.

## 추가 업데이트 (2026-06-14) - 액션 버튼 도움말 간격 전수 수정

### 한국어 기록
- 버튼 옆에 자동으로 붙는 `?` 도움말 버튼이 일부 화면에서 비정상적으로 멀리 떨어지는 문제를 확인했습니다.
- 원인은 `ActionHelpProvider`가 버튼 바로 뒤에 `action-help-trigger`를 형제 요소로 삽입하는데, 일부 액션 컨테이너가 `justify-content: space-between`을 사용해 원래 버튼과 `?` 버튼을 양끝으로 밀어낸 것이었습니다.
- 전수 확인 결과, 실제로 동일 문제가 반복될 수 있는 액션 컨테이너는 `section-heading`, `analysis-hero`, `sticky-action-bar`, `toolbar`, `form-actions`, `row` 계열이었습니다.
- `analysis-hero`와 `sticky-action-bar`를 `justify-content: flex-start` 기반으로 정리하고, 첫 번째 설명 영역만 남는 공간을 차지하도록 `margin-right: auto`를 적용했습니다.
- `analysis-hero`와 `sticky-action-bar`의 직접 자식 `action-help-trigger`에도 작은 음수 margin을 적용해 원래 액션 버튼 바로 옆에 붙도록 수정했습니다.
- 카드 헤더, 상태 행, 리스트 행처럼 `space-between`이 필요한 단순 정보 정렬 영역은 버튼 도움말 문제와 무관하므로 레이아웃을 유지했습니다.
- 전수 재발 방지를 위해 프론트 계약 테스트에 `analysis-hero`, `sticky-action-bar`가 `space-between`으로 돌아가지 않고 `column-gap: 6px`를 유지하는지 검증을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 18개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨
- 브라우저 실제 렌더링 검증: `/notice-comparison`, `/analysis`, `/judgment-runs`, `/settings`, `/settings/external-access`, `/nara` 대표 라우트에서 자동 도움말 버튼 간격을 확인했고, 감지된 버튼-도움말 조합의 최대 간격은 4px였습니다.

### AI / Engineering Version (English)
- Fixed action help `?` buttons drifting away from their target buttons in flex action containers.
- Root cause: auto-inserted `.action-help-trigger` siblings were distributed by `justify-content: space-between` in `analysis-hero` and `sticky-action-bar`.
- Updated action containers so text/summary content takes the available space while action buttons and help triggers stay adjacent.
- Kept informational `space-between` rows unchanged because they are not action-help target containers.
- Added frontend contract assertions to prevent `analysis-hero` and `sticky-action-bar` from regressing to spaced-apart button/help layouts.
- Verified rendered routes in the browser; detected button/help pairs stayed within a 4px gap.

## 추가 업데이트 (2026-06-14) - 판단 검토 UX 전면 개선 제안서 작성

### 한국어 기록
- 사용자 피드백에 따라 서비스 핵심 기능인 `판단 검토` 화면의 UX 문제를 분석했습니다.
- 확인한 주요 문제:
  - 실행 이력 클릭 시 선택 피드백과 상세 영역 이동이 약해 아무 반응이 없는 것처럼 보입니다.
  - `citation candidate_found`, `weak_candidate`, `review_ready` 같은 내부 상태값이 사용자 화면에 노출될 수 있습니다.
  - 부족조건, 필요 서류, 기준문서 근거, 다음 행동이 한눈에 연결되지 않습니다.
  - Gemini API를 활용해 사용자용 요약과 준비 액션을 정리하는 흐름이 판단 검토 화면에 부족합니다.
- `docs/judgment-review-ux-improvement-proposal.md`를 작성했습니다.
  - 한국어 제안서를 먼저 작성했습니다.
  - 뒤에 `AI / Engineering Version (English)` 섹션을 추가했습니다.
  - 화면 구조, 문구 사전, Gemini 활용 방식, 구현 단계, 테스트 기준, 완료 기준을 포함했습니다.

검증:
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Analyzed the core `JudgmentRunsPage` UX based on user feedback.
- Wrote `docs/judgment-review-ux-improvement-proposal.md`.
- The proposal covers user-facing label mapping, run-history interaction, summary-first layout, priority action grouping, citation evidence presentation, Gemini-generated user summaries, fallback behavior, implementation steps, test plan, and acceptance criteria.

## 추가 업데이트 (2026-06-14) - 부족조건 미리보기 / 판단 검토 모달 UX와 Gemini 요약 구현

### 한국어 기록
- 사용자 요청 계획에 따라 `부족조건 미리보기`와 `판단 검토` 화면을 요약 중심 UX로 재구성했습니다.
- 메인 페이지에는 공고/법인 선택, 실행 버튼, 판단 요약, 우선 준비 항목만 남기고 최근 이력, 상세 결과, 요구조건, 법인 프로필, 근거 원문은 모달에서 확인하도록 분리했습니다.
- 백엔드 비교/판단 결과에 `user_summary`를 추가했습니다.
  - Gemini 설정이 있으면 기존 엔진 결과를 사람이 이해하기 쉬운 문장으로 재정리합니다.
  - Gemini가 없거나 실패하면 deterministic fallback 요약을 저장해 화면이 항상 동작하게 했습니다.
  - Gemini는 새로운 판단을 만들지 않고 기존 결과의 `부족 사유`, `다음 행동`, `필요 서류`, `근거 링크`만 풀어쓰도록 제한했습니다.
- 근거 링크 확인을 위해 새 API를 추가했습니다.
  - `GET /api/basis-documents/{basis_document_id}/chunks/{chunk_id}`
  - `GET /api/notice-requirements/{requirement_candidate_id}`
  - 법인 증빙서류는 기존 `GET /api/corporation-evidence-documents/{id}`를 재사용합니다.
- 프론트엔드에는 다음 모달 selector를 추가했습니다.
  - `demo-comparison-history-modal`
  - `demo-comparison-detail-modal`
  - `demo-comparison-evidence-modal`
  - `demo-judgment-history-modal`
  - `demo-judgment-detail-modal`
  - `demo-judgment-evidence-modal`
- 오래된 실행 결과처럼 `user_summary`가 비어 있는 경우에도 화면에서 기존 결과를 분석해 fallback 요약과 근거 링크를 보여주도록 보강했습니다.
- 이력 행을 클릭하면 목록 응답만 보여주는 것이 아니라 상세 API를 다시 조회해 요구조건/근거/증빙 링크까지 모달에 표시하도록 수정했습니다.
- 사용자 화면에 보이는 `citation`, `candidate_found`, `weak_candidate`, `review_ready` 계열 문구를 `근거`, `검토 가능한 근거`, `사람 확인 필요`처럼 이해 가능한 라벨로 정리했습니다.
- `docs/judgment-review-ux-improvement-proposal.md`에 이번 구현 범위, Gemini/fallback 정책, 근거 링크 정책, 모달별 정보 범위를 최신화했습니다.

검증:
- `py -3.13 -m unittest tests.test_api_flows -v`: 107개 통과
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 19개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨
- 브라우저 UX 검증: `/notice-comparison`에서 비교 이력 모달, 상세 모달, 공고 요구조건 근거 모달을 확인했습니다.
- 브라우저 UX 검증: `/judgment-runs`에서 판단 이력 모달, 상세 모달, 기준문서 근거 모달을 확인했습니다.

### AI / Engineering Version (English)
- Implemented the modal-first summary UX for `NoticeComparisonPage` and `JudgmentRunsPage`.
- Added `user_summary` generation to comparison and judgment results.
  - Uses Gemini through the existing AI JSON generation path when configured.
  - Falls back to deterministic summaries when Gemini is unavailable or fails.
  - Restricts summaries to rewriting existing engine output, not creating new judgment facts.
- Added evidence detail APIs for basis chunks and notice requirement candidates.
- Reused corporation evidence document detail API for evidence modals.
- Added frontend modal selectors for demo/video automation and regression tests.
- Hardened older result handling by deriving fallback summaries and evidence links when saved `user_summary` data is empty.
- Updated frontend contract tests to assert modal UX, evidence link labels, and removal of raw engine status labels from user-facing pages.

## 추가 업데이트 (2026-06-14) - 왼쪽 네비게이션 설정 그룹 재배치

### 한국어 기록
- 사용자 요청에 따라 왼쪽 네비게이션 메뉴의 운영/관리성 항목을 `설정` 그룹으로 이동했습니다.
- 이동한 메뉴:
  - `운영 대시보드`: `업무 현황` 그룹에서 `설정` 그룹으로 이동
  - `백업/복원`: `업무 현황` 그룹에서 `설정` 그룹으로 이동
  - `자동 수집 관리`: `공고 업무` 그룹에서 `설정` 그룹으로 이동
- 라우트와 페이지 구현은 변경하지 않고, 사이드바 노출 그룹만 재배치했습니다.
- 프론트 계약 테스트에 세 메뉴가 `설정` 그룹에만 포함되고 기존 그룹에는 남지 않는지 검증을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 19개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Moved operational/admin-oriented sidebar entries into the `settings` navigation group without changing routes.
- Moved `/operations`, `/backups`, and `/nara-collection-runs` under `설정`.
- Added a frontend contract assertion to ensure those labels stay in the settings group and are no longer rendered under overview or notice groups.

## 추가 업데이트 (2026-06-14) - 기준문서 규칙 후보 관리 UX 및 긴 원문 렌더링 보강

### 한국어 기록
- 사용자 피드백에 따라 `기준문서 규칙 후보 관리` 화면의 목적과 사용 흐름을 화면 안에서 이해하기 쉽게 정리했습니다.
- 이 화면의 역할은 기준문서에서 자동 추출된 조건 후보를 사람이 검토하고, 승인된 후보만 판단 검토의 우선 근거 규칙으로 사용하게 만드는 것입니다.
- 화면 상단에 3단계 사용 흐름을 추가했습니다.
  - 후보 추출
  - 문구 검토
  - 근거 확인 후 승인
- 긴 기준문서 PDF에서 추출된 후보가 많을 때 브라우저가 멈추는 문제를 보강했습니다.
  - 후보 목록은 조건 문구를 180자 미리보기로 축약합니다.
  - 상세 하단 기준문서 원문은 360자 미리보기만 기본 표시합니다.
  - 전체 원문은 `원문 보기` 모달에서만 확인합니다.
  - 모달에서도 기본은 약 4,200자 미리보기이며, 사용자가 `전체 원문 표시`를 누른 경우에만 전체 텍스트를 표시합니다.
- `basis-rule-candidates` 목록 API에 선택적 `limit/offset`을 추가했습니다.
  - 기존 호환을 위해 limit이 없으면 전체 반환 동작을 유지합니다.
  - 프론트 화면은 기본 `limit=200`으로 호출해 9,908건 같은 대량 후보를 한 번에 렌더링하지 않습니다.
  - 응답에 `candidate_count`, `returned_count`, `limit`, `offset`을 내려 화면에서 전체 개수와 표시 개수를 구분합니다.
- 브라우저에서 실제 현재 데이터 기준 `전체 9,908건 중 200건 표시`, 원문 기본 모달 미오픈, 원문 미리보기 높이 제한을 확인했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 20개 통과
- `py -3.13 -m unittest tests.test_api_flows.ApiFlowTests.test_phase25a_basis_rule_candidate_extraction_keeps_review_status -v`: 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 107개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨
- 브라우저 UX 확인: `/basis-rule-candidates`에서 사용 흐름 카드 3개, 목록 200건 제한, 원문 모달, 원문 영역 높이 제한 확인

### AI / Engineering Version (English)
- Improved `BasisRuleCandidatesPage` with a clearer workflow explanation and safer long-text rendering.
- Added a three-step guide: extract candidates, review wording, verify evidence and approve.
- Collapsed long candidate text by default in list and detail views.
- Moved full source/chunk text into an on-demand modal with an additional preview-first guard.
- Added optional `limit/offset` support to `/api/basis-rule-candidates`.
- The frontend now requests `limit=200` to avoid rendering thousands of candidates and large text blobs at once.
- Added backend and frontend contract coverage for limited candidate lists and collapsed long sources.

## 추가 업데이트 (2026-06-14) - FE/BE 서버 재실행 및 ngrok 주소 확인

### 한국어 기록
- 사용자 요청에 따라 로컬 FE/BE 서버를 재실행했습니다.
- 백엔드는 `http://127.0.0.1:18111`에서 정상 응답을 확인했습니다.
- 프론트엔드는 `http://127.0.0.1:5199`에서 정상 응답을 확인했습니다.
- ngrok 프로세스는 재시작하지 않았습니다.
- 현재 확인된 외부 접속 주소:
  - 프론트엔드: `https://8ed6-118-216-124-59.ngrok-free.app`
  - 백엔드 API: `https://0354-118-216-124-59.ngrok-free.app`
- 외부 프론트엔드가 백엔드 API를 로컬 주소가 아니라 `https://0354-118-216-124-59.ngrok-free.app`로 바라보도록 FE dev server를 재기동했습니다.

검증:
- `http://127.0.0.1:18111/health`: 200
- `http://127.0.0.1:5199`: 200
- `https://8ed6-118-216-124-59.ngrok-free.app`: 200
- `https://0354-118-216-124-59.ngrok-free.app/health`: 200
- 외부 프론트엔드의 `/src/app/api.ts` 응답에 백엔드 public URL 포함, 로컬 API URL 미포함 확인

### AI / Engineering Version (English)
- Restarted the local backend and frontend servers.
- Kept existing ngrok processes running to preserve public URLs.
- Verified backend on `127.0.0.1:18111` and frontend on `127.0.0.1:5199`.
- Verified the current frontend ngrok URL and backend ngrok URL.
- Restarted the frontend dev server with `VITE_API_BASE_URL` set to the backend public ngrok URL so external browser sessions do not call `127.0.0.1`.

## 추가 업데이트 (2026-06-14) - 작업 이력 메뉴 설정 그룹 이동

### 한국어 기록
- 사용자 요청에 따라 왼쪽 네비게이션의 `작업 이력` 메뉴를 `업무 현황` 그룹에서 `설정` 그룹으로 이동했습니다.
- 라우트와 페이지 구현은 변경하지 않고 사이드바 노출 위치만 바꿨습니다.
- 프론트 계약 테스트에 `작업 이력`이 `설정` 그룹에 포함되고 기존 `업무 현황`/`공고 업무` 그룹에는 남지 않는지 검증을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 20개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Moved the `/operation-runs` sidebar entry from the overview group into the settings group.
- Kept the route and page implementation unchanged.
- Extended the frontend contract test so `작업 이력` must remain under settings and not under overview or notice groups.

## 추가 업데이트 (2026-06-14) - 법인 증빙자료 업로드 연결 옵션 문구 수정

### 한국어 기록
- 사용자 요청에 따라 `법인 증빙자료 업로드` 화면의 `기존 법인에 연결` 선택 필드 문구를 수정했습니다.
- 기존 문구 `새 법인으로 생성 예정`을 `새로운 법인 생성 및 추가`로 변경했습니다.
- 프론트 계약 테스트에 새 문구가 존재하고 기존 문구가 남지 않는지 검증을 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 20개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Updated the corporation evidence upload select option copy from `새 법인으로 생성 예정` to `새로운 법인 생성 및 추가`.
- Added a frontend contract assertion to keep the new copy and reject the old copy.

## 추가 업데이트 (2026-06-14) - 판단 검토 화면 `보강 필요` 표시 문구 정리

### 한국어 기록
- 사용자 요청에 따라 `판단 검토` 화면에 표시되던 `보강 필요` 문구를 정리했습니다.
- 해당 문구는 내부 `missing` 상태와 `needs_followup` 검토 상태를 사용자 라벨로 보여주기 위해 존재했습니다.
- `판단 검토` 화면 자체가 부족조건 검토 맥락이므로 중복되고 딱딱한 표현으로 판단해 사용자 표시 문구를 바꿨습니다.
  - `missing`: `보강 필요` -> `준비 필요`
  - 검토 상태 `needs_followup`: `보강 필요` -> `추가 확인`
  - 이력/상세/요약 문구의 `보강` 표현을 `준비` 중심으로 교체
- 기존 DB에 저장된 과거 `user_summary` 안에 `보강 필요`가 남아 있어도 화면 표시 직전에 `준비 필요`로 변환하도록 보강했습니다.
- 프론트 계약 테스트에 기존 표시 문구가 다시 들어오지 않도록 금지 케이스를 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 20개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Removed user-facing `보강 필요` wording from the judgment review page.
- Replaced missing-result copy with `준비 필요` and follow-up review status copy with `추가 확인`.
- Added a frontend display normalizer so legacy saved summaries containing `보강 필요` render as `준비 필요`.
- Extended frontend contract tests to prevent the removed visible copy from returning.

## 추가 업데이트 (2026-06-14) - 판단 검토 / 부족조건 미리보기 선택 흐름과 이력 모달 UX 정리

### 한국어 기록
- `판단 검토` 페이지에서 첫 공고/첫 법인/최근 판단 결과를 자동 선택하던 흐름을 제거했습니다.
- `공고를 선택하세요`, `법인을 선택하세요`를 기본값으로 두고, 실제 선택 전에는 `판단 검토 실행` 버튼이 비활성화되도록 정리했습니다.
- 공고 또는 법인 선택을 변경하면 이전 판단 결과와 상세/근거 모달 상태가 초기화되도록 수정했습니다.
- `판단 요약` 상위 제목을 `판단 결과`로 바꾸고, 판단 실행 후에만 요약과 우선 준비 항목이 보이도록 정리했습니다.
- `판단 검토 실행 이력 보기` 문구와 `판단 검토 실행 이력으로 돌아가기` 버튼을 추가해 이력 모달에서 상세로 이동한 뒤 다시 돌아올 수 있게 했습니다.
- 판단 요약의 우선 준비 항목에는 관련 조건 목록과 `공고 원문 보기` 링크를 함께 표시하도록 보강했습니다.
- `부족조건 미리보기` 페이지도 공고/법인 자동 선택을 제거하고, 선택 변경 시 기존 비교 결과를 초기화하도록 수정했습니다.
- `공고 요구조건 후보` 모달 안의 반복 `공고 요구조건 보기` 버튼을 제거하고, 요구값/정규화 값/신뢰도/추출 방식/원문을 카드에 바로 표시하도록 변경했습니다.
- 두 페이지의 `계약서 초안 생성` 버튼은 삭제했습니다.
- 판단 실행이 Gemini 설정 상태에서 실제 Gemini 결과를 `result.user_summary`에 저장하는 API 테스트를 추가했습니다.

검증:
- `py -3.13 -m unittest tests.test_frontend_contracts -v`: 20개 통과
- `py -3.13 -m unittest tests.test_api_flows -v`: 108개 통과
- `npm run build`: 통과
- `py -3.13 scripts\check-encoding.py`: `ENCODING_CHECK_OK`
- `git diff --check`: 공백 오류 없음, 기존 LF/CRLF 변환 경고만 출력됨

### AI / Engineering Version (English)
- Removed automatic default notice/corporation/latest judgment selection from the judgment review page.
- Kept judgment and comparison results hidden until the user explicitly runs or selects a history item.
- Added selection-change reset behavior for result and modal state.
- Renamed the judgment summary heading to `판단 결과` and kept `판단 요약` as the summary subsection.
- Added history-to-detail back navigation for judgment and comparison modals.
- Expanded judgment priority actions with related requirement items and notice-source links.
- Removed contract draft quick actions from the judgment and comparison pages.
- Reworked the notice requirement candidate modal to show requirement details inline instead of nested per-row source buttons.
- Added a backend API regression test proving Gemini-configured judgment runs store the Gemini user summary payload.
