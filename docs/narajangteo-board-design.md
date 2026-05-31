# 한국어 버전

## 문서 목적
이 문서는 `SMART 조달청 계산기`에 새로 추가할 `나라장터 게시판` 기능의 UX 설계와 기능 구현 설계를 정리합니다.

목표는 관리자가 포탈 안에서 나라장터 공고를 검색하고, 상세 내용을 확인하고, 첨부 PDF를 내려받고, 선택한 공고를 저장과 동시에 자동 분석까지 실행할 수 있게 만드는 것입니다.

## 기능 위치
권장 단계는 `Phase 1.5`입니다.

이유:
- 기존 Phase 1의 수동 PDF/DOCX 업로드 분석 기능을 재사용할 수 있습니다.
- Phase 3의 “최종 자격 판단 엔진”이나 “조달청 사이트 크롤러”까지는 아직 필요하지 않습니다.
- 공공데이터 API 기반 조회이므로 사이트 HTML 크롤링보다 안정적입니다.

## 범위
### 포함
- 좌측 메뉴에 `나라장터 게시판` 추가
- 나라장터 공고 리스트 조회
- 기본 검색과 상세검색
- 공고 상세 보기
- 공고 첨부파일 목록 보기
- 처리 가능 첨부파일 다운로드
- 라디오 박스로 공고 1개 선택
- `공고 상세 저장` 액션
- 공고 메타데이터 저장
- 공고 상세 API 재조회
- 공고 첨부 PDF/DOCX 자동 다운로드
- PDF/DOCX 파싱
- AI 요약 또는 내부 fallback 요약
- 공고 분석 결과 저장
- 처리 상태 표시

### 제외
- 최종 자격 판정
- 법인 요건 자동 매칭
- 기준문서 RAG 근거 검색
- HWP/HWPX 파싱
- 나라장터 사이트 HTML 크롤링
- 로그인/권한

## 핵심 UX 컨셉
`나라장터 게시판`은 “검색 -> 상세 확인 -> 1개 선택 -> 저장 및 자동 분석 -> 분석 결과 확인” 흐름으로 설계합니다.

관리자는 여러 공고를 비교해 보되, 분석 실행은 한 번에 하나의 공고만 선택합니다. 이렇게 하면 API 호출, 파일 다운로드, 분석 작업의 실패 범위를 좁힐 수 있고 사용자가 현재 처리 대상을 명확히 이해할 수 있습니다.

## 정보 구조
새 메뉴:
- `나라장터 게시판`

권장 메뉴 구조:
- `나라장터 게시판`
- `공고 검색`: 나라장터 API에서 새 공고를 검색하고 상세 저장/분석을 실행하는 화면
- `저장한 공고`: 사용자가 `공고 상세 저장`으로 저장한 공고문들을 다시 조회/관리하는 게시판
- `설정 > API 연동`: 나라장터 API 키 설정 여부와 연결 상태를 확인하는 화면

권장 라우트:
- `/nara-board`
- `/nara-board/:bidNtceNo/:bidNtceOrd`
- `/nara-saved-notices`
- `/nara-saved-notices/:id`
- `/nara-saved-notices/:id/analysis`
- `/settings/integrations`
- `/settings/integrations/nara`

MVP에서는 좌측 사이드바에 `나라장터 게시판` 그룹을 두고, 하위 탭 또는 하위 메뉴로 `공고 검색`과 `저장한 공고`를 제공합니다.

`저장한 공고`는 사용자가 선택 저장한 공고문만 보여주는 내부 게시판입니다. 외부 API 검색 결과와 달리 DB에 저장된 공고, 다운로드한 첨부파일, 분석 상태, 분석 결과를 기준으로 조회합니다.

## 페이지 UX

