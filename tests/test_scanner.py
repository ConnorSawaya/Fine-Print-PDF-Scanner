import os
import unittest
from unittest.mock import Mock, patch

import scanner


class PdfExtractionTests(unittest.TestCase):
    def test_rejects_oversized_upload_before_parsing(self):
        upload = Mock()
        upload.getvalue.return_value = b"x" * (scanner.MAX_PDF_BYTES + 1)
        with patch.object(scanner, "PdfReader") as reader:
            with self.assertRaisesRegex(scanner.PdfLimitError, "10 MB"):
                scanner.extract_pdf_text(upload)
            reader.assert_not_called()

    def test_rejects_invalid_pdf_with_safe_error(self):
        upload = Mock()
        upload.getvalue.return_value = b"not a pdf"
        with patch.object(scanner, "PdfReader", side_effect=RuntimeError("private parser detail")):
            with self.assertRaisesRegex(ValueError, "valid PDF") as raised:
                scanner.extract_pdf_text(upload)
        self.assertNotIn("private parser detail", str(raised.exception))

    def test_rejects_encrypted_pdf(self):
        reader = Mock()
        reader.is_encrypted = True
        with patch.object(scanner, "PdfReader", return_value=reader):
            with self.assertRaisesRegex(scanner.PdfLimitError, "Password-protected"):
                scanner.extract_pdf_text(Mock(getvalue=Mock(return_value=b"%PDF")))

    def test_rejects_too_many_pages(self):
        reader = Mock()
        reader.is_encrypted = False
        reader.pages = [object()] * (scanner.MAX_PDF_PAGES + 1)
        with patch.object(scanner, "PdfReader", return_value=reader):
            with self.assertRaisesRegex(scanner.PdfLimitError, "30 pages"):
                scanner.extract_pdf_text(Mock(getvalue=Mock(return_value=b"%PDF")))

    def test_rejects_extracted_text_over_limit(self):
        reader = Mock()
        reader.is_encrypted = False
        reader.pages = [Mock(extract_text=Mock(return_value="x" * 5))]
        with patch.object(scanner, "MAX_EXTRACTED_CHARS", 4), patch.object(
            scanner, "PdfReader", return_value=reader
        ):
            with self.assertRaisesRegex(scanner.PdfLimitError, "character limit"):
                scanner.extract_pdf_text(Mock(getvalue=Mock(return_value=b"%PDF")))


class ScanBudgetTests(unittest.TestCase):
    def setUp(self):
        with scanner._scan_times_lock:
            scanner._scan_times.clear()

    def tearDown(self):
        with scanner._scan_times_lock:
            scanner._scan_times.clear()

    def test_session_budget_is_three_scans_per_hour(self):
        session = {}
        for second in range(scanner.MAX_SCANS_PER_SESSION_PER_HOUR):
            self.assertTrue(scanner.reserve_scan(session, now=second))
        self.assertFalse(scanner.reserve_scan(session, now=4))
        self.assertTrue(
            scanner.reserve_scan(session, now=scanner.SCAN_WINDOW_SECONDS + 1)
        )

    def test_server_budget_is_shared_across_sessions(self):
        for second in range(scanner.MAX_SCANS_PER_HOUR):
            self.assertTrue(scanner.reserve_scan({"id": second}, now=second))
        self.assertFalse(scanner.reserve_scan({"id": "next"}, now=20))

    def test_missing_api_key_keeps_sample_mode_offline(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(scanner.get_client())

    def test_request_bounds_timeout_retries_and_output_tokens(self):
        client = Mock()
        client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="Review. Score: 55 /100"))
        ]
        self.assertEqual(scanner.analyze_text(client, "terms"), "Review. Score: 55 /100")
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], scanner.MAX_RESPONSE_TOKENS)
        self.assertIn("untrusted", kwargs["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
