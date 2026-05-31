import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


if os.getenv("RUN_NARA_PHASE17_QA") != "1":
    raise unittest.SkipTest("Set RUN_NARA_PHASE17_QA=1 after downloading samples to run Phase 1.7 Nara PDF QA tests.")


_TMP_DIR = Path(tempfile.mkdtemp(prefix="wisdom_nara_phase17_qa_"))

os.environ["SQLITE_PATH"] = str(_TMP_DIR / "test.db")
os.environ["STORAGE_ROOT"] = str(_TMP_DIR / "storage")
os.environ.setdefault("OCR_ENGINE", "noop")
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

from app import main as runtime  # noqa: E402
from app.pipelines.parser import extract_document  # noqa: E402
from tests.nara_pdf_sample_cache import load_sample_manifest, sample_path  # noqa: E402


SAMPLE_DIR = Path(__file__).resolve().parent / "nara-pdf-samples"


def tearDownModule() -> None:
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


class NaraPhase17LiveSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest, cls.samples, cls.manifest_path = load_sample_manifest(
            "NARA_PHASE17_SAMPLE_MANIFEST",
            SAMPLE_DIR,
            min_samples=5,
            label="Phase 1.7 Nara PDF QA",
        )

    def test_downloaded_samples_are_valid_pdfs(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample.get("saved_path")):
                path = sample_path(sample)
                self.assertTrue(path.exists(), f"Missing sample file: {path}")
                self.assertGreater(path.stat().st_size, 1024)
                self.assertTrue(path.read_bytes().startswith(b"%PDF"))

    def test_phase17_requirement_extraction_from_real_notice_pdfs(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample.get("bid_ntce_no")):
                path = sample_path(sample)
                parsed = extract_document(path)
                self.assertEqual(parsed.kind, "pdf")
                self.assertGreaterEqual(len(parsed.text.strip()), 400)

                notice = {
                    "bid_ntce_nm": sample.get("bid_ntce_nm", ""),
                    "bid_ntce_no": sample.get("bid_ntce_no", ""),
                    "bid_ntce_ord": sample.get("bid_ntce_ord", ""),
                    "ntce_instt_nm": sample.get("ntce_instt_nm", ""),
                    "dminstt_nm": sample.get("dminstt_nm", ""),
                    "bid_ntce_dt": sample.get("bid_ntce_dt", ""),
                    "bid_clse_dt": sample.get("bid_clse_dt", ""),
                }
                notice_text = runtime.build_nara_summary_text(notice, [parsed.text])
                requirements = runtime.extract_notice_requirements(notice, notice_text)
                candidates = runtime.build_notice_requirement_candidates(requirements)
                candidate_types = {candidate["requirement_type"] for candidate in candidates}
                semantic_types = {"region", "license", "company_type", "required_document", "requirement_line"}

                self.assertGreaterEqual(len(candidates), 3)
                self.assertTrue(candidate_types & semantic_types)
                serialized = json.dumps({"requirements": requirements, "candidates": candidates}, ensure_ascii=False).lower()
                self.assertNotIn("eligible", serialized)
                self.assertNotIn("not eligible", serialized)
                self.assertNotIn("지원 가능", serialized)
                self.assertNotIn("지원 불가능", serialized)

    def test_manifest_qa_results_are_passing(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample.get("bid_ntce_no")):
                qa = sample.get("qa") or {}
                self.assertTrue(qa.get("passed"))
                self.assertGreaterEqual(qa.get("text_char_count", 0), 400)
                if "candidate_count" in qa:
                    self.assertGreaterEqual(qa.get("candidate_count", 0), 3)
                if "semantic_candidate_count" in qa:
                    self.assertGreaterEqual(qa.get("semantic_candidate_count", 0), 1)
                self.assertEqual(qa.get("forbidden_terms_found") or [], [])
