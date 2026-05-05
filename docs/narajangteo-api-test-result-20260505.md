# 한국어 버전

## 문서 목적
이 문서는 공공데이터포털 인증키를 사용하여 `2026-05-05` 기준 나라장터 API를 실제 호출한 결과와, 우리 서비스에서의 활용 가능성을 정리합니다.

실행 스크립트:
- `scripts/test-nara-api.py`

상세 결과 JSON:
- `temp/nara-api-test-20260505-latest.json`

주의:
- 실제 인증키 값은 문서에 기록하지 않았습니다.
- 테스트는 `NARA_API_SERVICE_KEY` 환경변수로 키를 주입하여 실행했습니다.

## 테스트 조건
| 항목 | 값 |
|---|---|
| 기준 날짜 | `2026-05-05` |
| 조회 시작 | `202605050000` |
| 조회 종료 | `202605052359` |
| 응답 형식 | `json` |
| 페이지 크기 | `10` |
| 주요 대상 | 공사 공고 |

## 테스트 결과 요약
모든 테스트 대상 API가 HTTP 200과 API 결과코드 `00`으로 정상 응답했습니다.

| 테스트 | Operation | 결과 | totalCount | itemCount | 첨부 수 |
|---|---|---:|---:|---:|---:|
| 공사 공고 검색 | `getBidPblancListInfoCnstwkPPSSrch` | 정상 | 23 | 10 | 39 |
| 공사 공고 목록 | `getBidPblancListInfoCnstwk` | 정상 | 23 | 10 | 39 |
| 공사 기초금액 | `getBidPblancListInfoCnstwkBsisAmount` | 정상 | 31 | 10 | 0 |
| 면허제한 | `getBidPblancListInfoLicenseLimit` | 정상 | 42 | 10 | 0 |
| 참가가능지역 | `getBidPblancListInfoPrtcptPsblRgn` | 정상 | 31 | 10 | 0 |
| e발주 첨부파일 | `getBidPblancListInfoEorderAtchFileInfo` | 정상 | 0 | 0 | 0 |
| 표준 입찰공고정보 | `getDataSetOpnStdBidPblancInfo` | 정상 | 44 | 10 | 0 |

## 대표 공고 샘플
공사 공고 검색 결과의 첫 번째 공고:

| 필드 | 값 |
|---|---|
| 입찰공고번호 | `R26BK01503422` |
| 입찰공고차수 | `000` |
| 공고명 | `2025년 중랑교 외 1개소 보수공사` |
| 공고기관 | `서울특별시` |
| 수요기관 | `서울특별시 도로사업소 성동도로사업소` |
| 입찰공고일시 | `2026-05-05 06:32:29` |
| 입찰개시 | `2026-05-08 10:00:00` |
| 입찰마감 | `2026-05-12 12:00:00` |
| 개찰일시 | `2026-05-12 13:00:00` |
| 추정가격 | `230,860,000` |
| 예산금액 | `253,946,000` |
| 업종제한여부 | `Y` |
| 공사현장지역 | `서울특별시` |

## 상세 조회 결과
대표 공고 `R26BK01503422 / 000`에 대해 공고번호 기준 상세 API를 다시 호출했습니다.

| API | 결과 | 확인 내용 |
|---|---|---|
| 공고 상세 | 정상 | 공고 메타데이터 1건 조회 |
| 기초금액 | 정상 | `253,946,000` |
| 면허제한 | 정상 | 3건 조회 |
| 참가가능지역 | 정상 | `서울특별시` |
| e발주 첨부파일 | 정상 | 0건 |

대표 면허제한:
- `지반조성ㆍ포장공사업/4989`
- `금속창호ㆍ지붕건축물조립공사업/4991`

## 첨부파일 확인
공사 공고 검색 응답 10건에서 첨부파일은 총 39개 확인되었습니다.

| 구분 | 개수 |
|---|---:|
| 전체 첨부 | 39 |
| 지원 가능 첨부(PDF/DOCX) | 14 |
| 지원 제외 첨부(HWP/HWPX/XLSX 등) | 25 |

