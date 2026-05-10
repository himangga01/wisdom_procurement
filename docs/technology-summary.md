# 한국어 버전

## 문서 목적
이 문서는 현재 프로젝트의 Markdown 문서들을 바탕으로 `SMART 조달청 계산기`의 핵심 기술 요소와 활용 기술을 한눈에 정리합니다.

참고 문서:
- `README.md`
- `docs/technical-design.md`
- `docs/ux-design.md`
- `docs/ai-api-setup.md`
- `docs/narajangteo-api-analysis.md`
- `docs/narajangteo-api-test-result-20260505.md`
- `docs/narajangteo-board-design.md`
- `docs/work-log.md`
- `AGENTS.md`

## 한줄 요약
`SMART 조달청 계산기`는 로컬 PC에서 실행되는 조달문서/나라장터 공고 분석 포탈이며, 핵심은 `공고/문서 수집 -> PDF/DOCX 텍스트 추출 -> OCR 후보 판정 -> AI 구조화 요약 -> 로컬 저장/재조회 -> 향후 RAG 기반 판단 확장`입니다.

## 핵심 기술 요소

### 1. 로컬 우선 관리자 포탈
서비스는 단일 관리자 사용자가 로컬 PC에서 운영하는 웹 포탈입니다.

핵심 의미:
- 초기 Phase에서는 로그인 없이 빠르게 사용합니다.
- SQLite와 로컬 파일 저장소를 사용해 단일 PC 운영을 단순화합니다.
- 향후 인증/권한을 추가할 수 있도록 구조는 확장 가능하게 유지합니다.

### 2. 법인/프로젝트 중심 데이터 구조
일반 업로드 문서는 단순 파일이 아니라 `법인 -> 프로젝트 -> 문서 -> 분석 결과` 흐름으로 관리합니다.

핵심 의미:
- 프로젝트가 이력 관리의 중심입니다.
- 법인 정보는 향후 자격 판단의 입력값이 됩니다.
- 분석 결과는 파일 단위로 누적 저장하고 재분석 이력을 남길 수 있습니다.

### 3. 나라장터 공고 수집/저장 구조
Phase 1.5에서는 나라장터 사이트 HTML 크롤링이 아니라 공공데이터 API를 사용합니다.

핵심 흐름:
```text
나라장터 공고 검색
-> 공고 1개 선택
-> 공고 상세 저장
-> 상세/기초금액/면허제한/참가가능지역 API 재조회
-> 첨부 PDF/DOCX 자동 다운로드
-> 파싱
-> AI 요약
-> 저장한 공고 게시판에서 재조회
```

핵심 의미:
- `공고 검색`은 외부 API 조회 화면입니다.
- `저장한 공고`는 사용자가 저장한 내부 공고 게시판입니다.
- 공고 검색 진입 시 기본 조회 기간은 최근 1개월입니다.
- HWP/HWPX/XLSX는 분석하지 않고 지원 제외 메타데이터로 저장합니다.

### 4. 문서 파싱과 레이아웃 보정
조달 공고 PDF는 표, 항목 번호, 날짜, 금액이 붙어서 추출되는 경우가 많기 때문에 단순 텍스트 추출만으로는 부족합니다.

핵심 방식:
- PDF 기본 추출 엔진은 `PyMuPDF`입니다.
- 페이지별 텍스트, 블록 수, 문자 수, OCR 필요 여부를 메타데이터로 남깁니다.
- 조달문서에서 깨지기 쉬운 항목 번호, 날짜, 금액 주변을 정규화합니다.
- DOCX는 `python-docx`로 추출합니다.

### 5. OCR fallback 구조
모든 PDF에 OCR을 무조건 적용하지 않습니다.

핵심 방식:
- 텍스트 레이어가 충분하면 OCR을 생략합니다.
- 추출 텍스트가 부족하거나 이미지형 PDF로 판단되면 OCR fallback으로 전환합니다.
- OCR 후보는 `PaddleOCR` 우선, 경량 대안은 `Tesseract(kor+eng)`입니다.
- Stirling PDF는 메인 reader가 아니라 향후 PDF 전처리/OCR 보조 서버 후보입니다.

### 6. AI 구조화 요약
Phase 1의 AI 목표는 최종 판단이 아니라 요약입니다.

핵심 방식:
- 기본 Provider/모델은 Google Gemini `gemini-2.5-flash`입니다.
- 보조 Provider/모델은 OpenAI `gpt-5.4-mini`, `gpt-5.4`입니다.
- 포탈에서 분석 실행 시 사용할 Provider/모델을 선택할 수 있습니다.
- 출력은 JSON 구조화 결과와 사용자용 Markdown 요약을 함께 고려합니다.
- 문서에 없는 내용은 생성하지 않도록 프롬프트를 설계합니다.
- API 키가 없거나 실패하면 내부 fallback 요약으로 UI/흐름 테스트가 가능합니다.

