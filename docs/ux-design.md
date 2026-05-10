# 한국어 버전

## 제품 목표
- 단일 관리자 사용자가 복잡한 조달 문서를 빠르게 정리하고 추적할 수 있어야 한다.
- 법인, 프로젝트, 문서, 분석 결과가 하나의 관리 흐름으로 이어져야 한다.
- 요약 중심 MVP에서 기준문서/RAG/판단 화면으로 자연스럽게 확장 가능해야 한다.

## 주요 관리자 페르소나
- 역할: 행정사 또는 내부 검토 담당자
- 환경: 로컬 PC에서 여러 프로젝트와 법인을 오가며 문서를 검토
- 니즈
  - 프로젝트 중심 이력 추적
  - 문서 처리 상태 확인
  - 빠른 검색과 필터
  - AI 결과와 원문을 함께 비교

## 어드민 대시보드 컨셉
- 첫 화면에서 최근 프로젝트와 분석 상태를 즉시 파악
- 카드 + 테이블 혼합형 레이아웃
- 파일 중심이 아니라 프로젝트 중심 탐색
- 향후 기준 PDF와 공고 수집 메뉴까지 확장 가능한 내비 구조

## 정보 구조
- Dashboard
- Corporation Management
- Project Management
- Project Detail
- Analysis Detail
- Basis PDF Management
- Basis PDF Detail
- 나라장터 게시판
- 나라장터 저장 공고 상세
- Settings
- API Integrations

## 페이지 목록
- `/dashboard`
- `/corporations`
- `/corporations/:id`
- `/projects`
- `/projects/new`
- `/projects/:id`
- `/documents/:id/analysis`
- `/nara-board`
- `/nara-saved-notices`
- `/nara-saved-notices/:id`
- `/nara-saved-notices/:id/analysis`
- `/settings`
- `/settings/integrations`
- `/settings/integrations/nara`
- `/basis-documents`
- `/basis-documents/:id`

## 내비게이션 구조
- 좌측 사이드바
  - Dashboard
  - Corporations
  - Projects
  - Nara Board
  - Nara Board > 공고 검색
  - Nara Board > 저장한 공고
  - Basis PDFs
  - Settings
  - Settings > API 연동
- 상단 바
  - 검색
  - 최근 작업
  - 처리 상태 표시

## 법인 관리 페이지 UX
- 상단에 `법인 추가` 버튼
- 중앙에 테이블 배치
- 주요 컬럼
  - 법인명
  - 관리 법인그룹
  - 업종/분류
  - 지역
  - 인증/면허
  - 회사 규모
  - 최근 수정일
- 상세 패널 또는 상세 페이지에서 내부 메모 확인
- 삭제 시 연관 프로젝트 존재 여부 경고
- 향후 지원 가능성 판단을 위해 법인 상세 화면은 `준비 상태 프로필` 형태로 확장한다.
- Phase 1.6부터 법인 관리의 중심은 직접 입력 폼이 아니라 증빙자료 업로드와 자동 추출 결과 확인이다.
- 법인은 관리 법인그룹 단위로 구분한다.
- 같은 사업자등록번호가 다른 관리 법인그룹에 있으면 등록은 허용하되 안내 배너를 표시한다.
- 같은 사업자등록번호가 같은 관리 법인그룹에 이미 있으면 `이미 존재하는 법인`으로 등록을 차단한다.
- 권장 탭
  - 기본정보
  - 소재지/지역
  - 업종/면허/인증
  - 기업유형/우대조건
  - 실적/인력/장비
  - 증빙자료
  - 판단 이력
- 각 탭에는 `이 정보가 공고 지원 가능성 판단에 왜 필요한지`를 짧게 설명한다.
- 입력값은 `확인됨`, `증빙 없음`, `만료`, `확인 필요` 상태를 표시할 수 있어야 한다.
- 법인 증빙자료는 사업자등록증, 면허/등록증, 중소기업확인서, 실적증명서, 신용평가서 등을 업로드하고 관련 필드에 연결하는 UX가 필요하다.

