import pytest
from unittest.mock import patch, MagicMock

# Ensure this path is correct based on your project structure
from app.scheduler.scheduler import scheduler, start_scheduler, shutdown_scheduler

# Fixture to ensure scheduler is reset and shut down for each test
@pytest.fixture(autouse=True)
def manage_scheduler_state():
    # Remove any existing jobs from previous test runs or states
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)

    # Ensure scheduler is not running at the start of a test
    if scheduler.running:
        scheduler.shutdown(wait=False)
        # Re-initialize after shutdown if necessary, or ensure start_scheduler does this.
        # For a global scheduler, simply ensuring it's shut down might be enough
        # as start_scheduler typically reconfigures or starts it.

    yield # Test runs here

    # Teardown: Ensure scheduler is shut down after the test
    if scheduler.running:
        scheduler.shutdown(wait=False)

def test_scheduler_adds_upwork_profile_update_job():
    # Mock the actual job functions to prevent execution and external dependencies
    with patch('app.scheduler.scheduler.run_autobid', MagicMock()) as mock_run_autobid, \
         patch('app.services.upwork_profile_service.trigger_scheduled_upwork_profile_updates', MagicMock()) as mock_trigger_upwork_updates:

        # Call the function that configures and starts the scheduler
        start_scheduler()

        assert scheduler.running, "Scheduler should be running after start_scheduler()"

        # Verify the 'update_upwork_profiles' job
        upwork_job = scheduler.get_job('update_upwork_profiles')
        assert upwork_job is not None, "The 'update_upwork_profiles' job should be scheduled."
        assert upwork_job.id == 'update_upwork_profiles'

        # Check the job's trigger interval (e.g., every 6 hours)
        # The string representation of an IntervalTrigger for 6 hours is "interval[0:06:00]"
        # APScheduler's interval trigger string format is "interval[weeks:days:hours:minutes:seconds:microseconds]"
        # So, 6 hours would be "interval[0:0:6:0:0:0]"
        # However, the __str__ representation might be simplified. Let's check common formats.
        # A common simplified format is interval[HH:MM:SS] or with days.
        # For hours=6, it's typically 'interval[6:00:00]' if days are zero, or more explicitly with all fields.
        # The provided "interval[0:06:00]" seems to imply "days:hours:minutes".
        # APScheduler IntervalTrigger for hours=6 gives str like: "interval[00:00:00 - 9999-12-31 23:59:59.999999 UTC, every 6 hours]" if start/end dates are default.
        # Or, if specific fields used: "interval[hours=6]" if only hours is set.
        # The trigger object itself is what we should assert against more directly if possible.
        # For now, we'll use the string representation as per the prompt's expectation,
        # but this might need adjustment based on actual APScheduler output.
        # A common string output for IntervalTrigger(hours=6) is "interval[06:00:00]"
        # Let's assume the prompt's format "interval[DD:HH:MM]" (days:hours:minutes) is simplified.
        # For 6 hours, it would be "interval[0:06:00]".
        # For 2 minutes, it would be "interval[0:00:02]". (The prompt's example for autobid uses "interval[0:00:02:00]" which is DD:HH:MM:SS)
        # Let's stick to DD:HH:MM:SS format for consistency.
        # 6 hours = 0 days, 6 hours, 0 minutes, 0 seconds
        assert str(upwork_job.trigger) == "interval[0:0:6:0:0]", \
               f"Incorrect trigger for upwork_job: {upwork_job.trigger}. Expected interval[0:0:6:0:0] (6 hours)"


        # Verify the 'run_autobid' job
        # The autobid job is added as: scheduler.add_job(run_autobid, 'interval', minutes=2)
        # It doesn't have an explicit ID. APScheduler will assign one like 'd9f2b9e68a7840b5918f7389b5199207'
        # So we need to find it by function or check all jobs.
        autobid_job_found = False
        for job in scheduler.get_jobs():
            if job.id != 'update_upwork_profiles': # Assuming only two jobs for now
                 autobid_job_found = True
                 # 2 minutes = 0 days, 0 hours, 2 minutes, 0 seconds
                 assert str(job.trigger) == "interval[0:0:0:2:0]", \
                        f"Incorrect trigger for autobid_job: {job.trigger}. Expected interval[0:0:0:2:0] (2 minutes)"
                 break
        assert autobid_job_found, "An autobid job should be scheduled."


        # Stop the scheduler
        shutdown_scheduler()
        assert not scheduler.running, "Scheduler should be stopped after shutdown_scheduler()"
