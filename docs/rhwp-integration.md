# HWP/HWPX 엔진 통합

작성일: 2026-10-02 (Asia/Seoul). 구현 기준: 최신 `main`의 `3e08bef` 및 이번 HWP 통합 변경.

## 적용 범위

- 프로젝트 문서, 법인 증빙자료, 나라장터 공고 첨부의 HWP 5/HWPX를 공통 `extract_document()` 파서에서 읽는다.
- 프로젝트 문서 목록의 **한글 내보내기**에서 문자열 치환과 HWP/HWPX 변환을 실행하고 새 파일을 다운로드한다. 서버 원본과 사용자가 제공한 파일은 덮어쓰지 않는다.
- 치환 저장본을 원본과 요청된 치환 내용으로 검증하고, 형식 변환 저장본을 검증된 입력 텍스트와 대조한다. 공백/줄바꿈 외의 본문 또는 번호 차이가 있으면 다운로드를 차단한다.
- 기준문서는 PDF 전용을 유지한다. 기존 DOCX 계약서 생성은 이 기능과 별개이다.
- 빈 문서는 분석용 텍스트 추출에서 명시적으로 거부하지만, 빈 양식의 변환이나 전체 내용 삭제 후 저장은 허용한다.

## 설치와 설정

```powershell
powershell -NoProfile -File scripts/setup-rhwp.ps1
```

공식 Windows x64 RHWP **0.8.6**을 `backend/tools/rhwp/rhwp.exe`에 설치한다. 설치 파일은 다음 SHA-256과 일치해야 한다.

```text
867e0a84b778ebda92b88433ede301818eaea21e7d58eb77ff9a732f41d170d9
```

바이너리는 Git에 포함하지 않는다. 다른 PC에서는 설치 스크립트를 실행한다. RHWP가 없거나 설정 버전과 다르면 `needs_hwp_setup` 상태를 제공하고 분석 API는 재시도 가능한 503 응답을 반환한다.

설정 예시는 `backend/.env.example`에 있다.

| 설정 | 기본/의미 |
| --- | --- |
| `RHWP_BIN_PATH` | `./tools/rhwp/rhwp.exe`; 지정하면 이 실행 파일을 사용 |
| `RHWP_EXPECTED_VERSION` | `0.8.6`; 설치 버전과 일치해야 함 |
| `RHWP_TIMEOUT_SECONDS` | `60`; 엔진 확인·편집·변환·검증을 포함한 작업 시간 예산 |
| `RHWP_TEMP_DIR` | `./storage/hwp-temp`; 격리된 처리 사본 위치 |
| `RHWP_SOURCE_DIR` | 선택 사항; 지정한 소스 저장소의 `target/release` 또는 `target/debug` 실행 파일 탐색 |

경로를 지정하지 않으면 프로젝트 도구 폴더, 지정된 소스 폴더의 빌드 결과, PATH를 순서대로 확인한다. Linux/macOS에서는 같은 버전의 공식 CLI를 설치하고 `RHWP_BIN_PATH`를 해당 실행 파일로 지정한다. 이번 실제 실행 검증은 Windows에서 수행했다.

## 처리 계약

- 셸을 사용하지 않고 인자 배열로 CLI를 실행한다. 원본 파일을 격리된 사본으로 복사해 처리한다.
- 입력은 최대 50 MiB이다. HWP의 OLE 서명과 HWPX ZIP 본문 구조를 확인한다. HWPX는 최대 10,000개 항목/256 MiB 비압축 데이터, 텍스트 추출은 최대 500쪽/1,000,000자이다.
- JSON 스키마 버전, 페이지 순서, 텍스트 유형, 생략/절단 여부를 확인한다. 불완전한 텍스트를 정상 분석 결과처럼 반환하지 않는다.
- 치환 건수가 0이면 편집 성공으로 처리하지 않는다. 출력은 검증을 통과한 뒤 새 경로에 배타적으로 생성한다.
- 원본 요청에서 기대한 치환 결과와 편집본을 먼저 대조하므로, 편집 과정의 다른 내용 변경도 차단한다. 이후 변환본의 텍스트를 다시 검증한다.
- 변환 시 RHWP의 IR 및 페이지 수 검증도 실행한다. 이 검증만으로 텍스트/번호 보존을 보장하지 않으므로 별도의 본문 검증이 필요하다.
- 원본 읽기, JSON 오류, 시간 초과, 설정 누락, 검증 실패를 구분한다. 원문이나 엔진 stderr를 오류 응답으로 노출하지 않는다.

API:

```text
GET  /api/settings/hwp-engine/status
POST /api/documents/{document_id}/hwp-export
     {"format":"hwp|hwpx", "find":"optional literal", "replace":"optional literal"}
```

입력/출력 경로는 요청으로 받지 않는다. DB의 문서 식별자와 서버 저장 경로를 사용하며, 출력은 첨부 파일 응답이다. `find`를 생략하면 형식 변환만 수행한다. 본문 검증 실패는 422와 `hwp_edit_verification_failed` 또는 `hwp_text_verification_failed`를 반환한다.

## 실제 검증 결과