### 법인 등록 저입력 UX
- 법인 등록은 `직접 입력 최소화`를 최우선 원칙으로 한다.
- 법인 등록 첫 화면은 일반 입력 폼이 아니라 `사업자등록증 업로드` 화면으로 시작한다.
- 첫 화면에서 관리 법인그룹을 선택한다. 기본값은 `기본 관리그룹`이다.
- 기존 그룹은 드롭다운/자동완성으로 선택하고, 새 그룹이 필요할 때만 직접 입력한다.
- 사용자가 사업자등록증을 업로드하면 이미지/PDF/Word 파일에서 법인명, 사업자등록번호, 대표자명, 사업장 주소, 업태/종목을 자동 추출한다.
- 사용자는 자동 추출 결과를 확인하고 틀린 값만 수정한다.
- `사업자등록증 없음` 또는 `나중에 입력`을 선택한 경우에만 직접 입력 폼을 표시한다.
- 수동 입력 폼의 최초 필수값은 법인명, 본점 지역, 대표 업종/사업분야 정도로 제한한다.
- 수동 입력으로 생성한 법인은 `기본정보 미검증` 또는 `증빙자료 없음` 상태를 표시한다.
- 기업유형/우대조건은 텍스트 입력이 아니라 체크박스 카드 또는 토글 카드로 선택한다.
- 중소기업확인서, 여성기업, 장애인기업, 사회적기업, 협동조합, 벤처기업, 창업기업, 직접생산확인증명서 등을 빠른 선택 항목으로 제공한다.
- 각 항목을 선택하면 만료일, 세부유형, 증빙자료 연결 필드만 펼쳐진다.
- 면허/인증은 검색형 드롭다운과 자주 쓰는 면허 빠른 선택 칩으로 입력한다.
- 실적/인력/장비는 먼저 `없음`, `있음`, `확인 필요` 중 하나를 선택하게 하고, `있음`일 때만 상세 입력을 펼친다.
- 실적과 인증은 직접 입력보다 증빙자료 업로드 후 자동 추출 결과를 확인/수정하는 흐름을 우선한다.
- 법인 상세에는 단순 입력 완료율이 아니라 `공고 판단 준비도`를 표시한다.
- 준비도 예시는 기본정보, 면허/인증, 기업유형, 실적, 제재 여부 등 판단에 필요한 정보가 얼마나 갖춰졌는지로 계산한다.

법인 등록 첫 화면 권장 구성:

```text
사업자등록증을 업로드하면 법인 기본정보를 자동으로 채워드립니다.

[사업자등록증 업로드]
[사업자등록증이 없어요 / 직접 입력할게요]
```

사업자등록증 자동 추출 결과 화면:
- 좌측: 원본 문서 미리보기
- 우측: 추출된 법인명, 사업자등록번호, 대표자명, 주소, 업태, 종목
- 필드별 신뢰도 또는 `확인 필요` 배지
- 사업자등록번호 중복 안내
  - 같은 그룹 중복: 생성 차단 메시지
  - 다른 그룹 중복: 계속 등록 가능 안내
- `확인 후 법인 생성` 버튼

### 증빙자료 자동 추출 UX
- 법인 상세 `증빙자료` 탭에서 사업자등록증 외 모든 증빙서류를 추가 업로드할 수 있다.
- 여러 파일을 한 번에 업로드할 수 있고, 파일별로 예상 문서 유형을 표시한다.
- 시스템이 모르는 서류는 `AI로 문서 유형 파악 중` 상태로 표시한다.
- 자동 분류 결과는 바로 법인정보에 반영하지 않고 사용자가 확인해야 한다.
- 추출 결과 확인 화면은 원본 문서, 추출값, 기존값, 충돌 여부를 함께 보여준다.
- 사용자는 필드별로 `반영`, `무시`, `수정`, `다른 항목에 연결`을 선택할 수 있다.
- 현재 구현은 자동 추출 후보를 체크박스와 수정 입력으로 보여주며, 선택한 후보만 법인 프로필에 반영한다.
- 선택하지 않은 후보는 보류 상태로 남겨 OCR 오류나 보조 증빙의 잘못된 값이 핵심 식별값을 덮어쓰지 않도록 한다.
- HWP/HWPX는 직접 파싱하지 않고 PDF 변환 후 업로드 안내를 표시한다.

