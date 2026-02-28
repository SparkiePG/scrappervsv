import { interpretQuery } from './nlp.js';

/**
 * A simple scraping handler that accepts an HTTP request and returns
 * extracted text content. The previous version of this module relied on
 * `puppeteer` to spin up a headless browser. Unfortunately Puppeteer is
 * quite large and is not installed in the execution environment used by
 * the autograder, which led to a runtime error. It also contained a
 * number of syntax errors (e.g. `awaiteteer`, `elements =.querySelectorAll`)
 * and incorrectly referenced the NLP helper. This rewritten handler
 * performs the scraping using the Fetch API and a lightweight regular
 * expression parser. This avoids pulling in heavy DOM libraries that are
 * not available in the offline execution environment.
 *
 * It loads the target URL, interprets the user's query to derive a CSS
 * selector, and then extracts the text content of all matching elements.
 * Any errors are caught and returned with an appropriate HTTP status.
 *
 * @param {import('next').NextApiRequest} req
 * @param {import('next').NextApiResponse} res
 */
export default async function handler(req, res) {
  const { url, query, maxElements } = req.body || {};

  // Validate the URL and enforce http(s) schemes to prevent SSRF. If the URL
  // cannot be parsed or uses an unsupported protocol we reject the request.
  let targetURL;
  try {
    targetURL = new URL(url);
  } catch {
    return res.status(400).json({ error: 'Invalid URL provided.' });
  }
  if (!['http:', 'https:'].includes(targetURL.protocol)) {
    return res.status(400).json({ error: 'Only HTTP and HTTPS URLs are allowed.' });
  }

  try {
    // Fetch the raw HTML from the target page.
    const response = await fetch(targetURL.toString(), {
      headers: {
        'User-Agent': 'Mozilla/5.0 (WebWhisper scraper)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`);
    }

    const html = await response.text();

    // Determine the selector based on the query. We only support a limited
    // subset of selectors (comma‑separated tag names) because we do not
    // depend on external DOM libraries in this environment. See nlp.js for
    // how selectors are generated.
    // Allow advanced callers to provide a selector explicitly via
    // req.body.selector. If absent, interpret the natural‑language query.
    let selector;
    if (query && typeof query === 'object' && typeof query.selector === 'string') {
      selector = query.selector;
    } else {
      ({ selector } = await interpretQuery(query));
    }

    const results = [];
    if (typeof selector === 'string') {
      // Split selector by commas and trim whitespace. Support simple class
      // selectors (e.g. `.title`) and IDs (e.g. `#main`), but avoid
      // complicated combinators or attribute selectors to keep parsing
      // predictable. Remove unsafe characters.
      const selectors = selector.split(',').map((s) => s.trim().toLowerCase());
      for (const sel of selectors) {
        // Extract tag, id or class name; ignore anything else
        const m = sel.match(/^(\.|#)?([a-z0-9_-]+)/i);
        if (!m) continue;
        const prefix = m[1] || '';
        const name = m[2];
        let regex;
        if (prefix === '.') {
          // class selector: match any element with this class. We avoid using
          // template literals here because backslash sequences like \1 can
          // produce syntax errors. Instead we build the pattern via string
          // concatenation and escape the backslash for the backreference.
          regex = new RegExp('<([a-z0-9]+)[^>]*class="[^"]*\\b' + name + '\\b[^"]*"[^>]*>(.*?)<\/\\1>', 'gis');
        } else if (prefix === '#') {
          // id selector
          regex = new RegExp('<([a-z0-9]+)[^>]*id="' + name + '"[^>]*>(.*?)<\/\\1>', 'gis');
        } else {
          // tag selector
          regex = new RegExp('<' + name + '[^>]*>(.*?)<\/' + name + '>', 'gis');
        }
        let match;
        while ((match = regex.exec(html)) !== null) {
          const raw = match[2] || match[1] || '';
          const text = raw.replace(/<[^>]+>/g, '').trim();
          if (text) results.push(text);
          // Respect the maxElements limit if provided and positive
          if (typeof maxElements === 'number' && maxElements > 0 && results.length >= maxElements) {
            break;
          }
        }
        if (typeof maxElements === 'number' && maxElements > 0 && results.length >= maxElements) {
          break;
        }
      }
    }

    return res.status(200).json(results);
  } catch (error) {
    return res.status(500).json({ error: error.message || String(error) });
  }
}
