import math

import pytest

from eval.metrics import judged_at_k, ndcg_at_k, precision_at_k, reciprocal_rank

GRADES = {"a": 2, "b": 1, "c": 0, "d": 2}


def test_precision_counts_grades_of_one_or_more_and_divides_by_k():
    assert precision_at_k(["a", "b", "c", "x"], GRADES, k=4) == 0.5 
    assert precision_at_k(["a"], GRADES, k=10) == 0.1  


def test_reciprocal_rank_is_one_over_first_relevant_position():
    assert reciprocal_rank(["c", "x", "b"], GRADES) == pytest.approx(1 / 3)
    assert reciprocal_rank(["c", "x"], GRADES) == 0.0
    assert reciprocal_rank(["x", "c", "a"], GRADES, k=2) == 0.0  


def test_ndcg_is_one_for_the_ideal_order_and_lower_otherwise():
    assert ndcg_at_k(["a", "d", "b", "c"], GRADES) == pytest.approx(1.0)
    worse = ndcg_at_k(["c", "b", "a", "d"], GRADES)
    assert 0 < worse < 1


def test_ndcg_matches_hand_computation():
    dcg = 3 / math.log2(3)
    ideal = 3 / math.log2(2) + 3 / math.log2(3) + 1 / math.log2(4)
    assert ndcg_at_k(["c", "a"], GRADES) == pytest.approx(dcg / ideal)


def test_ndcg_undefined_without_any_relevant_judgment():
    assert ndcg_at_k(["c"], {"c": 0}) is None


def test_judged_share():
    assert judged_at_k(["a", "x", "c", "y"], GRADES) == 0.5
