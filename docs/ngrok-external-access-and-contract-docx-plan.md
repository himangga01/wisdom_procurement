# 한국어 버전

# ngrok 외부 접속 및 계약서 DOCX 자동 생성 설계/구현계획

작성일: 2026-06-07

## 목적

현재 서비스는 로컬 단일 PC에서만 실행되는 것을 기본 전제로 합니다. 이번 계획은 다음 두 기능을 안전하게 추가하기 위한 FE/BE 설계와 구현 순서를 정의합니다.

1. ngrok을 이용해 외부에서도 현재 로컬 서비스를 접속할 수 있게 한다.
2. 법인 기본정보와 선택한 저장 공고문 내용을 기반으로 기본 계약서 DOCX를 자동 생성한다.

이번 문서는 구현 전 계획서입니다. 실제 코드 수정은 이 계획 확인 후 진행합니다.

## 단계 제안

### Phase 4E. ngrok 외부 접속 지원

운영 제품화의 확장 단계로 둡니다. 서비스 자체를 클라우드 서버로 바꾸는 것이 아니라, 로컬 PC에서 실행 중인 백엔드/프론트엔드에 ngrok 터널을 붙이는 방식입니다.

### Phase 5A. 계약서 DOCX 자동 생성 MVP

나라장터 저장 공고, 법인 정보, 판단/비교 결과를 활용하는 문서 생성 기능입니다. 법률적으로 확정된 계약서가 아니라, 관리자가 검토/수정할 수 있는 기본 계약서 초안 DOCX를 생성하는 MVP로 시작합니다.

## 기능 1. ngrok 외부 접속 지원

### 현재 구조

- 백엔드: Flask, `APP_PORT` 기준으로 실행
- 프론트엔드: Vite dev server, `VITE_API_BASE_URL`로 백엔드 API 주소를 주입
- 서버 실행 스크립트: `scripts/manage-servers.ps1`
- 현재 백엔드는 `127.0.0.1`에 바인딩되어 있으며, ngrok agent가 로컬 포트에 붙는 방식이면 외부 공개를 위해 백엔드를 `0.0.0.0`으로 열 필요는 없습니다.
- 현재 CORS는 전체 origin 허용 상태입니다.

### 핵심 문제

외부 사용자의 브라우저는 `http://127.0.0.1:18111` 같은 로컬 주소를 호출할 수 없습니다. 따라서 프론트엔드가 외부에서 열릴 때는 백엔드 API 주소도 ngrok 공개 URL이어야 합니다.

### 권장 실행 흐름

1. 백엔드 로컬 서버를 실행한다.
2. 백엔드 포트에 ngrok 터널을 연다.
3. ngrok 로컬 API에서 백엔드 public URL을 읽는다.
4. 프론트엔드를 `VITE_API_BASE_URL=<백엔드 ngrok URL>`로 실행한다.
5. 프론트엔드 포트에 ngrok 터널을 연다.
6. `temp/ngrok.status.json`에 프론트/백엔드 public URL, local URL, process id, 갱신 시각을 저장한다.

### 백엔드 설계

#### 환경변수

- `APP_PORT`: 기존 백엔드 포트
- `APP_HOST`: 기본값 `127.0.0.1`, ngrok 방식에서는 유지 가능
- `EXTERNAL_ACCESS_ENABLED`: 외부 접속 모드 여부 표시
- `EXTERNAL_ACCESS_PROVIDER`: `ngrok`
- `APP_PUBLIC_BACKEND_URL`: 현재 백엔드 ngrok URL
- `APP_PUBLIC_FRONTEND_URL`: 현재 프론트엔드 ngrok URL
- `APP_CORS_ORIGINS`: MVP에서는 전체 origin 허용을 유지하되, 후속으로 제한할 수 있도록 옵션만 둔다.

#### API

```text
GET /api/external-access/status
```

응답 예:

```json
{
  "enabled": true,
  "provider": "ngrok",
  "frontend_public_url": "https://example.ngrok-free.app",
  "backend_public_url": "https://api-example.ngrok-free.app",
  "frontend_local_url": "http://127.0.0.1:5199",
  "backend_local_url": "http://127.0.0.1:18111",
  "updated_at": "2026-06-07T12:00:00+09:00",
  "warnings": [
    "외부 접속 URL은 이 로컬 PC 서비스에 직접 연결됩니다.",
    "ngrok auth token과 API 키 원문은 응답에 포함하지 않습니다."
  ]
}
```

#### 스크립트

새 스크립트:

```text
scripts/manage-ngrok.ps1
```

