"""String similarity helpers (stdlib only).

POI deduplication previously used ``fuzzywuzzy.token_set_ratio``; this module
reimplements the same idea with :mod:`difflib` so editors resolve imports
without extra wheels (e.g. python-Levenshtein).
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _full_process(s: str) -> str:
    """Lowercase and keep alphanumerics + spaces (like fuzzywuzzy full_process)."""
    return re.sub(r"[^\w\s]", "", s.lower()).strip()


def _ratio(a: str, b: str) -> int:
    if a == b:
        return 100
    if not a or not b:
        return 0
    return int(SequenceMatcher(None, a, b).ratio() * 100)


def token_set_ratio(s1: str, s2: str) -> int:
    """
    Similarity 0–100; word-order independent, aligned with
    ``fuzzywuzzy.fuzz.token_set_ratio`` for typical POI names.
    """
    s1, s2 = _full_process(s1), _full_process(s2)
    if not s1 or not s2:
        return 0
    if s1 == s2:
        return 100

    t1 = set(s1.split())
    t2 = set(s2.split())
    inter = t1 & t2
    diff1 = t1 - t2
    diff2 = t2 - t1

    def _sorted_join(tokens: set[str]) -> str:
        return " ".join(sorted(tokens))

    sorted_sect = _sorted_join(inter)
    sorted_1to2 = _sorted_join(diff1)
    sorted_2to1 = _sorted_join(diff2)

    combined1 = (sorted_sect + " " + sorted_1to2 + " " + sorted_2to1).strip()
    combined2 = (sorted_sect + " " + sorted_2to1 + " " + sorted_1to2).strip()

    return max(
        _ratio(sorted_sect, combined1),
        _ratio(sorted_sect, combined2),
        _ratio(combined1, combined2),
    )
