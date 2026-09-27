from app.services.ai_benchmark import passes_retrieval_gate, score_retrieval
from app.services.ai_retrieval import _expanded_terms, _score


def test_semantic_alias_expansion_reduces_vocabulary_mismatch():
    query = _expanded_terms("How should a manager coach someone?")
    assert "leader" in query
    assert "feedback" in query
    assert _score(query, "Mentoring and feedback help develop people.", "Leadership practice") > 0


def test_retrieval_scorecard_computes_hit_rate_and_mrr():
    score = score_retrieval(
        rankings=[["lesson-a", "lesson-b"], ["lesson-x", "lesson-c"], ["lesson-d"]],
        expected_ids=[{"lesson-a"}, {"lesson-c"}, {"lesson-d"}],
    )
    assert score.cases == 3
    assert score.hit_rate_at_k == 1.0
    assert score.mean_reciprocal_rank == 0.8333
    assert passes_retrieval_gate(score)


def test_retrieval_gate_rejects_weak_baseline():
    score = score_retrieval(
        rankings=[["wrong"], ["also-wrong"]],
        expected_ids=[{"expected-a"}, {"expected-b"}],
    )
    assert passes_retrieval_gate(score) is False