### 1. 나라장터 게시판 목록
화면 구성:
- 상단 제목: `나라장터 게시판`
- 설명: `나라장터 공공데이터 API에서 공고를 조회하고, 필요한 공고를 저장해 자동 분석합니다.`
- 기본 검색 바
- 상세검색 토글/드로어
- 공고 리스트 테이블
- 우측 또는 하단 상세 미리보기 패널
- 하단 고정 액션 영역: `공고 상세 저장`

페이지 진입 동작:
- `공고 검색` 페이지에 진입하면 즉시 기본 조건으로 공고 목록 API를 호출합니다.
- 기본 조회 기간은 `최근 1개월`입니다.
- 예: 오늘이 `2026-05-05`라면 `2026-04-05 00:00`부터 `2026-05-05 23:59`까지 조회합니다.
- 기본 페이지 크기는 20건입니다.
- API 키가 없거나 연결 테스트에 실패한 상태라면 자동 조회 대신 설정 안내 배너를 표시합니다.

테이블 컬럼:
- 선택 라디오
- 공고명
- 공고기관
- 수요기관
- 공고일시
- 입찰마감
- 추정가격
- 지역
- 업종제한 여부
- 첨부파일 수
- 저장 여부
- 분석 상태

행 클릭 동작:
- 행을 클릭하면 상세 미리보기 패널을 엽니다.
- 라디오 버튼은 분석 대상으로 선택할 공고를 명확히 지정합니다.

### 2. 기본 검색
기본 검색은 빠르게 쓰는 필터만 노출합니다.
- 검색어: 공고명 기준
- 조회 기간: 공고게시일 기준
- 지역명
- 마감 공고 제외 여부

기본값:
- 조회 기간은 최근 1개월
- 응답 수는 20건
- 정렬은 공고일시 최신순

### 3. 상세검색
상세검색은 드로어 또는 접이식 패널로 제공합니다.

필터:
- 공고명
- 공고기관명
- 수요기관명
- 참가제한지역명
- 업종명
- 추정가격 시작/종료
- 공고게시일 기준 또는 개찰일 기준
- 입찰마감 제외 여부
- 페이지 크기

UX 원칙:
- 필터 초기화 버튼 제공
- 검색 실행 버튼은 오른쪽 하단에 고정
- 적용된 필터는 칩 형태로 표시

### 4. 공고 상세 미리보기
상세 패널 주요 섹션:
- 공고 기본정보
- 일정
- 금액
- 참가 제한 힌트
- 첨부파일
- 원문 링크

상세 필드:
- 입찰공고번호/차수
- 공고명
- 공고기관
- 수요기관
- 공고일시
- 입찰개시/마감/개찰일시
- 추정가격/예산금액/기초금액
- 공사현장지역
- 업종제한 여부
- 면허제한 목록
- 참가가능지역 목록

### 5. 첨부파일 다운로드 UX
첨부파일 목록은 지원 상태를 명확히 구분합니다.

표시 정보:
- 파일명
- 확장자
- 출처 필드
- 지원 상태
- 다운로드 상태
- 액션

처리 정책:
- `.pdf`: 다운로드 및 분석 가능
- `.docx`: 다운로드 및 분석 가능
- `.hwp`, `.hwpx`, `.xlsx`, 기타: 현재는 지원 제외, 메타데이터만 저장

액션:
- 처리 가능 파일: `다운로드`
- 처리 제외 파일: `처리 제외` 배지와 안내 툴팁

### 6. 공고 상세 저장 UX
관리자가 라디오로 1개 공고를 선택하면 `공고 상세 저장` 버튼이 활성화됩니다.

버튼 클릭 후 처리 흐름:
1. 확인 모달 표시
2. 공고 상세 저장 작업 시작
3. 진행 상태 모달 또는 우측 패널 표시
4. 완료 후 `분석 결과 보기` 버튼 제공

확인 모달 문구 예시:
```text
선택한 공고를 저장하고 첨부 PDF/DOCX를 자동 다운로드한 뒤 분석합니다.
HWP/HWPX/XLSX 파일은 현재 분석하지 않고 메타데이터만 저장합니다.
```