Phase 1.6 UX 재검토 결과:
- 1.6A에서는 법인 등록 시작 화면과 사업자등록증명/사업자등록증 추출 확인 UX만 우선 완성한다.
- 1.6B에서 주요 증빙자료 카드, 증빙자료 탭, 만료/충돌/확인 필요 상태를 확장한다.
- 1.6C에서 알 수 없는 문서의 AI 분류, 수동 유형 지정, 재추출, 교정 이력을 고도화한다.
- OCR이 준비되지 않은 PC에서는 이미지 증빙을 실패로 처리하지 말고 `OCR 설정 필요` 상태와 수동 입력 fallback을 제공한다.
- AI 분류 결과는 자동 반영하지 않고 사용자가 명시적으로 확인해야 한다.
- 현재 백엔드는 알 수 없는 증빙서류에 대해 AI 분류 성공 시 `ai_suggested` 상태로 후보를 저장한다.
- 사용자는 동일한 후보 검토 화면에서 AI 제안값도 체크/수정 후 선택 반영한다.
- 현재 화면은 증빙자료 관리 테이블을 제공하며, 사용자는 업로드 이후에도 상세 검토, 메타데이터 수정, 재처리, 삭제를 수행할 수 있다.
- OCR/파싱 결과가 틀린 경우 상세 화면의 `OCR/파싱 텍스트 보정` 영역에서 텍스트를 직접 수정하고 다시 분석할 수 있다.
- 법인 프로필 준비도 카드는 최종 지원 가능성 판정이 아니라 부족한 법인 정보와 증빙을 빠르게 알려주는 안내 UI다.
- 저장된 나라장터 공고 상세에는 지역, 면허/업종, 기업유형, 제출서류, 금액, 마감일을 `요구조건 구조화 후보`로 보여준다.

증빙자료 탭 목록 컬럼:
- 파일명
- 문서 유형
- 추출 상태
- 유효기간
- 연결된 법인 필드
- 충돌 여부
- 대표 증빙 여부
- 최근 분석일
- 대기 후보 수
- 승인 후보 수

증빙자료 상태:
- 분석 중
- 확인 필요
- 반영 완료
- 충돌 있음
- 만료됨
- 지원 안 됨

## 프로젝트 관리 페이지 UX
- 프로젝트를 최상위 운영 단위로 표시
- 카드/테이블 전환 가능
- 주요 정보
  - 프로젝트명
  - 연결 법인
  - 문서 수
  - 최근 분석 상태
  - 마지막 수정일
- 프로젝트 상세에서 업로드 이력과 분석 결과 접근

## 프로젝트 생성 UX
- 권장: 한 화면 폼 + 생성 후 업로드 유도
- 필수 입력
  - 프로젝트명
  - 법인 선택
- 선택 입력
  - 메모
  - 상태
- 법인이 없는 경우 바로 법인 생성으로 이어지는 동선 제공

## 파일 업로드 UX
- 업로드는 항상 메타데이터 포함
- 입력 항목
  - 프로젝트
  - 문서 파일
  - 문서 유형
  - 메모
  - 개정 메모
- PDF/DOCX만 허용
- 드래그 앤 드롭 + 파일 선택 지원
- 업로드 직후 처리 상태 패널 표시

## 법인 선택 UX
- 검색 가능한 드롭다운
- 표시값
  - 법인명
  - 관리 법인그룹
  - 업종
  - 지역
- 결과가 없으면 `법인 먼저 등록` CTA 제공

## 업로드 히스토리 대시보드/테이블 UX
- 프로젝트 기준 그룹화
- 검색 키워드
  - 프로젝트명
  - 법인명
  - 파일명
- 필터
  - 문서 유형
  - 분석 상태
  - 날짜
- 액션
  - 상세
  - 수정
  - 삭제
  - 재분석

## 분석 결과 페이지 UX
- 상단 헤더
  - 프로젝트명
  - 법인명
  - 문서명
  - 분석 상태 배지
  - 재분석 버튼
- 본문 섹션
  - 한줄 요약
  - 상세 요약
  - 주요 일정
  - 요구사항
  - 제출 문서
  - 위험/불명확 항목
  - 원문 추출 텍스트
- AI 결과와 원문은 시각적으로 분리

