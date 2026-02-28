"""
Simple job scheduler for recurring scraping tasks.

This module defines a :class:`ScheduleManager` that can schedule
functions to run periodically using Python's ``threading.Timer``.
It maintains a registry of recurring jobs and allows them to be
started and stopped individually.  Although primitive compared to
libraries like Celery or APScheduler, it illustrates how one might
extend the scraping service to perform regular updates without user
intervention.

The scheduler is not integrated into the Flask API by default, but
could be exposed via admin endpoints or configured on startup to
refresh specific pages at intervals.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional


class ScheduledJob:
    """Represents a recurring job."""

    def __init__(self, func: Callable, interval: float) -> None:
        self.func = func
        self.interval = interval
        self._timer: Optional[threading.Timer] = None
        self._running = False

    def _run(self) -> None:
        if not self._running:
            return
        try:
            self.func()
        finally:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._timer = threading.Timer(self.interval, self._run)
        self._timer.start()

    def stop(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None


class ScheduleManager:
    """Manage multiple scheduled jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}

    def add_job(self, name: str, func: Callable, interval: float) -> None:
        """Add and start a recurring job.

        Parameters
        ----------
        name : str
            Unique name for the job.
        func : Callable
            Function to call every ``interval`` seconds.
        interval : float
            Number of seconds between calls.
        """
        if name in self._jobs:
            raise ValueError(f"Job {name} already exists")
        job = ScheduledJob(func, interval)
        self._jobs[name] = job
        job.start()

    def remove_job(self, name: str) -> None:
        """Stop and remove a job by name."""
        job = self._jobs.pop(name, None)
        if job:
            job.stop()

    def stop_all(self) -> None:
        """Stop and remove all jobs."""
        for job in list(self._jobs.values()):
            job.stop()
        self._jobs.clear()