진행 단계:
- 공고 상세 조회
- 기초금액 조회
- 면허제한 조회
- 참가가능지역 조회
- 첨부파일 수집
- PDF/DOCX 다운로드
- 문서 파싱
- AI 요약
- 결과 저장

상태값:
- `queued`
- `fetching_notice`
- `saving_notice`
- `downloading_attachments`
- `parsing_documents`
- `summarizing`
- `completed`
- `failed`
- `partial_failed`

### 7. 저장된 공고 상세/분석 결과 UX
저장 완료 후 별도 상세 페이지로 이동합니다.

상단:
- 공고명
- 공고번호/차수
- 저장 상태
- 분석 상태
- 재분석 버튼

본문:
- 공고 메타데이터 요약
- 첨부파일 다운로드 상태
- 분석 결과
- 원문 추출 텍스트
- API 원본 JSON 접기/펼치기

### 8. 저장한 공고 게시판 UX
`저장한 공고`는 `공고 상세 저장` 액션으로 저장된 공고만 모아서 보여주는 게시판입니다.

권장 경로:
- `/nara-saved-notices`

목록 컬럼:
- 공고명
- 공고번호/차수
- 공고기관
- 수요기관
- 입찰마감
- 첨부 다운로드 상태
- 분석 상태
- 저장일
- 최근 분석일

검색/필터:
- 공고명
- 공고기관/수요기관
- 지역
- 저장일
- 입찰마감일
- 분석 상태
- 첨부 다운로드 상태

액션:
- 상세 보기
- 분석 결과 보기
- 재분석
- 로컬 첨부파일 다운로드
- 삭제

삭제 UX:
- 삭제 시 저장된 공고 메타데이터, 분석 결과, 다운로드 첨부파일을 함께 삭제할지 확인 모달에서 명확히 안내합니다.

## 나라장터 API 설정 UX
나라장터 API 키는 공고 검색/저장 기능의 전제 조건이므로 별도 설정 메뉴에서 상태를 확인할 수 있어야 합니다.

권장 메뉴:
- `설정`
- `설정 > API 연동`
- `설정 > API 연동 > 나라장터`

권장 경로:
- `/settings/integrations/nara`

표시 정보:
- 나라장터 API 키 설정 여부
- 마스킹된 키 값
- 사용 중인 `BidPublicInfoService` base URL
- 사용 중인 `PubDataOpnStdService` base URL
- 응답 형식
- 마지막 연결 테스트 시각
- 마지막 연결 테스트 결과
- 공고 API 승인/호출 가능 여부
- 표준 데이터 API 승인/호출 가능 여부
- PDF 첨부 다운로드 테스트 가능 여부

보안 원칙:
- API 키 전체 값은 화면에 노출하지 않습니다.
- 예: `8164************36ab`
- 프론트엔드로 전체 키를 내려주지 않습니다.
- 저장 방식은 `.env` 또는 로컬 설정 파일/로컬 DB 중 하나로 정하되, Git에는 커밋하지 않습니다.

액션:
- `연결 테스트`
- `공고 API 테스트`
- `첨부 PDF 다운로드 테스트`
- `설정 다시 불러오기`

연결 테스트 결과 예시:
```text
나라장터 API 키가 설정되어 있습니다.
공고 목록 조회: 정상
공고 상세 조회: 정상
첨부 PDF 다운로드: 정상
마지막 확인: 2026-05-05 22:50
```

오류 안내 예시:
- API 키 미설정: `설정 파일 또는 환경변수에 NARA_API_SERVICE_KEY를 등록해주세요.`
- 인증 오류: `인증키가 유효하지 않거나 Encoding/Decoding 키 선택이 잘못되었을 수 있습니다.`
- 승인 오류: `공공데이터포털에서 해당 API 활용신청/승인 상태를 확인해주세요.`
- 호출 제한: `일일 호출량 또는 동시 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.`

