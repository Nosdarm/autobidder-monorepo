# app/autobidder/manager.py
import asyncio
import logging
from app.services.autobidder_settings_service import get_enabled_autobid_settings
from app.browser.browser_bidder import run_browser_bidder_for_profile

queue = asyncio.Queue()

async def enqueue_profiles():
    logging.info("[QUEUE] Getting autobidder settings...")
    try:
        settings_list = await asyncio.to_thread(get_enabled_autobid_settings)
        count = 0
        for setting in settings_list:
            await queue.put(setting.profile_id)
            count += 1
        logging.info(f"[QUEUE] Added {count} profiles to the queue.")
    except Exception as e:
        logging.error(f"[QUEUE] Error getting settings or adding to queue: {e}", exc_info=True)


async def worker(worker_id: int):
    logging.info(f"[WORKER {worker_id}] Started.")
    while True:
        profile_id = None
        try:
            profile_id = await queue.get()
            logging.info(f"[WORKER {worker_id}] Got profile {profile_id} from queue.")

            logging.info(f"[WORKER {worker_id}] Starting processing for profile {profile_id}...")
            await asyncio.to_thread(run_browser_bidder_for_profile, profile_id)
            logging.info(f"[WORKER {worker_id}] Finished processing for profile {profile_id}.")

        except asyncio.CancelledError:
            logging.info(f"[WORKER {worker_id}] Cancellation signal received, stopping...")
            break
        except Exception as e:
            if profile_id:
                logging.error(f"[WORKER {worker_id}] Error processing profile {profile_id}: {e}", exc_info=True)
            else:
                logging.error(f"[WORKER {worker_id}] Error getting job from queue: {e}", exc_info=True)
            await asyncio.sleep(5)
        finally:
            if profile_id is not None:
                queue.task_done()
                logging.debug(f"[WORKER {worker_id}] Task done for profile {profile_id}.")


async def start_autobidder_loop():
    logging.info("[INIT] Starting autobidder loop...")
    try:
        enqueue_task = asyncio.create_task(enqueue_profiles())

        num_workers = 1
        workers = [asyncio.create_task(worker(i)) for i in range(num_workers)]

        await enqueue_task

        logging.info("[MANAGER] Waiting for queue processing...")
        await queue.join()
        logging.info("[MANAGER] Queue processing finished.")

        logging.info("[MANAGER] Cancelling workers...")
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        logging.info("[MANAGER] Workers finished.")

    except Exception as e:
        logging.error(f"[MANAGER] Critical error in autobidder loop: {e}", exc_info=True)

    logging.info("[DONE] Autobidder loop finished.")