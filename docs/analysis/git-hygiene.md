# Git 추적·제외 정책 및 정리 기록

- 분석/작업일: 2026-10-04 (Asia/Seoul)
- 기준: `main`, HEAD `d96fb7f4b387225e3249960ce01138d59413e707`
- 시작 상태: 원격과 로컬 커밋은 일치했으며, 미추적 기준문서 PDF 4개가 있었다. 코드 변경이나 기존 스테이징 변경은 없었다.
- 목적: 소스와 운영 데이터를 분리하고, 제외할 파일을 `.gitignore`에 명시하여 반복적인 미추적/생성 파일 커밋을 방지한다.
- 정본: 이 파일. 이후 Git 추적 정책 분석은 먼저 이 기록과 현재 HEAD/작업 트리를 대조하고 근거를 갱신한다.

## 현재 구조와 확인한 문제

서비스는 프론트엔드와 Flask 백엔드를 분리하며, 로컬 SQLite와 `backend/storage/`에 운영 상태를 보관한다. DB 원본과 운영 파일은 소스 코드와 생명주기가 다르다. 설치 도구와 빌드 캐시는 재생성 가능한 환경 산출물이다.

기존 `.gitignore`는 일부 스토리지 하위 폴더만 제외했다. 이 때문에 새 기준문서 4개는 미추적 파일로 남았고, 이미 인덱스에 있던 운영 파일은 ignore 규칙을 추가하더라도 계속 추적되는 상태였다. 기존 서비스 분석의 R27(생성 파일 추적) 및 R02(credential-shaped 메모)를 이번 HEAD의 Git 인덱스/파일 메타데이터와 대조했다. 파일 본문이나 비밀값은 검사·기록하지 않았다.

| 처음 추적되던 운영 파일 | 수 |
| --- | ---: |
| 기준문서 PDF | 30 |
| 기준문서 인덱스 JSON | 1 |
| 계약서 DOCX | 30 |
| 법인 증빙 자료 | 60 |
| 나라장터 첨부 | 4 |
| OCR 임시 이미지 | 290 |
| 백업 ZIP | 1 |
| DB journal | 2 |
| 운영 스토리지 합계 | 418 |

추가로 TypeScript 빌드 캐시 1개와 과거 credential-shaped 메모 1개가 추적되어 있었다. 해당 메모의 유효성은 확인하지 않았다.

## 적용 정책과 우선순위

1. **운영/비밀 파일의 향후 커밋 차단:** `/backend/storage/`, 로컬 dotenv 변형, 비밀 메모, SQLite sidecar, 가상환경/테스트 캐시/TypeScript 빌드 캐시를 제외한다.
2. **현재 인덱스 정리:** `git rm --cached`로 운영 스토리지 418개, 빌드 캐시 1개, 메모 1개를 추적 해제한다. 총 420개이며 로컬 파일을 삭제하지 않는다.
3. **정상 공유 파일 보존:** 소스, `.env.example`, 고정 테스트 픽스처, 라이선스, 프로젝트 문서, 의도적으로 공유하는 샘플/시연 산출물은 계속 추적한다. 모든 PDF/이미지/ZIP을 전역으로 숨기지 않는다.
4. **다른 PC 인수인계:** 이 커밋을 pull하기 전에 운영 DB/스토리지를 별도 백업한다. 새 clone은 코드/공유 자료만 전달하며 운영 상태를 대신하지 않는다.

## 수행 및 검증

```text
git fetch --prune origin
git pull --ff-only origin main
git rm --cached -r -- backend/storage frontend/tsconfig.tsbuildinfo "gpt api.txt"
git check-ignore --no-index ...
git diff --cached --check
```