분석 결과 섹션:
- 한줄 요약
- 공고 핵심 내용
- 주요 일정
- 금액 정보
- 참가 제한 조건
- 제출/준비 필요사항
- 첨부파일별 요약
- 확인 필요/불명확 항목

## 기능 구현 설계

## 데이터 모델 제안

### procurement_notices
나라장터 공고 저장 테이블입니다.

주요 필드:
- `id`
- `bid_ntce_no`
- `bid_ntce_ord`
- `title`
- `notice_institution_name`
- `demand_institution_name`
- `bid_notice_datetime`
- `bid_begin_datetime`
- `bid_close_datetime`
- `opening_datetime`
- `estimated_price`
- `budget_amount`
- `basis_amount`
- `industry_limit_yn`
- `construction_site_region`
- `notice_url`
- `detail_url`
- `source_api`
- `raw_notice_json`
- `raw_enrichment_json`
- `save_status`
- `analysis_status`
- `latest_analysis_id`
- `created_at`
- `updated_at`

제약:
- `bid_ntce_no + bid_ntce_ord`는 unique로 관리합니다.
- 동일 공고를 다시 저장하면 중복 생성하지 않고 기존 공고를 갱신하거나 재분석합니다.

### procurement_notice_attachments
공고 첨부파일 메타데이터와 다운로드 결과를 저장합니다.

주요 필드:
- `id`
- `notice_id`
- `source_field`
- `original_file_name`
- `file_url`
- `file_extension`
- `support_status`
- `download_status`
- `stored_file_path`
- `mime_type`
- `file_size`
- `file_hash`
- `parse_status`
- `parsed_text_path`
- `parser_metadata_json`
- `error_message`
- `created_at`
- `updated_at`

지원 상태:
- `supported`
- `unsupported`

다운로드 상태:
- `pending`
- `downloaded`
- `skipped_unsupported`
- `failed`

### procurement_notice_analyses
공고 분석 결과를 저장합니다.

주요 필드:
- `id`
- `notice_id`
- `analysis_type`
- `model_provider`
- `model_name`
- `prompt_version`
- `input_hash`
- `output_json`
- `output_markdown`
- `token_usage_json`
- `status`
- `error_message`
- `created_at`

MVP에서는 기존 `analyses` 테이블을 억지로 재사용하지 말고, 공고 전용 분석 테이블을 분리하는 것을 권장합니다. 기존 `analyses`는 `project_documents`에 강하게 연결되어 있기 때문입니다.

### procurement_notice_jobs
저장/다운로드/분석 작업 상태를 추적합니다.

주요 필드:
- `id`
- `notice_id`
- `job_type`
- `status`
- `current_step`
- `progress_percent`
- `message`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`

## 백엔드 서비스 구성

권장 모듈:
```text
backend/app/
  api/
    nara_board.py
  services/
    nara_api_client.py
    nara_notice_service.py
    notice_attachment_service.py
    notice_analysis_service.py
  pipelines/
    notice_ingestion_pipeline.py
    parser.py
    summarizer.py
  repositories/
    procurement_notice_repository.py