### 7. 분석 캐시와 재분석
같은 문서를 반복 분석할 때 비용과 시간을 줄이고, 결과 재현성을 확보합니다.

핵심 방식:
- 캐시 키는 `input_hash + prompt_version + model_name` 기준입니다.
- 재분석 버튼은 강제 재실행입니다.
- 모델명, 프롬프트 버전, 사용량 정보를 저장합니다.
- 이전 분석 결과는 보존하고 최신 결과만 대표값으로 연결합니다.

### 8. 기준문서 RAG 준비
Phase 2에서는 기준 PDF를 향후 판단 엔진의 지식 자산으로 변환합니다.

핵심 흐름:
```text
기준 PDF 업로드
-> 텍스트 추출
-> OCR
-> 정규화
-> 자동 청킹
-> 청크 메타데이터 생성
-> 임베딩
-> 로컬 벡터 인덱싱
```

핵심 의미:
- 사용자가 직접 청킹하지 않습니다.
- 기준문서는 일반 프로젝트 문서와 분리됩니다.
- 향후 근거 조항 검색, citation, 자격 판단에 사용됩니다.

### 9. API 키/보안 설정
나라장터와 AI API 키는 외부 서비스 연동의 핵심 보안 자산입니다.

핵심 방식:
- API 키는 `.env` 또는 OS 환경변수로 관리합니다.
- 프론트엔드에는 전체 키를 절대 내려주지 않습니다.
- 설정 화면에는 설정 여부, 마스킹된 키, base URL, 마지막 연결 테스트 결과만 표시합니다.
- 실제 키 값은 문서/로그/테스트 결과에 저장하지 않습니다.

### 10. 처리 상태와 실패 복구
문서 분석은 여러 단계가 있으므로 상태 추적이 중요합니다.

핵심 상태 예시:
- `queued`
- `fetching_notice`
- `downloading_attachments`
- `parsing_documents`
- `summarizing`
- `completed`
- `partial_failed`
- `failed`

핵심 의미:
- 일부 첨부 다운로드가 실패해도 나머지 처리는 계속할 수 있습니다.
- 실패 단계와 오류 메시지를 남겨 재시도할 수 있게 합니다.

## 활용 기술

### 프론트엔드
| 기술 | 용도 |
|---|---|
| React | 관리자 포탈 UI |
| TypeScript | 화면/데이터 타입 안정성 |
| Vite | 빠른 개발 서버와 빌드 |
| React Router | 페이지 라우팅 |
| 경량 API 클라이언트 + React state | 현재 Phase 1 포탈의 API 호출/상태 관리 |
| TanStack Query / React Hook Form | 데이터 캐싱과 복잡한 폼이 늘어날 때 검토할 확장 후보 |
| Node.js 20+ | 프론트엔드 개발/빌드 런타임 |

### 백엔드
| 기술 | 용도 |
|---|---|
| Python 3.13.13 | 문서 처리, API 서버, OCR, AI 연동 |
| FastAPI | 설계상 권장 백엔드 프레임워크 |
| Flask | 현재 Phase 1 실제 구현 런타임 |
| SQLAlchemy | 설계상 ORM 계층 |
| Pydantic | 설계상 요청/응답 스키마 검증 |
| Background Tasks 또는 Worker Queue | 긴 문서 분석/다운로드 작업 확장 |

주의:
- 현재 Phase 1 실제 구현은 Flask 단일 파일 백엔드가 기준입니다.
- FastAPI, SQLAlchemy, Pydantic은 향후 구조화/마이그레이션 후보로만 유지합니다.
- Phase 1.6 작업에는 FastAPI 마이그레이션을 섞지 않습니다.

### 데이터 저장
| 기술 | 용도 |
|---|---|
| SQLite | 로컬 단일 PC DB |
| Local filesystem | 업로드 파일, 다운로드 첨부파일, 기준 PDF 저장 |
| JSON 컬럼/텍스트 | 원본 API 응답, 분석 결과, 메타데이터 저장 |

### 문서 처리
| 기술 | 용도 |
|---|---|
| PyMuPDF | PDF 텍스트/블록/페이지 메타데이터 추출 |
| python-docx | DOCX 문단/표 텍스트 추출 |
| PaddleOCR | 한국어 OCR fallback 우선 후보 |
| Tesseract(kor+eng) | 경량 OCR fallback 후보 |
| Stirling PDF | 향후 PDF 전처리/OCR 보조 서버 후보 |

