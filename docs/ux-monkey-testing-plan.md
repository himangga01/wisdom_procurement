# UX 몽키테스트 제안

작성일: 2026-05-31

## 한국어 버전

## 결론

이 서비스에는 완전 랜덤 클릭형 몽키테스트보다 `시드 고정 안전 몽키테스트`가 더 적합하다.
로컬 DB와 실제 저장 파일을 다루기 때문에, 기본 테스트가 삭제/승인/복원/백업 생성 같은 파괴적 작업을 누르면 운영 데이터가 손상될 수 있다.

## 추천 테스트 계층

### 1. 정적 UX 계약 테스트

목적:
- 사이드바 메뉴에 있는 경로가 실제 `<Route>`에 등록되어 있는지 확인한다.
- 메뉴 경로가 상단 hero metadata를 가지고 있는지 확인한다.
- 화면은 열리지만 대시보드 제목이 잘못 표시되는 UX 회귀를 방지한다.

현재 반영:
- `backend/tests/test_frontend_contracts.py`

실행:
```powershell
cd backend
py -3.13 -m unittest tests.test_frontend_contracts -v
```

### 2. 라우트 스모크 테스트

목적:
- 주요 화면을 모두 열어 blank page, JS runtime error, console error를 잡는다.
- 프론트 빌드만으로는 잡히지 않는 런타임 렌더링 문제를 찾는다.

추천 도구:
- Playwright

### 3. 안전 몽키테스트

목적:
- 시드가 고정된 랜덤 순서로 화면 이동, 안전 버튼 클릭, 입력 필드 입력을 반복한다.
- 같은 seed로 재현 가능해야 한다.
- 기본값에서는 삭제/복원/승인/반려/저장/생성/실행/재시도 같은 버튼을 누르지 않는다.

현재 반영:
- `scripts/ux-monkey-test.mjs`
- `frontend/package.json`의 `ux:monkey` script

준비:
```powershell
cd frontend
npm install -D playwright
npx playwright install chromium
```

서버 실행:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start
```

실행:
```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531
```

스크린샷까지 저장:
```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531 --screenshot-dir ../temp/ux-monkey
```

### 4. 파괴적 몽키테스트

목적:
- 삭제, 승인, 반려, 재시도, 백업 생성 같은 실제 mutate 동작까지 포함해 더 강하게 흔든다.

주의:
- 운영 데이터가 아닌 임시 DB/임시 storage에서만 실행한다.
- 반드시 seed와 실행 로그를 남긴다.

실행 예:
```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 120 --seed 20260531 --allow-dangerous
```

## 실패로 간주할 조건

- 페이지 body가 비어 있음
- `<main>` landmark가 없음
- 브라우저 `pageerror` 발생
- console error 발생
- 프론트 정적 라우트 계약 테스트 실패
- 스크린샷에서 주요 화면이 빈 상태이거나 레이아웃이 심하게 겹침

## Questions for Product Owner

- 파괴적 몽키테스트를 위한 전용 임시 DB/임시 storage 실행 명령을 표준화할지 결정이 필요하다.
- UX 테스트 통과 기준에 스크린샷 시각 검토를 포함할지 결정이 필요하다.

---

# AI / Engineering Version (English)

## Recommendation

Use seeded safe monkey testing rather than fully random destructive monkey testing.
This app stores local DB rows and files, so default random clicks must avoid destructive actions such as delete, restore, approve, reject, save, create, run, and retry.

## Test Layers

### 1. Static UX Contract Tests

Purpose:
- Ensure every sidebar navigation path is registered as a React route.
- Ensure every primary navigation path has page metadata.
- Prevent UX regressions where a page renders but falls back to dashboard hero copy.

Implemented:
- `backend/tests/test_frontend_contracts.py`

Run:
```powershell
cd backend
py -3.13 -m unittest tests.test_frontend_contracts -v
```

### 2. Route Smoke Tests

Purpose:
- Open every major page and catch blank screens, JS runtime errors, and console errors.

Recommended tool:
- Playwright

### 3. Safe Seeded Monkey Test

Purpose:
- Reproducibly navigate pages, click safe controls, and fill inputs.
- Default mode avoids destructive actions.

Implemented:
- `scripts/ux-monkey-test.mjs`
- `frontend/package.json` script `ux:monkey`

Setup:
```powershell
cd frontend
npm install -D playwright
npx playwright install chromium
```

Run:
```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531
```

### 4. Destructive Monkey Test

Purpose:
- Include mutation-heavy controls such as delete, approve, reject, retry, and backup creation.

Rule:
- Run only against temporary DB/storage.

Run:
```powershell
cd frontend
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 120 --seed 20260531 --allow-dangerous
```

## Failure Criteria

- Blank body
- Missing `<main>` landmark
- Browser `pageerror`
- Console error
- Static route contract failure
- Screenshot-visible blank or severely overlapping layout

## Questions for Product Owner

- Decide whether to standardize a temporary DB/storage launcher for destructive monkey tests.
- Decide whether screenshot review should be part of the formal UX gate.
