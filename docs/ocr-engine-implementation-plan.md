# 한국어 버전

## 목적
이 문서는 `SMART 조달청 계산기`의 실제 OCR 엔진 구현 계획을 정의합니다.

현재 프로젝트는 PDF/DOCX 텍스트 추출은 동작하지만, 스캔 PDF나 이미지 파일에 대한 실제 OCR 엔진은 아직 연결되어 있지 않습니다. 따라서 Phase 1.6A 전에 OCR 엔진을 먼저 구현해 증빙자료 자동 추출의 기반을 만듭니다.

## 결론: 사용할 오픈소스

### 1차 선택: PaddleOCR PP-OCRv5
주 OCR 엔진은 `PaddleOCR PP-OCRv5`를 사용합니다.

선택 이유:
- 한국어 OCR 지원
- 문서 이미지, 스캔본, 복합 레이아웃에 Tesseract보다 유리할 가능성이 높음
- Python에서 직접 호출 가능
- 향후 문서 구조 분석, 표/레이아웃 분석 확장 여지가 있음
- 오픈소스 생태계와 모델 업데이트가 활발함

공식 자료 기준:
- PaddleOCR PP-OCRv5는 한국어를 포함한 다국어 인식을 지원합니다.
- PaddleOCR 공식 설치 문서는 `paddleocr` inference package 설치 방식을 제공합니다.

### 2차 대안: Tesseract OCR
Tesseract는 경량 fallback 엔진으로 둡니다.

사용 위치:
- PaddleOCR 설치가 실패하는 PC
- 매우 단순한 이미지 OCR
- 빠른 로컬 테스트
- PaddleOCR 결과와 비교하는 회귀 테스트

단점:
- 한글 조달문서/증빙자료의 표, 도장, 낮은 해상도, 복잡한 레이아웃에서는 품질이 불안정할 수 있음
- 전처리 품질에 민감함

## 현재 프로젝트 상태

현재 구현:
- PDF 추출: `PyMuPDF`
- DOCX 추출: `python-docx`
- OCR 상태 감지: PDF 텍스트가 부족하면 `needs_ocr`
- 실제 OCR 엔진: 미구현

현재 파일:
- `backend/app/pipelines/parser.py`
- `backend/app/pipelines/ocr.py`
- `backend/app/main.py`

현재 제한:
- 일반 업로드 허용 확장자는 `.pdf`, `.docx`
- 이미지 파일 `.jpg`, `.jpeg`, `.png`는 아직 업로드 파이프라인에 연결되지 않음
- `ocr.py`는 `needs_ocr` 상태만 반환하고 실제 OCR을 수행하지 않음

## Python 런타임 기준

현재 서비스 표준:
- Python: `3.13.13`
- Windows 실행 명령: `py -3.13`
- 실제 실행 파일: `C:\Python313\python.exe`

PaddleOCR/PaddlePaddle은 Python 3.13.13 기준으로 설치하고 검증합니다. 기존 가상환경 경로는 과거 검증용 환경으로만 보며, 현재 서버 실행/스모크 테스트/OCR 테스트의 표준은 전역 Python 3.13.13입니다.

정책:
- Phase 1.6 OCR 구현은 Python 3.13.13 기준으로 안정화한다.
- 서버 실행 스크립트와 스모크 테스트는 `py -3.13` 또는 `C:\Python313\python.exe`를 사용한다.
- 문서와 코드에서 다른 Python 런타임을 표준으로 가정하지 않는다.

## 구현 목표

### Phase OCR-1: OCR 엔진 어댑터 구현
목표:
- 기존 `ocr.py`를 실제 OCR 엔진을 호출하는 어댑터 구조로 변경
- OCR 엔진이 없어도 서버가 죽지 않도록 graceful fallback 제공

구현 항목:
- `OcrResult` 데이터 구조
- `OcrEngine` 인터페이스
- `PaddleOcrEngine`
- `TesseractOcrEngine` 후보 또는 stub
- `NoopOcrEngine`
- OCR 엔진 선택 설정
- OCR 가능 여부 health check

설정값 예시:
```env
OCR_ENGINE=paddle
OCR_LANG=kor+eng
OCR_DEVICE=cpu
OCR_MIN_TEXT_LENGTH=80
OCR_RENDER_DPI=220
```

### Phase OCR-2: PDF OCR 연결
목표:
- `PyMuPDF`로 PDF 텍스트 추출
- 텍스트가 부족한 페이지 또는 전체 문서가 스캔형이면 페이지 이미지를 렌더링
- 렌더링 이미지에 PaddleOCR 실행
- 페이지별 OCR 텍스트와 메타데이터 저장

