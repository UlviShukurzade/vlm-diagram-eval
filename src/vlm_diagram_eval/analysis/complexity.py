"""Structural Complexity Index (SCI) and difficulty stratification.

Implements thesis section 4.4. For a directed graph G = (V, E) with N = |V|,
E = |E|, D decision nodes (out-degree > 1) and P distinct parent identifiers:

    SCI(G) = 0.5*N + 1.0*E + 1.0*(E/N) + 3.0*D + 3.0*P

Each term isolates a different structural pressure:

    0.5*N     node scale -- diagram size, deliberately down-weighted
    1.0*E     edge scale -- total relational load
    1.0*E/N   connectivity -- average edge density
    3.0*D     branching -- nodes with more than one outgoing edge
    3.0*P     nesting -- distinct subgraph containers

Difficulty tiers (section 4.4): Easy < 12, Moderate 12-25, Hard >= 25.

This is a faithful port of ``calculate_sci_components`` from the thesis working
tree's ``filter_eligible.ipynb``. ``tests/test_complexity.py`` asserts it
reproduces the ``sci_*`` columns of ``sample_900_sci.parquet`` -- the values the
thesis itself reports -- so any drift from the published numbers fails the suite.
"""

from typing import Any

import networkx as nx

# Component weights, thesis section 4.4.2. Changing these invalidates comparison
# with published results and with the stored difficulty labels.
W_NODES = 0.5
W_EDGES = 1.0
W_CONNECTIVITY = 1.0
W_DECISIONS = 3.0
W_NESTING = 3.0

EASY_BELOW = 12
HARD_AT_OR_ABOVE = 25

_EMPTY: dict[str, Any] = {
    "node_count": 0,
    "edge_count": 0,
    "decision_count": 0,
    "parent_count": 0,
    "sci_nodes": 0.0,
    "sci_edges": 0.0,
    "sci_connectivity": 0.0,
    "sci_decisions": 0.0,
    "sci_nesting": 0.0,
    "sci_score": 0.0,
}


def calculate_sci_components(graph: nx.DiGraph) -> dict[str, Any]:
    """Decompose a graph into its SCI components.

    Args:
        graph: Directed graph, typically from
            :func:`vlm_diagram_eval.parsing.graph.get_graph_from_json`. Subgraph
            membership must be carried on the ``parent`` node attribute.

    Returns:
        Raw counts (``node_count``, ``edge_count``, ``decision_count``,
        ``parent_count``), the five weighted components (``sci_nodes`` ...
        ``sci_nesting``), and the total ``sci_score``. An empty graph returns all
        zeros rather than raising, so batch runs stay aligned with their input.
    """
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()

    decisions = len([n for n in graph.nodes() if graph.out_degree(n) > 1])
    parents = set(nx.get_node_attributes(graph, "parent").values())
    parents.discard(None)
    parent_count = len(parents)

    if n_nodes == 0:
        return dict(_EMPTY)

    node_score = float(n_nodes * W_NODES)
    edge_score = float(n_edges * W_EDGES)
    connectivity_score = float((n_edges / n_nodes) * W_CONNECTIVITY)
    decision_score = float(decisions * W_DECISIONS)
    nesting_score = float(parent_count * W_NESTING)

    return {
        "node_count": n_nodes,
        "edge_count": n_edges,
        "decision_count": decisions,
        "parent_count": parent_count,
        "sci_nodes": node_score,
        "sci_edges": edge_score,
        "sci_connectivity": connectivity_score,
        "sci_decisions": decision_score,
        "sci_nesting": nesting_score,
        "sci_score": node_score + edge_score + connectivity_score + decision_score + nesting_score,
    }


def get_difficulty(score: float | None) -> str:
    """Map an SCI score to its difficulty tier.

    Boundaries follow thesis section 4.4: Easy < 12, Moderate 12-25, Hard >= 25.
    A score of exactly 25 is Hard.

    Args:
        score: An SCI score, or None for a diagram that failed to parse.

    Returns:
        ``"Easy"``, ``"Moderate"``, ``"Hard"``, or ``"Unknown"`` when score is None.
    """
    if score is None:
        return "Unknown"
    if score < EASY_BELOW:
        return "Easy"
    if score < HARD_AT_OR_ABOVE:
        return "Moderate"
    return "Hard"


def score_diagram(code: str) -> dict[str, Any]:
    """Parse Mermaid source and return its SCI components plus difficulty tier.

    Requires the parser service (``make parser``).

    Args:
        code: Mermaid source.

    Returns:
        The :func:`calculate_sci_components` mapping with a ``difficulty`` key added.
    """
    from vlm_diagram_eval.parsing.graph import get_graph_from_json

    components = calculate_sci_components(get_graph_from_json(code))
    components["difficulty"] = get_difficulty(components["sci_score"])
    return components