```

역할:
- `nara_api_client.py`: 공공데이터 API 호출, 응답 코드 검증, 재시도, 타임아웃
- `nara_notice_service.py`: 검색/상세 조회/저장 orchestration
- `notice_attachment_service.py`: 첨부파일 정규화, 지원 확장자 판정, 다운로드
- `notice_analysis_service.py`: 공고 분석 결과 생성과 저장
- `notice_ingestion_pipeline.py`: 저장 버튼 이후 전체 파이프라인 제어

## API 설계 제안

### 나라장터 검색
```http
GET /api/nara/notices/search
```

쿼리:
- `keyword`
- `date_from`
- `date_to`
- `date_type`
- `notice_institution`
- `demand_institution`
- `region`
- `industry`
- `price_min`
- `price_max`
- `exclude_closed`
- `page`
- `page_size`

동작:
- `getBidPblancListInfoCnstwkPPSSrch` 호출
- 검색 결과와 첨부파일 요약 반환
- DB 저장은 하지 않습니다.

### 공고 상세 미리보기
```http
GET /api/nara/notices/preview
```

쿼리:
- `bid_ntce_no`
- `bid_ntce_ord`

동작:
- 공고 상세 조회
- 기초금액 조회
- 면허제한 조회
- 참가가능지역 조회
- 첨부파일 목록 정규화
- 저장하지 않은 preview 응답 반환

### 공고 상세 저장 및 분석 시작
```http
POST /api/nara/notices/save-and-analyze
```

요청:
```json
{
  "bid_ntce_no": "R26BK01503422",
  "bid_ntce_ord": "000",
  "force_refresh": false,
  "reanalyze": false
}
```

응답:
```json
{
  "notice_id": 1,
  "job_id": 10,
  "status": "queued"
}
```

### 작업 상태 조회
```http
GET /api/nara/notice-jobs/{job_id}
```

### 나라장터 API 설정 상태 조회
```http
GET /api/settings/integrations/nara/status
```

응답 예시:
```json
{
  "configured": true,
  "masked_key": "8164************36ab",
  "bid_public_base_url": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService",
  "pubdata_base_url": "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService",
  "response_type": "json",
  "last_tested_at": "2026-05-05T22:50:00",
  "last_test_status": "ok"
}
```

### 나라장터 API 연결 테스트
```http
POST /api/settings/integrations/nara/test
```

동작:
- 환경변수 또는 로컬 설정에서 API 키를 읽습니다.
- 최근 1개월 기본 조건으로 공고 목록 테스트를 수행합니다.
- 대표 공고가 있으면 상세 조회와 PDF 첨부 다운로드 테스트까지 수행합니다.
- 전체 API 키는 응답에 포함하지 않습니다.

### 저장된 공고 상세
```http
GET /api/nara/saved-notices/{notice_id}
```

### 첨부파일 다운로드
```http
GET /api/nara/saved-notices/{notice_id}/attachments/{attachment_id}/download
```

동작:
- 이미 로컬에 저장된 파일을 내려줍니다.
- 아직 다운로드되지 않았고 처리 가능한 파일이면 다운로드 후 제공할 수 있습니다.
- 외부 URL을 프론트엔드에 직접 맡기기보다 백엔드가 프록시/로컬 저장을 담당하는 편이 안정적입니다.

### 재분석
```http
POST /api/nara/saved-notices/{notice_id}/reanalyze
```

## 저장 및 분석 파이프라인

```text
사용자 공고 1개 선택
-> POST /api/nara/notices/save-and-analyze
-> 공고 상세 API 재조회
-> 기초금액/면허제한/참가가능지역 보강
-> procurement_notices upsert
-> 첨부파일 URL 정규화
-> procurement_notice_attachments upsert
-> PDF/DOCX 첨부 자동 다운로드
-> 파일 해시 계산
-> PyMuPDF/python-docx 파싱
-> 추출 텍스트 정규화
-> 첨부파일별 요약 생성
-> 공고 단위 통합 요약 생성
-> procurement_notice_analyses 저장
-> latest_analysis_id 갱신
-> 사용자에게 완료 상태 표시
```

## 첨부파일 처리 정책

### 다운로드 대상
- `.pdf`
- `.docx`

### 메타데이터만 저장
- `.hwp`
- `.hwpx`
- `.xlsx`
- `.xls`
- `.zip`
- 확장자 불명

### 중복 제거
다음 기준으로 중복을 제거합니다.
- `notice_id + file_url`
- `notice_id + original_file_name + source_field`
- 다운로드 후 `file_hash`

## 분석 프롬프트 전략
공고 분석은 자격 판단이 아니라 요약입니다.

모델에 요청할 출력 구조:
```json
{
  "one_line_summary": "",
  "notice_overview": "",
  "important_dates": [],
  "amounts": [],
  "participation_requirements": [],
  "required_documents": [],
  "attachment_summaries": [],
  "risks_or_unclear_points": [],
  "next_actions": []
}
```

주의:
- 최종 자격 결론을 내리지 않습니다.
- 근거가 없는 내용은 추정하지 않습니다.
- API 메타데이터와 PDF 추출 텍스트를 분리해서 입력합니다.
- 첨부파일별 요약과 공고 통합 요약을 구분합니다.

## 에러 처리

### API 오류
- 인증키 오류
- 승인되지 않은 API
- 데이터 없음
- 날짜 범위 오류
- 호출량 제한

UX:
- 사용자에게 짧은 원인과 해결 힌트 제공
- 기술 상세는 접기 영역 또는 로그에 표시

### 다운로드 오류
- URL 만료/접근 불가
- Content-Type 불일치
- PDF 시그니처 불일치
- 네트워크 타임아웃

정책:
- 해당 첨부만 `failed` 처리
- 다른 첨부 분석은 계속 진행
- 전체 작업은 `partial_failed`로 종료 가능

### 분석 오류
- 파싱 실패
- AI API 실패
- 내부 fallback 요약 사용

정책:
- 실패 단계 기록
- 재시도 버튼 제공
- fallback 결과는 명확히 표시

## 보안 및 키 관리
- `NARA_API_SERVICE_KEY`는 `.env` 또는 OS 환경변수로만 관리합니다.
- 인증키를 프론트엔드에 노출하지 않습니다.
- 테스트 결과 JSON에도 인증키를 저장하지 않습니다.
- 외부 첨부 URL은 저장하되, 실제 파일은 로컬 저장소에 복사해 분석합니다.

## 저장소 구조 추가 제안
```text
backend/
  app/
    api/
      nara_board.py
    services/
      nara_api_client.py
      nara_notice_service.py
      notice_attachment_service.py
      notice_analysis_service.py
    pipelines/
      notice_ingestion_pipeline.py
    repositories/
      procurement_notice_repository.py
    storage/
      nara_notices/

