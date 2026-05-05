# 한국어 버전

## 문서 목적
이 문서는 `source/api_doc` 폴더의 나라장터 API 문서를 분석하여, `SMART 조달청 계산기`에 나라장터 공고 자동 조회 기능을 추가하기 위한 API 이해 내용을 정리합니다.

분석 대상 파일:
- `source/api_doc/조달청_OpenAPI참고자료_나라장터_입찰공고정보서비스_1.2.docx`
- `source/api_doc/조달청_OpenAPI참고자료_나라장터_공공데이터개방표준서비스_1.2.docx`
- `source/api_doc/api 에러 코드.txt`

## 결론
우리 서비스의 다음 구현에서는 `나라장터 입찰공고정보서비스(BidPublicInfoService)`를 우선 사용하면 됩니다.

특히 현재 사용자가 직접 PDF/DOCX 공고문을 업로드하는 구조를 확장하려면 아래 흐름이 가장 현실적입니다.

```text
나라장터 API로 공고 목록 조회
-> 공고 메타데이터 저장
-> 공고 첨부파일 URL 수집
-> PDF/DOCX만 다운로드
-> 기존 PyMuPDF/DOCX 파싱
-> 기존 AI 요약 파이프라인 재사용
```

## 핵심 서비스 1: 나라장터 입찰공고정보서비스

### 서비스 기본 정보
- 서비스 ID: `BidPublicInfoService`
- 기본 URL: `https://apis.data.go.kr/1230000/ad/BidPublicInfoService`
- 방식: REST GET
- 인증: 공공데이터포털 `ServiceKey`
- 응답 형식: XML 기본, `type=json` 지정 시 JSON 가능
- 데이터 갱신: 수시

### 공통 요청 파라미터
| 파라미터 | 의미 | 필수 | 비고 |
|---|---:|---:|---|
| `ServiceKey` | 공공데이터포털 인증키 | 필수 | URL 인코딩 이슈 주의 |
| `numOfRows` | 페이지당 결과 수 | 필수 | 예: `10` |
| `pageNo` | 페이지 번호 | 필수 | 예: `1` |
| `type` | 응답 타입 | 선택 | JSON 사용 시 `json` |
| `inqryDiv` | 조회구분 | 필수 | API별 의미가 조금 다름 |
| `inqryBgnDt` | 조회 시작일시 | 조건부 | `YYYYMMDDHHMM` |
| `inqryEndDt` | 조회 종료일시 | 조건부 | `YYYYMMDDHHMM` |
| `bidNtceNo` | 입찰공고번호 | 조건부 | 공고번호 직접 조회 시 사용 |
| `bidNtceOrd` | 입찰공고차수 | 일부 API 조건부 | 보통 `000` |

## 우선 구현 대상 API

### 1. 공사 공고 목록 조회
- Operation: `getBidPblancListInfoCnstwk`
- 용도: 공사 입찰공고 목록 조회
- 조회 방식:
  - `inqryDiv=1`: 등록일시 기준
  - `inqryDiv=2`: 입찰공고번호 기준
  - `inqryDiv=3`: 변경일시 기준
- 우리 서비스에서의 용도:
  - 최신 공고 동기화
  - 특정 공고번호로 상세 재조회
  - 변경 공고 감지

### 2. 나라장터 검색조건 기반 공사 공고 조회
- Operation: `getBidPblancListInfoCnstwkPPSSrch`
- 용도: 나라장터 검색조건 기반 공사 공고 조회
- 조회 방식:
  - `inqryDiv=1`: 공고게시일시 기준
  - `inqryDiv=2`: 개찰일시 기준
- 주요 검색 조건:
  - `bidNtceNm`: 입찰공고명
  - `ntceInsttNm`: 공고기관명
  - `dminsttNm`: 수요기관명
  - `prtcptLmtRgnCd`: 참가제한지역코드
  - `prtcptLmtRgnNm`: 참가제한지역명
  - `indstrytyCd`: 업종코드
  - `indstrytyNm`: 업종명
  - `presmptPrceBgn`: 추정가격 시작
  - `presmptPrceEnd`: 추정가격 종료
  - `bidClseExcpYn`: 입찰마감 제외 여부
- 우리 서비스에서의 용도:
  - 포탈의 “나라장터 공고 검색” 화면에 가장 적합
  - 지역/업종/금액/키워드 필터를 UI로 제공하기 좋음

