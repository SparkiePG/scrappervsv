"""
ApiScraper: Example of retrieving data via a REST API instead of scraping.

Some websites expose JSON or other machine‑readable APIs that provide the
same data available on their pages.  Using these APIs is often
preferable to scraping HTML because the provider defines an explicit
contract and may offer higher rate limits.  In practice you would
implement logic here to query the relevant API endpoints based on the
URL provided.

In this demonstration project the ApiScraper is a stub: it returns
``success = False`` with an explanatory error.  You can extend it by
inspecting the URL to determine if an API exists (e.g., Wikipedia,
NewsAPI) and then fetching data using ``requests`` or an SDK.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from .base import Scraper


logger = logging.getLogger(__name__)


class ApiScraper(Scraper):
    """Stub scraper illustrating how to call an official API."""

    name = "api"

    def can_handle(self, url: str) -> bool:
        # You could implement heuristics here to detect if an API exists
        # for the given domain.  For now, always return False so this
        # scraper is not selected unless explicitly requested.
        return False

    def scrape(self, url: str) -> Dict[str, Any]:
        # Returning success=False indicates this scraper could not fetch data.
        logger.info("ApiScraper invoked for %s but not implemented", url)
        return {
            'success': False,
            'text': '',
            'images': [],
            'links': [],
            'metadata': {},
            'error': 'ApiScraper not implemented for this domain',
        }