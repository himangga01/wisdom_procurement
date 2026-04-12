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
- 현재 기본 동작: 추출 텍스트가 충분하면 OCR 스킵
- 텍스트가 부족하면 `needs_ocr` 상태로 표기
- 실제 OCR 엔진(Tesseract/PaddleOCR) 연결은 다음 구현 단계에서 확장

## 9. 운영 시 주의사항
- API 키는 Git에 커밋하지 않는다.
- 민감 정보가 포함된 원문은 최소 범위만 모델로 전송한다.
- 모델/프롬프트 버전을 DB에 남겨 재현성을 확보한다.

## 10. 빠른 점검 체크리스트
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

## Security Notes
- never commit API keys
- minimize sensitive text sent to model
- log model/prompt versions for reproducibility

## References
- OpenAI Models: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- GPT-5 Guide: [https://platform.openai.com/docs/guides/gpt-5](https://platform.openai.com/docs/guides/gpt-5)
