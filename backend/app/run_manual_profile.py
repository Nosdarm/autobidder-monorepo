# run_manual_profile.py
import asyncio
from app.browser.browser_bidder import run_browser_bidder_for_profile

if __name__ == "__main__":
    asyncio.run(run_browser_bidder_for_profile("123abc"))
