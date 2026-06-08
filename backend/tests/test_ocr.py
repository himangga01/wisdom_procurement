import os
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import fitz

from app.pipelines.corporation_evidence import analyze_corporation_evidence
from app.pipelines import ocr


TEST_TMP_ROOT = Path(__file__).resolve().parents[2] / "temp" / "ocr-tests"
TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


@contextmanager
def test_temp_dir():
    path = TEST_TMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class FakeOcrEngine(ocr.OcrEngine):
    name = "fake"

    def __init__(self, language: str = "kor+eng") -> None:
        super().__init__(language)
        self.seen_images: list[Path] = []

    def is_available(self) -> bool:
        return True

    def recognize_image(self, image_path: Path, page_number: int | None = None) -> ocr.OcrResult:
        self.seen_images.append(image_path)
        page = ocr.OcrPageResult(
            page_number=page_number,
            text="business registration 142-81-28387",
            confidence=0.91,
        )
        return ocr.OcrResult(
            text=page.text,
            status=ocr.OCR_STATUS_COMPLETED,
            engine=self.name,
            language=self.language,
            page_count=1,
            pages=[page],
            average_confidence=0.91,
        )


class OcrPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_get_ocr_engine = ocr.get_ocr_engine
        self._old_env = {key: os.environ.get(key) for key in ("OCR_ENGINE", "OCR_LANG", "OCR_MIN_TEXT_LENGTH")}

    def tearDown(self) -> None:
        ocr.get_ocr_engine = self._old_get_ocr_engine
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_text_above_threshold_skips_ocr(self) -> None:
        text = "A" * 120

        result = ocr.run_ocr_if_needed(text, None, "pdf", {})

        self.assertEqual(result.status, ocr.OCR_STATUS_SKIPPED)
        self.assertEqual(result.text, text)

    def test_force_ocr_runs_even_when_text_is_above_threshold(self) -> None:
        fake_engine = FakeOcrEngine()
        ocr.get_ocr_engine = lambda: fake_engine

        with test_temp_dir() as tmp:
            image_path = tmp / "basis-page.png"
            image_path.write_bytes(b"fake-image")

            result = ocr.run_ocr_if_needed("A" * 120, image_path, "image", {}, force=True)

        self.assertEqual(result.status, ocr.OCR_STATUS_COMPLETED)
        self.assertEqual(result.engine, "fake")
        self.assertIn("142-81-28387", result.text)
        self.assertEqual(len(fake_engine.seen_images), 1)

    def test_missing_ocr_engine_returns_setup_status(self) -> None:
        os.environ["OCR_ENGINE"] = "noop"

        with test_temp_dir() as tmp:
            image_path = tmp / "sample.png"
            image_path.write_bytes(b"fake-image")

            result = ocr.run_ocr(image_path)

        self.assertEqual(result.status, ocr.OCR_STATUS_NEEDS_SETUP)
        self.assertEqual(result.engine, "noop")
        self.assertIn("not available", result.warnings[0])

    def test_image_ocr_uses_selected_engine(self) -> None:
        fake_engine = FakeOcrEngine()
        ocr.get_ocr_engine = lambda: fake_engine

        with test_temp_dir() as tmp:
            image_path = tmp / "business_registration.png"
            image_path.write_bytes(b"fake-image")

            result = ocr.run_ocr(image_path)

        self.assertEqual(result.status, ocr.OCR_STATUS_COMPLETED)
        self.assertEqual(result.engine, "fake")
        self.assertIn("142-81-28387", result.text)
        self.assertEqual(len(fake_engine.seen_images), 1)

    def test_pdf_ocr_renders_pages_for_engine(self) -> None:
        fake_engine = FakeOcrEngine()
        ocr.get_ocr_engine = lambda: fake_engine

        with test_temp_dir() as tmp:
            pdf_path = tmp / "scan.pdf"
            doc = fitz.open()
            doc.new_page(width=300, height=200)
            doc.save(pdf_path)
            doc.close()

            result = ocr.run_ocr(pdf_path)

        self.assertEqual(result.status, ocr.OCR_STATUS_COMPLETED)
        self.assertEqual(result.page_count, 1)
        self.assertIn("142-81-28387", result.text)
        self.assertEqual(fake_engine.seen_images[0].suffix, ".png")

    def test_business_registration_sample_image_with_real_engine_when_enabled(self) -> None:
        if os.getenv("RUN_REAL_OCR_TESTS") != "1":
            self.skipTest("Set RUN_REAL_OCR_TESTS=1 to run real OCR sample tests.")

        sample_path = os.getenv("OCR_SAMPLE_IMAGE_PATH", "")
        if not sample_path:
            self.skipTest("Set OCR_SAMPLE_IMAGE_PATH to the business registration image.")

        path = Path(sample_path)
        if not path.exists():
            self.skipTest(f"OCR sample image not found: {path}")

        result = ocr.run_ocr(path)
        if result.status in {ocr.OCR_STATUS_NEEDS_SETUP, ocr.OCR_STATUS_UNAVAILABLE}:
            self.skipTest(f"OCR engine unavailable: {result.error_message}")

        normalized = result.text.replace(" ", "")
        self.assertEqual(result.status, ocr.OCR_STATUS_COMPLETED)
        self.assertTrue(
            any(token in normalized for token in ("사업자등록", "142-81-28387", "온세이엔씨")),
            result.text,
        )
        analysis = analyze_corporation_evidence(result.text, path.name)
        fields = {candidate.field_key: candidate.extracted_value for candidate in analysis.candidates}
        self.assertEqual(analysis.document_type, "business_registration_certificate")
        self.assertIn("건설업", fields["business_type"])
        self.assertIn("도매 및 소매업", fields["business_type"])
        self.assertIn("신재생에너지설비설치전문기업", fields["business_item"])
        self.assertIn("컴퓨터 관련 주변기기", fields["business_item"])


if __name__ == "__main__":
    unittest.main()
