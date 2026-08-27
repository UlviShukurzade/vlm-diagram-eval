"""Client for the containerised Mermaid parser service.

Mermaid code is parsed by Mermaid's own parser inside the service (see
``services/mermaid_parser``) and returned as nodes and edges, which this module
turns into a NetworkX graph. Ground truth and model output take the identical
path, so parser quirks cancel out of any comparison.
"""

import os

import matplotlib.pyplot as plt
import networkx as nx
import requests

# Endpoint of the containerised parser (see `make parser`). Override with
# PARSER_SERVICE_URL to point at a service on another host or port.
PARSER_URL = os.environ.get("PARSER_SERVICE_URL", "http://localhost:9595").rstrip("/") + "/diagram"
PARSER_TIMEOUT = float(os.environ.get("PARSER_SERVICE_TIMEOUT", "30"))


def api_parser(data):
    # print(data)
    # Use MultiDiGraph to prevent edge overwriting
    nx_format = {"directed": True, "multigraph": False, "graph": {}, "nodes": [], "links": []}

    for node_data in data["nodes"]:
        # Standardize labels: lower case, replace <br> with \n, normalize spaces
        raw_label = str(node_data.get("label", "")).lower()
        clean_label = raw_label.replace("<br>", "\n").replace("\\n", "\n").replace("\n", " ")
        clean_label = " ".join(clean_label.split())  # Collapses multiple spaces into one

        nx_node = {
            "id": node_data["id"],
            "label": clean_label,  # Normalize for WL Kernel
            "shape": node_data.get("shape", "squareRect"),
            "parent": node_data.get("parentId", None),  # Store as attribute, not just edge
        }
        nx_format["nodes"].append(nx_node)

    for edge in data["edges"]:
        # Ensure every edge has a 'type' or 'label' for labeled WL Kernels
        label = edge.get("label", "unlabeled")
        nx_edge = {"source": edge["start"], "target": edge["end"], "id": edge["id"], "label": label}
        nx_format["links"].append(nx_edge)

    # Convert to graph and handle subgraphs
    G = nx.node_link_graph(nx_format, edges="links")
    return G


def get_graph_from_json(code):
    # Pre-process code to fix known Mermaid Parser issues
    # 1. Fix empty subgraph labels: subgraph id [""] -> subgraph id [" "]
    code = code.replace('[""]', '[" "]')

    # 2. Fix Left, Up, Down directional arrows (not supported in older Mermaid Flowcharts)
    # Replaces <-- with -->, <== with ==>, etc.
    # NOTE: This FLIPS the direction of the edge, but allows parsing to continue.
    # Given that Spectral/WL kernels are robust to some edge flips (or we check undirected),
    # this is better than a crash.
    # code = code.replace("<--", "-->").replace("<==", "==>").replace("o--", "---")

    payload = {"code": code}
    mapping = {
        "flowchart": api_parser,
        "graph": api_parser,
        "stateDiagram-v2": api_parser,
        "stateDiagram": api_parser,
        "classDiagram": api_parser,
    }
    for id, parser in mapping.items():
        if code.find(id) != -1:
            resp = requests.post(PARSER_URL, json=payload, timeout=PARSER_TIMEOUT)
            resp.raise_for_status()
            # actual_edge_count = len(resp.json()['edges'])
            # print("######################\nActual edge count (from Mermaid API):", actual_edge_count)
            # time.sleep(0.05)
            return parser(resp.json())
    raise ValueError("Diagram type is currently not supported!")


def plot_graph(G, save_path):
    plt.figure(figsize=(15, 8))

    pos = nx.spring_layout(G, k=1, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_size=300)

    node_labels = nx.get_node_attributes(G, "label")
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=6)

    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=10, width=0.5)

    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=5, label_pos=0.7)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight", pad_inches=0.5)


if __name__ == "__main__":
    example = """
    graph TD
        subgraph Forest Garden Layers
            C[Canopy Layer]
            S[Shrub Layer]
            H[Herbaceous Layer]
            R[Root Layer]
            M[Soil Microbiome]
        end
        subgraph System Architecture Layers
            UI[User Interface]
            ML[Middle Logic]
            DS[Data Services]
            DB[Database]
            IS[Infrastructure]
        end
        C --- UI
        S --- ML
        H --- DS
        R --- DB
        M --- IS
        C --> S
        S --> H
        H --> R
        R --> M
        UI --> ML
        ML --> DS
        DS --> DB
        DB --> IS
    """

    G = get_graph_from_json(example)

    # actual_edge_count = sum(1 for _, _, d in G.edges(data=True) if d.get('label') != 'subgraph')
    # print("Actual edge count (excluding subgraph edges):", actual_edge_count)
    # print(G)
    # G2 = get_graph_from_json(flowchart_49441_65_gen)
    # print(G2)

    # nx.draw(G, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=10)
    # plt.savefig("graph.png")

    # plot_graph(G, "class.png")

    # Draw the graph
    # pos = nx.spring_layout(G)  # Layout for nodes
    # nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=10)

    # Draw edge labels
    # edge_labels = nx.get_edge_attributes(G, "label")
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # plt.show()

    # plt.savefig("graph_edge_shape.png")
    # adj_matrix = nx.to_numpy_array(G)
    # print(adj_matrix)
    # print("\n\n to_dict_of_lists \n\n##############################\n\n\n\n", nx.to_dict_of_lists(G))
    # print("\n\n to_edgelist \n\n##############################\n\n\n\n", nx.to_edgelist(G))
    # print("\n\n to_dict_of_dicts \n\n##############################\n\n\n\n", nx.to_dict_of_dicts(G))

    print(G.nodes(data=True))
