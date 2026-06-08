import json
import logging
import tempfile
import unittest
from pathlib import Path

from app.core.logging import (
    configure_backend_logging,
    get_logger,
    log_event,
    log_exception,
    sanitize_log_context,
    sanitize_log_value,
)


class BackendLoggingTests(unittest.TestCase):
    def tearDown(self) -> None:
        root_logger = logging.getLogger("wisdom_procurement")
        for handler in list(root_logger.handlers):
            handler.close()
        root_logger.handlers.clear()

    def test_sanitize_log_context_masks_secrets_and_identifiers(self) -> None:
        payload = sanitize_log_context(
            {
                "url": "https://example.test/file.pdf?serviceKey=RAW_SECRET&keyword=forest",
                "authorization": "Bearer RAW_TOKEN",
                "nested": {
                    "gemini_api_key": "RAW_GEMINI_KEY",
                    "business_registration_number": "142-81-28387",
                    "memo": "customer 900101-1234567",
                },
            }
        )

        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("RAW_SECRET", serialized)
        self.assertNotIn("RAW_TOKEN", serialized)
        self.assertNotIn("RAW_GEMINI_KEY", serialized)
        self.assertNotIn("142-81-28387", serialized)
        self.assertNotIn("900101-1234567", serialized)
        self.assertIn("keyword=forest", payload["url"])
        self.assertIn("142-**-*****", serialized)
        self.assertIn("[REDACTED_RRN]", serialized)

    def test_sanitize_log_value_masks_secret_inside_plain_message(self) -> None:
        message = sanitize_log_value("Authorization: Bearer SHOULD_NOT_LEAK for 142-81-28387")

        self.assertNotIn("SHOULD_NOT_LEAK", message)
        self.assertNotIn("142-81-28387", message)
        self.assertIn("Bearer [REDACTED]", message)
        self.assertIn("142-**-*****", message)

    def test_jsonl_logging_writes_info_and_error_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wisdom_log_test_") as tmp:
            log_dir = configure_backend_logging(Path(tmp), level="INFO", max_mb=1, backups=0)
            logger = get_logger("tests.backend_logging")

            log_event(
                logger,
                "logging.test.info",
                url="https://example.test?token=RAW_TOKEN&item=ok",
                request_id="req-123",
            )
            try:
                raise RuntimeError("failed with Authorization: Bearer RAW_SECRET")
            except RuntimeError as exc:
                log_exception(logger, "logging.test.error", exc, api_key="RAW_API_KEY", request_id="req-123")

            for handler in logging.getLogger("wisdom_procurement").handlers:
                handler.flush()

            backend_log = log_dir / "backend.log"
            error_log = log_dir / "backend-error.log"
            self.assertTrue(backend_log.exists())
            self.assertTrue(error_log.exists())

            backend_lines = [json.loads(line) for line in backend_log.read_text(encoding="utf-8").splitlines()]
            error_lines = [json.loads(line) for line in error_log.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(backend_lines[0]["event"], "logging.test.info")
            self.assertEqual(backend_lines[0]["request_id"], "req-123")
            self.assertIn("token=%5BREDACTED%5D", backend_lines[0]["url"])
            self.assertEqual(error_lines[0]["event"], "logging.test.error")
            self.assertEqual(error_lines[0]["api_key"], "[REDACTED]")
            serialized = json.dumps(backend_lines + error_lines, ensure_ascii=False)
            self.assertNotIn("RAW_TOKEN", serialized)
            self.assertNotIn("RAW_API_KEY", serialized)
            self.assertNotIn("RAW_SECRET", serialized)


if __name__ == "__main__":
    unittest.main()
