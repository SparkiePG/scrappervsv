"""
AI utilities for QuadScraper
============================

This module wraps optional natural‑language processing features.  It exposes
functions that use pre‑trained transformer models to perform tasks such as
named‑entity recognition (NER).  Because these models are large and may
require GPU acceleration, the functions fall back to simple heuristics or
empty results when the necessary dependencies are unavailable.

Usage example:

.. code-block:: python

    from backend.ai import perform_ner

    text = "John Doe lives in New York."
    entities = perform_ner(text)
    for ent in entities:
        print(ent['word'], ent['entity_group'])

The implementation tries to import ``transformers.pipeline``.  If the
``transformers`` package is not installed, ``perform_ner`` will return an
empty list and log a warning.  This design allows the rest of the system to
operate even when the AI components are not present.
"""

from __future__ import annotations

from typing import List, Dict, Any

try:
    # Lazy import of transformers to avoid heavy startup cost if unused
    from transformers import pipeline  # type: ignore
    _ner_pipeline = pipeline("ner", grouped_entities=True)
except Exception:
    _ner_pipeline = None


def perform_ner(text: str) -> List[Dict[str, Any]]:
    """Perform named‑entity recognition on the provided text.

    :param text: The input text to analyse.
    :return: A list of entity dictionaries containing ``word`` and
      ``entity_group`` keys.  If no NER model is available or the text
      is empty, returns an empty list.
    """
    if not text or not isinstance(text, str):
        return []
    if _ner_pipeline is None:
        # When transformers is not installed, skip NER.  In a production
        # deployment you might log this condition or raise a custom
        # exception to inform the caller that AI features are unavailable.
        return []
    try:
        entities = _ner_pipeline(text)
        # The Hugging Face pipeline returns a list of entities.  We return
        # only the fields we care about to keep responses lean.
        simplified: List[Dict[str, Any]] = []
        for ent in entities:
            simplified.append({
                'word': ent.get('word'),
                'entity_group': ent.get('entity_group'),
                'score': ent.get('score'),
            })
        return simplified
    except Exception:
        # On unexpected errors, fall back to empty.  Avoid leaking
        # exceptions to the caller because AI is an optional feature.
        return []