## 나라장터 게시판 UX
- 목적은 나라장터 공고를 포탈 안에서 검색하고, 1개 공고를 선택해 저장과 자동 분석을 실행하는 것이다.
- 상단에는 `나라장터 게시판` 제목, API 조회 상태, 마지막 조회 시각을 표시한다.
- 화면은 `검색 영역`, `공고 리스트`, `상세 미리보기`, `하단 액션 바`로 구성한다.
- 공고 리스트는 테이블 중심으로 제공하고, 각 행의 첫 컬럼에 라디오 버튼을 둔다.
- 사용자가 라디오로 1개 공고를 선택해야 `공고 상세 저장` 버튼이 활성화된다.

주요 테이블 컬럼:
- 선택
- 공고명
- 공고기관
- 수요기관
- 공고일시
- 입찰마감
- 추정가격
- 지역
- 업종제한
- 첨부 수
- 저장 여부
- 분석 상태

## 나라장터 공고 검색 UX
- 기본 검색은 공고명, 조회 기간, 지역명, 마감 공고 제외 여부만 노출한다.
- `공고 검색` 페이지에 진입하면 즉시 기본 조건으로 공고 목록을 자동 조회한다.
- 기본 조회 기간은 최근 1개월이다.
- 예: 오늘이 `2026-05-05`이면 `2026-04-05 00:00`부터 `2026-05-05 23:59`까지 조회한다.
- API 키가 미설정이면 자동 조회 대신 `설정 > API 연동`으로 이동하는 안내 배너를 보여준다.
- 상세검색은 드로어 또는 접이식 패널로 제공한다.
- 상세검색 필드는 공고기관명, 수요기관명, 참가제한지역명, 업종명, 추정가격 범위, 공고게시일/개찰일 기준, 페이지 크기를 포함한다.
- 적용된 필터는 검색 영역 아래에 칩으로 보여준다.
- 필터 초기화 버튼을 제공한다.

## 나라장터 공고 상세 UX
- 행 클릭 시 우측 패널 또는 하단 패널에서 상세 미리보기를 제공한다.
- 상세 미리보기는 공고 기본정보, 일정, 금액, 참가 제한 힌트, 첨부파일, 원문 링크로 나눈다.
- 기초금액, 면허제한, 참가가능지역은 상세 조회 시 보강된 정보로 표시한다.
- 원문 링크는 새 창으로 열되, 실제 첨부 분석은 백엔드가 저장한 로컬 파일 기준으로 진행한다.

## 나라장터 첨부파일 다운로드 UX
- 첨부파일 목록에는 파일명, 확장자, 출처 필드, 지원 상태, 다운로드 상태, 액션을 표시한다.
- PDF/DOCX는 `다운로드` 버튼을 제공한다.
- HWP/HWPX/XLSX 등은 `지원 제외` 배지와 안내 툴팁을 표시한다.
- 저장 전에는 외부 URL 기준 다운로드 테스트 또는 미리보기 다운로드를 제공할 수 있다.
- 저장 후에는 로컬에 저장된 파일을 다운로드하게 한다.

## 공고 상세 저장 UX
- `공고 상세 저장`은 라디오로 선택한 1개 공고에만 실행한다.
- 클릭 시 확인 모달을 띄운다.
- 모달에는 PDF/DOCX만 분석하고 HWP/HWPX/XLSX는 메타데이터만 저장한다는 안내를 포함한다.
- 작업 시작 후 진행 상태 패널을 표시한다.

진행 단계:
- 공고 상세 조회
- 기초금액/면허제한/참가가능지역 조회
- 공고 저장
- 첨부파일 다운로드
- PDF/DOCX 파싱
- AI 요약
- 결과 저장

완료 후 CTA:
- `분석 결과 보기`
- `저장된 공고 보기`
- `나라장터 게시판으로 돌아가기`

## 저장된 공고 분석 결과 UX
- 상단에는 공고명, 공고번호/차수, 저장 상태, 분석 상태, 재분석 버튼을 둔다.
- 본문은 공고 메타데이터 요약, 첨부파일 상태, 분석 결과, 원문 추출 텍스트, API 원본 JSON으로 구성한다.
- 분석 결과는 한줄 요약, 공고 핵심 내용, 주요 일정, 금액 정보, 참가 제한 조건, 제출/준비 필요사항, 첨부파일별 요약, 확인 필요 항목으로 나눈다.
- 최종 지원 가능/불가능 판단처럼 보이는 표현은 Phase 1.5에서 사용하지 않는다.