합성 HWP/HWPX 픽스처, 독립 코드 검토, 전체 백엔드 unittest, 프론트엔드 빌드, 격리된 Chromium 다운로드 흐름을 검증했다. 사용자가 제공한 실제 HWP 두 개도 외부 AI 호출 없이 로컬 서비스 API로 시험했다.

| 실제 문서 | RHWP 추출 지표 | 결과 |
| --- | --- | --- |
| 관광사업 등록신청서 | 엔진 기준 2쪽 / 4,043자 | 읽기·서비스 분석·HWP 치환 저장·HWPX 변환·HWP 왕복 모두 확인 |
| 관광호텔 사업계획 승인 신청 안내 | 엔진 기준 30쪽 / 35,401자 | 읽기·서비스 분석·HWP 치환 저장 확인. HWPX 변환에서 항목 번호 `1.`→`6.` 차이를 검출하여 배포 차단 |

두 원본의 SHA-256이 검증 전후 동일했다. 검증용 HWP 사본에는 `[엔진 검증용]` 표시를 넣었다. 실제 파일, 변환본, 테스트 DB, 본문은 Git에 포함하지 않는다. 상세 로컬 결과는 `temp/rhwp-acceptance-20261002/report.json`에 있다.

## 검증 한계

- 위쪽 수는 RHWP 엔진 결과이며, 한컴 프로그램에서 직접 열어 확인한 쪽수나 시각적 동일성 검증은 아니다.
- 안내 문서의 HWPX 변환은 호환성 한계가 남아 있다. 원래 HWP 형식으로 내보내기는 성공했으며, 번호가 바뀐 HWPX는 성공 파일로 제공하지 않는다.
- 이미지 전용 HWP의 OCR, HWP 3, 암호 입력, 전체 워드프로세서 UI는 이번 범위에 포함하지 않았다.
- 이번 PC에는 Python 3.12.10만 설치되어 이 환경에서 시험했다. 저장소 표준 Python 3.13.13의 실행 및 실제 PaddleOCR/Java PDF 리더는 별도 확인이 필요하다.
- 빈 텍스트의 분석 실패와 빈 문서의 내보내기는 구분한다. 네이티브 CLI가 없는 환경에서는 네이티브 전용 테스트가 생략되고, 미설치 오류 계약은 계속 검증된다.

## 라이선스와 출처

사용자가 제공한 RHWP 소스 `680111ec7bea2fe11110de18c3676ba5a1cf7847`을 확인하고, 실행은 공식 0.8.6 바이너리를 사용했다. RHWP 소스는 변경하지 않았다. MIT 저작권 고지는 `backend/third_party/RHWP-LICENSE.txt`에 보존했다.

- [RHWP 공식 저장소](https://github.com/edwardkim/rhwp)
- [0.8.6 공식 릴리스](https://github.com/edwardkim/rhwp/releases/tag/v0.8.6)
- [CLI 계약 문서](https://github.com/edwardkim/rhwp/blob/devel/mydocs/manual/cli_commands.md)

## Questions for Product Owner

- HWPX의 번호 보존 문제가 수정된 새 엔진 버전은 같은 실제 문서로 재검증한 뒤 도입한다.
- 향후 누름틀/표 셀 입력이나 한글 문서 전체 편집 UI가 필요하면 현재 문자열 치환/변환과 별도 기능으로 정의한다.

---

# AI / Engineering Version (English)

RHWP 0.8.6 is integrated as a bounded subprocess adapter behind the existing common parser. HWP 5/HWPX now enter project-document, corporation-evidence and Nara-attachment workflows. Basis ingestion remains PDF-only; existing DOCX contract generation is unchanged.

The approved write scope is literal find/replace and HWP/HWPX export into a separate downloaded file. The engine copies inputs into private staging, enforces signature/container/text/time limits, validates JSON/page coverage, checks edits against the original plus the requested replacement, verifies serialization, then publishes exclusively. Empty text is permitted for write verification but rejected for successful analysis. Missing/incompatible binaries yield `needs_hwp_setup`; native-only tests are optional when the runtime is absent.

Install the pinned Windows CLI using `scripts/setup-rhwp.ps1`. The release archive SHA-256 is recorded above; runtime binaries and processing directories are ignored by Git. The MIT notice is retained in `backend/third_party/RHWP-LICENSE.txt`. The supplied RHWP checkout was inspected without source changes; the production integration uses the official release binary rather than an unverified source build.

Verification includes the backend unittest suite, native synthetic read/edit/round-trip checks, frontend build and an isolated real Chromium export/download/reparse flow. Two user-supplied HWP files were tested through an offline local service API. Their original hashes remained unchanged, and both passed native HWP reading/analysis/edit export. The registration form also passed HWPX/HWP round-trip checks. The 30-page engine-rendered guide changed one list number during HWPX conversion despite upstream IR/page checks; the independent text check rejects that export with 422. Native HWP export remains available. This is a known compatibility limit, not a fully passed HWPX result.

Actual document bodies, original private paths, artifacts and test databases are not committed. Hancom visual fidelity and Python 3.13.13 execution were not tested; this PC's verification used Python 3.12.10. OCR-only HWP, password input, HWP 3 and a full word-processing editor remain outside the approved bounded scope.
