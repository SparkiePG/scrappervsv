"""
Scrapers package
================

This package defines a hierarchy of scrapers for different scenarios.  Each
scraper implements a ``Scraper`` interface with methods to determine if it
can handle a given URL and to extract data from that URL.  Concrete
implementations include:

* :class:`StaticScraper` — uses ``requests`` and ``BeautifulSoup`` to fetch
  static HTML content and extract text, images, links and metadata.

* :class:`DynamicScraper` — attempts to render pages with JavaScript using
  Selenium or Pyppeteer (if available) before extracting content.  If
  those libraries are not installed, it falls back to static parsing.

* :class:`ApiScraper` — demonstrates how a scraper could query an API
  endpoint instead of crawling a page.  It is a stub in this project.

* :class:`CombinedScraper` — orchestrates multiple strategies in sequence,
  falling back to the next scraper if the previous one fails.  This
  increases resilience by ensuring that if one scraping method fails,
  another will attempt to fill the gap.

The goal of providing multiple scrapers is to make the scraping service
adaptable: if a page is static, we don't pay the cost of launching a
browser; if it's dynamic, we can still extract the data; if an API
exists, we can avoid scraping altogether.  This modular design also
encourages future extensions: new scrapers can be added without
modifying the existing API surface.

See ``backend/scrapers/README.md`` for more details on each scraper.
"""

from .base import Scraper
from .static_scraper import StaticScraper
from .dynamic_scraper import DynamicScraper
from .api_scraper import ApiScraper
from .file_scraper import FileScraper
from .content_scraper import ContentScraper
from .combined_scraper import CombinedScraper

__all__ = [
    "Scraper",
    "StaticScraper",
    "DynamicScraper",
    "ApiScraper",
    "ContentScraper",
    "FileScraper",
    "CombinedScraper",
]