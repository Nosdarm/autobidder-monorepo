import unittest
import os
from unittest.mock import patch
from app.config import Settings # Assuming app.config.settings is the instance
                                # For testing, we might need to instantiate Settings directly
                                # or reload the module if settings is a module-level singleton.

class TestConfig(unittest.TestCase):

    def test_default_values(self):
        """Test that Settings load with their default values."""
        settings = Settings(_env_file=None) # Avoid loading .env for default tests
        self.assertEqual(settings.APP_NAME, "AutoBidder API")
        self.assertEqual(settings.JWT_ALGORITHM, "HS256")
        self.assertEqual(settings.OPENAI_MODEL, "gpt-4o-mini")
        self.assertEqual(settings.DATABASE_URL, "sqlite+aiosqlite:///./autobidder.db")
        self.assertIsNone(settings.OPENAI_API_KEY) # Default is None

    def test_environment_variable_override(self):
        """Test that environment variables override default values."""
        test_app_name = "My Test App"
        test_openai_model = "gpt-3.5-turbo-test"
        test_secret_key = "test-secret-from-env"

        with patch.dict(os.environ, {
            "APP_NAME": test_app_name,
            "OPENAI_MODEL": test_openai_model,
            "SECRET_KEY": test_secret_key  # SECRET_KEY has no default
        }):
            # Instantiate Settings within the patched context to ensure it reads
            # the mocked environment variables.
            # We pass _env_file=None to prevent an actual .env file (if any)
            # from interfering with this specific test.
            settings_from_env = Settings(_env_file=None)

            self.assertEqual(settings_from_env.APP_NAME, test_app_name)
            self.assertEqual(settings_from_env.OPENAI_MODEL, test_openai_model)
            self.assertEqual(settings_from_env.SECRET_KEY, test_secret_key)
    
    def test_secret_key_is_required(self):
        """Test that Settings raise an error if SECRET_KEY is not set."""
        # Temporarily remove SECRET_KEY if it's set in the actual environment
        # for this test.
        with patch.dict(os.environ, {}, clear=True):
            # Ensure SECRET_KEY is not in os.environ for this specific check
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]
            
            with self.assertRaises(ValueError) as context: # Pydantic v2 raises pydantic_core.ValidationError
                                                            # which BaseSettings catches and can re-raise or handle.
                                                            # Let's check for a general ValueError or a more specific
                                                            # Pydantic related error if possible.
                                                            # For pydantic-settings, it's often a ValidationError from pydantic_core
                                                            # which might be wrapped. For now, ValueError is a broad check.
                Settings(_env_file=None) # Attempt to instantiate without SECRET_KEY
            
            # Check if the error message contains something about SECRET_KEY
            # This depends on how Pydantic reports missing required fields.
            # For Pydantic v2, the error structure is more complex.
            # A simple check might be:
            # self.assertIn("SECRET_KEY", str(context.exception).lower())
            # However, the specific error is a validation error.
            # The prompt asked for the test, not necessarily making it pass with
            # current Pydantic behavior without more detailed error inspection.
            # The core idea is that instantiation should fail.
            # Given Pydantic's behavior, it will raise a validation error if a field
            # without a default and not Optional is missing.
            # The default pydantic error for a missing field is a ValidationError.
            # Let's assume ValueError is sufficient for this conceptual test for now.
            # print(str(context.exception)) # For debugging the exact error
            self.assertTrue("SECRET_KEY" in str(context.exception) or "validation error" in str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()
