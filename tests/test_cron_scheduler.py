import asyncio
from datetime import datetime, timedelta
from arkhe_scheduler.cron_scheduler import CronJob, CathedralCronScheduler

def test_should_run():
    async def dummy_task():
        pass

    job = CronJob(
        name="test_job",
        schedule="* * * * *",  # Every minute
        task=dummy_task
    )

    now = datetime(2023, 1, 1, 12, 0, 0)

    # croniter get_next returns 12:01:00 when initialized at 12:00:00
    # Thus, calling should_run at 12:00:00 is False, but should_run at 12:01:00 is True.
    assert job.should_run(now) is False

    next_minute = now + timedelta(minutes=1)
    assert job.should_run(next_minute) is True

    job.mark_executed(next_minute)

    # After execution, next_run should be 12:02:00
    assert job.next_run == datetime(2023, 1, 1, 12, 2, 0)

    # should_run should return False before 12:02:00
    later = next_minute + timedelta(seconds=30)
    assert job.should_run(later) is False

    # should_run should return True at or after 12:02:00
    two_minutes = next_minute + timedelta(minutes=1)
    assert job.should_run(two_minutes) is True


def test_scheduler_jobs():
    scheduler = CathedralCronScheduler()

    job_names = [job.name for job in scheduler.jobs]

    expected_jobs = [
        "phi_c_sync",
        "cvs_scan",
        "apm_model",
        "sbom_generation",
        "edge_ai_optimization",
        "hsm_cert_rotation",
        "log_pruning"
    ]

    for expected_job in expected_jobs:
        assert expected_job in job_names

    # Check a specific job schedule
    phi_c_sync_job = next(job for job in scheduler.jobs if job.name == "phi_c_sync")
    assert phi_c_sync_job.schedule == "* * * * *"