frontend/
  src/
    pages/
      NaraBoardPage.tsx
      NaraSavedNoticeDetailPage.tsx
    features/
      nara-board/
        components/
        api.ts
        types.ts
    entities/
      nara-notice/
```

## 구현 순서
1. DB 모델 추가
2. 나라장터 API 클라이언트 서비스화
3. 검색 API 구현
4. 상세 preview API 구현
5. 첨부파일 정규화/지원 확장자 판정 구현
6. 저장 및 분석 job 모델 구현
7. PDF/DOCX 다운로드 서비스 구현
8. 기존 parser/summarizer 파이프라인 연결
9. 나라장터 게시판 UI 구현
10. 저장된 공고 상세/분석 결과 UI 구현
11. 스모크 테스트와 API mocking 테스트 추가

## 테스트 계획
- API 클라이언트 단위 테스트
- 첨부파일 정규화 테스트
- PDF 다운로드 시그니처 테스트
- 저장 중복 방지 테스트
- 파이프라인 partial failure 테스트
- 프론트엔드 검색/선택/저장 플로우 테스트
- 실제 API는 별도 수동/통합 테스트 스크립트로 유지

## 가정
- 1차 구현은 공사 공고 API를 우선 지원합니다.
- 저장된 공고는 프로젝트에 자동 연결하지 않고 별도 `나라장터 저장 공고`로 관리합니다.
- 향후 사용자가 저장된 공고에서 프로젝트를 생성하거나 법인과 연결할 수 있습니다.
- 한 번에 저장/분석하는 공고는 1개입니다.
- PDF/DOCX가 여러 개면 모두 다운로드하되, 분석 결과는 첨부별 요약과 통합 요약을 모두 저장합니다.

## Questions for Product Owner
- 저장된 공고를 기존 `프로젝트`에 바로 연결해야 하나요, 아니면 별도 저장 후 필요 시 프로젝트로 전환하면 될까요?
- 공사 공고만 먼저 지원해도 될까요, 아니면 물품/용역 공고도 같은 화면에서 바로 필요할까요?
- 첨부 PDF가 여러 개인 경우 전체를 분석해야 하나요, 아니면 공고문으로 보이는 PDF만 우선 분석해야 하나요?
- 다운로드한 원본 PDF를 사용자가 로컬에서 다시 받을 수 있게 해야 하나요?
- 저장된 공고 삭제 시 다운로드한 첨부파일도 함께 삭제할까요, 아니면 보관할까요?

---

# AI / Engineering Version (English)

## Purpose
This document defines the UX and implementation design for the `Nara Marketplace Board` feature.

The feature lets the administrator search Nara Marketplace notices inside the portal, inspect detail data, download supported attachments, select one notice via radio button, and run a save/download/parse/summarize pipeline.

## Phase
Recommended phase: `Phase 1.5`.

This is API-based notice ingestion, not HTML crawling and not the final eligibility judgment engine.

## Scope
In scope:
- Nara board page
- notice list
- basic and advanced search
- notice detail preview
- attachment list
- supported attachment download
- one selected notice via radio button
- `save and analyze` action
- notice metadata persistence
- detail/enrichment API lookup
- PDF/DOCX auto-download
- parsing
- summarization
- persisted notice analysis
- job/progress status

Out of scope:
- eligibility verdict
- corporation-vs-notice matching
- RAG evidence retrieval
- HWP/HWPX parsing
- HTML crawling
- auth

## UX Architecture
Routes:
- `/nara-board`
- `/nara-board/:bidNtceNo/:bidNtceOrd`
- `/nara-saved-notices`
- `/nara-saved-notices/:id`
- `/nara-saved-notices/:id/analysis`

Recommended navigation:
- `Nara Board`
- `Search Notices`
- `Saved Notices`
- `Settings > Integrations > Nara`

`Saved Notices` is an internal board for notices persisted through the `Save Notice Detail` action. It lists only local DB records and their download/analysis state, not live API search results.

On entering `Search Notices`, the frontend should automatically request the default notice list with a one-month date range. If today is `2026-05-05`, the default range is `2026-04-05 00:00` to `2026-05-05 23:59`.

Main board layout:
- header
- basic search
- advanced search drawer
- notice table
- detail preview panel
- sticky `Save Notice Detail` action

Table columns:
- radio select
- title
- notice institution
- demand institution
- notice datetime
- bid close datetime
- estimated price
- region
- industry limit flag
- attachment count
- saved status
- analysis status

Save action flow:
```text
select one notice
-> confirm modal
-> start save/analyze job
-> progress modal/panel
-> navigate to saved notice analysis
```

## Data Model

### procurement_notices
Persisted notice snapshot.

Recommended fields:
- `id`
- `bid_ntce_no`
- `bid_ntce_ord`
- `title`
- `notice_institution_name`
- `demand_institution_name`
- `bid_notice_datetime`
- `bid_begin_datetime`
- `bid_close_datetime`
- `opening_datetime`
- `estimated_price`
- `budget_amount`
- `basis_amount`
- `industry_limit_yn`
- `construction_site_region`
- `notice_url`
- `detail_url`
- `source_api`
- `raw_notice_json`
- `raw_enrichment_json`
- `save_status`
- `analysis_status`
- `latest_analysis_id`
- `created_at`
- `updated_at`

Unique key:
- `bid_ntce_no + bid_ntce_ord`

### procurement_notice_attachments
Persist attachment metadata and local download state.

Recommended fields:
- `id`
- `notice_id`
- `source_field`
- `original_file_name`
- `file_url`
- `file_extension`
- `support_status`
- `download_status`
- `stored_file_path`
- `mime_type`
- `file_size`
- `file_hash`
- `parse_status`
- `parsed_text_path`
- `parser_metadata_json`
- `error_message`
- `created_at`
- `updated_at`

### procurement_notice_analyses
Persist notice-level summaries.

Recommended fields:
- `id`
- `notice_id`
- `analysis_type`
- `model_provider`
- `model_name`
- `prompt_version`
- `input_hash`
- `output_json`
- `output_markdown`
- `token_usage_json`
- `status`
- `error_message`
- `created_at`

### procurement_notice_jobs
Track asynchronous save/download/analyze progress.

Recommended fields:
- `id`
- `notice_id`
- `job_type`
- `status`
- `current_step`
- `progress_percent`
- `message`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`

