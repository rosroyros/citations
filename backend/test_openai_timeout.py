import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import logging
from pathlib import Path
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

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
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 20
        mock_response.choices = [MagicMock(message=MagicMock(content="CITATION #1\n═══\nORIGINAL: Test\nSOURCE TYPE: Book\nVALIDATION RESULTS:\n✓ No APA 7 formatting errors detected"))]
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(api_key="test-key")
        
        # Run validation
        asyncio.run(provider.validate_citations("Test citation"))
        
        # Check logs
        logs = "\n".join(self.log_capture)
        
        self.assertIn("Calling OpenAI (timeout=85.0s", logs)
        self.assertIn("size=", logs)
        self.assertIn("Success in", logs)

    @patch('providers.openai_provider.AsyncOpenAI')
    def test_instrumentation_logging_timeout(self, mock_openai_class):
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        from openai import APITimeoutError
        
        # Mock timeout error
        # APITimeoutError signature in this version is (request: httpx.Request)
        mock_client.chat.completions.create = AsyncMock(side_effect=APITimeoutError(request=MagicMock()))

        provider = OpenAIProvider(api_key="test-key")
        
        # Run validation (expect failure after retries)
        with self.assertRaises(ValueError):
            asyncio.run(provider.validate_citations("Test citation"))
            
        # Check logs
        logs = "\n".join(self.log_capture)
        
        self.assertIn("Calling OpenAI (timeout=85.0s", logs)
        self.assertIn("Failed with timeout after", logs)
        self.assertIn("(Configured timeout: 85.0s)", logs)

if __name__ == '__main__':
    unittest.main()
