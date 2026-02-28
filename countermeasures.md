# Countermeasures and Contingency Plans for QuadScraper

QuadScraper is a multi‑component project composed of a Next.js front‑end, a Python/Flask back‑end, a React dashboard and a cross‑browser extension.  Because it pulls together several technologies, problems can arise at many layers – from build and lint failures to runtime errors and scraping limitations.  This document summarises common classes of errors you might encounter and provides countermeasures based on published guidelines and best practices.  The goal is to help you debug issues quickly and design fallbacks so the application continues to work even when one component fails.

## 1 Next.js build and runtime errors

### ESLint rule not found

**Symptoms:** During `next build` Vercel fails with an error similar to:

```
Error: Definition for rule '@typescript-eslint/no-unused-vars' was not found.
```

This happens because the project’s `.eslintrc` refers to a rule provided by `@typescript-eslint/eslint-plugin` but the plugin is not installed.  Countermeasures:

1. **Install the plugin** – Add `@typescript-eslint/eslint-plugin` (and its peer `@typescript-eslint/parser`) to your `devDependencies` and run `npm install`.
2. **Disable the rule** – Remove the rule from `.eslintrc` or set `ignoreDuringBuilds: true` in `next.config.js` so ESLint errors don’t block production builds.  The official Next.js docs show how to disable ESLint during builds by setting `eslint.ignoreDuringBuilds` to `true`【842070507737832†L467-L479】.
3. **Fallback plan:** Add a root‑level `next.config.js` with `ignoreDuringBuilds: true`.  This allows the build to succeed while you sort out linter dependencies.

### Window or document undefined

Server‑rendered code runs in Node.js, which doesn’t have the browser’s `window` or `document` objects.  Attempting to access them directly results in a `document is not defined` or `window is not defined` error.  The Sentry blog advises wrapping such code in a `useEffect` hook or using dynamic imports with SSR disabled so the code only executes in the browser【441668669940349†L585-L592】.

### Invalid URL in middleware

If you see `TypeError: Invalid URL` in middleware or API routes, ensure that the host name is explicitly provided.  According to Sentry’s guide, this error often occurs when the server host URL is missing; you can resolve it by specifying the hostname in your server configuration【441668669940349†L594-L607】.

### Middleware not executed

Middleware files must be placed correctly.  For Next.js 12.2 and later the file should be named `middleware.js` at the project root.  Earlier versions used `_middleware.js` inside the `pages` directory【441668669940349†L609-L615】.  Ensure file names and locations match your Next.js version.

### Static generation errors

If you use `getStaticProps` for server‑side generation but forget to define `getStaticPaths`, Next.js will throw `getStaticPaths is required`.  Define the missing function when using dynamic routes【441668669940349†L618-L620】.

### Module not found

Importing server‑side modules (e.g. `fs`, `path` or Node‑only libraries) into client components triggers a “Module not found” error.  The fix is to move such imports into server‑side code (e.g. `getServerSideProps`, API routes) or configure webpack to polyfill them【441668669940349†L622-L628】.

### CORS errors

When an external site or your own front end calls a Next.js API route from a different origin, the browser may block the request.  To resolve CORS issues, install the CORS middleware (e.g. `cors` package) and enable cross‑origin sharing in your API route【441668669940349†L630-L641】.

### Runtime timeouts and 10 second limits

Vercel’s serverless functions default to 10 second execution time.  Long scrapes may time out.  Countermeasures:

* Reduce the amount of work done in a single request; break large tasks into smaller jobs processed asynchronously in the Python backend.
* Increase the maximum duration in `vercel.json` (e.g. `"maxDuration": 25`) if your plan allows longer functions.
* Return a job ID immediately and poll for results from the client.

### Dynamic import errors

Our API route dynamically imports `groq-sdk` only if the user chooses the Groq provider.  This prevents build failures when the package is absent.  Always guard dynamic imports with try/catch and return a clear error message when optional dependencies are missing.

## 2 Node/NPM and dependency issues

### Deprecated or vulnerable packages

