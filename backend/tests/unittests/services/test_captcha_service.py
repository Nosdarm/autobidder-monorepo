import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

import httpx # Though we mock its client and response

from app.services.captcha_service import solve_captcha_task
from app.config import Settings # To mock its values
from pydantic import AnyHttpUrl # For constructing mock settings URLs

# Helper for Mocking httpx.Response
def mock_httpx_response(status_code: int, json_data: dict) -> httpx.Response:
    """Creates a mock httpx.Response object."""
    return httpx.Response(status_code, json=json_data, request=httpx.Request(method="POST", url="http://fakeurl"))

# --- Test Cases ---

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_config", [
    {
        "name": "capmonster",
        "api_key_field": "CAPMONSTER_API_KEY",
        "create_url_field": "CAPMONSTER_CREATE_TASK_URL",
        "get_url_field": "CAPMONSTER_GET_TASK_URL",
        "key_in_get_payload": "clientKey"
    },
    {
        "name": "2captcha",
        "api_key_field": "TWOCAPTCHA_API_KEY",
        "create_url_field": "TWOCAPTCHA_CREATE_TASK_URL",
        "get_url_field": "TWOCAPTCHA_GET_TASK_URL",
        "key_in_get_payload": "clientKey" # 2Captcha uses clientKey for createTask, key (implicitly via URL) or clientKey for getTaskResult
    },
    {
        "name": "anticaptcha",
        "api_key_field": "ANTICAPTCHA_API_KEY",
        "create_url_field": "ANTICAPTCHA_CREATE_TASK_URL",
        "get_url_field": "ANTICAPTCHA_GET_TASK_URL",
        "key_in_get_payload": "key" # AntiCaptcha uses 'key' in getTaskResult payload
    }
])
async def test_solve_captcha_successful_hcaptcha(provider_config):
    """Tests successful HCaptcha solving for each provider."""

    provider_name = provider_config["name"]
    mock_settings = Settings() # Create a real Settings object to modify
    setattr(mock_settings, 'CAPTCHA_PROVIDER_NAME', provider_name)
    setattr(mock_settings, provider_config["api_key_field"], "test_api_key")
    # Ensure URLs are set if they have defaults that might be None in a minimal Settings()
    setattr(mock_settings, provider_config["create_url_field"], AnyHttpUrl(f"http://fake{provider_name}.com/createTask"))
    setattr(mock_settings, provider_config["get_url_field"], AnyHttpUrl(f"http://fake{provider_name}.com/getTaskResult"))

    mock_create_task_url = str(getattr(mock_settings, provider_config["create_url_field"]))
    mock_get_result_url = str(getattr(mock_settings, provider_config["get_url_field"]))

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep: # Patch sleep

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value

        # Simulate API responses
        # 1. createTask response
        create_task_response_json = {"errorId": 0, "taskId": "test_task_id_123"}
        if provider_name == "2captcha": # 2captcha might return status 1 for success on create
             create_task_response_json = {"status": 1, "request": "test_task_id_123"} # taskid is in request

        # 2. getTaskResult responses (processing then ready)
        processing_response_json = {"status": "processing", "errorId": 0} # Capmonster/AntiCaptcha
        if provider_name == "2captcha":
            processing_response_json = {"status": 0, "request": "CAPCHA_NOT_READY"}

        ready_response_json = {"status": "ready", "solution": {"gRecaptchaResponse": "solved_token"}, "errorId": 0} # Capmonster/AntiCaptcha
        if provider_name == "2captcha":
            ready_response_json = {"status": 1, "request": "solved_token"}


        mock_http_client_instance.post.side_effect = [
            mock_httpx_response(200, create_task_response_json),
            mock_httpx_response(200, processing_response_json),
            mock_httpx_response(200, processing_response_json),
            mock_httpx_response(200, ready_response_json)
        ]

        solution = await solve_captcha_task(url="http://test.com", sitekey="test_sitekey", task_type="HCaptchaTaskProxyless")
        assert solution == "solved_token"

        # Assert calls to http client
        assert mock_http_client_instance.post.call_count == 4 # 1 create, 3 getResult (2 processing, 1 ready)

        # Check createTask call
        create_call_args = mock_http_client_instance.post.call_args_list[0]
        assert create_call_args.args[0] == mock_create_task_url
        assert create_call_args.kwargs['json']['clientKey'] == "test_api_key"
        assert create_call_args.kwargs['json']['task']['type'] == "HCaptchaTaskProxyless"

        # Check getTaskResult call (last one)
        get_call_args = mock_http_client_instance.post.call_args_list[-1]
        assert get_call_args.args[0] == mock_get_result_url

        expected_get_payload_key = provider_config["key_in_get_payload"]
        assert get_call_args.kwargs['json'][expected_get_payload_key] == "test_api_key"
        assert get_call_args.kwargs['json']['taskId'] == ("test_task_id_123" if provider_name != "2captcha" else "test_task_id_123")


