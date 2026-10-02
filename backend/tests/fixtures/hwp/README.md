# 한글 엔진 합성 픽스처

`synthetic.hwp`와 `synthetic.hwpx`는 개인 문서를 사용하지 않는 읽기·쓰기 회귀 검증 자료입니다.
RHWP의 MIT 라이선스 `template/empty.hwp`에 테스트 문구를 삽입하고 공식 CLI 0.8.6으로 생성했습니다.
입찰참가자격, 사업자등록증, 제출기한과 `RHWP_TEST_ORIGINAL` 식별자를 포함합니다.
외부 엔진의 라이선스는 `backend/third_party/RHWP-LICENSE.txt`에 보존합니다.

## AI / Engineering Version (English)

These fixtures contain synthetic Korean qualification/date text and the literal marker `RHWP_TEST_ORIGINAL`.
They were created with RHWP 0.8.6 from its MIT-licensed `template/empty.hwp`; no customer document was used.
The HWPX fixture was exported with successful IR and page-count verification.
Retain the upstream notice in `backend/third_party/RHWP-LICENSE.txt` when redistributing the fixtures.
