# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`에서 Phase 1 개발/실행을 위한 AI API 세팅 방법을 정리합니다.

## 1. 어떤 API를 쓰는가
- 기본 Provider: Google Gemini API
- 기본 모델: `gemini-2.5-flash`
- 보조 Provider: OpenAI API
- 보조 모델: `gpt-5.4-mini`, `gpt-5.4`

Phase 1은 문서 요약이 목표이므로, 복잡한 판단 로직 대신 안정적인 구조화 요약 응답에 집중합니다.
포탈에서는 문서 분석/재분석 또는 나라장터 공고 저장 분석 시 사용할 Provider와 모델을 선택할 수 있습니다.

## 2. 사전 준비
1. Gemini API 키 발급
2. 필요 시 OpenAI API 키 발급
3. 백엔드 프로젝트에 `.env` 파일 생성
4. 필수 패키지 설치

## 3. 백엔드 환경 변수 설정
`backend/.env` 예시
```env
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
SQLITE_PATH=./app.db
STORAGE_ROOT=./storage
AI_PROVIDER_DEFAULT=gemini
AI_MODEL_DEFAULT=gemini-2.5-flash
OPENAI_API_KEY=sk-...
OPENAI_MODEL_PRIMARY=gpt-5.4-mini
OPENAI_MODEL_SECONDARY=gpt-5.4
GEMINI_API_KEY=...
GEMINI_MODEL_PRIMARY=gemini-2.5-flash
OCR_LANGUAGES=kor+eng
```

API 키 입력 위치는 `backend/.env`입니다.
- Gemini 키는 `GEMINI_API_KEY=` 뒤에 한 줄로 붙여 넣습니다.
- OpenAI 키는 `OPENAI_API_KEY=` 뒤에 한 줄로 붙여 넣습니다.
- 따옴표는 필요하지 않습니다.
- `backend/.env`는 Git에 올리지 않는 로컬 비밀 설정 파일입니다.
- 키를 변경한 뒤에는 백엔드 서버를 재시작해야 새 값이 반영됩니다.

## 4. 의존성 설치
```bash
cd backend
py -3.13 -m pip install -r requirements.txt
py -3.13 -m pip install -r requirements-ocr.txt
```

## 5. API 연동 동작 방식
- 포탈에서 선택한 Provider/모델을 백엔드 분석 API에 전달
- `GEMINI_API_KEY`가 있고 Gemini 모델을 선택하면 Gemini API 호출
- `OPENAI_API_KEY`가 있고 OpenAI 모델을 선택하면 OpenAI API 호출
- API 키가 없거나 실패하면 fallback 요약 사용
- fallback은 개발 중 UI/흐름 테스트를 위해 제공됨

즉, Phase 1 개발 중에는 키 없이도 기본 기능 점검이 가능합니다.

## 6. 요약 요청 구조
현재 구현은 아래 원칙을 따릅니다.
- 조달문서 분석 역할 고정
- JSON 구조화 출력 강제
- 문서에 없는 내용 생성 금지 지시
- 한국어 사용자용 마크다운 요약 동시 생성

## 7. 캐시 / 재분석 정책
- 캐시 키: `input_hash + prompt_version + model_name`
- 동일 입력이면 기존 분석 재사용 가능
- 재분석 버튼은 강제 재실행
- 이전 분석 이력은 보존

## 8. OCR 관련 안내
Phase 1 코드에는 OCR 연결 지점이 준비되어 있습니다.
- PDF 추출 기본 엔진은 `pypdf`에서 `PyMuPDF`로 교체하는 것으로 결정했습니다.
- 현재 조달 PDF 샘플은 텍스트 레이어가 있어 OCR보다 레이아웃 기반 추출 품질이 더 중요합니다.
- `PyMuPDF`로 페이지별 텍스트, 블록, 좌표 정보를 추출한 뒤 정규화 텍스트를 생성합니다.
- 추출 텍스트가 충분하면 OCR은 스킵합니다.
- 텍스트가 부족하거나 이미지형 PDF로 판단되면 OCR fallback으로 전환합니다.
- OCR fallback 후보는 `PaddleOCR`을 우선 검토하고, 경량 대안으로 `Tesseract(kor+eng)`를 둡니다.
- Stirling PDF는 메인 reader 엔진이 아니라 향후 PDF 전처리/OCR 보조 서버로 선택 연동할 수 있습니다.