## 저장한 공고 게시판 UX
- `저장한 공고`는 사용자가 `공고 상세 저장`으로 저장한 공고문만 보여주는 내부 게시판이다.
- API 검색 결과와 다르게 DB에 저장된 공고, 다운로드한 첨부파일, 분석 상태, 분석 결과를 기준으로 보여준다.
- 권장 경로는 `/nara-saved-notices`이다.

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

액션:
- 상세 보기
- 분석 결과 보기
- 재분석
- 로컬 첨부파일 다운로드
- 삭제

## 설정/API 연동 UX
- `설정 > API 연동` 메뉴에서 나라장터 API 키 설정 여부와 연결 상태를 확인한다.
- API 키 전체 값은 절대 표시하지 않고 마스킹된 값만 보여준다.
- 프론트엔드로 전체 API 키를 내려주지 않는다.
- 연결 테스트 버튼을 제공한다.

나라장터 API 카드 표시 정보:
- 설정 상태
- 마스킹된 키
- 공고 API base URL
- 표준 데이터 API base URL
- 응답 형식
- 마지막 연결 테스트 시각
- 마지막 연결 테스트 결과

액션:
- 연결 테스트
- 공고 API 테스트
- 첨부 PDF 다운로드 테스트
- 설정 다시 불러오기

상태 메시지:
- 정상: `나라장터 API 연결이 정상입니다.`
- 키 미설정: `NARA_API_SERVICE_KEY가 설정되어 있지 않습니다.`
- 인증 실패: `인증키가 유효하지 않거나 인코딩 키 선택이 잘못되었을 수 있습니다.`
- 승인 필요: `공공데이터포털에서 해당 API 활용신청/승인 상태를 확인해주세요.`

## 재분석 UX
- 재분석 버튼 클릭 시 확인 모달
- 안내 문구: 기존 결과는 보관되고 최신 결과만 대표값으로 갱신
- 실행 중 상태 배지/스피너 표시
- 실패 시 오류 메시지와 재시도 버튼 제공

## 기준 PDF 관리 페이지 UX
- 일반 프로젝트 문서와 분리된 메뉴
- 목록 컬럼
  - 문서명
  - 카테고리
  - 발행기관
  - 버전
  - 유효 시작일
  - 현재 사용 여부
  - 처리 상태
  - 청크 수
  - 추출 규칙 수
  - 최근 처리 시각
- 액션
  - 상세
  - 수정
  - 삭제
  - 재처리
- 기준문서 관리는 단순 PDF 보관함이 아니라 `판단 근거 관리 콘솔`로 설계한다.
- 상세 화면에는 원본 PDF 정보, 처리 상태, 청크 미리보기, 추출된 판단 규칙, 오류 로그, 버전 정보를 표시한다.
- `현재 판단에 사용할 버전`을 명확히 표시하고, 오래된 기준문서는 참고 문서로만 남길 수 있어야 한다.

## 기준 PDF 업로드 UX
- 업로드 시 메타데이터 필수
  - 문서명
  - 카테고리
  - 버전
  - 메모
- 업로드 후 처리 단계 진행 표시
  - 텍스트 추출
  - OCR
  - 청킹
  - 인덱싱

## 기준 PDF 처리 상태 UX
- 상태값 예시
  - uploaded
  - extracting
  - ocr_done
  - chunked
  - indexed
  - failed
- 상세 화면에서 청크 수, 페이지 수, 최근 오류 메시지 제공

## 빈 화면 / 로딩 / 에러 상태
- 빈 화면
  - 첫 법인 등록 CTA
  - 첫 프로젝트 생성 CTA
  - 첫 기준 PDF 업로드 CTA
- 로딩
  - 스켈레톤 카드
  - 진행 문구
- 에러
  - 실패 원인 요약
  - 재시도 버튼
  - 처리 실패 단계 표시

## 모던 어드민 디자인 톤
- 밝은 배경 기반
- 짙은 네이비 + 청록 포인트
- 카드 중심 레이아웃
- 선명한 데이터 테이블
- 절제된 배지 컬러 시스템

## 반응형 메모
- 주 사용 환경은 데스크톱
- 태블릿에서 기본 작업 가능
- 모바일은 조회 중심
- 문서 상세 화면은 작은 화면에서 아코디언 구조 권장