흐름:
```text
PDF 업로드
  -> PyMuPDF 텍스트 추출
  -> 텍스트 충분하면 OCR skipped
  -> 텍스트 부족하면 PyMuPDF로 페이지 이미지 렌더링
  -> PaddleOCR 실행
  -> 페이지별 OCR 텍스트 병합
  -> ocr_status=completed
  -> 분석/요약 파이프라인으로 전달
```

### Phase OCR-3: 이미지 OCR 연결
목표:
- JPG/JPEG/PNG 파일을 OCR 대상으로 허용
- 증빙자료 업로드에서 이미지 파일 처리 가능

흐름:
```text
이미지 업로드
  -> 파일 저장
  -> 이미지 전처리
  -> PaddleOCR 실행
  -> 텍스트/좌표/신뢰도 저장
  -> 증빙자료 분류/필드 추출 후보 생성
```

### Phase OCR-4: 테스트와 샘플 검증
목표:
- 실제 조달 공고문/사업자등록증명/증빙자료 이미지에서 OCR 품질 검증

테스트 항목:
- 텍스트 레이어 PDF는 OCR을 건너뛴다.
- 빈 PDF 또는 스캔 PDF는 OCR 대상으로 표시된다.
- 이미지 파일은 OCR이 실행된다.
- OCR 엔진 미설치 시 `ocr_status=unavailable` 또는 `needs_ocr_setup`으로 처리된다.
- OCR 결과가 없더라도 서버와 업로드 플로우는 실패하지 않는다.

## 백엔드 설계

권장 파일 구조:
```text
backend/app/pipelines/
  parser.py
  ocr.py
  ocr_engines/
    __init__.py
    base.py
    paddle_engine.py
    tesseract_engine.py
    noop_engine.py
  image_preprocess.py
```

### OcrResult
```text
- text
- status
- engine
- language
- page_count
- pages
- average_confidence
- warnings
- error_message
```

### OCR 상태값
```text
pending
skipped
needs_ocr
completed
unavailable
failed
needs_ocr_setup
```

## 기존 파이프라인 재사용 방식

재사용 가능:
- `extract_document()`
- `PyMuPDF` PDF 텍스트 추출
- DOCX 텍스트 추출
- 분석 캐시에서 사용하는 텍스트 해시 전략
- `ocr_status` 컬럼

수정 필요:
- `ocr.py`는 실제 OCR 엔진 호출로 변경
- `extract_document()` 결과가 `needs_ocr=True`이면 OCR 엔진을 호출하도록 분석 흐름 수정
- Nara 첨부파일 분석에서도 동일 OCR 경로 사용
- Phase 1.6 증빙자료 파이프라인에서도 동일 OCR 경로 사용

주의:
- 기존 `run_analysis()`는 `project_documents` 도메인에 묶여 있으므로 법인 증빙자료에 그대로 재사용하지 않는다.
- OCR/파싱 유틸은 공통 재사용하고, 증빙자료 분류/필드 추출은 별도 파이프라인으로 둔다.

## 설치 계획

우선 검증 환경:
- Windows
- Python 3.13.13
- CPU 모드

권장 패키지:
```text
paddlepaddle==3.2.2
paddleocr
opencv-python
pillow
numpy
python-bidi==0.4.2
```

Tesseract fallback 후보:
```text
pytesseract
```

추가 OS 설치가 필요할 수 있음:
- Tesseract executable
- Korean traineddata `kor.traineddata`
- English traineddata `eng.traineddata`

### 로컬 설치 검증 결과

2026-05-10 로컬 Windows 환경에서 확인한 결과:
- Winget으로 Python 3.13을 `3.13.13`으로 업그레이드/복구 설치했다.
- 전역 실행 명령은 `py -3.13`을 사용한다.
- 전역 Python 3.13.13에서 `pip`, `paddlepaddle==3.2.2`, `paddleocr==3.3.3` 설치와 OCR 실행이 성공했다.
- `paddlepaddle==3.3.1`은 PP-OCRv5 실행 중 `ConvertPirAttribute2RuntimeAttribute` oneDNN 런타임 오류가 발생했다.
- `paddlepaddle==3.2.2`로 낮추면 제공된 사업자등록증 이미지 OCR이 성공했다.
- `python-bidi==0.6.9`는 Python 3.13 환경에서 Rust 빌드 중 `python313.lib`를 찾지 못해 실패했다.
- `python-bidi==0.4.2`는 순수 Python wheel로 설치 성공했고 PaddleOCR 의존성도 충족했다.
- 사용자 제공 한글 경로 이미지는 PowerShell/Python 전달 과정에서 경로가 깨질 수 있으므로, 실제 테스트에서는 `backend/storage/ocr-samples/business_registration.png`로 복사해 검증했다.
- 실제 서비스 업로드 파일은 UUID 기반 ASCII 경로로 저장되므로 같은 경로 문제를 피할 수 있다.

