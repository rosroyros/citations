import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

import app
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app.app)


@pytest.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app.app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestGeminiRoutingIntegration:
    """Integration tests for Gemini A/B routing and fallback mechanism."""

    @pytest.fixture
    def mock_openai_provider(self):
        """Mock OpenAI provider."""
        mock_provider = Mock(spec=OpenAIProvider)
        mock_provider.validate_citations = AsyncMock(return_value={
            "results": [{
                "citation_number": 1,
                "original": "Test citation",
                "source_type": "Test",
                "errors": []
            }]
        })
        return mock_provider

    @pytest.fixture
    def mock_gemini_provider(self):
        """Mock Gemini provider."""
        mock_provider = Mock(spec=GeminiProvider)
        mock_provider.validate_citations = AsyncMock(return_value={
            "results": [{
                "citation_number": 1,
                "original": "Test citation from Gemini",
                "source_type": "Test",
                "errors": []
            }]
        })
        return mock_provider

    @pytest.fixture
    def sample_citations(self):
        """Sample citation data."""
        return {
            "citations": ["Smith, J. (2020). Test citation. Publisher."]
        }

    async def test_model_b_routes_to_gemini_success(self, async_client, sample_citations,
                                                    mock_openai_provider, mock_gemini_provider):
        """Test that X-Model-Preference: model_b routes to Gemini successfully."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider_for_request') as mock_get_provider:

            # Mock get_provider to return Gemini for model_b
            mock_get_provider.return_value = (mock_gemini_provider, 'model_b', False)

            response = await async_client.post(
                "/api/validate/async",
                json=sample_citations,
                headers={"X-Model-Preference": "model_b"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

            # Verify Gemini was called (not OpenAI)
            mock_gemini_provider.validate_citations.assert_called_once()
            mock_openai_provider.validate_citations.assert_not_called()

    async def test_model_b_gemini_failure_fallback_to_openai(self, async_client, sample_citations,
                                                            mock_openai_provider, mock_gemini_provider):
        """Test that when Gemini fails with model_b, it falls back to OpenAI."""
        # Make Gemini fail
        mock_gemini_provider.validate_citations.side_effect = Exception("Gemini API error")

        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider') as mock_get_provider, \
             patch('app.log_event') as mock_log_event:

            # First call returns Gemini (which will fail), second returns OpenAI for fallback
            mock_get_provider.side_effect = [
                (mock_gemini_provider, 'model_b', False),
                (mock_openai_provider, 'model_a', True)  # fallback=True
            ]

            response = await async_client.post(
                "/api/validate/async",
                json=sample_citations,
                headers={"X-Model-Preference": "model_b"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

            # Verify fallback was logged
            mock_log_event.assert_called_with(
                "MODEL_FALLBACK",
                {
                    "requested_model": "model_b",
                    "fallback_model": "model_a",
                    "reason": "Gemini provider not available"
                }
            )

    async def test_model_a_forces_openai(self, async_client, sample_citations,
                                       mock_openai_provider, mock_gemini_provider):
        """Test that X-Model-Preference: model_a always uses OpenAI."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider_for_request') as mock_get_provider:

            # Mock get_provider to return OpenAI for model_a
            mock_get_provider.return_value = (mock_openai_provider, 'model_a', False)

            response = await async_client.post(
                "/api/validate/async",
                json=sample_citations,
                headers={"X-Model-Preference": "model_a"}
            )

            assert response.status_code == 200

            # Verify OpenAI was called
            mock_openai_provider.validate_citations.assert_called_once()
            mock_gemini_provider.validate_citations.assert_not_called()

    async def test_no_header_defaults_to_openai(self, async_client, sample_citations,
                                               mock_openai_provider, mock_gemini_provider):
        """Test that no X-Model-Preference header defaults to OpenAI."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider_for_request') as mock_get_provider:

            # Mock get_provider to return OpenAI by default
            mock_get_provider.return_value = (mock_openai_provider, 'model_a', False)

            response = await async_client.post(
                "/api/validate/async",
                json=sample_citations
            )

            assert response.status_code == 200

            # Verify OpenAI was called by default
            mock_openai_provider.validate_citations.assert_called_once()
            mock_gemini_provider.validate_citations.assert_not_called()

    async def test_job_polling_returns_model_info(self, async_client, sample_citations,
                                                 mock_openai_provider, mock_gemini_provider):
        """Test that job polling endpoint returns model information."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider') as mock_get_provider, \
             patch('app.jobs') as mock_jobs:

            # Setup mock job with model info
            job_id = "test-job-123"
            mock_jobs.__getitem__.return_value = {
                "status": "completed",
                "results": [{
                    "citation_number": 1,
                    "original": "Test citation",
                    "source_type": "Test",
                    "errors": []
                }],
                "model_preference": "model_b",
                "provider_used": "gemini",
                "fallback_occurred": False
            }

            response = await async_client.get(f"/api/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["model_preference"] == "model_b"
            assert data["provider_used"] == "gemini"
            assert data["fallback_occurred"] is False

    async def test_direct_validate_endpoint_model_routing(self, client, sample_citations,
                                                         mock_openai_provider, mock_gemini_provider):
        """Test model routing on direct /api/validate endpoint."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider') as mock_get_provider, \
             patch('app.log_event') as mock_log_event:

            # Mock for model_b request
            mock_get_provider.return_value = (mock_gemini_provider, 'model_b', False)

            response = client.post(
                "/api/validate",
                json=sample_citations,
                headers={"X-Model-Preference": "model_b"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "results" in data

            # Verify Gemini was called
            mock_gemini_provider.validate_citations.assert_called_once()

            # Verify provider info is logged
            mock_log_event.assert_called_with(
                "CITATION_VALIDATION",
                {
                    "citation_count": 1,
                    "provider": "model_b",
                    "is_fallback": False
                }
            )

    async def test_model_b_with_no_gemini_available(self, async_client, sample_citations,
                                                   mock_openai_provider):
        """Test model_b when Gemini provider is not available."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', None), \
             patch('app.get_provider') as mock_get_provider, \
             patch('app.log_event') as mock_log_event:

            # Should fall back to OpenAI when Gemini is None
            mock_get_provider.return_value = (mock_openai_provider, 'model_a', True)

            response = await async_client.post(
                "/api/validate/async",
                json=sample_citations,
                headers={"X-Model-Preference": "model_b"}
            )

            assert response.status_code == 200

            # Verify fallback was logged
            mock_log_event.assert_any_call(
                "MODEL_FALLBACK",
                {
                    "requested_model": "model_b",
                    "fallback_model": "model_a",
                    "reason": "Gemini provider not available"
                }
            )

    def test_get_provider_for_request_function_model_selection(self):
        """Test the get_provider function directly."""
        # Mock Request object with headers
        mock_request = Mock()
        mock_request.headers = {"X-Model-Preference": "model_b"}

        with patch('app.openai_provider') as mock_openai, \
             patch('app.gemini_provider') as mock_gemini:

            # Test model_b with available Gemini
            provider, model_id, fallback = app.get_provider_for_request(mock_request)
            assert model_id == 'model_b'
            assert fallback is False

            # Test model_a forces OpenAI
            mock_request.headers = {"X-Model-Preference": "model_a"}
            provider, model_id, fallback = app.get_provider_for_request(mock_request)
            assert model_id == 'model_a'
            assert fallback is False

            # Test no header defaults to model_a
            mock_request.headers = {}
            provider, model_id, fallback = app.get_provider_for_request(mock_request)
            assert model_id == 'model_a'
            assert fallback is False

    async def test_multiple_concurrent_requests_model_routing(self, async_client, sample_citations,
                                                             mock_openai_provider, mock_gemini_provider):
        """Test concurrent requests with different model preferences."""
        with patch('app.openai_provider', mock_openai_provider), \
             patch('app.gemini_provider', mock_gemini_provider), \
             patch('app.get_provider_for_request') as mock_get_provider:

            # Track which provider gets called
            gemini_calls = []
            openai_calls = []

            async def track_gemini(*args, **kwargs):
                gemini_calls.append(True)
                return {"results": []}

            async def track_openai(*args, **kwargs):
                openai_calls.append(True)
                return {"results": []}

            mock_gemini_provider.validate_citations = track_gemini
            mock_openai_provider.validate_citations = track_openai

            # Create tasks for concurrent requests
            tasks = [
                async_client.post(
                    "/api/validate/async",
                    json=sample_citations,
                    headers={"X-Model-Preference": "model_b"}
                ),
                async_client.post(
                    "/api/validate/async",
                    json=sample_citations,
                    headers={"X-Model-Preference": "model_a"}
                ),
                async_client.post(
                    "/api/validate/async",
                    json=sample_citations
                )
            ]

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200

            # Verify routing worked correctly
            assert len(gemini_calls) == 1  # One model_b request
            assert len(openai_calls) == 2  # One model_a and one default