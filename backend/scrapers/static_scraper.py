"""
StaticScraper: fetch and parse static HTML pages.

This scraper uses the ``requests`` library to retrieve the page and
``BeautifulSoup`` to parse the HTML.  It extracts visible text, image
sources and hyperlink targets.  It respects robots.txt via the base
scraper API and can set a custom user agent.  If an error occurs
during fetching or parsing, ``success`` will be ``False`` and an
``error`` message will be included.
"""

from __future__ import annotations

import logging
from typing import Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .base import Scraper
from backend.utils import get_proxy_dict


logger = logging.getLogger(__name__)


class StaticScraper(Scraper):
    """Scraper for static HTML pages using Requests and BeautifulSoup."""

    name = "static"

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
            proxies = get_proxy_dict() or {}
            resp = requests.get(url, headers=headers, timeout=20, proxies=proxies)
            resp.raise_for_status()
        except Exception as exc:
            result["error"] = f"Request failed: {exc}"
            logger.warning("StaticScraper failed to fetch %s: %s", url, exc)
            return result
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Text extraction: join visible text and truncate
            text = soup.get_text(separator=" ", strip=True)[:50000]
            images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
            links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
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
            logger.exception("StaticScraper failed to parse %s", url)
            return result