## 구현 순서

1. Python 3.13.13 OCR 런타임 기준 확정
2. `docs/ocr-engine-implementation-plan.md` 작성
3. `backend/app/pipelines/ocr.py`를 어댑터 기반 구조로 변경
4. PaddleOCR 의존성 설치 및 import health check
5. PDF 페이지 렌더링 함수 추가
6. OCR 결과 구조화
7. 기존 문서 분석 파이프라인에 OCR 호출 연결
8. 이미지 파일 OCR 테스트 추가
9. 스캔 PDF OCR 테스트 추가
10. 서버 스크립트에서 Python 3.13.13 런타임 사용 여부 점검
11. 작업 로그 업데이트

## 리스크와 대응

### 리스크 1: 다른 Python 런타임으로 잘못 실행
대응:
- OCR은 Python 3.13.13에서 먼저 구현하고 검증
- 서버 스크립트에서 `py -3.13` 또는 `C:\Python313\python.exe`를 명시적으로 선택

### 리스크 2: PaddleOCR 설치 용량과 첫 실행 시간
대응:
- 첫 실행 시 모델 다운로드 안내
- OCR 설정 상태 화면에 엔진/모델 준비 여부 표시

### 리스크 3: OCR 품질 편차
대응:
- DPI 200~300 렌더링 옵션 제공
- 원문 텍스트와 OCR 텍스트를 분리 저장
- 신뢰도가 낮으면 사용자 확인 필요로 표시

### 리스크 4: 개인정보/민감정보 로그 노출
대응:
- OCR 원문 전체를 일반 로그에 남기지 않음
- 사업자등록번호, 대표자명, 주소 등은 마스킹

## 결정 사항

- 주 엔진은 `PaddleOCR PP-OCRv5`
- fallback 후보는 `Tesseract OCR`
- OCR 구현은 `OcrService/OcrEngine` 어댑터 구조로 진행
- PDF 렌더링은 기존 `PyMuPDF`를 사용
- 이미지 전처리는 `OpenCV`와 `Pillow`를 사용
- Python 3.13.13에서 우선 검증

## Questions for Product Owner

- OCR 첫 구현에서 GPU 사용이 필요한가, CPU만 허용할 것인가?
- OCR 모델 다운로드가 최초 실행 시 인터넷을 사용하는 방식이어도 괜찮은가?
- OCR 결과 원문을 DB에 저장할 것인가, 파일로 저장하고 DB에는 경로만 둘 것인가?
- OCR 품질이 낮은 경우 외부 Vision API 사용을 후순위 옵션으로 허용할 것인가?

## 참고 자료

