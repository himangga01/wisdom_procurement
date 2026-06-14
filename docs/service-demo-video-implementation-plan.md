# 서비스 시연 영상 생성 구현계획

## 한국어 버전

## 목적
`docs/service-rocket-pitch.md`의 `3. 제품 시연 흐름`을 실제 포탈 화면 녹화 영상으로 만들기 위한 실행 가능한 도구를 구현한다.

이 작업의 목표는 단순한 화면 녹화가 아니라, 영상 생성 전에 제품 시연 파이프라인이 실제로 동작하는지 검증하고, 검증된 데모 데이터를 기반으로 화면을 이동하며 녹화한 뒤, 공유 가능한 MP4 산출물까지 생성하는 것이다.

## 구현 범위

1. 데모 데이터 준비
   - 백엔드 API로 시연 법인, 증빙 샘플, 저장 공고, 기준문서, 부족조건 비교, 판단 run, 계약서 초안을 생성한다.
   - DB를 직접 수정하지 않고 서비스 API만 사용한다.
   - 생성 결과는 `artifacts/demo-video/runs/<seed>/demo-data.json`에 저장한다.

2. 녹화 전 검증
   - 제품 시연 흐름 회귀 테스트를 실행한다.
   - 프론트엔드 빌드를 실행한다.
   - 검증 결과는 `artifacts/demo-video/preflight.json`에 저장한다.

3. 화면 녹화
   - Playwright Chromium으로 로컬 포탈을 열고 장면별 라우트를 이동한다.
   - 각 장면에는 작은 설명 오버레이를 표시한다.
   - 장면별 스크린샷과 녹화 리포트를 저장한다.
   - 원본 영상은 WebM으로 저장한다.

4. MP4 변환
   - `ffmpeg-static`으로 WebM을 MP4로 변환한다.
   - 최종 MP4는 `artifacts/demo-video/service-demo-<seed>.mp4`에 저장한다.

5. 영상 검사
   - `ffprobe-static`으로 비디오 스트림, 해상도, 길이를 검사한다.
   - 검사 결과는 `artifacts/demo-video/latest-inspection.json`에 저장한다.

## 추가 파일

- `scripts/demo-video-utils.mjs`
  - 공통 경로, API 호출, 명령 실행, 간단한 PDF fixture 생성 유틸
- `scripts/prepare-service-demo-data.mjs`
  - 데모 데이터 생성 스크립트
- `scripts/create-service-demo-video.mjs`
  - preflight와 Playwright 녹화 스크립트
- `scripts/render-service-demo-video.mjs`
  - WebM을 MP4로 변환하는 스크립트
- `scripts/inspect-service-demo-video.mjs`
  - MP4 산출물 검사 스크립트
- `scripts/create-demo-video.ps1`
  - 서버 시작, 녹화, 변환, 검사를 묶은 Windows 실행 래퍼
- `scripts/demo-video.config.json`
  - 기본 URL, 출력 경로, 장면 순서 설정

## 실행 방법

1. 최초 1회 브라우저 런타임 설치

```powershell
cd frontend
npm run demo:browser-install
```

2. 서버 실행

```powershell
powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start
```

3. 전체 영상 생성

```powershell
cd frontend
npm run demo:record
npm run demo:render
npm run demo:inspect
```

또는 Windows 래퍼를 사용한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create-demo-video.ps1
```

## 검증 계획

- `cd frontend; npm run demo:browser-install`
- `cd frontend; npm run demo:preflight`
- `powershell -ExecutionPolicy Bypass -File scripts\manage-servers.ps1 -Action start`
- `cd frontend; npm run demo:record -- --dry-run --scene intro,corporations`
- `cd frontend; npm run demo:record -- --skip-preflight`
- `cd frontend; npm run demo:render`
- `cd frontend; npm run demo:inspect`
- `py -3.13 scripts\check-encoding.py`
- `git diff --check`

## 현재 한계

- 1차 구현은 반복 가능한 `stable-demo` 모드 중심이다.
- 실제 `source/test_doc/` PDF 전체 OCR 장면과 실시간 나라장터 API 검색 장면은 별도 모드로 확장할 수 있게 계획만 유지한다.
- 영상 장면은 UI 클릭 중심이 아니라, API로 검증된 상태를 만든 뒤 화면을 이동하며 보여주는 방식이다.

---

# AI / Engineering Version (English)

## Objective
Implement an executable demo video toolchain for the Rocket Pitch product demo flow.

The toolchain must validate the backend/frontend demo pipeline, seed stable demo data through public service APIs, record the UI with Playwright, render an MP4 with FFmpeg, and inspect the final video artifact with FFprobe.

## Implementation Scope

1. Seed demo data via backend APIs only.
2. Run preflight regression and frontend build before recording.
3. Record local UI routes with Playwright Chromium.
4. Convert WebM to MP4 through `ffmpeg-static`.
5. Validate the MP4 with `ffprobe-static`.

## Commands

```powershell
cd frontend
npm run demo:browser-install
npm run demo:preflight
npm run demo:record
npm run demo:render
npm run demo:inspect
```

Windows wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create-demo-video.ps1
```

## Artifacts

- `artifacts/demo-video/latest-demo-data.json`
- `artifacts/demo-video/latest-report.json`
- `artifacts/demo-video/latest-render.json`
- `artifacts/demo-video/latest-inspection.json`
- `artifacts/demo-video/service-demo-<seed>.mp4`

## Notes

- Initial implementation targets deterministic `stable-demo`.
- `real-pdf-demo` and `live-nara-demo` remain planned extensions.
- Recording navigates verified UI state rather than performing every data-creation click through the browser.
