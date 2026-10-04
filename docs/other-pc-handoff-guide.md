# 다른 PC 작업 인수인계 가이드

## 한국어 버전

최종 갱신일: 2026-08-21

## 문서 목적

이 문서는 다른 Windows PC에서 `SMART 조달청 계산기`의 개발과 로컬 실행을 이어가기 위한 인수인계 기준입니다. 소스 코드만 이어가는 경우와 기존 PC의 운영 데이터까지 이어가는 경우를 구분합니다.

## 1. 현재 기준

- 기준 브랜치: `main`
- 원격 저장소: `https://github.com/himangga01/wisdom_procurement.git`
- 백엔드: Python 3.13.13, Flask, SQLite
- 프론트엔드: React, TypeScript, Vite
- PDF: OpenDataLoader 우선 `auto`, PyMuPDF fallback
- OCR: PaddleOCR PP-OCRv5, 미설치 시 degrade/fallback
- AI: Gemini 2.5 Flash 기본, OpenAI 선택 가능
- 로컬 주소: 백엔드 `http://127.0.0.1:18111`, 프론트엔드 `http://127.0.0.1:5199`
- 고정 외부 주소: `https://smart.kang.ngrok.pro`
- 최신 기능 및 남은 작업: [README](../README.md), [남은 개발 단계 로드맵](remaining-development-roadmap.md)

최신 커밋은 고정된 문서값을 믿지 말고 새 PC에서 직접 확인합니다.

```powershell
git switch main
git pull --ff-only origin main
git log -1 --oneline --decorate
git status --short --branch
```

## 2. 반드시 별도로 준비할 항목

Git으로 전달되지 않는 항목:

- `backend/.env`: Gemini, OpenAI, 나라장터 API 키와 로컬 설정
- `frontend/.env`: 로컬 프론트 API 설정
- `backend/app.db`: 현재 법인, 프로젝트, 문서, 공고, 판단, 작업 이력 데이터
- `backend/storage/` 전체: 업로드, 기준문서/인덱스, 증빙, 계약서, 백업, OCR 중간 파일과 로그
- `temp/`: 서버/ngrok 상태 파일과 임시 로그
- ngrok 로컬 인증 설정
- PaddleOCR/PaddleX 모델 캐시

복사하지 않아도 되는 항목:

- `frontend/node_modules/`
- `frontend/dist/`
- `__pycache__/`, `.pytest_cache/`
- `temp/*.status.json`
- Python 패키지 설치 폴더

주의:

- `.env`와 `app.db`는 `.gitignore` 대상이므로 `git clone`만으로 기존 운영 상태가 복원되지 않습니다.
- 저장소에는 `source/test_doc/`, `source/rag_doc/`, 명시적 데모 영상 산출물이 추적되어 있습니다.
- 2026-10-04부터 `backend/storage/` 전체는 운영 데이터로 분리해 Git 추적을 해제했습니다. 새 clone으로 운영 DB/스토리지/인덱스/백업이 이전되지 않습니다.
- 기존 다른 PC에서 이 추적 해제 커밋을 pull하면 이전에 추적되던 스토리지 파일이 제거될 수 있으므로, 먼저 그 PC의 운영 DB와 스토리지를 별도 위치에 백업하세요. 이 정리 작업을 수행한 현재 PC에서는 `git rm --cached`로 로컬 파일을 보존했습니다.
- 현재 Git pack 크기는 약 326 MiB이며, 초기 clone과 checkout에 시간이 걸릴 수 있습니다.

## 3. 보안 확인 사항

`gpt api.txt`는 과거 credential 패턴과 일치했던 파일입니다. 2026-10-04 현재 트리의 Git 추적을 해제하고 ignore 규칙을 추가했으며 로컬 파일은 보존했습니다. 과거 Git 이력에는 남아 있고 유효성은 시험하지 않았습니다. 값은 이 문서에 기록하지 않습니다.

다른 PC에서 작업하기 전에 다음 조치가 필요합니다.

