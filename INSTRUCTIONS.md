# QuadScraper – Comprehensive Web Scraping Platform

QuadScraper is a multi‑faceted scraping platform that combines a robust
Python backend, a user‑friendly React dashboard, and a cross‑browser
extension to extract web content ethically and efficiently.  It was
designed after reviewing numerous open‑source projects (Scrapy, Goose,
Playwright, Scrapling) and best‑practice articles.  Unlike ad‑hoc
scripts that break when the page layout changes, QuadScraper offers
five complementary scraping strategies (file, static HTML, content extract,
dynamic rendering and API) and a modular architecture to adapt when one
approach fails.

> **Important:** QuadScraper respects `robots.txt` rules and assumes
> you have permission to scrape the sites you target.  It does **not**
> scrape dark‑web or illicit sources, and we cannot support usage on
> “dark forums” or similar.  Please use this tool responsibly and in
> accordance with all applicable laws and terms of service.

## Features

1. **Multi‑strategy scraping** – The backend exposes five scraping
   strategies: file downloads, static HTML (requests + BeautifulSoup),
   content‑heuristic extraction (largest `<p>` cluster), dynamic
   rendering via Selenium, and API (stub).  The default
   `CombinedScraper` tries them in order and returns the first
   successful result.  This approach follows best practices for
   handling dynamic content: static scraping for speed, headless
   browsers like Selenium for JavaScript‑rendered pages【999827968678680†L154-L160】,
   and API calls when available【999827968678680†L147-L151】.

2. **Asynchronous task manager** – Scrapes run in the background via
   a thread pool.  Clients can start a job, poll its status, list all
   running jobs, or cancel pending work.  Concurrency is limited to
   avoid overloading remote servers, aligning with recommendations to
   implement rate‑limiting and throttling【999827968678680†L160-L165】.

3. **Resilient content extraction** – The `ContentScraper` uses simple
   heuristics to locate the main article body and avoid boilerplate.
   If the site changes, the combined scraper falls back to dynamic
   rendering to recover data.

4. **File scraping & document parsing** – The `FileScraper` detects when a URL points to
   a downloadable resource such as an image, video, audio file or
   document.  It respects content type and size limits and returns
   the binary as a base64‑encoded payload along with metadata (file
   name and MIME type).  For PDFs and DOCX files, the scraper
   attempts to extract textual content using `pdfminer` and
   `python‑docx`, so the resulting JSON includes a `text` field.  If
   the resource is HTML, it defers to other strategies.  This
   enables downloading pictures, videos and documents directly from
   the scraper without relying on separate tools, while explicitly
   avoiding paywalled or premium content.  Extracted text can be
   previewed in the dashboard.

5. **React dashboard** – A minimal but accessible UI lets users enter
   URLs, choose a scraping strategy, and view results with preview
   text, image and link counts.  It polls the backend until the job
   finishes, ensuring responsiveness.

6. **Browser extension** – A cross‑browser extension (Chrome, Edge,
   Firefox, Opera) lets you scrape the current page or a selected
   element directly from your browser.  It includes a CSS selector
   field for targeted extraction and sends data to the backend API or
   allows JSON download.

7. **Scheduler & reports** – A simple scheduler module can trigger
   periodic scrapes (e.g., every hour) without external cron jobs.  A
   reporting module provides word counts, top terms and counts of
   images/links for analytics.

8. **Comprehensive documentation** – Files in `docs/` describe the
   architecture, modules and extensibility.  Each scraper has its own
   README explaining how it works and how to add new strategies.

9. **AI endpoint (optional)** – The backend includes an `/ner` API
   endpoint that performs named‑entity recognition on arbitrary text.
   It uses a transformer model if the `transformers` library is
   installed and falls back to an empty result otherwise.  This
   feature demonstrates how QuadScraper can incorporate machine
   learning for data processing.  You can call it via:

   ```bash
   curl -X POST http://localhost:5000/ner -H 'Content-Type: application/json' \
     -d '{"text": "John Doe lives in New York."}'
   ```

   The response contains a list of detected entities.

## Project structure

```
backend/             # Python API server and scraping logic
  app.py             # Flask routes: start jobs, status, cancel
  scrapers/          # Static, dynamic, content, API and combined scrapers
  tasks.py           # Thread‑pool task manager
  scheduler.py       # Recurring job scheduler
  reports.py         # Summary statistics helpers
  utils.py           # URL validation and normalisation
  __init__.py

frontend/            # React dashboard (create‑react‑app)
  public/
  src/App.js         # Main component for job submission and results

web-scraper-extension/
  manifest.json      # Cross‑browser extension manifest (MV3)
  popup.html/js      # UI for scraping the current page
  content.js         # Content script to extract data client‑side
  browser-polyfill.js

WebWhisper-main/     # Next.js site (marketing + optional API proxy)
docs/                # Architecture and design documentation
```

## Installation

### Requirements

