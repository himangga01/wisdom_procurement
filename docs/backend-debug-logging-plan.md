# 백엔드 디버깅 로그 추가 계획

## 목적
이 계획은 서비스 장애나 분석 실패가 발생했을 때 백엔드 단에서 원인을 빠르게 추적할 수 있도록 파일 로그를 추가하는 작업 범위를 정리한다.

현재 서비스에는 `operation_runs`, `backup_runs`, `nara_collection_runs` 같은 관리자용 이력 테이블이 있지만, 개발자가 실제 예외 스택, 요청 ID, 파일 처리 단계, 외부 API 호출 실패 원인을 따라갈 수 있는 백엔드 파일 로그 체계는 부족하다.

이번 작업의 목표는 다음과 같다.

- 이슈 발생 시 백엔드 로그 파일에서 요청 흐름과 실패 지점을 확인할 수 있게 한다.
- 문서 파싱, PDF 리더, OCR, RAG, 나라장터 첨부 다운로드, 계약서 생성, 백업 같은 실패 가능성이 높은 로직에 로그를 추가한다.
- API 키, 개인정보, 원문 증빙 내용이 로그에 노출되지 않도록 마스킹 규칙을 먼저 둔다.
- 로그 파일이 무한히 커지지 않도록 rotation과 보관 개수를 설정한다.
- 기존 `operation_runs`는 관리자 화면용 이력으로 유지하고, 새 로그는 개발/운영 디버깅용 파일 로그로 분리한다.

## 현재 상태 요약
- `backend/app/main.py`는 Flask 앱을 직접 생성하고, `after_request`에서는 JSON UTF-8 헤더만 보정한다.
- 요청 단위 `request_id`, 요청 시간, 응답 코드, 예외 스택 로깅은 아직 없다.
- `backend/app/services/operations.py`의 `record_operation_run()`은 운영 이력 DB 저장용이며, 상세 스택 트레이스나 단계별 디버깅 로그를 남기는 용도는 아니다.
- 주요 실패 지점은 `error_message` 컬럼에는 저장되지만, 실패 전후 문맥이 부족하다.

## 로그 저장 위치
기본 저장 위치는 다음으로 둔다.

- `backend/storage/logs/backend.log`
- `backend/storage/logs/backend-error.log`

설정값은 `.env`에서 조정 가능하게 한다.

```env
BACKEND_LOG_DIR=./storage/logs
BACKEND_LOG_LEVEL=INFO
BACKEND_LOG_MAX_MB=20
BACKEND_LOG_BACKUPS=10
BACKEND_LOG_FORMAT=jsonl
BACKEND_LOG_REQUEST_BODY=false
```

기본 정책:
- `backend.log`: 요청, 주요 처리 단계, 성공/실패 이벤트를 JSON Lines 형태로 저장
- `backend-error.log`: `ERROR` 이상만 별도 저장
- 로그 디렉터리는 자동 생성
- 로그 파일은 백업 대상에 기본 포함하지 않는다
- `.env`, API 키, 인증 헤더, 나라장터 `serviceKey`, Gemini/OpenAI 키는 로그에 저장하지 않는다

## 로그 형식
JSON Lines 형태를 기본으로 한다.

예시:

```json
{"ts":"2026-06-07T21:30:15+09:00","level":"ERROR","event":"pdf.parse.failed","request_id":"...","domain":"document","target_id":12,"error_code":"pdf_parse_failed","message":"OpenDataLoader timed out after 180 seconds.","exception_type":"PdfReaderError","stacktrace":"..."}
```

공통 필드:
- `ts`: KST 기준 ISO 시간
- `level`: `INFO`, `WARNING`, `ERROR`
- `event`: 이벤트 이름
- `request_id`: 요청 단위 추적 ID
- `method`, `path`, `status_code`, `duration_ms`: HTTP 요청 로그용
- `domain`: `document`, `basis_document`, `nara`, `contract`, `backup`, `ai`, `ocr`, `pdf_reader`
- `target_id`: 관련 DB id가 있을 때만 기록
- `operation_run_id`: 운영 이력과 연결 가능한 경우 기록
- `error_code`: 정규화된 실패 코드
- `message`: 짧은 원인
- `metadata`: 안전하게 마스킹된 부가 정보

## 민감정보 마스킹 규칙
로그 추가 전에 공통 sanitizer를 만든다.