대표 지원 가능 첨부:
- `1.입찰공고문(재공고).pdf`
- `공고문_2026_747_[범화리 농로아스콘 포장공사].pdf`
- `공고문_2026_746_[민주지산자연휴양림 시설(도로)보수공사].pdf`

대표 지원 제외 첨부:
- `1.입찰공고문(재공고).hwpx`
- `15. 물량내역서(입찰공고용).xlsx`
- `4. 공사시방서(중랑교 외 1개소 보수공사).hwpx`

## 첨부 PDF 다운로드 검증
첫 번째 지원 가능 PDF 첨부를 실제 요청했습니다.

| 항목 | 결과 |
|---|---|
| 파일명 | `1.입찰공고문(재공고).pdf` |
| HTTP 상태 | `200` |
| Content-Type | `application/pdf` |
| PDF 시그니처 | `%PDF` 확인 |
| 다운로드 바이트 | `510,526` bytes |
| 자동 스크립트 기록 | `download_test.success=true` |

결론:
- 나라장터 API 응답의 첨부 URL로 PDF 다운로드가 가능합니다.
- 이 PDF를 기존 `PyMuPDF` 분석 파이프라인에 바로 연결할 수 있습니다.
- 현재 `scripts/test-nara-api.py`는 첫 번째 지원 가능 PDF/DOCX 첨부를 자동으로 내려받아 HTTP 상태, Content-Type, 다운로드 바이트, 파일 시그니처를 결과 JSON에 기록합니다.

## 우리 기능에 활용 가능한 방식

### 1. 공고 검색 대시보드
`getBidPblancListInfoCnstwkPPSSrch`를 사용하면 포탈에서 나라장터 공사 공고를 검색할 수 있습니다.

활용 필터:
- 기간
- 공고명
- 공고기관
- 수요기관
- 지역
- 업종
- 추정가격 범위
- 입찰마감 제외 여부

### 2. 공고 저장 모델
`bidNtceNo + bidNtceOrd`를 고유키로 사용하면 됩니다.

저장 추천 필드:
- 공고번호/차수
- 공고명
- 공고기관/수요기관
- 입찰공고일시
- 입찰개시/마감/개찰일시
- 추정가격/예산금액/기초금액
- 업종제한여부
- 공사현장지역
- 원문 상세 URL
- 원본 API JSON

### 3. 첨부파일 수집
`ntceSpecDocUrl1..10`, `ntceSpecFileNm1..10`, `stdNtceDocUrl`을 수집하면 됩니다.

처리 정책:
- `.pdf`, `.docx`: 다운로드 후 분석
- `.hwp`, `.hwpx`, `.xlsx`: 다운로드하지 않고 지원 제외 메타데이터로 저장
- 동일 URL/파일명 중복 제거 필요

### 4. 기존 분석 파이프라인 연결
다운로드한 PDF/DOCX는 현재 구현된 흐름을 재사용할 수 있습니다.

```text
나라장터 첨부파일 다운로드
-> project_documents 또는 notice_documents 저장
-> PyMuPDF/python-docx 텍스트 추출
-> GPT-5.1 요약 또는 fallback 요약
-> 분석 결과 저장
```

### 5. 향후 자격 판단 데이터
아래 API는 Phase 3 자격 판단에 직접 활용 가능합니다.

- `getBidPblancListInfoLicenseLimit`: 면허/업종 제한
- `getBidPblancListInfoPrtcptPsblRgn`: 참가 가능 지역
- `getBidPblancListInfoCnstwkBsisAmount`: 기초금액

## 구현 판단
Phase 1.5로 구현 가능한 범위:
- 나라장터 API 키 설정
- 공사 공고 검색
- 공고 메타데이터 저장
- 첨부파일 목록 저장
- PDF/DOCX 다운로드
- 기존 분석 파이프라인 연결