## Backend Modules
```text
backend/app/
  api/nara_board.py
  services/nara_api_client.py
  services/nara_notice_service.py
  services/notice_attachment_service.py
  services/notice_analysis_service.py
  pipelines/notice_ingestion_pipeline.py
  repositories/procurement_notice_repository.py
```

## API Proposal

Search:
```http
GET /api/nara/notices/search
```

Preview:
```http
GET /api/nara/notices/preview?bid_ntce_no=...&bid_ntce_ord=...
```

Save and analyze:
```http
POST /api/nara/notices/save-and-analyze
```

Request:
```json
{
  "bid_ntce_no": "R26BK01503422",
  "bid_ntce_ord": "000",
  "force_refresh": false,
  "reanalyze": false
}
```

Job status:
```http
GET /api/nara/notice-jobs/{job_id}
```

Saved notice detail:
```http
GET /api/nara/saved-notices/{notice_id}
```

Attachment download:
```http
GET /api/nara/saved-notices/{notice_id}/attachments/{attachment_id}/download
```

Reanalyze:
```http
POST /api/nara/saved-notices/{notice_id}/reanalyze
```

## Pipeline
```text
selected notice
-> save-and-analyze request
-> fetch notice detail
-> fetch basis amount / license / region enrichment
-> upsert procurement_notices
-> normalize attachment URLs
-> upsert procurement_notice_attachments
-> download supported PDF/DOCX
-> hash file
-> parse with PyMuPDF/python-docx
-> normalize extracted text
-> summarize each attachment
-> summarize notice as a whole
-> persist procurement_notice_analyses
-> update latest_analysis_id
-> return completed job status
```