## 9. PDF 추출 엔진 교체 구현 계획
1. 백엔드 의존성에 `PyMuPDF`를 추가합니다.
2. PDF 추출 로직을 `pypdf`에서 `PyMuPDF` 기반으로 교체합니다.
3. 페이지별 추출 문자 수, 블록 수, OCR 필요 여부를 메타데이터로 남깁니다.
4. 조달문서에서 자주 깨지는 항목 번호, 날짜, 금액, 표 헤더 주변 줄바꿈을 후처리합니다.
5. 선택한 LLM에는 원본 파일이 아니라 정규화된 추출 텍스트와 핵심 메타데이터를 전달합니다.
6. API 키가 없을 때는 기존 fallback 요약으로 동작하지만, 추출 텍스트 품질은 `PyMuPDF` 기준으로 개선합니다.

## 10. 운영 시 주의사항
- API 키는 Git에 커밋하지 않는다.
- 민감 정보가 포함된 원문은 최소 범위만 모델로 전송한다.
- 모델/프롬프트 버전을 DB에 남겨 재현성을 확보한다.

## 11. 빠른 점검 체크리스트
1. `/health` 응답 확인
2. 법인 생성 -> 프로젝트 생성 -> 문서 업로드
3. `분석` 버튼 클릭
4. 분석 결과 페이지에서 마크다운 출력 확인

---

# AI / Engineering Version (English)

## Purpose
This guide describes practical AI API setup for Phase 1 implementation of SMART Procurement Calculator.

## Provider and Models
- Default provider: Google Gemini API
- Default model: `gemini-2.5-flash`
- Secondary provider: OpenAI API
- Secondary models: `gpt-5.4-mini`, `gpt-5.4`

## Environment Variables
Use `backend/.env`:
```env
AI_PROVIDER_DEFAULT=gemini
AI_MODEL_DEFAULT=gemini-2.5-flash
GEMINI_API_KEY=...
GEMINI_MODEL_PRIMARY=gemini-2.5-flash
OPENAI_API_KEY=sk-...
OPENAI_MODEL_PRIMARY=gpt-5.4-mini
OPENAI_MODEL_SECONDARY=gpt-5.4
```

Put real API keys in `backend/.env` as single-line `GEMINI_API_KEY=...` and `OPENAI_API_KEY=...` values.
Do not commit this file. Restart the backend after changing the key or model values.

## Runtime Behavior
- The portal sends the selected provider/model to the backend analysis endpoint.
- If the selected provider key exists, call that provider for structured summary.
- If the selected key is missing or request fails, deterministic fallback summary is returned.

This allows UI and pipeline development without blocking on external API readiness.

## Prompt/Output Rules
- fixed assistant role for Korean procurement summary
- strict JSON output schema
- no unsupported claims
- markdown rendering for admin-friendly display

## Cache and Re-analysis
- cache key includes input hash, prompt version, and model
- re-analysis endpoint forces a new run
- prior analyses are preserved as history

## OCR Note
Current phase exposes OCR integration seam and status handling (`skipped`, `needs_ocr`).
Engine-level OCR implementation can be plugged in next without API contract changes.

## PDF Extraction Decision
- Replace the current default PDF extractor from `pypdf` to `PyMuPDF`.
- Use `PyMuPDF` for text, page, block, and coordinate-aware extraction.
- Keep DOCX extraction on `python-docx`.
- Run OCR only when extracted text is insufficient or pages appear image-based.
- Prefer `PaddleOCR` as the stronger OCR fallback candidate for Korean procurement documents.
- Keep `Tesseract(kor+eng)` as a lighter fallback option.
- Treat Stirling PDF as an optional future PDF preprocessing/OCR service, not as the main embedded reader.

## Security Notes
- never commit API keys
- minimize sensitive text sent to model
- log model/prompt versions for reproducibility

## References
- Gemini API Docs: [https://ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
- Gemini Structured Outputs: [https://ai.google.dev/gemini-api/docs/structured-output](https://ai.google.dev/gemini-api/docs/structured-output)
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
