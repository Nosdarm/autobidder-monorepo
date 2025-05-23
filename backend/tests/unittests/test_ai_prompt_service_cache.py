import unittest
from unittest.mock import patch, AsyncMock # AsyncMock for async functions
import asyncio # For running async functions in tests

# Assuming ai_prompt_service is structured to allow these imports
# Adjust paths if necessary based on actual project structure and sys.path in test runner
from app.services.ai_prompt_service import (
    generate_preview,
    preview_cache,
    MAX_CACHE_SIZE
)

# Helper to run async functions in synchronous tests if needed,
# though unittest.IsolatedAsyncioTestCase is better for full async tests.
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

class TestGeneratePreviewCaching(unittest.IsolatedAsyncioTestCase): # Changed to IsolatedAsyncioTestCase

    def setUp(self):
        """Clear the cache before each test."""
        preview_cache.clear()

    @patch('app.services.ai_prompt_service.client.chat.completions.create', new_callable=AsyncMock)
    async def test_cache_hit(self, mock_openai_create):
        """Test that a repeated call with the same input uses the cache."""
        # Configure the mock response
        mock_choice = unittest.mock.Mock()
        mock_choice.message.content = " Mocked preview text "
        mock_response = unittest.mock.Mock()
        mock_response.choices = [mock_choice]
        mock_openai_create.return_value = mock_response

        # First call - should call OpenAI API
        result1 = await generate_preview("test text")
        mock_openai_create.assert_called_once()
        self.assertEqual(result1, "Mocked preview text")

        # Second call with the same input - should use cache
        result2 = await generate_preview("test text")
        mock_openai_create.assert_called_once()  # Still called only once
        self.assertEqual(result2, "Mocked preview text")
        self.assertEqual(result1, result2)
        self.assertIn("test text", preview_cache)

    @patch('app.services.ai_prompt_service.client.chat.completions.create', new_callable=AsyncMock)
    async def test_cache_miss(self, mock_openai_create):
        """Test that different inputs result in separate API calls."""
        mock_choice1 = unittest.mock.Mock()
        mock_choice1.message.content = " Preview for text 1 "
        mock_response1 = unittest.mock.Mock()
        mock_response1.choices = [mock_choice1]

        mock_choice2 = unittest.mock.Mock()
        mock_choice2.message.content = " Preview for text 2 "
        mock_response2 = unittest.mock.Mock()
        mock_response2.choices = [mock_choice2]
        
        # Configure the mock to return different values for different calls if needed,
        # or just track calls. Here, we'll make it return sequentially.
        mock_openai_create.side_effect = [mock_response1, mock_response2]

        # First call
        result1 = await generate_preview("test text 1")
        self.assertEqual(mock_openai_create.call_count, 1)
        self.assertEqual(result1, "Preview for text 1")
        self.assertIn("test text 1", preview_cache)
        self.assertNotIn("test text 2", preview_cache)

        # Second call with different input
        result2 = await generate_preview("test text 2")
        self.assertEqual(mock_openai_create.call_count, 2)
        self.assertEqual(result2, "Preview for text 2")
        self.assertIn("test text 2", preview_cache)
        
    @patch('app.services.ai_prompt_service.client.chat.completions.create', new_callable=AsyncMock)
    async def test_cache_eviction(self, mock_openai_create):
        """Test that the cache evicts items when MAX_CACHE_SIZE is reached."""
        # Configure a generic mock response
        mock_choice = unittest.mock.Mock()
        mock_choice.message.content = "Generic preview "
        mock_response = unittest.mock.Mock()
        mock_response.choices = [mock_choice]
        mock_openai_create.return_value = mock_response

        # Fill the cache up to MAX_CACHE_SIZE - 1
        for i in range(MAX_CACHE_SIZE -1):
            await generate_preview(f"text {i}")
        
        self.assertEqual(len(preview_cache), MAX_CACHE_SIZE - 1)
        mock_openai_create.reset_mock() # Reset call count before critical part

        # Add one more item to fill the cache exactly to MAX_CACHE_SIZE
        await generate_preview(f"text {MAX_CACHE_SIZE -1}")
        self.assertEqual(len(preview_cache), MAX_CACHE_SIZE)
        self.assertEqual(mock_openai_create.call_count, 1) # Called for the new item

        # Add one more item, which should trigger cache clearing and then add this new item
        first_evicted_key = "text 0" # This key should be gone after eviction
        new_key = f"text {MAX_CACHE_SIZE}"
        
        await generate_preview(new_key)
        
        # After eviction (clear()) and adding the new item, cache size should be 1
        self.assertEqual(len(preview_cache), 1)
        self.assertIn(new_key, preview_cache) # The newest item should be in cache
        self.assertNotIn(first_evicted_key, preview_cache) # An old item should be gone
        self.assertEqual(mock_openai_create.call_count, 2) # Called for the item that triggered eviction


if __name__ == '__main__':
    unittest.main()
