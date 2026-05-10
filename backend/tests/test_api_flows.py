import io
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import fitz
from docx import Document

_TMP_DIR = Path(tempfile.mkdtemp(prefix="wisdom_api_tests_"))

os.environ["SQLITE_PATH"] = str(_TMP_DIR / "test.db")
os.environ["STORAGE_ROOT"] = str(_TMP_DIR / "storage")
os.environ["OCR_ENGINE"] = "noop"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["AI_PROVIDER_DEFAULT"] = "gemini"
os.environ["AI_MODEL_DEFAULT"] = "gemini-2.5-flash"
os.environ.pop("NARA_API_SERVICE_KEY", None)

from app import main as runtime  # noqa: E402

runtime.NARA_API_SERVICE_KEY = ""
runtime.OPENAI_API_KEY = ""
runtime.GEMINI_API_KEY = ""


def make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((40, 80), text)
    payload = doc.tobytes()
    doc.close()
    return payload


def make_docx_bytes(text: str) -> bytes:
    doc = Document()
    for line in text.strip().splitlines():
        doc.add_paragraph(line.strip())
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class ApiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        runtime.app.config["TESTING"] = True
        self.client = runtime.app.test_client()
        with runtime.db_conn() as conn:
            conn.executescript(
                """
                DELETE FROM analyses;
                DELETE FROM corporation_profile_update_candidates;
                DELETE FROM corporation_evidence_documents;
                DELETE FROM nara_notice_attachments;
                DELETE FROM nara_notices;
                DELETE FROM integration_test_results;
                DELETE FROM project_documents;
                DELETE FROM projects;
                DELETE FROM corporations;
                """
            )
            conn.commit()

        storage_root = Path(os.environ["STORAGE_ROOT"])
        if storage_root.exists():
            shutil.rmtree(storage_root)
        runtime.init_db()

    def create_corporation(self) -> dict:
        response = self.client.post(
            "/api/corporations",
            json={
                "name": "테스트 법인",
                "business_category": "IT",
                "region": "서울",
                "certifications_json": ["ISO9001"],
                "company_size_classification": "중소기업",
                "internal_notes": "테스트",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_project(self, corporation_id: int) -> dict:
        response = self.client.post(
            "/api/projects",
            json={
                "name": "테스트 프로젝트",
                "corporation_id": corporation_id,
                "status": "active",
                "notes": "초기 메모",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def upload_document(self, project_id: int) -> dict:
        response = self.client.post(
            "/api/documents",
            data={
                "project_id": str(project_id),
                "document_type": "notice",
                "memo": "업로드 메모",
                "revision_note": "r1",
                "file": (io.BytesIO(make_pdf_bytes("Phase 1 API flow notice")), "notice.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def upload_business_registration_evidence(
        self,
        corporation_id: int | None = None,
        management_group_name: str = "기본 관리그룹",
    ) -> dict:
        evidence_text = """
        사업자등록증
        등록번호 : 142-81-28387
        법인명(단체명) : 주식회사 온세이엔씨
        대표자 : 안영식
        개업연월일 : 2010 년 05 월 25 일
        법인등록번호 : 134511-0154712
        사업장 소재지 : 경기도 성남시 수정구 청계산로 686, 8층 820호
        사업의 종류 : 업태 건설업
        종목 전기공사
        """
        data = {
            "document_type": "auto",
            "management_group_name": management_group_name,
            "memo": "사업자등록증 자동 추출 테스트",
            "file": (io.BytesIO(make_docx_bytes(evidence_text)), "business-registration.docx"),
        }
        if corporation_id:
            data["corporation_id"] = str(corporation_id)

        response = self.client.post(
            "/api/corporation-evidence-documents",
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def wait_for_saved_nara_notice(self, notice_id: int, timeout: float = 5.0) -> dict:
        deadline = time.time() + timeout
        last_payload: dict | None = None
        while time.time() < deadline:
            response = self.client.get(f"/api/nara/saved-notices/{notice_id}")
            self.assertEqual(response.status_code, 200)
            last_payload = response.get_json()
            if last_payload["analysis_status"] not in {"pending", "saving", "queued"}:
                return last_payload
            time.sleep(0.05)

        self.fail(f"Nara notice job did not finish in time. last_payload={last_payload}")

    def upload_small_business_evidence(self, corporation_id: int) -> dict:
        evidence_text = """
        중소기업확인서
        기업명 : 테스트 법인
        사업자등록번호 : 142-81-28387
        대표자 : 안영식
        기업규모 : 소기업
        유효기간 : 2026.01.01 ~ 2026.12.31
        """
        response = self.client.post(
            "/api/corporation-evidence-documents",
            data={
                "corporation_id": str(corporation_id),
                "document_type": "auto",
                "memo": "중소기업확인서 자동 추출 테스트",
                "file": (io.BytesIO(make_docx_bytes(evidence_text)), "small-business.docx"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def test_crud_update_delete_flow(self) -> None:
        corporation = self.create_corporation()
        corp_patch = self.client.patch(
            f"/api/corporations/{corporation['id']}",
            json={"region": "부산", "certifications_json": "직접생산확인, ISO14001"},
        )
        self.assertEqual(corp_patch.status_code, 200)
        self.assertEqual(corp_patch.get_json()["region"], "부산")

        project = self.create_project(corporation["id"])
        project_patch = self.client.patch(
            f"/api/projects/{project['id']}",
            json={"name": "수정된 프로젝트", "status": "paused"},
        )
        self.assertEqual(project_patch.status_code, 200)
        self.assertEqual(project_patch.get_json()["status"], "paused")

        document = self.upload_document(project["id"])
        document_patch = self.client.patch(
            f"/api/documents/{document['id']}",
            json={"document_type": "spec", "memo": "수정된 메모", "revision_note": "r2"},
        )
        self.assertEqual(document_patch.status_code, 200)
        self.assertEqual(document_patch.get_json()["document_type"], "spec")

        document_delete = self.client.delete(f"/api/documents/{document['id']}")
        self.assertEqual(document_delete.status_code, 200)

        project_delete = self.client.delete(f"/api/projects/{project['id']}")
        self.assertEqual(project_delete.status_code, 200)

        corp_delete = self.client.delete(f"/api/corporations/{corporation['id']}")
        self.assertEqual(corp_delete.status_code, 200)

    def test_project_delete_removes_documents_analyses_and_files(self) -> None:
        corporation = self.create_corporation()
        project = self.create_project(corporation["id"])
        document = self.upload_document(project["id"])
        stored_path = Path(document["stored_file_path"])
        self.assertTrue(stored_path.exists())

        analysis = self.client.post(f"/api/documents/{document['id']}/analyze")
        self.assertEqual(analysis.status_code, 200)

        project_delete = self.client.delete(f"/api/projects/{project['id']}")
        self.assertEqual(project_delete.status_code, 200)
        self.assertFalse(stored_path.exists())

        with runtime.db_conn() as conn:
            doc_count = conn.execute("SELECT COUNT(*) c FROM project_documents").fetchone()["c"]
            analysis_count = conn.execute("SELECT COUNT(*) c FROM analyses").fetchone()["c"]

        self.assertEqual(doc_count, 0)
        self.assertEqual(analysis_count, 0)

    def test_ai_model_settings_masks_keys_and_defaults_to_gemini(self) -> None:
        previous_gemini_key = runtime.GEMINI_API_KEY
        previous_openai_key = runtime.OPENAI_API_KEY
        try:
            runtime.GEMINI_API_KEY = "gemini-test-key-123456"
            runtime.OPENAI_API_KEY = "openai-test-key-123456"

            response = self.client.get("/api/settings/ai-models")

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["default_provider"], "gemini")
            self.assertEqual(payload["default_model"], "gemini-2.5-flash")
            self.assertTrue(payload["providers"]["gemini"]["configured"])
            self.assertTrue(payload["providers"]["openai"]["configured"])
            self.assertNotIn("gemini-test-key-123456", json.dumps(payload))
            option_keys = {(item["provider"], item["model"]) for item in payload["options"]}
            self.assertIn(("gemini", "gemini-2.5-flash"), option_keys)
            gemini_option = next(item for item in payload["options"] if item["provider"] == "gemini")
            self.assertIn("gemini-2.5-flash", gemini_option["label"])
            self.assertNotIn("Flash-Lite", gemini_option["label"])
        finally:
            runtime.GEMINI_API_KEY = previous_gemini_key
            runtime.OPENAI_API_KEY = previous_openai_key

    def test_document_analysis_uses_selected_ai_model(self) -> None:
        corporation = self.create_corporation()
        project = self.create_project(corporation["id"])
        document = self.upload_document(project["id"])
        previous_summarizer = runtime.summarize_with_ai
        previous_gemini_key = runtime.GEMINI_API_KEY
        observed = {}

        def fake_summarizer(text: str, selection: dict):
            observed["selection"] = dict(selection)
            payload = {
                "document_summary": "선택 모델 테스트 요약",
                "key_dates": [],
                "requirements": ["요구사항 A"],
                "required_documents": [],
                "risks": [],
                "questions_to_check": [],
                "confidence_note": "테스트",
            }
            usage = {
                "provider": selection["provider"],
                "model": selection["model"],
                "input_chars": len(text),
            }
            return payload, runtime.render_summary_markdown(payload), usage

        try:
            runtime.GEMINI_API_KEY = "gemini-test-key"
            runtime.summarize_with_ai = fake_summarizer

            response = self.client.post(
                f"/api/documents/{document['id']}/analyze",
                json={
                    "model_provider": "gemini",
                    "model_name": "gemini-2.5-flash",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(observed["selection"]["provider"], "gemini")
            self.assertEqual(observed["selection"]["model"], "gemini-2.5-flash")

            latest = self.client.get(f"/api/analyses/latest/by-document/{document['id']}")
            self.assertEqual(latest.status_code, 200)
            analysis = latest.get_json()
            self.assertEqual(analysis["model_provider"], "gemini")
            self.assertEqual(analysis["model_name"], "gemini-2.5-flash")
        finally:
            runtime.summarize_with_ai = previous_summarizer
            runtime.GEMINI_API_KEY = previous_gemini_key

    def test_unknown_evidence_uses_ai_classification_fallback_as_review_candidates(self) -> None:
        previous_classifier = runtime.classify_unknown_evidence_with_ai
        previous_gemini_key = runtime.GEMINI_API_KEY
        observed = {}

        def fake_classifier(text: str, file_name: str, provider=None, model=None):
            observed["file_name"] = file_name
            observed["text"] = text
            return runtime.EvidenceExtractionResult(
                document_type="credit_rating_certificate",
                classification_confidence=0.73,
                classification_status="ai_suggested",
                candidates=[
                    runtime.EvidenceFieldCandidate(
                        field_key="certifications_json",
                        field_label="인증/확인서",
                        extracted_value='["기업신용평가등급 B+"]',
                        confidence=0.7,
                        source_text="기업신용평가등급 B+",
                    )
                ],
                warnings=["AI 분류 제안 테스트"],
            )

        try:
            runtime.GEMINI_API_KEY = "gemini-test-key"
            runtime.classify_unknown_evidence_with_ai = fake_classifier
            response = self.client.post(
                "/api/corporation-evidence-documents",
                data={
                    "document_type": "auto",
                    "management_group_name": "AI그룹",
                    "memo": "알 수 없는 증빙 AI 분류 테스트",
                    "file": (
                        io.BytesIO(
                            make_docx_bytes(
                                """
                                협력업체 내부 검토 메모
                                업체명 : 테스트 법인
                                참고 문구 : 담당자가 별도 확인해야 하는 임의 자료
                                비고 : 규칙 기반 분류 대상이 아닌 문서
                                """
                            )
                        ),
                        "unknown-evidence.docx",
                    ),
                },
                content_type="multipart/form-data",
            )

            self.assertEqual(response.status_code, 201)
            payload = response.get_json()
            self.assertEqual(payload["document_type"], "credit_rating_certificate")
            self.assertEqual(payload["classification_status"], "ai_suggested")
            self.assertEqual(payload["review_status"], "pending")
            self.assertEqual(payload["candidates"][0]["field_key"], "certifications_json")
            self.assertEqual(payload["candidates"][0]["status"], "pending")
            self.assertEqual(observed["file_name"], "unknown-evidence.docx")
        finally:
            runtime.classify_unknown_evidence_with_ai = previous_classifier
            runtime.GEMINI_API_KEY = previous_gemini_key

    def test_business_registration_kind_fields_use_ai_cleanup_when_configured(self) -> None:
        previous_generator = runtime.generate_json_with_ai
        previous_gemini_key = runtime.GEMINI_API_KEY
        observed = {}

        def fake_json_generator(prompt: str, selection: dict):
            observed["prompt"] = prompt
            observed["selection"] = dict(selection)
            return (
                {
                    "business_type": ["건설업", "도소매", "도매 및 소매업"],
                    "business_item": [
                        "전기공사",
                        "신재생에너지설비설치전문기업",
                        "일반건축공사업",
                        "전문소방시설공사",
                        "안전시설물설치",
                        "정보통신공사업",
                        "토목공사업",
                        "전기",
                        "소방",
                        "통신자재",
                        "컴퓨터 관련 주변기기",
                        "산업안전용품",
                    ],
                    "business_category": "업태: 건설업, 도소매, 도매 및 소매업 / 종목: 전기공사, 신재생에너지설비설치전문기업, 일반건축공사업, 전문소방시설공사, 안전시설물설치, 정보통신공사업, 토목공사업, 전기, 소방, 통신자재, 컴퓨터 관련 주변기기, 산업안전용품",
                    "warnings": [],
                },
                {"provider": "gemini", "model": selection["model"]},
            )

        ocr_text = """
        사업자등록증
        등록번호 : 142-81-28387
        법인명(단체명) : 주식회사 온세이엔씨
        대표자 : 안영식
        사업의 종류:
        업태
        건설업
        종목
        전기공사,신재생에너지설비설치전문기
        업
        건설업
        일반건축공사업
        도매 및
        소매업
        컴퓨터 관련 주변기기
        """

        try:
            runtime.GEMINI_API_KEY = "gemini-test-key"
            runtime.generate_json_with_ai = fake_json_generator
            result = runtime.analyze_corporation_evidence_text(
                ocr_text,
                "사업자등록증.png",
                "auto",
            )

            fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}
            self.assertEqual(observed["selection"]["provider"], "gemini")
            self.assertIn("사업의 종류", observed["prompt"])
            self.assertIn("신재생에너지설비설치전문기업", fields["business_item"])
            self.assertIn("컴퓨터 관련 주변기기", fields["business_item"])
            self.assertIn("업태: 건설업", fields["business_category"])
            self.assertTrue(any("AI 업태/종목 정리" in warning for warning in result.warnings))
        finally:
            runtime.generate_json_with_ai = previous_generator
            runtime.GEMINI_API_KEY = previous_gemini_key

    def test_evidence_upload_extracts_candidates_and_creates_corporation_after_approval(self) -> None:
        evidence = self.upload_business_registration_evidence()

        self.assertEqual(evidence["document_type"], "business_registration_certificate")
        self.assertEqual(evidence["classification_status"], "classified")
        field_values = {candidate["field_key"]: candidate["extracted_value"] for candidate in evidence["candidates"]}
        self.assertEqual(field_values["business_registration_number"], "142-81-28387")
        self.assertEqual(field_values["name"], "주식회사 온세이엔씨")
        self.assertEqual(field_values["representative_name"], "안영식")

        response = self.client.post(f"/api/corporation-evidence-documents/{evidence['id']}/approve", json={})
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        corporation = payload["corporation"]
        self.assertEqual(corporation["name"], "주식회사 온세이엔씨")
        self.assertEqual(corporation["business_registration_number"], "142-81-28387")
        self.assertEqual(corporation["representative_name"], "안영식")
        self.assertEqual(corporation["evidence_verification_status"], "evidence_reviewed")
        self.assertIn("name", payload["applied_fields"])

    def test_evidence_approval_updates_existing_corporation(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])

        response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/approve",
            json={"field_values": {"name": corporation["name"]}},
        )
        self.assertEqual(response.status_code, 200)

        updated = response.get_json()["corporation"]
        self.assertEqual(updated["id"], corporation["id"])
        self.assertEqual(updated["business_registration_number"], "142-81-28387")
        self.assertEqual(updated["representative_name"], "안영식")

        list_response = self.client.get(f"/api/corporations/{corporation['id']}/evidence-documents")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.get_json()), 1)

    def test_empty_candidate_ids_does_not_approve_all_candidates_when_field_values_exist(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])

        response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/approve",
            json={
                "candidate_ids": [],
                "field_values": {"name": corporation["name"]},
            },
        )

        self.assertEqual(response.status_code, 200)
        updated = response.get_json()["corporation"]
        self.assertEqual(updated["name"], corporation["name"])
        self.assertEqual(updated["business_registration_number"], "")

        detail = self.client.get(f"/api/corporation-evidence-documents/{evidence['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(all(candidate["status"] == "pending" for candidate in detail.get_json()["candidates"]))

    def test_selected_evidence_candidates_only_apply_selected_and_edited_values(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])
        candidates = {candidate["field_key"]: candidate for candidate in evidence["candidates"]}

        response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/approve",
            json={
                "candidate_ids": [
                    candidates["business_registration_number"]["id"],
                    candidates["representative_name"]["id"],
                ],
                "field_values": {"representative_name": "수정대표"},
            },
        )

        self.assertEqual(response.status_code, 200)
        updated = response.get_json()["corporation"]
        self.assertEqual(updated["name"], corporation["name"])
        self.assertEqual(updated["business_registration_number"], "142-81-28387")
        self.assertEqual(updated["representative_name"], "수정대표")

        detail = self.client.get(f"/api/corporation-evidence-documents/{evidence['id']}")
        self.assertEqual(detail.status_code, 200)
        statuses = {candidate["field_key"]: candidate["status"] for candidate in detail.get_json()["candidates"]}
        self.assertEqual(statuses["business_registration_number"], "approved")
        self.assertEqual(statuses["representative_name"], "approved")
        self.assertEqual(statuses["name"], "pending")

    def test_core_evidence_approval_merges_certifications_and_preference_tags(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_small_business_evidence(corporation["id"])

        self.assertEqual(evidence["document_type"], "small_business_confirmation")
        fields = {candidate["field_key"]: candidate["extracted_value"] for candidate in evidence["candidates"]}
        self.assertEqual(fields["company_size_classification"], "소기업")

        response = self.client.post(f"/api/corporation-evidence-documents/{evidence['id']}/approve", json={})
        self.assertEqual(response.status_code, 200)

        updated = response.get_json()["corporation"]
        certifications = json.loads(updated["certifications_json"])
        preference_tags = json.loads(updated["preference_tags_json"])
        self.assertIn("ISO9001", certifications)
        self.assertIn("중소기업확인서", certifications)
        self.assertIn("중소기업", preference_tags)
        self.assertEqual(updated["company_size_classification"], "소기업")

    def test_corporation_readiness_reports_missing_items_and_evidence_progress(self) -> None:
        corporation = self.create_corporation()

        initial_response = self.client.get(f"/api/corporations/{corporation['id']}/readiness")
        self.assertEqual(initial_response.status_code, 200)
        initial = initial_response.get_json()
        self.assertEqual(initial["status"], "needs_evidence")
        self.assertIn("사업자등록번호", initial["missing_items"])
        self.assertEqual(initial["evidence_count"], 0)

        evidence = self.upload_business_registration_evidence(corporation["id"])
        approve_response = self.client.post(f"/api/corporation-evidence-documents/{evidence['id']}/approve", json={})
        self.assertEqual(approve_response.status_code, 200)

        list_response = self.client.get("/api/corporations/readiness")
        self.assertEqual(list_response.status_code, 200)
        readiness = list_response.get_json()[0]
        self.assertEqual(readiness["corporation_id"], corporation["id"])
        self.assertGreater(readiness["score"], initial["score"])
        self.assertGreaterEqual(readiness["approved_candidate_count"], 1)
        self.assertNotIn("사업자등록번호", readiness["missing_items"])

    def test_evidence_documents_can_be_listed_updated_and_reprocessed(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_small_business_evidence(corporation["id"])

        list_response = self.client.get("/api/corporation-evidence-documents")
        self.assertEqual(list_response.status_code, 200)
        rows = list_response.get_json()
        self.assertEqual(rows[0]["id"], evidence["id"])
        self.assertEqual(rows[0]["corporation_name"], corporation["name"])
        self.assertGreater(rows[0]["candidate_count"], 0)
        self.assertEqual(rows[0]["pending_candidate_count"], rows[0]["candidate_count"])
        self.assertEqual(rows[0]["candidates"], [])

        patch_response = self.client.patch(
            f"/api/corporation-evidence-documents/{evidence['id']}",
            json={
                "memo": "메타데이터 수정 테스트",
                "review_status": "needs_review",
                "document_type": "small_business_confirmation",
            },
        )
        self.assertEqual(patch_response.status_code, 200)
        patched = patch_response.get_json()
        self.assertEqual(patched["memo"], "메타데이터 수정 테스트")
        self.assertEqual(patched["review_status"], "needs_review")

        reprocess_response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/reprocess",
            json={"document_type": "small_business_confirmation"},
        )
        self.assertEqual(reprocess_response.status_code, 200)
        reprocessed = reprocess_response.get_json()
        self.assertEqual(reprocessed["document_type"], "small_business_confirmation")
        self.assertEqual(reprocessed["review_status"], "pending")
        self.assertTrue(reprocessed["candidates"])
        self.assertIn("중소기업확인서", reprocessed["extracted_text_preview"])

    def test_evidence_reprocess_preserves_approved_candidates_without_duplicate_pending_values(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])
        candidates = {candidate["field_key"]: candidate for candidate in evidence["candidates"]}

        approve_response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/approve",
            json={"candidate_ids": [candidates["business_registration_number"]["id"]]},
        )
        self.assertEqual(approve_response.status_code, 200)

        reprocess_response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/reprocess",
            json={"document_type": "business_registration_certificate"},
        )
        self.assertEqual(reprocess_response.status_code, 200)
        reprocessed = reprocess_response.get_json()
        business_number_candidates = [
            candidate
            for candidate in reprocessed["candidates"]
            if candidate["field_key"] == "business_registration_number"
            and candidate["extracted_value"] == "142-81-28387"
        ]

        self.assertEqual(len(business_number_candidates), 1)
        self.assertEqual(business_number_candidates[0]["status"], "approved")
        self.assertTrue(any(candidate["status"] == "pending" for candidate in reprocessed["candidates"]))

    def test_evidence_corrected_text_can_be_reanalyzed(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])

        corrected_text = """
        기업신용평가등급확인서
        업체명 : 테스트 법인
        사업자등록번호 : 142-81-28387
        평가등급 : A-
        유효기간 : 2026.01.01 ~ 2026.12.31
        """
        response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/reanalyze-text",
            json={
                "document_type": "auto",
                "extracted_text": corrected_text,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["document_type"], "credit_rating_certificate")
        self.assertEqual(payload["ocr_status"], "corrected")
        self.assertIn("A-", payload["extracted_text"])
        fields = {candidate["field_key"]: candidate["extracted_value"] for candidate in payload["candidates"]}
        self.assertIn("기업신용평가등급 A-", fields["certifications_json"])

    def test_evidence_corrected_text_requires_non_empty_text(self) -> None:
        corporation = self.create_corporation()
        evidence = self.upload_business_registration_evidence(corporation["id"])

        response = self.client.post(
            f"/api/corporation-evidence-documents/{evidence['id']}/reanalyze-text",
            json={"document_type": "auto", "extracted_text": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("extracted_text", response.get_json()["detail"])

    def test_business_registration_duplicate_is_blocked_inside_same_management_group(self) -> None:
        first = self.client.post(
            "/api/corporations",
            json={
                "name": "기존 법인",
                "management_group_name": "A그룹",
                "business_registration_number": "142-81-28387",
            },
        )
        self.assertEqual(first.status_code, 201)

        duplicate = self.client.post(
            "/api/corporations",
            json={
                "name": "같은 그룹 중복 법인",
                "management_group_name": "A그룹",
                "business_registration_number": "1428128387",
            },
        )

        self.assertEqual(duplicate.status_code, 409)
        self.assertIn("동일한 사업자등록번호", duplicate.get_json()["detail"])

    def test_business_registration_duplicate_is_allowed_across_management_groups_with_warning(self) -> None:
        first = self.client.post(
            "/api/corporations",
            json={
                "name": "기존 법인",
                "management_group_name": "A그룹",
                "business_registration_number": "142-81-28387",
            },
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/api/corporations",
            json={
                "name": "다른 그룹 법인",
                "management_group_name": "B그룹",
                "business_registration_number": "1428128387",
            },
        )

        self.assertEqual(second.status_code, 201)
        payload = second.get_json()
        self.assertEqual(payload["business_registration_number"], "142-81-28387")
        self.assertIn("warnings", payload)
        self.assertEqual(payload["duplicate_corporations"][0]["management_group_name"], "A그룹")

    def test_evidence_created_corporation_uses_management_group_duplicate_policy(self) -> None:
        existing = self.client.post(
            "/api/corporations",
            json={
                "name": "기존 법인",
                "management_group_name": "A그룹",
                "business_registration_number": "142-81-28387",
            },
        )
        self.assertEqual(existing.status_code, 201)

        blocked_evidence = self.upload_business_registration_evidence(management_group_name="A그룹")
        blocked = self.client.post(f"/api/corporation-evidence-documents/{blocked_evidence['id']}/approve", json={})
        self.assertEqual(blocked.status_code, 409)

        allowed_evidence = self.upload_business_registration_evidence(management_group_name="B그룹")
        allowed = self.client.post(f"/api/corporation-evidence-documents/{allowed_evidence['id']}/approve", json={})
        self.assertEqual(allowed.status_code, 200)
        payload = allowed.get_json()
        self.assertEqual(payload["corporation"]["management_group_name"], "B그룹")
        self.assertTrue(payload["warnings"])

    def test_nara_settings_status_does_not_expose_full_key_when_unconfigured(self) -> None:
        response = self.client.get("/api/settings/integrations/nara/status")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertFalse(payload["configured"])
        self.assertEqual(payload["masked_key"], "")
        self.assertEqual(payload["last_test_status"], "not_run")
        self.assertNotIn("service_key", payload)

    def test_nara_settings_status_returns_latest_saved_test_result(self) -> None:
        runtime.save_integration_test_result("nara", "ok", 200, "00", "NORMAL SERVICE", 7)

        response = self.client.get("/api/settings/integrations/nara/status")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertEqual(payload["last_test_status"], "ok")
        self.assertEqual(payload["last_test_http_status"], 200)
        self.assertEqual(payload["last_test_result_code"], "00")
        self.assertEqual(payload["last_test_total_count"], 7)
        self.assertTrue(payload["last_tested_at"])

    def test_nara_search_requires_api_key(self) -> None:
        response = self.client.get("/api/nara/notices/search")
        self.assertEqual(response.status_code, 400)
        self.assertIn("NARA_API_SERVICE_KEY", response.get_json()["detail"])

    def test_attachment_preview_rejects_missing_url(self) -> None:
        response = self.client.get("/api/nara/attachments/preview")
        self.assertEqual(response.status_code, 400)
        self.assertIn("url is required", response.get_json()["detail"])

    def test_nara_notice_can_be_saved_and_summarized_from_selected_raw_item(self) -> None:
        response = self.client.post(
            "/api/nara/notices/save-and-analyze",
            json={
                "notice": {
                    "bidNtceNo": "20260500001",
                    "bidNtceOrd": "000",
                    "bidNtceNm": "테스트 나라장터 공고",
                    "ntceInsttNm": "테스트 공고기관",
                    "dminsttNm": "테스트 수요기관",
                    "bidNtceDt": "2026-05-05 10:00",
                    "bidBeginDt": "2026-05-10 09:00",
                    "bidClseDt": "2026-05-20 17:00",
                    "opengDt": "2026-05-21 11:00",
                    "presmptPrce": "1000000",
                    "bssamt": "1100000",
                    "prtcptPsblRgnNm": "경기도",
                    "lcnsLmtNm": "조경식재공사업",
                    "bidNtceDtlUrl": "https://example.go.kr/notice/20260500001",
                    "ntceSpecFileNm1": "sample.hwp",
                    "ntceSpecDocUrl1": "",
                }
            },
        )
        self.assertEqual(response.status_code, 202)

        payload = response.get_json()
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["notice"]["bid_ntce_no"], "20260500001")
        self.assertEqual(payload["notice"]["analysis_status"], "pending")

        saved = self.wait_for_saved_nara_notice(payload["notice"]["id"])
        self.assertEqual(saved["download_status"], "no_supported_attachments")
        self.assertIn("문서 요약", saved["analysis_summary_markdown"])
        self.assertIn("공고 요구조건 구조화 후보", saved["analysis_summary_markdown"])
        summary_json = json.loads(saved["analysis_summary_json"])
        requirements = summary_json["notice_requirements"]
        self.assertIn("경기도", requirements["regions"])
        self.assertIn("조경식재공사업", requirements["licenses"])
        self.assertEqual(requirements["money"]["presmpt_prce"], "1000000")
        self.assertEqual(requirements["dates"]["bid_clse_dt"], "2026-05-20 17:00")
        self.assertFalse(
            any(attachment["source_field"] == "stdNtceDocUrl" for attachment in saved["attachments"])
        )

        saved_response = self.client.get(f"/api/nara/saved-notices/{payload['notice']['id']}")
        self.assertEqual(saved_response.status_code, 200)
        self.assertEqual(saved_response.get_json()["bid_ntce_nm"], "테스트 나라장터 공고")

    def test_notice_requirement_extraction_reads_text_candidates_without_verdict(self) -> None:
        requirements = runtime.extract_notice_requirements(
            {
                "region_text": "전라남도 해남군",
                "license_text": "산림사업법인",
                "presmpt_prce": "103980909",
                "bid_clse_dt": "2026-05-08 10:00",
            },
            """
            입찰참가자격: 중소기업확인서를 보유한 업체
            면허: 산림사업법인 또는 조경식재공사업 등록 업체
            제출서류: 사업자등록증, 국세납세증명서, 직접생산확인증명서
            우대조건: 여성기업
            """,
        )

        self.assertIn("전라남도 해남군", requirements["regions"])
        self.assertIn("산림사업법인", requirements["licenses"])
        self.assertIn("조경식재", requirements["licenses"])
        self.assertIn("중소기업", requirements["company_types"])
        self.assertIn("여성기업", requirements["company_types"])
        self.assertIn("사업자등록증", requirements["required_documents"])
        self.assertIn("국세 납세증명서", requirements["required_documents"])
        self.assertTrue(requirements["uncertainty_notes"])
        self.assertNotIn("eligible", json.dumps(requirements).lower())

    def test_standard_notice_url_is_named_in_korean_when_present(self) -> None:
        attachments = runtime.collect_nara_attachments(
            [
                {
                    "stdNtceDocUrl": "https://example.go.kr/notice/standard",
                }
            ]
        )

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["file_name"], "표준공고문.pdf")
        self.assertEqual(attachments[0]["support_status"], "supported")


if __name__ == "__main__":
    unittest.main()
