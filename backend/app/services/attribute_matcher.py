"""Attribute-based catalog matching: deterministic, explainable, testable.

Replaces whole-string fuzzy scoring as the primary matcher. Instead of asking
"do these two strings look alike?", it asks "do they agree on the things that
actually determine whether they are the same part?"

Scoring rules, in priority order:
  1. A CONFLICT on any attribute both sides state -> reject (score penalty).
  2. Agreement on discriminating attributes (family, diameter, bearing, ...)
     -> strong evidence for a match.
  3. Fuzzy string similarity acts only as a tie-breaker among survivors, so the
     old signal still contributes without being able to override a conflict.
"""

from typing import Final, Sequence

from rapidfuzz import fuzz

from app.services.attribute_extractor import canonicalize, extract_attributes

# Attributes that identify *which product* it is. Agreement here is evidence.
_DISCRIMINATING: Final[tuple[str, ...]] = (
    "family",
    "diameter",
    "bearing",
    "pressure",
    "material",
    "length",
    "thread_pitch",
)

# Attribute weights: how much each agreement is worth.
_WEIGHTS: Final[dict[str, float]] = {
    "family": 40.0,
    "bearing": 40.0,
    "diameter": 25.0,
    "thread_pitch": 15.0,
    "length": 15.0,
    "material": 10.0,
    "pressure": 10.0,
    "finish": 10.0,
}

# Below this, no candidate is trusted enough to auto-match.
MATCH_THRESHOLD: Final = 60.0
# Two candidates within this many points of each other are a tie -> no auto-match.
AMBIGUITY_MARGIN: Final = 8.0

_ATTRIBUTE_COLUMNS: Final[tuple[str, ...]] = (
    "family",
    "diameter",
    "thread_pitch",
    "length",
    "finish",
    "material",
    "pressure",
    "bearing",
)


def catalog_attributes(row: dict[str, str]) -> dict[str, str]:
    """
    Derive comparable attributes for one catalog row.

    Catalog columns are authoritative when present; otherwise the description is
    parsed with the same rules used for the order line, so both sides of the
    comparison are normalized identically.
    """
    attributes = extract_attributes(row.get("description", ""))
    for column in _ATTRIBUTE_COLUMNS:
        value = (row.get(column) or "").strip()
        if value:
            attributes[column] = value.lower()
    return canonicalize(attributes)


def score_candidate(
    query: dict[str, str], candidate: dict[str, str], query_text: str, candidate_text: str
) -> tuple[float, list[str], list[str]]:
    """
    Score one query against one candidate.

    Returns (score, agreements, conflicts). Conflicts are reported separately
    because they are the reason a match is rejected, not merely a penalty.
    """
    agreements: list[str] = []
    conflicts: list[str] = []
    score = 0.0

    for attribute in _DISCRIMINATING:
        left = query.get(attribute, "").strip()
        right = candidate.get(attribute, "").strip()
        if not left or not right:
            continue
        if left == right:
            agreements.append(attribute)
            score += _WEIGHTS.get(attribute, 10.0)
        else:
            conflicts.append(attribute)

    finish_query = query.get("finish", "").strip()
    finish_candidate = candidate.get("finish", "").strip()
    if finish_query and finish_candidate:
        if finish_query == finish_candidate:
            agreements.append("finish")
            score += _WEIGHTS["finish"]
        else:
            conflicts.append("finish")

    if not conflicts:
        # Fuzzy similarity is a tie-breaker only, capped so it can never carry
        # a match on its own.
        score += fuzz.token_sort_ratio(query_text, candidate_text) / 100 * 15.0

    return score, agreements, conflicts


def match_description(
    query_text: str, catalog_rows: Sequence[dict[str, str]]
) -> tuple[str | None, float, str | None, list[str]]:
    """
    Find the best catalog row for a free-text description.

    Returns (sku, score, runner_up_sku, conflicts). A low-confidence or
    ambiguous result returns no SKU, because a wrong SKU is more expensive for
    an order-entry system than a flagged gap.
    """
    if not catalog_rows:
        return None, 0.0, None, []

    query = canonicalize(extract_attributes(query_text))
    scored: list[tuple[float, str, list[str]]] = []
    for row in catalog_rows:
        score, _agreements, conflicts = score_candidate(
            query, catalog_attributes(row), query_text, row.get("description", "")
        )
        if conflicts:
            continue
        scored.append((score, row["sku"], conflicts))

    if not scored:
        return None, 0.0, None, ["all candidates conflicted"]

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_sku, _ = scored[0]
    runner_up = scored[1][1] if len(scored) > 1 else None

    if best_score < MATCH_THRESHOLD:
        return None, round(best_score, 1), best_sku, []

    if runner_up is not None and (best_score - scored[1][0]) < AMBIGUITY_MARGIN:
        # Too close to call. Do not guess between two real products.
        return None, round(best_score, 1), runner_up, ["ambiguous"]

    return best_sku, round(best_score, 1), runner_up, []
