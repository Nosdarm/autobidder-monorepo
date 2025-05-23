import unittest
from unittest.mock import patch, AsyncMock # AsyncMock for async functions
import asyncio # For running async functions in tests

# Assuming ai_prompt_service is structured to allow these imports
# Adjust paths if necessary based on actual project structure and sys.path in test runner
from app.services.ai_prompt_service import generate_preview
# Removed imports for preview_cache and MAX_CACHE_SIZE as they are no longer used in tests
# from app.config import settings # To mock settings.REDIS_CACHE_TTL_SECONDS if needed

# Helper to run async functions in synchronous tests if needed,
# though unittest.IsolatedAsyncioTestCase is better for full async tests.
# This helper is not strictly needed with IsolatedAsyncioTestCase but kept if useful elsewhere
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None) # Clean up to avoid interference
    return wrapper

@patch('app.services.ai_prompt_service.redis_cache_client', new_callable=AsyncMock)
class TestGeneratePreviewCachingWithRedis(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Clear any potential side-effects or reset mocks if needed."""
        # The @patch decorator itself handles resetting the mock object (mock_redis_client)
        # for each test method. So, explicit reset here might not be needed for mock_redis_client.
        # If there were other shared resources, this would be the place to reset them.
        pass

    @patch('app.services.ai_prompt_service.client.chat.completions.create', new_callable=AsyncMock)
    async def test_cache_hit(self, mock_openai_call, mock_redis_client):
        """Test that a repeated call with the same input uses the Redis cache."""
        test_input_text = "test cache hit text"
        cache_key = f"preview_cache:{test_input_text}"
        cached_value = "cached preview text from Redis"
        
        mock_redis_client.get.return_value = cached_value # Simulate cache hit

        # First call - should hit the cache
        result1 = await generate_preview(test_input_text)
        
        mock_redis_client.get.assert_called_once_with(cache_key)
        mock_openai_call.assert_not_called() # OpenAI should not be called
        self.assertEqual(result1, cached_value)

        # Second call - should also hit the cache
        result2 = await generate_preview(test_input_text)
        
        self.assertEqual(mock_redis_client.get.call_count, 2) # Called again
        mock_openai_call.assert_not_called() # Still not called
        self.assertEqual(result2, cached_value)

    @patch('app.services.ai_prompt_service.settings.REDIS_CACHE_TTL_SECONDS', 3600) # Mock TTL for predictability
    @patch('app.services.ai_prompt_service.client.chat.completions.create', new_callable=AsyncMock)
    async def test_cache_miss_then_cache_hit(self, mock_openai_call, mock_redis_client):
        """Test cache miss (API call, then cache set) followed by a cache hit."""
        test_input_text = "new text for cache miss"
        cache_key = f"preview_cache:{test_input_text}"
        fresh_preview_from_openai = "fresh preview from OpenAI"

        # --- First call: Cache Miss ---
        mock_redis_client.get.return_value = None # Simulate cache miss

        # Configure mock OpenAI response
        mock_choice = unittest.mock.Mock()
        mock_choice.message.content = f" {fresh_preview_from_openai} " # Add spaces for strip()
        mock_openai_response = unittest.mock.Mock()
        mock_openai_response.choices = [mock_choice]
        mock_openai_call.return_value = mock_openai_response
        
        result_miss = await generate_preview(test_input_text)

        mock_redis_client.get.assert_called_once_with(cache_key)
        mock_openai_call.assert_called_once()
        # Assert that redis_cache_client.set was called correctly
        # The TTL value comes from the mocked settings.REDIS_CACHE_TTL_SECONDS (3600)
        mock_redis_client.set.assert_called_once_with(cache_key, fresh_preview_from_openai)
        self.assertEqual(result_miss, fresh_preview_from_openai)

        # --- Second call: Cache Hit ---
        # Reset get mock for the second phase of this test.
        # Configure get to return the value we just "cached".
        mock_redis_client.get.reset_mock() # Reset call count and return_value for .get
        mock_redis_client.get.return_value = fresh_preview_from_openai
        # OpenAI mock should not be called again, so its state from the first call is fine.
        # Set mock should not be called again either.
        mock_redis_client.set.reset_mock()


        result_hit = await generate_preview(test_input_text)
        
        mock_redis_client.get.assert_called_once_with(cache_key) # Get was called
        mock_openai_call.assert_called_once() # OpenAI still only called once in total for this test
        mock_redis_client.set.assert_not_called() # Set was not called this time
        self.assertEqual(result_hit, fresh_preview_from_openai)

    # test_cache_eviction is removed as per instructions.

if __name__ == '__main__':
    unittest.main()