명령:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/manage-ngrok.ps1 start
powershell -ExecutionPolicy Bypass -File scripts/manage-ngrok.ps1 status
powershell -ExecutionPolicy Bypass -File scripts/manage-ngrok.ps1 stop
```

주요 역할:

- ngrok CLI 설치 여부 확인
- `NGROK_AUTHTOKEN` 또는 사전 설정된 ngrok config 확인
- 백엔드/프론트엔드 서버 기동
- 백엔드 터널 생성 후 URL 획득
- 백엔드 public URL을 주입해 프론트엔드 실행
- 프론트엔드 터널 생성
- 상태 JSON 저장
- 종료 시 ngrok/server process 정리

#### Vite 설정

ngrok host header 때문에 Vite가 차단될 수 있으므로 `frontend/vite.config.ts`에 외부 접속 모드용 설정을 추가합니다.

```ts
server: {
  allowedHosts: process.env.VITE_ALLOW_NGROK_HOSTS === "1" ? true : undefined,
}
```

### 프론트엔드 설계

#### 화면 위치

기본 위치:

- `/settings/integrations/nara`를 단일 설정 페이지에서 확장하거나
- 새 경로 `/settings/external-access` 추가

권장:

- 새 페이지 `/settings/external-access`
- 사이드바 설정 그룹에 `외부 접속` 추가
- 운영 대시보드에는 public URL 상태만 작게 표시

#### 화면 요소

- 현재 외부 접속 상태
- 프론트엔드 public URL
- 백엔드 public URL
- 로컬 URL
- 갱신 시각
- 보안 경고
- URL 복사 버튼
- ngrok 실행/중지는 프론트에서 직접 하지 않고, 로컬 스크립트 실행 안내 또는 상태 표시만 제공

프론트에서 OS process를 직접 제어하지 않는 이유:

- 브라우저는 로컬 PowerShell process를 안전하게 실행할 수 없습니다.
- 서버 process 제어는 `scripts/manage-ngrok.ps1`가 담당하는 편이 명확합니다.

### 테스트 계획

#### 백엔드

- `GET /api/external-access/status`
  - status 파일 없음: `enabled=false`
  - status 파일 있음: URL과 provider 반환
  - token/API key 원문 미노출

#### 스크립트

- ngrok CLI 없음: 명확한 오류 메시지
- ngrok API에서 tunnel URL 파싱
- `start/status/stop` 상태 파일 생성/삭제

#### 프론트엔드

- status API 결과 렌더링
- URL 없음/오류 상태에서도 화면 깨지지 않음
- `npm run build`
- UX monkey에서 `/settings/external-access` route 포함

#### 수동 QA

1. `manage-ngrok.ps1 start`
2. 프론트 public URL 접속
3. 대시보드, 나라장터 저장 공고, 법인 목록 조회
4. 백엔드 public URL이 브라우저에서 직접 health/API 호출 가능
5. `manage-ngrok.ps1 stop` 후 접속 차단 확인

## 기능 2. 계약서 DOCX 자동 생성

### 기능 정의

관리자가 법인과 저장 공고문을 선택하면, 서비스가 다음 데이터를 조합해 기본 계약서 DOCX를 생성합니다.

- 법인 기본정보
- 선택한 나라장터 저장 공고문 정보
- 공고 요구조건 요약
- 선택한 판단 run 또는 비교 결과
- 준비/제출 서류 목록
- 계약 금액, 계약 기간, 계약 상대방 등 아직 확정되지 않은 항목은 placeholder로 둔다.

### 표준계약서 양식 적용 방침

사용자가 제공한 기준 양식:

```text
C:/Users/HOONJAE/Documents/카카오톡 받은 파일/[별지 제9호서식] 용역 표준계약서(지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙).pdf
```

확인한 양식 특징:

- 1페이지 A4 세로 문서
- 상단 좌측: `[별지 제9호서식] <개정 2024. 12. 6.>`
- 상단 우측: `(앞쪽)`
- 중앙 제목: `용역표준계약서`
- 제목 우측: `계약번호 제   호`, `공고번호 제   호`
- 본문 1차 표: 세로 병합 라벨 `계약서`, 발주처, 계약상대자, 상호 또는 법인명, 주소, 대표자, 법인등록번호, 전화번호
- 본문 2차 표: 세로 병합 라벨 `계약내용`, 용역명, 계약금액, 총용역부기금액, 계약보증금, 지연배상금률, 계약기간, 위치, 그 밖의 사항
- 하단: 계약 체결 확약 문구, 붙임서류 목록, 자치단체의 장 또는 계약담당자 서명/날인, 계약상대자 서명/날인, `210㎜×297㎜`

DOCX 생성 시 위 PDF를 단순 텍스트 참고로만 쓰지 않고, 표 구조와 배치를 최대한 동일하게 재현합니다.

구현 원칙:

- 생성 문서 제목은 양식과 동일하게 `용역표준계약서`를 사용한다.
- 화면과 DB 상태명은 법적 오해를 줄이기 위해 계속 `계약서 초안`으로 표시한다.
- DOCX 본문 첫 페이지는 표준계약서 양식에 맞춘다.
- 자동 입력값이 없는 항목은 빈칸 또는 placeholder로 둔다.
- 공고 데이터와 법인 데이터는 양식 필드에 대응해서 채운다.
- 부족조건/판단 결과는 첫 페이지 양식을 깨지 않도록 `그 밖의 사항` 또는 별도 후속 페이지/첨부 스타일 섹션으로 넣는다.
- 원본 PDF 파일은 사용자 로컬 파일이므로 저장소에 바로 커밋하지 않는다.
- 구현 시에는 PDF를 보고 만든 DOCX layout template 또는 code template을 저장소에 두고, PDF 원본은 테스트용 local reference로만 사용한다.

필드 매핑 초안:

| 표준계약서 항목 | 서비스 데이터 | 처리 |
| --- | --- | --- |
| 계약번호 | 생성 시 입력 또는 자동 placeholder | 미입력 시 `제        호` |
| 공고번호 | `nara_notices.bid_ntce_no` + `bid_ntce_ord` | 자동 입력 |
| 발주처 | `ntce_instt_nm` 또는 `dminstt_nm` | PO 결정 전에는 공고기관 우선 |
| 상호 또는 법인명 | `corporations.name` | 자동 입력 |
| 주소 | 법인 profile/수동 입력 필드 | 없으면 빈칸 |
| 대표자 | 법인 profile/수동 입력 필드 | 없으면 빈칸 |
| 법인등록번호 | 법인 profile/수동 입력 필드 | 없으면 빈칸 |
| 전화번호 | 법인 profile/수동 입력 필드 | 없으면 빈칸 |
| 용역명 | `nara_notices.bid_ntce_nm` | 자동 입력 |
| 계약금액 | custom field 또는 `bssamt` 참고값 | PO 결정 필요 |
| 총용역부기금액 | custom field | 기본 빈칸 |
| 계약보증금 | custom field | 기본 빈칸 |
| 지연배상금률 | custom field | 기본 빈칸 |
| 계약기간 | custom field 또는 공고 일정 참고 | 기본 빈칸 |
| 위치 | custom field 또는 `region_text` | 기본 빈칸 |
| 그 밖의 사항 | 공고 요구조건/검토 필요사항 요약 | 별도 섹션과 충돌하지 않게 요약 |

### 중요한 정책

- 생성물은 `계약서 초안`입니다.
- 자동 생성 DOCX는 법률 검토를 대체하지 않습니다.
- 기준문서 citation이나 판단 엔진 결과를 확정 계약 조건처럼 단정하지 않습니다.
- 민감한 법인 정보는 로그에 원문으로 남기지 않습니다.
- 파일은 `storage/contracts/` 아래에 저장하고 백업 대상에 포함할지 별도 정책을 둡니다.

### 백엔드 데이터 모델

새 테이블:

```sql
CREATE TABLE IF NOT EXISTS contract_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nara_notice_id INTEGER NOT NULL,
  corporation_id INTEGER NOT NULL,
  judgment_run_id INTEGER,
  status TEXT DEFAULT 'generated',
  review_status TEXT DEFAULT 'draft',
  contract_type TEXT DEFAULT 'basic_procurement_contract',
  template_version TEXT DEFAULT 'contract_docx_template_v1',
  title TEXT DEFAULT '',
  file_name TEXT DEFAULT '',
  stored_file_path TEXT DEFAULT '',
  file_size_bytes INTEGER DEFAULT 0,
  input_snapshot_json TEXT DEFAULT '{}',
  generated_fields_json TEXT DEFAULT '{}',
  validation_json TEXT DEFAULT '{}',
  error_message TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(nara_notice_id) REFERENCES nara_notices(id),
  FOREIGN KEY(corporation_id) REFERENCES corporations(id),
  FOREIGN KEY(judgment_run_id) REFERENCES judgment_runs(id)
);
```

권장 인덱스:

```sql
CREATE INDEX IF NOT EXISTS idx_contract_documents_notice_corporation
ON contract_documents(nara_notice_id, corporation_id);

