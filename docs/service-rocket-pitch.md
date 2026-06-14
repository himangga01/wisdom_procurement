# SMART 조달청 계산기 Rocket Pitch

# 한국어 버전

## 문서 목적
이 문서는 비개발자 청중에게 `SMART 조달청 계산기`를 쉽고 설득력 있게 소개하기 위한 발표용 설명 문서입니다.

기술 구조를 설명하기보다 다음 흐름으로 서비스를 이해시키는 데 초점을 둡니다.

```text
문제 제기 -> 해결 방법 -> 제품 시연 -> 사용 요청
```

## 한 줄 소개
`SMART 조달청 계산기`는 나라장터 공고, 법인 증빙자료, 기준문서를 한 곳에 모아 조달 참여 준비에 필요한 부족조건과 필요서류를 빠르게 확인하도록 돕는 로컬 실행형 AI 업무 포탈입니다.

## 30초 Rocket Pitch
조달 업무에서 가장 오래 걸리는 일은 공고문, 첨부파일, 법인 증빙자료, 기준문서를 따로 열어 보며 “우리 법인이 지금 무엇이 부족한가”를 확인하는 과정입니다.

`SMART 조달청 계산기`는 나라장터 공고를 저장하고, 첨부 PDF/DOCX를 자동 분석하며, 법인 증빙자료와 기준문서를 함께 비교해 부족조건, 필요서류, 준비 가이드를 보여줍니다.

이 서비스는 최종 합격을 단정하는 도구가 아니라, 담당자가 더 빠르고 안전하게 검토할 수 있도록 근거와 확인이 필요한 항목을 정리해 주는 조달 업무 보조 포탈입니다.

## 발표 대상
- 조달 업무를 검토하는 행정사
- 법인 입찰 준비 담당자
- 공고문과 증빙자료를 반복 확인하는 내부 실무자
- 조달 업무 자동화를 검토하는 의사결정자

## 1. 문제 제기

### 문제 1. 공고문과 첨부파일이 너무 많고 형식이 제각각입니다
나라장터 공고에는 본문, 첨부 PDF, DOCX, 표, 금액, 마감일, 면허 제한, 지역 제한이 섞여 있습니다.

담당자는 공고마다 파일을 내려받고, 중요한 조건을 다시 찾아보고, 누락된 제출서류가 없는지 수작업으로 확인해야 합니다.

### 문제 2. 법인 정보와 증빙자료가 따로 관리됩니다
사업자등록증, 중소기업확인서, 직접생산확인증명서, 면허증, 실적증명서, 신용평가서 같은 자료는 입찰 검토에 중요하지만 대부분 파일 단위로 흩어져 있습니다.

결과적으로 “이 법인이 해당 공고를 준비할 수 있는 상태인가”를 판단하려면 여러 문서와 메모를 동시에 봐야 합니다.

### 문제 3. 기준문서는 표와 조항이 많아 근거 확인이 어렵습니다
직접생산 확인기준 같은 기준문서는 페이지 수가 많고 표가 많습니다.

특정 제품, 세부품명, 설비, 인력, 생산공정 조건을 찾기 위해 긴 PDF를 반복 검색해야 하며, 조건을 찾더라도 어느 근거를 기준으로 판단했는지 정리하기 어렵습니다.

### 문제 4. 계약서 초안 작성도 반복 업무입니다
공고와 법인 정보가 이미 정리되어 있어도 계약서 초안을 다시 작성하려면 공고번호, 계약금액, 계약기간, 법인 기본정보를 사람이 옮겨 적어야 합니다.

이 과정에서 누락이나 오타가 생길 수 있고, 검토용 초안을 만드는 데도 시간이 듭니다.

### 문제 5. 운영 중 실패와 이력을 추적하기 어렵습니다
문서 분석, 첨부 다운로드, AI 요약, OCR, 기준문서 인덱싱 같은 작업은 실패할 수 있습니다.

실무에서는 “어떤 작업이 실패했는지”, “다시 실행해야 하는지”, “백업은 정상인지”를 볼 수 있어야 합니다.

## 2. 해결 방법

