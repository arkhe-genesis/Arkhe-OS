import time
from typing import Callable, List, Tuple

class Substrato5CronScheduler:
    def __init__(self):
        # Store tuples of (interval_seconds, next_run_time, callback)
        self.jobs: List[Tuple[float, float, Callable]] = []

    def schedule(self, interval_seconds: float, callback: Callable):
        """Schedules a job to run every `interval_seconds`."""
        next_run = time.time() + interval_seconds
        self.jobs.append((interval_seconds, next_run, callback))

    def run_pending(self):
        """Runs any jobs that are due."""
        now = time.time()
        for i in range(len(self.jobs)):
            interval, next_run, callback = self.jobs[i]
            if now >= next_run:
                callback()
                # Reschedule
                self.jobs[i] = (interval, now + interval, callback)

if __name__ == "__main__":
    def my_task():
        print("Task executed at", time.strftime("%X"))

    scheduler = Substrato5CronScheduler()
    scheduler.schedule(2.0, my_task)

    print("Starting scheduler simulation...")
    start = time.time()
    # Run for 5 seconds
    while time.time() - start < 5:
        scheduler.run_pending()
        time.sleep(0.1)
