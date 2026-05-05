# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`에서 Phase 1 개발/실행을 위한 AI API 세팅 방법을 정리합니다.

## 1. 어떤 API를 쓰는가
- 1순위: OpenAI API
- 주 모델: `gpt-5.1`
- 보조 모델: `gpt-5-mini`

Phase 1은 문서 요약이 목표이므로, 복잡한 판단 로직 대신 안정적인 구조화 요약 응답에 집중합니다.

## 2. 사전 준비
1. OpenAI API 키 발급
2. 백엔드 프로젝트에 `.env` 파일 생성
3. 필수 패키지 설치

## 3. 백엔드 환경 변수 설정
`backend/.env` 예시
```env
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
SQLITE_PATH=./app.db
STORAGE_ROOT=./storage
OPENAI_API_KEY=sk-...
OPENAI_MODEL_PRIMARY=gpt-5.1
OPENAI_MODEL_SECONDARY=gpt-5-mini
OCR_LANGUAGES=kor+eng
```

## 4. 의존성 설치
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

## 5. API 연동 동작 방식
- `OPENAI_API_KEY`가 있으면 실제 OpenAI API 호출
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
5. GPT-5.1에는 원본 파일이 아니라 정규화된 추출 텍스트와 핵심 메타데이터를 전달합니다.
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
- Provider: OpenAI API
- Primary model: `gpt-5.1`
- Cost-efficient secondary model: `gpt-5-mini`

## Environment Variables
Use `backend/.env`:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_PRIMARY=gpt-5.1
OPENAI_MODEL_SECONDARY=gpt-5-mini
```

## Runtime Behavior
- If API key exists: call OpenAI API for structured summary.
- If key is missing or request fails: deterministic fallback summary is returned.

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
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