## Attachment Policy
Download and analyze:
- `.pdf`
- `.docx`

Store metadata only:
- `.hwp`
- `.hwpx`
- `.xlsx`
- `.xls`
- `.zip`
- unknown extensions

## Prompt Output Schema
```json
{
  "one_line_summary": "",
  "notice_overview": "",
  "important_dates": [],
  "amounts": [],
  "participation_requirements": [],
  "required_documents": [],
  "attachment_summaries": [],
  "risks_or_unclear_points": [],
  "next_actions": []
}
```

Rules:
- Do not produce an eligibility verdict.
- Do not infer unsupported facts.
- Keep API metadata and extracted attachment text separate.
- Store attachment-level summaries and notice-level aggregate summary.

## Testing
- API client unit tests
- attachment normalization tests
- binary download and signature tests
- idempotent save tests
- partial failure pipeline tests
- frontend search/select/save tests
- live API test remains a separate integration script

## Assumptions
- first implementation targets construction notices only
- saved notices are independent from projects in MVP
- one notice is saved/analyzed per action
- all supported PDF/DOCX attachments are downloaded
- multiple attachments produce both per-file and aggregate summaries

## Questions for Product Owner
- Should saved notices be linked to projects immediately?
- Should goods/services notices be included in the first release?
- Should all supported attachments be analyzed, or only the PDF that looks like the main notice?
- Should users be able to download locally stored original PDFs?
- When deleting a saved notice, should local files also be deleted?
