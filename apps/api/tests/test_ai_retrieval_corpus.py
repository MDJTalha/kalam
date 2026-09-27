import json
from pathlib import Path

from app.services.ai_benchmark import passes_retrieval_gate, score_retrieval
from app.services.ai_retrieval import _expanded_terms, _score

FIXTURE = Path(__file__).parent / "fixtures" / "ai_retrieval_eval.json"


def test_retrieval_evaluation_corpus_meets_quality_gate():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    documents = payload["documents"]
    rankings = []
    expected_ids = []
    for case in payload["cases"]:
        query_terms = _expanded_terms(case["query"])
        ranked = sorted(
            documents,
            key=lambda doc: (-_score(query_terms, doc["text"], doc["title"]), doc["id"]),
        )
        rankings.append([doc["id"] for doc in ranked])
        expected_ids.append(set(case["expected"]))
    score = score_retrieval(rankings=rankings, expected_ids=expected_ids, k=3)
    assert score.cases == len(payload["cases"])
    assert score.hit_rate_at_k >= 0.9
    assert score.mean_reciprocal_rank >= 0.75
    assert passes_retrieval_gate(score)
