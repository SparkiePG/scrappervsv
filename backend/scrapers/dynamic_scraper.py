"""
DynamicScraper: render pages with JavaScript and extract content.

This scraper attempts to use Selenium with a headless Chrome/Chromium
driver to load pages that require JavaScript to render their content.  If
Selenium is not installed or a driver cannot be created, it falls back
to the :class:`StaticScraper` so that scraping still proceeds.

Because browsers are heavyweight, this scraper is only used when
explicitly requested or when other scrapers fail.  In a production
environment you might prefer Pyppeteer or Playwright.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from bs4 import BeautifulSoup

from .base import Scraper
from .static_scraper import StaticScraper

logger = logging.getLogger(__name__)


class DynamicScraper(Scraper):
    """Scraper that uses Selenium to render dynamic pages."""

    name = "dynamic"

    def __init__(self, user_agent: str | None = None) -> None:
        super().__init__(user_agent=user_agent)
        # Use a static scraper as fallback
        self._fallback = StaticScraper(user_agent)

    def scrape(self, url: str) -> Dict[str, Any]:
        try:
            from selenium import webdriver  # type: ignore
            from selenium.webdriver.chrome.options import Options  # type: ignore
        except Exception as exc:  # ImportError or other
            logger.info("Selenium not available; falling back to static scraping")
            return self._fallback.scrape(url)
        # Configure headless browser
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        # Set the user agent string
        options.add_argument(f'user-agent={self.user_agent}')
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as exc:
            logger.warning("Could not start Selenium Chrome driver: %s", exc)
            return self._fallback.scrape(url)
        try:
            driver.set_page_load_timeout(30)
            driver.get(url)
            html = driver.page_source
        except Exception as exc:
            logger.warning("Selenium failed to load %s: %s", url, exc)
            return self._fallback.scrape(url)
        finally:
            try:
                driver.quit()
            except Exception:
                pass
        # Parse the rendered HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)[:50000]
            images = [img.get('src') for img in soup.find_all('img') if img.get('src')]
            links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
            metadata = {
                'title': soup.title.string.strip() if soup.title and soup.title.string else '',
                'description': '',
                'keywords': '',
                'author': '',
            }
            def get_meta(name: str) -> str:
                tag = soup.find('meta', attrs={'name': name})
                if tag and tag.get('content'):
                    return tag['content']
                tag = soup.find('meta', attrs={'property': f'og:{name}'})
                if tag and tag.get('content'):
                    return tag['content']
                return ''
            metadata['description'] = get_meta('description')
            metadata['keywords'] = get_meta('keywords')
            metadata['author'] = get_meta('author')
            return {
                'success': True,
                'text': text,
                'images': images,
                'links': links,
                'metadata': metadata,
            }
        except Exception as exc:
            logger.exception("DynamicScraper failed to parse %s", url)
            return self._fallback.scrape(url)