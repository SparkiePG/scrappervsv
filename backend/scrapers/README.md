Scrapers Overview
=================

This directory contains multiple *scraper* implementations designed to
extract useful data from web pages under different circumstances.  The
goal is to provide a resilient scraping system that can adapt if one
method fails, minimise the use of heavy dependencies, and make it
easy to extend with new strategies.  Each scraper inherits from
:class:`base.Scraper` and implements two key methods:

``can_handle(url)``
    Returns ``True`` if the scraper is appropriate for the given URL.
    For example, an API scraper might check that the domain has a
    documented API; the default implementation always returns ``True``.

``scrape(url)``
    Performs the actual retrieval and parsing of the URL.  Returns a
    dictionary with keys ``success``, ``text``, ``images``, ``links``,
    ``metadata`` and optionally ``error``.  See the docstring in
    :mod:`base` for details.

Available scrapers
------------------

``StaticScraper``
    Fetches pages using the `requests` library and parses them with
    `BeautifulSoup`.  Extracts visible text (truncated to 50 000
    characters), image sources, hyperlinks and basic metadata.
    Suitable for static sites that don't require JavaScript to render
    content.  Uses a configurable User‑Agent header and propagates
    HTTP errors to the caller.

``DynamicScraper``
    Attempts to render pages with JavaScript by launching a headless
    Chrome via Selenium.  If Selenium is unavailable or fails to
    launch, it falls back to the static scraper.  Once the page is
    rendered, it extracts text, images, links and metadata similarly
    to the static scraper.  Because headless browsers are resource
    intensive, this scraper should be used sparingly or as a fall
    back.  In production you might replace Selenium with Pyppeteer or
    Playwright.

``ApiScraper``
    A stub demonstrating how to implement a scraper that calls a
    structured API instead of fetching HTML.  In a real deployment
    you could inspect the URL and query domain‑specific APIs (such as
    Wikipedia's REST endpoints or NewsAPI).  The provided
    implementation always returns ``success=False``.

``CombinedScraper``
    Orchestrates multiple scraping strategies in sequence.  By
    default it tries the ``FileScraper``, ``StaticScraper``,
    ``ContentScraper``, ``ApiScraper`` and ``DynamicScraper`` in that
    order.  The inclusion of ``FileScraper`` first means that if the
    target URL points to a downloadable file (even without a typical
    extension), it will be fetched before attempting to parse
    HTML.  ``ContentScraper`` provides a focused article extract
    before falling back to API or dynamic scraping.  If
    ``can_handle(url)`` returns ``False`` for a given strategy it is
    skipped, except for ``FileScraper`` which is always attempted and
    will simply return ``success=False`` for HTML pages.  If a
    scraper returns ``success=True`` the result is returned
    immediately.  If all strategies fail the combined scraper
    returns an error with a list of the underlying errors.  This
    pattern provides a robust fallback mechanism and is inspired by
    the principle of graceful degradation【314426102923457†L249-L303】.

``ContentScraper``
    Identifies the main article body on a page by locating the
    element containing the most paragraph text.  This heuristic
    provides a more focused extraction of the primary content than
    aggregating all text.  It should be used when you want a cleaner
    article without navigation or boilerplate sections.  See
    ``content_scraper.py`` for details.

``FileScraper``
    Detects when a URL points to a non‑HTML resource (images, videos,
    documents) based on file extension and content type.  It
    downloads the resource (up to a configurable size limit) and
    returns it as a base64‑encoded string along with metadata such as
    filename and MIME type.  If the resource appears to be HTML it
    defers to other scrapers.  This scraper does not circumvent
    authentication or paywalls and should only be used on publicly
    accessible files【510108747246327†L93-L100】.

Adding new scrapers
-------------------

To add a new scraping strategy, create a new module that defines a
subclass of :class:`base.Scraper`, implement ``scrape``, and
optionally override ``can_handle``.  Then import your scraper in
``__init__.py`` and include it in ``CombinedScraper``'s default
sequence if appropriate.  Ensure your scraper respects target
website policies (e.g. robots.txt) and only collects data necessary
for its purpose.