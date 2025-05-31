# app/services/captcha_service.py
import httpx
import os # Keep os if needed for other parts, otherwise remove
import asyncio
from app.config import settings # Import settings

# CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY") # Replaced by settings
# CAPTCHA_PROVIDER = os.getenv( # Replaced by settings
#     "CAPTCHA_PROVIDER",
#     "2captcha")

# The old check for a single CAPTCHA_API_KEY is removed.
import logging # Added
from typing import Optional # Added

# Provider-specific keys will be checked within the solve_captcha_task function.

logger = logging.getLogger(__name__) # Added

async def solve_captcha_task(url: str, sitekey: str, task_type: str = "HCaptchaTaskProxyless") -> str:
    """
    Решает CAPTCHA задачу (hCaptcha, reCAPTCHA v2, etc.) через выбранного CAPTCHA-провайдера.
    Возвращает токен решения.
    """
    logger.info(f"Attempting to solve CAPTCHA using provider: {settings.CAPTCHA_PROVIDER_NAME}") # Added initial log message
    api_key: Optional[str] = None
    create_task_url: str
    get_result_url: str

    provider_name = settings.CAPTCHA_PROVIDER_NAME.lower()

    if provider_name == "capmonster":
        api_key = settings.CAPMONSTER_API_KEY
        create_task_url = str(settings.CAPMONSTER_CREATE_TASK_URL)
        get_result_url = str(settings.CAPMONSTER_GET_TASK_URL)
    elif provider_name == "2captcha":
        api_key = settings.TWOCAPTCHA_API_KEY
        create_task_url = str(settings.TWOCAPTCHA_CREATE_TASK_URL)
        get_result_url = str(settings.TWOCAPTCHA_GET_TASK_URL)
    elif provider_name == "anticaptcha":
        api_key = settings.ANTICAPTCHA_API_KEY
        create_task_url = str(settings.ANTICAPTCHA_CREATE_TASK_URL)
        get_result_url = str(settings.ANTICAPTCHA_GET_TASK_URL)
    else:
        raise ValueError(f"Unsupported CAPTCHA provider: {settings.CAPTCHA_PROVIDER_NAME}")

    if not api_key:
        raise ValueError(f"API key for {settings.CAPTCHA_PROVIDER_NAME} is not set in settings.")

    # TODO: Review if task structure for HCaptchaTaskProxyless differs significantly between providers.
    # For now, assuming a common structure where 'clientKey' is at the top level, and 'task' object is similar.
    # AntiCaptcha might use 'key' instead of 'clientKey' in the main payload for some API interactions,
    # but for createTask, 'clientKey' is often part of the main object or 'key' for the task object.
    # CapMonster and 2Captcha generally use 'clientKey' in the top-level object.

    # Construct the task definition based on task_type
    task_definition = {
        "type": task_type,
        "websiteURL": url,
        "websiteKey": sitekey # Standard key for HCaptchaTaskProxyless, RecaptchaV2TaskProxyless
        # TODO: Add logic for other task types that might require different parameters or key names:
        # if task_type == "FunCaptchaTaskProxyless":
        #     task_definition["websitePublicKey"] = sitekey # FunCaptcha uses 'websitePublicKey'
        #     del task_definition["websiteKey"]
        # if task_type == "RecaptchaV3TaskProxyless":
        #     task_definition["pageAction"] = "your_default_action" # Example, should be passed in or configured
        #     task_definition["minScore"] = 0.3 # Example, should be passed in or configured
    }

    task_payload = {
        "clientKey": api_key,
        "task": task_definition
        # AntiCaptcha specific: "softId": YOUR_SOFT_ID (optional, for developers)
        # if provider_name == "anticaptcha":
        #    task_payload["softId"] = 1234 # Replace with your actual softId if you have one
    }

    async with httpx.AsyncClient() as client:
        # 1. Create CAPTCHA solving task
        logger.info(f"Creating CAPTCHA task ({task_type}) with {provider_name} at {create_task_url} for sitekey {sitekey}") # Changed print to logger
        resp = await client.post(create_task_url, json=task_payload, timeout=30.0)

        if resp.status_code != 200:
            logger.error(f"Failed to create CAPTCHA task with {provider_name}. Status: {resp.status_code}, Response: {resp.text}")
            raise RuntimeError(f"❌ Failed to create CAPTCHA task with {provider_name}. Status: {resp.status_code}, Response: {resp.text}")

        resp_data = resp.json()
        task_id = resp_data.get("taskId")

        # Error handling for task creation response (varies by provider)
        # TODO: Consider more specific error handling per provider if their error responses differ greatly.
        if not task_id:
            error_code = resp_data.get("errorCode")
            error_description = resp_data.get("errorDescription") or resp_data.get("errorText") # errorText for 2captcha
            if error_code:
                 logger.error(f"Error creating CAPTCHA task with {provider_name}: {error_code} - {error_description}. Response: {resp.text}")
                 raise RuntimeError(f"❌ Error creating CAPTCHA task with {provider_name}: {error_code} - {error_description}.")
            logger.error(f"Failed to get taskId from {provider_name}. Response: {resp.text}")
            raise RuntimeError(f"❌ Failed to get taskId from {provider_name}.")

        logger.info(f"CAPTCHA task created with ID: {task_id} using {provider_name} for task type {task_type}.") # Changed print to logger

        # 2. Poll for task result
        # TODO: Review if getTaskResult payload differs for AntiCaptcha beyond 'key' vs 'clientKey'.
        get_task_payload = {
            "clientKey": api_key, # Common for CapMonster, 2Captcha
            "taskId": task_id
        }
        if provider_name == "anticaptcha": # AntiCaptcha uses "key"
            get_task_payload = {"key": api_key, "taskId": task_id}

        for i in range(30): # Poll for ~2.5 minutes (30 * 5s)
            await asyncio.sleep(5)
            logger.info(f"Polling for CAPTCHA result (attempt {i+1}/30) for task ID: {task_id} ({task_type}) from {provider_name}") # Changed print to logger
            result_resp = await client.post(get_result_url, json=get_task_payload, timeout=30.0)

            if result_resp.status_code != 200:
                logger.warning(f"Non-200 status when polling for CAPTCHA result from {provider_name}. Status: {result_resp.status_code}, Response: {result_resp.text}")
                continue

            status_data = result_resp.json()

            # Status checking (varies by provider)
            # TODO: Revisit if solution structure or key names differ significantly for other task_types.
            # For HCaptchaTaskProxyless and RecaptchaV2TaskProxyless, "gRecaptchaResponse" is common.
            # RecaptchaV3 typically returns a token that's used differently (not directly in a form field).
            current_status = status_data.get("status") # Common for CapMonster, AntiCaptcha

            if provider_name == "2captcha":
                if status_data.get("status") == 1 and status_data.get("request"): # Success for 2Captcha
                    logger.info(f"CAPTCHA solved successfully by 2Captcha for task {task_id} ({task_type}).")
                    return status_data["request"] # Solution is in 'request' field
                elif status_data.get("status") == 0 and status_data.get("request") == "CAPCHA_NOT_READY":
                    current_status = "processing" # Normalize for common logic
                elif status_data.get("status") == 0: # Other error from 2Captcha
                    error_text = status_data.get("request")
                    logger.error(f"Error from 2Captcha while solving task {task_id} ({task_type}): {error_text}. Response: {status_data}")
                    raise RuntimeError(f"❌ Error from 2Captcha: {error_text}")

            if current_status == "ready":
                solution = status_data.get("solution")
                # Common solution field for HCaptcha and RecaptchaV2 is gRecaptchaResponse
                # RecaptchaV3 might use a different key like "token" or also "gRecaptchaResponse" depending on provider.
                # TODO: Verify solution key for different task_types if they vary from "gRecaptchaResponse"
                token_key = "gRecaptchaResponse" # Default for HCaptcha, RecaptchaV2
                # if task_type == "RecaptchaV3TaskProxyless": token_key = "token" # Example for V3

                if solution and solution.get(token_key):
                    logger.info(f"CAPTCHA solved successfully by {provider_name} for task {task_id} ({task_type}).")
                    return solution[token_key]
                else:
                    logger.error(f"{provider_name} reported status 'ready' but solution (key: {token_key}) was not found/malformed for task {task_id} ({task_type}). Response: {status_data}")
                    raise RuntimeError(f"❌ {provider_name} reported 'ready' but solution format incorrect.")

            elif current_status == "processing":
                logger.info(f"Task {task_id} ({task_type}) still processing by {provider_name}...")
                continue

            error_code = status_data.get("errorCode") # Common for CapMonster, AntiCaptcha
            if error_code:
                error_description = status_data.get("errorDescription")
                logger.error(f"Error from {provider_name} while solving task {task_id} ({task_type}): {error_code} - {error_description}")
                raise RuntimeError(f"❌ Error from {provider_name}: {error_code} - {error_description}")

            logger.warning(f"Unknown status or format from {provider_name} for task {task_id} ({task_type}): {status_data}. Continuing to poll.")

    task_id_str = task_id if 'task_id' in locals() and task_id is not None else 'unknown'
    logger.error(f"CAPTCHA solution not received from {settings.CAPTCHA_PROVIDER_NAME} for task {task_id_str} ({task_type}) within the allotted time.")
    raise TimeoutError(f"❌ CAPTCHA solution not received from {settings.CAPTCHA_PROVIDER_NAME} for task {task_id_str} ({task_type}).")
