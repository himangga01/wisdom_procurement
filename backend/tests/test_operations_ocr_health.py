import os
import unittest
from unittest.mock import patch

from app.services import operations


class OperationsOcrHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = {key: os.environ.get(key) for key in ("OCR_ENGINE", "OCR_LANG", "OCR_LANGUAGES")}

    def tearDown(self) -> None:
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_ocr_health_defaults_to_paddle_when_engine_is_not_explicitly_set(self) -> None:
        os.environ.pop("OCR_ENGINE", None)
        os.environ["OCR_LANGUAGES"] = "kor+eng"

        with patch.object(operations.importlib.util, "find_spec", return_value=object()):
            payload = operations._ocr_health()

        self.assertEqual(payload["status"], "configured")
        self.assertEqual(payload["engine"], "paddle")
        self.assertEqual(payload["language"], "kor+eng")

    def test_ocr_health_reports_noop_as_explicitly_unavailable(self) -> None:
        os.environ["OCR_ENGINE"] = "noop"

        payload = operations._ocr_health()

        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["engine"], "noop")

    def test_ocr_health_reports_missing_paddle_dependency(self) -> None:
        os.environ["OCR_ENGINE"] = "paddle"

        def fake_find_spec(module_name: str):
            return None if module_name == "paddleocr" else object()

        with patch.object(operations.importlib.util, "find_spec", side_effect=fake_find_spec):
            payload = operations._ocr_health()

        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["engine"], "paddle")
        self.assertIn("paddleocr", payload["missing_packages"])


if __name__ == "__main__":
    unittest.main()