## 컴포넌트 전략
- `AppShell`
- `SidebarNav`
- `TopSearchBar`
- `MetricCard`
- `DataTable`
- `StatusBadge`
- `UploadDialog`
- `AnalysisSectionCard`
- `ProcessingTimeline`
- `ConfirmDialog`
- `NaraNoticeSearchForm`
- `NaraAdvancedSearchDrawer`
- `NaraNoticeTable`
- `NaraNoticePreviewPanel`
- `NaraAttachmentList`
- `NaraSaveProgressDialog`

## 미래 판단 결과 페이지 컨셉
- 상단: 판단 결과 배지
  - 지원 가능
  - 검토 필요
  - 지원 곤란
- 결과 화면의 핵심은 `지원 가능`을 강조하는 것이 아니라 `현재 부족한 조건`과 `준비해야 할 것`을 빠르게 파악하게 하는 것이다.
- 중간: 판단 사유 요약과 차단 조건 카드
- 조건별 매칭 테이블
  - 공고 요구조건
  - 법인 현재 상태
  - 매칭 결과
  - 필요한 인증/면허/서류
  - 근거 조항
- 하단: 준비 체크리스트와 단계별 준비 가이드
- 우측 또는 하단 패널: 기준문서 근거와 인용 조항
- 근거가 부족한 항목은 `검토 필요`로 표시하고 확정적인 문구를 피한다.

## 미래 증거 인용 UI 컨셉
- 근거 문서명, 버전, 페이지, 섹션 표시
- 인용문 하이라이트
- `이 판단에 사용된 근거` 패널 제공
- 클릭 시 기준문서 상세로 이동 가능
- 공고문 원문 근거와 기준문서 근거를 구분해서 표시한다.
- 법인 증빙자료가 판단에 사용된 경우 증빙자료명과 유효기간도 함께 표시한다.

## 가정
- 사용자는 기술 개발자가 아니라 행정 실무자다.
- 한 화면에서 빠르게 훑어보는 UX가 중요하다.
- 장문 문서는 요약 -> 상세 -> 원문 순서가 적합하다.

## Questions for Product Owner
- 대시보드 최우선 KPI가 무엇인지
- 프로젝트 상태값 체계가 필요한지
- 기준문서 버전 노출 수준을 어디까지 둘지
- 분석 결과 인쇄/내보내기가 필요한지

## 권장 프론트엔드 구조
```text
frontend/
  src/
    app/
    pages/
    widgets/
    features/
    entities/
    shared/
```

---

# AI / Engineering Version (English)

## UX Mission
Design a modern admin portal for a non-technical administrator who manages corporations and projects, uploads procurement files, monitors processing states, and reviews AI summaries with confidence.

## Persona
- single administrator
- document-heavy workflow
- needs project-centric history, search, status visibility, and side-by-side AI/source review

## IA
- Dashboard
- Corporations
- Projects
- Analysis Detail
- Nara Board
- Saved Nara Notices
- Basis PDFs
- Settings
- API Integrations

## Navigation
- left sidebar for major modules
- top bar for search and quick status
- Nara Board should expose `Search Notices` and `Saved Notices` as child items or tabs.
- Settings should expose `API Integrations`, including Nara API status and connection tests.

## Key UX Rules
- uploads are never raw-file-only actions
- project is the primary history unit
- re-analysis preserves prior results
- basis PDFs must remain separate from project documents

