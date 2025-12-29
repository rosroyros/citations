import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import logging
import re
from pathlib import Path
import asyncio
from openai import APITimeoutError, RateLimitError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from providers.openai_provider import OpenAIProvider

class TestOpenAITimeoutInstrumentation(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("openai_provider")
        self.logger.setLevel(logging.INFO)
        self.log_capture = []
        
        # Capture logs
        class ListHandler(logging.Handler):
            def __init__(self, log_list):
                super().__init__()
                self.log_list = log_list
            def emit(self, record):
                self.log_list.append(self.format(record))
        
        self.handler = ListHandler(self.log_capture)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    @patch('providers.openai_provider.AsyncOpenAI')
    def test_instrumentation_logging_success(self, mock_openai_class):
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock successful response (V2 API structure)
        mock_response = MagicMock()
        # Mock usage (checked via hasattr in code)
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_response.usage.total_tokens = 20
        mock_response.output_text = "CITATION #1\n═══\nORIGINAL: Test\nSOURCE TYPE: Book\nVALIDATION RESULTS:\n✓ No APA 7 formatting errors detected"
        
        # Mock responses.create (V2 API)
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(api_key="test-key")
        
        # Run validation
        asyncio.run(provider.validate_citations("Test citation"))
        
        # Check logs
        logs = "\n".join(self.log_capture)
        
        # Verify attempt start log
        attempt_match = re.search(r'Attempt 1/3: Calling OpenAI \(timeout=([\d.]+)s, model=([^,]+), size=(\d+) chars\)', logs)
        self.assertIsNotNone(attempt_match)
        self.assertEqual(float(attempt_match.group(1)), 85.0)
        self.assertEqual(attempt_match.group(2), "gpt-5-mini")
        self.assertTrue(int(attempt_match.group(3)) > 0)

        # Verify success duration log
        duration_match = re.search(r'Attempt 1/3: Success in ([\d.]+)s', logs)
        self.assertIsNotNone(duration_match)

    @patch('providers.openai_provider.AsyncOpenAI')
    def test_instrumentation_logging_timeout(self, mock_openai_class):
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock timeout error
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(side_effect=APITimeoutError(request=MagicMock()))

        provider = OpenAIProvider(api_key="test-key")
        
        # Run validation (expect failure after retries)
        with self.assertRaises(ValueError):
            asyncio.run(provider.validate_citations("Test citation"))
            
        # Check logs
        logs = "\n".join(self.log_capture)
        
        # Verify timeout specific log
        timeout_match = re.search(r'Attempt 1/3: Failed with timeout after ([\d.]+)s \(Configured timeout: ([\d.]+)s\)', logs)
        self.assertIsNotNone(timeout_match, "Timeout log message not found")
        self.assertEqual(float(timeout_match.group(2)), 85.0)
        
        # Verify retries occurred
        self.assertIn("Attempt 2/3", logs)
        self.assertIn("Attempt 3/3", logs)

    @patch('providers.openai_provider.AsyncOpenAI')
    def test_instrumentation_logging_rate_limit(self, mock_openai_class):
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock rate limit error
        mock_client.responses = MagicMock()
        mock_client.responses.create = AsyncMock(side_effect=RateLimitError(message="Rate limited", response=MagicMock(), body={}))

        provider = OpenAIProvider(api_key="test-key")
        
        # Run validation (expect failure after retries)
        with self.assertRaises(ValueError):
            asyncio.run(provider.validate_citations("Test citation"))
            
        # Check logs
        logs = "\n".join(self.log_capture)
        
        # Verify rate limit specific log
        rate_limit_match = re.search(r'Attempt 1/3: Failed with rate_limit after ([\d.]+)s \(Configured timeout: ([\d.]+)s\)', logs)
        self.assertIsNotNone(rate_limit_match, "Rate limit log message not found")
if __name__ == '__main__':
    unittest.main()