During installation, npm may warn that certain packages (e.g. `glob@7.2.3`, `rimraf@3.0.2`, `inflight@1.0.6`) are deprecated.  Keep dependencies up to date by running `npm update` periodically.  In CI, enable `npm audit` to identify vulnerable packages.

### Lockfile and module cache corruption

If a build fails due to missing modules even after installing dependencies, delete the `.next` directory and `node_modules` then reinstall with `npm install`.  Some developers also remove `package-lock.json` when upgrading major versions.

### Incompatible Node/Next.js versions

Next.js 14 (used here) may have breaking changes with older plugins.  Check the `next` release notes and update your dependencies accordingly.  If you cannot upgrade, pin your dependencies to compatible versions.

## 3 Front‑end and UI errors

### Invalid JSX or Tailwind classes

Linting and build errors can occur when JSX is malformed (e.g. stray opening tags, comments inside returned expressions) or Tailwind classes are incomplete.  In our case, the `ResultsPreview` component returned a JSX fragment with a comment before the `<div>`, causing a parsing error.  Fix by moving comments outside JSX and wrapping elements in a single return statement.

### Hydration mismatches

Hydration errors appear when client‑side rendered markup does not match the server’s HTML.  They often arise from using browser‑only code (like `localStorage`) during server rendering.  Use the `useEffect` hook or dynamic imports to avoid executing such code on the server【441668669940349†L585-L592】.

### Large bundles and slow loads

Avoid importing heavy dependencies (e.g. Cheerio, Puppeteer) in front‑end components.  Instead, use API routes or the Python backend for scraping work.  Use dynamic imports or code splitting for optional features to keep the bundle size small.

### Accessibility issues

Adhere to WCAG guidelines for colour contrast and keyboard accessibility.  For example, text should have at least a 4.5:1 contrast ratio for normal text【560140671448684†L29-L47】; place important information in the first 5 seconds of user scanning and limit the number of simultaneous visualisations【26356401491938†L138-L166】【26356401491938†L180-L187】.

## 4 Python backend and scraping errors

### Missing dependencies

Ensure all required Python libraries (`requests`, `beautifulsoup4`, `pdfminer`, `python-docx`) are listed in `backend/requirements.txt`.  A `ModuleNotFoundError` indicates a missing dependency.  Install them with `pip install -r requirements.txt` or use a virtual environment.

### Network and HTTP errors

The backend interacts with arbitrary websites.  Common failures include:

* **Connection timeouts:** websites may be slow or blocking.  Use the `timeout` parameter in `requests.get()` and catch `requests.exceptions.Timeout` to abort gracefully.
* **Invalid URLs:** Validate input URLs with Python’s `urllib.parse` or `new URL` in JavaScript before scraping.
* **HTTP 4xx/5xx responses:** Return informative error messages to the client; avoid infinite retries.
* **SSL errors:** Some sites require TLS 1.3 or have invalid certificates.  Set `verify=False` only when absolutely necessary; otherwise handle `SSLError` gracefully.

### Respecting `robots.txt` and rate limits

Web scraping should honour sites’ `robots.txt` files.  Use Python’s `urllib.robotparser` to check whether the user‑agent is allowed to access a URL.  Implement request throttling and exponential backoff to avoid hitting rate limits.  Rotating proxies and random delays help distribute load across IP addresses, as recommended by scraping best practices【742794737568601†L1796-L1803】.

### Dynamic content and JavaScript rendering

When pages rely on client‑side JavaScript, static HTML parsing may return little or no data.  The dynamic scraper uses headless browsers to render the page; however, headless browsers are heavier and may fail in serverless environments.  Provide a fallback: first attempt static scraping; if no meaningful text is extracted, try the dynamic scraper; if that also fails or times out, return an informative error.

### File and media scraping

Our `FileScraper` downloads files up to a size limit and attempts to extract text from PDFs and DOCX documents.  Potential errors include files larger than the configured limit, unsupported MIME types, or conversion failures.  In these cases, return metadata (file name and type) and allow the user to download the raw file, but clearly state that content extraction failed.  Never attempt to bypass authentication or paywalls; scraping protected or premium content without permission is illegal【510108747246327†L93-L100】.

