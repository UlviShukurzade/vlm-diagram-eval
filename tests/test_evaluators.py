"""Evaluator tests.

These build NetworkX graphs directly rather than going through the parser
service, so they run without Docker. See ``test_parsing.py`` for the tests that
exercise the service.

The core property asserted here is self-similarity: a metric that does not score
a graph as maximally similar to itself is broken, whatever else it does.
"""

from itertools import pairwise

import networkx as nx
import pytest

from vlm_diagram_eval.evaluators.metrics import (
    DirectedErrorEvaluator,
    DirectedSpectralSimilarity,
    UndirectedSpectralSimilarity,
    WLSimilarityGrakel,
)

SIMILARITY_EVALUATORS = [
    DirectedSpectralSimilarity,
    UndirectedSpectralSimilarity,
    WLSimilarityGrakel,
]


def _chain(n: int = 5) -> nx.DiGraph:
    """A -> B -> C -> ... with labels on both nodes and edges."""
    g = nx.DiGraph()
    names = [chr(ord("a") + i) for i in range(n)]
    for name in names:
        g.add_node(name, label=name)
    for src, dst in pairwise(names):
        g.add_edge(src, dst, label="next")
    return g


def _star(n: int = 5) -> nx.DiGraph:
    """A hub pointing at n-1 leaves — structurally unlike a chain of the same size."""
    g = nx.DiGraph()
    g.add_node("hub", label="hub")
    for i in range(n - 1):
        leaf = f"leaf{i}"
        g.add_node(leaf, label=leaf)
        g.add_edge("hub", leaf, label="to")
    return g


@pytest.mark.parametrize("evaluator_cls", SIMILARITY_EVALUATORS, ids=lambda c: c().name())
def test_identical_graphs_score_maximally(evaluator_cls):
    g = _chain()
    score = evaluator_cls().evaluate(g, g)
    assert score is not None, "evaluator returned None for a valid graph pair"
    assert score == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("evaluator_cls", SIMILARITY_EVALUATORS, ids=lambda c: c().name())
def test_different_graphs_score_lower_than_identical(evaluator_cls):
    evaluator = evaluator_cls()
    same = evaluator.evaluate(_chain(), _chain())
    different = evaluator.evaluate(_chain(), _star())
    assert different is not None
    assert different < same


@pytest.mark.parametrize("evaluator_cls", SIMILARITY_EVALUATORS, ids=lambda c: c().name())
def test_scores_are_within_unit_interval(evaluator_cls):
    score = evaluator_cls().evaluate(_chain(), _star())
    assert 0.0 <= score <= 1.0


def test_directed_error_evaluator_reports_no_errors_for_identical_graphs():
    result = DirectedErrorEvaluator().evaluate(_chain(), _chain())
    assert result["Score_F1"] == pytest.approx(1.0)
    assert result["Count_Missing"] == 0
    assert result["Count_Flipped"] == 0
    assert result["Count_Hallucinated"] == 0
    assert result["Count_Correct"] == 4  # a->b->c->d->e


def test_directed_error_evaluator_detects_a_flipped_edge():
    truth = _chain(3)  # a -> b -> c

    flipped = nx.DiGraph()
    for name in ("a", "b", "c"):
        flipped.add_node(name, label=name)
    flipped.add_edge("a", "b", label="next")
    flipped.add_edge("c", "b", label="next")  # direction reversed

    result = DirectedErrorEvaluator().evaluate(truth, flipped)
    assert result["Count_Flipped"] == 1
    assert result["Score_F1"] < 1.0


def test_directed_error_evaluator_detects_a_hallucinated_edge():
    truth = _chain(3)

    extra = _chain(3)
    extra.add_edge("a", "c", label="shortcut")  # an edge the truth does not have

    result = DirectedErrorEvaluator().evaluate(truth, extra)
    assert result["Count_Hallucinated"] == 1
    assert result["Count_Missing"] == 0
