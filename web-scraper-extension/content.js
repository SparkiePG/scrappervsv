// Content script injected into every page. It listens for messages from the
// extension's popup and, upon request, extracts useful data from the DOM.

/**
 * Identify the element that likely contains the main article text on a page.
 * This heuristic looks for a parent element of paragraphs (<p>) with the
 * largest total text length. If no suitable candidate is found it falls back
 * to the page body's inner text (truncated).
 * @returns {string} The extracted main text content.
 */
function extractMainText(selector) {
  try {
    // If a specific selector is provided, extract text from matching elements.
    if (selector) {
      let elements;
      try {
        elements = Array.from(document.querySelectorAll(selector));
      } catch (e) {
        elements = [];
      }
      if (elements && elements.length > 0) {
        const combined = elements
          .map((el) => el.innerText.trim())
          .filter((txt) => txt.length > 0)
          .join(' ');
        return combined.substring(0, 20000);
      }
    }
    // No selector or no elements matched; fall back to heuristic extraction.
    const scores = new Map();
    const paragraphs = Array.from(document.querySelectorAll('p'));
    paragraphs.forEach((p) => {
      const len = p.innerText.trim().length;
      if (len < 20) return; // ignore very short paragraphs
      let parent = p.parentElement;
      // Walk up the DOM tree to find a reasonable container
      while (parent && parent !== document.body && !/^(ARTICLE|DIV|MAIN)$/i.test(parent.tagName)) {
        parent = parent.parentElement;
      }
      if (!parent) return;
      const prev = scores.get(parent) || 0;
      scores.set(parent, prev + len);
    });
    let bestElement = null;
    let maxScore = 0;
    scores.forEach((score, element) => {
      if (score > maxScore) {
        maxScore = score;
        bestElement = element;
      }
    });
    const text = bestElement ? bestElement.innerText.trim() : document.body.innerText.trim();
    return text.substring(0, 20000);
  } catch (err) {
    return '';
  }
}

/**
 * Gather basic metadata from the document.
 * Includes title, description, keywords and author if available.
 */
function extractMetadata() {
  const getMeta = (selector) => document.querySelector(selector)?.getAttribute('content') || '';
  return {
    title: document.title || '',
    description: getMeta('meta[name="description"]') || getMeta('meta[property="og:description"]'),
    keywords: getMeta('meta[name="keywords"]'),
    author: getMeta('meta[name="author"]')
  };
}

/**
 * Collect all image sources on the page. Only include absolute URLs to
 * avoid duplicating relative paths.
 */
function extractImages() {
  return Array.from(document.images)
    .map((img) => img.src)
    .filter((src) => !!src);
}

/**
 * Collect all hyperlink targets on the page. Returns the href attribute
 * values for all anchors with a defined href.
 */
function extractLinks() {
  return Array.from(document.querySelectorAll('a[href]'))
    .map((a) => a.href)
    .filter((href) => !!href);
}

// Listener for messages from the extension's popup. When a message with
// action "extractData" is received we gather the various pieces of data and
// respond with an object containing the results. Returning true keeps
// the channel open for asynchronous response.
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request && request.action === 'extractData') {
    const sel = request.selector || null;
    const data = {
      metadata: extractMetadata(),
      mainText: extractMainText(sel),
      images: extractImages(),
      links: extractLinks()
    };
    sendResponse({ data });
    return true;
  }
});