### 3. 공사 기초금액 조회
- Operation: `getBidPblancListInfoCnstwkBsisAmount`
- 용도: 공사 공고의 기초금액 조회
- 주요 응답:
  - `bidNtceNo`: 입찰공고번호
  - `bidNtceOrd`: 입찰공고차수
  - `bidNtceNm`: 입찰공고명
  - `bssamt`: 기초금액
- 우리 서비스에서의 용도:
  - 공고 카드/상세 화면에서 기초금액 보강
  - AI 요약 전 구조화 메타데이터로 활용

### 4. 면허제한정보 조회
- Operation: `getBidPblancListInfoLicenseLimit`
- 용도: 공고별 면허/업종 제한 조회
- 주요 응답:
  - `lcnsLmtNm`: 면허제한명
  - `permsnIndstrytyList`: 허용업종목록
  - `indstrytyMfrcFldList`: 주력업종분야목록
- 우리 서비스에서의 용도:
  - Phase 3 자격 판단의 핵심 데이터
  - Phase 1/2에서는 상세 정보 저장까지만 권장

### 5. 참가가능지역정보 조회
- Operation: `getBidPblancListInfoPrtcptPsblRgn`
- 용도: 공고별 참가 가능 지역 조회
- 주요 응답:
  - `prtcptPsblRgnNm`: 참가가능지역명
  - `bsnsDivNm`: 업무구분명
- 우리 서비스에서의 용도:
  - 법인 소재지와 공고 지역 제한 비교의 기반
  - Phase 3 자격 판단에서 중요

### 6. e발주 첨부파일정보 조회
- Operation: `getBidPblancListInfoEorderAtchFileInfo`
- 용도: e발주 첨부파일 조회
- 주요 응답:
  - `eorderDocDivNm`: e발주문서구분명
  - `eorderAtchFileNm`: e발주첨부파일명
  - `eorderAtchFileUrl`: e발주첨부파일URL
- 우리 서비스에서의 용도:
  - 일반 공고규격서 URL 외에 e발주 첨부파일까지 수집할 때 사용

## 공고 목록 응답에서 중요한 필드
| 필드 | 의미 | 활용 |
|---|---|---|
| `bidNtceNo` | 입찰공고번호 | 공고 고유키 |
| `bidNtceOrd` | 입찰공고차수 | 공고 버전/차수 |
| `bidNtceNm` | 입찰공고명 | 화면 제목, 검색 |
| `ntceInsttNm` | 공고기관명 | 기관 필터 |
| `dminsttNm` | 수요기관명 | 기관 필터 |
| `bidNtceDt` | 입찰공고일시 | 최신순 정렬 |
| `bidBeginDt` | 입찰개시일시 | 일정 표시 |
| `bidClseDt` | 입찰마감일시 | 중요 일정 |
| `opengDt` | 개찰일시 | 중요 일정 |
| `bidQlfctRgstDt` | 입찰참가자격등록마감일시 | 준비 체크리스트 |
| `cntrctCnclsMthdNm` | 계약체결방법명 | 수의계약/제한경쟁 등 |
| `presmptPrce` | 추정가격 | 금액 필터 |
| `bdgtAmt` | 예산금액 | 금액 표시 |
| `VAT` | 부가가치세 | 금액 계산 |
| `sucsfbidLwltRate` | 낙찰하한율 | 분석 요약 |
| `indstrytyLmtYn` | 업종제한여부 | 자격 판단 후보 |
| `cnstrtsiteRgnNm` | 공사현장지역명 | 지역 판단 후보 |
| `bidNtceDtlUrl` | 입찰공고상세URL | 원문 링크 |
| `bidNtceUrl` | 입찰공고URL | 원문 링크 |

## 첨부파일 관련 필드
공고 목록 응답에는 첨부파일 URL과 파일명이 직접 포함됩니다.

주요 필드:
- `ntceSpecDocUrl1` ~ `ntceSpecDocUrl10`
- `ntceSpecFileNm1` ~ `ntceSpecFileNm10`
- `stdNtceDocUrl`
- `sptDscrptDocUrl1` ~ `sptDscrptDocUrl5`

중요한 주의사항:
- 나라장터 첨부파일은 PDF만 있는 것이 아닙니다.
- 문서 예시에도 `hwp`, `hwpx`, `xlsx`가 자주 등장합니다.
- 현재 프로젝트는 HWP를 범위 제외했고, PDF/DOCX만 지원합니다.
- 따라서 Phase 1 API 수집에서는 PDF/DOCX만 자동 다운로드하고, HWP/HWPX/XLSX는 “지원 제외 첨부파일”로 메타데이터만 저장하는 것이 안전합니다.

## 핵심 서비스 2: 나라장터 공공데이터개방표준서비스

