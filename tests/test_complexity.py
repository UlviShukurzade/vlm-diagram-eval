"""SCI tests, including reproduction against the thesis's own published values.

``tests/fixtures/sci_reference.csv`` holds a slice of ``sample_900_sci.parquet``
-- the 900-diagram evaluation set from thesis section 4.5 -- with the SCI
components the thesis reports. The reproduction test re-derives those numbers
from the Mermaid source and asserts they match.

That makes this the one place the repository verifies a published result rather
than merely implementing its specification.
"""

import csv
from pathlib import Path

import networkx as nx
import pytest

from vlm_diagram_eval.analysis.complexity import (
    calculate_sci_components,
    get_difficulty,
)

REFERENCE = Path(__file__).parent / "fixtures" / "sci_reference.csv"


# ── Unit behaviour ────────────────────────────────────────────────────────────


def test_empty_graph_scores_zero_rather_than_raising():
    result = calculate_sci_components(nx.DiGraph())
    assert result["sci_score"] == 0.0
    assert result["node_count"] == 0


def test_components_follow_the_published_weights():
    """A -> B, A -> C: 3 nodes, 2 edges, 1 decision node, no nesting."""
    g = nx.DiGraph()
    for n in "ABC":
        g.add_node(n, parent=None)
    g.add_edge("A", "B")
    g.add_edge("A", "C")

    r = calculate_sci_components(g)
    assert r["node_count"] == 3
    assert r["edge_count"] == 2
    assert r["decision_count"] == 1  # A has out-degree 2
    assert r["parent_count"] == 0
    assert r["sci_nodes"] == pytest.approx(1.5)  # 0.5 * 3
    assert r["sci_edges"] == pytest.approx(2.0)  # 1.0 * 2
    assert r["sci_connectivity"] == pytest.approx(2 / 3)  # 1.0 * E/N
    assert r["sci_decisions"] == pytest.approx(3.0)  # 3.0 * 1
    assert r["sci_nesting"] == pytest.approx(0.0)
    assert r["sci_score"] == pytest.approx(1.5 + 2.0 + 2 / 3 + 3.0)


def test_decision_nodes_need_out_degree_above_one():
    """In-degree must not count: a join is not a branch."""
    g = nx.DiGraph()
    for n in "ABC":
        g.add_node(n, parent=None)
    g.add_edge("A", "C")
    g.add_edge("B", "C")  # C has in-degree 2, out-degree 0
    assert calculate_sci_components(g)["decision_count"] == 0


def test_nesting_counts_distinct_parents_ignoring_none():
    g = nx.DiGraph()
    g.add_node("a", parent="box1")
    g.add_node("b", parent="box1")  # same container
    g.add_node("c", parent="box2")
    g.add_node("d", parent=None)  # not nested
    r = calculate_sci_components(g)
    assert r["parent_count"] == 2
    assert r["sci_nesting"] == pytest.approx(6.0)


@pytest.mark.parametrize(
    ("score", "tier"),
    [
        (0.0, "Easy"),
        (11.99, "Easy"),
        (12.0, "Moderate"),
        (24.99, "Moderate"),
        (25.0, "Hard"),  # thesis 4.4: Hard is >= 25
        (100.0, "Hard"),
        (None, "Unknown"),
    ],
)
def test_difficulty_boundaries(score, tier):
    assert get_difficulty(score) == tier


# ── Reproduction of published values ──────────────────────────────────────────


def _reference_rows():
    if not REFERENCE.exists():
        pytest.skip("sci_reference.csv not present")
    with REFERENCE.open() as fh:
        return list(csv.DictReader(fh))


@pytest.mark.needs_parser
def test_reproduces_thesis_sci_values():
    """Re-derive SCI from source and compare against the thesis's own numbers."""
    from vlm_diagram_eval.parsing.graph import get_graph_from_json

    rows = _reference_rows()
    assert rows, "reference set is empty"

    mismatches = []
    for row in rows:
        got = calculate_sci_components(get_graph_from_json(row["code"]))
        for field in (
            "node_count",
            "edge_count",
            "decision_count",
            "parent_count",
            "sci_nodes",
            "sci_edges",
            "sci_connectivity",
            "sci_decisions",
            "sci_nesting",
            "sci_score",
        ):
            expected = float(row[field])
            if abs(got[field] - expected) > 1e-6:
                mismatches.append(f"{row['image_filename']} {field}: got {got[field]}, thesis {expected}")

    assert not mismatches, "SCI no longer reproduces published values:\n" + "\n".join(mismatches[:20])


@pytest.mark.needs_parser
def test_reproduces_thesis_difficulty_labels():
    from vlm_diagram_eval.parsing.graph import get_graph_from_json

    rows = _reference_rows()
    wrong = []
    for row in rows:
        components = calculate_sci_components(get_graph_from_json(row["code"]))
        tier = get_difficulty(components["sci_score"])
        if tier != row["difficulty"]:
            wrong.append(
                f"{row['image_filename']}: got {tier}, thesis {row['difficulty']} (SCI {components['sci_score']:.2f})"
            )
    assert not wrong, "difficulty stratification drifted:\n" + "\n".join(wrong[:20])