### AI / LLM
| 기술 | 용도 |
|---|---|
| Gemini `gemini-2.5-flash` | 기본 요약/구조화 모델 |
| OpenAI `gpt-5.4-mini` | 선택 가능한 OpenAI 요약 모델 |
| OpenAI `gpt-5.4` | 정밀 재분석/향후 판단 보조 모델 후보 |
| Provider/model selector | 포탈에서 분석 실행 시 모델 선택 |
| 구조화 JSON 출력 | 일정, 금액, 요구사항, 위험 항목 등 정리 |
| Markdown 요약 | 사용자 친화적 결과 표시 |
| 내부 fallback 요약 | API 키가 없거나 실패할 때 개발/테스트용 요약 |

### 나라장터 API
| API | 용도 |
|---|---|
| `BidPublicInfoService` | 공고 검색/상세/첨부 수집의 1순위 API |
| `getBidPblancListInfoCnstwkPPSSrch` | 공사 공고 검색 |
| `getBidPblancListInfoCnstwk` | 공사 공고 상세/목록 |
| `getBidPblancListInfoCnstwkBsisAmount` | 기초금액 조회 |
| `getBidPblancListInfoLicenseLimit` | 면허/업종 제한 조회 |
| `getBidPblancListInfoPrtcptPsblRgn` | 참가가능지역 조회 |
| `getBidPblancListInfoEorderAtchFileInfo` | e발주 첨부파일 조회 |
| `PubDataOpnStdService` | 표준 입찰/낙찰/계약 데이터 보조 후보 |

검증된 내용:
- 실제 API 호출에서 정상 응답을 확인했습니다.
- PDF 첨부 다운로드도 HTTP 200, `application/pdf`, `%PDF` 시그니처로 검증했습니다.

### RAG / 지식베이스
| 기술 | 용도 |
|---|---|
| 자동 청킹 | 기준 PDF를 검색 가능한 단위로 분할 |
| Embedding | 기준문서 의미 검색용 벡터 생성 |
| Qdrant | 로컬 벡터 저장소 우선 후보 |
| Chroma | 단순 프로토타입용 대안 |
| Citation metadata | 근거 조항, 페이지, 섹션 표시 |

### 운영/테스트 도구
| 도구 | 용도 |
|---|---|
| `scripts/manage-servers.ps1` | FE/BE 서버 시작/중지/재시작 |
| `scripts/smoke-test.ps1` | 법인 생성부터 분석 조회까지 스모크 테스트 |
| `scripts/test-nara-api.py` | 나라장터 API 및 첨부 PDF 다운로드 테스트 |
| Python `unittest` | 백엔드 파서 단위 테스트 |

## 단계별 기술 적용 요약
| 단계 | 핵심 기술 |
|---|---|
| Phase 1 | React 포탈, 로컬 DB, 파일 업로드, PyMuPDF/DOCX 파싱, AI 요약, 재분석 |
| Phase 1.5 | 나라장터 API, 공고 검색, 저장한 공고, 첨부 PDF/DOCX 다운로드, 공고 분석 |
| Phase 2 | 기준 PDF 관리, OCR, 자동 청킹, 임베딩, 로컬 벡터 인덱싱 |
| Phase 3 | 법인-공고 요건 매칭, RAG 근거 검색, 판단 엔진, 체크리스트/가이드 생성 |

## 현재 주의할 점
- HWP/HWPX는 현재 범위 제외입니다.
- Phase 1.5는 요약까지이며 최종 지원 가능/불가능 판단은 하지 않습니다.
- 나라장터 API 키는 전체 값을 화면, 로그, 문서에 노출하면 안 됩니다.
- 설계상 백엔드는 FastAPI 권장이지만 현재 구현은 Flask이므로 다음 구현 전에 방향을 결정해야 합니다.
- 기준문서 RAG는 설계/확장 대상이며 현재 최종 판단에는 사용하지 않습니다.

---

# AI / Engineering Version (English)

## Purpose
This document summarizes the core technical elements and technology stack of `SMART Procurement Calculator` based on the current repository Markdown documents.

## One-Line Summary
The service is a local-first procurement document and Nara Marketplace notice analysis portal. Its core pipeline is `ingest notice/document -> extract PDF/DOCX text -> detect OCR need -> structured AI summary -> local persistence -> future RAG-based judgment`.

## Core Technical Elements

### 1. Local-First Admin Portal
- Single administrator in Phase 1.
- Local SQLite and filesystem storage.
- No auth in Phase 1, but architecture should remain auth-ready.

### 2. Corporation / Project Data Model
- Target uploads are managed as `corporation -> project -> document -> analysis`.
- Corporation attributes become future eligibility inputs.
- Analyses are versioned and re-analysis preserves history.

