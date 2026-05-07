import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import fitz

_TMP_DIR = Path(tempfile.mkdtemp(prefix="wisdom_api_tests_"))

os.environ["SQLITE_PATH"] = str(_TMP_DIR / "test.db")
os.environ["STORAGE_ROOT"] = str(_TMP_DIR / "storage")
os.environ.pop("NARA_API_SERVICE_KEY", None)

from app import main as runtime  # noqa: E402

runtime.NARA_API_SERVICE_KEY = ""


def make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((40, 80), text)
    payload = doc.tobytes()
    doc.close()
    return payload


class ApiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        runtime.app.config["TESTING"] = True
        self.client = runtime.app.test_client()
        with runtime.db_conn() as conn:
            conn.executescript(
                """
                DELETE FROM analyses;
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
                    "bidClseDt": "2026-05-20 17:00",
                    "presmptPrce": "1000000",
                    "ntceSpecFileNm1": "sample.hwp",
                    "ntceSpecDocUrl1": "",
                }
            },
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["notice"]["bid_ntce_no"], "20260500001")
        self.assertEqual(payload["notice"]["download_status"], "no_supported_attachments")
        self.assertIn("문서 요약", payload["notice"]["analysis_summary_markdown"])
        self.assertFalse(
            any(attachment["source_field"] == "stdNtceDocUrl" for attachment in payload["notice"]["attachments"])
        )

        saved = self.client.get(f"/api/nara/saved-notices/{payload['notice']['id']}")
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["bid_ntce_nm"], "테스트 나라장터 공고")

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
