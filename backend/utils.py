"""
Utility functions for URL validation and normalisation.

These helpers ensure that URLs supplied to the scraping API are well
formed and safe to use.  They encapsulate common parsing logic,
reducing duplication in the API endpoints and scrapers.

Functions
---------

``is_valid_url(url: str) -> bool``
    Returns ``True`` if the given string looks like a valid HTTP or
    HTTPS URL.  This performs a basic syntax check using
    ``urllib.parse.urlparse`` and rejects empty hosts or unsupported
    schemes.

``normalize_url(url: str) -> str``
    Returns a normalised version of the URL: scheme and host in
    lowercase, default ports removed, and redundant path segments
    resolved.  If the input is not a valid URL, it is returned
    unchanged.

``get_base_domain(url: str) -> str | None``
    Returns the registered domain portion of the URL (e.g. ``example.com``
    from ``https://sub.example.com/path``), or ``None`` if the URL
    cannot be parsed.  Useful for applying domain‑specific rules.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse
from typing import Optional

try:
    # Use tldextract if available for accurate domain extraction
    import tldextract  # type: ignore
except Exception:
    tldextract = None


def is_valid_url(url: str) -> bool:
    """Return True if the string appears to be a valid HTTP/S URL."""
    if not isinstance(url, str) or not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def normalize_url(url: str) -> str:
    """Normalise the URL by lowercasing scheme and host and stripping default ports."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        # Remove default ports
        if (scheme == 'http' and netloc.endswith(':80')):
            netloc = netloc[:-3]
        elif (scheme == 'https' and netloc.endswith(':443')):
            netloc = netloc[:-4]
        # Resolve path: remove duplicate slashes
        path = re.sub(r'/+', '/', parsed.path)
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        return url


def get_base_domain(url: str) -> Optional[str]:
    """Return the registered domain for the given URL, if possible."""
    if not is_valid_url(url):
        return None
    if tldextract:
        ext = tldextract.extract(url)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
    # Fallback: return hostname without subdomains
    parsed = urlparse(url)
    host = parsed.hostname or ''
    parts = host.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return host or None

# ---------------------------------------------------------------------------
# Proxy configuration helpers
# ---------------------------------------------------------------------------

import os
from typing import Dict, Optional

import random

_USER_AGENTS = [
    # A selection of modern desktop browser user agents (as of 2025/2026)
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0 Mobile/16A5357b Safari/604.1',
]

def get_default_user_agent() -> str:
    """
    Return a realistic, randomly chosen User‑Agent string.  Rotating user
    agents can help disguise the scraper as different browsers and reduce
    the risk of being blocked or detected【764700871765204†L194-L204】.  If the list
    of user agents is empty, a generic identifier is returned.
    """
    if not _USER_AGENTS:
        return 'WebScraperBot/1.0 (+https://example.com/contact)'
    return random.choice(_USER_AGENTS)

def get_proxy_dict() -> Optional[Dict[str, str]]:
    """
    Return a dictionary of proxies to pass to ``requests`` or ``aiohttp`` based
    on environment variables.  The following variables are checked:

    * ``SCRAPER_HTTP_PROXY`` or ``HTTP_PROXY`` – proxy URL for HTTP requests.
    * ``SCRAPER_HTTPS_PROXY`` or ``HTTPS_PROXY`` – proxy URL for HTTPS requests.

    If neither variable is set, returns ``None``.  This allows the caller to
    omit the ``proxies`` parameter entirely.  Proxy URLs should include the
    scheme and host (and optionally port), e.g. ``http://proxy.example.com:8080``.

    Examples
    --------
    >>> os.environ['SCRAPER_HTTP_PROXY'] = 'http://localhost:3128'
    >>> get_proxy_dict()
    {'http': 'http://localhost:3128', 'https': 'http://localhost:3128'}
    """
    http_proxy = os.environ.get('SCRAPER_HTTP_PROXY') or os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('SCRAPER_HTTPS_PROXY') or os.environ.get('HTTPS_PROXY')
    if not http_proxy and not https_proxy:
        return None
    proxies: Dict[str, str] = {}
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy
    # If only one proxy is provided, use it for both schemes
    if not https_proxy and http_proxy:
        proxies['https'] = http_proxy
    if not http_proxy and https_proxy:
        proxies['http'] = https_proxy
    return proxies