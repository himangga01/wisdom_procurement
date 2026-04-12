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
- Future Notice Dashboard

## 페이지 목록
- `/dashboard`
- `/corporations`
- `/corporations/:id`
- `/projects`
- `/projects/new`
- `/projects/:id`
- `/documents/:id/analysis`
- `/basis-documents`
- `/basis-documents/:id`

## 내비게이션 구조
- 좌측 사이드바
  - Dashboard
  - Corporations
  - Projects
  - Basis PDFs
- 상단 바
  - 검색
  - 최근 작업
  - 처리 상태 표시

## 법인 관리 페이지 UX
- 상단에 `법인 추가` 버튼
- 중앙에 테이블 배치
- 주요 컬럼
  - 법인명
  - 업종/분류
  - 지역
  - 인증/면허
  - 회사 규모
  - 최근 수정일
- 상세 패널 또는 상세 페이지에서 내부 메모 확인
- 삭제 시 연관 프로젝트 존재 여부 경고

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
  - 버전
  - 처리 상태
  - 최근 처리 시각
- 액션
  - 상세
  - 수정
  - 삭제
  - 재처리

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

## 미래 판단 결과 페이지 컨셉
- 상단: 판단 결과 배지
  - 지원 가능
  - 검토 필요
  - 지원 곤란
- 중간: 판단 사유 요약
- 하단: 체크리스트와 준비 가이드
- 우측 또는 하단 패널: 근거 문서와 인용 조항

## 미래 증거 인용 UI 컨셉
- 근거 문서명, 버전, 페이지, 섹션 표시
- 인용문 하이라이트
- `이 판단에 사용된 근거` 패널 제공
- 클릭 시 기준문서 상세로 이동 가능

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
- Basis PDFs
- Future Notice Dashboard

## Navigation
- left sidebar for major modules
- top bar for search and quick status

## Key UX Rules
- uploads are never raw-file-only actions
- project is the primary history unit
- re-analysis preserves prior results
- basis PDFs must remain separate from project documents

## Future UX Hooks
- verdict page
- evidence panel
- checklist panel
- confidence/uncertainty note

## Open Questions
- dashboard KPI priority
- project status taxonomy
- export/print need
- basis version visibility policy