마스킹 대상:
- `NARA_API_SERVICE_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- URL query의 `serviceKey`, `apiKey`, `key`, `token`
- `Authorization`, `Bearer`, `Basic`
- 주민등록번호 형태, 사업자등록번호는 필요 시 뒤 4자리만 유지
- 업로드 원문 텍스트, OCR 전체 텍스트, LLM prompt 전문

로그에 허용할 수 있는 값:
- 파일명
- 파일 확장자
- 파일 크기
- 문서 id, 공고 id, 기준문서 id
- 텍스트 길이, 페이지 수, 테이블 수
- 외부 API HTTP status
- 외부 API base URL 또는 host
- 에러 메시지 요약

## 구현 단계

### P0. 공통 로깅 기반 구축
1. `backend/app/core/logging.py` 추가
   - `configure_backend_logging(log_dir, level, max_mb, backups)`
   - `get_logger(name)`
   - `new_request_id()`
   - `sanitize_log_value(value)`
   - `sanitize_log_context(payload)`
   - `log_event(logger, event, level="info", **context)`
   - `log_exception(logger, event, exc, **context)`
2. `RotatingFileHandler` 적용
   - `backend.log`
   - `backend-error.log`
3. JSON Lines formatter 적용
4. 로그 설정 실패 시 앱 실행은 막지 않고 콘솔 경고만 남긴다.

### P1. Flask 요청 단위 로깅
1. `backend/app/main.py`에 요청 lifecycle 훅 추가
   - `before_request`: `request_id`, 시작 시간 저장
   - `after_request`: method/path/status/duration 로그
   - `errorhandler(Exception)`: 예외 스택 로그
2. 응답 헤더에 `X-Request-ID` 추가
3. `/health`는 너무 자주 호출될 수 있으므로 기본적으로 `DEBUG` 또는 샘플링 대상으로 둔다.
4. 요청 body는 기본 저장하지 않는다.

### P2. 실패 가능성이 높은 로직에 도메인 로그 추가
우선순위 순서대로 진행한다.

1. 문서 업로드/분석
   - `run_analysis()`
   - `extract_document()`
   - `run_ocr_if_needed()`
   - 로그 이벤트:
     - `document.analysis.started`
     - `document.parse.failed`
     - `document.ocr.failed`
     - `document.analysis.ai_failed`
     - `document.analysis.completed`

2. PDF 리더
   - `backend/app/pipelines/pdf_readers.py`
   - OpenDataLoader 실행 전후, timeout, fallback 발생 기록
   - 로그 이벤트:
     - `pdf_reader.opendataloader.started`
     - `pdf_reader.opendataloader.failed`
     - `pdf_reader.fallback.pymupdf`
     - `pdf_reader.completed`

3. 기준문서 RAG
   - `process_basis_document()`
   - `rebuild_basis_index()`
   - `validate_basis_index()`
   - `basis_search_results()`
   - 로그 이벤트:
     - `basis.processing.started`
     - `basis.processing.failed`
     - `basis.index.swap.completed`
     - `basis.index.validation.failed`
     - `basis.search.failed`

4. 나라장터 저장/분석
   - `save_and_analyze_nara_notice_item()`
   - `run_nara_notice_analysis_job()`
   - `request_binary()`, `request_text()` 호출부
   - 첨부 URL 검증/다운로드/파싱 실패 기록
   - 로그 이벤트:
     - `nara.notice.save.started`
     - `nara.attachment.download.failed`
     - `nara.attachment.parse.failed`
     - `nara.notice.analysis.partial_failed`
     - `nara.notice.analysis.completed`

5. 외부 API/AI
   - `summarize_with_ai()`
   - `summarize_with_gemini()`
   - `summarize_with_openai()`
   - 로그 이벤트:
     - `ai.summary.started`
     - `ai.summary.failed`
     - `ai.summary.fallback_used`

6. 계약서 생성
   - `create_contract_document()`
   - renderer 실패, 입력 snapshot validation 실패 기록
   - 로그 이벤트:
     - `contract.create.started`
     - `contract.validation.failed`
     - `contract.render.failed`
     - `contract.create.completed`

7. 백업/복원 계획
   - `create_backup_run()`
   - `validate_backup_file()`
   - `restore_plan_for_backup()`
   - 로그 이벤트:
     - `backup.create.started`
     - `backup.snapshot.failed`
     - `backup.validation.failed`
     - `backup.create.completed`

### P3. 운영 이력과 로그 연결
1. `record_operation_run()` 호출 결과의 id를 로그 context에 넣을 수 있는 곳은 연결한다.
2. 운영 이력에는 짧은 실패 사유를 유지하고, 상세 스택은 파일 로그에서 확인하도록 역할을 분리한다.
3. 향후 필요 시 관리자 화면에서 `request_id` 또는 `operation_run_id`로 로그 파일을 검색하는 기능을 Phase 4 후속으로 분리한다.

### P4. 테스트 추가
1. sanitizer 테스트
   - API 키, `serviceKey`, Authorization 값 마스킹 확인
2. JSONL formatter 테스트
   - 필수 필드 존재 확인
   - 한글 메시지 UTF-8 유지 확인
3. 파일 로그 생성 테스트
   - 임시 log dir 사용
   - `backend.log`, `backend-error.log` 생성 확인
4. 요청 단위 로그 테스트
   - 테스트 클라이언트 요청 후 `X-Request-ID` 확인
   - 500 예외 시 error log에 stacktrace 필드 확인
5. 도메인 실패 로그 테스트
   - PDF reader timeout/mock 실패
   - 문서 파싱 실패
   - 나라장터 첨부 다운로드 실패
   - 계약서 renderer 실패
   - 백업 snapshot 실패

## 우선 구현 범위
1차 구현은 다음까지만 진행한다.

1. 공통 로깅 기반
2. Flask 요청 단위 로그
3. 문서/PDF/RAG/나라장터/계약서/백업 실패 지점 로그
4. sanitizer와 파일 로그 테스트
5. README 또는 운영 문서의 로그 확인 방법 보강
6. `docs/work-log.md` 작업 기록

관리자 화면에서 로그 파일을 읽는 기능은 1차 범위에 포함하지 않는다. 로그 파일은 개발자/운영자가 로컬 PC에서 직접 확인하는 방식으로 시작한다.

## 예상 파일 변경
- `backend/app/core/logging.py` 신규 추가
- `backend/app/core/config.py` 로그 설정 추가
- `backend/app/main.py` 요청 lifecycle 및 주요 라우트/작업 로그 추가
- `backend/app/pipelines/parser.py` 문서 파싱 로그 추가
- `backend/app/pipelines/pdf_readers.py` PDF 리더 로그 추가
- `backend/app/pipelines/basis_document.py` 기준문서/RAG 로그 추가
- `backend/app/services/nara_api.py` 나라장터 HTTP 요청 로그 보조 추가
- `backend/app/services/backups.py` 백업 로그 추가
- `backend/app/services/contract_documents.py` 계약서 생성 로그 추가
- `backend/tests/test_backend_logging.py` 신규 추가
- `README.md` 또는 운영 관련 문서에 로그 확인 방법 추가
- `docs/work-log.md` 작업 기록 추가

## 검증 명령
구현 후 최소 검증은 다음으로 한다.

```powershell
py -3.13 -m unittest backend.tests.test_backend_logging -v
py -3.13 -m unittest backend.tests.test_api_flows -v
py -3.13 scripts\check-encoding.py
git diff --check -- backend/app backend/tests docs README.md
```

프론트 변경이 없으면 `npm run build`는 생략 가능하다. 단, 로그 상태를 관리자 화면에 연결하는 후속 작업이 생기면 프론트 빌드도 수행한다.

## Questions for Product Owner
- 로그 파일을 관리자 화면에서 직접 조회하는 기능까지 원하는가, 아니면 로컬 파일 확인으로 충분한가?
- 로그 보관 기간 또는 최대 용량 기준이 따로 필요한가?
- 운영자가 ZIP 백업에 로그를 포함하길 원하는가? 현재 계획은 민감정보 보호를 위해 백업에 기본 포함하지 않는 방향이다.

---

# AI / Engineering Version (English)

## Objective
Add backend file logging for debugging production-like local failures. Existing DB run tables remain user-facing operation history; new logs are developer-facing diagnostics.

## Proposed Architecture
- Add `backend/app/core/logging.py`.
- Configure JSON Lines rotating logs:
  - `backend/storage/logs/backend.log`
  - `backend/storage/logs/backend-error.log`
- Add env controls:
  - `BACKEND_LOG_DIR`
  - `BACKEND_LOG_LEVEL`
  - `BACKEND_LOG_MAX_MB`
  - `BACKEND_LOG_BACKUPS`
  - `BACKEND_LOG_FORMAT`
  - `BACKEND_LOG_REQUEST_BODY`
- Add request lifecycle logging in Flask:
  - `before_request`: request id and start time
  - `after_request`: status and duration
  - `errorhandler(Exception)`: sanitized stacktrace
  - response header `X-Request-ID`

## Sensitive Data Policy
Never log raw API keys, authorization headers, Nara `serviceKey`, uploaded/OCR full text, full LLM prompts, or sensitive corporation identifiers. Use a central sanitizer for nested dict/list/string values.

## Priority Domains
1. Document upload and analysis
2. PDF readers and OpenDataLoader fallback
3. Basis document processing and RAG index validation/search
4. Nara notice save/analyze and attachment download/parse
5. AI summary calls and fallback
6. Contract document generation
7. Backup creation and validation

## Testing
Add `backend/tests/test_backend_logging.py` for:
- sanitizer behavior
- JSONL formatter fields
- rotating file handler creation
- request id response header
- error log stacktrace
- representative domain failures

## Out Of Scope For First Pass
No frontend/admin log viewer in the first implementation. Logs are stored locally for developer inspection. A viewer can be added later if the product owner wants it.