@pytest.mark.asyncio
async def test_create_task_api_error():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient:

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        mock_http_client_instance.post.return_value = mock_httpx_response(
            200, {"errorId": 1, "errorCode": "ERROR_KEY_DOES_NOT_EXIST", "errorDescription": "Key does not exist"}
        )

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "ERROR_KEY_DOES_NOT_EXIST" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_result_polling_timeout():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep: # Patch sleep to speed up test

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value

        # createTask is successful
        create_task_response_json = {"errorId": 0, "taskId": "timeout_task_id"}
        # getTaskResult always returns "processing"
        processing_response_json = {"status": "processing", "errorId": 0}

        # Configure side_effect to return create_task_response first, then always processing_response
        responses = [mock_httpx_response(200, create_task_response_json)] + \
                    [mock_httpx_response(200, processing_response_json)] * 30 # Simulate 30 processing responses
        mock_http_client_instance.post.side_effect = responses

        with pytest.raises(TimeoutError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "CAPTCHA solution not received" in str(exc_info.value)
        assert "timeout_task_id" in str(exc_info.value) # Check if task_id is in the error
        assert mock_sleep.call_count == 29 # Called 29 times before the 30th poll attempt fails the loop

@pytest.mark.asyncio
async def test_get_result_api_error_during_polling():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        create_task_response_json = {"errorId": 0, "taskId": "poll_error_task_id"}
        processing_response_json = {"status": "processing", "errorId": 0}
        error_response_json = {"errorId": 1, "errorCode": "ERROR_TASK_ABSENT", "errorDescription": "Task ID not found"}

        mock_http_client_instance.post.side_effect = [
            mock_httpx_response(200, create_task_response_json),
            mock_httpx_response(200, processing_response_json),
            mock_httpx_response(200, error_response_json)
        ]

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "ERROR_TASK_ABSENT" in str(exc_info.value)

@pytest.mark.asyncio
async def test_unsupported_provider_name():
    # Use PropertyMock for CAPTCHA_PROVIDER_NAME as it's a direct attribute access
    with patch.object(Settings, 'CAPTCHA_PROVIDER_NAME', new_callable=PropertyMock, return_value="unknown_provider"):
        # No need to mock other settings if this check happens first
        with pytest.raises(ValueError, match="Unsupported CAPTCHA provider: unknown_provider"):
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")


@pytest.mark.asyncio
async def test_missing_api_key_for_selected_provider():
    # Create a settings object where the selected provider's key is None
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="2captcha", TWOCAPTCHA_API_KEY=None)

    with patch('app.services.captcha_service.settings', mock_settings):
        with pytest.raises(ValueError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "API key for 2captcha is not set" in str(exc_info.value)

@pytest.mark.asyncio
async def test_different_task_types_in_payload():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value

        create_task_response_json = {"errorId": 0, "taskId": "task_type_test_id"}
        ready_response_json = {"status": "ready", "solution": {"gRecaptchaResponse": "solved_token_v2"}, "errorId": 0}

        mock_http_client_instance.post.side_effect = [
            mock_httpx_response(200, create_task_response_json),
            mock_httpx_response(200, ready_response_json)
        ]

        test_task_type = "RecaptchaV2TaskProxyless"
        solution = await solve_captcha_task(
            url="http://test.com",
            sitekey="test_sitekey_v2",
            task_type=test_task_type
        )
        assert solution == "solved_token_v2"

        # Assert that the task type was correctly passed in the payload
        create_call_args = mock_http_client_instance.post.call_args_list[0]
        assert create_call_args.kwargs['json']['task']['type'] == test_task_type
        assert create_call_args.kwargs['json']['task']['websiteKey'] == "test_sitekey_v2"

@pytest.mark.asyncio
async def test_create_task_http_error():
    """Tests handling of non-200 HTTP status code during task creation."""
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient:

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        # Simulate a 500 server error from the CAPTCHA provider
        mock_http_client_instance.post.return_value = mock_httpx_response(
            500, {"errorDescription": "Internal Server Error"}
        )

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "Failed to create CAPTCHA task" in str(exc_info.value)
        assert "Status: 500" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_result_malformed_solution():
    """Tests handling of 'ready' status but malformed/missing solution object."""
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="capmonster", CAPMONSTER_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value

        create_task_response_json = {"errorId": 0, "taskId": "malformed_solution_task_id"}
        # Simulate 'ready' status but missing 'gRecaptchaResponse' in solution
        ready_response_malformed_json = {"status": "ready", "solution": {"someOtherKey": "value"}, "errorId": 0}

        mock_http_client_instance.post.side_effect = [
            mock_httpx_response(200, create_task_response_json),
            mock_httpx_response(200, ready_response_malformed_json)
        ]

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "reported 'ready' but solution format incorrect" in str(exc_info.value)

@pytest.mark.asyncio
async def test_2captcha_error_response_on_create():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="2captcha", TWOCAPTCHA_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient:

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        # 2Captcha returns status 0 and error text in 'request' for some errors
        error_response_json = {"status": 0, "request": "ERROR_WRONG_USER_KEY"}
        mock_http_client_instance.post.return_value = mock_httpx_response(200, error_response_json)

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        # This needs to match how solve_captcha_task constructs the error message for 2captcha create errors
        assert "Failed to get taskId from 2captcha" in str(exc_info.value) or "ERROR_WRONG_USER_KEY" in str(exc_info.value)

@pytest.mark.asyncio
async def test_2captcha_error_response_on_get_result():
    mock_settings = Settings(CAPTCHA_PROVIDER_NAME="2captcha", TWOCAPTCHA_API_KEY="test_key")

    with patch('app.services.captcha_service.settings', mock_settings), \
         patch('httpx.AsyncClient') as MockAsyncClient, \
         patch('asyncio.sleep', new_callable=AsyncMock):

        mock_http_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        create_task_response_json = {"status": 1, "request": "test_task_id_2captcha_err"}
        # 2Captcha error during polling
        error_polling_response_json = {"status": 0, "request": "ERROR_CAPTCHA_UNSOLVABLE"}

        mock_http_client_instance.post.side_effect = [
            mock_httpx_response(200, create_task_response_json),
            mock_httpx_response(200, error_polling_response_json)
        ]

        with pytest.raises(RuntimeError) as exc_info:
            await solve_captcha_task(url="http://test.com", sitekey="test_sitekey")
        assert "Error from 2Captcha: ERROR_CAPTCHA_UNSOLVABLE" in str(exc_info.value)