아직 제외할 범위:
- HWP/HWPX 변환
- XLSX 분석
- 최종 지원 가능/불가능 판단
- 기준문서 RAG 판단
- 낙찰/계약 이력 분석

---

# AI / Engineering Version (English)

## Purpose
This document records real Nara Marketplace API test results for `2026-05-05` and maps the responses to SMART Procurement Calculator features.

Script:
- `scripts/test-nara-api.py`

Detailed JSON:
- `temp/nara-api-test-20260505-214831.json`

The actual API key is intentionally omitted from this document.

## Test Conditions
- Date: `2026-05-05`
- Start datetime: `202605050000`
- End datetime: `202605052359`
- Response format: `json`
- Page size: `10`
- Main target: construction notices

## Result Summary
All tested APIs returned HTTP 200 and API result code `00`.

| Test | Operation | Status | totalCount | itemCount | attachments |
|---|---|---:|---:|---:|---:|
| Construction search | `getBidPblancListInfoCnstwkPPSSrch` | OK | 23 | 10 | 39 |
| Construction list | `getBidPblancListInfoCnstwk` | OK | 23 | 10 | 39 |
| Basis amount | `getBidPblancListInfoCnstwkBsisAmount` | OK | 31 | 10 | 0 |
| License limit | `getBidPblancListInfoLicenseLimit` | OK | 42 | 10 | 0 |
| Eligible region | `getBidPblancListInfoPrtcptPsblRgn` | OK | 31 | 10 | 0 |
| e-order attachments | `getBidPblancListInfoEorderAtchFileInfo` | OK | 0 | 0 | 0 |
| Standard bid notice | `getDataSetOpnStdBidPblancInfo` | OK | 44 | 10 | 0 |

## Representative Notice
- Notice number: `R26BK01503422`
- Notice order: `000`
- Title: `2025년 중랑교 외 1개소 보수공사`
- Notice institution: `서울특별시`
- Demand institution: `서울특별시 도로사업소 성동도로사업소`
- Notice datetime: `2026-05-05 06:32:29`
- Bid begin: `2026-05-08 10:00:00`
- Bid close: `2026-05-12 12:00:00`
- Opening datetime: `2026-05-12 13:00:00`
- Estimated price: `230,860,000`
- Budget amount: `253,946,000`
- Industry limit: `Y`
- Site region: `서울특별시`

## Detail API Results
For `R26BK01503422 / 000`:
- Notice detail: 1 item
- Basis amount: `253,946,000`
- License limits: 3 items
- Eligible region: `서울특별시`
- e-order attachments: 0 items

Sample license limits:
- `지반조성ㆍ포장공사업/4989`
- `금속창호ㆍ지붕건축물조립공사업/4991`

## Attachment Findings
From the first 10 construction notices:
- Total attachments: 39
- Supported attachments: 14 PDF/DOCX candidates
- Unsupported attachments: 25 HWP/HWPX/XLSX/etc.

The first supported PDF download was tested:
- Filename: `1.입찰공고문(재공고).pdf`
- HTTP status: `200`
- Content-Type: `application/pdf`
- PDF signature: valid `%PDF`
- Downloaded bytes: `510,526`
- Script result: `download_test.success=true`

## Product Usage
Use `getBidPblancListInfoCnstwkPPSSrch` for the portal search screen.

Persist notices using:
- `bidNtceNo + bidNtceOrd` as unique key
- title, institutions, dates, amounts, eligibility hints, detail URL, raw JSON

Persist attachments using:
- URL, file name, source field, extension, support status, download status

Download policy:
- PDF/DOCX: download and analyze
- HWP/HWPX/XLSX: store metadata only, mark unsupported

Reuse existing analysis pipeline:

```text
download attachment
-> save as document
-> PyMuPDF/python-docx extraction
-> GPT/fallback summary
-> persist analysis result
```

Future eligibility inputs:
- `getBidPblancListInfoLicenseLimit`
- `getBidPblancListInfoPrtcptPsblRgn`
- `getBidPblancListInfoCnstwkBsisAmount`
