"""
Match users by shared sources of meaning.

Not a single compatibility score — returns the structure of alignment:
which values are shared, which are unique to each person, and how
similar the unique values are.
"""

from __future__ import annotations

from .dedup import policy_similarity
from .store import Store


def find_matches(
    user_id: str,
    store: Store,
    top_n: int = 10,
) -> list[dict]:
    """
    Find the most aligned users for a given user.

    Returns a list of matches, each with:
      - user_id: the matched user
      - shared: list of shared canonical value titles
      - unique_self: values only the querying user holds
      - unique_other: values only the matched user holds
      - alignment: proportion of values that overlap
      - resonance: average similarity of unique values (how close the
        non-overlapping values are to each other)
    """
    my_values = store.user_values(user_id)
    if not my_values:
        return []

    my_ids = {v["id"] for v in my_values}
    my_by_id = {v["id"]: v for v in my_values}

    # Find all users who share at least one canonical value
    candidates: dict[str, set[str]] = {}
    for v in my_values:
        for other_uid in store.users_for_value(v["id"]):
            if other_uid == user_id:
                continue
            candidates.setdefault(other_uid, set()).add(v["id"])

    # Score each candidate
    matches = []
    for other_uid, shared_ids in candidates.items():
        other_values = store.user_values(other_uid)
        other_ids = {v["id"] for v in other_values}
        other_by_id = {v["id"]: v for v in other_values}

        shared = [my_by_id[vid]["title"] for vid in shared_ids]
        unique_self_vals = [my_by_id[vid] for vid in my_ids - other_ids]
        unique_other_vals = [other_by_id[vid] for vid in other_ids - my_ids]

        # Alignment: fraction of combined unique values that are shared
        total = len(my_ids | other_ids)
        alignment = len(shared_ids) / total if total else 0.0

        # Resonance: how similar the non-overlapping values are
        resonance = _cross_resonance(unique_self_vals, unique_other_vals)

        matches.append({
            "user_id": other_uid,
            "shared": sorted(shared),
            "unique_self": sorted(v["title"] for v in unique_self_vals),
            "unique_other": sorted(v["title"] for v in unique_other_vals),
            "alignment": round(alignment, 3),
            "resonance": round(resonance, 3),
        })

    matches.sort(key=lambda m: (m["alignment"], m["resonance"]), reverse=True)
    return matches[:top_n]


def _cross_resonance(
    values_a: list[dict], values_b: list[dict]
) -> float:
    """Average best-match similarity between two sets of values."""
    if not values_a or not values_b:
        return 0.0
    total = 0.0
    for va in values_a:
        best = max(
            policy_similarity(va["policies"], vb["policies"])
            for vb in values_b
        )
        total += best
    for vb in values_b:
        best = max(
            policy_similarity(va["policies"], vb["policies"])
            for va in values_a
        )
        total += best
    return total / (len(values_a) + len(values_b))
