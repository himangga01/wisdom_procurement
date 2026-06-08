# 기준문서 PDF Markdown 재생성 및 비교 구현계획

## 목적

사용자가 업로드하는 기준문서 PDF는 서비스 내부에서 직접 텍스트와 표를 추출한 뒤 RAG 인덱싱에 사용됩니다.

이번 작업은 실제 기준문서 PDF를 우리 로직으로 다시 Markdown 파일로 재생성하고, 사용자가 제공한 기준 MD 파일과 비교해 다음을 확인하기 위한 것입니다.

- PDF 본문 텍스트가 Markdown 재생성 결과에 충분히 포함되는지
- 표가 Markdown 표 형태로 어느 정도 복원되는지
- 사용자가 제공한 MD 기준과 비교했을 때 table-aware extraction 보강이 필요한 지점을 수치화할 수 있는지

## 입력 파일

서비스 재생성 대상:

- `backend/tests/real-basis-document-samples/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf`

비교 기준:

- `C:/Users/HOONJAE/Documents/카카오톡 받은 파일/중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`

## 구현 범위

### 1. PDF -> Markdown 재생성 스크립트

추가 파일:

- `scripts/regenerate-real-basis-document-md.py`

기능:

- manifest 또는 `--pdf`로 PDF 경로를 찾는다.
- 물리 PDF 1쪽은 단일 논리페이지로 처리한다.
- 물리 PDF 2쪽 이후는 좌/우 영역으로 분리해 논리페이지로 처리한다.
- 각 논리페이지마다 다음을 출력한다.
  - PDF 물리 페이지 번호
  - 원문 논리페이지 번호
  - 영역: 전체/좌측/우측
  - 영역 내 텍스트
  - PyMuPDF `find_tables(clip=...)`로 감지한 표를 Markdown 표로 변환한 결과
- 생성 결과를 `backend/tests/real-basis-document-samples/regenerated-basis-document.md`에 저장한다.

### 2. 재생성 MD와 사용자 MD 비교

비교 스크립트 내부에서 기존 `scripts/compare-real-basis-document-txt.py`의 비교 함수를 재사용한다.

비교 지표:

- character count
- compact character count
- token multiset recall
- unique token recall
- char 5-gram recall
- line coverage
- numeric recall
- Markdown table count
- Markdown table row count
- table row coverage

비교 리포트:

- `backend/tests/real-basis-document-samples/md-regeneration-comparison-report.json`

### 3. 테스트 코드

추가 파일:

- `backend/tests/test_real_basis_md_regeneration.py`

검증:

- Markdown table rendering helper가 pipe/newline을 안전하게 처리하는지
- Markdown table row parser가 구분선을 제외하고 row를 계산하는지
- 논리페이지 분할 규칙이 1쪽 전체, 2쪽 이후 좌/우를 반환하는지

## 실행 순서

1. 구현계획 문서 작성
2. `.gitignore`에 생성 MD와 비교 리포트 제외 규칙 추가
3. PDF -> MD 재생성 스크립트 작성
4. 회귀 테스트 작성
5. 실제 기준문서 PDF로 MD 재생성
6. 사용자가 제공한 MD와 비교
7. 결과를 기존 보완 계획과 work-log에 기록

## 성공 기준

- 스크립트가 전체 PDF 489쪽을 처리한다.
- 논리페이지 수가 977쪽에 근접한다.
- 재생성 MD에 텍스트와 Markdown 표가 모두 포함된다.
- 비교 리포트가 생성된다.
- 회귀 테스트와 전체 backend pytest가 통과한다.

## 예상 리스크

- PyMuPDF `find_tables()`는 표가 아닌 짧은 조각도 표로 감지할 수 있다.
- 사용자 MD는 선 기반 표 감지와 좌/우 논리페이지 분리 결과가 포함되어 있어, 현재 서비스 재생성 MD와 완전 일치하지 않을 수 있다.
- 이번 구현은 비교 기준선을 만들기 위한 1차 재생성입니다. 최종 보강은 table-aware extraction pipeline에서 진행해야 합니다.

## 실행 결과

실행 명령:

```powershell
py -3.13 scripts/regenerate-real-basis-document-md.py `
  --reference-md "C:\Users\HOONJAE\Documents\카카오톡 받은 파일\중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md" `
  --strict
```

생성 파일:

- `backend/tests/real-basis-document-samples/regenerated-basis-document.md`
- `backend/tests/real-basis-document-samples/md-regeneration-comparison-report.json`

재생성 결과:

- PDF 물리 페이지 수: 489
- 재생성 논리페이지 수: 977
- 재생성 텍스트 문자 수: 697,837
- 재생성 Markdown 문자 수: 1,635,197
- 감지 표 수: 3,034
- 감지 표 행 수: 11,900
- 재생성 Markdown table count: 3,034
- 재생성 Markdown table row count: 13,390

기준 MD:

- 기준 MD 문자 수: 1,731,919
- 기준 MD table count: 1,928
- 기준 MD table row count: 11,351

비교 결과:

- regenerated token recall in reference: 0.9303
- reference token recall in regenerated: 0.7931
- regenerated char 5-gram recall in reference: 0.8665
- reference char 5-gram recall in regenerated: 0.8171
- regenerated line coverage in reference: 0.7839
- reference line coverage in regenerated: 0.6875
- regenerated numeric recall in reference: 0.9588
- reference numeric recall in regenerated: 0.7368
- regenerated table row coverage in reference: 0.7060
- reference table row coverage in regenerated: 0.7644
- strict 기준 통과

해석:

- 논리페이지 수는 기준 MD와 동일한 977쪽으로 재현됐다.
- 본문/토큰/5-gram 기준 일치도는 plain text 비교보다 더 좋아졌다.
- 표 row coverage는 양방향 70% 이상으로 기준선을 만들 수 있는 수준이다.
- 재생성 표 수가 기준 MD보다 많다. 이는 `find_tables()`가 짧은 제목/고시번호 조각을 표로 과검출하는 현상 때문이다.
- 다음 보강은 표 후보 필터링, 표 bbox 병합, 표 header/row 품질 점수화가 핵심이다.

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

이 문서의 초기 구현은 PyMuPDF `find_tables()` 기반 Markdown 재생성 기준선을 만들기 위한 작업이었습니다.
현재 서비스의 기본 기준문서 PDF reader는 OpenDataLoader 우선 `auto` 모드입니다.

현재 해석:
- `regenerated-basis-document.md`는 PyMuPDF 기반 역사적 baseline 산출물입니다.
- `opendataloader-regenerated-basis-document.md`, `opendataloader-regenerated-basis-document-auto.md`, `opendataloader-regenerated-basis-document-fallback.md`는 OpenDataLoader 교체 이후 QA 산출물입니다.
- 현재 RAG table 품질 판단은 exact row 문자열 일치보다 table-row token coverage를 우선합니다.
- PyMuPDF는 fallback과 OCR 렌더링 보조 엔진으로 유지됩니다.
- 최신 PDF/RAG 회귀 기준선은 전체 backend `134 passed`, `8 skipped`입니다.

---

# AI / Engineering Version (English)

## Current Code Update
Last updated: 2026-06-07

The initial implementation in this document generated a PyMuPDF `find_tables()` Markdown baseline.
The current service default basis PDF reader is OpenDataLoader-first `auto` mode.

Interpretation:
- `regenerated-basis-document.md` is a historical PyMuPDF baseline artifact.
- `opendataloader-regenerated-basis-document.md`, `opendataloader-regenerated-basis-document-auto.md`, and `opendataloader-regenerated-basis-document-fallback.md` are post-replacement QA artifacts.
- Current table-quality evaluation prioritizes table-row token coverage over exact row-string matching.
- PyMuPDF remains fallback and OCR rendering helper.
- Latest PDF/RAG backend baseline: `134 passed`, `8 skipped`.

## Purpose

Regenerate a Markdown artifact from the real basis-document PDF using service-side extraction logic and compare it against the user-provided Markdown reference.

The goal is to measure RAG extraction gaps, especially table structure preservation.

## Inputs

Service source:

- real basis-document PDF sample under `backend/tests/real-basis-document-samples/`

Reference:

- user-provided `중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md`

## Implementation

Add:

- `scripts/regenerate-real-basis-document-md.py`
- `backend/tests/test_real_basis_md_regeneration.py`

The script:

- loads the PDF from manifest or `--pdf`
- treats physical page 1 as one logical page
- splits physical pages 2+ into left/right logical pages
- extracts clipped text per logical page
- uses PyMuPDF `find_tables(clip=...)` per logical page
- renders detected tables as Markdown tables
- writes `regenerated-basis-document.md`
- compares against the reference MD and writes `md-regeneration-comparison-report.json`

## Metrics

- character and compact-character counts
- token recall
- char n-gram recall
- line coverage
- numeric recall
- Markdown table count
- Markdown table row count
- table row coverage

## Acceptance

- full PDF is processed
- about 977 logical pages are generated
- regenerated Markdown includes both text and tables
- comparison report is generated
- targeted and backend tests pass

## Execution Result

Generated files:

- `backend/tests/real-basis-document-samples/regenerated-basis-document.md`
- `backend/tests/real-basis-document-samples/md-regeneration-comparison-report.json`

Result:

- physical pages: 489
- logical pages: 977
- regenerated text characters: 697,837
- regenerated Markdown characters: 1,635,197
- detected tables: 3,034
- detected table rows: 11,900
- regenerated Markdown table count: 3,034
- regenerated Markdown table rows: 13,390
- reference MD characters: 1,731,919
- reference MD table count: 1,928
- reference MD table rows: 11,351
- regenerated token recall in reference: 0.9303
- reference token recall in regenerated: 0.7931
- regenerated char 5-gram recall in reference: 0.8665
- reference char 5-gram recall in regenerated: 0.8171
- regenerated table row coverage in reference: 0.7060
- reference table row coverage in regenerated: 0.7644
- strict thresholds passed

Interpretation:

- logical page regeneration matches the reference MD count exactly.
- Markdown regeneration improves similarity compared with plain text-only extraction.
- table row coverage is good enough as a baseline but not yet final quality.
- PyMuPDF `find_tables()` over-detects some short text fragments as tables, so table candidate filtering and row quality scoring are the next improvements.
