# 현재 서비스 전체 검증 보강 계획

## 현재 코드 기준 업데이트
최종 갱신일: 2026-06-07

이 문서는 전체 테스트, 빌드, UX, API 검증 중 발견한 테스트 인프라 이슈를 정리한 문서입니다.
현재 기준으로 추가 반영해야 할 검증 포인트는 다음과 같습니다.

- 전체 backend 최신 기준선: `134 passed`, `8 skipped`
- PDF/RAG targeted tests: `22 passed`
- 신규 PDF/RAG API regression tests: `4 passed`
- 문서/인코딩 검증: `py -3.13 scripts/check-encoding.py`
- whitespace 검증: `git diff --check`
- 프론트엔드 빌드: `cd frontend; npm run build`
- UX monkey는 `frontend/package.json`의 `ux:monkey` script와 Playwright Chromium으로 실행합니다.
- 현재 PDF reader 운영 기본값은 OpenDataLoader 우선 `auto` 모드이며, 전체 backend tests는 빠른 회귀를 위해 일부 환경에서 PyMuPDF 기본값을 사용할 수 있습니다. OpenDataLoader 운영 경로는 별도 targeted/real-basis QA로 보완합니다.

## 한국어 버전

## 문서 목적
현재 서비스 코드 상태에서 전체 테스트, 빌드, UX 테스트, API 테스트를 실행하던 중 발견된 테스트 인프라 누락을 기록하고, 수정 범위와 완료 기준을 명확히 하기 위한 문서입니다.

## 검증 범위
- 백엔드 전체 테스트: `py -3.13 -m pytest backend/tests -q`
- 프론트엔드 빌드: `npm run build`
- 인코딩 검사: `py -3.13 scripts/check-encoding.py`
- 실제 서버 API smoke: `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`
- UX monkey smoke: `npm run ux:monkey`
- 브라우저 주요 화면 확인

## 발견된 문제

## P2. UX monkey 테스트 런타임 의존성 누락

### 현상
`scripts/ux-monkey-test.mjs`는 Playwright를 사용하도록 설계되어 있습니다.

하지만 현재 `frontend/package.json`에는 `playwright` devDependency가 없어, 새 환경에서 `npm run ux:monkey`를 안정적으로 실행할 수 없습니다.

### 영향
- UX monkey 테스트가 환경 의존적으로 실패할 수 있습니다.
- 새 개발자/운영자 PC에서 `npm install` 후 바로 UX smoke를 실행할 수 없습니다.
- UX 테스트 자동화가 문서화되어 있어도 실제 프로젝트 의존성으로 고정되어 있지 않습니다.

### 수정 계획
1. `frontend`에 `playwright`를 devDependency로 추가한다.
2. Playwright chromium 런타임을 설치한다.
3. 로컬 서버를 띄운 뒤 안전 모드 UX monkey를 실행한다.
4. 주요 운영 화면을 브라우저에서 열어 blank page, 콘솔 오류, 기본 navigation 문제를 확인한다.
5. 검증 결과를 `docs/work-log.md`에 기록한다.

### 완료 기준
- [x] `npm run ux:monkey`가 로컬 서버에 대해 통과한다.
- [x] Playwright 의존성이 `frontend/package.json`과 lockfile에 반영된다.
- [x] 백엔드 전체 테스트와 프론트 빌드가 계속 통과한다.
- [x] work-log에 전체 검증 결과가 기록된다.

## P2. 프론트 dev server 의존성 보안 경고

### 현상
Playwright 의존성을 추가한 뒤 `npm audit`에서 Vite/esbuild 계열 moderate 취약점이 보고되었습니다.

일반 `npm audit fix`로 PostCSS 관련 항목은 정리되었지만, Vite/esbuild 항목은 Vite major upgrade가 필요합니다.

### 영향
- 주로 개발 서버 관련 취약점이지만, 로컬 운영/개발 테스트 환경을 계속 쓰는 서비스 특성상 무시하지 않는 편이 안전합니다.
- Vite major upgrade는 프론트 빌드 호환성 확인이 필요합니다.

### 수정 계획
1. `npm audit fix --force`로 Vite/esbuild 취약점 수정 버전을 반영한다.
2. `npm run build`로 프론트 빌드 호환성을 확인한다.
3. UX monkey와 브라우저 확인으로 dev server 동작을 확인한다.
4. 최종 `npm audit` 결과를 기록한다.

### 완료 기준
- [x] `npm audit`에서 moderate 이상 취약점이 남지 않는다.
- [x] `npm run build`가 통과한다.
- [x] UX 테스트가 통과한다.

## Questions for Product Owner
- 없음. 이 수정은 기능 변경이 아니라 UX 테스트 자동화 실행 가능성을 고정하는 테스트 인프라 보강입니다.

---

# AI / Engineering Version (English)

## Purpose
Document the test-infrastructure gap found during full current-service verification and define the fix plan.

## Current Code Update
Last updated: 2026-06-07

Current verification baseline:
- full backend tests: `134 passed`, `8 skipped`
- targeted PDF/RAG tests: `22 passed`
- new PDF/RAG API regression tests: `4 passed`
- encoding check: `py -3.13 scripts/check-encoding.py`
- whitespace check: `git diff --check`
- frontend build: `cd frontend; npm run build`
- UX monkey: `frontend/package.json` `ux:monkey` script with Playwright Chromium

Operational note:
- Production PDF reader default is OpenDataLoader-first `auto` mode.
- Some fast backend regression tests may set PyMuPDF as the default reader; OpenDataLoader paths remain covered by targeted and real-basis QA.

## Verification Scope
- Backend tests: `py -3.13 -m pytest backend/tests -q`
- Frontend build: `npm run build`
- Encoding check: `py -3.13 scripts/check-encoding.py`
- Live API smoke: `powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1`
- UX monkey smoke: `npm run ux:monkey`
- Browser-based route sanity checks

## Finding

## P2. Missing UX Monkey Runtime Dependency

### Problem
`scripts/ux-monkey-test.mjs` requires Playwright, but `frontend/package.json` does not declare `playwright` as a devDependency.

### Impact
- UX monkey tests can fail on a fresh environment.
- `npm install` does not prepare the frontend workspace for the documented UX smoke test.

### Plan
1. Add `playwright` as a frontend devDependency.
2. Install the chromium runtime.
3. Run safe-mode UX monkey testing against local servers.
4. Open key routes in the browser and check for blank pages, console errors, and navigation failures.
5. Record results in `docs/work-log.md`.

### Completion
- [x] `npm run ux:monkey` passes against local servers.
- [x] Playwright dependency is recorded in `frontend/package.json` and lockfile.
- [x] Backend tests and frontend build still pass.
- [x] Verification results are recorded in `docs/work-log.md`.

## P2. Frontend Dev-Server Dependency Audit Warnings

### Problem
After adding Playwright, `npm audit` reported moderate Vite/esbuild advisories.

Regular `npm audit fix` cleaned up PostCSS, but the remaining Vite/esbuild advisories require a Vite major upgrade.

### Impact
- These advisories primarily affect the development server, but this project relies on local development/operation testing.
- The Vite major upgrade must be verified with frontend build and UX smoke tests.

### Plan
1. Run `npm audit fix --force` to move Vite/esbuild to fixed versions.
2. Verify frontend compatibility with `npm run build`.
3. Verify dev-server behavior with UX monkey and browser checks.
4. Record final `npm audit` status.

### Completion
- [x] `npm audit` reports no moderate-or-higher vulnerabilities.
- [x] `npm run build` passes.
- [x] UX tests pass.

## Questions for Product Owner
None. This is a test-infrastructure hardening change, not product behavior.
