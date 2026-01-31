"""Scheduler service for periodic tasks."""

import asyncio
import threading
from datetime import datetime
from typing import Callable, Dict, Any
import time


class TaskScheduler:
    """Simple scheduler for periodic tasks."""

    def __init__(self):
        self.tasks = {}
        self.running = False
        self.thread = None

    def add_periodic_task(self, name: str, func: Callable, interval: int, immediate: bool = True):
        """Add a periodic task to run every 'interval' seconds.

        Args:
            name: Unique name for the task
            func: Function to call
            interval: Interval in seconds
            immediate: Whether to run immediately on start
        """
        self.tasks[name] = {
            'func': func,
            'interval': interval,
            'last_run': time.time() if not immediate else time.time() - interval,
            'enabled': True
        }

    def remove_task(self, name: str):
        """Remove a scheduled task."""
        if name in self.tasks:
            del self.tasks[name]

    def disable_task(self, name: str):
        """Disable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = False

    def enable_task(self, name: str):
        """Enable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = True

    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        while self.running:
            current_time = time.time()

            for name, task in self.tasks.items():
                if task['enabled'] and (current_time - task['last_run']) >= task['interval']:
                    try:
                        task['func']()
                        task['last_run'] = current_time
                    except Exception as e:
                        print(f"Error running scheduled task {name}: {e}")

            time.sleep(1)  # Sleep briefly to avoid busy waiting

    def start(self):
        """Start the scheduler."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish


# Global scheduler instance
scheduler = TaskScheduler()


def init_scheduler():
    """Initialize the scheduler with default tasks."""
    from .dashboard_updater import update_dashboard_now

    # Update dashboard every 30 seconds
    scheduler.add_periodic_task(
        name="dashboard_update",
        func=update_dashboard_now,
        interval=30,  # Every 30 seconds
        immediate=True
    )

    # You can add more periodic tasks here as needed
    # For example: audit log cleanup, health checks, etc.

    scheduler.start()


def shutdown_scheduler():
    """Shutdown the scheduler."""
    scheduler.stop()


# Convenience functions
def schedule_dashboard_update():
    """Schedule a dashboard update."""
    from .dashboard_updater import update_dashboard_now
    update_dashboard_now()


if __name__ == "__main__":
    # Test the scheduler
    def test_task():
        print(f"Test task executed at {datetime.now()}")

    scheduler.add_periodic_task("test", test_task, 5)
    scheduler.start()

    # Let it run for a bit
    time.sleep(20)
    scheduler.stop()