### 서비스 기본 정보
- 서비스 ID: `PubDataOpnStdService`
- 기본 URL: `http://apis.data.go.kr/1230000/ao/PubDataOpnStdService`
- 방식: REST GET
- 인증: 공공데이터포털 `ServiceKey`
- 응답 형식: XML/JSON

### 제공 오퍼레이션
| Operation | 의미 | 현재 활용도 |
|---|---|---|
| `getDataSetOpnStdBidPblancInfo` | 표준 입찰공고정보 | 보조 후보 |
| `getDataSetOpnStdScsbidInfo` | 표준 낙찰정보 | Phase 3 이후 |
| `getDataSetOpnStdCntrctInfo` | 표준 계약정보 | Phase 3 이후 |

판단:
- 이 서비스는 공공데이터 개방표준에 맞춘 입찰/낙찰/계약 데이터입니다.
- 현재 목표인 “공고문 자동 수집 + 첨부파일 분석”에는 `BidPublicInfoService`가 더 직접적입니다.
- 향후 낙찰/계약 이력 분석까지 확장할 때 `PubDataOpnStdService`를 추가로 사용하면 좋습니다.

## 에러 코드 및 예외 처리
문서상 주요 에러:
- `Unauthorized`: 인증키 없음 또는 유효하지 않음
- `Forbidden`: API 활용신청/승인 상태 문제
- `API not found`: URL 오류 또는 폐기 API
- `API rate limit exceeded`: 동시 요청 초과
- `API token quota exceeded`: 일일 호출량 초과
- `Unexpected error`: 일시적 시스템 오류

공공데이터 응답 코드에서 주의할 항목:
- `00`: 정상
- `03`: 데이터 없음
- `06`: 날짜 포맷 오류
- `07`: 입력 범위 초과
- `08`, `11`: 필수값 누락
- `20`: 서비스 접근 거부
- `22`: 호출 제한 초과
- `30`: 등록되지 않은 서비스 키 또는 URL 인코딩 문제
- `31`: 만료된 서비스 키
- `32`: 등록되지 않은 도메인/IP

## 추천 구현 순서
1. 환경변수 추가
   - `NARA_API_SERVICE_KEY`
   - `NARA_BID_PUBLIC_API_BASE_URL=https://apis.data.go.kr/1230000/ad/BidPublicInfoService`
   - `NARA_PUBDATA_API_BASE_URL=https://apis.data.go.kr/1230000/ao/PubDataOpnStdService`
   - `NARA_API_RESPONSE_TYPE=json`
   - 실제 인증키 값은 `.env`에만 저장하고 Git에 커밋하지 않는다.
   - 공공데이터포털에서 제공하는 Encoding/Decoding 키 중 실제 호출에 성공하는 키를 사용한다.
   - API별 활용신청/승인 상태가 다를 수 있으므로 `BidPublicInfoService`와 `PubDataOpnStdService`가 모두 승인되어 있는지 확인한다.
2. 백엔드에 나라장터 API 클라이언트 추가
   - GET 요청
   - `type=json` 기본 적용
   - 응답 `header.resultCode` 검사
   - 재시도/타임아웃 처리
3. 공고 검색 API 추가
   - 우선 `getBidPblancListInfoCnstwkPPSSrch`
   - 화면 필터: 기간, 공고명, 지역, 업종, 금액
4. 공고 저장 테이블 추가
   - `procurement_notices`
   - 고유키: `bidNtceNo + bidNtceOrd`
   - 원본 API JSON 저장
5. 첨부파일 메타데이터 저장
   - `notice_attachments`
   - URL, 파일명, 확장자, 지원 여부, 다운로드 상태
6. PDF/DOCX만 다운로드
   - 기존 `project_documents` 또는 별도 `notice_documents`로 연결
   - 기존 PyMuPDF/DOCX 파싱 및 AI 요약 재사용
7. 지원 제외 파일 처리
   - `hwp`, `hwpx`, `xlsx`는 자동 분석하지 않고 UI에 “지원 제외” 표시

## Phase 판단
기존 문서에서는 조달청 자동 수집을 Phase 3로 두었지만, 사용자가 기능 추가를 승인하면 “Phase 1.5”로 분리하는 것이 좋습니다.

추천 범위:
- Phase 1.5 포함:
  - API 키 설정
  - 공고 검색
  - 공고 목록 저장
  - PDF/DOCX 첨부파일 다운로드
  - 기존 분석 파이프라인 연결
