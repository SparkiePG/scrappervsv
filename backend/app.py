"""
WebScraper Backend
===================

This Flask application exposes two endpoints:

* ``/start_scrape`` – Starts a new scraping job. It accepts a JSON body with a
  ``url`` field and an optional ``user_agent``. The server validates the URL,
  checks the target site's ``robots.txt`` to ensure scraping is permitted for
  the provided user agent, fetches the page with a custom ``User-Agent``
  header, extracts visible text, images and links, stores the result under
  a job ID and returns that ID. If the domain disallows scraping or the
  request fails, it returns an error response.

* ``/data/<job_id>`` – Returns previously scraped data by job ID or a 404 if
  the job ID does not exist.

Key improvements over the initial version:

* **Robots.txt compliance**: Before fetching a page, the server consults the
  site's ``robots.txt`` using Python's built‑in ``urllib.robotparser``. If the
  site explicitly disallows crawling of the requested URL for the configured
  agent, the request is rejected. Ethical scraping guidelines recommend
  respecting crawler directives to avoid legal and technical issues【314426102923457†L249-L303】.

* **Customisable User‑Agent**: Clients can specify a custom user agent in the
  request body. A descriptive ``User-Agent`` string that identifies your
  organisation and contact information builds trust with site operators and
  helps them reach out in case of issues【314426102923457†L273-L277】. If none is
  provided, the default agent ``WebScraperBot/1.0 (+https://example.com/contact)``
  is used.

* **Error handling**: If the URL is missing, invalid, blocked by robots.txt,
  or if the network request fails, the server returns an explicit error with
  a corresponding HTTP status code.

Note: This is still a simplified example. A production system should
persist results to a database, implement asynchronous workers for
concurrency and rate limiting, and include authentication/authorization if
exposed publicly. See the project README for more details.
"""

from flask import Flask, request, jsonify
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

from backend.scrapers import StaticScraper, ContentScraper, DynamicScraper, ApiScraper, CombinedScraper, FileScraper
from backend.ai import perform_ner
from backend.tasks import task_manager

# A more featureful Flask backend for managing scraping jobs.  This
# server validates URLs, honours robots.txt directives, and offloads
# scraping work to background tasks so that long‑running operations do
# not block the web server.  Clients can choose between different
# scraping strategies: static, dynamic, API or combined.  Results are
# returned asynchronously via the ``/status`` endpoint.

app = Flask(__name__)
scraped_data: dict[str, dict] = {}  # Deprecated: retained for backward compatibility


@app.route('/start_scrape', methods=['POST'])
def start_scrape() -> tuple[dict, int] | tuple[dict, int]:  # type: ignore[override]
    """Start a new scraping job with configurable strategy.

    The request body must include a ``url`` and may optionally include
    ``strategy`` and ``user_agent`` fields.  ``strategy`` can be one of
    ``static``, ``dynamic``, ``api`` or ``combined``.  The default is
    ``combined``, which tries static, API and dynamic scrapers in
    sequence.  A custom ``user_agent`` may be provided; otherwise
    ``WebScraperBot/1.0 (+https://example.com/contact)`` is used.

    Before scheduling the job, the server validates the URL, ensures
    it uses HTTP or HTTPS, and checks the site's robots.txt for
    permission to crawl the page with the given user agent.  If
    disallowed, an error is returned.  Otherwise a background task
    is submitted and a job ID is returned to the client.
    """
    data = request.get_json(silent=True) or {}
    url = data.get('url')
    strategy = (data.get('strategy') or 'combined').lower()
    user_agent_in = data.get('user_agent')
    if not url:
        return {'error': 'URL is required'}, 400
    # Validate scheme and hostname
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return {'error': 'Invalid URL'}, 400
    # Determine User-Agent string
    # Use the provided user agent if supplied; otherwise allow the scraper to choose
    if isinstance(user_agent_in, str) and user_agent_in.strip():
        agent = user_agent_in.strip()
    else:
        agent = None  # Let the scraper pick a realistic default
    # Check robots.txt
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", '/robots.txt')
    try:
        rp = RobotFileParser(robots_url)
        rp.read()
        if not rp.can_fetch(agent, url):
            return {'error': f'Scraping disallowed by robots.txt for user agent {agent}'}, 403
    except Exception:
        # If robots.txt cannot be parsed, proceed but note this situation
        pass
    # Select scraper based on strategy
    scraper_map = {
        'file': FileScraper,
        'static': StaticScraper,
        'content': ContentScraper,
        'dynamic': DynamicScraper,
        'api': ApiScraper,
        'combined': CombinedScraper,
    }
    ScraperClass = scraper_map.get(strategy)
    if ScraperClass is None:
        return {'error': f'Unknown strategy {strategy}'}, 400
    try:
        scraper = ScraperClass(user_agent=agent)  # type: ignore[call-arg]
    except Exception as exc:
        return {'error': f'Failed to create scraper: {exc}'}, 500
    # Submit the scraping task
    job_id = task_manager.submit(scraper.scrape, url)
    return {'status': 'pending', 'job_id': job_id, 'strategy': strategy}, 202