### 해결 1. 나라장터 공고를 검색하고 저장합니다
사용자는 나라장터 공고를 검색하고, 필요한 공고를 저장할 수 있습니다.

저장된 공고는 내부 게시판처럼 다시 볼 수 있으며, 공고 첨부 PDF/DOCX는 자동으로 내려받아 분석합니다.

### 해결 2. 문서 내용을 자동으로 읽고 정리합니다
서비스는 PDF와 DOCX 문서에서 텍스트와 표 내용을 추출합니다.

PDF는 OpenDataLoader 기반 추출을 우선 사용하고, 필요한 경우 PyMuPDF와 OCR을 보조로 사용합니다.

비개발자 관점에서는 다음처럼 이해하면 됩니다.

```text
파일 업로드 또는 공고 저장
-> 문서 내용 읽기
-> 표와 주요 문장 추출
-> AI 요약과 구조화 결과 생성
-> 화면에서 검토
```

### 해결 3. 법인 증빙자료를 업로드하고 필요한 값만 반영합니다
법인 증빙자료를 업로드하면 서비스가 문서 유형과 주요 값을 자동 추출합니다.

다만 추출 결과를 바로 확정하지 않고, 사용자가 확인한 값만 법인 프로필에 반영합니다.

이 방식은 OCR이나 AI가 틀린 값을 법인 정보에 덮어쓰는 위험을 줄입니다.

### 해결 4. 기준문서를 지식 자산으로 바꿉니다
기준문서 PDF를 업로드하면 서비스가 텍스트 추출, OCR, 청킹, 인덱싱을 자동으로 처리합니다.

이후 공고 요구조건이나 법인 준비 상태를 검토할 때 기준문서의 관련 조항과 표를 빠르게 찾는 데 활용합니다.

핵심은 사용자가 직접 기준문서를 쪼개거나 검색 인덱스를 만들 필요가 없다는 점입니다.

### 해결 5. 최종 판정이 아니라 부족조건 중심으로 보여줍니다
서비스는 “지원 가능”을 쉽게 단정하지 않습니다.

대신 다음 정보를 중심으로 보여줍니다.

- 현재 준비된 조건
- 부족한 조건
- 추가 확인이 필요한 조건
- 필요한 제출서류
- 기준문서 근거 상태
- 다음 준비 가이드

이 접근은 실무자가 최종 판단을 더 빠르게 검토하도록 돕는 방식입니다.

### 해결 6. 계약서 DOCX 초안을 생성합니다
저장된 공고와 법인 기본정보를 기준으로 `용역표준계약서` 형식의 DOCX 초안을 생성합니다.

생성된 계약서는 바로 확정 문서가 아니라, 관리자가 검토하고 수정하기 위한 초안입니다.

### 해결 7. 운영 대시보드와 이력으로 관리합니다
서비스는 운영 대시보드, 작업 이력, 실패 관리, 백업/검증/복원계획 화면을 제공합니다.

따라서 단순 분석 도구가 아니라, 실제 운영 중 상태를 추적할 수 있는 업무 포탈로 사용할 수 있습니다.

## 3. 제품 시연 흐름

### 시연 목표
청중이 “이 서비스가 실제 조달 검토 시간을 어떻게 줄이는지”를 화면 흐름으로 이해하게 만드는 것이 목표입니다.

### 시연 1. 법인을 등록하고 증빙자료를 준비합니다
법인 관리 화면에서 법인을 등록하고, 사업자등록증, 확인서, 면허증, 실적증명서 등 증빙자료를 업로드합니다.

서비스는 문서 유형과 주요 값을 추출하고, 사용자는 반영할 값만 선택합니다.

발표 멘트:

```text
조달 검토는 먼저 우리 법인의 기본정보와 증빙자료가 준비되어 있어야 합니다.
서비스는 증빙자료에서 값을 가져오고, 사용자가 확인한 값만 법인 프로필에 반영합니다.
```

### 시연 2. 대시보드에서 오늘 확인할 업무를 봅니다
첫 화면에서 최근 공고, 최근 문서, 법인 준비 상태, 처리 상태, 운영 상태를 확인합니다.

발표 멘트:

```text
법인과 문서를 등록한 뒤에는 대시보드에서 현재 업무 상태를 봅니다.
오늘 어떤 공고와 문서를 먼저 확인해야 하는지 바로 알 수 있습니다.
```

### 시연 3. 나라장터 공고를 검색하고 저장합니다
나라장터 공고 검색 화면에서 공고를 조회하고, 필요한 공고를 선택해 저장합니다.

저장 후 첨부파일 다운로드와 분석이 이어집니다.

발표 멘트:

```text
나라장터에서 공고를 찾은 뒤 다시 파일을 따로 정리하지 않아도 됩니다.
저장한 공고는 내부 검토 대상이 되고, 첨부 문서는 자동으로 분석됩니다.
```

### 시연 4. 저장한 공고의 요구조건 후보를 확인합니다
저장 공고 상세 화면에서 지역, 면허, 기업유형, 제출서류, 금액, 마감일 같은 요구조건 후보를 확인합니다.

발표 멘트:

```text
공고문에서 사람이 놓치기 쉬운 요구조건을 먼저 후보로 뽑아 보여줍니다.
담당자는 원문과 결과를 비교하면서 빠르게 확인할 수 있습니다.
```

### 시연 5. 기준문서를 업로드하고 검색 가능한 지식으로 만듭니다
기준문서 관리 화면에서 기준문서 PDF를 업로드합니다.

서비스는 문서 추출, OCR, 청크 생성, 인덱싱 상태를 보여줍니다.

발표 멘트:

```text
직접생산 확인기준처럼 긴 기준문서를 단순 파일로 보관하지 않고, 검색 가능한 기준 지식으로 바꿉니다.
표가 많거나 페이지가 긴 문서도 처리 상태를 보면서 관리할 수 있습니다.
```

### 시연 6. 공고와 법인을 비교해 부족조건을 확인합니다
부족조건 미리보기 또는 판단 검토 화면에서 저장 공고와 법인을 선택합니다.

서비스는 준비된 항목, 부족한 항목, 확인이 필요한 항목, 기준문서 근거 상태를 보여줍니다.

발표 멘트:

```text
이 화면의 목적은 합격을 단정하는 것이 아닙니다.
지금 무엇이 부족하고, 어떤 서류와 근거를 더 확인해야 하는지 알려주는 것입니다.
```

### 시연 7. 계약서 초안을 생성합니다
계약서 생성 화면에서 저장 공고와 법인을 선택하고, 필요한 입력값을 확인한 뒤 DOCX 초안을 생성합니다.

발표 멘트:

```text
공고와 법인 정보가 이미 정리되어 있으므로, 반복 입력을 줄이고 검토용 계약서 초안을 빠르게 만들 수 있습니다.
최종 계약서는 반드시 관리자가 검토합니다.
```

### 시연 8. 운영 상태와 실패 이력을 확인합니다
운영 대시보드와 작업 이력 화면에서 분석 성공/실패, 재시도, 백업 상태를 확인합니다.

발표 멘트:

```text
AI 기능은 결과만큼 운영 상태도 중요합니다.
어떤 작업이 실패했는지, 다시 실행해야 하는지, 백업은 정상인지 관리자가 볼 수 있습니다.
```

## 4. 사용 요청

### 요청 1. 실제 업무 샘플로 검증해 주세요
서비스 품질은 실제 공고와 실제 증빙자료에서 확인해야 합니다.

검증에 필요한 샘플:

- 최근 나라장터 공고 5~10건
- 공고 첨부 PDF/DOCX
- 실제 기준문서 PDF
- 사업자등록증, 확인서, 면허증, 실적증명서 등 법인 증빙자료 샘플
- 기존에 사람이 정리한 체크리스트나 검토 결과

### 요청 2. 추출 결과가 맞는지 업무 담당자가 확인해 주세요
AI가 뽑은 결과는 담당자의 업무 기준과 비교해야 합니다.

확인할 항목:

- 공고 요구조건이 맞게 추출되었는지
- 제출서류가 빠지지 않았는지
- 법인 증빙자료 값이 올바른지
- 기준문서 근거가 실무 판단에 쓸 수 있는지
- 계약서 초안에 필요한 항목이 충분한지

