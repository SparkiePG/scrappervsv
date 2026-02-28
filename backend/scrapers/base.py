"""
Base classes for scrapers.

All scrapers should inherit from :class:`Scraper` and implement the
``scrape`` method.  Scrapers may also override ``can_handle`` to
indicate that they are only appropriate for certain kinds of URLs (for
example, API scrapers may require a specific domain or path).

Each scraper returns a dictionary with at least the following keys:

``success``
    A boolean indicating whether the scrape was successful.
``text``
    The extracted textual content of the page.  May be an empty string
    if not applicable.
``images``
    A list of image URLs.
``links``
    A list of hyperlinks.
``metadata``
    A dictionary of page metadata (title, description, etc.).
``error`` (optional)
    A human‑readable error message if the scrape failed.

Scrapers should raise exceptions only for unrecoverable errors (such
as invalid configuration); network failures and parse errors should be
caught internally and reflected in the returned ``success`` flag.
"""

from __future__ import annotations

from typing import Dict, Any


class Scraper:
    """Base class for all scrapers.

    Subclasses must override :meth:`scrape` and may override
    :meth:`can_handle`.
    """

    name: str = "base"

    def __init__(self, user_agent: str | None = None) -> None:
        # Use provided user agent or choose a realistic one if none supplied
        from backend.utils import get_default_user_agent  # lazy import to avoid circular
        if user_agent and user_agent.strip():
            self.user_agent = user_agent
        else:
            self.user_agent = get_default_user_agent()

    def can_handle(self, url: str) -> bool:
        """Return True if this scraper is suitable for the given URL.

        The default implementation always returns True.  Subclasses can
        override this method to restrict to specific domains or patterns.
        """
        return True

    def scrape(self, url: str) -> Dict[str, Any]:
        """Scrape the given URL and return a result dictionary.

        Subclasses must implement this method.  The returned dict must
        include a ``success`` key as described above.
        """
        raise NotImplementedError("Scraper.scrape() must be implemented in subclasses")