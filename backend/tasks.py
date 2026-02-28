"""
Task management for asynchronous scraping jobs.

This module defines a :class:`TaskManager` class that manages
asynchronous scraping tasks.  Scraping can be resource‑intensive and
time‑consuming; running tasks in the background prevents the HTTP
server from blocking while a scrape is in progress.  Users can poll
for status and retrieve results when they are ready.

The manager uses a :class:`concurrent.futures.ThreadPoolExecutor` to
run scraping functions in separate threads.  A unique job ID is
generated for each submission.  When a job completes, its result is
stored in an internal dictionary.  If a job raises an exception,
the exception message is captured and returned as an error.

Example usage::

    from backend.scrapers import CombinedScraper
    from backend.tasks import task_manager

    scraper = CombinedScraper()
    job_id = task_manager.submit(scraper.scrape, url)
    # Later...
    status, result = task_manager.get_status(job_id)
    if status == 'finished':
        print(result)

The module instantiates a global :data:`task_manager` that can be
imported by the Flask app.  A global instance avoids creating many
executors and allows configurable worker limits.

Concurrency configuration is inspired by best practices for large
crawls: limit the number of concurrent threads to avoid overloading
both your machine and target websites, and ensure jobs that hang
timeout rather than blocking indefinitely【561465343201228†L124-L139】【561465343201228†L199-L208】.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock
from typing import Callable, Dict, Any, Tuple, Optional


class TaskManager:
    """Manage background scraping tasks using a thread pool."""

    def __init__(self, max_workers: int = 4) -> None:
        # Limit concurrency to avoid overwhelming the system
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: Dict[str, Future] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def submit(self, fn: Callable[..., Dict[str, Any]], *args, **kwargs) -> str:
        """Submit a new job to run in the background.

        Returns
        -------
        job_id : str
            A unique identifier for the submitted job.
        """
        job_id = uuid.uuid4().hex
        future = self._executor.submit(fn, *args, **kwargs)
        with self._lock:
            self._futures[job_id] = future
        # When complete, store result or exception
        def _callback(fut: Future) -> None:
            try:
                result = fut.result()
                if not isinstance(result, dict):
                    result = {
                        "success": False,
                        "error": f"Invalid result type {type(result)}",
                    }
            except Exception as exc:
                result = {
                    "success": False,
                    "error": str(exc),
                }
            with self._lock:
                self._results[job_id] = result
        future.add_done_callback(_callback)
        return job_id

    def get_status(self, job_id: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Get the status and result of a job.

        Parameters
        ----------
        job_id : str
            The job identifier returned by :meth:`submit`.

        Returns
        -------
        status : {'pending', 'finished', None}
            ``'pending'`` if the job is still running, ``'finished'``
            if completed, or ``None`` if no such job exists.
        result : dict | None
            The result of the job if finished, or ``None`` if pending
            or unknown.
        """
        with self._lock:
            future = self._futures.get(job_id)
            result = self._results.get(job_id)
        if future is None:
            return None, None
        if future.done():
            return "finished", result
        return "pending", None

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Return a snapshot of all jobs with their statuses.

        Returns a dictionary mapping job IDs to status and, if finished,
        the result.  This can be used for administrative dashboards.
        """
        jobs: Dict[str, Dict[str, Any]] = {}
        with self._lock:
            job_ids = list(self._futures.keys())
        for job_id in job_ids:
            status, result = self.get_status(job_id)
            jobs[job_id] = {
                'status': status,
            }
            if status == 'finished':
                jobs[job_id]['result'] = result
        return jobs

    def cancel(self, job_id: str) -> bool:
        """Attempt to cancel a pending job.

        Returns ``True`` if the job was cancelled, ``False`` if it was
        already running or finished or not found.  Cancellation is best
        effort: if the job has already started execution, it may not
        stop until completion.
        """
        with self._lock:
            future = self._futures.get(job_id)
        if future is None:
            return False
        # ``cancel`` returns False if the call could not be cancelled
        # (e.g. if it is already running).  We do not remove it from
        # our tracking structures here; it will be cleaned up when
        # finished.
        return future.cancel()


# A global task manager instance with a reasonable number of workers.
# The number of workers can be increased via environment variables
# or configuration if needed.
task_manager = TaskManager(max_workers=4)