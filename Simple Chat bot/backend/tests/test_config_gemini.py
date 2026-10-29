import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from config import _load_dotenv, get_settings
from services.llm_service import LLMError, _raise_for_status


class GeminiConfigurationTest(unittest.TestCase):
    def test_dotenv_comments_and_quotes(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / ".env"
            path.write_text('GEMINI_API_KEY= # empty key\nGROQ_API_KEY="test-value#literal" # note\nDEFAULT_PROVIDER=gemini # note\n', encoding="utf-8")
            _load_dotenv(path)
            self.assertEqual(os.environ["GEMINI_API_KEY"], "")
            self.assertEqual(os.environ["GROQ_API_KEY"], "test-value#literal")
            self.assertEqual(os.environ["DEFAULT_PROVIDER"], "gemini")

    def test_google_api_key_alias(self):
        get_settings.cache_clear()
        try:
            with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "  test-value  "}, clear=True), patch("config._load_dotenv"):
                self.assertEqual(get_settings().gemini_api_key, "test-value")
        finally:
            get_settings.cache_clear()

    def test_gemini_failure_types_and_no_raw_details(self):
        for status, message, expected in [
            (400, "API key not valid. test-secret-value", "bad_key"),
            (403, "Project access is restricted test-secret-value", "permission_denied"),
            (402, "Payment required test-secret-value", "billing_required"),
            (429, "Quota exceeded test-secret-value", "rate_limited"),
            (400, "Unsupported temperature test-secret-value", "bad_model"),
        ]:
            with self.subTest(status=status, expected=expected):
                response = Mock(ok=False, status_code=status)
                response.json.return_value = {"error": {"message": message}}
                with self.assertRaises(LLMError) as raised:
                    _raise_for_status(response, "Gemini")
                self.assertEqual(raised.exception.code, expected)
                self.assertNotIn("test-secret-value", str(raised.exception))
