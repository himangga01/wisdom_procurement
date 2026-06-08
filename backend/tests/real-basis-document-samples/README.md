# 실제 기준문서 샘플 보관소

이 폴더는 실제 `중소기업자간 경쟁제품 직접생산 확인기준` PDF를 로컬 테스트 샘플로 보관하기 위한 위치입니다.

PDF 원본과 실행 산출물은 저장소에 커밋하지 않습니다. `README.md`와 `manifest.example.json`만 추적하고, 실제 파일은 `.gitignore`로 제외합니다.

## 샘플 등록

```powershell
py -3.13 scripts/register-real-basis-document-sample.py `
  --source "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf"
```

등록 후 생성되는 파일:

- `manifest.json`
- 실제 PDF 사본

## 추출 리포트 생성

```powershell
py -3.13 scripts/analyze-real-basis-document-pdf.py
```

생성되는 파일:

- `extraction-report.json`
- `extraction-baseline.json`

## 실제 RAG 테스트 실행

```powershell
$env:RUN_REAL_BASIS_RAG_TESTS="1"
py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q
Remove-Item Env:\RUN_REAL_BASIS_RAG_TESTS
```

`RUN_REAL_BASIS_RAG_TESTS=1`이 없으면 테스트는 skip됩니다. 다른 PC에서 저장소를 받은 사람은 먼저 직접 PDF를 등록한 뒤 테스트해야 합니다.

## 외부 TXT/DOCX/MD 기준 텍스트와 비교

PDF를 별도 도구로 추출한 TXT, DOCX, MD가 있으면, 우리 서비스의 PDF 직접 파싱 결과와 비교할 수 있습니다.
DOCX는 문단과 표 셀 텍스트를 모두 읽습니다.

```powershell
py -3.13 scripts/compare-real-basis-document-txt.py `
  --reference-file "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).txt"
```

DOCX 기준 파일 예시:

```powershell
py -3.13 scripts/compare-real-basis-document-txt.py `
  --reference-file "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).docx"
```

MD 기준 파일 예시:

```powershell
py -3.13 scripts/compare-real-basis-document-txt.py `
  --reference-file "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md"
```

## PDF에서 MD 재생성 후 기준 MD와 비교

우리 서비스 방식으로 PDF에서 텍스트와 표를 Markdown으로 재생성한 뒤, 기준 MD와 비교할 수 있습니다.

```powershell
py -3.13 scripts/regenerate-real-basis-document-md.py `
  --reference-md "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md" `
  --strict
```

생성되는 파일:

- `regenerated-basis-document.md`
- `md-regeneration-comparison-report.json`

생성되는 파일:

- `text-comparison-report.json`

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

이 폴더는 실제 기준문서 PDF를 Git에 넣지 않고 로컬에서만 QA fixture로 쓰기 위한 위치입니다.

현재 사용 기준:
- 원본 PDF와 `manifest.json`, 실제 추출 report는 `.gitignore` 대상입니다.
- `regenerated-basis-document.md`는 PyMuPDF 기반 역사적 Markdown 재생성 baseline입니다.
- `opendataloader-regenerated-basis-document.md`, `opendataloader-regenerated-basis-document-auto.md`, `opendataloader-regenerated-basis-document-fallback.md`는 OpenDataLoader 전환 이후 QA 산출물입니다.
- 현재 서비스 기본 PDF reader는 OpenDataLoader 우선 `auto` 모드이며, PyMuPDF는 fallback으로 유지됩니다.
- DOCX 기준 비교는 문단과 표 cell 텍스트를 함께 사용합니다.
- 실제 기준문서 RAG opt-in 테스트는 `RUN_REAL_BASIS_RAG_TESTS=1`일 때만 실행합니다.

권장 실행:
```powershell
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine opendataloader --threads 4 --timeout-seconds 1200 --strict
py -3.13 scripts/run-opendataloader-real-basis-qa.py --engine auto --threads 4 --timeout-seconds 1200 --strict
```

---

# AI / Engineering Version (English)

This folder stores opt-in local real-basis-document QA samples.

Current code update:
- real PDFs, `manifest.json`, and extraction reports remain ignored local artifacts
- `regenerated-basis-document.md` is a historical PyMuPDF Markdown baseline
- `opendataloader-regenerated-basis-document*.md` files are post-replacement OpenDataLoader QA artifacts
- default service PDF reader is OpenDataLoader-first `auto` mode with PyMuPDF fallback
- DOCX reference comparison includes paragraph and table-cell text
- real-basis RAG tests run only with `RUN_REAL_BASIS_RAG_TESTS=1`

Tracked files:

- `README.md`
- `manifest.example.json`

Ignored local artifacts:

- real PDF files
- `manifest.json`
- extraction reports and baselines
- temporary SQLite/storage outputs

Run order:

1. Register the local PDF with `scripts/register-real-basis-document-sample.py`.
2. Generate extraction QA artifacts with `scripts/analyze-real-basis-document-pdf.py`.
3. Run `backend/tests/test_real_basis_document_rag.py` with `RUN_REAL_BASIS_RAG_TESTS=1`.
4. Optionally compare service PDF extraction against an externally extracted TXT, DOCX, or MD with `scripts/compare-real-basis-document-txt.py`; DOCX paragraph and table-cell metadata is included.
5. Regenerate Markdown from the service PDF extraction and compare it with a reference MD using `scripts/regenerate-real-basis-document-md.py`.