1. 해당 키를 더 이상 신뢰하지 않고 발급 서비스에서 회전 또는 폐기합니다.
2. 새 키는 `backend/.env`에만 입력합니다.
3. 현재 트리의 추적 해제와 별개로, 과거 Git 이력 정리는 명시적 승인 후 진행합니다. 이번 정리는 키 회전이나 이력 재작성을 수행하지 않습니다.
4. 키 원문을 README, 작업 로그, 화면 캡처, 커밋 메시지에 남기지 않습니다.

고정 ngrok 주소는 인증 기능이 없는 현재 포탈을 외부에 공개합니다. 개발/시연 중에만 실행하고 URL 공유 범위를 제한합니다.

## 4. 새 PC 설치

필수 설치:

- Git
- Windows PowerShell
- Python 3.13.13과 Windows Python Launcher
- Node.js 20.19.0 이상 또는 22.12.0 이상
- Java 11 이상
- 실제 OCR을 사용할 경우 PaddleOCR 의존성
- 외부 접속을 사용할 경우 ngrok CLI

확인 명령:

```powershell
git --version
py -3.13 --version
node -v
npm -v
java -version
ngrok version
```

## 5. 저장소 준비

```powershell
git clone https://github.com/himangga01/wisdom_procurement.git
cd wisdom_procurement
git switch main
git pull --ff-only origin main
```

사용자 지침에 따라 기능 작업은 별도 브랜치가 아니라 `main`에서 이어갑니다. 작업 전에는 반드시 원격과 동기화 상태를 확인합니다.

```powershell
git status --short --branch
git rev-list --left-right --count origin/main...main
```

## 6. 의존성 설치

백엔드:

```powershell
cd backend
py -3.13 -m pip install --upgrade pip
py -3.13 -m pip install -r requirements.txt
cd ..
```

실제 OCR까지 사용하는 경우:

```powershell
cd backend
py -3.13 -m pip install -r requirements-ocr.txt
cd ..
```

프론트엔드와 Playwright:

```powershell
cd frontend
npm install
npx playwright install chromium
cd ..
```

## 7. 환경 파일 설정

```powershell
Copy-Item backend\.env.example backend\.env -ErrorAction SilentlyContinue
Copy-Item frontend\.env.example frontend\.env -ErrorAction SilentlyContinue
```

`backend/.env`에 새 PC에서 사용할 키를 직접 입력합니다.

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
NARA_API_SERVICE_KEY=
```

권장 PDF/OCR 설정:

```env
AI_PROVIDER_DEFAULT=gemini
AI_MODEL_DEFAULT=gemini-2.5-flash
PDF_READER_ENGINE=auto
OCR_ENGINE=paddle
OCR_LANGUAGES=kor+eng
```

API 키는 메신저 평문, Git, 문서 파일로 옮기지 말고 암호화된 비밀관리 수단을 사용합니다.

## 8. 기존 운영 데이터까지 이전하는 경우

소스 코드만 이어가는 경우 이 단계는 건너뜁니다.

기존 PC에서 먼저 서버를 중지합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 stop
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action stop
```

서버 중지 후 다음 항목을 암호화된 저장매체 또는 안전한 내부 전송수단으로 옮깁니다.

- `backend/app.db`
- `backend/storage/`
- 필요한 경우 `backend/.env`, `frontend/.env`

새 PC의 동일한 상대경로에 배치한 뒤 서버를 실행합니다. 현재 제품은 백업 ZIP 생성·검증·복원계획 dry-run까지만 제공하며 실제 자동 복원은 구현되어 있지 않습니다. 따라서 DB와 스토리지를 복사할 때는 원본을 별도 보관하고 덮어쓰기 전에 대상 파일을 확인해야 합니다.

`temp/`, PID 상태 파일, 기존 PC의 ngrok 상태 파일은 복사하지 않습니다.

## 9. 로컬 서버 실행

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action status
```

접속:

- 포탈: `http://127.0.0.1:5199`
- 백엔드: `http://127.0.0.1:18111`