### Concurrency and job management

Running many scraping jobs concurrently can exhaust resources or trigger rate limits.  Use Python’s `ThreadPoolExecutor` with a controlled number of workers and queue jobs.  Monitor CPU and memory usage and scale horizontally if needed.  For long‑running jobs, return a job ID and allow the front end to poll for completion.

## 5 Puppeteer and headless browser errors

When incorporating a Node.js scraping layer using **Puppeteer** (for example, to handle dynamic content client‑side or as part of a Chrome extension), several pitfalls can derail your scraper.  A blog on Puppeteer antipatterns highlights common mistakes and their remedies:

* **Navigation timeouts** – By default, `page.goto()` will timeout after 30 seconds if the page fails to load, causing `Navigation Timeout Exceeded` errors.  Pass a larger `timeout` option (e.g., 60000) to increase the limit【227580035605949†L50-L60】.  You can also use `page.waitForNavigation()` or `waitUntil: 'networkidle0'` to wait for network quiet.

* **Returning DOM elements from `evaluate`** – The `page.evaluate()` function runs in the browser context and cannot serialize complex DOM objects back to Node; attempting to return a DOM node results in an empty object.  Use `page.$()` or `page.evaluateHandle()` to obtain an `ElementHandle`, then operate on it in the browser context【51899025257707†L174-L224】.

* **Undefined variables inside `evaluate`** – Variables defined in Node are not in scope in the browser context; referencing them inside the callback results in `ReferenceError`.  Pass variables as additional arguments to `evaluate` or embed them in the callback string【51899025257707†L233-L281】.

* **Headful vs headless differences** – Some websites behave differently when rendered headless.  Use headful mode (`headless: false`) during debugging to replicate real browser behaviour and adjust wait conditions accordingly【51899025257707†L294-L309】.

* **Memory leaks and concurrency** – Launching many pages simultaneously can exhaust memory.  Close unused `ElementHandle`s and `pages`, reuse browser instances, and avoid doing too much work in parallel【51899025257707†L294-L309】.

* **Fallback plan** – If Puppeteer continues to fail (e.g., due to anti‑bot protections), fall back to the Python dynamic scraper or a serverless API such as Playwright‑based services.  Always implement try/catch around Puppeteer calls and return informative errors rather than crashing the process.

## 6 Cheerio and HTML parsing errors

When using **Cheerio** for server‑side HTML parsing, errors often stem from poorly scoped selectors or unhandled exceptions.  A Node development blog outlines several strategies【651638158556391†L90-L205】:

* **Use granular try/catch blocks** – Wrap individual extraction steps in their own try/catch rather than wrapping the entire scrape.  This localises errors and makes debugging easier【651638158556391†L98-L127】.

* **Debugging tools** – Enable Cheerio’s debug mode and use a logging library like `winston` to capture detailed logs of the HTML being processed【651638158556391†L148-L176】.

* **Handle missing elements gracefully** – Always check whether a selector returns a result before accessing its properties.  Use default values or return `null` when elements are absent【651638158556391†L186-L205】.

* **Maintenance practices** – Document your selector patterns and expected outputs, set up monitoring for failed scrapes, create test cases with sample HTML, and regularly validate data.  Web pages change; adapt your parsers accordingly【651638158556391†L209-L217】.

## 7 Proxy rotation and user agents

Anti‑scraping measures such as IP blocking, CAPTCHAs and geo‑restriction can hinder scraping.  A guide on rotating proxies explains why a pool of IP addresses is essential for large‑scale scraping and offers best practices【894727041085380†L41-L54】:

* **Avoid bans and CAPTCHAs** – Rotating your IP for each request makes your traffic resemble many different users【894727041085380†L42-L48】.  Combine this with user‑agent rotation to present different browser identities【742794737568601†L1796-L1803】.

* **Scale operations** – With thousands of IPs, you can distribute requests across the pool to scrape at scale without hitting rate limits【894727041085380†L93-L112】.

* **Geographic targeting** – Using proxies based in different countries allows you to collect location‑specific data【894727041085380†L113-L118】.

