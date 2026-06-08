import socket
import unittest
from unittest.mock import patch

from app.services.nara_api import validate_external_attachment_url


class NaraAttachmentUrlSafetyTests(unittest.TestCase):
    def test_rejects_literal_non_external_addresses(self) -> None:
        cases = [
            ("file:///C:/secret.pdf", "only HTTP/HTTPS URLs are allowed"),
            ("http://localhost/private.pdf", "localhost is not allowed"),
            ("http://127.0.0.1/private.pdf", "loopback address is not allowed"),
            ("http://10.0.0.5/private.pdf", "private network address is not allowed"),
            ("http://169.254.10.10/private.pdf", "link-local address is not allowed"),
            ("http://100.64.0.10/private.pdf", "non-global address is not allowed"),
            ("http://[fc00::1]/private.pdf", "private network address is not allowed"),
        ]

        for url, expected_reason in cases:
            with self.subTest(url=url):
                safe, reason = validate_external_attachment_url(url)

                self.assertFalse(safe)
                self.assertIn(expected_reason, reason)

    def test_rejects_hostname_when_dns_resolves_to_non_global_address(self) -> None:
        fake_infos = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("100.64.0.20", 0))]

        with patch("app.services.nara_api.socket.getaddrinfo", return_value=fake_infos):
            safe, reason = validate_external_attachment_url("https://download.example.test/notice.pdf")

        self.assertFalse(safe)
        self.assertIn("non-global address is not allowed", reason)

    def test_accepts_hostname_when_dns_resolves_to_public_address(self) -> None:
        fake_infos = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 0))]

        with patch("app.services.nara_api.socket.getaddrinfo", return_value=fake_infos):
            safe, reason = validate_external_attachment_url("https://download.example.test/notice.pdf")

        self.assertTrue(safe)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