중지:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action stop
```

알려진 이식성 제한:

- `scripts/manage-servers.ps1`의 일반 경로 계산은 저장소 위치를 기준으로 하지만, 보조 프로세스 검색 조건 한 곳에 `D:\project\wisdom_procurement`가 남아 있습니다.
- 다른 경로에서도 status 파일과 포트 기반 종료는 동작하지만, 상태 파일이 사라진 오래된 프로세스 탐지는 제한될 수 있습니다.
- 이 제한을 피하려면 현재와 같은 `D:\project\wisdom_procurement` 경로를 사용하거나, 후속 코드 수정에서 절대경로 조건을 `$Root` 기반으로 바꿉니다.

## 10. 고정 ngrok 주소 사용

고정 도메인을 소유한 같은 ngrok 계정의 인증 토큰이 필요합니다. 동일 도메인은 동시에 여러 PC에서 사용할 수 없으므로 기존 PC의 endpoint를 먼저 중지합니다.

```powershell
ngrok config add-authtoken <new-or-authorized-token>
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 status
```

공개 주소:

- 포탈: `https://smart.kang.ngrok.pro`
- API: `https://smart.kang.ngrok.pro/api`

중지:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 stop
```

## 11. 테스트 자료와 데모 자료

Git에 포함된 대표 자료:

- 법인 증빙 샘플: `source/test_doc/`
- 기준문서 샘플: `source/rag_doc/`
- 데모 영상 스크립트: `scripts/create-service-demo-video.mjs`
- 데모 영상 계획: `docs/service-demo-interactive-video-implementation-plan.md`

일부 과거 QA 문서와 `scripts/run-opendataloader-real-basis-qa.py` 기본값에는 이전 PC의 `C:\Users\HOONJAE\...` 경로가 남아 있습니다. 새 PC에서는 Git에 포함된 기준문서 경로를 명시합니다.

```powershell
py -3.13 scripts\run-opendataloader-real-basis-qa.py --pdf "source\rag_doc\RAG_기준문서_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf" --engine opendataloader --timeout-seconds 1200 --strict
```

이 명령은 추출·페이지·표·청크 기준을 확인합니다. 기존 PC에서 사용한 별도 비교용 MD까지 대조하려면 `--reference-md <새 PC의 기준 MD 경로>`를 추가합니다. 비교용 TXT/DOCX/MD 원본은 현재 Git에 포함되어 있지 않습니다.

## 12. 작업 재개 순서

1. `git pull --ff-only origin main`으로 최신 코드를 받습니다.
2. `.env`와 필요한 운영 데이터가 준비됐는지 확인합니다.
3. 로컬 서버를 실행합니다.
4. 포탈에서 API 연동, OCR, PDF reader 상태를 확인합니다.
5. [남은 개발 단계 로드맵](remaining-development-roadmap.md)의 우선순위를 확인합니다.
6. 작업 전 관련 계획서와 [작업 로그](work-log.md)를 읽습니다.
7. 작업이 끝나면 한국어/영어 순서로 `docs/work-log.md`에 기록합니다.
8. 요청된 검증만 수행하고 결과를 기록합니다.
9. `main`에 커밋하고 `origin/main`으로 푸시합니다.

## 13. 현재 우선 확인할 남은 작업

1. 추적 중인 credential 의심 파일 제거 및 키 회전
2. 고정 ngrok 외부 접속의 인증·권한·접속 통제
3. 실백엔드 전체 흐름 장시간 QA
4. OpenDataLoader/PyMuPDF 공식 회귀 테스트 정책
5. 실제 백업 복원 절차
6. 대용량 영상·스토리지 산출물의 Git 보관 정책
7. `manage-servers.ps1` 및 QA 스크립트의 절대경로 제거

## Questions for Product Owner

- `open`: `gpt api.txt`의 Git 이력 제거와 관련 키 회전을 즉시 진행할지 결정이 필요합니다.
- `open`: 새 PC에서도 현재와 같은 저장소 경로를 사용할지, 서버 스크립트의 절대경로를 먼저 제거할지 결정이 필요합니다.
- `open`: 기존 운영 DB와 스토리지를 새 PC로 실제 이전할지, 새 빈 DB로 개발만 이어갈지 결정이 필요합니다.

---

# AI / Engineering Version (English)

Last updated: 2026-08-21

## Purpose

This guide explains how to continue development and local operation on another Windows PC. It distinguishes a source-only handoff from a full runtime-state handoff.

## Current Baseline

- branch: `main`
- remote: `https://github.com/himangga01/wisdom_procurement.git`
- backend: Python 3.13.13, Flask, SQLite
- frontend: React, TypeScript, Vite
- PDF: OpenDataLoader-first `auto`, PyMuPDF fallback
- OCR: PaddleOCR PP-OCRv5 with degrade/fallback behavior
- local URLs: backend `http://127.0.0.1:18111`, frontend `http://127.0.0.1:5199`
- fixed public URL: `https://smart.kang.ngrok.pro`