In QuadScraper, the backend reads proxy URLs from `SCRAPER_HTTP_PROXY` and `SCRAPER_HTTPS_PROXY` environment variables and picks a random user agent for each request.  Set these variables before starting the server to enable rotation.

## 8 Node.js runtime errors

Node applications are subject to numerous system errors.  A Node error guide catalogues common issues and fixes【870380548584824†L110-L134】:

* **Heap out of memory** – When processing large datasets or high concurrency, Node may exhaust its default heap (approx. 2 GB).  Identify leaks, process data in streams, or increase the heap via `--max-old-space-size`【870380548584824†L110-L134】.

* **Connection reset (ECONNRESET)** – Indicates a peer closed the connection unexpectedly.  Retry the request with exponential backoff or handle partial responses gracefully【870380548584824†L161-L166】.

* **Address in use (EADDRINUSE)** – Another process is already using the port.  Terminate the conflicting process or configure your server to listen on a different port.

* **DNS lookup failures (ENOTFOUND)** – The domain cannot be resolved.  Validate URLs before scraping and ensure network connectivity.

* **File system errors (ENOENT, EISDIR, ENOTDIR)** – Occur when reading/writing files in the wrong location or with incorrect paths.  Check path inputs and ensure proper permissions.

Adhering to proper error handling patterns – using `try/catch`, validating inputs, closing resources, and writing unit tests – will prevent most of these issues.

## 5 Chrome extension and browser APIs

### Manifest configuration errors

Browser stores expect a valid `manifest.json`.  Common issues include missing icons, invalid version numbers, unsupported permissions or manifest version mismatches.  Ensure the manifest declares all required icons (16, 32, 48, 128 px for Chrome; additional sizes for Firefox and Edge) and uses `manifest_version: 3`.  When adding permissions, request only what you need (e.g. `activeTab`, `scripting`, `downloads`) to avoid rejection.

### Cross‑origin restrictions

Content scripts cannot fetch arbitrary URLs due to the browser’s same‑origin policy.  Use background scripts or your server’s API to fetch external resources.  For example, the extension can send messages to the backend which performs the scrape and returns results.

### Browser compatibility

Although the extension is built with Manifest V3, different stores have slightly different requirements (Edge requires a `300×300` logo and at least one screenshot【569765340323826†L525-L567】; Firefox allows SVG icons but recommends providing 32 × 32 px and 64 × 64 px PNGs【587435394203988†L189-L214】).  Test the extension in each target browser and adjust the manifest and assets accordingly.

### Plan B: Stand‑alone front end

If the extension is rejected or fails to work in a particular browser, users can still run the React dashboard (in `frontend/`) to interact with the Python backend.  This ensures the scraping functionality remains accessible.

## 6 Deployment and infrastructure

### Environment variables and secrets

Missing API keys or misconfigured environment variables can break third‑party provider integrations (e.g. OpenAI or Groq).  Use Vercel’s dashboard to set environment variables securely.  In the API route, provide clear error messages when required keys are absent.

### Build caching and cold starts

Vercel caches dependencies across builds; if caches are stale or corrupted, builds may fail.  Clearing caches or triggering a clean deployment often resolves inexplicable build errors.  Use environment‑aware logging to identify which stage fails (installation, compilation or runtime).

### Monitoring and alerts

Deploy a monitoring tool like Sentry or New Relic to capture runtime errors in production.  Real‑time alerts enable quick response when errors occur and help track the frequency and root cause of issues【441668669940349†L585-L592】.

## Summary

By anticipating these classes of errors and implementing the recommended countermeasures, you can make QuadScraper resilient across different environments.  Key strategies include installing the correct ESLint plugins or disabling linting during builds, carefully handling browser‑only APIs in server code, respecting website rate limits and `robots.txt`, providing dynamic scraping fallbacks, and maintaining minimal permissions in the extension manifest.  Always stay within legal bounds – avoid scraping copyrighted or paywalled content without permission【510108747246327†L93-L100】 – and use monitoring tools to detect issues early.  Having clear fallback paths (stand‑alone backend, separate dashboard, dynamic vs static scraping) ensures that your users can still obtain data when one component fails.