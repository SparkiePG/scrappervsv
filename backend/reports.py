"""
Reporting utilities for scraped data.

This module provides helper functions to summarise the results of a
scraping job.  Although the API returns raw text, images and links,
it can be useful to derive additional metrics for analytics and
monitoring.  The functions here operate on the result dicts
returned by scrapers and return lightweight summaries.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Any, List


def word_count(text: str) -> int:
    """Return the number of words in the given text."""
    return len(re.findall(r'\b\w+\b', text))


def top_words(text: str, n: int = 10) -> List[tuple[str, int]]:
    """Return the ``n`` most common words in the text.

    Words shorter than three characters are ignored.  The
    implementation uses a case‑insensitive counter.
    """
    words = re.findall(r'\b\w{3,}\b', text.lower())
    counts = Counter(words)
    return counts.most_common(n)


def summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary of a scraping result.

    The summary includes the total word count, number of images,
    number of links, and the top ten words.  It does not modify
    the input result.
    """
    text = result.get('text') or ''
    images = result.get('images') or []
    links = result.get('links') or []
    summary = {
        'word_count': word_count(text),
        'image_count': len(images),
        'link_count': len(links),
        'top_words': top_words(text, 10),
    }
    return summary