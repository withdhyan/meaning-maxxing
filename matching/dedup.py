"""
Value deduplication via policy text similarity.

Uses MAI's criteria: two values overlap if someone following one set of
policies would attend to the same things as the other.

This implementation uses word overlap (Jaccard similarity) on normalized
policy text. For production, swap in embedding-based similarity.
"""

from __future__ import annotations

import re
from typing import Optional

# Similarity threshold: above this, two values are considered the same
# source of meaning. Tuned conservatively — false negatives are better
# than false merges.
SIMILARITY_THRESHOLD = 0.50


def policy_similarity(policies_a: list[str], policies_b: list[str]) -> float:
    """
    Jaccard similarity on normalized policy word sets.

    Strips the CAPITALIZED_NOUN prefix to focus on the qualifying phrases
    where the actual meaning lives.
    """
    words_a = _policy_words(policies_a)
    words_b = _policy_words(policies_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def find_duplicate(
    title: str,
    policies: list[str],
    existing: list[dict],
) -> Optional[str]:
    """
    Check if a value duplicates any in the existing set.

    Returns the ID of the matching canonical value, or None.
    """
    for canonical in existing:
        sim = policy_similarity(policies, canonical["policies"])
        if sim >= SIMILARITY_THRESHOLD:
            return canonical["id"]
    return None


# -- Internals --

_CAPS_PREFIX = re.compile(r"^[A-Z][A-Z\s]+\b")
_STOPWORDS = frozenset(
    "a an the that this these those of in to for with from by on at is are "
    "was were be been being have has had do does did will would shall should "
    "may might can could and but or nor not no so yet also very".split()
)


def _normalize(text: str) -> str:
    """Lowercase, strip CAPS prefix, remove punctuation."""
    text = _CAPS_PREFIX.sub("", text)
    text = re.sub(r"[^\w\s]", "", text.lower())
    return text.strip()


def _policy_words(policies: list[str]) -> set[str]:
    """Extract content words from a list of policies."""
    words = set()
    for p in policies:
        for w in _normalize(p).split():
            if w not in _STOPWORDS and len(w) > 2:
                words.add(w)
    return words
