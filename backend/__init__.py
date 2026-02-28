"""
Backend package for the web scraper project.

This package encapsulates the API server, scraping strategies, task
management, utilities and scheduling.  It can be imported as a
namespace to access submodules such as ``backend.scrapers``,
``backend.tasks`` and ``backend.scheduler``.
"""

__all__ = [
    'scrapers',
    'tasks',
    'scheduler',
    'utils',
    'reports',
]