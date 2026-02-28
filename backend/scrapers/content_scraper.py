"""
ContentScraper: extract the main article text from a page using heuristics.

This scraper attempts to identify the primary content of a web page
by locating the DOM element containing the largest amount of
paragraph text.  It is inspired by libraries such as Goose and
readability.js but implemented here using only BeautifulSoup.  The
goal is to return a more coherent body of text than the brute‑force
approach of :class:`StaticScraper`, which concatenates all text on
the page.

Algorithm
---------

1. Fetch the page with ``requests`` using the configured user agent.
2. Parse the HTML with ``BeautifulSoup``.
3. Find all elements that contain at least one ``<p>`` tag.
4. For each candidate element, compute the combined length of text in
   its ``<p>`` descendants.
5. Select the element with the maximum text length.  If none are
   found, fall back to the entire document body.
6. Extract the text from the selected element, as well as images and
   links contained within it.
7. Return a result dict as for other scrapers.

This approach provides a better "article extract" than simply
concatenating all text, but it is a heuristic and may fail for
pages with unusual structures.  It should therefore be used as a
middle ground between the static and dynamic scrapers.

Note: We do not use third‑party libraries like ``readability-lxml``
here to keep the dependencies minimal and avoid licensing issues.
However, if available, such libraries can provide more accurate
extraction and could be integrated in a future revision.
"""

from __future__ import annotations

import logging
from typing import Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .base import Scraper

logger = logging.getLogger(__name__)


class ContentScraper(Scraper):
    """Scraper that extracts the main article content using heuristics."""

    name = "content"

    def scrape(self, url: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": False,
            "text": "",
            "images": [],
            "links": [],
            "metadata": {},
        }
        try:
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            result["error"] = f"Request failed: {exc}"
            logger.warning("ContentScraper failed to fetch %s: %s", url, exc)
            return result
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Attempt to find the main content element
            candidates = []
            for elem in soup.find_all():
                # Only consider elements with at least one <p>
                if elem.find("p"):
                    text_length = sum(len(p.get_text(strip=True)) for p in elem.find_all("p"))
                    if text_length > 0:
                        candidates.append((text_length, elem))
            # Select the candidate with maximum text
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                main_elem: Tag = candidates[0][1]
            else:
                # Fallback to entire body or document
                main_elem = soup.body or soup
            # Extract text, images and links from the selected element
            text = main_elem.get_text(separator=" ", strip=True)[:50000]
            images = [img.get("src") for img in main_elem.find_all("img") if img.get("src")]
            links = [a.get("href") for a in main_elem.find_all("a") if a.get("href")]
            metadata = {
                "title": soup.title.string.strip() if soup.title and soup.title.string else "",
                "description": "",
                "keywords": "",
                "author": "",
            }
            # Fill description, keywords, author if available
            def get_meta(name: str) -> str:
                tag = soup.find("meta", attrs={"name": name})
                if tag and tag.get("content"):
                    return tag["content"]
                tag = soup.find("meta", attrs={"property": f"og:{name}"})
                if tag and tag.get("content"):
                    return tag["content"]
                return ""
            metadata["description"] = get_meta("description")
            metadata["keywords"] = get_meta("keywords")
            metadata["author"] = get_meta("author")
            result.update({
                "success": True,
                "text": text,
                "images": images,
                "links": links,
                "metadata": metadata,
            })
            return result
        except Exception as exc:
            result["error"] = f"Parsing failed: {exc}"
            logger.exception("ContentScraper failed to parse %s", url)
            return result