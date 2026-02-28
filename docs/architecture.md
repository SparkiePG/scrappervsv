Project Architecture
====================

Overview
--------

This project provides a multi‑layer scraping platform consisting of a
backend API, a frontend dashboard and a browser extension.  The
system is designed to be resilient: if one scraping approach fails,
another will attempt to retrieve the data.  The architecture draws
inspiration from best practices in web scraping, asynchronous task
management and accessible user interface design.

Components
----------

### Backend API (``backend``)

The backend is implemented using Flask for the HTTP server and
consists of the following layers:

* **Scrapers**: Located under ``backend/scrapers``, each scraper
  encapsulates a particular retrieval strategy.  The base classes and
  concrete implementations are documented in ``backend/scrapers/README.md``.
  The key design principle is **graceful degradation**: try the
  simplest, fastest method first and fall back to more complex methods
  only when needed【314426102923457†L249-L303】.

* **Task manager**: Defined in ``backend/tasks.py``, this module
  manages background jobs using a thread pool.  Each job is assigned
  a unique ID and can be polled for completion.  Limiting the number
  of concurrent threads prevents resource exhaustion and aligns with
  recommendations for large crawls to increase concurrency gradually
  while observing resource limits【561465343201228†L124-L139】.

* **Flask app**: Defined in ``backend/app.py``, this exposes the
  ``/start_scrape`` endpoint for initiating jobs and ``/status`` for
  polling results.  It validates URLs, honours robots.txt
  restrictions, constructs the appropriate scraper based on a
  requested strategy, and enqueues the scrape in the task manager.
  Jobs are run asynchronously so the HTTP server remains responsive.

### Frontend (``frontend``)

The frontend is a React application that provides a dashboard for
entering URLs, selecting scraping strategies, and viewing results.
It uses accessible, high‑contrast colours and adheres to the
5‑second rule for dashboard design: key information (job status,
scraped text preview) is surfaced at the top【26356401491938†L138-L166】.
Users can filter and search through scraped data, download JSON
exports and monitor multiple jobs concurrently.

### Browser Extension (``web‑scraper‑extension``)

The extension allows users to scrape the current page directly from
their browser.  It injects a content script to extract text,
metadata, images and links, and can send these to the backend API for
storage.  The popup UI includes an optional CSS selector field for
targeted scraping and is designed to meet Chrome’s size guidelines
while remaining accessible.

### Next.js Site (``WebWhisper-main``)

The Next.js frontend provides a polished marketing site and an
alternative interface to the API.  It demonstrates how the scraper
can be integrated into a modern web application.  The API route
``/api/scrape`` dynamically imports optional providers (e.g. Groq)
and sanitises HTML using regular expressions.

Concurrency and Resilience
-------------------------

Large‑scale scraping requires careful concurrency management to avoid
overloading both the scraper and the target sites.  Scrapy’s
documentation for broad crawls advises increasing concurrency (e.g.
to 100) while reducing logging, disabling cookies and retries, and
lowering download timeouts【561465343201228†L124-L139】【561465343201228†L177-L197】.
Although this project does not use Scrapy, these principles informed
the design of the ``TaskManager``: limit the number of worker
threads, capture errors and timeouts gracefully, and provide status
polling so that clients can back off if a job is taking too long.

Accessibility and User Experience
---------------------------------

User interfaces should be usable by everyone, including people with
disabilities.  The frontend and extension abide by WCAG 2.1
guidelines, ensuring text and background colours have sufficient
contrast (ratio of at least 4.5:1 for normal text)【560140671448684†L29-L47】,
providing clear focus states, using semantic HTML elements and ARIA
attributes, and structuring content so that screen readers announce
status updates in a timely manner.

Extensibility
-------------

New scrapers can be added by implementing the ``Scraper`` interface
and optionally overriding ``can_handle``.  They can then be wired
into the ``CombinedScraper`` or used directly.  The task manager can
also be swapped for an asynchronous framework such as Celery or
AsyncIO if more advanced queuing and distributed execution are
required.  Persistence can be added via a database layer, and rate
limiting middleware could be introduced to honour per‑site policies.

Additional Utility Modules
--------------------------

Beyond the core scrapers and task manager, several auxiliary modules
support the platform:

* **Utilities** (``backend/utils.py``) – Provides functions to validate
  and normalise URLs, ensuring only well‑formed HTTP/S URLs are
  processed and canonicalising them for consistent handling.  It
  includes ``get_proxy_dict`` which reads environment variables to
  configure HTTP and HTTPS proxies and ``get_default_user_agent``
  which selects a realistic browser user agent string at random.
  Rotating user agents and proxies helps distribute requests
  and avoid detection【742794737568601†L1796-L1803】.

* **Scheduler** (``backend/scheduler.py``) – Implements a simple
  recurring job scheduler using ``threading.Timer``.  This can be used
  to refresh certain pages at regular intervals or perform periodic
  housekeeping without relying on external cron jobs.

* **Reports** (``backend/reports.py``) – Contains helper functions to
  summarise scraped results, such as counting words, images and
  links and extracting the most common terms.  These metrics can
  inform analytics dashboards or monitoring tools.

* **FileScraper** – A scraping strategy for non‑HTML resources.  It
  detects when a URL points to an image, video or document based on
  file extension and content type.  If applicable, it downloads the
  resource (up to a configurable size limit) and returns it as a
  base64‑encoded payload with metadata.  For PDFs and DOCX files, it
  attempts to extract textual content using `pdfminer` and
  `python‑docx` so that documents can be indexed or searched.  If the
  resource appears to be HTML, it defers to other scrapers.  The
  scraper does **not** bypass authentication or paywalls; downloading
  copyrighted or premium media without permission is not
  supported【510108747246327†L93-L100】.

* **AI utilities** – The `backend/ai.py` module wraps optional
  natural‑language processing features.  It provides a `perform_ner`
  function that uses a transformer-based named-entity recognition
  (NER) model to extract entities from arbitrary text.  Because these
  models are large and may not be installed in every environment,
  `perform_ner` gracefully falls back to returning an empty list when
  the `transformers` package is unavailable.  The Flask backend
  exposes a `/ner` endpoint which accepts a JSON body with a `text`
  field and returns the extracted entities.  This AI functionality is
  optional and does not interfere with the core scraping features.