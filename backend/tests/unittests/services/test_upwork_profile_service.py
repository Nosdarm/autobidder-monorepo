import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import os

from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import Playwright # Added for type hinting

# Adjust path as necessary if service moves or for test structure
from app.services.upwork_profile_service import fetch_and_update_upwork_profile, USER_DATA_DIR, UpworkProfileFetcher
from app.models.profile import Profile # For creating mock profile objects if needed for DB checks

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    # Mock execute, scalars, first for typical query patterns
    mock_execute_result = AsyncMock()
    mock_scalars_result = AsyncMock()
    mock_scalars_result.first.return_value = None # Default to not found for queries

    mock_execute_result.scalars.return_value = mock_scalars_result
    session.execute.return_value = mock_execute_result
    return session

async def test_fetch_profile_dir_not_found(mock_db_session: AsyncSession):
    profile_id = "non_existent_profile"

    with patch("os.path.exists", return_value=False) as mock_os_exists:
        result = await fetch_and_update_upwork_profile(profile_id, mock_db_session)

        mock_os_exists.assert_called_once_with(os.path.join(USER_DATA_DIR, profile_id))
        assert result == {"status": "error", "message": "Profile directory not found. Please ensure session is saved."}

async def test_fetch_browser_launch_failure(mock_db_session: AsyncSession):
    profile_id = "test_profile_launch_fail"

    with patch("os.path.exists", return_value=True): # Profile directory exists
        # Mock async_playwright().start() and the subsequent _launch_browser call
        mock_playwright_manager_instance = AsyncMock(spec=Playwright) # Mock for the object returned by async_playwright().start()
        mock_playwright_manager_instance.stop = AsyncMock()

        # This is the object that `async_playwright()` itself returns, which then has a `start` method
        mock_playwright_context_manager = AsyncMock()
        mock_playwright_context_manager.start = AsyncMock(return_value=mock_playwright_manager_instance)

        with patch("app.services.upwork_profile_service.async_playwright", return_value=mock_playwright_context_manager) as mock_ap_module, \
             patch.object(UpworkProfileFetcher, "_launch_browser", new_callable=AsyncMock) as mock_launch_browser_method:

            mock_launch_browser_method.return_value = (None, None) # Simulate launch failure (page, context)

            result = await fetch_and_update_upwork_profile(profile_id, mock_db_session)

            mock_ap_module.assert_called_once() # Check that async_playwright() was called
            mock_playwright_context_manager.start.assert_called_once() # Check that .start() was called

            # Check that UpworkProfileFetcher was instantiated and _launch_browser was called on it
            # To do this properly, we might need to spy on UpworkProfileFetcher instantiation or pass mock instance.
            # For simplicity, let's assert that _launch_browser was called (it's patched on the class)
            mock_launch_browser_method.assert_called_once_with(mock_playwright_manager_instance)

            mock_playwright_manager_instance.stop.assert_called_once() # Ensure playwright manager is stopped

            assert result == {"status": "error", "message": f"Failed to launch browser for profile {profile_id}."} # Corrected expected message

# TODO: Add more tests:
# - Successful path (mocking navigation, parsing, and DB update)
# - Test for _navigate_to_profile failure
# - Test for _parse_profile_data failure (e.g. returns empty dict or specific error)
# - Test for _update_local_profile when profile not found in DB
# - Test for _update_local_profile successful update