- Phase 1.5 제외:
  - 최종 지원 가능/불가능 판단
  - 기준문서 RAG 판단
  - HWP/HWPX 변환
  - 낙찰/계약 이력 분석

---

# AI / Engineering Version (English)

## Purpose
This document summarizes the Nara Marketplace API documents under `source/api_doc` and maps them to the next implementation step for SMART Procurement Calculator.

## Primary Recommendation
Use `BidPublicInfoService` as the first integration target.

Pipeline:

```text
query Nara Marketplace notices
-> persist notice metadata
-> collect attachment URLs
-> download supported PDF/DOCX attachments only
-> reuse existing PyMuPDF/DOCX parser
-> reuse existing AI summary pipeline
```

## Service: BidPublicInfoService
- Service ID: `BidPublicInfoService`
- Base URL: `https://apis.data.go.kr/1230000/ad/BidPublicInfoService`
- Protocol: REST GET
- Auth: public data portal `ServiceKey`
- Response: XML by default, JSON when `type=json`

## Priority Operations
| Operation | Meaning | Use |
|---|---|---|
| `getBidPblancListInfoCnstwk` | construction notice list | incremental sync/direct notice lookup |
| `getBidPblancListInfoCnstwkPPSSrch` | construction notices by Nara search conditions | portal search UI |
| `getBidPblancListInfoCnstwkBsisAmount` | construction basis amount | enrich notice detail |
| `getBidPblancListInfoLicenseLimit` | license/industry restrictions | future eligibility input |
| `getBidPblancListInfoPrtcptPsblRgn` | eligible regions | future eligibility input |
| `getBidPblancListInfoEorderAtchFileInfo` | e-order attachments | optional attachment enrichment |

## Common Request Parameters
- `ServiceKey`: required API key.
- `numOfRows`: required page size.
- `pageNo`: required page number.
- `type`: optional, use `json`.
- `inqryDiv`: required query type.
- `inqryBgnDt`, `inqryEndDt`: conditional date range in `YYYYMMDDHHMM`.
- `bidNtceNo`: conditional notice number.
- `bidNtceOrd`: conditional notice order for some detail operations.

## Important Response Fields
- Notice identity: `bidNtceNo`, `bidNtceOrd`, `untyNtceNo`.
- Display: `bidNtceNm`, `ntceInsttNm`, `dminsttNm`.
- Schedule: `bidNtceDt`, `bidBeginDt`, `bidClseDt`, `opengDt`, `bidQlfctRgstDt`.
- Money: `presmptPrce`, `bdgtAmt`, `VAT`, `bssamt`.
- Eligibility hints: `indstrytyLmtYn`, `cnstrtsiteRgnNm`, `lcnsLmtNm`, `prtcptPsblRgnNm`.
- Attachments: `ntceSpecDocUrl1..10`, `ntceSpecFileNm1..10`, `stdNtceDocUrl`, `sptDscrptDocUrl1..5`.
- Links: `bidNtceDtlUrl`, `bidNtceUrl`.

## Attachment Handling
The API returns attachment URLs and file names directly. However, attachments may be `hwp`, `hwpx`, `xlsx`, not just PDF/DOCX.

Phase 1.5 should:
- download and analyze PDF/DOCX only
- store unsupported attachments as metadata
- show unsupported status in the UI
- avoid implementing HWP/HWPX conversion unless explicitly approved later

## Secondary Service: PubDataOpnStdService
- Service ID: `PubDataOpnStdService`
- Base URL: `https://apis.data.go.kr/1230000/ao/PubDataOpnStdService`
- Operations:
  - `getDataSetOpnStdBidPblancInfo`
  - `getDataSetOpnStdScsbidInfo`
  - `getDataSetOpnStdCntrctInfo`

Assessment:
- Useful for standardized bid, award, and contract data.
- Less direct for attachment-based notice ingestion.
- Better suited for later analytics or Phase 3.

## Error Handling
Handle:
- invalid/missing key: `Unauthorized`, code `30`
- not approved: `Forbidden`, code `20`
- no data: code `03`
- date format/range errors: codes `06`, `07`
- missing required params: codes `08`, `11`
- quota/rate limit: `API rate limit exceeded`, `API token quota exceeded`, code `22`
- backend/transient failures: retry with backoff

## Recommended Implementation Phase
Introduce this as `Phase 1.5`.

Include:
- API key setup
- notice search
- notice metadata persistence
- attachment metadata persistence
- PDF/DOCX download
- parser/AI summary reuse

Exclude:
- final eligibility judgment
- RAG-based legal evidence judgment
- HWP/HWPX conversion
- award/contract analytics