CREATE INDEX IF NOT EXISTS idx_contract_documents_created_at
ON contract_documents(created_at);
```

### 저장 경로

```text
storage/contracts/{contract_document_id}/contract-{id}.docx
```

### 백엔드 서비스 구조

신규 파일:

```text
backend/app/services/contract_documents.py
```

주요 함수:

- `build_contract_input_snapshot(conn, notice_id, corporation_id, judgment_run_id=None)`
- `validate_contract_generation_input(snapshot)`
- `render_basic_contract_docx(snapshot, output_path)`
- `create_contract_document(conn, payload, storage_root)`
- `contract_document_payload(conn, row)`
- `delete_contract_document(conn, contract_document_id)`

현재 백엔드가 `main.py`에 많은 route를 직접 갖고 있으므로, 1차 구현은 service 파일에 로직을 두고 `main.py`에는 route glue만 추가합니다.

### DOCX 템플릿 구성

`python-docx`로 다음 섹션을 생성합니다.

1. 제목: 계약서 초안
2. 문서 상태: 자동 생성 초안 / 관리자 검토 필요
3. 계약 당사자
   - 발주/수요기관: 공고 데이터 기준
   - 계약상대자: 법인 정보 기준
4. 공고 정보
   - 공고명
   - 공고번호/차수
   - 공고기관
   - 수요기관
   - 입찰 마감/개찰일
   - 추정가격/기초금액
5. 계약 기본 조항
   - 계약 목적
   - 계약 범위
   - 계약 금액 placeholder
   - 계약 기간 placeholder
   - 납품/수행 장소 placeholder
6. 제출/준비 서류
   - judgment run의 `preparation_guide.required_documents`
   - 공고 요구조건 추출 결과
7. 검토 필요 조건
   - missing/uncertain/needs_review 판단 항목
8. 특기사항
   - 자동 생성 출처
   - 관리자 검토 필요
   - 법률 검토 필요

### API 설계

```text
GET /api/contracts
POST /api/contracts/preview
POST /api/contracts
GET /api/contracts/{contract_id}
GET /api/contracts/{contract_id}/download
DELETE /api/contracts/{contract_id}
PATCH /api/contracts/{contract_id}/review
```

#### POST /api/contracts/preview

DOCX 파일을 만들기 전에 입력 스냅샷과 자동 채움 필드를 미리 보여줍니다.

요청:

```json
{
  "nara_notice_id": 1,
  "corporation_id": 2,
  "judgment_run_id": 3
}
```

응답:

```json
{
  "valid": true,
  "warnings": ["계약 금액은 공고 기초금액을 참고값으로만 넣었습니다."],
  "snapshot": {
    "notice": {},
    "corporation": {},
    "judgment_run": {},
    "contract_fields": {}
  }
}
```

#### POST /api/contracts

DOCX를 생성하고 이력을 저장합니다.

요청:

```json
{
  "nara_notice_id": 1,
  "corporation_id": 2,
  "judgment_run_id": 3,
  "title": "테스트 공고 계약서 초안",
  "custom_fields": {
    "contract_amount": "",
    "contract_period": "",
    "delivery_location": ""
  }
}
```

응답:

```json
{
  "id": 10,
  "status": "generated",
  "review_status": "draft",
  "file_name": "contract-10.docx",
  "download_url": "/api/contracts/10/download",
  "validation": {
    "valid": true,
    "warnings": []
  }
}
```

### 프론트엔드 설계

#### 라우트

```text
/contracts
/contracts/:id
```

#### 사이드바

`공고 업무` 또는 새 그룹 `문서 생성`에 추가:

```text
계약서 생성
```

#### `/contracts` 화면

주요 영역:

- 법인 선택
- 저장 공고 선택
- 판단 run 선택
- 기본 필드 편집
  - 계약 금액
  - 계약 기간
  - 납품/수행 장소
  - 특기사항
- 미리보기
  - 공고 정보
  - 법인 정보
  - 제출/준비 서류
  - 검토 필요 조건
- 생성 버튼
- 생성 이력 리스트
- 다운로드 버튼

#### 연결 진입점

다음 화면에서 `계약서 초안 생성` 버튼을 추가합니다.

- 저장 공고 상세: `/nara-saved-notices/:id`
- 판단 run 목록/상세: `/judgment-runs`
- 부족조건 미리보기: `/notice-comparison`

### 테스트 계획

#### 백엔드 단위/API 테스트

- 계약서 preview
  - 정상 notice/corporation 조합
  - 없는 notice/corporation이면 404 또는 400
  - judgment_run_id가 notice/corporation과 맞지 않으면 400
- DOCX 생성
  - `POST /api/contracts`가 `201` 반환
  - `storage/contracts/{id}`에 docx 저장
  - `python-docx`로 다시 열었을 때 공고명, 법인명, 공고번호가 포함됨
  - `python-docx`로 다시 열었을 때 `용역표준계약서`, `계약서`, `계약내용`, `발주처`, `계약상대자`, `붙임서류`, `자치단체의 장 또는 계약담당자`, `계약상대자` 라벨이 포함됨
  - 첫 페이지 기준 표가 2개 이상의 table로 생성되고, 계약상대자/계약내용 항목이 병합/표 구조로 표현됨
  - A4 세로 문서 설정과 기본 margin이 적용됨
  - placeholder가 비어 있어도 문서 생성 실패하지 않음
- 다운로드
  - content-type이 DOCX MIME
  - 파일명 header가 한글 깨짐 없이 안전하게 인코딩됨
- 삭제
  - DB row 삭제
  - 저장 파일 삭제
- 보안
  - 파일 경로 traversal 불가
  - 민감 env/API key가 snapshot에 포함되지 않음

#### 프론트엔드 테스트

- `api.ts` 타입/API 함수 추가
- `types.ts` 계약서 타입 추가
- `/contracts` 빌드 통과
- 선택값 없음 상태에서 생성 버튼 비활성화
- preview 실패/생성 실패 메시지 표시
- 다운로드 링크 정상 생성

#### UX 테스트

- seeded UX monkey route 목록에 `/contracts` 추가
- 위험 버튼은 기본 monkey에서 누르지 않도록 안전 키워드에 `download`, `generate`, `계약서 생성` 처리 검토
- 화면 폭이 좁아도 선택 폼과 preview가 겹치지 않는지 확인

## 상세 구현 Step

### Step 0. 구현 전 고정 결정

목표: 구현 중 UX/데이터 모델이 흔들리지 않도록 정책을 먼저 고정합니다.

작업:

1. 화면/DB 상태명은 `계약서 초안`으로 유지하고, 생성 DOCX 제목만 `용역표준계약서`로 둔다.
2. 공고의 계약 상대방 표기 우선순위는 1차 구현에서 `공고기관(ntce_instt_nm)` 우선으로 둔다.
3. 계약 금액은 1차 구현에서 사용자 입력값을 우선하고, 미입력 시 공고의 `bssamt` 또는 `presmpt_prce`를 참고값으로만 표시한다.
4. 표준계약서 원본 PDF는 저장소에 커밋하지 않고, 코드 기반 DOCX layout builder로 재현한다.
5. ngrok은 1차 구현에서 개발/시연용 외부 접속 기능으로 둔다.
6. 생성된 계약서 DOCX와 DB row는 생성 시점의 immutable snapshot을 기준으로 유지한다. 이후 공고/법인/판단 run이 변경되어도 기존 계약서 초안은 자동 변경하지 않는다.
7. 1차 계약서 양식은 `용역표준계약서` 전용으로 둔다. 공고가 용역 성격인지 확실하지 않으면 생성은 가능하되 preview와 DOCX 검토 메모에 경고를 남긴다.

완료 기준:

- 위 정책이 이 문서와 work-log에 기록되어 있다.
- 구현 중 새 정책 결정이 필요하면 `Questions for Product Owner`에 추가한다.

### Step 1. 계약서 BE 데이터 모델

목표: 계약서 생성 이력과 산출물 경로를 저장할 수 있게 합니다.

작업:

1. `init_db()`에 `contract_documents` 테이블 생성 SQL을 추가한다.
2. `idx_contract_documents_notice_corporation`, `idx_contract_documents_created_at` 인덱스를 추가한다.
3. `storage/contracts/`를 계약서 산출물 저장 위치로 표준화한다.
4. 백업 서비스의 포함 디렉터리에 `contracts`를 추가할지 결정하고, 포함한다면 `.env` 제외 정책과 함께 반영한다.
5. 삭제 시 DB row와 저장 파일을 함께 정리하는 helper를 설계한다.
6. `status` 허용값은 `generated`, `failed`, `deleted`로 시작하고, `review_status` 허용값은 `draft`, `needs_review`, `approved`, `rejected`, `archived`로 시작한다.
7. 저장 파일명은 한글/공백이 있어도 다운로드가 깨지지 않도록 DB용 원본명과 파일시스템용 안전명을 분리한다.

테스트:

1. `init_db()` 후 `contract_documents` 테이블과 인덱스가 존재한다.
2. 계약서 저장 경로가 `storage/contracts/{id}/` 밖으로 나가지 않는다.
3. 백업에 포함하는 경우 계약서 DOCX는 포함되고 `.env`류 파일은 제외된다.
4. 허용되지 않은 `status`/`review_status` 값은 저장되지 않는다.

### Step 2. 계약서 BE 입력 스냅샷/검증

목표: DOCX 생성에 필요한 공고/법인/판단 데이터를 안정적으로 모읍니다.

작업:

1. `backend/app/services/contract_documents.py`를 추가한다.
2. `build_contract_input_snapshot(conn, notice_id, corporation_id, judgment_run_id=None)`를 구현한다.
3. 저장 공고가 없으면 `404`, 법인이 없으면 `404`가 되도록 route 레벨 응답 정책을 정한다.
4. `judgment_run_id`가 들어온 경우 notice/corporation 조합이 일치하는지 검증한다.
5. `custom_fields`를 정규화한다.
6. snapshot에서 API key, ngrok token, 원문 env 값 같은 민감 정보가 들어가지 않도록 allowlist 기반으로 구성한다.
7. 법인 프로필에 없는 계약서용 보완값은 `generated_fields_json` 또는 `custom_fields`에만 저장하고, 사용자가 별도 승인하지 않는 한 corporation profile을 자동 수정하지 않는다.
8. snapshot에는 계약서 양식 버전, 입력 데이터 id, 입력 데이터 표시값, 생성 시각을 함께 저장한다.

테스트:

1. 정상 notice/corporation 조합 preview가 성공한다.
2. 없는 notice/corporation은 실패한다.
3. judgment run이 다른 notice/corporation에 속하면 실패한다.
4. snapshot JSON에 `API_KEY`, `TOKEN`, `SERVICE_KEY`, `.env` 원문이 포함되지 않는다.
5. 생성 후 원본 공고/법인 정보를 수정해도 기존 계약서 snapshot과 DOCX 다운로드 결과가 바뀌지 않는다.

### Step 3. 계약서 BE 표준양식 DOCX Layout Builder

목표: 제공된 `[별지 제9호서식] 용역표준계약서` PDF의 첫 페이지 양식을 DOCX로 재현합니다.

작업:

1. `render_standard_service_contract_docx(snapshot, output_path)`를 구현한다.
2. A4 세로, 기본 margin, 한글 기본 폰트 설정을 적용한다.
3. 상단 `[별지 제9호서식] <개정 2024. 12. 6.>`와 `(앞쪽)`을 배치한다.
4. 중앙 제목 `용역표준계약서`를 배치한다.
5. 우측 계약번호/공고번호 영역을 만든다.
6. `계약서` 표를 만든다.
   - 발주처
   - 계약상대자
   - 상호 또는 법인명
   - 주소
   - 대표자
   - 법인등록번호
   - 전화번호
7. `계약내용` 표를 만든다.
   - 용역명
   - 계약금액
   - 총용역부기금액
   - 계약보증금
   - 지연배상금률
   - 계약기간
   - 위치
   - 그 밖의 사항
8. 확약 문구, 붙임서류, 서명/날인란, `210㎜×297㎜` footer를 만든다.
9. 부족조건/검토 필요사항은 `그 밖의 사항`에 짧게 요약하고, 길어지면 후속 페이지에 `자동 생성 검토 메모`로 배치한다.
10. DOCX 생성은 임시 파일에 먼저 렌더링한 뒤 성공 시 최종 경로로 교체하고, 실패 시 임시 파일과 반쪽짜리 산출물을 정리한다.
11. `python-docx`만으로 1페이지 양식 전체를 완벽히 동일하게 복제하기 어려운 경우, 첫 구현은 표 구조/필드/라벨/페이지 설정 일치를 테스트 기준으로 삼고 시각적 오차는 QA 메모에 남긴다.

테스트:

1. 생성 DOCX를 `python-docx`로 열 수 있다.
2. 문서 텍스트에 `용역표준계약서`, `계약서`, `계약내용`, `발주처`, `계약상대자`, `붙임서류`가 포함된다.
3. 문서에 최소 2개 이상의 table이 존재한다.
4. A4 세로 page size가 적용된다.
5. 공고명, 공고번호, 법인명이 자동 입력된다.
6. 빈 custom field가 있어도 생성 실패하지 않는다.
7. 렌더링 실패를 강제로 발생시켰을 때 최종 DOCX가 남지 않고 operation run이 실패로 기록된다.

### Step 4. 계약서 BE API

목표: 프론트에서 preview, 생성, 다운로드, 이력 관리를 할 수 있게 합니다.

작업:

1. `GET /api/contracts`를 추가한다.
2. `POST /api/contracts/preview`를 추가한다.
3. `POST /api/contracts`를 추가한다.
4. `GET /api/contracts/{contract_id}`를 추가한다.
5. `GET /api/contracts/{contract_id}/download`를 추가한다.
6. `PATCH /api/contracts/{contract_id}/review`를 추가한다.
7. `DELETE /api/contracts/{contract_id}`를 추가한다.
8. 생성/삭제/검토 변경에 `operation_runs` 기록을 추가한다.
9. 다운로드 응답에 DOCX MIME과 UTF-8 안전 파일명을 적용한다.
10. `GET /api/contracts`는 `notice_id`, `corporation_id`, `review_status`, `status`, `keyword` 필터를 지원한다.
11. 생성 실패도 `contract_documents.status=failed`와 `operation_runs.status=failed`로 남겨 관리자가 실패 사유를 볼 수 있게 한다.
12. 저장 파일이 없는 다운로드 요청은 404를 반환하고, 파일 경로는 `storage/contracts` 하위인지 다시 검증한다.

테스트:

1. preview API 정상/실패 케이스.
2. create API가 `201`과 payload를 반환한다.
3. list/detail API가 생성 이력을 반환한다.
4. download API가 DOCX MIME과 파일 내용을 반환한다.
5. delete API가 DB row와 저장 파일을 삭제한다.
6. review API가 `review_status`와 note를 갱신한다.
7. operation run에 계약서 생성 이력이 남는다.
8. 생성 실패 시 실패 row, 실패 operation run, 실패 사유가 남는다.
9. list API 필터가 notice/corporation/status/review_status 기준으로 동작한다.
10. 다운로드 파일명이 한글 제목이어도 `Content-Disposition`이 UTF-8로 안전하게 내려간다.

### Step 5. 계약서 FE 타입/API

목표: 프론트가 계약서 API를 타입 안전하게 사용할 수 있게 합니다.

작업:

1. `frontend/src/app/types.ts`에 `ContractDocument`, `ContractPreview`, `ContractCustomFields` 타입을 추가한다.
2. `frontend/src/app/api.ts`에 계약서 API helper를 추가한다.
3. 다운로드 URL helper 또는 `buildApiUrl()` export 정책을 정리한다.
4. API 실패 메시지를 기존 `request()` 흐름에 맞춘다.
5. preview/create 실패 payload가 와도 화면 state가 깨지지 않도록 validation/warnings/errors 기본 shape를 정규화한다.

테스트:

1. `npm run build`가 타입 오류 없이 통과한다.
2. 빈 payload/오류 payload 타입이 화면에서 안전하게 처리된다.
3. 생성 실패 응답 후에도 리스트 새로고침과 오류 표시가 정상 동작한다.

### Step 6. 계약서 FE 화면

목표: 관리자가 법인과 공고를 선택하고 DOCX 초안을 생성/다운로드할 수 있게 합니다.

작업:

1. `frontend/src/pages/ContractsPage.tsx`를 추가한다.
2. 법인 select, 저장 공고 select, judgment run select를 만든다.
3. 계약번호, 계약금액, 계약기간, 위치, 그 밖의 사항 등 custom field 입력 폼을 만든다.
4. `미리보기` 버튼으로 preview API를 호출한다.
5. preview panel에 표준계약서 매핑 결과와 경고를 표시한다.
6. `계약서 초안 생성` 버튼으로 create API를 호출한다.
7. 생성 이력 리스트를 표시한다.
8. 생성된 DOCX 다운로드 버튼을 제공한다.
9. 입력값이 부족하면 생성 버튼을 비활성화한다.
10. 생성 이력은 status/review_status 필터와 키워드 검색을 제공한다.
11. 같은 공고/법인 조합으로 여러 초안을 만들 수 있으며, 기존 초안을 덮어쓰지 않는다.

UX 기준:

1. SaaS/운영 도구 톤의 조용한 폼/표 중심 UI로 만든다.
2. 표준양식 설명문을 화면에 길게 늘어놓지 않는다.
3. 모바일/좁은 화면에서 select와 preview가 겹치지 않는다.
4. 위험한 삭제 버튼은 기존 monkey safe 정책에 걸리도록 명확한 텍스트를 둔다.

검증:

1. `npm run build`
2. `/contracts` route smoke
3. UX monkey route 목록에 `/contracts` 추가
4. 같은 조합으로 두 번 생성했을 때 이력 2건이 보이고 각각 다운로드가 가능하다.

### Step 7. 계약서 FE 진입점 연결

목표: 기존 업무 흐름에서 계약서 생성으로 자연스럽게 이동하게 합니다.

작업:

1. 사이드바에 `계약서 생성` nav item을 추가한다.
2. `/nara-saved-notices/:id`에 `계약서 초안 생성` 링크를 추가한다.
3. `/judgment-runs`에서 선택 run 기반 계약서 생성 링크를 추가한다.
4. `/notice-comparison`에서 선택 notice/corporation 조합 기반 링크를 추가한다.
5. 링크 query param 예: `/contracts?notice_id=1&corporation_id=2&judgment_run_id=3`

테스트:

1. 각 진입점이 `/contracts`로 올바른 query param을 전달한다.
2. query param이 있으면 select 초기값이 자동 선택된다.
3. 대상 데이터가 삭제된 경우 화면이 깨지지 않고 안내를 표시한다.

### Step 8. ngrok 스크립트

목표: 로컬 서버와 ngrok tunnel을 한 번에 관리할 수 있게 합니다.

작업:

1. `scripts/manage-ngrok.ps1`를 추가한다.
2. `start/status/stop` action을 구현한다.
3. ngrok CLI 존재 여부를 검사한다.
4. ngrok auth 설정 여부를 검사한다.
5. 백엔드 서버를 시작한다.
6. 백엔드 tunnel을 열고 ngrok local API에서 public URL을 읽는다.
7. `VITE_API_BASE_URL=<backend public URL>`로 프론트엔드를 시작한다.
8. 프론트엔드 tunnel을 열고 public URL을 읽는다.
9. `temp/ngrok.status.json`을 저장한다.
10. `stop`에서 ngrok/frontend/backend process를 정리한다.
11. 포트가 이미 사용 중이면 기존 `manage-servers.ps1` 상태 파일을 확인하고, 관리 대상 프로세스만 정리하거나 명확한 오류를 반환한다.
12. ngrok 무료 URL은 재시작 때 바뀔 수 있으므로, start 때마다 프론트엔드를 새 backend public URL로 다시 시작한다.
13. status 파일에는 public/local URL, pid, port, updated_at만 저장하고 token, API key, 전체 env 값은 저장하지 않는다.

테스트:

1. ngrok CLI 없음 오류 메시지.
2. status 파일 schema 검증.
3. start 후 backend/frontend public URL 존재.
4. stop 후 status 파일 또는 running 상태 정리.
5. 포트 충돌 상황에서 임의 프로세스를 종료하지 않는다.
6. 재시작 후 `VITE_API_BASE_URL`이 새 backend public URL을 사용한다.

### Step 9. ngrok BE/FE 상태 화면

목표: 외부 접속 URL과 주의사항을 관리자 화면에서 확인할 수 있게 합니다.

작업:

1. `GET /api/external-access/status`를 추가한다.
2. status 파일 없음이면 `enabled=false`를 반환한다.
3. status 파일 있음이면 public/local URL과 updated_at을 반환한다.
4. 응답에서 ngrok token, API key, env 원문을 제외한다.
5. `frontend/vite.config.ts`에 ngrok allowed host 옵션을 추가한다.
6. `frontend/src/pages/ExternalAccessPage.tsx`를 추가한다.
7. `/settings/external-access` route/nav를 추가한다.
8. URL 복사 버튼과 보안 경고를 표시한다.
9. 현재 MVP는 전체 origin 허용을 유지하지만, status 화면에는 외부 접속 URL이 열려 있는 동안 민감 자료 업로드/공유에 주의해야 한다는 경고를 표시한다.
10. 프론트 화면은 ngrok start/stop을 직접 실행하지 않고, 로컬 스크립트 명령과 현재 상태만 안내한다.

테스트:

1. status API status 파일 없음/있음 케이스.
2. token/API key 미노출 테스트.
3. `npm run build`
4. UX monkey route 목록에 `/settings/external-access` 추가
5. status 파일에 임의 secret-like 필드를 넣어도 API/화면에 노출되지 않는다.

### Step 10. 문서/README/전체 QA

목표: 다른 PC에서도 기능을 이해하고 검증할 수 있게 마무리합니다.

작업:

1. README에 계약서 생성 사용법을 추가한다.
2. README에 ngrok 설치/인증/실행/중지 가이드를 추가한다.
3. 문서 링크 목록에 이번 계획 문서를 추가한다.
4. `docs/work-log.md`에 구현/검증 결과를 누적 기록한다.
5. 필요하면 `docs/ux-monkey-testing-plan.md` route 목록을 갱신한다.
6. README 문서 링크 목록에 이번 계획서가 실제 클릭 가능한 상대경로로 포함되는지 검증한다.
7. 백업/복원 문구에 `storage/contracts` 포함 여부를 반영한다.
8. 운영 작업 이력 화면 라벨에 계약서 생성/삭제/검토 operation type을 추가한다.

전체 검증:

```powershell
py -3.13 -m pytest backend/tests -q
cd frontend
npm run build
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260607 --screenshot-dir ..\temp\ux-monkey-contracts
cd ..
py -3.13 scripts\check-encoding.py
git diff --check
```

## 우선순위

1. 계약서 DOCX 생성 BE 모델/API
2. 계약서 FE 생성/다운로드 UX
3. ngrok 실행 스크립트와 상태 API
4. 외부 접속 설정 페이지
5. README 가이드와 UX monkey 확장

ngrok은 시연/외부 확인용 운영 편의 기능이고, 계약서 생성은 서비스의 핵심 업무 기능에 가깝습니다. 따라서 실제 개발은 계약서 생성 MVP를 먼저 구현하고, ngrok은 이어서 붙이는 순서가 더 안전합니다. 다만 사용자가 외부 접속 시연을 먼저 원한다면 ngrok MVP부터 진행할 수 있습니다.

## Questions for Product Owner

- 현재 계획은 화면/DB 문구를 `계약서 초안`, DOCX 제목을 `용역표준계약서`로 고정합니다. 이 정책을 바꿀 필요가 있을까요?
- 계약서에 포함할 법인 정보 범위는 어디까지 허용할까요? 예: 사업자등록번호, 대표자명, 주소, 연락처.
- 현재 계획은 공고기관을 우선 표시합니다. 발주기관/수요기관 우선순위를 다르게 둘 필요가 있을까요?
- 현재 계획은 사용자 입력 계약금액을 우선하고 공고 금액은 참고값으로만 둡니다. 공고의 기초금액/추정가격을 자동 입력값으로 사용할까요?
- ngrok 외부 접속은 개발/시연용으로만 둘까요, 아니면 운영 기능으로 화면에 상시 노출할까요?
- ngrok 토큰/도메인 설정은 사용자가 직접 CLI에 설정하는 방식으로 둘까요, `.env` 입력 방식도 지원할까요?

---

# AI / Engineering Version (English)

## Objective

Plan two new features before implementation:

1. External access to the local-first app through ngrok.
2. Automatic DOCX contract draft generation from a selected corporation and saved Nara notice.

This document is plan-only. No implementation should start until the plan is accepted.

## Proposed Phases

- Phase 4E: ngrok external access support.
- Phase 5A: DOCX contract draft generation MVP.

## Feature 1: ngrok External Access

### Current Architecture

- Flask backend runs on `APP_PORT`.
- Vite frontend injects backend URL through `VITE_API_BASE_URL`.
- `scripts/manage-servers.ps1` starts backend and frontend locally.
- Backend currently binds to `127.0.0.1`; this can remain for ngrok agent tunneling.
- CORS currently allows all origins.

### Key Constraint

An external browser cannot call `127.0.0.1` on the user's machine. The frontend must be started with the backend ngrok public URL.

### Recommended Flow

1. Start the local backend.
2. Open an ngrok tunnel for the backend port.
3. Read backend public URL from the local ngrok API.
4. Start frontend with `VITE_API_BASE_URL=<backend-ngrok-url>`.
5. Open an ngrok tunnel for the frontend port.
6. Store status in `temp/ngrok.status.json`.

### Backend Additions

Environment variables:

- `APP_PORT`
- `APP_HOST`
- `EXTERNAL_ACCESS_ENABLED`
- `EXTERNAL_ACCESS_PROVIDER=ngrok`
- `APP_PUBLIC_BACKEND_URL`
- `APP_PUBLIC_FRONTEND_URL`
- `APP_CORS_ORIGINS`

API:

```text
GET /api/external-access/status
```

This endpoint reads `temp/ngrok.status.json` and returns masked/public-only state. It must not return the ngrok auth token or API keys.

### Script

Add:

```text
scripts/manage-ngrok.ps1
```

Actions:

- `start`
- `status`
- `stop`

Responsibilities:

- verify ngrok CLI/config
- start backend
- create backend tunnel
- discover backend public URL
- start frontend with that URL
- create frontend tunnel
- write status JSON
- clean up processes on stop

### Frontend

Add:

```text
/settings/external-access
```

The page should display:

- enabled/disabled state
- frontend public URL
- backend public URL
- local URLs
- update time
- warnings
- copy buttons

The frontend should not directly start/stop OS processes. PowerShell scripts handle that.

### Tests

- Backend endpoint with and without status file.
- No secrets in status payload.
- ngrok script URL parsing and status write.
- Frontend route renders empty/error states.
- `npm run build`.
- UX monkey includes `/settings/external-access`.

## Feature 2: DOCX Contract Draft Generation

### Scope

Generate a basic contract draft DOCX from:

- corporation profile
- selected saved Nara notice
- optional judgment run
- notice requirements
- missing/uncertain requirement guidance

The output is a draft and must not be represented as a legally final contract.

### Reference Form Layout

The user-provided reference PDF is:

```text
C:/Users/HOONJAE/Documents/카카오톡 받은 파일/[별지 제9호서식] 용역 표준계약서(지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙).pdf
```

The DOCX generator must reproduce this standard local-government service contract form layout, not a free-form narrative contract.

Observed reference layout:

- one-page A4 portrait form
- top-left `[별지 제9호서식] <개정 2024. 12. 6.>`
- top-right `(앞쪽)`
- centered title `용역표준계약서`
- upper-right contract number and notice number fields
- first table for contract parties, with a vertical `계약서` label
- second table for contract details, with a vertical `계약내용` label
- closing confirmation paragraph
- attachment list
- signature/seal lines for the local government head/contract officer and contractor
- `210㎜×297㎜` footer note

Implementation policy:

- Keep the generated record labeled as a draft in UI and DB.
- Use the official form title `용역표준계약서` inside the generated DOCX.
- The first DOCX page should follow the standard form table layout.
- Missing auto-fill values remain blank or use placeholders.
- Put missing-condition/judgment summaries in `Other notes` or a follow-up attachment-style section so the first-page form is not distorted.
- Do not commit the user's local PDF unless explicitly approved. Implement a repository-native DOCX/code template based on the inspected layout.

Field mapping:

| Standard form field | Source | Behavior |
| --- | --- | --- |
| Contract number | custom field | blank placeholder by default |
| Notice number | saved Nara notice number/order | auto-fill |
| Buyer | notice institution or demand institution | notice institution by default until PO decision |
| Contractor company name | corporation name | auto-fill |
| Address | corporation profile/custom field | blank if unavailable |
| Representative | corporation profile/custom field | blank if unavailable |
| Corporate registration number | corporation profile/custom field | blank if unavailable |
| Phone number | corporation profile/custom field | blank if unavailable |
| Service name | saved notice title | auto-fill |
| Contract amount | custom field or notice amount reference | PO decision required |
| Total service budget amount | custom field | blank by default |
| Contract guarantee | custom field | blank by default |
| Delay penalty rate | custom field | blank by default |
| Contract period | custom field or notice schedule reference | blank by default |
| Location | custom field or notice region | blank by default |
| Other notes | requirement/judgment summary | concise summary or follow-up page |

### New Table

```sql
contract_documents (
  id,
  nara_notice_id,
  corporation_id,
  judgment_run_id,
  status,
  review_status,
  contract_type,
  template_version,
  title,
  file_name,
  stored_file_path,
  file_size_bytes,
  input_snapshot_json,
  generated_fields_json,
  validation_json,
  error_message,
  created_at,
  updated_at
)
```

### Storage

```text
storage/contracts/{contract_document_id}/contract-{id}.docx
```

### Backend Service

Add:

```text
backend/app/services/contract_documents.py
```

Functions:

- `build_contract_input_snapshot`
- `validate_contract_generation_input`
- `render_basic_contract_docx`
- `create_contract_document`
- `contract_document_payload`
- `delete_contract_document`

Use `python-docx`, which is already in `backend/requirements.txt`.

### APIs

```text
GET /api/contracts
POST /api/contracts/preview
POST /api/contracts
GET /api/contracts/{contract_id}
GET /api/contracts/{contract_id}/download
DELETE /api/contracts/{contract_id}
PATCH /api/contracts/{contract_id}/review
```

### Frontend

Routes:

```text
/contracts
/contracts/:id
```

Add navigation item:

```text
Contract Drafts / 계약서 생성
```

Main page layout:

- corporation selector
- saved notice selector
- judgment run selector
- editable contract fields
- preview panel
- generate button
- history list
- download button

Entry points:

- saved notice detail
- judgment runs
- notice comparison

### Tests

Backend:

- preview success/failure
- generate DOCX and read it back with `python-docx`
- generated DOCX contains standard form labels: `용역표준계약서`, `계약서`, `계약내용`, `발주처`, `계약상대자`, `붙임서류`
- generated DOCX has at least two tables that represent the party and contract-detail sections
- generated DOCX uses A4 portrait page settings
- download content type and filename
- delete removes DB row and file
- judgment run mismatch validation
- no secret leakage in snapshot

Frontend:

- types and API helpers compile
- disabled generate when required selections are missing
- error states render
- download link renders
- `npm run build`
- UX monkey route coverage

## Detailed Implementation Steps

### Step 0. Freeze Product Policies

1. Keep UI and DB wording as `contract draft`; use `용역표준계약서` only as the generated DOCX title.
2. Use notice institution as the default buyer until the product owner decides otherwise.
3. Prefer user-entered contract amount; use `bssamt` or `presmpt_prce` only as a reference if no amount is entered.
4. Do not commit the user's local reference PDF.
5. Treat ngrok as a demo/testing external-access feature in the first implementation.
6. Generated contract rows and DOCX files must be based on an immutable input snapshot. Later notice, corporation, or judgment-run edits must not mutate existing drafts.
7. The first template is dedicated to the service standard contract form. If the selected notice is not clearly a service notice, generation may proceed but preview and DOCX review notes must include a warning.

Exit criteria:

- Decisions are recorded in this document and work-log.
- New unresolved decisions are added to Product Questions.

### Step 1. Contract Backend Data Model

1. Add `contract_documents` table creation to `init_db()`.
2. Add notice/corporation and created-at indexes.
3. Standardize `storage/contracts/{id}/` as output storage.
4. Decide and implement whether `storage/contracts` is included in backups.
5. Add file cleanup helper for delete flows.
6. Start with `status` values `generated`, `failed`, `deleted`; start with `review_status` values `draft`, `needs_review`, `approved`, `rejected`, `archived`.
7. Separate DB display filenames from filesystem-safe filenames so Korean titles and spaces do not break downloads.

Tests:

- table/indexes exist after DB init
- output path stays under `storage/contracts`
- backup policy covers generated DOCX and still excludes env files
- invalid `status` and `review_status` values are rejected

### Step 2. Contract Backend Snapshot And Validation

1. Add `backend/app/services/contract_documents.py`.
2. Implement `build_contract_input_snapshot`.
3. Validate missing notice/corporation.
4. Validate `judgment_run_id` belongs to the selected notice/corporation.
5. Normalize `custom_fields`.
6. Build snapshots from an allowlist so secrets never enter generated JSON.
7. Store contract-only supplemental values in `generated_fields_json` or `custom_fields`; do not update the corporation profile without explicit user approval.
8. Include template version, source ids, source display values, and generation time in the snapshot.

Tests:

- preview success
- missing notice/corporation failure
- mismatched judgment run failure
- no API keys, tokens, service keys, or env raw values in snapshot
- after source notice/corporation edits, an existing contract snapshot and download output remain unchanged

### Step 3. Standard Form DOCX Layout Builder

1. Implement `render_standard_service_contract_docx`.
2. Apply A4 portrait page settings and margins.
3. Add form header, title, contract number, and notice number.
4. Add first table for parties with vertical `계약서` label.
5. Add second table for contract details with vertical `계약내용` label.
6. Add closing paragraph, attachment list, signature/seal lines, and footer note.
7. Place long judgment/missing-condition summaries in a follow-up memo section.
8. Render to a temporary DOCX first, then move to the final path only after success; clean up temporary and partial outputs on failure.
9. If `python-docx` cannot exactly reproduce the visual PDF, the MVP acceptance standard is matching page setup, labels, table structure, and mapped fields; visual differences are documented in QA notes.

Tests:

- DOCX opens with `python-docx`
- contains standard labels
- has at least two tables
- uses A4 portrait settings
- auto-fills notice title, notice number, and corporation name
- blank custom fields do not fail generation
- forced render failure leaves no final DOCX and records a failed operation run

### Step 4. Contract Backend APIs

1. Add `GET /api/contracts`.
2. Add `POST /api/contracts/preview`.
3. Add `POST /api/contracts`.
4. Add `GET /api/contracts/{contract_id}`.
5. Add `GET /api/contracts/{contract_id}/download`.
6. Add `PATCH /api/contracts/{contract_id}/review`.
7. Add `DELETE /api/contracts/{contract_id}`.
8. Record operation runs for create/delete/review changes.
9. Return DOCX MIME type and UTF-8 safe filenames on download.
10. Support `notice_id`, `corporation_id`, `review_status`, `status`, and `keyword` filters in `GET /api/contracts`.
11. Persist generation failures as `contract_documents.status=failed` plus `operation_runs.status=failed` so admins can inspect the reason.
12. Return 404 when the stored DOCX is missing, and re-check that the resolved path stays under `storage/contracts`.

Tests:

- preview success/failure
- create returns `201`
- list/detail returns generated records
- download returns DOCX bytes
- delete removes row and file
- review updates status/note
- operation run is recorded
- failed generation stores failed row, failed operation run, and error reason
- list filters work by notice, corporation, status, and review status
- download uses UTF-8-safe `Content-Disposition` for Korean filenames

### Step 5. Contract Frontend Types And API

1. Add contract types to `frontend/src/app/types.ts`.
2. Add contract API helpers to `frontend/src/app/api.ts`.
3. Decide/export download URL helper.
4. Keep API errors consistent with existing `request()` behavior.
5. Normalize validation, warnings, and errors shapes so failed preview/create payloads cannot break UI state.

Tests:

- `npm run build`
- empty/error payloads are handled safely
- failed create response still refreshes the list and shows an error state

### Step 6. Contract Frontend Page

1. Add `frontend/src/pages/ContractsPage.tsx`.
2. Add corporation, saved notice, and judgment run selectors.
3. Add custom field form.
4. Add preview action and preview panel.
5. Add create action.
6. Add generated contract history.
7. Add download button.
8. Disable create until required selections are present.
9. Add generated-history filters by status, review status, and keyword.
10. Allow multiple drafts for the same notice/corporation pair; never overwrite an existing draft.

UX checks:

- quiet operational UI
- no long explanatory text inside the app
- responsive layout without overlapping
- destructive actions remain clear for monkey-test safety
- generating twice for the same pair shows two history rows and both downloads work

### Step 7. Contract Entry Points

1. Add sidebar nav item.
2. Add entry link from saved notice detail.
3. Add entry link from judgment runs.
4. Add entry link from notice comparison.
5. Support query params such as `/contracts?notice_id=1&corporation_id=2&judgment_run_id=3`.

Tests:

- entry links pass correct query params
- selectors initialize from query params
- deleted target data renders a safe empty/error state

### Step 8. ngrok Script

1. Add `scripts/manage-ngrok.ps1`.
2. Implement `start/status/stop`.
3. Verify ngrok CLI exists.
4. Verify ngrok auth is configured.
5. Start backend.
6. Open backend tunnel and read public URL.
7. Start frontend with backend public URL as `VITE_API_BASE_URL`.
8. Open frontend tunnel and read public URL.
9. Write `temp/ngrok.status.json`.
10. Stop all managed ngrok/server processes.
11. If ports are already occupied, inspect existing `manage-servers.ps1` status and only stop managed processes or return a clear error.
12. Because free ngrok URLs may change on restart, restart the frontend with the newly discovered backend public URL each time.
13. Store only public/local URLs, pids, ports, and updated time in the status file; never store tokens, API keys, or raw env values.

Tests:

- clear error when ngrok CLI is missing
- status JSON schema is valid
- public URLs exist after start
- stop cleans running state
- port collision handling does not kill arbitrary unrelated processes
- restart uses the latest backend public URL in `VITE_API_BASE_URL`

### Step 9. ngrok Backend/Frontend Status UI

1. Add `GET /api/external-access/status`.
2. Return `enabled=false` when status file is absent.
3. Return public/local URLs and updated time when present.
4. Exclude tokens, API keys, and env raw values.
5. Add Vite allowed-host option.
6. Add `ExternalAccessPage`.
7. Add `/settings/external-access` route/nav.
8. Show copy buttons and warnings.
9. Keep all-origin CORS for the MVP, but show a warning that external URLs expose the local app while tunnels are running.
10. Do not start or stop ngrok from the frontend; show local script commands and current status only.

Tests:

- status API with/without file
- no secret leakage
- `npm run build`
- UX monkey includes `/settings/external-access`
- even if a status file contains secret-like fields, API/UI responses do not expose them

### Step 10. Documentation And Full QA

1. Add contract draft usage guide to README.
2. Add ngrok install/auth/start/stop guide to README.
3. Add this plan to README document links.
4. Keep appending implementation and verification results to `docs/work-log.md`.
5. Update UX monkey route documentation if needed.
6. Verify the README link to this plan uses a clickable repository-relative path.
7. Update backup/restore wording to reflect whether `storage/contracts` is included.
8. Add labels for contract create/delete/review operation types in the operations UI.

Verification:

```powershell
py -3.13 -m pytest backend/tests -q
cd frontend
npm run build
npm run ux:monkey -- --base-url http://127.0.0.1:5199 --steps 80 --seed 20260607 --screenshot-dir ..\temp\ux-monkey-contracts
cd ..
py -3.13 scripts\check-encoding.py
git diff --check
```

## Product Questions

- Current policy keeps UI/DB wording as `contract draft` and the generated DOCX title as `용역표준계약서`. Should this policy change?
- Which corporation fields may be included in DOCX?
- Current policy uses notice institution first. Should buyer/counterparty priority change?
- Current policy prefers user-entered amount and treats notice amount only as reference. Should notice amount be auto-filled?
- Is ngrok only for demo/testing, or a persistent operations feature?
- Should ngrok configuration live in CLI config only or also in `.env`?
