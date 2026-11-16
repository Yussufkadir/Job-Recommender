"""Ranking metrics over graded relevance judgments.

Relevance scale (see eval/README.md): 2 = strong match, 1 = partly relevant, 0 = not relevant.
Results nobody has judged count as not relevant, the usual convention in IR evaluation;
`judged_at_k` reports how much of the top k was actually judged, so you can tell when the
numbers rest on missing labels.
"""
import math
from typing import Mapping, Optional, Sequence

RELEVANT = 1 


def precision_at_k(ranked: Sequence[str], grades: Mapping[str, int], k: int = 10) -> float:
    """Share of the top k results that are relevant. Divides by k even when fewer results
    came back: an empty slot is a missed opportunity, not a free pass."""
    return sum(grades.get(job, 0) >= RELEVANT for job in ranked[:k]) / k


def reciprocal_rank(ranked: Sequence[str], grades: Mapping[str, int], k: int = 10) -> float:
    """1 / position of the first relevant result in the top k, or 0 if there is none."""
    for position, job in enumerate(ranked[:k], start=1):
        if grades.get(job, 0) >= RELEVANT:
            return 1.0 / position
    return 0.0


def _dcg(gains: Sequence[int]) -> float:
    return sum((2 ** gain - 1) / math.log2(position + 1) for position, gain in enumerate(gains, start=1))


def ndcg_at_k(ranked: Sequence[str], grades: Mapping[str, int], k: int = 10) -> Optional[float]:
    """DCG of the top k divided by the best achievable DCG from all judged jobs for the query.
    None when the query has no relevant judged job at all (the score would be undefined)."""
    ideal = _dcg(sorted(grades.values(), reverse=True)[:k])
    if ideal == 0:
        return None
    return _dcg([grades.get(job, 0) for job in ranked[:k]]) / ideal


def judged_at_k(ranked: Sequence[str], grades: Mapping[str, int], k: int = 10) -> float:
    """Share of the top k that has a judgment (relevant or not)."""
    top = ranked[:k]
    return sum(job in grades for job in top) / len(top) if top else 1.0
