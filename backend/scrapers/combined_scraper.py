"""
CombinedScraper orchestrates multiple scraping strategies.

This scraper attempts several underlying strategies in sequence
until one succeeds.  The order of strategies can be customised by
passing a list of scraper classes or instances.  For each strategy
the ``can_handle`` method is called to determine if it should be
applied to the given URL.  If ``can_handle`` returns ``False`` the
strategy is skipped.  If a strategy returns a result with
``success=True`` that result is returned immediately.  Otherwise the
next strategy is tried.  If no strategy succeeds, the returned
result will include ``success=False`` and an aggregated list of
errors under the ``errors`` key.

Using multiple strategies increases resilience: a static scraper
handles most pages quickly, a dynamic scraper renders JavaScript
when needed, and specialised API scrapers can be inserted for
specific domains.  If one approach fails due to network issues,
parsing errors, or missing dependencies, another may still produce
a useful result.  This design follows the principle of graceful
degradation recommended by ethical scraping guidelines: always try
simpler, faster methods first and fall back to more expensive
techniques only when necessary【314426102923457†L249-L303】.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Sequence, Optional, Type

from .base import Scraper

logger = logging.getLogger(__name__)


class CombinedScraper(Scraper):
    """Scraper that tries multiple underlying strategies in sequence.

    Parameters
    ----------
    scrapers : Sequence[Scraper | Type[Scraper]]
        A sequence of scraper instances or classes.  If a class is
        provided it will be instantiated when used.  The default
        sequence consists of :class:`StaticScraper`,
        :class:`ApiScraper` and :class:`DynamicScraper` in that
        order.

    Example
    -------
    >>> from .static_scraper import StaticScraper
    >>> from .dynamic_scraper import DynamicScraper
    >>> s = CombinedScraper([StaticScraper, DynamicScraper])
    >>> result = s.scrape("https://example.com")
    """

    name = "combined"

    def __init__(self, scrapers: Optional[Sequence[Scraper | Type[Scraper]]] = None,
                 user_agent: str | None = None) -> None:
        super().__init__(user_agent=user_agent)
        # Default order: static -> API -> dynamic
        if scrapers is None:
            from .file_scraper import FileScraper  # lazy import to avoid circular
            from .static_scraper import StaticScraper
            from .content_scraper import ContentScraper
            from .api_scraper import ApiScraper
            from .dynamic_scraper import DynamicScraper
            # Default order: file -> static -> content -> API -> dynamic
            scrapers = (FileScraper, StaticScraper, ContentScraper, ApiScraper, DynamicScraper)
        # Normalise scrapers to instances; instantiate with user_agent if needed
        instances: List[Scraper] = []
        for scr in scrapers:
            if isinstance(scr, Scraper):
                # Copy to ensure each has the same user_agent
                scr.user_agent = self.user_agent
                instances.append(scr)
            else:
                try:
                    instance = scr(user_agent=self.user_agent)  # type: ignore[call-arg]
                    instances.append(instance)
                except Exception as exc:
                    logger.warning("Could not instantiate scraper %s: %s", scr, exc)
        self.scrapers: List[Scraper] = instances

    def scrape(self, url: str) -> Dict[str, Any]:
        errors: List[str] = []
        for scraper in self.scrapers:
            try:
                # If the scraper is a FileScraper (identified by its name), always
                # attempt it regardless of can_handle.  The FileScraper will
                # itself check the Content‑Type and return success only for
                # non‑HTML resources.  This allows downloading files even
                # when the URL lacks a typical extension.  For other scrapers,
                # respect the can_handle predicate to avoid unnecessary work.
                if scraper.name != 'file' and not scraper.can_handle(url):
                    continue
            except Exception as exc:
                logger.warning("Error calling can_handle on %s: %s", scraper.name, exc)
                continue
            try:
                result = scraper.scrape(url)
            except Exception as exc:
                # Catch unexpected exceptions and record
                err_msg = f"{scraper.name} scraper raised exception: {exc}"
                logger.exception(err_msg)
                errors.append(err_msg)
                continue
            if result.get("success"):
                # Forward success; include which scraper succeeded
                result.setdefault("metadata", {})
                result["metadata"]["scraper"] = scraper.name
                return result
            # Record error if provided
            if "error" in result and result["error"]:
                errors.append(f"{scraper.name}: {result['error']}")
        # No scraper succeeded
        return {
            "success": False,
            "text": "",
            "images": [],
            "links": [],
            "metadata": {"scraper": "none"},
            "errors": errors,
            "error": "All scraping strategies failed",
        }