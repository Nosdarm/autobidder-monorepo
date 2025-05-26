import asyncio
import unittest
import time # For time.sleep in synchronous tests
from fastapi.testclient import TestClient
from app.main import app # Your FastAPI app instance
# It's important that app.state.limiter is initialized when app is imported.

class TestAIPromptsRateLimiting(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Note: slowapi's get_remote_address will likely see all TestClient
        # requests as coming from "127.0.0.1". This is usually fine for testing
        # the basic rate limiting logic for a single "client".

    def test_rate_limit_exceeded(self):
        """Test that exceeding the rate limit returns a 429 error."""
        # The rate limit is "5/minute"
        # Endpoint is POST /ai/prompts/preview
        # Body: {"prompt_id": "test_id", "description": "test description"}
        
        endpoint_url = "/ai/prompts/preview"
        payload = {"prompt_id": "test-prompt", "description": "Some text for preview"}
        
        # Make 5 successful requests
        for i in range(5):
            response = self.client.post(endpoint_url, json=payload)
            self.assertEqual(response.status_code, 200, f"Request {i+1} failed, expected 200")

        # The 6th request should be rate-limited
        response = self.client.post(endpoint_url, json=payload)
        self.assertEqual(response.status_code, 429, "Expected 429 status code for 6th request")

    def test_rate_limit_reset_after_cooldown(self):
        """Test that the rate limit resets after the cooldown period."""
        endpoint_url = "/ai/prompts/preview"
        payload = {"prompt_id": "test-prompt-cooldown", "description": "Cooldown test"}
        rate_limit_count = 5  # e.g., "5/minute"
        cooldown_period = 60  # seconds for a "per minute" limit

        # Exceed the limit
        for i in range(rate_limit_count):
            response = self.client.post(endpoint_url, json=payload)
            self.assertEqual(response.status_code, 200, f"Initial request {i+1} failed")
        
        response = self.client.post(endpoint_url, json=payload)
        self.assertEqual(response.status_code, 429, "Rate limit was not triggered as expected")

        # Wait for the cooldown period
        print(f"\nWaiting for {cooldown_period} seconds for rate limit to reset...")
        time.sleep(cooldown_period)
        print("Wait finished. Attempting request again.")

        # Make another request, it should now be successful
        response_after_cooldown = self.client.post(endpoint_url, json=payload)
        self.assertEqual(response_after_cooldown.status_code, 200, 
                         "Request after cooldown failed, expected 200")


if __name__ == '__main__':
    unittest.main()
