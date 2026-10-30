from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_ids: frozenset[str]


@dataclass(frozen=True)
class RetrievalScore:
    cases: int
    hit_rate_at_k: float
    mean_reciprocal_rank: float


def score_ranked_ids(cases: Sequence[RetrievalCase], ranked_ids: Sequence[Sequence[str]], *, k: int = 3) -> RetrievalScore:
    if len(cases) != len(ranked_ids):
        raise ValueError("cases and ranked_ids must have equal length")
    if not cases:
        return RetrievalScore(cases=0, hit_rate_at_k=0.0, mean_reciprocal_rank=0.0)

    hits = 0
    reciprocal_rank_total = 0.0
    for case, ranking in zip(cases, ranked_ids, strict=True):
        top = list(ranking)[:k]
        if any(item in case.expected_ids for item in top):
            hits += 1
        for index, item in enumerate(ranking, start=1):
            if item in case.expected_ids:
                reciprocal_rank_total += 1.0 / index
                break

    count = len(cases)
    return RetrievalScore(
        cases=count,
        hit_rate_at_k=round(hits / count, 4),
        mean_reciprocal_rank=round(reciprocal_rank_total / count, 4),
    )


def meets_quality_gate(score: RetrievalScore, *, min_hit_rate: float = 0.9, min_mrr: float = 0.75) -> bool:
    return score.cases > 0 and score.hit_rate_at_k >= min_hit_rate and score.mean_reciprocal_rank >= min_mrr


def score_retrieval(*, rankings: Sequence[Sequence[str]], expected_ids: Sequence[set[str] | frozenset[str]], k: int = 3) -> RetrievalScore:
    cases = [
        RetrievalCase(query=f"case-{index + 1}", expected_ids=frozenset(expected))
        for index, expected in enumerate(expected_ids)
    ]
    return score_ranked_ids(cases, rankings, k=k)


def passes_retrieval_gate(score: RetrievalScore, *, min_hit_rate: float = 0.9, min_mrr: float = 0.75) -> bool:
    return meets_quality_gate(score, min_hit_rate=min_hit_rate, min_mrr=min_mrr)
