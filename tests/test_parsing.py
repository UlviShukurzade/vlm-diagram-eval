"""Parser tests.

These need the Mermaid parser service running on :9595 (`make parser`). They are
marked ``needs_parser`` so `make test-fast` can skip them.

The fixtures in ``tests/fixtures/diagrams.py`` were collected during the thesis
work and cover all four diagram types the pipeline supports.
"""

import networkx as nx
import pytest
import requests

from tests.fixtures.diagrams import (
    ALL_DIAGRAMS,
    NESTED_LAYERS,
    MERMAID_CLASS_DIAGRAM,
    MERMAID_YES_NO,
    MINIMAL,
    STATE_DIAGRAM,
)
from vlm_diagram_eval.parsing.graph import get_graph_from_json

pytestmark = pytest.mark.needs_parser

PARSER_URL = "http://localhost:9595/diagram"


def _service_is_up() -> bool:
    try:
        requests.post(PARSER_URL, json={"code": "graph TD; A-->B;"}, timeout=5)
    except requests.exceptions.RequestException:
        return False
    return True


@pytest.fixture(scope="session", autouse=True)
def require_parser_service():
    if not _service_is_up():
        pytest.skip("Mermaid parser service not reachable on :9595 — run `make parser`", allow_module_level=True)


def test_minimal_flowchart_has_expected_shape():
    """MINIMAL is ``A-->B-->C`` plus ``A-->C``: three nodes, three edges."""
    g = get_graph_from_json(MINIMAL)
    assert isinstance(g, nx.DiGraph)
    assert g.number_of_nodes() == 3
    assert g.number_of_edges() == 3
    assert set(g.edges()) == {("A", "B"), ("B", "C"), ("A", "C")}


def test_every_fixture_parses_without_error():
    for name, code in ALL_DIAGRAMS.items():
        g = get_graph_from_json(code)
        assert g.number_of_nodes() > 0, f"{name} parsed to an empty graph"


def test_subgraph_membership_lands_on_the_parent_attribute():
    """NESTED_LAYERS wraps two groups of five nodes in subgraphs.

    Membership must be a node attribute, not a synthetic edge — the earlier
    implementation emitted extra 'subgraph' edges, which inflated edge counts and
    changed every downstream metric.
    """
    g = get_graph_from_json(NESTED_LAYERS)
    parents = {n: d.get("parent") for n, d in g.nodes(data=True) if d.get("parent")}
    assert parents, "no node carried a 'parent' attribute"
    assert not any(d.get("label") == "subgraph" for _, _, d in g.edges(data=True))


def test_labels_are_normalised_to_lowercase():
    g = get_graph_from_json(NESTED_LAYERS)
    labels = [d.get("label", "") for _, d in g.nodes(data=True) if d.get("label")]
    assert labels
    assert all(label == label.lower() for label in labels)


def test_edge_labels_are_preserved():
    g = get_graph_from_json(MERMAID_YES_NO)
    labels = {d.get("label") for _, _, d in g.edges(data=True)}
    assert "Yes" in labels
    assert "No" in labels


def test_edge_labels_are_not_lowercased_unlike_node_labels():
    """Pins a real asymmetry in ``api_parser``.

    Node labels are normalised (lowercased, whitespace collapsed) for the WL
    kernel; edge labels are passed through verbatim. Edge labels also feed the
    labelled kernel, so this asymmetry is worth being deliberate about rather
    than discovering by accident.
    """
    g = get_graph_from_json(MERMAID_YES_NO)
    node_labels = [d["label"] for _, d in g.nodes(data=True) if d.get("label")]
    edge_labels = [d["label"] for *_, d in g.edges(data=True) if d.get("label")]

    assert all(label == label.lower() for label in node_labels)
    assert any(label != label.lower() for label in edge_labels)


def test_state_diagram_parses():
    g = get_graph_from_json(STATE_DIAGRAM)
    assert g.number_of_nodes() > 0
    assert g.number_of_edges() > 0


def test_class_diagram_parses():
    g = get_graph_from_json(MERMAID_CLASS_DIAGRAM)
    assert g.number_of_nodes() > 0


def test_unsupported_diagram_type_raises():
    with pytest.raises(ValueError):
        get_graph_from_json('pie title Pets\n  "Dogs" : 386')