### 요청 3. “자동 확정”보다 “검토 속도 향상” 기준으로 평가해 주세요
이 서비스는 담당자의 판단을 대체하는 도구가 아닙니다.

평가 기준은 다음이 적합합니다.

- 공고 검토 시간이 줄었는가
- 요구조건 누락 가능성이 줄었는가
- 증빙자료 확인이 쉬워졌는가
- 기준문서 근거를 찾는 시간이 줄었는가
- 계약서 초안 작성 시간이 줄었는가
- 실패 이력과 백업 상태를 관리자가 이해할 수 있는가

### 요청 4. 시범 운영 담당자를 정해 주세요
실제 운영에서 좋은 결과를 내려면 한 명 이상의 업무 담당자가 다음 역할을 맡아야 합니다.

- 공고 샘플 선정
- 법인 증빙자료 샘플 제공
- 추출 결과 검토
- 화면 용어 피드백
- 계약서 초안 항목 검토
- 우선 개선사항 정리

## 핵심 메시지
`SMART 조달청 계산기`는 조달 업무를 완전 자동으로 끝내는 기계가 아닙니다.

대신 공고, 첨부파일, 법인 증빙자료, 기준문서를 한 흐름으로 묶어 담당자가 더 빠르게 검토하고, 부족조건과 필요서류를 더 명확하게 확인하도록 돕는 업무 보조 포탈입니다.

## 청중에게 남길 마지막 문장
“이 서비스의 목표는 판단을 대신하는 것이 아니라, 조달 검토자가 놓치기 쉬운 조건과 서류를 더 빨리 발견하도록 돕는 것입니다.”

## 참고한 내부 문서
- `README.md`
- `docs/technical-design.md`
- `docs/ux-design.md`
- `docs/technology-summary.md`
- `docs/ai-api-setup.md`
- `docs/narajangteo-api-analysis.md`
- `docs/narajangteo-board-design.md`
- `docs/eligibility-rag-implementation-plan.md`
- `docs/ngrok-external-access-and-contract-docx-plan.md`
- `docs/work-log.md`

---

# AI / Engineering Version (English)

## Purpose
This document is a non-developer-facing rocket pitch for `SMART Procurement Calculator`.

It intentionally avoids implementation-heavy explanations and frames the product through:

```text
Problem -> Solution -> Product Demo -> Usage Request
```

## One-Liner
`SMART Procurement Calculator` is a local-first AI operations portal that helps procurement reviewers collect Nara notices, analyze attachments, manage corporation evidence, search basis documents, identify missing requirements, and generate review-only contract DOCX drafts.

## Product Positioning
- Not an automatic final eligibility verdict engine.
- Not a replacement for expert review.
- A workflow assistant that reduces manual document checking time.
- A local-first admin portal for a single operator, with ngrok-based demo/external access support.

## Current Product Capabilities Reflected
- Nara public API notice search, save, attachment download, and analysis.
- PDF/DOCX extraction using the shared document extraction pipeline.
- Corporation evidence upload, extraction, review, and profile enrichment.
- Basis PDF ingestion, OCR, chunking, JSON basis index, retrieval, and citation readiness.
- Gap-first judgment outputs: prepared, missing, uncertain, needs review, citation status.
- Operations dashboard, operation runs, failure tracking, backup validation, and restore dry-run.
- Contract DOCX draft generation from saved notice and corporation data.

## Demo Flow
1. Corporation registration/evidence: create a corporation profile and approve extracted fields.
2. Dashboard: show work queue, corporation readiness, and processing status.
3. Nara search: find and save a notice.
4. Saved notice detail: review extracted requirements.
5. Basis document: upload basis PDF and show processing/search readiness.
6. Notice comparison/judgment: show missing requirements and citation status.
7. Contract generation: create a review-only DOCX draft.
8. Operations: show failures, retries, backups, and external access status.

## Usage Ask
- Provide real notice and evidence samples.
- Review extraction results with domain experts.
- Evaluate the product by review-time reduction and missed-condition reduction, not by fully automated final decisions.
- Assign a pilot operator who can provide terminology and workflow feedback.