- fetch/pull 시 `main`과 `origin/main`이 일치했고 pull은 `Already up to date`였다.
- 인덱스 제거 전 파일 크기와 수정시간을 저장하고 제거 후 대조했다. 420개 모두 존재하며 메타데이터 변화는 0개였다. 이는 실제 관찰이며 임의의 파일 삭제/이동을 실행하지 않았다.
- ignore 양성 24건과 소스/환경 예시/고정 픽스처 보존 10건을 실제 `git check-ignore`로 확인했고 실패는 0건이었다. 현재 인덱스에 ignore 규칙과 충돌하는 추적 파일은 0개다.
- 정리 커밋 `af9618add0531dd05720938afaea406b2cf8dda1`을 `origin/main`에 푸시했다. `git ls-remote`의 main ref가 로컬 HEAD와 일치했고 ahead/behind는 `0/0`, 작업 트리의 porcelain 출력은 비어 있었다. 게시 후에도 420개 파일의 존재/크기/수정시간이 유지됨을 확인했다. 이 문서의 최종 증거 기록은 후속 문서 커밋으로 저장한다.
- 원격 refs는 fetch의 prune 옵션으로 정리했다. 별도 worktree의 prune dry-run에는 제거 대상이 없었으며, 보존 브랜치/작업 트리는 삭제하지 않았다.

## 한계와 미해결 사항

- 추적 해제는 과거 Git 이력의 삭제가 아니다. 과거 운영 파일/메모와 repository pack은 이력에 남는다. force-push나 이력 재작성은 수행하지 않는다.
- 메모의 credential 유효성, 키 회전/폐기, 현재 데이터 내용, 다른 PC의 실제 백업/복원을 검증하지 않았다. 비밀값은 표시하지 않았다.
- 변경 범위는 Git 정책/인덱스/문서다. 애플리케이션 코드·DB·운영 파일을 수정하지 않으며 앱 테스트/빌드를 반복하지 않는다. 기존 서비스 검증을 이번 Git 검증으로 재표시하지 않는다.
- 다른 PC에서 pull할 때 Git의 추적 삭제가 그 PC 파일을 제거할 수 있다. 현재 PC의 보존 결과가 다른 PC의 보존까지 보장하지 않는다.

## Questions for Product Owner

- 과거 민감 메모/운영 데이터의 Git 이력 정리와 키 소유자 조치를 별도 진행할지는 아직 결정하지 않았다.
- 의도적 시연 영상/참고 샘플의 별도 저장소 또는 LFS 전환은 이번 정리 범위에 포함하지 않았다.

---

# AI / Engineering Version (English)

This is the canonical Git tracking/ignore-policy report for the 2026-10-04 cleanup, based on main `d96fb7f`. Read it before subsequent related analyses, compare the current baseline and working tree, and refresh actual evidence while preserving history.

The initial index tracked 418 runtime-storage files, one TypeScript cache and one previously identified credential-shaped note. Four additional basis PDFs were untracked. The cleanup excludes the complete runtime storage tree and appropriate local secret/database/build/cache artifacts, then removes those 420 existing entries with `git rm --cached`. Source, environment examples, stable fixtures, licenses and intentional shared deliverables stay versioned.

Local existence, sizes and modification times were checked before/after index removal and publication: all 420 files remained, with zero metadata changes. Git fetch/prune and fast-forward-only pull confirmed the initial main/origin match. Cleanup commit `af9618add0531dd05720938afaea406b2cf8dda1` was pushed to origin/main; the actual remote ref matched HEAD, ahead/behind was 0/0, porcelain status was empty and tracked-ignored entries were zero. This final evidence is retained in a follow-up documentation commit. No application tests or live restarts were needed for these metadata/documentation changes.

This does not rewrite historical objects, revoke credentials or shrink the old pack. The note's validity was not tested and its contents were not read or exposed. Another PC must back up its runtime DB/storage before pulling the tracked-file deletions; preservation in this checkout does not guarantee preservation elsewhere. Existing backup branches/worktrees remain intact. See [project instructions](../../AGENTS.md), [service analysis](../service-analysis.md) and [other-PC handoff](../other-pc-handoff-guide.md).