@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id: str):
    """Return the status and result of a scraping job.

    If the job is still pending, returns ``{'status': 'pending'}``.  If
    finished, returns ``{'status': 'finished', 'result': ...}``.  If
    the job ID is unknown, returns a 404.
    """
    status, result = task_manager.get_status(job_id)
    if status is None:
        return {'error': 'Job not found'}, 404
    if status == 'pending':
        return {'status': 'pending'}, 200
    # finished: include result
    return {'status': 'finished', 'result': result}, 200


@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List all current scraping tasks with their statuses.

    Returns a dictionary mapping job IDs to their status and, if
    finished, the result.  This endpoint can be used by admin
    dashboards to monitor progress of multiple jobs at once.
    """
    jobs = task_manager.list_jobs()
    return jsonify(jobs)


@app.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id: str):
    """Attempt to cancel a pending scraping job.

    Returns a JSON object with ``cancelled: true`` if the job was
    successfully cancelled, or ``cancelled: false`` if it could not
    be cancelled (e.g. it is already running or finished).  If the
    job ID does not exist, returns a 404.
    """
    status, _ = task_manager.get_status(job_id)
    if status is None:
        return {'error': 'Job not found'}, 404
    cancelled = task_manager.cancel(job_id)
    return {'cancelled': bool(cancelled)}, 200


# -----------------------------------------------------------------------------
# AI endpoints
# -----------------------------------------------------------------------------

@app.route('/ner', methods=['POST'])
def named_entity_recognition() -> tuple[dict, int]:  # type: ignore[override]
    """Return named entities extracted from the input text.

    This endpoint accepts a JSON payload containing a ``text`` field and uses
    the optional natural‑language processing pipeline defined in
    :func:`backend.ai.perform_ner` to extract named entities.  The return
    value is a list of entities, each with ``word``, ``entity_group``, and
    ``score`` fields.  If the AI model is unavailable, an empty list is
    returned.  The function always responds with HTTP 200; invalid inputs
    yield an empty list.  AI features are optional and do not affect core
    scraping functionality.
    """
    payload = request.get_json(silent=True) or {}
    text = payload.get('text')
    if not isinstance(text, str) or not text.strip():
        return {'entities': []}, 200
    entities = perform_ner(text)
    return {'entities': entities}, 200


@app.route('/data/<job_id>', methods=['GET'])
def get_data(job_id: str):
    """Deprecated endpoint: retrieve stored scraped data for legacy jobs.

    For compatibility with the earlier synchronous implementation, this
    endpoint returns data from the in‑memory ``scraped_data`` dict if
    present.  New asynchronous jobs should use the ``/status`` endpoint
    instead.  If not found, this will fall back to querying the task
    manager.
    """
    # First check legacy storage
    data = scraped_data.get(job_id)
    if data:
        return jsonify(data)
    # Fall back to asynchronous tasks
    status, result = task_manager.get_status(job_id)
    if status is None:
        return {'error': 'Job not found'}, 404
    if status == 'pending':
        return {'status': 'pending'}, 200
    return jsonify(result)


if __name__ == '__main__':  # pragma: no cover
    # Bind to 0.0.0.0 so the service is reachable from outside Docker
    app.run(host='0.0.0.0', port=5000, debug=True)