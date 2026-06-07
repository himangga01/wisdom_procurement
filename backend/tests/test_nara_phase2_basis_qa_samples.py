import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


if os.getenv("RUN_NARA_PHASE2_QA") != "1":
    raise unittest.SkipTest("Set RUN_NARA_PHASE2_QA=1 after downloading samples to run Phase 2 Nara PDF QA tests.")


_TMP_DIR = Path(tempfile.mkdtemp(prefix="wisdom_nara_phase2_qa_"))

os.environ["SQLITE_PATH"] = str(_TMP_DIR / "test.db")
os.environ["STORAGE_ROOT"] = str(_TMP_DIR / "storage")
os.environ.setdefault("OCR_ENGINE", "noop")
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

from app import main as runtime  # noqa: E402
from app.core.text import basis_tokenize  # noqa: E402
from tests.nara_pdf_sample_cache import load_sample_manifest, sample_path  # noqa: E402


SAMPLE_DIR = Path(__file__).resolve().parent / "nara-phase2-basis-qa-samples"


def tearDownModule() -> None:
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


class NaraPhase2BasisQaSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest, cls.samples, cls.manifest_path = load_sample_manifest(
            "NARA_PHASE2_SAMPLE_MANIFEST",
            SAMPLE_DIR,
            min_samples=10,
            label="Phase 2 Nara PDF QA",
        )

    def setUp(self) -> None:
        runtime.app.config["TESTING"] = True
        self.client = runtime.app.test_client()
        runtime.init_db()

    def test_downloaded_samples_are_valid_phase2_qa_pdfs(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample.get("saved_path")):
                path = sample_path(sample)
                self.assertTrue(path.exists(), f"Missing sample file: {path}")
                self.assertGreater(path.stat().st_size, 1024)
                self.assertTrue(path.read_bytes().startswith(b"%PDF"))
                qa = sample.get("qa") or {}
                self.assertTrue(qa.get("passed"))
                self.assertGreaterEqual(qa.get("text_char_count", 0), 300)
                if "chunk_count" in qa:
                    self.assertGreaterEqual(qa.get("chunk_count", 0), 1)
                if "vector_count" in qa:
                    self.assertEqual(qa.get("chunk_count"), qa.get("vector_count"))
                if "search_result_count" in qa:
                    self.assertGreaterEqual(qa.get("search_result_count", 0), 1)

    def test_phase2_basis_pipeline_reprocesses_real_nara_notice_pdfs(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample.get("bid_ntce_no")):
                path = sample_path(sample)
                response = self.client.post(
                    "/api/basis-documents",
                    data={
                        "title": f"Phase 2 QA 재검증 {sample.get('sample_no')}",
                        "category": "nara_notice_pdf_qa_test",
                        "document_version": self.manifest.get("generated_at", "")[:10],
                        "issuing_agency": sample.get("ntce_instt_nm", ""),
                        "memo": "opt-in Phase 2 QA test sample",
                        "file": (io.BytesIO(path.read_bytes()), path.name),
                    },
                    content_type="multipart/form-data",
                )
                self.assertEqual(response.status_code, 201)
                payload = response.get_json()
                self.assertEqual(payload["processing_status"], "completed")
                self.assertEqual(payload["parse_status"], "completed")
                self.assertEqual(payload["index_status"], "completed")
                self.assertGreaterEqual(payload["chunk_count"], 1)
                self.assertEqual(payload["chunk_count"], payload["vector_count"])

                search_query = (sample.get("qa") or {}).get("search_query") or self._search_query_from_payload(payload)
                search_response = self.client.post(
                    "/api/basis-search",
                    json={"query": search_query, "category": "nara_notice_pdf_qa_test", "top_k": 3},
                )
                self.assertEqual(search_response.status_code, 200)
                search_payload = search_response.get_json()
                self.assertGreaterEqual(search_payload["result_count"], 1)
                serialized = json.dumps(search_payload, ensure_ascii=False).lower()
                self.assertNotIn("eligible", serialized)
                self.assertNotIn("not eligible", serialized)
                self.assertNotIn("지원 가능", serialized)
                self.assertNotIn("지원 불가능", serialized)

    def _search_query_from_payload(self, payload: dict) -> str:
        tokens = basis_tokenize(payload.get("extracted_text_preview", ""))
        selected = [token for token in tokens if len(token) >= 2 and not token.isdigit()][:5]
        return " ".join(selected) or payload.get("title") or "공고문"