Always read the current commit from Git instead of relying on a hardcoded hash in documentation.

```powershell
git switch main
git pull --ff-only origin main
git log -1 --oneline --decorate
git status --short --branch
```

## Git Versus Local State

Not transferred by Git:

- `backend/.env`, `frontend/.env`
- `backend/app.db`
- all of `backend/storage/`, including uploaded sources, contracts/evidence, indexes, backups and OCR intermediates
- ngrok authentication
- PaddleOCR/PaddleX model caches

Already tracked in Git:

- `source/test_doc/`
- `source/rag_doc/`
- demo video artifacts

Since 2026-10-04, runtime storage is untracked. Before pulling this cleanup on another PC, back up its runtime DB and storage: tracked-file deletions can remove those existing files there. The cleanup checkout preserved local files with `git rm --cached`. Historical blobs remain in Git, so this change does not by itself shrink the old repository pack.

## Security Blocker

The formerly tracked `gpt api.txt` matched a credential pattern. It is now ignored/untracked in the current tree and preserved locally, but remains in historical Git objects; validity was not tested. Do not reveal its value. Credential-owner revocation/replacement and any history rewrite remain separate actions.

The fixed ngrok endpoint exposes the current unauthenticated single-admin portal. Run it only for controlled development or demonstration access.

## New PC Setup

1. Install Git, PowerShell, Python 3.13.13, Node.js 20.19+/22.12+, Java 11+, and optionally ngrok.
2. Clone the repository and switch to `main`.
3. Install `backend/requirements.txt` and optionally `backend/requirements-ocr.txt`.
4. Run `npm install` and `npx playwright install chromium` in `frontend/`.
5. Copy `.env.example` files and enter newly issued API keys.
6. Start local servers with `scripts/manage-servers.ps1`.

## Runtime-State Transfer

For source-only development, do not copy runtime data.

For full continuity, stop both local servers and ngrok on the old PC, then securely transfer:

- `backend/app.db`
- `backend/storage/`
- required `.env` files through an encrypted channel

Do not transfer PID/status files from `temp/`. Automatic restore is not implemented; preserve originals before replacing database or storage files.

## Fixed ngrok Domain

Use an authorized token from the ngrok account that owns `smart.kang.ngrok.pro`. Stop the old endpoint before starting the same domain on the new PC.

```powershell
ngrok config add-authtoken <authorized-token>
powershell -ExecutionPolicy Bypass -File scripts\manage-ngrok.ps1 start
```

## Portability Limitations

- `scripts/manage-servers.ps1` still has one auxiliary process-discovery condition tied to `D:\project\wisdom_procurement`.
- Historical QA documents and the default real-basis QA source path still reference the previous user's absolute path.
- Pass the tracked `source/rag_doc/...pdf` path explicitly on another PC.

## Resume Checklist

1. Pull `origin/main` with fast-forward only.
2. Restore local secrets and optional runtime state.
3. Start local servers.
4. Confirm integration/OCR/PDF-reader status in the portal.
5. Read `docs/remaining-development-roadmap.md` and relevant plans.
6. Record work in `docs/work-log.md` in Korean first and English second.
7. Run only user-approved verification.
8. Commit directly to `main` and push `origin/main`.

## Questions for Product Owner

- Decide whether to rotate the exposed-looking credential and remove `gpt api.txt` from Git history now.
- Decide whether to keep the current repository path on the new PC or first remove hardcoded path assumptions.
- Decide whether the new PC needs the existing runtime database/storage or a clean development database.