### 3. Nara Marketplace Notice Ingestion
Phase 1.5 uses public data APIs, not HTML crawling.

```text
search notices
-> select one notice
-> save notice detail
-> refetch detail/enrichment APIs
-> download PDF/DOCX attachments
-> parse
-> summarize
-> show in Saved Notices
```

### 4. Document Parsing and Layout Normalization
- PDF extraction: `PyMuPDF`.
- DOCX extraction: `python-docx`.
- Store page/block/character/OCR-needed metadata.
- Normalize procurement-specific clause numbers, dates, amounts, and table-like text.

### 5. OCR Fallback
- OCR is not applied to every PDF.
- Use OCR only when extracted text is insufficient or pages appear image-based.
- Preferred OCR candidate: `PaddleOCR`.
- Lightweight candidate: `Tesseract(kor+eng)`.
- Stirling PDF is optional future preprocessing/OCR helper, not the primary reader.

### 6. Structured AI Summarization
- Default provider/model: Gemini `gemini-2.5-flash`.
- Selectable OpenAI alternatives: `gpt-5.4-mini`, `gpt-5.4`.
- Portal users can choose the provider/model for analysis and re-analysis.
- Output should include structured JSON and user-readable Markdown.
- No unsupported eligibility verdicts in Phase 1/1.5.
- Fallback summary supports development/testing when API keys are absent.

### 7. Cache and Re-analysis
- Cache key: `input_hash + prompt_version + model_name`.
- Re-analysis forces a rerun.
- Store model name, prompt version, and usage metadata for reproducibility.

### 8. Basis Document RAG Preparation
Phase 2 converts basis PDFs into retrieval-ready knowledge assets:

```text
basis PDF upload
-> extract/OCR
-> normalize
-> auto chunk
-> metadata
-> embedding
-> local vector index
```

### 9. API Key Security
- Store keys in `.env` or OS environment variables.
- Never return full API keys to the frontend.
- Settings screens show configured status, masked key, base URLs, and last connection test.

### 10. Job Status and Failure Recovery
- Long-running notice/document workflows need explicit statuses.
- Partial attachment failures should not always fail the whole job.
- Store failed step and error message to support retry.

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- React Router
- lightweight API client + React state in the current implementation
- TanStack Query / React Hook Form as future candidates when caching/forms grow
- Node.js 20+

### Backend
- Python 3.13.13
- Current Phase 1 runtime uses Flask.
- FastAPI, SQLAlchemy, and Pydantic are future refactor candidates, not active runtime dependencies.
- Background tasks or worker queues are planned for long-running jobs.

### Storage
- SQLite
- Local filesystem
- JSON/text fields for raw API payloads, metadata, and analysis outputs

### Document Processing
- PyMuPDF
- python-docx
- PaddleOCR
- Tesseract
- Stirling PDF as optional future helper

### AI / LLM
- Gemini `gemini-2.5-flash`
- OpenAI `gpt-5.4-mini`
- OpenAI `gpt-5.4`
- Provider/model selector
- Structured JSON output
- Markdown summary
- Deterministic internal fallback summary

### Nara APIs
- `BidPublicInfoService`
- `PubDataOpnStdService`
- `getBidPblancListInfoCnstwkPPSSrch`
- `getBidPblancListInfoCnstwk`
- `getBidPblancListInfoCnstwkBsisAmount`
- `getBidPblancListInfoLicenseLimit`
- `getBidPblancListInfoPrtcptPsblRgn`
- `getBidPblancListInfoEorderAtchFileInfo`

### RAG / Knowledge Base
- Automatic chunking
- Embeddings
- Qdrant preferred
- Chroma optional
- Citation metadata for future evidence rendering

### Ops / Testing
- `scripts/manage-servers.ps1`
- `scripts/smoke-test.ps1`
- `scripts/test-nara-api.py`
- Python `unittest`

## Phase Mapping
| Phase | Core Technologies |
|---|---|
| Phase 1 | React portal, SQLite, file upload, PyMuPDF/DOCX parsing, AI summary, re-analysis |
| Phase 1.5 | Nara API, notice board, Saved Notices, PDF/DOCX attachment download, notice analysis |
| Phase 2 | Basis PDF ingestion, OCR, automatic chunking, embeddings, local vector index |
| Phase 3 | corporation-notice matching, RAG retrieval, judgment engine, checklist/guide generation |

## Notes
- HWP/HWPX is out of scope.
- Phase 1.5 produces summaries, not eligibility verdicts.
- Full API keys must never be exposed in frontend responses, logs, or docs.
- Backend direction should be clarified before larger implementation: continue Flask or move toward the documented FastAPI architecture.