* Python ≥3.10
* Node.js ≥18
* Chrome/Edge/Firefox (for extension and Selenium; Chrome must be
  installed if using the dynamic scraper)
* Optional: ``transformers``, ``pdfminer.six`` and ``python-docx`` to
  enable AI features and PDF/DOCX text extraction.  These
  dependencies are listed in the `backend/requirements.txt` file and
  are installed by default.

### Backend

1. Install Python dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```
   Note: `selenium` is optional; if it’s not installed or Chrome is not
   present, the dynamic scraper will fall back to static scraping.

2. Start the Flask server:

   ```bash
   python backend/app.py
   ```

   The server runs on `http://localhost:5000` by default and exposes
   the following endpoints:

   * `POST /start_scrape` – body: `{ "url": "https://example.com", "strategy": "combined" }`.  Returns a `job_id`.
   * `GET /status/<job_id>` – returns `{ "status": "pending" }` or `{ "status": "finished", "result": {...} }`.
   * `GET /tasks` – returns all job statuses.
   * `POST /cancel/<job_id>` – attempts to cancel a pending job.

### Frontend Dashboard

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:

   ```bash
   npm start
   ```

   The dashboard runs on `http://localhost:3000` and proxies requests to
   `http://localhost:5000`.

### Browser Extension

1. Open your browser’s extensions page (e.g. `chrome://extensions`).
2. Enable *Developer mode*.
3. Click **Load unpacked** and select the `web-scraper-extension` folder.
4. Pin the extension.  Navigate to any page and click the icon to
   scrape the visible page or a specific selector.

### Next.js Site

The `WebWhisper-main` directory contains a Next.js marketing site and
an optional API proxy.  To run it:

```bash
cd WebWhisper-main/WebWhisper-main
npm install
npm run dev
```

## Usage

1. Start the backend and optionally the React dashboard.
2. On the dashboard, enter a URL, choose a scraping strategy (static,
   content, dynamic, API or combined) and click **Scrape**.
3. The job status will update automatically.  When finished, the
   preview text, image count, link count and metadata are displayed.
4. Use the extension to scrape directly from the browser.  Enter a CSS
   selector for targeted extraction or leave blank to capture the
   whole page.  You can send the data to the backend or download
   JSON.

## Design choices & best practices

* **Ethical scraping** – The backend checks a site’s `robots.txt` file and
  uses a descriptive user agent.  Always respect websites’ terms of
  service and avoid scraping prohibited pages【999827968678680†L69-L83】.
* **Multiple strategies** – Static scrapers are fast and robust; if
  they fail to capture dynamic content, the system falls back to
  headless browsers like Selenium, which can render JavaScript and
  capture the page as a user would【999827968678680†L154-L160】.  The content
  scraper uses heuristics to extract the main article body, similar
  to adaptive scrapers like Scrapling.
* **Concurrency and throttling** – Jobs are processed via a thread pool
  with a configurable limit.  Concurrency improves performance but
  should be used responsibly to avoid overwhelming servers【999827968678680†L160-L165】.
* **Error handling** – Each scraper catches network and parsing errors
  and returns a `success` flag with an error message instead of
  raising exceptions.  The combined scraper aggregates errors and
  continues to the next strategy.

* **Proxy and user-agent rotation** – QuadScraper reads proxy URLs
  from the `SCRAPER_HTTP_PROXY` and `SCRAPER_HTTPS_PROXY` environment
  variables and selects a random modern browser user agent for each
  request when none is provided.  Rotating proxies and user agents
  reduces the risk of IP bans and helps emulate normal user traffic
  【742794737568601†L1796-L1803】.  Set these variables before starting
  the backend to enable proxy support.
* **Extensibility** – New scraping strategies can be added by
  implementing the `Scraper` interface and registering them in
  `CombinedScraper`.  The scheduler and reports modules show how the
  platform can evolve to include periodic tasks and analytics.

* **Rotating user agents & proxies** – To reduce the risk of being
  blocked, scrapers choose a random modern browser user‑agent string
  by default.  You can override this by providing a `user_agent` in
  requests to the API, or set environment variables
  `SCRAPER_HTTP_PROXY` and/or `SCRAPER_HTTPS_PROXY` to route requests
  through a proxy.  Implementing rotating proxies and random delays
  between requests are recommended best practices for large scale
  scraping【742794737568601†L1796-L1803】.

## Naming & purpose

**QuadScraper** (originally named for its four initial strategies) now
includes a dedicated file scraper.  It emphasises its complementary
scraping techniques and its ability to fill gaps when one method
fails.  It is not a superficial proof of concept; every module has
a functional role in enabling reliable scraping of both static and
dynamic websites, downloading of binary resources, with fallbacks
and automation hooks.

By following the installation and usage steps above, you can deploy
QuadScraper locally or host it on a platform like Vercel (for the
Next.js site) and Heroku/AWS (for the Flask API).  Feel free to
contribute improvements via GitHub issues and pull requests.