## Corporation Readiness Input UX
- Corporation registration should minimize manual text entry.
- The first corporation registration screen should start with business registration certificate upload, not a general manual form.
- The administrator selects a management group first. The default is `기본 관리그룹`.
- Existing management groups should be selectable via dropdown/autocomplete; new group names are typed only when needed.
- Duplicate rule: same business registration number + same management group is blocked; same business registration number + different management group is allowed with a warning.
- When the user uploads a certificate, the system should extract corporation name, business registration number, representative name, business address, business type, and business items from image/PDF/Word files.
- The user reviews extracted values and corrects only inaccurate fields.
- Manual input is shown only when the user selects `I do not have a business registration certificate` or `enter manually later`.
- Manual fallback should initially require only corporation name, headquarters region, and representative business category.
- Manually created corporations should show `basic information unverified` or `no evidence`.
- Company type and preferential conditions should use checkbox/toggle cards, not free text.
- Provide quick-select cards for SME confirmation, women-owned business, disabled-owned business, social enterprise, cooperative, venture company, startup company, and direct production certificate.
- Each selected card expands only the required subfields: subtype, expiry date, and linked evidence.
- Licenses and certifications should use searchable dropdowns and quick-select chips.
- Track record, staff, and equipment should start with `none`, `exists`, and `unknown`; detailed fields open only when `exists` is selected.
- Evidence upload plus automatic extraction should be preferred over manual entry.
- Corporation detail should show notice evaluation readiness instead of simple form completion.
- Phase 1.6 makes evidence upload and extraction review the primary corporation-management workflow before Phase 2.

Recommended first screen:

```text
Upload the business registration certificate to auto-fill corporation basic information.

[Upload Business Registration Certificate]
[I do not have it / Enter manually]
```

Extraction review screen:
- left: original document preview
- right: extracted corporation name, registration number, representative name, address, business type, and business items
- field-level confidence or `needs review` badge
- `Confirm and create corporation` button

## Corporation Evidence Extraction UX
- The corporation detail evidence tab accepts evidence documents beyond the business registration certificate.
- Multi-file upload is allowed.
- Each file shows predicted document type, extraction status, validity period, linked profile fields, and conflict status.
- Unknown documents show `AI classification in progress`.
- LLM classification results require user confirmation before profile updates.
- Extraction review shows original document, extracted value, existing value, confidence, and conflicts.
- User can apply, ignore, edit, or map each extracted field to another profile field.
- HWP/HWPX direct parsing remains unsupported; guide users to convert them to PDF.

Phase 1.6 UX review result:
- 1.6A should finish only the evidence-first onboarding screen and business registration extraction review UX.
- 1.6B should expand core evidence cards, evidence tab states, expiration, conflict, and needs-review indicators.
- 1.6C should improve unknown-document AI classification, manual type assignment, re-extraction, and correction history.
- If OCR is unavailable on the local PC, image evidence should show `OCR setup required` and provide manual fallback instead of failing the flow.
- AI classification output must require explicit user confirmation before profile updates.
- Current implementation shows extracted candidates with checkbox selection and editable values.
- Only selected candidates are applied to the corporation profile; unselected candidates remain pending to prevent accidental overwrites.
- Unknown evidence can now be saved as `ai_suggested` when AI classification succeeds.
- AI-suggested candidates use the same checkbox/edit/apply review flow as rule-extracted candidates.
- Current implementation includes an evidence management table with detail review, metadata edit, reprocess, and delete actions.
- OCR/parser text can be manually corrected and re-analyzed from the evidence detail view.
- Corporation readiness cards show missing profile/evidence inputs only; they are not eligibility verdicts.
- Saved Nara notice detail shows structured requirement candidates such as region, licenses, company types, required documents, amount, and deadline.

## Future UX Hooks
- verdict page
- evidence panel
- checklist panel
- confidence/uncertainty note

## Nara Board UX
- Provide a search-first notice board backed by the public data API.
- On page entry, automatically fetch notices with a default one-month date range.
- Use a table with one radio-select column so only one notice can be saved/analyzed per action.
- Support basic search plus an advanced search drawer.
- Show notice detail preview, enrichment data, and attachment list before saving.
- `Save Notice Detail` starts a progress-tracked job: fetch detail -> enrich -> save -> download PDF/DOCX -> parse -> summarize -> persist.
- HWP/HWPX/XLSX attachments must be marked unsupported in the UI.
- Saved notice analysis must not present a final eligibility verdict in Phase 1.5.
- Saved Notices is a separate internal board for locally persisted notices and their download/analysis status.

## Settings UX
- Provide `Settings > API Integrations > Nara`.
- Show configured/unconfigured status, masked key, base URLs, response type, last test time, and last test result.
- Never expose the full API key to the frontend.
- Provide connection, notice API, and attachment PDF download test actions.

## Open Questions
- dashboard KPI priority
- project status taxonomy
- export/print need
- basis version visibility policy
- whether saved Nara notices should immediately connect to projects
- whether construction notices only are enough for the first release