- [PaddleOCR PP-OCRv5 multilingual documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md)
- [PaddleOCR installation documentation](https://www.paddleocr.ai/v3.3.0/en/version3.x/installation.html)
- [PaddlePaddle PyPI package](https://pypi.org/project/paddlepaddle/)
- [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
- [Tesseract installation documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- [Tesseract Korean traineddata](https://github.com/tesseract-ocr/tessdata/blob/main/kor.traineddata)

## 현재 코드 기준 메모
최종 갱신일: 2026-06-07

- OCR은 모든 PDF에 무조건 적용하지 않고, 현재 PDF/DOCX 추출 결과가 부족할 때 fallback/degrade 경로로 사용합니다.
- PDF reader 기본값은 OpenDataLoader 우선 `auto` 모드이며, PyMuPDF는 fallback과 OCR 렌더링 보조 엔진으로 유지합니다.
- OCR 엔진 의존성이 없는 환경에서도 업로드/분석 흐름은 `needs_ocr_setup` 또는 fallback 상태로 degrade해야 합니다.
- 이 문서는 OCR 엔진 도입 계획서이며, 최신 PDF reader 정책은 `docs/opendataloader-pdf-replacement-test-plan.md`와 `README.md`를 우선합니다.

---

# AI / Engineering Version (English)

## Current Code Note
Last updated: 2026-06-07

- OCR is not applied to every PDF; it remains a fallback/degrade path when current PDF/DOCX extraction is insufficient.
- Default PDF reader is OpenDataLoader-first `auto`; PyMuPDF remains fallback and OCR rendering helper.
- Upload/analysis flows must degrade to `needs_ocr_setup` or fallback states when OCR dependencies are unavailable.
- Treat this as the OCR engine plan; use `docs/opendataloader-pdf-replacement-test-plan.md` and `README.md` for the current PDF reader policy.

## Purpose
This document defines the OCR engine implementation plan for `SMART Procurement Calculator`.

The project currently supports PDF/DOCX text extraction, but scanned PDFs and image files do not have a real OCR engine connected yet. OCR must be implemented before Phase 1.6A so corporation evidence auto-extraction can work reliably.

## Decision: Open-Source OCR Stack

### Primary Engine: PaddleOCR PP-OCRv5
Use `PaddleOCR PP-OCRv5` as the primary OCR engine.

Rationale:
- supports Korean OCR
- better fit than Tesseract for scanned documents, document images, and mixed layouts
- callable from Python
- can later expand toward layout/table/document parsing
- active open-source ecosystem

Official references indicate that PP-OCRv5 provides multilingual recognition including Korean, and PaddleOCR provides a Python inference package.

### Secondary Fallback: Tesseract OCR
Keep Tesseract as a lightweight fallback or diagnostic engine.

Use cases:
- PaddleOCR installation fails on a local PC
- simple image OCR
- quick local smoke testing
- comparison/regression testing against PaddleOCR output

Limitations:
- Korean procurement/evidence documents with tables, seals, low resolution, or complex layouts may produce unstable results
- image preprocessing strongly affects quality

## Current Project State

Implemented:
- PDF extraction: `PyMuPDF`
- DOCX extraction: `python-docx`
- OCR detection: PDFs with insufficient text are marked `needs_ocr`
- Real OCR engine: not implemented

Relevant files:
- `backend/app/pipelines/parser.py`
- `backend/app/pipelines/ocr.py`
- `backend/app/main.py`

Current limitations:
- upload allowlist is currently `.pdf` and `.docx`
- `.jpg`, `.jpeg`, and `.png` are not connected to the upload pipeline yet
- `ocr.py` only returns OCR status and does not run an engine

## Python Runtime Standard

Current service standard:
- Python: `3.13.13`
- Windows command: `py -3.13`
- executable: `C:\Python313\python.exe`

PaddleOCR/PaddlePaddle must be installed and validated against Python 3.13.13. Old virtual environment paths are treated only as historical validation environments; current backend server execution, smoke tests, and OCR tests use global Python 3.13.13.

Policy:
- stabilize Phase OCR work on Python 3.13.13
- server scripts and smoke tests must use `py -3.13` or `C:\Python313\python.exe`
- do not document or code another Python runtime as the service standard

## Implementation Goals

### Phase OCR-1: OCR Engine Adapter
Goal:
- replace the placeholder `ocr.py` with a real adapter-based OCR implementation
- keep the server stable when OCR is unavailable

Items:
- `OcrResult`
- `OcrEngine` interface
- `PaddleOcrEngine`
- optional `TesseractOcrEngine`
- `NoopOcrEngine`
- config-driven engine selection
- OCR health check

Example settings:
```env
OCR_ENGINE=paddle
OCR_LANG=kor+eng
OCR_DEVICE=cpu
OCR_MIN_TEXT_LENGTH=80
OCR_RENDER_DPI=220
```

### Phase OCR-2: PDF OCR
Flow:
```text
PDF upload
  -> PyMuPDF text extraction
  -> skip OCR if text is sufficient
  -> render low-text pages as images with PyMuPDF
  -> run PaddleOCR
  -> merge page OCR text
  -> ocr_status=completed
  -> pass text to analysis/summarization
```

### Phase OCR-3: Image OCR
Flow:
```text
image upload
  -> store file
  -> preprocess image
  -> run PaddleOCR
  -> store text, boxes, and confidence metadata
  -> create classification/extraction candidates
```

### Phase OCR-4: Tests And Sample Validation
Test coverage:
- text-layer PDFs skip OCR
- blank/scanned PDFs trigger OCR
- image files run OCR
- missing OCR dependency returns `unavailable` or `needs_ocr_setup`
- uploads do not fail just because OCR is unavailable

## Backend Design

Recommended structure:
```text
backend/app/pipelines/
  parser.py
  ocr.py
  ocr_engines/
    __init__.py
    base.py
    paddle_engine.py
    tesseract_engine.py
    noop_engine.py
  image_preprocess.py
```

### OcrResult
```text
- text
- status
- engine
- language
- page_count
- pages
- average_confidence
- warnings
- error_message
```

### OCR Status Values
```text
pending
skipped
needs_ocr
completed
unavailable
failed
needs_ocr_setup
```

## Reuse Strategy

Reusable:
- `extract_document()`
- existing `PyMuPDF` PDF extraction
- DOCX extraction
- text-hash based analysis cache concept
- `ocr_status` column

Needs changes:
- `ocr.py` must call real OCR engines
- analysis flow must invoke OCR when `needs_ocr=True`
- Nara attachment analysis should use the same OCR path
- Phase 1.6 evidence pipeline should use the same OCR path

Important:
- `run_analysis()` is tied to the `project_documents` domain and should not be reused directly for corporation evidence documents.
- Parsing/OCR utilities are shared; evidence classification and field extraction remain separate.

## Installation Plan

Initial validation target:
- Windows
- Python 3.13.13
- CPU mode

Recommended packages:
```text
paddlepaddle==3.2.2
paddleocr
opencv-python
pillow
numpy
python-bidi==0.4.2
```

Tesseract fallback candidate:
```text
pytesseract
```

Additional OS-level dependency may be required:
- Tesseract executable
- Korean traineddata `kor.traineddata`
- English traineddata `eng.traineddata`

### Local Installation Verification Result

Verified on the local Windows environment on 2026-05-10:
- Python 3.13 was upgraded/repaired to `3.13.13` through Winget.
- Use `py -3.13` as the global Python 3.13 command.
- Global Python 3.13.13 successfully installed `pip`, `paddlepaddle==3.2.2`, and `paddleocr==3.3.3`, and successfully ran OCR.
- `paddlepaddle==3.3.1` failed during PP-OCRv5 inference with a `ConvertPirAttribute2RuntimeAttribute` oneDNN runtime error.
- `paddlepaddle==3.2.2` successfully ran OCR on the provided business registration image.
- `python-bidi==0.6.9` failed to build on Python 3.13 because `python313.lib` was not available.
- `python-bidi==0.4.2` installed as a pure Python wheel and satisfied the PaddleOCR dependency.
- The original Korean sample path can be corrupted when passed through PowerShell/Python, so the test image was copied to `backend/storage/ocr-samples/business_registration.png`.
- Uploaded service files are stored under UUID-based ASCII paths, so the same path issue is avoided in normal operation.

## Implementation Order

1. Confirm Python 3.13 OCR runtime.
2. Add this OCR plan document.
3. Refactor `backend/app/pipelines/ocr.py` into an adapter-based implementation.
4. Install and health-check PaddleOCR dependencies.
5. Add PDF page rendering.
6. Structure OCR result metadata.
7. Connect OCR into the existing document analysis pipeline.
8. Add image OCR tests.
9. Add scanned PDF OCR tests.
10. Verify server scripts use the Python 3.13.13 runtime.
11. Update the work log.

## Risks And Mitigations

### Accidental Execution With Another Python Runtime
Mitigation:
- implement and validate OCR on Python 3.13.13
- explicitly select `py -3.13` or `C:\Python313\python.exe` in server scripts

### PaddleOCR Size And First-Run Download
Mitigation:
- show first-run model download guidance
- expose OCR engine/model readiness in settings

### OCR Quality Variation
Mitigation:
- provide DPI 200-300 rendering options
- store extracted text and OCR text separately
- mark low confidence output as needs review

### Sensitive Data Logging
Mitigation:
- do not write full OCR text to general logs
- mask business registration numbers, representative names, and addresses

## Decisions

- Primary OCR engine: `PaddleOCR PP-OCRv5`
- Fallback candidate: `Tesseract OCR`
- Architecture: `OcrService/OcrEngine` adapter
- PDF rendering: existing `PyMuPDF`
- Image preprocessing: `OpenCV` and `Pillow`
- Runtime: validate first on Python 3.13.13

## Questions for Product Owner

- Should the first OCR implementation be CPU-only, or should GPU be supported immediately?
- Is first-run internet access acceptable for OCR model downloads?
- Should OCR full text be stored in DB, or should DB store only paths to extracted text files?
- If local OCR quality is too low, can external Vision API be allowed as a later option?

## References

- [PaddleOCR PP-OCRv5 multilingual documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md)
- [PaddleOCR installation documentation](https://www.paddleocr.ai/v3.3.0/en/version3.x/installation.html)
- [PaddlePaddle PyPI package](https://pypi.org/project/paddlepaddle/)
- [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
- [Tesseract installation documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- [Tesseract Korean traineddata](https://github.com/tesseract-ocr/tessdata/blob/main/kor.traineddata)
